"""Business logic for tenant-safe attendance, corrections, and leave workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, false, func, or_, select, text
from sqlalchemy.orm import Session

from app.domains.academics.models import Section, Subject
from app.domains.attendance.models import AttendanceCorrection, AttendanceRecord, LeaveRequest
from app.domains.attendance.schemas import (
    AttendanceCorrectionCreate,
    AttendanceCorrectionReview,
    AttendanceRecordCreate,
    AttendanceRecordUpdate,
    AttendanceSubmitRequest,
    LeaveApproval,
    LeaveRequestCreate,
    LeaveRequestUpdate,
)
from app.domains.audit.models import AuditEvent
from app.domains.delivery.models import ClassSession, SubjectOffering, TimetablePeriod
from app.domains.students.service import StudentsService
from app.security_context import ActorContext, resolve_actor_student_ids

DEFAULT_ATTENDANCE_THRESHOLD_PERCENTAGE = 75.0
INVALID_SESSION_REFERENCE = "Invalid session_id reference"


class AttendanceDomainError(Exception):
    """Represent one controlled attendance domain error mapped to HTTP status."""

    def __init__(self, detail: str, status_code: int) -> None:
        """Store deterministic domain error details for router translation."""

        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class AttendanceValidationError(AttendanceDomainError):
    """Represent one attendance validation error mapped to HTTP 422."""

    def __init__(self, detail: str) -> None:
        """Initialize a validation error payload."""

        super().__init__(detail=detail, status_code=422)


class AttendanceConflictError(AttendanceDomainError):
    """Represent one attendance conflict mapped to HTTP 409."""

    def __init__(self, detail: str) -> None:
        """Initialize a conflict error payload."""

        super().__init__(detail=detail, status_code=409)


class AttendanceService:
    """Manage tenant-scoped attendance submission, locking, corrections, and leave."""

    def __init__(self, session: Session, actor: ActorContext) -> None:
        """Initialize the attendance service with actor and SQLAlchemy session."""

        self.session = session
        self.actor = actor
        self._set_tenant_context()

    def _set_tenant_context(self) -> None:
        """Set transaction-local tenant context for forced PostgreSQL RLS."""

        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self.actor.tenant_id)},
        )

    def _audit(self, action: str, entity_type: str, entity_id: UUID, details: dict[str, object]) -> None:
        """Persist one tenant-scoped audit event."""

        self.session.add(
            AuditEvent(
                tenant_id=self.actor.tenant_id,
                account_id=self.actor.account_id,
                membership_id=self.actor.membership_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
            )
        )

    def _paginate(self, query, skip: int, limit: int):
        """Return one tuple of paginated items and total count."""

        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def _scoped_session_ids(self):
        """Select class sessions visible through the actor's academic scopes."""

        query = select(ClassSession.id).where(ClassSession.tenant_id == self.actor.tenant_id)
        if self.actor.scopes_of_type("institution"):
            return query

        offering_conditions = []
        offering_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("subject_offering")
            if scope.scope_reference_id is not None
        )
        if offering_ids:
            offering_conditions.append(SubjectOffering.id.in_(offering_ids))
        department_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("department")
            if scope.scope_reference_id is not None
        )
        if department_ids:
            offering_conditions.append(
                SubjectOffering.subject_id.in_(
                    select(Subject.id).where(
                        Subject.tenant_id == self.actor.tenant_id,
                        Subject.department_id.in_(department_ids),
                    )
                )
            )
        section_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("section")
            if scope.scope_reference_id is not None
        )
        if section_ids:
            offering_conditions.append(SubjectOffering.section_id.in_(section_ids))
        batch_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("batch")
            if scope.scope_reference_id is not None
        )
        if batch_ids:
            offering_conditions.append(
                SubjectOffering.section_id.in_(
                    select(Section.id).where(
                        Section.tenant_id == self.actor.tenant_id,
                        Section.batch_id.in_(batch_ids),
                    )
                )
            )
        if not offering_conditions:
            return query.where(false())
        scoped_offering_ids = select(SubjectOffering.id).where(
            SubjectOffering.tenant_id == self.actor.tenant_id,
            or_(*offering_conditions),
        )
        return query.where(
            ClassSession.period_id.in_(
                select(TimetablePeriod.id).where(
                    TimetablePeriod.tenant_id == self.actor.tenant_id,
                    TimetablePeriod.offering_id.in_(scoped_offering_ids),
                )
            )
        )

    def _scoped_record_ids(self):
        """Select attendance records visible to the authenticated actor."""

        query = select(AttendanceRecord.id).where(
            AttendanceRecord.tenant_id == self.actor.tenant_id
        )
        if self.actor.scopes_of_type("institution"):
            return query
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            return query.where(AttendanceRecord.student_id.in_(student_ids))
        return query.where(
            AttendanceRecord.session_id.in_(self._scoped_session_ids()),
            AttendanceRecord.student_id.in_(
                StudentsService(self.session, self.actor).scoped_student_ids_query()
            ),
        )

    def _get_scoped_session(self, session_id: UUID) -> ClassSession | None:
        """Return one class session only when it is visible through actor scope."""

        return self.session.scalar(
            select(ClassSession).where(
                ClassSession.tenant_id == self.actor.tenant_id,
                ClassSession.id == session_id,
                ClassSession.id.in_(self._scoped_session_ids()),
            )
        )

    def _student_is_visible(self, student_id: UUID) -> bool:
        """Return whether the Student domain grants this actor access to one student."""

        return StudentsService(self.session, self.actor).get_student(student_id) is not None

    def list_records(self, skip: int = 0, limit: int = 100, session_id: UUID | None = None):
        """List attendance records with optional class session filter."""

        query = select(AttendanceRecord).where(
            AttendanceRecord.tenant_id == self.actor.tenant_id,
            AttendanceRecord.id.in_(self._scoped_record_ids()),
        )
        if session_id is not None:
            query = query.where(AttendanceRecord.session_id == session_id)
        query = query.order_by(AttendanceRecord.created_at.desc())
        return self._paginate(query, skip, limit)

    def get_record(self, record_id: UUID) -> AttendanceRecord | None:
        """Return one attendance record by ID for the current tenant."""

        query = select(AttendanceRecord).where(
                AttendanceRecord.tenant_id == self.actor.tenant_id,
                AttendanceRecord.id == record_id,
                AttendanceRecord.id.in_(self._scoped_record_ids()),
            )
        return self.session.scalar(query)

    def create_record(self, payload: AttendanceRecordCreate) -> AttendanceRecord:
        """Create one attendance record for one session and student pair."""

        session_row = self._get_scoped_session(payload.session_id)
        if session_row is None:
            raise AttendanceValidationError(INVALID_SESSION_REFERENCE)
        if not self._student_is_visible(payload.student_id):
            raise AttendanceValidationError("Invalid student_id reference")
        if session_row.state == "locked":
            raise AttendanceConflictError("Attendance is locked for this session")

        record = AttendanceRecord(
            tenant_id=self.actor.tenant_id,
            session_id=payload.session_id,
            student_id=payload.student_id,
            status=payload.status,
            state=payload.state,
        )
        self.session.add(record)
        self.session.flush()
        self._audit("attendance.record.create", "attendance_record", record.id, {"state": record.state})
        return record

    def update_record(self, record_id: UUID, payload: AttendanceRecordUpdate) -> AttendanceRecord | None:
        """Update mutable attendance fields when session is not locked."""

        record = self.get_record(record_id)
        if record is None:
            return None
        session_row = self.session.scalar(
            select(ClassSession).where(
                ClassSession.tenant_id == self.actor.tenant_id,
                ClassSession.id == record.session_id,
            )
        )
        if session_row is None:
            raise AttendanceValidationError("Invalid session for attendance record")
        if session_row.state == "locked" or record.state == "locked":
            raise AttendanceConflictError("Attendance record is locked")

        changes: dict[str, object] = {}
        if payload.status is not None and payload.status != record.status:
            changes["status"] = {"from": record.status, "to": payload.status}
            record.status = payload.status
        if payload.state is not None and payload.state != record.state:
            if payload.state == "locked":
                raise AttendanceValidationError("Use session lock endpoint to lock attendance")
            changes["state"] = {"from": record.state, "to": payload.state}
            record.state = payload.state

        if changes:
            self.session.flush()
            self._audit("attendance.record.update", "attendance_record", record.id, changes)
        return record

    def submit_attendance(self, payload: AttendanceSubmitRequest) -> int:
        """Upsert submitted attendance records for one class session."""

        session_row = self._get_scoped_session(payload.session_id)
        if session_row is None:
            raise AttendanceValidationError(INVALID_SESSION_REFERENCE)
        if session_row.state == "locked":
            raise AttendanceConflictError("Attendance is locked for this session")

        submitted_count = 0
        for requested in payload.records:
            if requested.session_id != payload.session_id:
                raise AttendanceValidationError("All records must target payload session_id")
            if not self._student_is_visible(requested.student_id):
                raise AttendanceValidationError("Invalid student_id reference")
            existing = self.session.scalar(
                select(AttendanceRecord).where(
                    AttendanceRecord.tenant_id == self.actor.tenant_id,
                    AttendanceRecord.session_id == payload.session_id,
                    AttendanceRecord.student_id == requested.student_id,
                )
            )
            if existing is None:
                self.session.add(
                    AttendanceRecord(
                        tenant_id=self.actor.tenant_id,
                        session_id=payload.session_id,
                        student_id=requested.student_id,
                        status=requested.status,
                        state="submitted",
                    )
                )
            else:
                if existing.state == "locked":
                    raise AttendanceConflictError("One or more records are locked")
                existing.status = requested.status
                existing.state = "submitted"
            submitted_count += 1

        session_row.state = "submitted"
        self.session.flush()
        self._audit(
            "attendance.session.submit",
            "class_session",
            session_row.id,
            {"submitted_count": submitted_count},
        )
        return submitted_count

    def lock_session_attendance(self, session_id: UUID) -> int:
        """Lock all submitted attendance records for one class session."""

        session_row = self._get_scoped_session(session_id)
        if session_row is None:
            raise AttendanceValidationError(INVALID_SESSION_REFERENCE)
        if session_row.state == "locked":
            return 0

        records = list(
            self.session.scalars(
                select(AttendanceRecord).where(
                    AttendanceRecord.tenant_id == self.actor.tenant_id,
                    AttendanceRecord.session_id == session_id,
                )
            )
        )
        for record in records:
            record.state = "locked"
        session_row.state = "locked"
        self.session.flush()
        self._audit(
            "attendance.session.lock",
            "class_session",
            session_row.id,
            {"locked_count": len(records)},
        )
        return len(records)

    def list_corrections(self, skip: int = 0, limit: int = 100):
        """List attendance correction requests for the current tenant."""

        query = (
            select(AttendanceCorrection)
            .where(
                AttendanceCorrection.tenant_id == self.actor.tenant_id,
                AttendanceCorrection.record_id.in_(self._scoped_record_ids()),
            )
            .order_by(AttendanceCorrection.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def get_correction(self, correction_id: UUID) -> AttendanceCorrection | None:
        """Return one attendance correction request by ID."""

        return self.session.scalar(
            select(AttendanceCorrection).where(
                AttendanceCorrection.tenant_id == self.actor.tenant_id,
                AttendanceCorrection.id == correction_id,
                AttendanceCorrection.record_id.in_(self._scoped_record_ids()),
            )
        )

    def request_correction(self, payload: AttendanceCorrectionCreate) -> AttendanceCorrection:
        """Create one attendance correction request on an existing record."""

        record = self.get_record(payload.record_id)
        if record is None:
            raise AttendanceValidationError("Invalid record_id reference")
        if record.state != "locked":
            raise AttendanceConflictError("Only locked attendance records can be corrected")
        if record.status == payload.requested_status:
            raise AttendanceValidationError("requested_status must change the attendance outcome")
        correction = AttendanceCorrection(
            tenant_id=self.actor.tenant_id,
            record_id=payload.record_id,
            original_status=record.status,
            requested_status=payload.requested_status,
            reason=payload.reason,
            state="requested",
        )
        self.session.add(correction)
        self.session.flush()
        self._audit(
            "attendance.correction.request",
            "attendance_correction",
            correction.id,
            {"record_id": str(correction.record_id)},
        )
        return correction

    def review_correction(
        self,
        correction_id: UUID,
        payload: AttendanceCorrectionReview,
    ) -> AttendanceCorrection | None:
        """Approve or reject one attendance correction request."""

        correction = self.get_correction(correction_id)
        if correction is None:
            return None
        if correction.state != "requested":
            raise AttendanceConflictError("Correction request is already reviewed")
        if payload.state == "approved":
            record = self.get_record(correction.record_id)
            if record is None:
                raise AttendanceValidationError("Correction attendance record no longer exists")
            if correction.original_status is None or correction.requested_status is None:
                raise AttendanceConflictError("Legacy correction has no requested attendance outcome")
            if record.status != correction.original_status:
                raise AttendanceConflictError("Attendance outcome changed after this request")
            record.status = correction.requested_status
        correction.state = payload.state
        correction.reviewed_by_membership_id = self.actor.membership_id
        correction.reviewed_at = datetime.now(UTC)
        self.session.flush()
        self._audit(
            "attendance.correction.review",
            "attendance_correction",
            correction.id,
            {
                "state": payload.state,
                "original_status": correction.original_status,
                "requested_status": correction.requested_status,
            },
        )
        return correction

    def list_leave_requests(self, skip: int = 0, limit: int = 100):
        """List leave requests for the current tenant."""

        query = (
            select(LeaveRequest)
            .where(
                LeaveRequest.tenant_id == self.actor.tenant_id,
                LeaveRequest.person_id.in_(
                    StudentsService(self.session, self.actor).scoped_person_ids_query()
                ),
            )
            .order_by(LeaveRequest.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def get_leave_request(self, leave_id: UUID) -> LeaveRequest | None:
        """Return one leave request by ID for the current tenant."""

        return self.session.scalar(
            select(LeaveRequest).where(
                LeaveRequest.tenant_id == self.actor.tenant_id,
                LeaveRequest.id == leave_id,
                LeaveRequest.person_id.in_(
                    StudentsService(self.session, self.actor).scoped_person_ids_query()
                ),
            )
        )

    def create_leave_request(self, payload: LeaveRequestCreate) -> LeaveRequest:
        """Create one leave request for one person and date range."""

        leave = LeaveRequest(
            tenant_id=self.actor.tenant_id,
            person_id=payload.person_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            leave_type=payload.leave_type,
            reason=payload.reason,
            state="requested",
        )
        self.session.add(leave)
        self.session.flush()
        self._audit("attendance.leave.request", "leave_request", leave.id, {"leave_type": leave.leave_type})
        return leave

    def update_leave_request(self, leave_id: UUID, payload: LeaveRequestUpdate) -> LeaveRequest | None:
        """Update mutable leave request details prior to approval."""

        leave = self.get_leave_request(leave_id)
        if leave is None:
            return None
        if leave.state == "approved":
            raise AttendanceConflictError("Approved leave requests cannot be modified")

        next_start = payload.start_date or leave.start_date
        next_end = payload.end_date or leave.end_date
        if next_end < next_start:
            raise AttendanceValidationError("end_date must be on or after start_date")

        changes: dict[str, object] = {}
        if payload.start_date is not None and payload.start_date != leave.start_date:
            changes["start_date"] = {"from": str(leave.start_date), "to": str(payload.start_date)}
            leave.start_date = payload.start_date
        if payload.end_date is not None and payload.end_date != leave.end_date:
            changes["end_date"] = {"from": str(leave.end_date), "to": str(payload.end_date)}
            leave.end_date = payload.end_date
        if payload.leave_type is not None and payload.leave_type != leave.leave_type:
            changes["leave_type"] = {"from": leave.leave_type, "to": payload.leave_type}
            leave.leave_type = payload.leave_type
        if payload.reason is not None and payload.reason != leave.reason:
            changes["reason"] = {"from": leave.reason, "to": payload.reason}
            leave.reason = payload.reason
        if payload.state is not None and payload.state != leave.state:
            if payload.state not in {"requested", "cancelled"}:
                raise AttendanceValidationError("state can only be requested or cancelled in this endpoint")
            changes["state"] = {"from": leave.state, "to": payload.state}
            leave.state = payload.state

        if changes:
            self.session.flush()
            self._audit("attendance.leave.update", "leave_request", leave.id, changes)
        return leave

    def approve_leave(self, leave_id: UUID, payload: LeaveApproval) -> LeaveRequest | None:
        """Approve or reject one leave request."""

        leave = self.get_leave_request(leave_id)
        if leave is None:
            return None
        if leave.state not in {"requested", "rejected"}:
            raise AttendanceConflictError("Leave request is not in an approvable state")

        leave.state = payload.state
        leave.approved_by_membership_id = self.actor.membership_id
        leave.approved_at = datetime.now(UTC)
        self.session.flush()
        self._audit(
            "attendance.leave.approve",
            "leave_request",
            leave.id,
            {"state": payload.state},
        )
        return leave

    def attendance_summary(self, student_id: UUID) -> dict[str, bool | int | float | UUID]:
        """Compute attendance summary from submitted and locked sessions only."""

        if not self._student_is_visible(student_id):
            raise AttendanceDomainError("Student not found", 404)
        result = self.session.execute(
            select(
                func.count(AttendanceRecord.id).label("eligible_sessions"),
                func.coalesce(
                    func.sum(case((AttendanceRecord.status == "present", 1), else_=0)),
                    0,
                ).label("present_sessions"),
                func.coalesce(
                    func.sum(case((AttendanceRecord.status == "absent", 1), else_=0)),
                    0,
                ).label("absent_sessions"),
                func.coalesce(
                    func.sum(case((AttendanceRecord.status == "late", 1), else_=0)),
                    0,
                ).label("late_sessions"),
                func.coalesce(
                    func.sum(case((AttendanceRecord.status == "excused", 1), else_=0)),
                    0,
                ).label("excused_sessions"),
            )
            .join(
                ClassSession,
                (ClassSession.tenant_id == AttendanceRecord.tenant_id)
                & (ClassSession.id == AttendanceRecord.session_id),
            )
            .where(
                AttendanceRecord.tenant_id == self.actor.tenant_id,
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.state.in_(("submitted", "locked")),
                ClassSession.state.in_(("submitted", "locked")),
            )
        ).one()

        eligible = int(result.eligible_sessions or 0)
        present = int(result.present_sessions or 0)
        absent = int(result.absent_sessions or 0)
        late = int(result.late_sessions or 0)
        excused = int(result.excused_sessions or 0)
        percentage = round((present / eligible) * 100, 2) if eligible > 0 else 0.0
        shortage = round(max(0.0, DEFAULT_ATTENDANCE_THRESHOLD_PERCENTAGE - percentage), 2)

        return {
            "student_id": student_id,
            "eligible_sessions": eligible,
            "present_sessions": present,
            "absent_sessions": absent,
            "late_sessions": late,
            "excused_sessions": excused,
            "attendance_percentage": percentage,
            "threshold_percentage": DEFAULT_ATTENDANCE_THRESHOLD_PERCENTAGE,
            "shortage_percentage_points": shortage,
            "exam_eligible": eligible > 0 and shortage == 0,
        }
