"""Pydantic schemas for faculty delivery, timetable, and session operations."""

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

FACULTY_STATUS_PATTERN = "^(active|on_leave|inactive)$"
OFFERING_STATUS_PATTERN = "^(planned|active|completed|cancelled)$"
ALLOCATION_STATUS_PATTERN = "^(active|inactive)$"
PERIOD_STATUS_PATTERN = "^(active|inactive)$"
SESSION_STATE_PATTERN = "^(scheduled|submitted|locked|cancelled)$"


class FacultyProfileCreate(BaseModel):
    """Payload for creating one faculty profile."""

    person_id: UUID
    employee_code: str = Field(min_length=1, max_length=48)
    status: str = Field(default="active", pattern=FACULTY_STATUS_PATTERN)


class FacultyProfileUpdate(BaseModel):
    """Payload for updating mutable faculty profile fields."""

    employee_code: str | None = Field(None, min_length=1, max_length=48)
    status: str | None = Field(None, pattern=FACULTY_STATUS_PATTERN)


class FacultyProfileSummary(BaseModel):
    """Response shape for one faculty profile record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    person_id: UUID
    employee_code: str
    status: str


class SubjectOfferingCreate(BaseModel):
    """Payload for creating one subject offering."""

    term_id: UUID
    subject_id: UUID
    section_id: UUID
    status: str = Field(default="planned", pattern=OFFERING_STATUS_PATTERN)


class SubjectOfferingUpdate(BaseModel):
    """Payload for updating one subject offering status."""

    status: str | None = Field(None, pattern=OFFERING_STATUS_PATTERN)


class SubjectOfferingSummary(BaseModel):
    """Response shape for one subject offering."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    term_id: UUID
    subject_id: UUID
    section_id: UUID
    status: str


class FacultyAllocationCreate(BaseModel):
    """Payload for creating one faculty allocation."""

    offering_id: UUID
    faculty_id: UUID
    status: str = Field(default="active", pattern=ALLOCATION_STATUS_PATTERN)


class FacultyAllocationUpdate(BaseModel):
    """Payload for updating one faculty allocation status."""

    status: str | None = Field(None, pattern=ALLOCATION_STATUS_PATTERN)


class FacultyAllocationSummary(BaseModel):
    """Response shape for one faculty allocation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    offering_id: UUID
    faculty_id: UUID
    status: str


class TimetablePeriodCreate(BaseModel):
    """Payload for creating one timetable period."""

    offering_id: UUID
    faculty_id: UUID
    room_id: UUID | None = None
    day_of_week: int = Field(ge=1, le=7)
    start_time: time
    end_time: time
    status: str = Field(default="active", pattern=PERIOD_STATUS_PATTERN)

    @model_validator(mode="after")
    def validate_time_range(self) -> "TimetablePeriodCreate":
        """Require end_time to be strictly after start_time."""

        if self.start_time >= self.end_time:
            msg = "end_time must be after start_time"
            raise ValueError(msg)
        return self


class TimetablePeriodUpdate(BaseModel):
    """Payload for updating one timetable period."""

    offering_id: UUID | None = None
    faculty_id: UUID | None = None
    room_id: UUID | None = None
    day_of_week: int | None = Field(None, ge=1, le=7)
    start_time: time | None = None
    end_time: time | None = None
    status: str | None = Field(None, pattern=PERIOD_STATUS_PATTERN)


class TimetablePeriodSummary(BaseModel):
    """Response shape for one timetable period."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    offering_id: UUID
    faculty_id: UUID
    room_id: UUID | None
    day_of_week: int
    start_time: time
    end_time: time
    status: str


class TimetablePublicationCreate(BaseModel):
    """Request publication of the actor-scoped active timetable for one term."""

    term_id: UUID
    note: str | None = Field(None, max_length=1000)


class TimetablePublicationLineSummary(BaseModel):
    """Return one immutable published timetable line."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_period_id: UUID
    offering_id: UUID
    subject_id: UUID
    section_id: UUID
    faculty_id: UUID
    room_id: UUID | None
    subject_code: str
    subject_name: str
    section_code: str
    section_name: str
    faculty_employee_code: str
    room_code: str | None
    room_name: str | None
    day_of_week: int
    start_time: time
    end_time: time


class TimetablePublicationSummary(BaseModel):
    """Return timetable publication metadata without its snapshot lines."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    term_id: UUID
    scope_type: str
    scope_reference_id: UUID | None
    version: int
    state: str
    note: str | None
    published_by_membership_id: UUID
    published_at: datetime


class TimetablePublicationDetail(TimetablePublicationSummary):
    """Return one publication with its immutable timetable lines."""

    lines: list[TimetablePublicationLineSummary]


