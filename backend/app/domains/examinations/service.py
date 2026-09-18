"""Business logic for tenant-safe examinations configuration and result workflows."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import false, func, or_, select, text
from sqlalchemy.orm import Session

from app.domains.academics.models import CollegeSetting, Program, Room, Section, Subject, Term
from app.domains.audit.models import AuditEvent
from app.domains.delivery.models import FacultyProfile, SubjectOffering
from app.domains.examinations.models import (
    AssessmentScheme,
    ExamRegistration,
    ExamSchedule,
    ExamSeatAllocation,
    ExamSession,
    GradeCardIssuance,
    GradeRule,
    HallTicketIssuance,
    InvigilationAssignment,
    MarkAdjustment,
    MarkEntry,
    PublishedResult,
    PublishedResultLine,
    ResultPublicationEvent,
    TranscriptIssuance,
)
from app.domains.examinations.schemas import (
    AssessmentSchemeCreate,
    ExamRegistrationCreate,
    ExamScheduleCreate,
    ExamSeatAllocationCreate,
    ExamSessionCreate,
    GradeCardDocument,
    GradeCardDocumentLine,
    GradeRuleCreate,
    HallTicketDocument,
    HallTicketDocumentExam,
    InvigilationAssignmentCreate,
    MarkAdjustmentCreate,
    MarkAdjustmentReview,
    MarkEntryUpsert,
    ResultReopenRequest,
    TranscriptDocument,
    TranscriptDocumentResult,
)
from app.domains.students.models import Person, Student, StudentEnrollment
from app.domains.tenancy.models import Tenant
from app.security_context import ActorContext, resolve_actor_student_ids


class ExaminationsDomainError(Exception):
    """Domain error carrying HTTP translation metadata."""

    def __init__(self, detail: str, status_code: int) -> None:
        """Initialize the error with client-safe detail and HTTP status."""

        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class ExaminationsValidationError(ExaminationsDomainError):
    """Validation error mapped to HTTP 422."""

    def __init__(self, detail: str) -> None:
        """Initialize an examinations validation error."""

        super().__init__(detail, 422)


class ExaminationsConflictError(ExaminationsDomainError):
    """Conflict error mapped to HTTP 409."""

    def __init__(self, detail: str) -> None:
        """Initialize an examinations conflict error."""

        super().__init__(detail, 409)


class ExaminationsService:
    """Manage assessments, sessions, schedules, marks, and published results."""

    def __init__(self, session: Session, actor: ActorContext) -> None:
        """Initialize the service and scope its session to the actor's tenant."""

        self.session = session
        self.actor = actor
        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(actor.tenant_id)},
        )

    def _paginate(self, query, skip: int, limit: int):
        """Return one page of query results and the unpaginated total."""

        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        return list(self.session.scalars(query.offset(skip).limit(limit))), total

    def _audit(self, action: str, entity: str, entity_id: UUID, details: dict[str, object]) -> None:
        """Stage a tenant-scoped audit event for the current transaction."""

        self.session.add(
            AuditEvent(
                tenant_id=self.actor.tenant_id,
                account_id=self.actor.account_id,
                membership_id=self.actor.membership_id,
                action=action,
                entity_type=entity,
                entity_id=entity_id,
                details=details,
            )
        )

    def _scoped_registration_ids(self):
        """Select exam registrations visible through the actor's academic scopes."""

        query = select(ExamRegistration.id).where(
            ExamRegistration.tenant_id == self.actor.tenant_id
        )
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            return query.where(ExamRegistration.student_id.in_(student_ids))
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
            ExamRegistration.schedule_id.in_(
                select(ExamSchedule.id).where(
                    ExamSchedule.tenant_id == self.actor.tenant_id,
                    ExamSchedule.offering_id.in_(scoped_offering_ids),
                )
            )
        )

    def _require_scoped_registration(self, registration_id: UUID) -> ExamRegistration:
        """Return one registration only when it belongs to the actor's academic scope."""

        registration = self.session.scalar(
            select(ExamRegistration).where(
                ExamRegistration.tenant_id == self.actor.tenant_id,
                ExamRegistration.id == registration_id,
                ExamRegistration.id.in_(self._scoped_registration_ids()),
            )
        )
        if registration is None:
            raise ExaminationsValidationError("Invalid registration_id reference")
        return registration

    def _require(self, model, id_: UUID, label: str):
        """Return a tenant-owned row or raise a labeled validation error."""

        row = self.session.scalar(select(model).where(model.tenant_id == self.actor.tenant_id, model.id == id_))
        if row is None:
            raise ExaminationsValidationError(f"Invalid {label} reference")
        return row

    def _document_number(self, prefix: str) -> str:
        """Generate one collision-resistant tenant document reference."""

        stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
        membership = str(self.actor.membership_id).split("-")[0].upper()
        return f"{prefix}-{stamp}-{membership}"

    def _document_branding(self) -> tuple[str, str, str, str]:
        """Return authoritative tenant and college-setting document branding."""

        tenant = self.session.scalar(select(Tenant).where(Tenant.id == self.actor.tenant_id))
        if tenant is None:
            raise ExaminationsValidationError("Tenant branding is unavailable")
        setting = self.session.scalar(
            select(CollegeSetting).where(CollegeSetting.tenant_id == self.actor.tenant_id)
        )
        return (
            setting.institution_name if setting else tenant.display_name,
            (setting.short_name if setting else None) or tenant.short_name,
            tenant.primary_color,
            tenant.accent_color,
        )

    def _student_identity(self, student_id: UUID) -> tuple[Student, Person]:
        """Return one tenant Student and canonical Person identity."""

        row = self.session.execute(
            select(Student, Person)
            .join(
                Person,
                (Person.tenant_id == Student.tenant_id) & (Person.id == Student.person_id),
            )
            .where(
                Student.tenant_id == self.actor.tenant_id,
                Student.id == student_id,
            )
        ).one_or_none()
        if row is None:
            raise ExaminationsValidationError("Invalid student_id reference")
        return row

    def list_assessment_schemes(self, skip: int = 0, limit: int = 100):
        """List assessment schemes for the actor's tenant."""

        query = select(AssessmentScheme).where(AssessmentScheme.tenant_id == self.actor.tenant_id)
        return self._paginate(query.order_by(AssessmentScheme.created_at.desc()), skip, limit)

    def create_assessment_scheme(self, payload: AssessmentSchemeCreate) -> AssessmentScheme:
        """Create an assessment scheme after validating academic references."""

        if payload.pass_marks > payload.max_marks:
            raise ExaminationsValidationError("pass_marks must be less than or equal to max_marks")
        self._require(Subject, payload.subject_id, "subject_id")
        self._require(Program, payload.program_id, "program_id")
        self._require(Term, payload.term_id, "term_id")
        item = AssessmentScheme(tenant_id=self.actor.tenant_id, **payload.model_dump())
        self.session.add(item)
        self.session.flush()
        self._audit("examinations.assessment_scheme.create", "assessment_scheme", item.id, {})
        return item

    def list_grade_rules(self, skip: int = 0, limit: int = 100):
        """List versioned grade bands for the actor's tenant."""

        query = select(GradeRule).where(GradeRule.tenant_id == self.actor.tenant_id)
        return self._paginate(query.order_by(GradeRule.version.desc(), GradeRule.min_percentage.desc()), skip, limit)

    def create_grade_rule(self, payload: GradeRuleCreate) -> GradeRule:
        """Create one non-overlapping versioned grade band."""

        if payload.min_percentage > payload.max_percentage:
            raise ExaminationsValidationError("min_percentage must be <= max_percentage")
        self._require(Term, payload.term_id, "term_id")
        overlapping = self.session.scalar(
            select(GradeRule.id).where(
                GradeRule.tenant_id == self.actor.tenant_id,
                GradeRule.term_id == payload.term_id,
                GradeRule.version == payload.version,
                GradeRule.min_percentage <= payload.max_percentage,
                GradeRule.max_percentage >= payload.min_percentage,
            )
        )
        if overlapping is not None:
            raise ExaminationsConflictError("Grade percentage band overlaps an existing rule version")
        item = GradeRule(tenant_id=self.actor.tenant_id, **payload.model_dump())
        self.session.add(item)
        self.session.flush()
        self._audit("examinations.grade_rule.create", "grade_rule", item.id, {"version": item.version})
        return item

    def list_exam_sessions(self, skip: int = 0, limit: int = 100):
        """List exam sessions for the actor's tenant."""

        query = select(ExamSession).where(ExamSession.tenant_id == self.actor.tenant_id)
        return self._paginate(query.order_by(ExamSession.created_at.desc()), skip, limit)

    def create_exam_session(self, payload: ExamSessionCreate) -> ExamSession:
        """Create an exam session for a valid tenant term."""

        self._require(Term, payload.term_id, "term_id")
        item = ExamSession(tenant_id=self.actor.tenant_id, **payload.model_dump())
        self.session.add(item)
        self.session.flush()
        self._audit("examinations.session.create", "exam_session", item.id, {"state": item.state})
        return item

    def list_exam_schedules(self, skip: int = 0, limit: int = 100, session_id: UUID | None = None):
        """List exam schedules with an optional session filter."""

        query = select(ExamSchedule).where(ExamSchedule.tenant_id == self.actor.tenant_id)
        if session_id is not None:
            query = query.where(ExamSchedule.session_id == session_id)
        return self._paginate(query.order_by(ExamSchedule.exam_date.asc()), skip, limit)

    def create_exam_schedule(self, payload: ExamScheduleCreate) -> ExamSchedule:
        """Create a schedule after validating term, offering, and room references."""

        session_row = self._require(ExamSession, payload.session_id, "session_id")
        offering = self._require(SubjectOffering, payload.offering_id, "offering_id")
        if offering.term_id != session_row.term_id:
            raise ExaminationsValidationError("offering_id term must match exam session term")
        if payload.room_id is not None:
            self._require(Room, payload.room_id, "room_id")
        item = ExamSchedule(tenant_id=self.actor.tenant_id, **payload.model_dump())
        self.session.add(item)
        self.session.flush()
        self._audit("examinations.schedule.create", "exam_schedule", item.id, {})
        return item

    def list_exam_registrations(self, skip: int = 0, limit: int = 100, schedule_id: UUID | None = None):
        """List exam registrations with an optional schedule filter."""

        query = select(ExamRegistration).where(
            ExamRegistration.tenant_id == self.actor.tenant_id,
            ExamRegistration.id.in_(self._scoped_registration_ids()),
        )
        if schedule_id is not None:
            query = query.where(ExamRegistration.schedule_id == schedule_id)
        return self._paginate(query.order_by(ExamRegistration.created_at.desc()), skip, limit)

    def create_exam_registration(self, payload: ExamRegistrationCreate) -> ExamRegistration:
        """Register a tenant student for a valid exam schedule."""

        self._require(Student, payload.student_id, "student_id")
        self._require(ExamSchedule, payload.schedule_id, "schedule_id")
        item = ExamRegistration(tenant_id=self.actor.tenant_id, **payload.model_dump())
        self.session.add(item)
        self.session.flush()
        self._audit("examinations.registration.create", "exam_registration", item.id, {})
        return item

    def list_seat_allocations(self, skip: int = 0, limit: int = 100):
        """List examination seat allocations for the actor's tenant."""

        query = select(ExamSeatAllocation).where(ExamSeatAllocation.tenant_id == self.actor.tenant_id)
        return self._paginate(query.order_by(ExamSeatAllocation.created_at.desc()), skip, limit)

    def allocate_seat(self, payload: ExamSeatAllocationCreate) -> ExamSeatAllocation:
        """Assign an eligible registration to an available room seat."""

        registration = self._require(ExamRegistration, payload.registration_id, "registration_id")
        if registration.eligibility != "eligible":
            raise ExaminationsConflictError("Only eligible registrations can receive hall seats")
        schedule = self._require(ExamSchedule, registration.schedule_id, "schedule_id")
        room = self._require(Room, payload.room_id, "room_id")
        allocated_count = self.session.scalar(
            select(func.count()).select_from(ExamSeatAllocation).where(
                ExamSeatAllocation.tenant_id == self.actor.tenant_id,
                ExamSeatAllocation.schedule_id == schedule.id,
                ExamSeatAllocation.room_id == room.id,
            )
        ) or 0
        if room.capacity is not None and allocated_count >= room.capacity:
            raise ExaminationsConflictError("Exam room capacity has been reached")
        item = ExamSeatAllocation(
            tenant_id=self.actor.tenant_id,
            schedule_id=schedule.id,
            registration_id=registration.id,
            room_id=room.id,
            seat_number=payload.seat_number,
        )
        self.session.add(item)
        self.session.flush()
        self._audit("examinations.seat.allocate", "exam_seat_allocation", item.id, {})
        return item

    def get_hall_ticket(self, registration_id: UUID) -> dict[str, object]:
        """Derive one hall ticket from registration, schedule, and seat sources."""

        registration = self._require_scoped_registration(registration_id)
        schedule = self._require(ExamSchedule, registration.schedule_id, "schedule_id")
        seat = self.session.scalar(
            select(ExamSeatAllocation).where(
                ExamSeatAllocation.tenant_id == self.actor.tenant_id,
                ExamSeatAllocation.registration_id == registration.id,
            )
        )
        return {
            "registration_id": registration.id,
            "student_id": registration.student_id,
            "schedule_id": schedule.id,
            "exam_date": schedule.exam_date,
            "room_id": seat.room_id if seat else schedule.room_id,
            "seat_number": seat.seat_number if seat else None,
            "eligibility": registration.eligibility,
        }

    def issue_hall_ticket(self, registration_id: UUID) -> HallTicketIssuance:
        """Issue one hall ticket per Student exam session and return it on replay."""

        registration = self._require_scoped_registration(registration_id)
        if registration.eligibility != "eligible":
            raise ExaminationsConflictError("Only eligible registrations can receive hall tickets")
        schedule = self._require(ExamSchedule, registration.schedule_id, "schedule_id")
        existing = self.session.scalar(
            select(HallTicketIssuance).where(
                HallTicketIssuance.tenant_id == self.actor.tenant_id,
                HallTicketIssuance.student_id == registration.student_id,
                HallTicketIssuance.session_id == schedule.session_id,
            )
        )
        if existing is not None:
            return existing
        registration_ids = list(
            self.session.scalars(
                select(ExamRegistration.id)
                .join(
                    ExamSchedule,
                    (ExamSchedule.tenant_id == ExamRegistration.tenant_id)
                    & (ExamSchedule.id == ExamRegistration.schedule_id),
                )
                .where(
                    ExamRegistration.tenant_id == self.actor.tenant_id,
                    ExamRegistration.student_id == registration.student_id,
                    ExamRegistration.eligibility == "eligible",
                    ExamSchedule.session_id == schedule.session_id,
                )
                .order_by(ExamSchedule.exam_date, ExamRegistration.id)
            )
        )
        issuance = HallTicketIssuance(
            tenant_id=self.actor.tenant_id,
            student_id=registration.student_id,
            session_id=schedule.session_id,
            ticket_number=self._document_number("HT"),
            registration_ids=[str(item) for item in registration_ids],
            issued_at=datetime.now(UTC),
            issued_by_membership_id=self.actor.membership_id,
        )
        self.session.add(issuance)
        self.session.flush()
        self._audit(
            "examinations.hall_ticket.issue",
            "hall_ticket_issuance",
            issuance.id,
            {"ticket_number": issuance.ticket_number, "registrations": len(registration_ids)},
        )
        return issuance

    def get_hall_ticket_document(self, registration_id: UUID) -> HallTicketDocument | None:
        """Derive one printable hall ticket from an authorized issuance manifest."""

        registration = self._require_scoped_registration(registration_id)
        schedule = self._require(ExamSchedule, registration.schedule_id, "schedule_id")
        issuance = self.session.scalar(
            select(HallTicketIssuance).where(
                HallTicketIssuance.tenant_id == self.actor.tenant_id,
                HallTicketIssuance.student_id == registration.student_id,
                HallTicketIssuance.session_id == schedule.session_id,
            )
        )
        if issuance is None:
            return None
        registration_ids = [UUID(item) for item in issuance.registration_ids]
        room_id = func.coalesce(ExamSeatAllocation.room_id, ExamSchedule.room_id)
        rows = list(
            self.session.execute(
                select(
                    ExamRegistration,
                    ExamSchedule,
                    Subject,
                    ExamSeatAllocation,
                    Room,
                )
                .join(
                    ExamSchedule,
                    (ExamSchedule.tenant_id == ExamRegistration.tenant_id)
                    & (ExamSchedule.id == ExamRegistration.schedule_id),
                )
                .join(
                    SubjectOffering,
                    (SubjectOffering.tenant_id == ExamSchedule.tenant_id)
                    & (SubjectOffering.id == ExamSchedule.offering_id),
                )
                .join(
                    Subject,
                    (Subject.tenant_id == SubjectOffering.tenant_id)
                    & (Subject.id == SubjectOffering.subject_id),
                )
                .outerjoin(
                    ExamSeatAllocation,
                    (ExamSeatAllocation.tenant_id == ExamRegistration.tenant_id)
                    & (ExamSeatAllocation.registration_id == ExamRegistration.id),
                )
                .outerjoin(
                    Room,
                    (Room.tenant_id == ExamRegistration.tenant_id) & (Room.id == room_id),
                )
                .where(
                    ExamRegistration.tenant_id == self.actor.tenant_id,
                    ExamRegistration.id.in_(registration_ids),
                )
                .order_by(ExamSchedule.exam_date, Subject.code)
            )
        )
        student, person = self._student_identity(issuance.student_id)
        session = self._require(ExamSession, issuance.session_id, "session_id")
        term = self._require(Term, session.term_id, "term_id")
        institution_name, short_name, primary_color, accent_color = self._document_branding()
        exams = [
            HallTicketDocumentExam(
                registration_id=row.ExamRegistration.id,
                subject_code=row.Subject.code,
                subject_name=row.Subject.name,
                exam_date=row.ExamSchedule.exam_date,
                room_code=row.Room.code if row.Room else None,
                room_name=row.Room.name if row.Room else None,
                seat_number=(
                    row.ExamSeatAllocation.seat_number if row.ExamSeatAllocation else None
                ),
            )
            for row in rows
        ]
        return HallTicketDocument(
            issuance_id=issuance.id,
            ticket_number=issuance.ticket_number,
            verification_reference=issuance.ticket_number,
            issued_at=issuance.issued_at,
            issued_by_membership_id=issuance.issued_by_membership_id,
            institution_name=institution_name,
            institution_short_name=short_name,
            primary_color=primary_color,
            accent_color=accent_color,
            student_id=student.id,
            student_name=person.full_name,
            registration_number=student.registration_number,
            session_id=session.id,
            term_name=term.display_name,
            exams=exams,
        )

    def list_invigilation_assignments(self, skip: int = 0, limit: int = 100):
        """List invigilation assignments for the actor's tenant."""

        query = select(InvigilationAssignment).where(
            InvigilationAssignment.tenant_id == self.actor.tenant_id
        )
        return self._paginate(query.order_by(InvigilationAssignment.created_at.desc()), skip, limit)

    def assign_invigilator(self, payload: InvigilationAssignmentCreate) -> InvigilationAssignment:
        """Assign a tenant faculty member to one scheduled examination room."""

        self._require(ExamSchedule, payload.schedule_id, "schedule_id")
        self._require(FacultyProfile, payload.faculty_id, "faculty_id")
        self._require(Room, payload.room_id, "room_id")
        item = InvigilationAssignment(tenant_id=self.actor.tenant_id, **payload.model_dump())
        self.session.add(item)
        self.session.flush()
        self._audit("examinations.invigilation.assign", "invigilation_assignment", item.id, {})
        return item

    def list_mark_adjustments(self, skip: int = 0, limit: int = 100):
        """List moderation and revaluation requests for the actor's tenant."""

        query = select(MarkAdjustment).where(MarkAdjustment.tenant_id == self.actor.tenant_id)
        return self._paginate(query.order_by(MarkAdjustment.created_at.desc()), skip, limit)

    def request_mark_adjustment(self, payload: MarkAdjustmentCreate) -> MarkAdjustment:
        """Request revised marks while preserving the locked source entry."""

        mark = self.get_mark_entry_by_registration(payload.registration_id)
        if mark is None or mark.state != "locked":
            raise ExaminationsConflictError("Only locked marks can be adjusted")
        registration = self._require(ExamRegistration, payload.registration_id, "registration_id")
        schedule = self._require(ExamSchedule, registration.schedule_id, "schedule_id")
        if payload.revised_marks > schedule.max_marks:
            raise ExaminationsValidationError("revised_marks must be <= schedule max_marks")
        pending = self.session.scalar(
            select(MarkAdjustment.id).where(
                MarkAdjustment.tenant_id == self.actor.tenant_id,
                MarkAdjustment.registration_id == registration.id,
                MarkAdjustment.state == "requested",
            )
        )
        if pending is not None:
            raise ExaminationsConflictError("A mark adjustment is already awaiting review")
        item = MarkAdjustment(
            tenant_id=self.actor.tenant_id,
            registration_id=registration.id,
            original_marks=mark.marks_obtained,
            revised_marks=payload.revised_marks,
            reason=payload.reason,
            state="requested",
            requested_by_membership_id=self.actor.membership_id,
        )
        self.session.add(item)
        self.session.flush()
        self._audit("examinations.mark_adjustment.request", "mark_adjustment", item.id, {})
        return item

    def review_mark_adjustment(self, adjustment_id: UUID, payload: MarkAdjustmentReview) -> MarkAdjustment:
        """Approve or reject one requested mark adjustment."""

        item = self._require(MarkAdjustment, adjustment_id, "adjustment_id")
        self._require_scoped_registration(item.registration_id)
        if item.state != "requested":
            raise ExaminationsConflictError("Only requested mark adjustments can be reviewed")
        item.state = payload.state
        item.reviewed_by_membership_id = self.actor.membership_id
        item.reviewed_at = datetime.now(UTC)
        self.session.flush()
        self._audit("examinations.mark_adjustment.review", "mark_adjustment", item.id, {"state": item.state})
        return item

    def get_mark_entry_by_registration(self, registration_id: UUID) -> MarkEntry | None:
        """Return the mark entry for a tenant exam registration."""

        return self.session.scalar(
            select(MarkEntry).where(
                MarkEntry.tenant_id == self.actor.tenant_id,
                MarkEntry.registration_id == registration_id,
                MarkEntry.registration_id.in_(self._scoped_registration_ids()),
            )
        )

    def enter_marks(self, registration_id: UUID, payload: MarkEntryUpsert) -> MarkEntry:
        """Create or update marks for an eligible unlocked registration."""

        registration = self._require_scoped_registration(registration_id)
        if registration.eligibility != "eligible":
            raise ExaminationsConflictError("Marks can be entered only for eligible registrations")
        schedule = self._require(ExamSchedule, registration.schedule_id, "schedule_id")
        if payload.marks_obtained > schedule.max_marks:
            raise ExaminationsValidationError("marks_obtained must be <= schedule max_marks")
        item = self.get_mark_entry_by_registration(registration_id)
        if item is None:
            item = MarkEntry(
                tenant_id=self.actor.tenant_id,
                registration_id=registration_id,
                marks_obtained=payload.marks_obtained,
                state="entered",
            )
            self.session.add(item)
        elif item.state != "entered":
            raise ExaminationsConflictError("Only marks in entered state can be modified")
        else:
            item.marks_obtained = payload.marks_obtained
        self.session.flush()
        return item

    def verify_marks(self, registration_id: UUID) -> MarkEntry:
        """Verify an entered mark record for later locking."""

        item = self.get_mark_entry_by_registration(registration_id)
        if item is None:
            raise ExaminationsValidationError("Marks not entered for registration")
        if item.state != "entered":
            raise ExaminationsConflictError("Only entered marks can be verified")
        item.state = "verified"
        item.verified_by_membership_id = self.actor.membership_id
        item.verified_at = datetime.now(UTC)
        self.session.flush()
        return item

    def lock_marks(self, registration_id: UUID) -> MarkEntry:
        """Lock a verified mark record idempotently."""

        item = self.get_mark_entry_by_registration(registration_id)
        if item is None:
            raise ExaminationsValidationError("Marks not entered for registration")
        if item.state == "locked":
            return item
        if item.state != "verified":
            raise ExaminationsConflictError("Only verified marks can be locked")
        item.state = "locked"
        item.locked_by_membership_id = self.actor.membership_id
        item.locked_at = datetime.now(UTC)
        self.session.flush()
        return item

    def list_published_results(self, skip: int = 0, limit: int = 100, session_id: UUID | None = None):
        """List published results with an optional exam-session filter."""

        query = select(PublishedResult).where(PublishedResult.tenant_id == self.actor.tenant_id)
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            query = query.where(PublishedResult.student_id.in_(student_ids))
        if session_id is not None:
            query = query.where(PublishedResult.session_id == session_id)
        return self._paginate(query.order_by(PublishedResult.created_at.desc()), skip, limit)

    def _resolve_grade(self, term_id: UUID, percentage: Decimal) -> tuple[str, Decimal]:
        """Resolve a grade from the latest published term rules or the legacy deterministic bands."""

        latest_version = self.session.scalar(
            select(func.max(GradeRule.version)).where(
                GradeRule.tenant_id == self.actor.tenant_id,
                GradeRule.term_id == term_id,
                GradeRule.state == "published",
            )
        )
        if latest_version is not None:
            rule = self.session.scalar(
                select(GradeRule).where(
                    GradeRule.tenant_id == self.actor.tenant_id,
                    GradeRule.term_id == term_id,
                    GradeRule.version == latest_version,
                    GradeRule.state == "published",
                    GradeRule.min_percentage <= percentage,
                    GradeRule.max_percentage >= percentage,
                )
            )
            if rule is None:
                raise ExaminationsValidationError("Published grade rules do not cover the calculated percentage")
            return rule.letter_grade, Decimal(rule.grade_point)
        if percentage >= Decimal(90):
            return "A+", Decimal("10.00")
        if percentage >= Decimal(80):
            return "A", Decimal("9.00")
        if percentage >= Decimal(60):
            return "B", Decimal("7.00")
        if percentage >= Decimal(50):
            return "C", Decimal("6.00")
        if percentage >= Decimal(40):
            return "D", Decimal("5.00")
        return "F", Decimal("0.00")

    def _calculate(self, session: ExamSession, student_id: UUID):
        """Calculate one student's aggregate result from locked marks."""

        term = self._require(Term, session.term_id, "term_id")
        enrollment = self.session.scalar(
            select(StudentEnrollment).where(
                StudentEnrollment.tenant_id == self.actor.tenant_id,
                StudentEnrollment.student_id == student_id,
                StudentEnrollment.academic_year_id == term.academic_year_id,
                StudentEnrollment.status == "active",
            )
        )
        if enrollment is None:
            raise ExaminationsValidationError("Active enrollment missing for student")

        rows = list(
            self.session.execute(
            select(ExamRegistration, ExamSchedule, SubjectOffering, MarkEntry, Subject, AssessmentScheme)
                .join(
                    ExamSchedule,
                    (ExamSchedule.tenant_id == ExamRegistration.tenant_id)
                    & (ExamSchedule.id == ExamRegistration.schedule_id),
                )
                .join(
                    SubjectOffering,
                    (SubjectOffering.tenant_id == ExamSchedule.tenant_id)
                    & (SubjectOffering.id == ExamSchedule.offering_id),
                )
                .outerjoin(
                    MarkEntry,
                    (MarkEntry.tenant_id == ExamRegistration.tenant_id)
                    & (MarkEntry.registration_id == ExamRegistration.id),
                )
                .join(
                    Subject,
                    (Subject.tenant_id == SubjectOffering.tenant_id)
                    & (Subject.id == SubjectOffering.subject_id),
                )
                .outerjoin(
                    AssessmentScheme,
                    (AssessmentScheme.tenant_id == SubjectOffering.tenant_id)
                    & (AssessmentScheme.term_id == session.term_id)
                    & (AssessmentScheme.subject_id == SubjectOffering.subject_id)
                    & (AssessmentScheme.program_id == enrollment.program_id),
                )
                .where(
                    ExamRegistration.tenant_id == self.actor.tenant_id,
                    ExamRegistration.student_id == student_id,
                    ExamRegistration.eligibility == "eligible",
                    ExamSchedule.session_id == session.id,
                )
            )
        )
        if len(rows) == 0:
            raise ExaminationsValidationError("No eligible registrations found for student in session")

        total_marks = Decimal("0.00")
        total_max = Decimal("0.00")
        all_passed = True
        registration_ids = [registration.id for registration, *_ in rows]
        adjustments = list(
            self.session.scalars(
                select(MarkAdjustment)
                .where(
                    MarkAdjustment.tenant_id == self.actor.tenant_id,
                    MarkAdjustment.registration_id.in_(registration_ids),
                    MarkAdjustment.state == "approved",
                )
                .order_by(MarkAdjustment.reviewed_at.desc())
            )
        )
        latest_adjustment: dict[UUID, MarkAdjustment] = {}
        for adjustment in adjustments:
            latest_adjustment.setdefault(adjustment.registration_id, adjustment)

        result_lines: list[dict[str, object]] = []
        weighted_points = Decimal("0.00")
        total_credits = 0
        for registration, schedule, _, mark_entry, subject, scheme in rows:
            if mark_entry is None or mark_entry.state != "locked":
                raise ExaminationsConflictError("All eligible registrations must have locked marks")
            if scheme is None:
                raise ExaminationsValidationError("Missing assessment scheme for one or more subjects")
            adjustment = latest_adjustment.get(registration.id)
            score = Decimal(adjustment.revised_marks if adjustment else mark_entry.marks_obtained)
            max_marks = Decimal(schedule.max_marks)
            subject_percentage = ((score / max_marks) * Decimal(100)).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
            subject_grade, grade_point = self._resolve_grade(session.term_id, subject_percentage)
            credits = subject.credits or 0
            total_marks += score
            total_max += max_marks
            if score < Decimal(scheme.pass_marks):
                all_passed = False
            weighted_points += grade_point * credits
            total_credits += credits
            result_lines.append(
                {
                    "registration_id": registration.id,
                    "subject_id": subject.id,
                    "marks_obtained": score,
                    "max_marks": max_marks,
                    "pass_marks": Decimal(scheme.pass_marks),
                    "credits": credits,
                    "grade": subject_grade,
                    "grade_point": grade_point,
                }
            )

        pct = ((total_marks / total_max) * Decimal(100)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        grade, fallback_point = self._resolve_grade(session.term_id, pct)
        gpa = (
            weighted_points / total_credits if total_credits > 0 else fallback_point
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        outcome = "pass" if all_passed and grade != "F" else "fail"
        return (
            total_marks.quantize(Decimal("0.01")),
            total_max.quantize(Decimal("0.01")),
            pct,
            grade,
            gpa,
            outcome,
            result_lines,
        )

    def _stage_result_snapshot(
        self,
        result: PublishedResult,
        event_type: str,
        lines: list[dict[str, object]],
        reason: str | None = None,
    ) -> None:
        """Stage immutable subject lines and one aggregate publication lifecycle snapshot."""

        if event_type != "reopened":
            for line in lines:
                self.session.add(
                    PublishedResultLine(
                        tenant_id=self.actor.tenant_id,
                        result_id=result.id,
                        publication_version=result.publication_version,
                        **line,
                    )
                )
        self.session.add(
            ResultPublicationEvent(
                tenant_id=self.actor.tenant_id,
                result_id=result.id,
                version=result.publication_version,
                event_type=event_type,
                reason=reason,
                snapshot={
                    "total_marks": str(result.total_marks),
                    "total_max_marks": str(result.total_max_marks),
                    "percentage": str(result.percentage),
                    "grade": result.grade,
                    "gpa": str(result.gpa),
                    "result": result.result,
                    "state": result.state,
                    "lines": [
                        {key: str(value) if isinstance(value, (Decimal, UUID)) else value for key, value in line.items()}
                        for line in lines
                    ],
                },
                performed_by_membership_id=self.actor.membership_id,
            )
        )

    def publish_results(self, session_id: UUID) -> int:
        """Publish all eligible calculated results for an exam session."""

        session = self._require(ExamSession, session_id, "session_id")
        student_ids = tuple(
            set(
                self.session.scalars(
                    select(ExamRegistration.student_id)
                    .join(
                        ExamSchedule,
                        (ExamSchedule.tenant_id == ExamRegistration.tenant_id)
                        & (ExamSchedule.id == ExamRegistration.schedule_id),
                    )
                    .where(
                        ExamRegistration.tenant_id == self.actor.tenant_id,
                        ExamRegistration.eligibility == "eligible",
                        ExamSchedule.session_id == session_id,
                    )
                )
            )
        )
        if len(student_ids) == 0:
            raise ExaminationsValidationError("No eligible registrations found for the session")

        now = datetime.now(UTC)
        count = 0
        for sid in student_ids:
            existing = self.session.scalar(
                select(PublishedResult).where(
                    PublishedResult.tenant_id == self.actor.tenant_id,
                    PublishedResult.student_id == sid,
                    PublishedResult.session_id == session_id,
                )
            )
            if existing is not None and existing.state == "published":
                continue
            total, max_total, pct, grade, gpa, outcome, lines = self._calculate(session, sid)
            target = existing or PublishedResult(
                tenant_id=self.actor.tenant_id,
                student_id=sid,
                session_id=session_id,
                total_marks=total,
                total_max_marks=max_total,
                percentage=pct,
                grade=grade,
                gpa=gpa,
                result=outcome,
                state="published",
                published_at=now,
                published_by_membership_id=self.actor.membership_id,
            )
            target.total_marks = total
            target.total_max_marks = max_total
            target.percentage = pct
            target.grade = grade
            target.gpa = gpa
            target.result = outcome
            target.state = "published"
            target.published_at = now
            target.published_by_membership_id = self.actor.membership_id
            target.reopened_at = None
            target.reopened_by_membership_id = None
            if existing is None:
                self.session.add(target)
            else:
                target.publication_version += 1
            self.session.flush()
            self._stage_result_snapshot(target, "republished" if existing else "published", lines)
            count += 1

        if count == 0:
            raise ExaminationsConflictError(
                "No publishable results found. Reopen specific results before republishing"
            )
        session.state = "published"
        self.session.flush()
        self._audit("examinations.results.publish", "exam_session", session.id, {"published_count": count})
        return count

    def reopen_result(self, result_id: UUID, payload: ResultReopenRequest) -> PublishedResult:
        """Reopen a published result for controlled correction."""

        item = self._require(PublishedResult, result_id, "result_id")
        if item.state == "reopened":
            return item
        item.state = "reopened"
        item.reopened_at = datetime.now(UTC)
        item.reopened_by_membership_id = self.actor.membership_id
        lines = list(
            self.session.scalars(
                select(PublishedResultLine).where(
                    PublishedResultLine.tenant_id == self.actor.tenant_id,
                    PublishedResultLine.result_id == item.id,
                    PublishedResultLine.publication_version == item.publication_version,
                )
            )
        )
        self._stage_result_snapshot(
            item,
            "reopened",
            [
                {
                    "registration_id": line.registration_id,
                    "subject_id": line.subject_id,
                    "marks_obtained": line.marks_obtained,
                    "max_marks": line.max_marks,
                    "pass_marks": line.pass_marks,
                    "credits": line.credits,
                    "grade": line.grade,
                    "grade_point": line.grade_point,
                }
                for line in lines
            ],
            payload.reason,
        )
        self.session.flush()
        self._audit("examinations.results.reopen", "published_result", item.id, {"reason": payload.reason})
        return item

    def republish_result(self, result_id: UUID) -> PublishedResult:
        """Recalculate and republish a previously reopened result."""

        item = self._require(PublishedResult, result_id, "result_id")
        if item.state != "reopened":
            raise ExaminationsConflictError("Result must be reopened before republish")
        session = self._require(ExamSession, item.session_id, "session_id")
        total, max_total, pct, grade, gpa, outcome, lines = self._calculate(session, item.student_id)
        item.publication_version += 1
        item.total_marks = total
        item.total_max_marks = max_total
        item.percentage = pct
        item.grade = grade
        item.gpa = gpa
        item.result = outcome
        item.state = "published"
        item.published_at = datetime.now(UTC)
        item.published_by_membership_id = self.actor.membership_id
        item.reopened_at = None
        item.reopened_by_membership_id = None
        self._stage_result_snapshot(item, "republished", lines)
        self.session.flush()
        self._audit("examinations.results.republish", "published_result", item.id, {})
        return item

    def get_result_detail(self, result_id: UUID) -> tuple[PublishedResult, list[PublishedResultLine], list[ResultPublicationEvent]]:
        """Return one result with its current subject lines and complete publication history."""

        result = self._require(PublishedResult, result_id, "result_id")
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None and result.student_id not in student_ids:
            raise ExaminationsValidationError("Invalid result_id reference")
        lines = list(
            self.session.scalars(
                select(PublishedResultLine).where(
                    PublishedResultLine.tenant_id == self.actor.tenant_id,
                    PublishedResultLine.result_id == result.id,
                    PublishedResultLine.publication_version == result.publication_version,
                )
            )
        )
        history = list(
            self.session.scalars(
                select(ResultPublicationEvent)
                .where(
                    ResultPublicationEvent.tenant_id == self.actor.tenant_id,
                    ResultPublicationEvent.result_id == result.id,
                )
                .order_by(ResultPublicationEvent.created_at.desc())
            )
        )
        return result, lines, history

    def build_transcript(self, student_id: UUID) -> tuple[list[PublishedResult], Decimal]:
        """Build one student's transcript and cumulative GPA from published results."""

        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None and student_id not in student_ids:
            raise ExaminationsValidationError("Invalid student_id reference")
        self._require(Student, student_id, "student_id")
        results = list(
            self.session.scalars(
                select(PublishedResult)
                .where(
                    PublishedResult.tenant_id == self.actor.tenant_id,
                    PublishedResult.student_id == student_id,
                    PublishedResult.state == "published",
                )
                .order_by(PublishedResult.published_at.asc())
            )
        )
        if not results:
            return [], Decimal("0.00")
        cgpa = (sum((Decimal(result.gpa) for result in results), Decimal("0.00")) / len(results)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        return results, cgpa

    def _result_snapshot(
        self,
        result_id: UUID,
        publication_version: int,
    ) -> tuple[dict[str, object], list[GradeCardDocumentLine]]:
        """Return one immutable published aggregate and its labeled subject lines."""

        event = self.session.scalar(
            select(ResultPublicationEvent)
            .where(
                ResultPublicationEvent.tenant_id == self.actor.tenant_id,
                ResultPublicationEvent.result_id == result_id,
                ResultPublicationEvent.version == publication_version,
                ResultPublicationEvent.event_type.in_(("published", "republished")),
            )
            .order_by(ResultPublicationEvent.created_at.desc())
        )
        if event is None:
            raise ExaminationsValidationError("Published result snapshot is unavailable")
        raw_lines = event.snapshot.get("lines", [])
        subject_ids = [UUID(str(line["subject_id"])) for line in raw_lines]
        subjects = {
            subject.id: subject
            for subject in self.session.scalars(
                select(Subject).where(
                    Subject.tenant_id == self.actor.tenant_id,
                    Subject.id.in_(subject_ids),
                )
            )
        }
        lines = [
            GradeCardDocumentLine(
                subject_code=subjects[UUID(str(line["subject_id"]))].code,
                subject_name=subjects[UUID(str(line["subject_id"]))].name,
                marks_obtained=Decimal(str(line["marks_obtained"])),
                max_marks=Decimal(str(line["max_marks"])),
                credits=int(line["credits"]),
                grade=str(line["grade"]),
                grade_point=Decimal(str(line["grade_point"])),
            )
            for line in raw_lines
        ]
        return event.snapshot, lines

    def _ensure_result_snapshot(self, result: PublishedResult) -> None:
        """Freeze a baseline event for legacy published results that only have immutable lines."""

        existing = self.session.scalar(
            select(ResultPublicationEvent.id).where(
                ResultPublicationEvent.tenant_id == self.actor.tenant_id,
                ResultPublicationEvent.result_id == result.id,
                ResultPublicationEvent.version == result.publication_version,
                ResultPublicationEvent.event_type.in_(("published", "republished")),
            )
        )
        if existing is not None:
            return
        lines = list(
            self.session.scalars(
                select(PublishedResultLine).where(
                    PublishedResultLine.tenant_id == self.actor.tenant_id,
                    PublishedResultLine.result_id == result.id,
                    PublishedResultLine.publication_version == result.publication_version,
                )
            )
        )
        self.session.add(
            ResultPublicationEvent(
                tenant_id=self.actor.tenant_id,
                result_id=result.id,
                version=result.publication_version,
                event_type="published",
                reason="Baseline snapshot frozen during document issuance",
                snapshot={
                    "total_marks": str(result.total_marks),
                    "total_max_marks": str(result.total_max_marks),
                    "percentage": str(result.percentage),
                    "grade": result.grade,
                    "gpa": str(result.gpa),
                    "result": result.result,
                    "state": result.state,
                    "lines": [
                        {
                            "registration_id": str(line.registration_id),
                            "subject_id": str(line.subject_id),
                            "marks_obtained": str(line.marks_obtained),
                            "max_marks": str(line.max_marks),
                            "pass_marks": str(line.pass_marks),
                            "credits": line.credits,
                            "grade": line.grade,
                            "grade_point": str(line.grade_point),
                        }
                        for line in lines
                    ],
                },
                performed_by_membership_id=self.actor.membership_id,
            )
        )
        self.session.flush()

    def issue_grade_card(self, result_id: UUID) -> GradeCardIssuance:
        """Issue one grade card for the current published result version on replay-safe terms."""

        result, _, _ = self.get_result_detail(result_id)
        if result.state != "published":
            raise ExaminationsConflictError("Only published results can receive grade cards")
        self._ensure_result_snapshot(result)
        existing = self.session.scalar(
            select(GradeCardIssuance).where(
                GradeCardIssuance.tenant_id == self.actor.tenant_id,
                GradeCardIssuance.result_id == result.id,
                GradeCardIssuance.publication_version == result.publication_version,
            )
        )
        if existing is not None:
            return existing
        issuance = GradeCardIssuance(
            tenant_id=self.actor.tenant_id,
            result_id=result.id,
            publication_version=result.publication_version,
            card_number=self._document_number("GC"),
            issued_at=datetime.now(UTC),
            issued_by_membership_id=self.actor.membership_id,
        )
        self.session.add(issuance)
        self.session.flush()
        self._audit(
            "examinations.grade_card.issue",
            "grade_card_issuance",
            issuance.id,
            {"card_number": issuance.card_number, "version": issuance.publication_version},
        )
        return issuance

    def get_grade_card_document(self, result_id: UUID) -> GradeCardDocument | None:
        """Derive the latest issued grade card from its immutable result snapshot."""

        result, _, _ = self.get_result_detail(result_id)
        issuance = self.session.scalar(
            select(GradeCardIssuance)
            .where(
                GradeCardIssuance.tenant_id == self.actor.tenant_id,
                GradeCardIssuance.result_id == result.id,
            )
            .order_by(GradeCardIssuance.publication_version.desc())
        )
        if issuance is None:
            return None
        snapshot, lines = self._result_snapshot(result.id, issuance.publication_version)
        student, person = self._student_identity(result.student_id)
        session = self._require(ExamSession, result.session_id, "session_id")
        term = self._require(Term, session.term_id, "term_id")
        institution_name, short_name, primary_color, accent_color = self._document_branding()
        return GradeCardDocument(
            issuance_id=issuance.id,
            card_number=issuance.card_number,
            verification_reference=issuance.card_number,
            issued_at=issuance.issued_at,
            issued_by_membership_id=issuance.issued_by_membership_id,
            institution_name=institution_name,
            institution_short_name=short_name,
            primary_color=primary_color,
            accent_color=accent_color,
            student_id=student.id,
            student_name=person.full_name,
            registration_number=student.registration_number,
            result_id=result.id,
            session_id=session.id,
            term_name=term.display_name,
            publication_version=issuance.publication_version,
            total_marks=Decimal(str(snapshot["total_marks"])),
            total_max_marks=Decimal(str(snapshot["total_max_marks"])),
            percentage=Decimal(str(snapshot["percentage"])),
            grade=str(snapshot["grade"]),
            gpa=Decimal(str(snapshot["gpa"])),
            result=str(snapshot["result"]),
            lines=lines,
        )

    def issue_transcript(self, student_id: UUID) -> TranscriptIssuance:
        """Issue one transcript for the current published-result version manifest."""

        results, _ = self.build_transcript(student_id)
        if not results:
            raise ExaminationsConflictError("At least one published result is required")
        for result in results:
            self._ensure_result_snapshot(result)
        manifest = [
            {"result_id": str(result.id), "publication_version": result.publication_version}
            for result in results
        ]
        version_hash = hashlib.sha256(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        existing = self.session.scalar(
            select(TranscriptIssuance).where(
                TranscriptIssuance.tenant_id == self.actor.tenant_id,
                TranscriptIssuance.student_id == student_id,
                TranscriptIssuance.version_hash == version_hash,
            )
        )
        if existing is not None:
            return existing
        issuance = TranscriptIssuance(
            tenant_id=self.actor.tenant_id,
            student_id=student_id,
            transcript_number=self._document_number("TR"),
            version_hash=version_hash,
            result_versions=manifest,
            issued_at=datetime.now(UTC),
            issued_by_membership_id=self.actor.membership_id,
        )
        self.session.add(issuance)
        self.session.flush()
        self._audit(
            "examinations.transcript.issue",
            "transcript_issuance",
            issuance.id,
            {"transcript_number": issuance.transcript_number, "results": len(manifest)},
        )
        return issuance

    def get_transcript_document(self, student_id: UUID) -> TranscriptDocument | None:
        """Derive the latest issued transcript from its immutable version manifest."""

        self.build_transcript(student_id)
        issuance = self.session.scalar(
            select(TranscriptIssuance)
            .where(
                TranscriptIssuance.tenant_id == self.actor.tenant_id,
                TranscriptIssuance.student_id == student_id,
            )
            .order_by(TranscriptIssuance.issued_at.desc())
        )
        if issuance is None:
            return None
        document_results = []
        gpa_total = Decimal("0.00")
        for manifest_item in issuance.result_versions:
            result_id = UUID(str(manifest_item["result_id"]))
            version = int(manifest_item["publication_version"])
            result = self._require(PublishedResult, result_id, "result_id")
            if result.student_id != student_id:
                raise ExaminationsValidationError("Transcript result manifest is invalid")
            snapshot, lines = self._result_snapshot(result.id, version)
            session = self._require(ExamSession, result.session_id, "session_id")
            term = self._require(Term, session.term_id, "term_id")
            gpa = Decimal(str(snapshot["gpa"]))
            gpa_total += gpa
            document_results.append(
                TranscriptDocumentResult(
                    result_id=result.id,
                    session_id=session.id,
                    term_name=term.display_name,
                    publication_version=version,
                    total_marks=Decimal(str(snapshot["total_marks"])),
                    total_max_marks=Decimal(str(snapshot["total_max_marks"])),
                    percentage=Decimal(str(snapshot["percentage"])),
                    grade=str(snapshot["grade"]),
                    gpa=gpa,
                    result=str(snapshot["result"]),
                    lines=lines,
                )
            )
        student, person = self._student_identity(student_id)
        institution_name, short_name, primary_color, accent_color = self._document_branding()
        cgpa = (gpa_total / len(document_results)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        return TranscriptDocument(
            issuance_id=issuance.id,
            transcript_number=issuance.transcript_number,
            verification_reference=issuance.transcript_number,
            issued_at=issuance.issued_at,
            issued_by_membership_id=issuance.issued_by_membership_id,
            institution_name=institution_name,
            institution_short_name=short_name,
            primary_color=primary_color,
            accent_color=accent_color,
            student_id=student.id,
            student_name=person.full_name,
            registration_number=student.registration_number,
            cgpa=cgpa,
            results=document_results,
        )
