"""Business logic and repository operations for academic structure management."""

from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import false, func, select, text
from sqlalchemy.orm import Session

from app.domains.academics.models import (
    AcademicYear,
    Batch,
    CalendarEvent,
    Campus,
    CollegeSetting,
    Curriculum,
    CurriculumSubject,
    Department,
    NumberingFormat,
    Program,
    Regulation,
    Room,
    Section,
    Subject,
    Term,
)
from app.domains.academics.schemas import (
    AcademicYearCreate,
    AcademicYearUpdate,
    BatchCreate,
    BatchUpdate,
    CalendarEventCreate,
    CalendarEventUpdate,
    CampusCreate,
    CampusUpdate,
    CollegeSettingCreate,
    CollegeSettingUpdate,
    CurriculumCreate,
    CurriculumSubjectCreate,
    CurriculumSubjectUpdate,
    CurriculumUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    NumberingFormatCreate,
    NumberingFormatUpdate,
    ProgramCreate,
    ProgramUpdate,
    RegulationCreate,
    RegulationUpdate,
    RoomCreate,
    RoomUpdate,
    SectionCreate,
    SectionUpdate,
    SubjectCreate,
    SubjectUpdate,
    TermCreate,
    TermUpdate,
)
from app.domains.admissions.models import AdmissionCampaign, Application
from app.domains.audit.models import AuditEvent
from app.domains.delivery.models import SubjectOffering, TimetablePeriod
from app.domains.examinations.models import (
    AssessmentScheme,
    ExamSchedule,
    ExamSeatAllocation,
    ExamSession,
    GradeRule,
    InvigilationAssignment,
    PublishedResultLine,
)
from app.domains.fees.models import FeePlan
from app.domains.identity.models import MembershipRoleScope
from app.domains.students.models import (
    StudentEnrollment,
    StudentLifecycleRequest,
    StudentProgression,
)
from app.security_context import ActorContext

ModelType = TypeVar("ModelType")


class AcademicsDomainError(Exception):
    """Represent a controlled domain error translated into a specific HTTP status."""

    def __init__(self, detail: str, status_code: int) -> None:
        """Store a stable API detail message and corresponding status code."""

        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class AcademicsValidationError(AcademicsDomainError):
    """Represent a validation failure mapped to HTTP 422."""

    def __init__(self, detail: str) -> None:
        """Create a validation error with a stable 422 response status."""

        super().__init__(detail=detail, status_code=422)


class AcademicsConflictError(AcademicsDomainError):
    """Represent an in-use academic structure conflict mapped to HTTP 409."""

    def __init__(self, detail: str) -> None:
        """Create a conflict error with a stable 409 response status."""

        super().__init__(detail=detail, status_code=409)