class PaginatedTimetablePublications(BaseModel):
    """Return a bounded timetable publication collection."""

    items: list[TimetablePublicationSummary]
    total: int = Field(ge=0)


class ClassSessionCreate(BaseModel):
    """Payload for creating one class session manually."""

    period_id: UUID
    session_date: date
    state: str = Field(default="scheduled", pattern=SESSION_STATE_PATTERN)


class ClassSessionUpdate(BaseModel):
    """Payload for updating mutable class session state."""

    state: str | None = Field(None, pattern=SESSION_STATE_PATTERN)


class ClassSessionSummary(BaseModel):
    """Response shape for one class session."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    period_id: UUID
    session_date: date
    state: str


class ClassSessionGenerateRequest(BaseModel):
    """Payload for generating dated class sessions from active timetable periods."""

    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_date_range(self) -> "ClassSessionGenerateRequest":
        """Require an inclusive range with end_date on or after start_date."""

        if self.end_date < self.start_date:
            msg = "end_date must be on or after start_date"
            raise ValueError(msg)
        return self


class ClassSessionGenerateResponse(BaseModel):
    """Response shape for generated class session identifiers."""

    created_count: int = Field(ge=0)
    session_ids: list[UUID]


class PaginatedFacultyProfiles(BaseModel):
    """Paginated wrapper for faculty profile listing."""

    items: list[FacultyProfileSummary]
    total: int = Field(ge=0)


class PaginatedSubjectOfferings(BaseModel):
    """Paginated wrapper for subject offering listing."""

    items: list[SubjectOfferingSummary]
    total: int = Field(ge=0)


class PaginatedFacultyAllocations(BaseModel):
    """Paginated wrapper for faculty allocation listing."""

    items: list[FacultyAllocationSummary]
    total: int = Field(ge=0)


class PaginatedTimetablePeriods(BaseModel):
    """Paginated wrapper for timetable period listing."""

    items: list[TimetablePeriodSummary]
    total: int = Field(ge=0)


class PaginatedClassSessions(BaseModel):
    """Paginated wrapper for class session listing."""

    items: list[ClassSessionSummary]
    total: int = Field(ge=0)


class DepartmentPostingCreate(BaseModel):
    """Create one effective-dated faculty department posting."""

    faculty_id: UUID
    department_id: UUID
    title: str = Field(min_length=1, max_length=120)
    starts_on: date
    ends_on: date | None = None


class DepartmentPostingSummary(DepartmentPostingCreate):
    """Return one persisted faculty department posting."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID


class ClassSubstitutionCreate(BaseModel):
    """Request one substitute faculty assignment for a class session."""

    session_id: UUID
    substitute_faculty_id: UUID
    reason: str = Field(min_length=3, max_length=2000)
    state: str = Field(default="requested", pattern="^(requested|approved|rejected|cancelled)$")


class ClassSubstitutionSummary(ClassSubstitutionCreate):
    """Return one persisted class substitution request."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID


class LessonPlanCreate(BaseModel):
    """Create one dated faculty lesson plan."""

    offering_id: UUID
    faculty_id: UUID
    planned_on: date
    title: str = Field(min_length=1, max_length=240)
    content: str | None = None
    state: str = Field(default="draft", pattern="^(draft|published|completed|cancelled)$")


class LessonPlanSummary(LessonPlanCreate):
    """Return one persisted lesson plan."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID


class LearningMaterialCreate(BaseModel):
    """Create one offering learning-resource reference."""

    offering_id: UUID
    title: str = Field(min_length=1, max_length=240)
    material_type: str = Field(pattern="^(document|link|video|assignment|other)$")
    resource_url: str = Field(min_length=1, max_length=2048)
    description: str | None = None


class LearningMaterialSummary(LearningMaterialCreate):
    """Return one persisted learning material reference."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID


class StudentLearningMaterialSummary(BaseModel):
    """Present one scoped learning resource with readable academic context."""

    id: UUID
    offering_id: UUID
    title: str
    material_type: str
    resource_url: str
    description: str | None
    subject_code: str
    subject_name: str
    section_code: str
    section_name: str
    term_code: str
    term_name: str
    faculty_employee_code: str | None


class PaginatedStudentLearningMaterials(BaseModel):
    """Return a bounded collection of scoped Student learning resources."""

    items: list[StudentLearningMaterialSummary]
    total: int = Field(ge=0)


class SyllabusProgressCreate(BaseModel):
    """Create one dated syllabus completion record."""

    offering_id: UUID
    faculty_id: UUID
    recorded_on: date
    topic: str = Field(min_length=1, max_length=500)
    completion_percentage: int = Field(ge=0, le=100)
    notes: str | None = None


class SyllabusProgressSummary(SyllabusProgressCreate):
    """Return one persisted syllabus progress record."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
