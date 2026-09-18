"""Business logic for tenant-safe faculty delivery, timetable, and class sessions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import false, func, or_, select, text
from sqlalchemy.orm import Session

from app.domains.academics.models import Batch, Department, Program, Room, Section, Subject, Term
from app.domains.audit.models import AuditEvent
from app.domains.delivery.models import (
    ClassSession,
    ClassSubstitution,
    DepartmentPosting,
    FacultyAllocation,
    FacultyProfile,
    LearningMaterial,
    LessonPlan,
    SubjectOffering,
    SyllabusProgress,
    TimetablePeriod,
    TimetablePublication,
    TimetablePublicationLine,
)
from app.domains.delivery.schemas import (
    ClassSessionCreate,
    ClassSessionGenerateRequest,
    ClassSessionUpdate,
    ClassSubstitutionCreate,
    DepartmentPostingCreate,
    FacultyAllocationCreate,
    FacultyAllocationUpdate,
    FacultyProfileCreate,
    FacultyProfileUpdate,
    LearningMaterialCreate,
    LessonPlanCreate,
    SubjectOfferingCreate,
    SubjectOfferingUpdate,
    SyllabusProgressCreate,
    TimetablePeriodCreate,
    TimetablePeriodUpdate,
    TimetablePublicationCreate,
)
from app.domains.students.models import Person, StudentEnrollment
from app.security_context import ActorContext, resolve_actor_student_ids

ModelType = TypeVar("ModelType")
INVALID_SUBJECT_OFFERING = "Invalid subject offering reference"
INVALID_FACULTY_REFERENCE = "Invalid faculty reference"


class DeliveryDomainError(Exception):
    """Represent one controlled delivery domain failure mapped to an HTTP status."""

    def __init__(self, detail: str, status_code: int) -> None:
        """Store one deterministic API error message with status code."""

        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class DeliveryValidationError(DeliveryDomainError):
    """Represent one delivery validation failure mapped to HTTP 422."""

    def __init__(self, detail: str) -> None:
        """Initialize a delivery validation error."""

        super().__init__(detail=detail, status_code=422)


class DeliveryConflictError(DeliveryDomainError):
    """Represent one delivery conflict mapped to HTTP 409."""

    def __init__(self, detail: str) -> None:
        """Initialize a delivery conflict error."""

        super().__init__(detail=detail, status_code=409)


class DeliveryService:
    """Manage tenant-scoped faculty delivery master and session lifecycle records."""

    def __init__(self, session: Session, actor: ActorContext) -> None:
        """Initialize the service with one SQLAlchemy session and authenticated actor."""

        self.session = session
        self.actor = actor
        self._set_tenant_context()

    def _set_tenant_context(self) -> None:
        """Set transaction-local tenant context used by forced PostgreSQL RLS."""

        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self.actor.tenant_id)},
        )

    def _audit(self, action: str, entity_type: str, entity_id: UUID, details: dict[str, object]) -> None:
        """Persist one audit event for the active tenant transaction."""

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

    def _require_entity(self, model: type[ModelType], entity_id: UUID, label: str) -> ModelType:
        """Return one tenant-scoped entity by ID or raise a controlled validation error."""

        entity = self.session.scalar(
            select(model).where(  # type: ignore[arg-type]
                model.id == entity_id,  # type: ignore[attr-defined]
                model.tenant_id == self.actor.tenant_id,  # type: ignore[attr-defined]
            )
        )
        if entity is None:
            raise DeliveryValidationError(f"Invalid {label} reference")
        return entity

    @staticmethod
    def _time_overlap(start_a, end_a, start_b, end_b) -> bool:
        """Return whether two half-open time ranges overlap."""

        return start_a < end_b and start_b < end_a

    def _validate_timetable_conflicts(
        self,
        *,
        period_id: UUID | None,
        faculty_id: UUID,
        room_id: UUID | None,
        day_of_week: int,
        start_time,
        end_time,
    ) -> None:
        """Reject conflicting timetable periods for the same faculty or room."""

        candidates = list(
            self.session.scalars(
                select(TimetablePeriod).where(
                    TimetablePeriod.tenant_id == self.actor.tenant_id,
                    TimetablePeriod.day_of_week == day_of_week,
                    TimetablePeriod.status == "active",
                )
            )
        )
        for candidate in candidates:
            if period_id is not None and candidate.id == period_id:
                continue
            if not self._time_overlap(start_time, end_time, candidate.start_time, candidate.end_time):
                continue
            if candidate.faculty_id == faculty_id:
                raise DeliveryConflictError("Faculty timetable conflict detected")
            if room_id is not None and candidate.room_id == room_id:
                raise DeliveryConflictError("Room timetable conflict detected")

    def _paginate(self, query, skip: int, limit: int):
        """Return one paginated query tuple of tenant-scoped items and total count."""

        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def _scoped_offering_ids(self):
        """Select subject offerings visible within the actor's assigned record scopes."""

        query = select(SubjectOffering.id).where(
            SubjectOffering.tenant_id == self.actor.tenant_id
        )
        if self.actor.scopes_of_type("institution"):
            return query

        conditions = []
        offering_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("subject_offering")
            if scope.scope_reference_id is not None
        )
        if offering_ids:
            conditions.append(SubjectOffering.id.in_(offering_ids))

        department_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("department")
            if scope.scope_reference_id is not None
        )
        if department_ids:
            conditions.append(
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
            conditions.append(SubjectOffering.section_id.in_(section_ids))

        batch_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("batch")
            if scope.scope_reference_id is not None
        )
        if batch_ids:
            conditions.append(
                SubjectOffering.section_id.in_(
                    select(Section.id).where(
                        Section.tenant_id == self.actor.tenant_id,
                        Section.batch_id.in_(batch_ids),
                    )
                )
            )

        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            conditions.append(
                SubjectOffering.section_id.in_(
                    select(StudentEnrollment.section_id).where(
                        StudentEnrollment.tenant_id == self.actor.tenant_id,
                        StudentEnrollment.student_id.in_(student_ids),
                        StudentEnrollment.section_id.is_not(None),
                        StudentEnrollment.status == "active",
                    )
                )
            )

        return query.where(or_(*conditions)) if conditions else query.where(false())

    def _scoped_faculty_ids(self):
        """Select faculty visible through scoped offerings or department postings."""

        query = select(FacultyProfile.id).where(
            FacultyProfile.tenant_id == self.actor.tenant_id
        )
        if self.actor.scopes_of_type("institution"):
            return query

        conditions = [
            FacultyProfile.id.in_(
                select(FacultyAllocation.faculty_id).where(
                    FacultyAllocation.tenant_id == self.actor.tenant_id,
                    FacultyAllocation.offering_id.in_(self._scoped_offering_ids()),
                )
            )
        ]
        department_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("department")
            if scope.scope_reference_id is not None
        )
        if department_ids:
            conditions.append(
                FacultyProfile.id.in_(
                    select(DepartmentPosting.faculty_id).where(
                        DepartmentPosting.tenant_id == self.actor.tenant_id,
                        DepartmentPosting.department_id.in_(department_ids),
                    )
                )
            )
        return query.where(or_(*conditions))

    def _publication_scope(self) -> tuple[str, UUID | None]:
        """Resolve the single publication boundary authorized for this actor."""

        if self.actor.scopes_of_type("institution"):
            return "institution", None
        department_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("department")
            if scope.scope_reference_id is not None
        )
        if len(department_ids) != 1:
            raise DeliveryValidationError(
                "Timetable publication requires institution scope or one Department scope"
            )
        return "department", department_ids[0]

    def _visible_publication_ids(self):
        """Select publications containing timetable lines visible to the actor."""

        query = select(TimetablePublication.id).where(
            TimetablePublication.tenant_id == self.actor.tenant_id
        )
        if self.actor.scopes_of_type("institution"):
            return query
        return query.where(
            TimetablePublication.id.in_(
                select(TimetablePublicationLine.publication_id).where(
                    TimetablePublicationLine.tenant_id == self.actor.tenant_id,
                    TimetablePublicationLine.offering_id.in_(self._scoped_offering_ids()),
                )
            )
        )

    def _can_create_offering(self, subject_id: UUID, section_id: UUID) -> bool:
        """Return whether actor scopes authorize a proposed subject offering."""

        if self.actor.scopes_of_type("institution"):
            return True
        department_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("department")
            if scope.scope_reference_id is not None
        )
        if department_ids and self.session.scalar(
            select(Subject.id).where(
                Subject.tenant_id == self.actor.tenant_id,
                Subject.id == subject_id,
                Subject.department_id.in_(department_ids),
            )
        ):
            return bool(
                self.session.scalar(
                    select(Section.id)
                    .join(
                        Batch,
                        (Batch.tenant_id == Section.tenant_id)
                        & (Batch.id == Section.batch_id),
                    )
                    .join(
                        Program,
                        (Program.tenant_id == Batch.tenant_id)
                        & (Program.id == Batch.program_id),
                    )
                    .where(
                        Section.tenant_id == self.actor.tenant_id,
                        Section.id == section_id,
                        Program.department_id.in_(department_ids),
                    )
                )
            )
        section_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("section")
            if scope.scope_reference_id is not None
        )
        if section_id in section_ids:
            return True
        batch_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("batch")
            if scope.scope_reference_id is not None
        )
        return bool(
            batch_ids
            and self.session.scalar(
                select(Section.id).where(
                    Section.tenant_id == self.actor.tenant_id,
                    Section.id == section_id,
                    Section.batch_id.in_(batch_ids),
                )
            )
        )

    def _list_operations(self, model: type[ModelType], skip: int, limit: int):
        """List one tenant-owned delivery operation model in reverse creation order."""

        query = (
            select(model)
            .where(model.tenant_id == self.actor.tenant_id)  # type: ignore[attr-defined]
            .order_by(model.created_at.desc())  # type: ignore[attr-defined]
        )
        return self._paginate(query, skip, limit)

    def _create_operation(
        self,
        model: type[ModelType],
        payload: BaseModel,
        action: str,
        entity_type: str,
    ) -> ModelType:
        """Create and audit one validated tenant-owned delivery operation record."""

        item = model(tenant_id=self.actor.tenant_id, **payload.model_dump())  # type: ignore[call-arg]
        self.session.add(item)
        self.session.flush()
        self._audit(action, entity_type, item.id, payload.model_dump(mode="json"))  # type: ignore[attr-defined]
        return item

    def list_faculty_profiles(self, skip: int = 0, limit: int = 100):
        """List faculty profiles visible through the actor's resolved scopes."""

        query = (
            select(FacultyProfile)
            .where(
                FacultyProfile.tenant_id == self.actor.tenant_id,
                FacultyProfile.id.in_(self._scoped_faculty_ids()),
            )
            .order_by(FacultyProfile.employee_code)
        )
        return self._paginate(query, skip, limit)

    def get_faculty_profile(self, faculty_id: UUID) -> FacultyProfile | None:
        """Return one faculty profile by ID for the current tenant."""

        return self.session.scalar(
            select(FacultyProfile).where(
                FacultyProfile.tenant_id == self.actor.tenant_id,
                FacultyProfile.id == faculty_id,
                FacultyProfile.id.in_(self._scoped_faculty_ids()),
            )
        )

    def create_faculty_profile(self, payload: FacultyProfileCreate) -> FacultyProfile:
        """Create one faculty profile after validating referenced person identity."""

        if not self.actor.scopes_of_type("institution"):
            raise DeliveryValidationError(
                "Faculty profiles can only be created with institution scope"
            )
        self._require_entity(Person, payload.person_id, "person_id")
        faculty = FacultyProfile(
            tenant_id=self.actor.tenant_id,
            person_id=payload.person_id,
            employee_code=payload.employee_code,
            status=payload.status,
        )
        self.session.add(faculty)
        self.session.flush()
        self._audit("delivery.faculty.create", "faculty_profile", faculty.id, {"status": faculty.status})
        return faculty

    def update_faculty_profile(self, faculty_id: UUID, payload: FacultyProfileUpdate) -> FacultyProfile | None:
        """Update mutable faculty profile fields."""

        faculty = self.get_faculty_profile(faculty_id)
        if faculty is None:
            return None
        changes: dict[str, object] = {}
        if payload.employee_code is not None and payload.employee_code != faculty.employee_code:
            changes["employee_code"] = {"from": faculty.employee_code, "to": payload.employee_code}
            faculty.employee_code = payload.employee_code
        if payload.status is not None and payload.status != faculty.status:
            changes["status"] = {"from": faculty.status, "to": payload.status}
            faculty.status = payload.status
        if changes:
            self.session.flush()
            self._audit("delivery.faculty.update", "faculty_profile", faculty.id, changes)
        return faculty

    def list_subject_offerings(self, skip: int = 0, limit: int = 100):
        """List subject offerings for the current tenant."""

        query = (
            select(SubjectOffering)
            .where(
                SubjectOffering.tenant_id == self.actor.tenant_id,
                SubjectOffering.id.in_(self._scoped_offering_ids()),
            )
            .order_by(SubjectOffering.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def get_subject_offering(self, offering_id: UUID) -> SubjectOffering | None:
        """Return one subject offering by ID for the current tenant."""

        return self.session.scalar(
            select(SubjectOffering).where(
                SubjectOffering.tenant_id == self.actor.tenant_id,
                SubjectOffering.id == offering_id,
                SubjectOffering.id.in_(self._scoped_offering_ids()),
            )
        )

    def create_subject_offering(self, payload: SubjectOfferingCreate) -> SubjectOffering:
        """Create one subject offering after validating academic references."""

        self._require_entity(Subject, payload.subject_id, "subject_id")
        self._require_entity(Section, payload.section_id, "section_id")
        self._require_entity(Term, payload.term_id, "term_id")
        if not self._can_create_offering(payload.subject_id, payload.section_id):
            raise DeliveryValidationError(INVALID_SUBJECT_OFFERING)
        offering = SubjectOffering(
            tenant_id=self.actor.tenant_id,
            term_id=payload.term_id,
            subject_id=payload.subject_id,
            section_id=payload.section_id,
            status=payload.status,
        )
        self.session.add(offering)
        self.session.flush()
        self._audit("delivery.offering.create", "subject_offering", offering.id, {"status": offering.status})
        return offering

    def update_subject_offering(
        self,
        offering_id: UUID,
        payload: SubjectOfferingUpdate,
    ) -> SubjectOffering | None:
        """Update one subject offering state."""

        offering = self.get_subject_offering(offering_id)
        if offering is None:
            return None
        if payload.status is not None and payload.status != offering.status:
            previous = offering.status
            offering.status = payload.status
            self.session.flush()
            self._audit(
                "delivery.offering.update",
                "subject_offering",
                offering.id,
                {"status": {"from": previous, "to": payload.status}},
            )
        return offering

    def list_faculty_allocations(self, skip: int = 0, limit: int = 100):
        """List faculty allocations for the current tenant."""

        query = (
            select(FacultyAllocation)
            .where(
                FacultyAllocation.tenant_id == self.actor.tenant_id,
                FacultyAllocation.offering_id.in_(self._scoped_offering_ids()),
            )
            .order_by(FacultyAllocation.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def get_faculty_allocation(self, allocation_id: UUID) -> FacultyAllocation | None:
        """Return one faculty allocation by ID."""

        return self.session.scalar(
            select(FacultyAllocation).where(
                FacultyAllocation.tenant_id == self.actor.tenant_id,
                FacultyAllocation.id == allocation_id,
                FacultyAllocation.offering_id.in_(self._scoped_offering_ids()),
            )
        )

    def create_faculty_allocation(self, payload: FacultyAllocationCreate) -> FacultyAllocation:
        """Create one faculty allocation."""

        if self.get_subject_offering(payload.offering_id) is None:
            raise DeliveryValidationError(INVALID_SUBJECT_OFFERING)
        if self.get_faculty_profile(payload.faculty_id) is None:
            raise DeliveryValidationError(INVALID_FACULTY_REFERENCE)
        allocation = FacultyAllocation(
            tenant_id=self.actor.tenant_id,
            offering_id=payload.offering_id,
            faculty_id=payload.faculty_id,
            status=payload.status,
        )
        self.session.add(allocation)
        self.session.flush()
        self._audit(
            "delivery.allocation.create",
            "faculty_allocation",
            allocation.id,
            {"status": allocation.status},
        )
        return allocation

    def update_faculty_allocation(
        self,
        allocation_id: UUID,
        payload: FacultyAllocationUpdate,
    ) -> FacultyAllocation | None:
        """Update one faculty allocation status."""

        allocation = self.get_faculty_allocation(allocation_id)
        if allocation is None:
            return None
        if payload.status is not None and payload.status != allocation.status:
            previous = allocation.status
            allocation.status = payload.status
            self.session.flush()
            self._audit(
                "delivery.allocation.update",
                "faculty_allocation",
                allocation.id,
                {"status": {"from": previous, "to": payload.status}},
            )
        return allocation

    def list_timetable_periods(self, skip: int = 0, limit: int = 100):
        """List timetable periods ordered by day and start time."""

        query = (
            select(TimetablePeriod)
            .where(
                TimetablePeriod.tenant_id == self.actor.tenant_id,
                TimetablePeriod.offering_id.in_(self._scoped_offering_ids()),
            )
            .order_by(TimetablePeriod.day_of_week, TimetablePeriod.start_time)
        )
        return self._paginate(query, skip, limit)

    def get_timetable_period(self, period_id: UUID) -> TimetablePeriod | None:
        """Return one timetable period by ID."""

        return self.session.scalar(
            select(TimetablePeriod).where(
                TimetablePeriod.tenant_id == self.actor.tenant_id,
                TimetablePeriod.id == period_id,
                TimetablePeriod.offering_id.in_(self._scoped_offering_ids()),
            )
        )

    def create_timetable_period(self, payload: TimetablePeriodCreate) -> TimetablePeriod:
        """Create one timetable period after enforcing faculty and room conflict rules."""

        if self.get_subject_offering(payload.offering_id) is None:
            raise DeliveryValidationError(INVALID_SUBJECT_OFFERING)
        if self.get_faculty_profile(payload.faculty_id) is None:
            raise DeliveryValidationError(INVALID_FACULTY_REFERENCE)
        self._validate_timetable_conflicts(
            period_id=None,
            faculty_id=payload.faculty_id,
            room_id=payload.room_id,
            day_of_week=payload.day_of_week,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )
        period = TimetablePeriod(
            tenant_id=self.actor.tenant_id,
            offering_id=payload.offering_id,
            faculty_id=payload.faculty_id,
            room_id=payload.room_id,
            day_of_week=payload.day_of_week,
            start_time=payload.start_time,
            end_time=payload.end_time,
            status=payload.status,
        )
        self.session.add(period)
        self.session.flush()
        self._audit(
            "delivery.timetable.create",
            "timetable_period",
            period.id,
            {"day_of_week": period.day_of_week, "status": period.status},
        )
        return period

    def update_timetable_period(
        self,
        period_id: UUID,
        payload: TimetablePeriodUpdate,
    ) -> TimetablePeriod | None:
        """Update timetable period fields while keeping conflict guarantees."""

        period = self.get_timetable_period(period_id)
        if period is None:
            return None

        next_offering_id = payload.offering_id or period.offering_id
        next_faculty_id = payload.faculty_id or period.faculty_id
        next_room_id = payload.room_id if payload.room_id is not None else period.room_id
        next_day_of_week = payload.day_of_week or period.day_of_week
        next_start_time = payload.start_time or period.start_time
        next_end_time = payload.end_time or period.end_time
        if self.get_subject_offering(next_offering_id) is None:
            raise DeliveryValidationError(INVALID_SUBJECT_OFFERING)
        if self.get_faculty_profile(next_faculty_id) is None:
            raise DeliveryValidationError(INVALID_FACULTY_REFERENCE)
        if next_start_time >= next_end_time:
            raise DeliveryValidationError("end_time must be after start_time")

        self._validate_timetable_conflicts(
            period_id=period.id,
            faculty_id=next_faculty_id,
            room_id=next_room_id,
            day_of_week=next_day_of_week,
            start_time=next_start_time,
            end_time=next_end_time,
        )

        changes: dict[str, object] = {}
        if payload.offering_id is not None and payload.offering_id != period.offering_id:
            changes["offering_id"] = {"from": str(period.offering_id), "to": str(payload.offering_id)}
            period.offering_id = next_offering_id
        if payload.faculty_id is not None and payload.faculty_id != period.faculty_id:
            changes["faculty_id"] = {"from": str(period.faculty_id), "to": str(payload.faculty_id)}
            period.faculty_id = next_faculty_id
        if payload.room_id is not None and payload.room_id != period.room_id:
            changes["room_id"] = {
                "from": str(period.room_id) if period.room_id else None,
                "to": str(payload.room_id),
            }
            period.room_id = payload.room_id
        if payload.day_of_week is not None and payload.day_of_week != period.day_of_week:
            changes["day_of_week"] = {"from": period.day_of_week, "to": payload.day_of_week}
            period.day_of_week = next_day_of_week
        if payload.start_time is not None and payload.start_time != period.start_time:
            changes["start_time"] = {"from": str(period.start_time), "to": str(payload.start_time)}
            period.start_time = next_start_time
        if payload.end_time is not None and payload.end_time != period.end_time:
            changes["end_time"] = {"from": str(period.end_time), "to": str(payload.end_time)}
            period.end_time = next_end_time
        if payload.status is not None and payload.status != period.status:
            changes["status"] = {"from": period.status, "to": payload.status}
            period.status = payload.status

        if changes:
            self.session.flush()
            self._audit("delivery.timetable.update", "timetable_period", period.id, changes)
        return period

    def list_timetable_publications(self, skip: int = 0, limit: int = 100):
        """List versioned timetable publications visible through actor scope."""

        query = (
            select(TimetablePublication)
            .where(
                TimetablePublication.tenant_id == self.actor.tenant_id,
                TimetablePublication.id.in_(self._visible_publication_ids()),
            )
            .order_by(
                TimetablePublication.published_at.desc(),
                TimetablePublication.version.desc(),
            )
        )
        return self._paginate(query, skip, limit)

    def get_timetable_publication(
        self, publication_id: UUID
    ) -> tuple[TimetablePublication, list[TimetablePublicationLine]] | None:
        """Return one visible publication with immutable lines limited to actor scope."""

        publication = self.session.scalar(
            select(TimetablePublication).where(
                TimetablePublication.tenant_id == self.actor.tenant_id,
                TimetablePublication.id == publication_id,
                TimetablePublication.id.in_(self._visible_publication_ids()),
            )
        )
        if publication is None:
            return None
        line_query = select(TimetablePublicationLine).where(
            TimetablePublicationLine.tenant_id == self.actor.tenant_id,
            TimetablePublicationLine.publication_id == publication.id,
        )
        if not self.actor.scopes_of_type("institution"):
            line_query = line_query.where(
                TimetablePublicationLine.offering_id.in_(self._scoped_offering_ids())
            )
        lines = list(
            self.session.scalars(
                line_query.order_by(
                    TimetablePublicationLine.day_of_week,
                    TimetablePublicationLine.start_time,
                    TimetablePublicationLine.section_code,
                )
            )
        )
        return publication, lines

    def publish_timetable(
        self, payload: TimetablePublicationCreate
    ) -> tuple[TimetablePublication, list[TimetablePublicationLine]]:
        """Snapshot active scoped timetable periods into one immutable publication version."""

        self._require_entity(Term, payload.term_id, "term_id")
        scope_type, scope_reference_id = self._publication_scope()
        rows = list(
            self.session.execute(
                select(
                    TimetablePeriod,
                    SubjectOffering,
                    Subject,
                    Section,
                    FacultyProfile,
                    Room,
                )
                .join(
                    SubjectOffering,
                    (SubjectOffering.tenant_id == TimetablePeriod.tenant_id)
                    & (SubjectOffering.id == TimetablePeriod.offering_id),
                )
                .join(
                    Subject,
                    (Subject.tenant_id == SubjectOffering.tenant_id)
                    & (Subject.id == SubjectOffering.subject_id),
                )
                .join(
                    Section,
                    (Section.tenant_id == SubjectOffering.tenant_id)
                    & (Section.id == SubjectOffering.section_id),
                )
                .join(
                    FacultyProfile,
                    (FacultyProfile.tenant_id == TimetablePeriod.tenant_id)
                    & (FacultyProfile.id == TimetablePeriod.faculty_id),
                )
                .outerjoin(
                    Room,
                    (Room.tenant_id == TimetablePeriod.tenant_id)
                    & (Room.id == TimetablePeriod.room_id),
                )
                .where(
                    TimetablePeriod.tenant_id == self.actor.tenant_id,
                    TimetablePeriod.status == "active",
                    TimetablePeriod.offering_id.in_(self._scoped_offering_ids()),
                    SubjectOffering.term_id == payload.term_id,
                    SubjectOffering.status.in_(("planned", "active")),
                )
                .order_by(
                    TimetablePeriod.day_of_week,
                    TimetablePeriod.start_time,
                    Section.code,
                )
            )
        )
        if not rows:
            raise DeliveryValidationError(
                "No active scoped timetable periods are available for this term"
            )

        publication_query = select(TimetablePublication).where(
            TimetablePublication.tenant_id == self.actor.tenant_id,
            TimetablePublication.term_id == payload.term_id,
            TimetablePublication.scope_type == scope_type,
        )
        publication_query = (
            publication_query.where(TimetablePublication.scope_reference_id.is_(None))
            if scope_reference_id is None
            else publication_query.where(
                TimetablePublication.scope_reference_id == scope_reference_id
            )
        )
        previous = list(
            self.session.scalars(
                publication_query.order_by(TimetablePublication.version).with_for_update()
            )
        )
        version = max((item.version for item in previous), default=0) + 1
        for item in previous:
            if item.state == "published":
                item.state = "superseded"

        publication = TimetablePublication(
            tenant_id=self.actor.tenant_id,
            term_id=payload.term_id,
            scope_type=scope_type,
            scope_reference_id=scope_reference_id,
            version=version,
            state="published",
            note=payload.note,
            published_by_membership_id=self.actor.membership_id,
            published_at=datetime.now(UTC),
        )
        self.session.add(publication)
        self.session.flush()

        lines = []
        for period, offering, subject, section, faculty, room in rows:
            line = TimetablePublicationLine(
                tenant_id=self.actor.tenant_id,
                publication_id=publication.id,
                source_period_id=period.id,
                offering_id=offering.id,
                subject_id=subject.id,
                section_id=section.id,
                faculty_id=faculty.id,
                room_id=room.id if room is not None else None,
                subject_code=subject.code,
                subject_name=subject.name,
                section_code=section.code,
                section_name=section.display_name,
                faculty_employee_code=faculty.employee_code,
                room_code=room.code if room is not None else None,
                room_name=room.name if room is not None else None,
                day_of_week=period.day_of_week,
                start_time=period.start_time,
                end_time=period.end_time,
            )
            self.session.add(line)
            lines.append(line)
        self.session.flush()
        self._audit(
            "delivery.timetable.publish",
            "timetable_publication",
            publication.id,
            {
                "term_id": str(payload.term_id),
                "scope_type": scope_type,
                "scope_reference_id": (
                    str(scope_reference_id) if scope_reference_id is not None else None
                ),
                "version": version,
                "line_count": len(lines),
            },
        )
        return publication, lines

    def list_class_sessions(self, skip: int = 0, limit: int = 100, period_id: UUID | None = None):
        """List class sessions with optional period filter."""

        scoped_period_ids = select(TimetablePeriod.id).where(
            TimetablePeriod.tenant_id == self.actor.tenant_id,
            TimetablePeriod.offering_id.in_(self._scoped_offering_ids()),
        )
        query = select(ClassSession).where(
            ClassSession.tenant_id == self.actor.tenant_id,
            ClassSession.period_id.in_(scoped_period_ids),
        )
        if period_id is not None:
            query = query.where(ClassSession.period_id == period_id)
        query = query.order_by(ClassSession.session_date.desc())
        return self._paginate(query, skip, limit)

    def get_class_session(self, session_id: UUID) -> ClassSession | None:
        """Return one class session by ID."""

        return self.session.scalar(
            select(ClassSession).where(
                ClassSession.tenant_id == self.actor.tenant_id,
                ClassSession.id == session_id,
                ClassSession.period_id.in_(
                    select(TimetablePeriod.id).where(
                        TimetablePeriod.tenant_id == self.actor.tenant_id,
                        TimetablePeriod.offering_id.in_(self._scoped_offering_ids()),
                    )
                ),
            )
        )

    def create_class_session(self, payload: ClassSessionCreate) -> ClassSession:
        """Create one class session from a period and date."""

        if self.get_timetable_period(payload.period_id) is None:
            raise DeliveryValidationError("Invalid timetable period reference")
        class_session = ClassSession(
            tenant_id=self.actor.tenant_id,
            period_id=payload.period_id,
            session_date=payload.session_date,
            state=payload.state,
        )
        self.session.add(class_session)
        self.session.flush()
        self._audit(
            "delivery.session.create",
            "class_session",
            class_session.id,
            {"state": class_session.state, "session_date": str(class_session.session_date)},
        )
        return class_session

    def update_class_session(self, session_id: UUID, payload: ClassSessionUpdate) -> ClassSession | None:
        """Update one class session state."""

        class_session = self.get_class_session(session_id)
        if class_session is None:
            return None
        if payload.state is not None and payload.state != class_session.state:
            previous = class_session.state
            class_session.state = payload.state
            self.session.flush()
            self._audit(
                "delivery.session.update",
                "class_session",
                class_session.id,
                {"state": {"from": previous, "to": payload.state}},
            )
        return class_session

    def generate_class_sessions(self, payload: ClassSessionGenerateRequest) -> tuple[int, list[UUID]]:
        """Generate dated sessions from active timetable periods across one date range."""

        periods = list(
            self.session.scalars(
                select(TimetablePeriod).where(
                    TimetablePeriod.tenant_id == self.actor.tenant_id,
                    TimetablePeriod.status == "active",
                    TimetablePeriod.offering_id.in_(self._scoped_offering_ids()),
                )
            )
        )
        period_by_day: dict[int, list[TimetablePeriod]] = {}
        for period in periods:
            period_by_day.setdefault(period.day_of_week, []).append(period)

        created_ids: list[UUID] = []
        current = payload.start_date
        while current <= payload.end_date:
            weekday = current.isoweekday()
            for period in period_by_day.get(weekday, []):
                existing = self.session.scalar(
                    select(ClassSession).where(
                        ClassSession.tenant_id == self.actor.tenant_id,
                        ClassSession.period_id == period.id,
                        ClassSession.session_date == current,
                    )
                )
                if existing is not None:
                    continue
                class_session = ClassSession(
                    tenant_id=self.actor.tenant_id,
                    period_id=period.id,
                    session_date=current,
                    state="scheduled",
                )
                self.session.add(class_session)
                self.session.flush()
                created_ids.append(class_session.id)
            current += timedelta(days=1)

        if created_ids:
            self._audit(
                "delivery.session.generate",
                "class_session",
                created_ids[0],
                {
                    "created_count": len(created_ids),
                    "start_date": str(payload.start_date),
                    "end_date": str(payload.end_date),
                },
            )
        return len(created_ids), created_ids

    def list_department_postings(self, skip: int = 0, limit: int = 100):
        """List effective-dated faculty postings visible in the actor's scope."""

        query = select(DepartmentPosting).where(
            DepartmentPosting.tenant_id == self.actor.tenant_id
        )
        if not self.actor.scopes_of_type("institution"):
            department_ids = tuple(
                scope.scope_reference_id
                for scope in self.actor.scopes_of_type("department")
                if scope.scope_reference_id is not None
            )
            query = (
                query.where(DepartmentPosting.department_id.in_(department_ids))
                if department_ids
                else query.where(false())
            )
        return self._paginate(query.order_by(DepartmentPosting.created_at.desc()), skip, limit)

    def create_department_posting(self, payload: DepartmentPostingCreate) -> DepartmentPosting:
        """Create and audit one effective-dated faculty department posting."""

        self._require_entity(Department, payload.department_id, "department_id")
        department_ids = {
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("department")
            if scope.scope_reference_id is not None
        }
        if not self.actor.scopes_of_type("institution") and payload.department_id not in department_ids:
            raise DeliveryValidationError("Invalid department reference")
        if self.get_faculty_profile(payload.faculty_id) is None:
            raise DeliveryValidationError(INVALID_FACULTY_REFERENCE)
        return self._create_operation(DepartmentPosting, payload, "delivery.posting.create", "department_posting")

    def list_substitutions(self, skip: int = 0, limit: int = 100):
        """List class-session substitution requests."""

        scoped_session_ids = select(ClassSession.id).where(
            ClassSession.tenant_id == self.actor.tenant_id,
            ClassSession.period_id.in_(
                select(TimetablePeriod.id).where(
                    TimetablePeriod.tenant_id == self.actor.tenant_id,
                    TimetablePeriod.offering_id.in_(self._scoped_offering_ids()),
                )
            ),
        )
        query = (
            select(ClassSubstitution)
            .where(
                ClassSubstitution.tenant_id == self.actor.tenant_id,
                ClassSubstitution.session_id.in_(scoped_session_ids),
            )
            .order_by(ClassSubstitution.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def create_substitution(self, payload: ClassSubstitutionCreate) -> ClassSubstitution:
        """Create and audit one class-session substitution request."""

        if self.get_class_session(payload.session_id) is None:
            raise DeliveryValidationError("Invalid class session reference")
        if self.get_faculty_profile(payload.substitute_faculty_id) is None:
            raise DeliveryValidationError("Invalid substitute faculty reference")
        return self._create_operation(ClassSubstitution, payload, "delivery.substitution.create", "class_substitution")

    def list_lesson_plans(self, skip: int = 0, limit: int = 100):
        """List dated faculty lesson plans."""

        query = (
            select(LessonPlan)
            .where(
                LessonPlan.tenant_id == self.actor.tenant_id,
                LessonPlan.offering_id.in_(self._scoped_offering_ids()),
            )
            .order_by(LessonPlan.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def create_lesson_plan(self, payload: LessonPlanCreate) -> LessonPlan:
        """Create and audit one dated faculty lesson plan."""

        if self.get_subject_offering(payload.offering_id) is None:
            raise DeliveryValidationError(INVALID_SUBJECT_OFFERING)
        return self._create_operation(LessonPlan, payload, "delivery.lesson_plan.create", "lesson_plan")

    def list_learning_materials(self, skip: int = 0, limit: int = 100):
        """List offering learning-resource references."""

        query = (
            select(LearningMaterial)
            .where(
                LearningMaterial.tenant_id == self.actor.tenant_id,
                LearningMaterial.offering_id.in_(self._scoped_offering_ids()),
            )
            .order_by(LearningMaterial.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def list_student_learning_materials(self, skip: int = 0, limit: int = 100):
        """List scoped learning materials with readable academic and Faculty context."""

        faculty_code = (
            select(FacultyProfile.employee_code)
            .join(
                FacultyAllocation,
                (FacultyAllocation.tenant_id == FacultyProfile.tenant_id)
                & (FacultyAllocation.faculty_id == FacultyProfile.id),
            )
            .where(
                FacultyAllocation.tenant_id == self.actor.tenant_id,
                FacultyAllocation.offering_id == LearningMaterial.offering_id,
                FacultyAllocation.status == "active",
            )
            .order_by(FacultyProfile.employee_code)
            .limit(1)
            .scalar_subquery()
        )
        query = (
            select(
                LearningMaterial,
                Subject.code.label("subject_code"),
                Subject.name.label("subject_name"),
                Section.code.label("section_code"),
                Section.display_name.label("section_name"),
                Term.code.label("term_code"),
                Term.display_name.label("term_name"),
                faculty_code.label("faculty_employee_code"),
            )
            .join(
                SubjectOffering,
                (SubjectOffering.tenant_id == LearningMaterial.tenant_id)
                & (SubjectOffering.id == LearningMaterial.offering_id),
            )
            .join(
                Subject,
                (Subject.tenant_id == SubjectOffering.tenant_id)
                & (Subject.id == SubjectOffering.subject_id),
            )
            .join(
                Section,
                (Section.tenant_id == SubjectOffering.tenant_id)
                & (Section.id == SubjectOffering.section_id),
            )
            .join(
                Term,
                (Term.tenant_id == SubjectOffering.tenant_id)
                & (Term.id == SubjectOffering.term_id),
            )
            .where(
                LearningMaterial.tenant_id == self.actor.tenant_id,
                LearningMaterial.offering_id.in_(self._scoped_offering_ids()),
            )
            .order_by(Subject.name, LearningMaterial.created_at.desc())
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        return list(self.session.execute(query.offset(skip).limit(limit))), total

    def create_learning_material(self, payload: LearningMaterialCreate) -> LearningMaterial:
        """Create and audit one offering learning-resource reference."""

        if self.get_subject_offering(payload.offering_id) is None:
            raise DeliveryValidationError(INVALID_SUBJECT_OFFERING)
        return self._create_operation(LearningMaterial, payload, "delivery.material.create", "learning_material")

    def list_syllabus_progress(self, skip: int = 0, limit: int = 100):
        """List dated syllabus completion records."""

        query = (
            select(SyllabusProgress)
            .where(
                SyllabusProgress.tenant_id == self.actor.tenant_id,
                SyllabusProgress.offering_id.in_(self._scoped_offering_ids()),
            )
            .order_by(SyllabusProgress.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def create_syllabus_progress(self, payload: SyllabusProgressCreate) -> SyllabusProgress:
        """Create and audit one dated syllabus completion record."""

        if self.get_subject_offering(payload.offering_id) is None:
            raise DeliveryValidationError(INVALID_SUBJECT_OFFERING)
        return self._create_operation(SyllabusProgress, payload, "delivery.progress.create", "syllabus_progress")