class AcademicsService:
    """Coordinate tenant-safe CRUD operations for academic institutional structures."""

    def __init__(self, session: Session, actor: ActorContext) -> None:
        """Initialize the service with a runtime session and authenticated actor context."""

        self.session = session
        self.actor = actor
        self._set_tenant_context()

    def _set_tenant_context(self) -> None:
        """Configure the session for tenant-isolated queries via app.tenant_id."""

        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self.actor.tenant_id)},
        )

    def _audit(self, action: str, entity_type: str, entity_id: UUID, details: dict[str, object]) -> None:
        """Record a tenant-scoped audit event for a mutation within the same transaction."""

        event = AuditEvent(
            tenant_id=self.actor.tenant_id,
            account_id=self.actor.account_id,
            membership_id=self.actor.membership_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
        self.session.add(event)

    def _require_entity(
        self,
        model: type[ModelType],
        entity_id: UUID,
        entity_label: str,
    ) -> ModelType:
        """Return a tenant-safe parent entity or raise an explicit 422 validation error."""

        entity = self.session.scalar(
            select(model).where(  # type: ignore[arg-type]
                model.id == entity_id,  # type: ignore[attr-defined]
                model.tenant_id == self.actor.tenant_id,  # type: ignore[attr-defined]
            )
        )
        if entity is None:
            raise AcademicsValidationError(f"Invalid {entity_label} reference")
        return entity

    def _scoped_department_ids(self):
        """Select departments visible through institution or department scopes."""

        query = select(Department.id).where(Department.tenant_id == self.actor.tenant_id)
        if self.actor.scopes_of_type("institution"):
            return query
        department_ids = tuple(
            scope.scope_reference_id
            for scope in self.actor.scopes_of_type("department")
            if scope.scope_reference_id is not None
        )
        return query.where(Department.id.in_(department_ids)) if department_ids else query.where(false())

    def _scoped_program_ids(self):
        """Select programs owned by departments visible to the actor."""

        return select(Program.id).where(
            Program.tenant_id == self.actor.tenant_id,
            Program.department_id.in_(self._scoped_department_ids()),
        )

    def _scoped_batch_ids(self):
        """Select batches owned by programs visible to the actor."""

        return select(Batch.id).where(
            Batch.tenant_id == self.actor.tenant_id,
            Batch.program_id.in_(self._scoped_program_ids()),
        )

    def _scoped_curriculum_ids(self):
        """Select curricula owned by programs visible to the actor."""

        return select(Curriculum.id).where(
            Curriculum.tenant_id == self.actor.tenant_id,
            Curriculum.program_id.in_(self._scoped_program_ids()),
        )

    def _program_has_dependents(self, program_id: UUID) -> bool:
        """Return whether any tenant-owned structure or workflow references a program."""

        tenant_id = self.actor.tenant_id
        queries = (
            select(Batch.id).where(Batch.tenant_id == tenant_id, Batch.program_id == program_id),
            select(Curriculum.id).where(
                Curriculum.tenant_id == tenant_id,
                Curriculum.program_id == program_id,
            ),
            select(AdmissionCampaign.id).where(
                AdmissionCampaign.tenant_id == tenant_id,
                AdmissionCampaign.program_id == program_id,
            ),
            select(Application.id).where(
                Application.tenant_id == tenant_id,
                Application.program_id == program_id,
            ),
            select(StudentEnrollment.id).where(
                StudentEnrollment.tenant_id == tenant_id,
                StudentEnrollment.program_id == program_id,
            ),
            select(StudentProgression.id).where(
                StudentProgression.tenant_id == tenant_id,
                StudentProgression.target_program_id == program_id,
            ),
            select(StudentLifecycleRequest.id).where(
                StudentLifecycleRequest.tenant_id == tenant_id,
                StudentLifecycleRequest.target_program_id == program_id,
            ),
            select(FeePlan.id).where(
                FeePlan.tenant_id == tenant_id,
                FeePlan.program_id == program_id,
            ),
            select(AssessmentScheme.id).where(
                AssessmentScheme.tenant_id == tenant_id,
                AssessmentScheme.program_id == program_id,
            ),
            select(MembershipRoleScope.id).where(
                MembershipRoleScope.tenant_id == tenant_id,
                MembershipRoleScope.scope_type == "program",
                MembershipRoleScope.scope_reference_id == program_id,
            ),
        )
        return any(self.session.scalar(query.limit(1)) is not None for query in queries)

    def _subject_has_dependents(self, subject_id: UUID) -> bool:
        """Return whether any tenant-owned structure or workflow references a subject."""

        tenant_id = self.actor.tenant_id
        queries = (
            select(CurriculumSubject.id).where(
                CurriculumSubject.tenant_id == tenant_id,
                CurriculumSubject.subject_id == subject_id,
            ),
            select(SubjectOffering.id).where(
                SubjectOffering.tenant_id == tenant_id,
                SubjectOffering.subject_id == subject_id,
            ),
            select(AssessmentScheme.id).where(
                AssessmentScheme.tenant_id == tenant_id,
                AssessmentScheme.subject_id == subject_id,
            ),
            select(PublishedResultLine.id).where(
                PublishedResultLine.tenant_id == tenant_id,
                PublishedResultLine.subject_id == subject_id,
            ),
        )
        return any(self.session.scalar(query.limit(1)) is not None for query in queries)

    def _batch_has_dependents(self, batch_id: UUID) -> bool:
        """Return whether any tenant-owned structure or workflow references a batch."""

        tenant_id = self.actor.tenant_id
        queries = (
            select(Section.id).where(
                Section.tenant_id == tenant_id,
                Section.batch_id == batch_id,
            ),
            select(StudentEnrollment.id).where(
                StudentEnrollment.tenant_id == tenant_id,
                StudentEnrollment.batch_id == batch_id,
            ),
            select(StudentProgression.id).where(
                StudentProgression.tenant_id == tenant_id,
                StudentProgression.target_batch_id == batch_id,
            ),
            select(StudentLifecycleRequest.id).where(
                StudentLifecycleRequest.tenant_id == tenant_id,
                StudentLifecycleRequest.target_batch_id == batch_id,
            ),
            select(MembershipRoleScope.id).where(
                MembershipRoleScope.tenant_id == tenant_id,
                MembershipRoleScope.scope_type == "batch",
                MembershipRoleScope.scope_reference_id == batch_id,
            ),
        )
        return any(self.session.scalar(query.limit(1)) is not None for query in queries)

    def _section_has_dependents(self, section_id: UUID) -> bool:
        """Return whether any tenant-owned workflow or authorization scope references a section."""

        tenant_id = self.actor.tenant_id
        queries = (
            select(SubjectOffering.id).where(
                SubjectOffering.tenant_id == tenant_id,
                SubjectOffering.section_id == section_id,
            ),
            select(StudentEnrollment.id).where(
                StudentEnrollment.tenant_id == tenant_id,
                StudentEnrollment.section_id == section_id,
            ),
            select(StudentProgression.id).where(
                StudentProgression.tenant_id == tenant_id,
                StudentProgression.target_section_id == section_id,
            ),
            select(StudentLifecycleRequest.id).where(
                StudentLifecycleRequest.tenant_id == tenant_id,
                StudentLifecycleRequest.target_section_id == section_id,
            ),
            select(MembershipRoleScope.id).where(
                MembershipRoleScope.tenant_id == tenant_id,
                MembershipRoleScope.scope_type == "section",
                MembershipRoleScope.scope_reference_id == section_id,
            ),
        )
        return any(self.session.scalar(query.limit(1)) is not None for query in queries)

    def _term_has_dependents(self, term_id: UUID) -> bool:
        """Return whether any tenant-owned delivery, calendar, or examination record uses a term."""

        tenant_id = self.actor.tenant_id
        queries = (
            select(SubjectOffering.id).where(
                SubjectOffering.tenant_id == tenant_id,
                SubjectOffering.term_id == term_id,
            ),
            select(CalendarEvent.id).where(
                CalendarEvent.tenant_id == tenant_id,
                CalendarEvent.term_id == term_id,
            ),
            select(AssessmentScheme.id).where(
                AssessmentScheme.tenant_id == tenant_id,
                AssessmentScheme.term_id == term_id,
            ),
            select(ExamSession.id).where(
                ExamSession.tenant_id == tenant_id,
                ExamSession.term_id == term_id,
            ),
            select(GradeRule.id).where(
                GradeRule.tenant_id == tenant_id,
                GradeRule.term_id == term_id,
            ),
        )
        return any(self.session.scalar(query.limit(1)) is not None for query in queries)

    def _room_has_dependents(self, room_id: UUID) -> bool:
        """Return whether any tenant-owned timetable or examination record uses a room."""

        tenant_id = self.actor.tenant_id
        queries = (
            select(TimetablePeriod.id).where(
                TimetablePeriod.tenant_id == tenant_id,
                TimetablePeriod.room_id == room_id,
            ),
            select(ExamSchedule.id).where(
                ExamSchedule.tenant_id == tenant_id,
                ExamSchedule.room_id == room_id,
            ),
            select(ExamSeatAllocation.id).where(
                ExamSeatAllocation.tenant_id == tenant_id,
                ExamSeatAllocation.room_id == room_id,
            ),
            select(InvigilationAssignment.id).where(
                InvigilationAssignment.tenant_id == tenant_id,
                InvigilationAssignment.room_id == room_id,
            ),
        )
        return any(self.session.scalar(query.limit(1)) is not None for query in queries)

    def _curriculum_has_dependents(self, curriculum_id: UUID) -> bool:
        """Return whether any tenant-owned subject mapping uses a curriculum."""

        return (
            self.session.scalar(
                select(CurriculumSubject.id)
                .where(
                    CurriculumSubject.tenant_id == self.actor.tenant_id,
                    CurriculumSubject.curriculum_id == curriculum_id,
                )
                .limit(1)
            )
            is not None
        )

    def _validate_date_range(self, starts_on: Any, ends_on: Any, context: str) -> None:
        """Validate that the start date does not come after the end date."""

        if starts_on > ends_on:
            raise AcademicsValidationError(f"{context} start date cannot be after end date")

    # Campus operations
    def list_campuses(self, skip: int = 0, limit: int = 100) -> tuple[list[Campus], int]:
        """Retrieve a paginated list of campuses for the current tenant."""

        query = select(Campus).where(Campus.tenant_id == self.actor.tenant_id).order_by(Campus.name)
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_campus(self, campus_id: UUID) -> Campus | None:
        """Retrieve a single campus by ID within the current tenant."""

        return self.session.scalar(
            select(Campus).where(Campus.id == campus_id, Campus.tenant_id == self.actor.tenant_id)
        )

    def create_campus(self, payload: CampusCreate) -> Campus:
        """Create a new campus for the current tenant and audit the operation."""

        campus = Campus(
            tenant_id=self.actor.tenant_id,
            code=payload.code,
            name=payload.name,
            address=payload.address,
            status=payload.status,
        )
        self.session.add(campus)
        self.session.flush()
        self._audit("create", "campus", campus.id, {"code": payload.code, "name": payload.name})
        return campus

    def update_campus(self, campus_id: UUID, payload: CampusUpdate) -> Campus | None:
        """Update an existing campus and audit the operation."""

        campus = self.get_campus(campus_id)
        if campus is None:
            return None
        changes = {}
        if payload.name is not None:
            changes["name"] = (campus.name, payload.name)
            campus.name = payload.name
        if payload.address is not None:
            changes["address"] = (campus.address, payload.address)
            campus.address = payload.address
        if payload.status is not None:
            changes["status"] = (campus.status, payload.status)
            campus.status = payload.status
        if changes:
            self.session.flush()
            self._audit("update", "campus", campus.id, changes)
        return campus

    # Academic Year operations
    def list_academic_years(self, skip: int = 0, limit: int = 100) -> tuple[list[AcademicYear], int]:
        """Retrieve a paginated list of academic years for the current tenant."""

        query = (
            select(AcademicYear)
            .where(AcademicYear.tenant_id == self.actor.tenant_id)
            .order_by(AcademicYear.starts_on.desc())
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_academic_year(self, year_id: UUID) -> AcademicYear | None:
        """Retrieve a single academic year by ID within the current tenant."""

        return self.session.scalar(
            select(AcademicYear).where(
                AcademicYear.id == year_id, AcademicYear.tenant_id == self.actor.tenant_id
            )
        )

    def create_academic_year(self, payload: AcademicYearCreate) -> AcademicYear:
        """Create a new academic year for the current tenant and audit the operation."""

        year = AcademicYear(
            tenant_id=self.actor.tenant_id,
            code=payload.code,
            display_name=payload.display_name,
            starts_on=payload.starts_on,
            ends_on=payload.ends_on,
            status=payload.status,
        )
        self.session.add(year)
        self.session.flush()
        self._audit("create", "academic_year", year.id, {"code": payload.code})
        return year

    def update_academic_year(self, year_id: UUID, payload: AcademicYearUpdate) -> AcademicYear | None:
        """Update an existing academic year and audit the operation."""

        year = self.get_academic_year(year_id)
        if year is None:
            return None
        changes = {}
        if payload.display_name is not None:
            changes["display_name"] = (year.display_name, payload.display_name)
            year.display_name = payload.display_name
        if payload.starts_on is not None:
            changes["starts_on"] = (str(year.starts_on), str(payload.starts_on))
            year.starts_on = payload.starts_on
        if payload.ends_on is not None:
            changes["ends_on"] = (str(year.ends_on), str(payload.ends_on))
            year.ends_on = payload.ends_on
        if payload.status is not None:
            changes["status"] = (year.status, payload.status)
            year.status = payload.status
        if changes:
            self.session.flush()
            self._audit("update", "academic_year", year.id, changes)
        return year

    # Term operations
    def list_terms(self, skip: int = 0, limit: int = 100) -> tuple[list[Term], int]:
        """Retrieve a paginated list of terms for the current tenant."""

        query = (
            select(Term)
            .where(Term.tenant_id == self.actor.tenant_id)
            .order_by(Term.academic_year_id, Term.starts_on)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_term(self, term_id: UUID) -> Term | None:
        """Retrieve a single term by ID within the current tenant."""

        return self.session.scalar(
            select(Term).where(Term.id == term_id, Term.tenant_id == self.actor.tenant_id)
        )

    def create_term(self, payload: TermCreate) -> Term:
        """Create a new term for the current tenant and audit the operation."""

        term = Term(
            tenant_id=self.actor.tenant_id,
            academic_year_id=payload.academic_year_id,
            code=payload.code,
            display_name=payload.display_name,
            starts_on=payload.starts_on,
            ends_on=payload.ends_on,
            status=payload.status,
        )
        self.session.add(term)
        self.session.flush()
        self._audit("create", "term", term.id, {"code": payload.code})
        return term

    def update_term(self, term_id: UUID, payload: TermUpdate) -> Term | None:
        """Update an existing term and audit the operation."""

        term = self.get_term(term_id)
        if term is None:
            return None
        changes = {}
        if (
            payload.academic_year_id is not None
            and payload.academic_year_id != term.academic_year_id
        ):
            self._require_entity(AcademicYear, payload.academic_year_id, "academic_year_id")
            if self._term_has_dependents(term.id):
                raise AcademicsConflictError(
                    "Term academic year cannot be changed after dependent records exist"
                )
            changes["academic_year_id"] = (
                str(term.academic_year_id),
                str(payload.academic_year_id),
            )
            term.academic_year_id = payload.academic_year_id
        if payload.display_name is not None:
            changes["display_name"] = (term.display_name, payload.display_name)
            term.display_name = payload.display_name
        if payload.starts_on is not None:
            changes["starts_on"] = (str(term.starts_on), str(payload.starts_on))
            term.starts_on = payload.starts_on
        if payload.ends_on is not None:
            changes["ends_on"] = (str(term.ends_on), str(payload.ends_on))
            term.ends_on = payload.ends_on
        if payload.status is not None:
            changes["status"] = (term.status, payload.status)
            term.status = payload.status
        if changes:
            self.session.flush()
            self._audit("update", "term", term.id, changes)
        return term

    # Department operations
    def list_departments(self, skip: int = 0, limit: int = 100) -> tuple[list[Department], int]:
        """Retrieve a paginated list of departments for the current tenant."""

        query = (
            select(Department)
            .where(
                Department.tenant_id == self.actor.tenant_id,
                Department.id.in_(self._scoped_department_ids()),
            )
            .order_by(Department.name)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_department(self, department_id: UUID) -> Department | None:
        """Retrieve a single department by ID within the current tenant."""

        return self.session.scalar(
            select(Department).where(
                Department.id == department_id,
                Department.tenant_id == self.actor.tenant_id,
                Department.id.in_(self._scoped_department_ids()),
            )
        )

    def create_department(self, payload: DepartmentCreate) -> Department:
        """Create a new department for the current tenant and audit the operation."""

        department = Department(
            tenant_id=self.actor.tenant_id,
            code=payload.code,
            name=payload.name,
            status=payload.status,
        )
        self.session.add(department)
        self.session.flush()
        self._audit("create", "department", department.id, {"code": payload.code, "name": payload.name})
        return department

    def update_department(self, department_id: UUID, payload: DepartmentUpdate) -> Department | None:
        """Update an existing department and audit the operation."""

        department = self.get_department(department_id)
        if department is None:
            return None
        changes = {}
        if payload.name is not None:
            changes["name"] = (department.name, payload.name)
            department.name = payload.name
        if payload.status is not None:
            changes["status"] = (department.status, payload.status)
            department.status = payload.status
        if changes:
            self.session.flush()
            self._audit("update", "department", department.id, changes)
        return department

    # Program operations
    def list_programs(self, skip: int = 0, limit: int = 100) -> tuple[list[Program], int]:
        """Retrieve a paginated list of programs for the current tenant."""

        query = (
            select(Program)
            .where(
                Program.tenant_id == self.actor.tenant_id,
                Program.id.in_(self._scoped_program_ids()),
            )
            .order_by(Program.name)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_program(self, program_id: UUID) -> Program | None:
        """Retrieve a single program by ID within the current tenant."""

        return self.session.scalar(
            select(Program).where(
                Program.id == program_id,
                Program.tenant_id == self.actor.tenant_id,
                Program.id.in_(self._scoped_program_ids()),
            )
        )

    def create_program(self, payload: ProgramCreate) -> Program:
        """Create a new program for the current tenant and audit the operation."""

        program = Program(
            tenant_id=self.actor.tenant_id,
            department_id=payload.department_id,
            code=payload.code,
            name=payload.name,
            degree_level=payload.degree_level,
            duration_years=payload.duration_years,
            status=payload.status,
        )
        self.session.add(program)
        self.session.flush()
        self._audit("create", "program", program.id, {"code": payload.code, "name": payload.name})
        return program

    def update_program(self, program_id: UUID, payload: ProgramUpdate) -> Program | None:
        """Update an existing program and audit the operation."""

        program = self.get_program(program_id)
        if program is None:
            return None
        changes = {}
        if payload.department_id is not None and payload.department_id != program.department_id:
            self._require_entity(Department, payload.department_id, "department_id")
            if self._program_has_dependents(program.id):
                raise AcademicsConflictError(
                    "Program department cannot be changed after dependent records exist"
                )
            changes["department_id"] = (
                str(program.department_id),
                str(payload.department_id),
            )
            program.department_id = payload.department_id
        if payload.name is not None:
            changes["name"] = (program.name, payload.name)
            program.name = payload.name
        if payload.degree_level is not None:
            changes["degree_level"] = (program.degree_level, payload.degree_level)
            program.degree_level = payload.degree_level
        if payload.duration_years is not None:
            changes["duration_years"] = (program.duration_years, payload.duration_years)
            program.duration_years = payload.duration_years
        if payload.status is not None:
            changes["status"] = (program.status, payload.status)
            program.status = payload.status
        if changes:
            self.session.flush()
            self._audit("update", "program", program.id, changes)
        return program

    # Subject operations
    def list_subjects(self, skip: int = 0, limit: int = 100) -> tuple[list[Subject], int]:
        """Retrieve a paginated list of subjects for the current tenant."""

        query = (
            select(Subject)
            .where(
                Subject.tenant_id == self.actor.tenant_id,
                Subject.department_id.in_(self._scoped_department_ids()),
            )
            .order_by(Subject.name)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_subject(self, subject_id: UUID) -> Subject | None:
        """Retrieve a single subject by ID within the current tenant."""

        return self.session.scalar(
            select(Subject).where(
                Subject.id == subject_id,
                Subject.tenant_id == self.actor.tenant_id,
                Subject.department_id.in_(self._scoped_department_ids()),
            )
        )

    def create_subject(self, payload: SubjectCreate) -> Subject:
        """Create a new subject for the current tenant and audit the operation."""

        subject = Subject(
            tenant_id=self.actor.tenant_id,
            department_id=payload.department_id,
            code=payload.code,
            name=payload.name,
            credits=payload.credits,
            status=payload.status,
        )
        self.session.add(subject)
        self.session.flush()
        self._audit("create", "subject", subject.id, {"code": payload.code, "name": payload.name})
        return subject

    def update_subject(self, subject_id: UUID, payload: SubjectUpdate) -> Subject | None:
        """Update an existing subject and audit the operation."""

        subject = self.get_subject(subject_id)
        if subject is None:
            return None
        changes = {}
        if payload.department_id is not None and payload.department_id != subject.department_id:
            self._require_entity(Department, payload.department_id, "department_id")
            if self._subject_has_dependents(subject.id):
                raise AcademicsConflictError(
                    "Subject department cannot be changed after dependent records exist"
                )
            changes["department_id"] = (
                str(subject.department_id),
                str(payload.department_id),
            )
            subject.department_id = payload.department_id
        if payload.name is not None:
            changes["name"] = (subject.name, payload.name)
            subject.name = payload.name
        if payload.credits is not None:
            changes["credits"] = (subject.credits, payload.credits)
            subject.credits = payload.credits
        if payload.status is not None:
            changes["status"] = (subject.status, payload.status)
            subject.status = payload.status
        if changes:
            self.session.flush()
            self._audit("update", "subject", subject.id, changes)
        return subject

    # Batch operations
    def list_batches(self, skip: int = 0, limit: int = 100) -> tuple[list[Batch], int]:
        """Retrieve a paginated list of batches for the current tenant."""

        query = (
            select(Batch)
            .where(
                Batch.tenant_id == self.actor.tenant_id,
                Batch.id.in_(self._scoped_batch_ids()),
            )
            .order_by(Batch.admission_year.desc(), Batch.display_name)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_batch(self, batch_id: UUID) -> Batch | None:
        """Retrieve a single batch by ID within the current tenant."""

        return self.session.scalar(
            select(Batch).where(
                Batch.id == batch_id,
                Batch.tenant_id == self.actor.tenant_id,
                Batch.id.in_(self._scoped_batch_ids()),
            )
        )

    def create_batch(self, payload: BatchCreate) -> Batch:
        """Create a new batch for the current tenant and audit the operation."""

        batch = Batch(
            tenant_id=self.actor.tenant_id,
            program_id=payload.program_id,
            admission_year=payload.admission_year,
            display_name=payload.display_name,
            status=payload.status,
        )
        self.session.add(batch)
        self.session.flush()
        self._audit("create", "batch", batch.id, {"admission_year": payload.admission_year})
        return batch

    def update_batch(self, batch_id: UUID, payload: BatchUpdate) -> Batch | None:
        """Update an existing batch and audit the operation."""

        batch = self.get_batch(batch_id)
        if batch is None:
            return None
        changes = {}
        if payload.program_id is not None and payload.program_id != batch.program_id:
            self._require_entity(Program, payload.program_id, "program_id")
            if self._batch_has_dependents(batch.id):
                raise AcademicsConflictError(
                    "Batch program cannot be changed after dependent records exist"
                )
            changes["program_id"] = (str(batch.program_id), str(payload.program_id))
            batch.program_id = payload.program_id
        if payload.display_name is not None:
            changes["display_name"] = (batch.display_name, payload.display_name)
            batch.display_name = payload.display_name
        if payload.status is not None:
            changes["status"] = (batch.status, payload.status)
            batch.status = payload.status
        if changes:
            self.session.flush()
            self._audit("update", "batch", batch.id, changes)
        return batch

    # Section operations
    def list_sections(self, skip: int = 0, limit: int = 100) -> tuple[list[Section], int]:
        """Retrieve a paginated list of sections for the current tenant."""

        query = (
            select(Section)
            .where(
                Section.tenant_id == self.actor.tenant_id,
                Section.batch_id.in_(self._scoped_batch_ids()),
            )
            .order_by(Section.batch_id, Section.code)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_section(self, section_id: UUID) -> Section | None:
        """Retrieve a single section by ID within the current tenant."""

        return self.session.scalar(
            select(Section).where(
                Section.id == section_id,
                Section.tenant_id == self.actor.tenant_id,
                Section.batch_id.in_(self._scoped_batch_ids()),
            )
        )

    def create_section(self, payload: SectionCreate) -> Section:
        """Create a new section for the current tenant and audit the operation."""

        section = Section(
            tenant_id=self.actor.tenant_id,
            batch_id=payload.batch_id,
            code=payload.code,
            display_name=payload.display_name,
            max_capacity=payload.max_capacity,
            status=payload.status,
        )
        self.session.add(section)
        self.session.flush()
        self._audit("create", "section", section.id, {"code": payload.code})
        return section

    def update_section(self, section_id: UUID, payload: SectionUpdate) -> Section | None:
        """Update an existing section and audit the operation."""

        section = self.get_section(section_id)
        if section is None:
            return None
        changes = {}
        if payload.batch_id is not None and payload.batch_id != section.batch_id:
            self._require_entity(Batch, payload.batch_id, "batch_id")
            if self._section_has_dependents(section.id):
                raise AcademicsConflictError(
                    "Section batch cannot be changed after dependent records exist"
                )
            changes["batch_id"] = (str(section.batch_id), str(payload.batch_id))
            section.batch_id = payload.batch_id
        if payload.display_name is not None:
            changes["display_name"] = (section.display_name, payload.display_name)
            section.display_name = payload.display_name
        if payload.max_capacity is not None:
            changes["max_capacity"] = (section.max_capacity, payload.max_capacity)
            section.max_capacity = payload.max_capacity
        if payload.status is not None:
            changes["status"] = (section.status, payload.status)
            section.status = payload.status
        if changes:
            self.session.flush()
            self._audit("update", "section", section.id, changes)
        return section

    # Room operations
    def list_rooms(self, skip: int = 0, limit: int = 100) -> tuple[list[Room], int]:
        """Retrieve a paginated list of rooms for the current tenant."""

        query = (
            select(Room)
            .where(Room.tenant_id == self.actor.tenant_id)
            .order_by(Room.campus_id, Room.code)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_room(self, room_id: UUID) -> Room | None:
        """Retrieve a single room by ID within the current tenant."""

        return self.session.scalar(
            select(Room).where(Room.id == room_id, Room.tenant_id == self.actor.tenant_id)
        )

    def create_room(self, payload: RoomCreate) -> Room:
        """Create a new room for the current tenant and audit the operation."""

        room = Room(
            tenant_id=self.actor.tenant_id,
            campus_id=payload.campus_id,
            code=payload.code,
            name=payload.name,
            room_type=payload.room_type,
            capacity=payload.capacity,
            has_projector=payload.has_projector,
            has_computers=payload.has_computers,
            status=payload.status,
        )
        self.session.add(room)
        self.session.flush()
        self._audit("create", "room", room.id, {"code": payload.code, "name": payload.name})
        return room

    def update_room(self, room_id: UUID, payload: RoomUpdate) -> Room | None:
        """Update an existing room and audit the operation."""

        room = self.get_room(room_id)
        if room is None:
            return None
        changes = {}
        if payload.campus_id is not None and payload.campus_id != room.campus_id:
            self._require_entity(Campus, payload.campus_id, "campus_id")
            if self._room_has_dependents(room.id):
                raise AcademicsConflictError(
                    "Room campus cannot be changed after dependent records exist"
                )
            changes["campus_id"] = (str(room.campus_id), str(payload.campus_id))
            room.campus_id = payload.campus_id
        if payload.name is not None:
            changes["name"] = (room.name, payload.name)
            room.name = payload.name
        if payload.room_type is not None:
            changes["room_type"] = (room.room_type, payload.room_type)
            room.room_type = payload.room_type
        if payload.capacity is not None:
            changes["capacity"] = (room.capacity, payload.capacity)
            room.capacity = payload.capacity
        if payload.has_projector is not None:
            changes["has_projector"] = (room.has_projector, payload.has_projector)
            room.has_projector = payload.has_projector
        if payload.has_computers is not None:
            changes["has_computers"] = (room.has_computers, payload.has_computers)
            room.has_computers = payload.has_computers
        if payload.status is not None:
            changes["status"] = (room.status, payload.status)
            room.status = payload.status
        if changes:
            self.session.flush()
            self._audit("update", "room", room.id, changes)
        return room

    # College Setting operations
    def list_college_settings(self, skip: int = 0, limit: int = 100) -> tuple[list[CollegeSetting], int]:
        """Retrieve tenant college settings using the same paginated response contract."""

        query = (
            select(CollegeSetting)
            .where(CollegeSetting.tenant_id == self.actor.tenant_id)
            .order_by(CollegeSetting.created_at.asc())
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_college_setting(self, setting_id: UUID) -> CollegeSetting | None:
        """Retrieve one college setting record by ID for the current tenant."""

        return self.session.scalar(
            select(CollegeSetting).where(
                CollegeSetting.id == setting_id,
                CollegeSetting.tenant_id == self.actor.tenant_id,
            )
        )

    def create_college_setting(self, payload: CollegeSettingCreate) -> CollegeSetting:
        """Create one college setting record for the tenant and audit the mutation."""

        setting = CollegeSetting(
            tenant_id=self.actor.tenant_id,
            institution_name=payload.institution_name,
            short_name=payload.short_name,
            timezone=payload.timezone,
            locale=payload.locale,
        )
        self.session.add(setting)
        self.session.flush()
        self._audit("create", "college_setting", setting.id, {"institution_name": payload.institution_name})
        return setting

    def update_college_setting(
        self,
        setting_id: UUID,
        payload: CollegeSettingUpdate,
    ) -> CollegeSetting | None:
        """Update one college setting record and audit changed fields only."""

        setting = self.get_college_setting(setting_id)
        if setting is None:
            return None
        changes: dict[str, tuple[object, object]] = {}
        if payload.institution_name is not None:
            changes["institution_name"] = (setting.institution_name, payload.institution_name)
            setting.institution_name = payload.institution_name
        if payload.short_name is not None:
            changes["short_name"] = (setting.short_name, payload.short_name)
            setting.short_name = payload.short_name
        if payload.timezone is not None:
            changes["timezone"] = (setting.timezone, payload.timezone)
            setting.timezone = payload.timezone
        if payload.locale is not None:
            changes["locale"] = (setting.locale, payload.locale)
            setting.locale = payload.locale
        if changes:
            self.session.flush()
            self._audit("update", "college_setting", setting.id, changes)
        return setting

    # Regulation operations
    def list_regulations(self, skip: int = 0, limit: int = 100) -> tuple[list[Regulation], int]:
        """Retrieve a paginated list of regulations for the current tenant."""

        query = (
            select(Regulation)
            .where(Regulation.tenant_id == self.actor.tenant_id)
            .order_by(Regulation.effective_from_year.desc(), Regulation.code)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_regulation(self, regulation_id: UUID) -> Regulation | None:
        """Retrieve one regulation by ID within the current tenant."""

        return self.session.scalar(
            select(Regulation).where(
                Regulation.id == regulation_id,
                Regulation.tenant_id == self.actor.tenant_id,
            )
        )

    def create_regulation(self, payload: RegulationCreate) -> Regulation:
        """Create one regulation for the tenant and audit the mutation."""

        regulation = Regulation(
            tenant_id=self.actor.tenant_id,
            code=payload.code,
            title=payload.title,
            effective_from_year=payload.effective_from_year,
            status=payload.status,
        )
        self.session.add(regulation)
        self.session.flush()
        self._audit("create", "regulation", regulation.id, {"code": payload.code})
        return regulation

    def update_regulation(self, regulation_id: UUID, payload: RegulationUpdate) -> Regulation | None:
        """Update one regulation and audit changed fields only."""

        regulation = self.get_regulation(regulation_id)
        if regulation is None:
            return None
        changes: dict[str, tuple[object, object]] = {}
        if payload.title is not None:
            changes["title"] = (regulation.title, payload.title)
            regulation.title = payload.title
        if payload.effective_from_year is not None:
            changes["effective_from_year"] = (
                regulation.effective_from_year,
                payload.effective_from_year,
            )
            regulation.effective_from_year = payload.effective_from_year
        if payload.status is not None:
            changes["status"] = (regulation.status, payload.status)
            regulation.status = payload.status
        if changes:
            self.session.flush()
            self._audit("update", "regulation", regulation.id, changes)
        return regulation

    # Curriculum operations
    def list_curricula(self, skip: int = 0, limit: int = 100) -> tuple[list[Curriculum], int]:
        """Retrieve a paginated list of curricula for the current tenant."""

        query = (
            select(Curriculum)
            .where(
                Curriculum.tenant_id == self.actor.tenant_id,
                Curriculum.id.in_(self._scoped_curriculum_ids()),
            )
            .order_by(Curriculum.code)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_curriculum(self, curriculum_id: UUID) -> Curriculum | None:
        """Retrieve one curriculum by ID within the current tenant."""

        return self.session.scalar(
            select(Curriculum).where(
                Curriculum.id == curriculum_id,
                Curriculum.tenant_id == self.actor.tenant_id,
                Curriculum.id.in_(self._scoped_curriculum_ids()),
            )
        )

    def create_curriculum(self, payload: CurriculumCreate) -> Curriculum:
        """Create one curriculum after validating parent references are tenant-safe."""

        self._require_entity(Program, payload.program_id, "program_id")
        self._require_entity(Regulation, payload.regulation_id, "regulation_id")
        curriculum = Curriculum(
            tenant_id=self.actor.tenant_id,
            program_id=payload.program_id,
            regulation_id=payload.regulation_id,
            code=payload.code,
            title=payload.title,
            total_credits=payload.total_credits,
            status=payload.status,
        )
        self.session.add(curriculum)
        self.session.flush()
        self._audit("create", "curriculum", curriculum.id, {"code": payload.code})
        return curriculum

    def _update_curriculum_parents(
        self,
        curriculum: Curriculum,
        payload: CurriculumUpdate,
        changes: dict[str, tuple[object, object]],
    ) -> None:
        """Validate and apply mutable curriculum parent relationships."""

        program_changed = (
            payload.program_id is not None and payload.program_id != curriculum.program_id
        )
        regulation_changed = (
            payload.regulation_id is not None
            and payload.regulation_id != curriculum.regulation_id
        )
        if program_changed:
            self._require_entity(Program, payload.program_id, "program_id")
        if regulation_changed:
            self._require_entity(Regulation, payload.regulation_id, "regulation_id")
        if (program_changed or regulation_changed) and self._curriculum_has_dependents(curriculum.id):
            raise AcademicsConflictError(
                "Curriculum parents cannot be changed after subject mappings exist"
            )
        if program_changed and payload.program_id is not None:
            changes["program_id"] = (str(curriculum.program_id), str(payload.program_id))
            curriculum.program_id = payload.program_id
        if regulation_changed and payload.regulation_id is not None:
            changes["regulation_id"] = (
                str(curriculum.regulation_id),
                str(payload.regulation_id),
            )
            curriculum.regulation_id = payload.regulation_id

    def update_curriculum(self, curriculum_id: UUID, payload: CurriculumUpdate) -> Curriculum | None:
        """Update one curriculum and audit changed fields only."""

        curriculum = self.get_curriculum(curriculum_id)
        if curriculum is None:
            return None
        changes: dict[str, tuple[object, object]] = {}
        self._update_curriculum_parents(curriculum, payload, changes)
        if payload.title is not None:
            changes["title"] = (curriculum.title, payload.title)
            curriculum.title = payload.title
        if payload.total_credits is not None:
            changes["total_credits"] = (curriculum.total_credits, payload.total_credits)
            curriculum.total_credits = payload.total_credits
        if payload.status is not None:
            changes["status"] = (curriculum.status, payload.status)
            curriculum.status = payload.status
        if changes:
            self.session.flush()
            self._audit("update", "curriculum", curriculum.id, changes)
        return curriculum

    # Curriculum Subject operations
    def list_curriculum_subjects(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[CurriculumSubject], int]:
        """Retrieve a paginated list of curriculum-subject mappings for the tenant."""

        query = (
            select(CurriculumSubject)
            .where(
                CurriculumSubject.tenant_id == self.actor.tenant_id,
                CurriculumSubject.curriculum_id.in_(self._scoped_curriculum_ids()),
            )
            .order_by(CurriculumSubject.curriculum_id, CurriculumSubject.term_number)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_curriculum_subject(self, mapping_id: UUID) -> CurriculumSubject | None:
        """Retrieve one curriculum-subject mapping by ID within the tenant."""

        return self.session.scalar(
            select(CurriculumSubject).where(
                CurriculumSubject.id == mapping_id,
                CurriculumSubject.tenant_id == self.actor.tenant_id,
                CurriculumSubject.curriculum_id.in_(self._scoped_curriculum_ids()),
            )
        )

    def create_curriculum_subject(self, payload: CurriculumSubjectCreate) -> CurriculumSubject:
        """Create one curriculum-subject mapping after validating tenant-safe parents."""

        self._require_entity(Curriculum, payload.curriculum_id, "curriculum_id")
        self._require_entity(Subject, payload.subject_id, "subject_id")
        mapping = CurriculumSubject(
            tenant_id=self.actor.tenant_id,
            curriculum_id=payload.curriculum_id,
            subject_id=payload.subject_id,
            term_number=payload.term_number,
            is_elective=payload.is_elective,
            credits_override=payload.credits_override,
        )
        self.session.add(mapping)
        self.session.flush()
        self._audit(
            "create",
            "curriculum_subject",
            mapping.id,
            {"curriculum_id": str(payload.curriculum_id), "subject_id": str(payload.subject_id)},
        )
        return mapping

    def update_curriculum_subject(
        self,
        mapping_id: UUID,
        payload: CurriculumSubjectUpdate,
    ) -> CurriculumSubject | None:
        """Update one curriculum-subject mapping and audit changed fields only."""

        mapping = self.get_curriculum_subject(mapping_id)
        if mapping is None:
            return None
        changes: dict[str, tuple[object, object]] = {}
        if payload.curriculum_id is not None and payload.curriculum_id != mapping.curriculum_id:
            self._require_entity(Curriculum, payload.curriculum_id, "curriculum_id")
            changes["curriculum_id"] = (
                str(mapping.curriculum_id),
                str(payload.curriculum_id),
            )
            mapping.curriculum_id = payload.curriculum_id
        if payload.subject_id is not None and payload.subject_id != mapping.subject_id:
            self._require_entity(Subject, payload.subject_id, "subject_id")
            changes["subject_id"] = (str(mapping.subject_id), str(payload.subject_id))
            mapping.subject_id = payload.subject_id
        if payload.term_number is not None:
            changes["term_number"] = (mapping.term_number, payload.term_number)
            mapping.term_number = payload.term_number
        if payload.is_elective is not None:
            changes["is_elective"] = (mapping.is_elective, payload.is_elective)
            mapping.is_elective = payload.is_elective
        if payload.credits_override is not None:
            changes["credits_override"] = (mapping.credits_override, payload.credits_override)
            mapping.credits_override = payload.credits_override
        if changes:
            self.session.flush()
            self._audit("update", "curriculum_subject", mapping.id, changes)
        return mapping

    # Calendar Event operations
    def list_calendar_events(self, skip: int = 0, limit: int = 100) -> tuple[list[CalendarEvent], int]:
        """Retrieve a paginated list of calendar events for the current tenant."""

        query = (
            select(CalendarEvent)
            .where(CalendarEvent.tenant_id == self.actor.tenant_id)
            .order_by(CalendarEvent.starts_on.desc(), CalendarEvent.name)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_calendar_event(self, event_id: UUID) -> CalendarEvent | None:
        """Retrieve one calendar event by ID within the current tenant."""

        return self.session.scalar(
            select(CalendarEvent).where(
                CalendarEvent.id == event_id,
                CalendarEvent.tenant_id == self.actor.tenant_id,
            )
        )

    def create_calendar_event(self, payload: CalendarEventCreate) -> CalendarEvent:
        """Create one calendar event after validating parent references and date bounds."""

        year = self._require_entity(AcademicYear, payload.academic_year_id, "academic_year_id")
        term = None
        if payload.term_id is not None:
            term = self._require_entity(Term, payload.term_id, "term_id")
            if term.academic_year_id != year.id:
                raise AcademicsValidationError("term_id must belong to the given academic_year_id")
        self._validate_date_range(payload.starts_on, payload.ends_on, "calendar event")
        event = CalendarEvent(
            tenant_id=self.actor.tenant_id,
            academic_year_id=payload.academic_year_id,
            term_id=term.id if term is not None else None,
            name=payload.name,
            event_type=payload.event_type,
            starts_on=payload.starts_on,
            ends_on=payload.ends_on,
            is_holiday=payload.is_holiday,
            status=payload.status,
        )
        self.session.add(event)
        self.session.flush()
        self._audit("create", "calendar_event", event.id, {"name": payload.name})
        return event

    def _update_calendar_event_parents(
        self,
        event: CalendarEvent,
        payload: CalendarEventUpdate,
        changes: dict[str, tuple[object, object]],
    ) -> None:
        """Validate and apply one calendar event's Academic Year and optional Term."""

        year_changed = (
            payload.academic_year_id is not None
            and payload.academic_year_id != event.academic_year_id
        )
        if year_changed:
            self._require_entity(AcademicYear, payload.academic_year_id, "academic_year_id")
        next_year_id = payload.academic_year_id if year_changed else event.academic_year_id
        term_supplied = "term_id" in payload.model_fields_set
        next_term_id = payload.term_id if term_supplied else event.term_id
        if next_term_id is not None:
            term = self._require_entity(Term, next_term_id, "term_id")
            if term.academic_year_id != next_year_id:
                raise AcademicsValidationError(
                    "term_id must belong to the given academic_year_id"
                )
        if year_changed and payload.academic_year_id is not None:
            changes["academic_year_id"] = (
                str(event.academic_year_id),
                str(payload.academic_year_id),
            )
            event.academic_year_id = payload.academic_year_id
        if term_supplied and next_term_id != event.term_id:
            changes["term_id"] = (
                str(event.term_id) if event.term_id is not None else None,
                str(next_term_id) if next_term_id is not None else None,
            )
            event.term_id = next_term_id

    def update_calendar_event(self, event_id: UUID, payload: CalendarEventUpdate) -> CalendarEvent | None:
        """Update one calendar event and audit changed fields only."""

        event = self.get_calendar_event(event_id)
        if event is None:
            return None
        changes: dict[str, tuple[object, object]] = {}
        self._update_calendar_event_parents(event, payload, changes)
        start_date = payload.starts_on if payload.starts_on is not None else event.starts_on
        end_date = payload.ends_on if payload.ends_on is not None else event.ends_on
        self._validate_date_range(start_date, end_date, "calendar event")
        if payload.name is not None:
            changes["name"] = (event.name, payload.name)
            event.name = payload.name
        if payload.event_type is not None:
            changes["event_type"] = (event.event_type, payload.event_type)
            event.event_type = payload.event_type
        if payload.starts_on is not None:
            changes["starts_on"] = (str(event.starts_on), str(payload.starts_on))
            event.starts_on = payload.starts_on
        if payload.ends_on is not None:
            changes["ends_on"] = (str(event.ends_on), str(payload.ends_on))
            event.ends_on = payload.ends_on
        if payload.is_holiday is not None:
            changes["is_holiday"] = (event.is_holiday, payload.is_holiday)
            event.is_holiday = payload.is_holiday
        if payload.status is not None:
            changes["status"] = (event.status, payload.status)
            event.status = payload.status
        if changes:
            self.session.flush()
            self._audit("update", "calendar_event", event.id, changes)
        return event

    # Numbering Format operations
    def list_numbering_formats(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[NumberingFormat], int]:
        """Retrieve a paginated list of numbering formats for the current tenant."""

        query = (
            select(NumberingFormat)
            .where(NumberingFormat.tenant_id == self.actor.tenant_id)
            .order_by(NumberingFormat.code)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_numbering_format(self, numbering_format_id: UUID) -> NumberingFormat | None:
        """Retrieve one numbering format by ID within the current tenant."""

        return self.session.scalar(
            select(NumberingFormat).where(
                NumberingFormat.id == numbering_format_id,
                NumberingFormat.tenant_id == self.actor.tenant_id,
            )
        )

    def create_numbering_format(self, payload: NumberingFormatCreate) -> NumberingFormat:
        """Create one numbering format for the tenant and audit the mutation."""

        numbering_format = NumberingFormat(
            tenant_id=self.actor.tenant_id,
            code=payload.code,
            entity_type=payload.entity_type,
            prefix=payload.prefix,
            suffix=payload.suffix,
            padding=payload.padding,
            next_number=payload.next_number,
            reset_frequency=payload.reset_frequency,
        )
        self.session.add(numbering_format)
        self.session.flush()
        self._audit("create", "numbering_format", numbering_format.id, {"code": payload.code})
        return numbering_format

    def update_numbering_format(
        self,
        numbering_format_id: UUID,
        payload: NumberingFormatUpdate,
    ) -> NumberingFormat | None:
        """Update one numbering format and audit changed fields only."""

        numbering_format = self.get_numbering_format(numbering_format_id)
        if numbering_format is None:
            return None
        changes: dict[str, tuple[object, object]] = {}
        if payload.prefix is not None:
            changes["prefix"] = (numbering_format.prefix, payload.prefix)
            numbering_format.prefix = payload.prefix
        if payload.suffix is not None:
            changes["suffix"] = (numbering_format.suffix, payload.suffix)
            numbering_format.suffix = payload.suffix
        if payload.padding is not None:
            changes["padding"] = (numbering_format.padding, payload.padding)
            numbering_format.padding = payload.padding
        if payload.next_number is not None:
            changes["next_number"] = (numbering_format.next_number, payload.next_number)
            numbering_format.next_number = payload.next_number
        if payload.reset_frequency is not None:
            changes["reset_frequency"] = (numbering_format.reset_frequency, payload.reset_frequency)
            numbering_format.reset_frequency = payload.reset_frequency
        if changes:
            self.session.flush()
            self._audit("update", "numbering_format", numbering_format.id, changes)
        return numbering_format

    # Overview
    def get_overview(self) -> dict[str, int]:
        """Return aggregate counts of configured academic structures for the tenant."""

        return {
            "campuses": self.session.scalar(
                select(func.count()).select_from(Campus).where(Campus.tenant_id == self.actor.tenant_id)
            )
            or 0,
            "academic_years": self.session.scalar(
                select(func.count())
                .select_from(AcademicYear)
                .where(AcademicYear.tenant_id == self.actor.tenant_id)
            )
            or 0,
            "terms": self.session.scalar(
                select(func.count()).select_from(Term).where(Term.tenant_id == self.actor.tenant_id)
            )
            or 0,
            "departments": self.session.scalar(
                select(func.count())
                .select_from(Department)
                .where(
                    Department.tenant_id == self.actor.tenant_id,
                    Department.id.in_(self._scoped_department_ids()),
                )
            )
            or 0,
            "programs": self.session.scalar(
                select(func.count())
                .select_from(Program)
                .where(
                    Program.tenant_id == self.actor.tenant_id,
                    Program.id.in_(self._scoped_program_ids()),
                )
            )
            or 0,
            "subjects": self.session.scalar(
                select(func.count())
                .select_from(Subject)
                .where(
                    Subject.tenant_id == self.actor.tenant_id,
                    Subject.department_id.in_(self._scoped_department_ids()),
                )
            )
            or 0,
            "batches": self.session.scalar(
                select(func.count())
                .select_from(Batch)
                .where(
                    Batch.tenant_id == self.actor.tenant_id,
                    Batch.id.in_(self._scoped_batch_ids()),
                )
            )
            or 0,
            "sections": self.session.scalar(
                select(func.count())
                .select_from(Section)
                .where(
                    Section.tenant_id == self.actor.tenant_id,
                    Section.batch_id.in_(self._scoped_batch_ids()),
                )
            )
            or 0,
            "rooms": self.session.scalar(
                select(func.count()).select_from(Room).where(Room.tenant_id == self.actor.tenant_id)
            )
            or 0,
            "college_settings": self.session.scalar(
                select(func.count())
                .select_from(CollegeSetting)
                .where(CollegeSetting.tenant_id == self.actor.tenant_id)
            )
            or 0,
            "regulations": self.session.scalar(
                select(func.count())
                .select_from(Regulation)
                .where(Regulation.tenant_id == self.actor.tenant_id)
            )
            or 0,
            "curricula": self.session.scalar(
                select(func.count())
                .select_from(Curriculum)
                .where(
                    Curriculum.tenant_id == self.actor.tenant_id,
                    Curriculum.id.in_(self._scoped_curriculum_ids()),
                )
            )
            or 0,
            "curriculum_subjects": self.session.scalar(
                select(func.count())
                .select_from(CurriculumSubject)
                .where(
                    CurriculumSubject.tenant_id == self.actor.tenant_id,
                    CurriculumSubject.curriculum_id.in_(self._scoped_curriculum_ids()),
                )
            )
            or 0,
            "calendar_events": self.session.scalar(
                select(func.count())
                .select_from(CalendarEvent)
                .where(CalendarEvent.tenant_id == self.actor.tenant_id)
            )
            or 0,
            "numbering_formats": self.session.scalar(
                select(func.count())
                .select_from(NumberingFormat)
                .where(NumberingFormat.tenant_id == self.actor.tenant_id)
            )
            or 0,
        }
