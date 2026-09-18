"""Pydantic schemas for academic structure API requests and responses."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ACTIVE_LIFECYCLE_PATTERN = "^(active|inactive|discontinued)$"


# Campus schemas
class CampusBase(BaseModel):
    """Base campus data shared across create and update operations."""

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=240)
    address: str | None = None
    status: str = Field(default="active", pattern="^(active|inactive|closed)$")


class CampusCreate(CampusBase):
    """Request payload for creating a new campus."""


class CampusUpdate(BaseModel):
    """Request payload for updating an existing campus."""

    name: str | None = Field(None, min_length=1, max_length=240)
    address: str | None = None
    status: str | None = Field(None, pattern="^(active|inactive|closed)$")


class CampusSummary(CampusBase):
    """Public campus data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID


# Academic Year schemas
class AcademicYearBase(BaseModel):
    """Base academic year data shared across create and update operations."""

    code: str = Field(min_length=1, max_length=32)
    display_name: str = Field(min_length=1, max_length=120)
    starts_on: date
    ends_on: date
    status: str = Field(default="planned", pattern="^(planned|active|completed|archived)$")


class AcademicYearCreate(AcademicYearBase):
    """Request payload for creating a new academic year."""


class AcademicYearUpdate(BaseModel):
    """Request payload for updating an existing academic year."""

    display_name: str | None = Field(None, min_length=1, max_length=120)
    starts_on: date | None = None
    ends_on: date | None = None
    status: str | None = Field(None, pattern="^(planned|active|completed|archived)$")


class AcademicYearSummary(AcademicYearBase):
    """Public academic year data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID


# Term schemas
class TermBase(BaseModel):
    """Base term data shared across create and update operations."""

    code: str = Field(min_length=1, max_length=32)
    display_name: str = Field(min_length=1, max_length=120)
    starts_on: date
    ends_on: date
    status: str = Field(default="planned", pattern="^(planned|active|completed)$")


class TermCreate(TermBase):
    """Request payload for creating a new term within an academic year."""

    academic_year_id: UUID


class TermUpdate(BaseModel):
    """Request payload for updating an existing term."""

    academic_year_id: UUID | None = None
    display_name: str | None = Field(None, min_length=1, max_length=120)
    starts_on: date | None = None
    ends_on: date | None = None
    status: str | None = Field(None, pattern="^(planned|active|completed)$")


class TermSummary(TermBase):
    """Public term data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    academic_year_id: UUID


# Department schemas
class DepartmentBase(BaseModel):
    """Base department data shared across create and update operations."""

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=240)
    status: str = Field(default="active", pattern="^(active|inactive)$")


class DepartmentCreate(DepartmentBase):
    """Request payload for creating a new department."""


class DepartmentUpdate(BaseModel):
    """Request payload for updating an existing department."""

    name: str | None = Field(None, min_length=1, max_length=240)
    status: str | None = Field(None, pattern="^(active|inactive)$")


class DepartmentSummary(DepartmentBase):
    """Public department data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID


# Program schemas
class ProgramBase(BaseModel):
    """Base program data shared across create and update operations."""

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=240)
    degree_level: str = Field(min_length=1, max_length=32)
    duration_years: int = Field(ge=1, le=10)
    status: str = Field(default="active", pattern=ACTIVE_LIFECYCLE_PATTERN)


class ProgramCreate(ProgramBase):
    """Request payload for creating a new program."""

    department_id: UUID


class ProgramUpdate(BaseModel):
    """Request payload for updating an existing program."""

    department_id: UUID | None = None
    name: str | None = Field(None, min_length=1, max_length=240)
    degree_level: str | None = Field(None, min_length=1, max_length=32)
    duration_years: int | None = Field(None, ge=1, le=10)
    status: str | None = Field(None, pattern=ACTIVE_LIFECYCLE_PATTERN)


class ProgramSummary(ProgramBase):
    """Public program data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    department_id: UUID


# Subject schemas
class SubjectBase(BaseModel):
    """Base subject data shared across create and update operations."""

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=240)
    credits: int | None = Field(None, ge=1, le=20)
    status: str = Field(default="active", pattern=ACTIVE_LIFECYCLE_PATTERN)


class SubjectCreate(SubjectBase):
    """Request payload for creating a new subject."""

    department_id: UUID


class SubjectUpdate(BaseModel):
    """Request payload for updating an existing subject."""

    department_id: UUID | None = None
    name: str | None = Field(None, min_length=1, max_length=240)
    credits: int | None = Field(None, ge=1, le=20)
    status: str | None = Field(None, pattern=ACTIVE_LIFECYCLE_PATTERN)


class SubjectSummary(SubjectBase):
    """Public subject data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    department_id: UUID


# Batch schemas
class BatchBase(BaseModel):
    """Base batch data shared across create and update operations."""

    admission_year: int = Field(ge=2000, le=2100)
    display_name: str = Field(min_length=1, max_length=120)
    status: str = Field(default="active", pattern="^(active|graduated|archived)$")


class BatchCreate(BatchBase):
    """Request payload for creating a new batch."""

    program_id: UUID


class BatchUpdate(BaseModel):
    """Request payload for updating an existing batch."""

    program_id: UUID | None = None
    display_name: str | None = Field(None, min_length=1, max_length=120)
    status: str | None = Field(None, pattern="^(active|graduated|archived)$")


class BatchSummary(BatchBase):
    """Public batch data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID


# Section schemas
class SectionBase(BaseModel):
    """Base section data shared across create and update operations."""

    code: str = Field(min_length=1, max_length=16)
    display_name: str = Field(min_length=1, max_length=120)
    max_capacity: int | None = Field(None, ge=1, le=500)
    status: str = Field(default="active", pattern="^(active|merged|archived)$")


class SectionCreate(SectionBase):
    """Request payload for creating a new section."""

    batch_id: UUID


class SectionUpdate(BaseModel):
    """Request payload for updating an existing section."""

    batch_id: UUID | None = None
    display_name: str | None = Field(None, min_length=1, max_length=120)
    max_capacity: int | None = Field(None, ge=1, le=500)
    status: str | None = Field(None, pattern="^(active|merged|archived)$")


class SectionSummary(SectionBase):
    """Public section data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    batch_id: UUID


# Room schemas
class RoomBase(BaseModel):
    """Base room data shared across create and update operations."""

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=240)
    room_type: str = Field(pattern="^(classroom|lab|auditorium|seminar|virtual)$")
    capacity: int | None = Field(None, ge=1, le=1000)
    has_projector: bool = False
    has_computers: bool = False
    status: str = Field(default="available", pattern="^(available|maintenance|unavailable)$")


class RoomCreate(RoomBase):
    """Request payload for creating a new room."""

    campus_id: UUID


class RoomUpdate(BaseModel):
    """Request payload for updating an existing room."""

    campus_id: UUID | None = None
    name: str | None = Field(None, min_length=1, max_length=240)
    room_type: str | None = Field(None, pattern="^(classroom|lab|auditorium|seminar|virtual)$")
    capacity: int | None = Field(None, ge=1, le=1000)
    has_projector: bool | None = None
    has_computers: bool | None = None
    status: str | None = Field(None, pattern="^(available|maintenance|unavailable)$")


class RoomSummary(RoomBase):
    """Public room data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    campus_id: UUID


# College Setting schemas
class CollegeSettingBase(BaseModel):
    """Base institution setting data shared across create and update operations."""

    institution_name: str = Field(min_length=1, max_length=240)
    short_name: str | None = Field(None, min_length=1, max_length=80)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    locale: str = Field(default="en-IN", min_length=2, max_length=32)


class CollegeSettingCreate(CollegeSettingBase):
    """Request payload for creating tenant institution settings."""


class CollegeSettingUpdate(BaseModel):
    """Request payload for updating tenant institution settings."""

    institution_name: str | None = Field(None, min_length=1, max_length=240)
    short_name: str | None = Field(None, min_length=1, max_length=80)
    timezone: str | None = Field(None, min_length=1, max_length=64)
    locale: str | None = Field(None, min_length=2, max_length=32)


class CollegeSettingSummary(CollegeSettingBase):
    """Public college setting data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID


# Regulation schemas
class RegulationBase(BaseModel):
    """Base regulation data shared across create and update operations."""

    code: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=240)
    effective_from_year: int = Field(ge=2000, le=2100)
    status: str = Field(default="active", pattern="^(active|inactive|archived)$")


class RegulationCreate(RegulationBase):
    """Request payload for creating a new regulation."""


class RegulationUpdate(BaseModel):
    """Request payload for updating an existing regulation."""

    title: str | None = Field(None, min_length=1, max_length=240)
    effective_from_year: int | None = Field(None, ge=2000, le=2100)
    status: str | None = Field(None, pattern="^(active|inactive|archived)$")


class RegulationSummary(RegulationBase):
    """Public regulation data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID


# Curriculum schemas
class CurriculumBase(BaseModel):
    """Base curriculum data shared across create and update operations."""

    code: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=240)
    total_credits: int | None = Field(None, ge=1, le=400)
    status: str = Field(default="draft", pattern="^(draft|active|archived)$")


class CurriculumCreate(CurriculumBase):
    """Request payload for creating a new curriculum."""

    program_id: UUID
    regulation_id: UUID


class CurriculumUpdate(BaseModel):
    """Request payload for updating an existing curriculum."""

    program_id: UUID | None = None
    regulation_id: UUID | None = None
    title: str | None = Field(None, min_length=1, max_length=240)
    total_credits: int | None = Field(None, ge=1, le=400)
    status: str | None = Field(None, pattern="^(draft|active|archived)$")


class CurriculumSummary(CurriculumBase):
    """Public curriculum data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    regulation_id: UUID


# Curriculum Subject schemas
class CurriculumSubjectBase(BaseModel):
    """Base curriculum-subject mapping data shared across create and update operations."""

    term_number: int = Field(ge=1, le=20)
    is_elective: bool = False
    credits_override: int | None = Field(None, ge=1, le=20)


class CurriculumSubjectCreate(CurriculumSubjectBase):
    """Request payload for creating a curriculum-subject mapping."""

    curriculum_id: UUID
    subject_id: UUID


class CurriculumSubjectUpdate(BaseModel):
    """Request payload for updating a curriculum-subject mapping."""

    curriculum_id: UUID | None = None
    subject_id: UUID | None = None
    term_number: int | None = Field(None, ge=1, le=20)
    is_elective: bool | None = None
    credits_override: int | None = Field(None, ge=1, le=20)


class CurriculumSubjectSummary(CurriculumSubjectBase):
    """Public curriculum-subject mapping data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    curriculum_id: UUID
    subject_id: UUID


# Calendar Event schemas
class CalendarEventBase(BaseModel):
    """Base calendar event data shared across create and update operations."""

    name: str = Field(min_length=1, max_length=240)
    event_type: str = Field(pattern="^(instructional|exam|holiday|deadline|other)$")
    starts_on: date
    ends_on: date
    is_holiday: bool = False
    status: str = Field(default="planned", pattern="^(planned|published|cancelled)$")


class CalendarEventCreate(CalendarEventBase):
    """Request payload for creating a new calendar event."""

    academic_year_id: UUID
    term_id: UUID | None = None


class CalendarEventUpdate(BaseModel):
    """Request payload for updating an existing calendar event."""

    academic_year_id: UUID | None = None
    name: str | None = Field(None, min_length=1, max_length=240)
    event_type: str | None = Field(None, pattern="^(instructional|exam|holiday|deadline|other)$")
    starts_on: date | None = None
    ends_on: date | None = None
    is_holiday: bool | None = None
    status: str | None = Field(None, pattern="^(planned|published|cancelled)$")
    term_id: UUID | None = None


class CalendarEventSummary(CalendarEventBase):
    """Public calendar event data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    term_id: UUID | None


# Numbering Format schemas
class NumberingFormatBase(BaseModel):
    """Base numbering format data shared across create and update operations."""

    code: str = Field(min_length=1, max_length=32)
    entity_type: str = Field(min_length=1, max_length=64)
    prefix: str | None = Field(None, max_length=40)
    suffix: str | None = Field(None, max_length=40)
    padding: int = Field(default=4, ge=1, le=10)
    next_number: int = Field(default=1, ge=1, le=999999999)
    reset_frequency: str = Field(default="none", pattern="^(none|yearly|termly)$")


class NumberingFormatCreate(NumberingFormatBase):
    """Request payload for creating a new numbering format."""


class NumberingFormatUpdate(BaseModel):
    """Request payload for updating an existing numbering format."""

    prefix: str | None = Field(None, max_length=40)
    suffix: str | None = Field(None, max_length=40)
    padding: int | None = Field(None, ge=1, le=10)
    next_number: int | None = Field(None, ge=1, le=999999999)
    reset_frequency: str | None = Field(None, pattern="^(none|yearly|termly)$")


class NumberingFormatSummary(NumberingFormatBase):
    """Public numbering format data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID


# List response wrappers
class CampusList(BaseModel):
    """Paginated list of campuses."""

    items: list[CampusSummary]
    total: int


class AcademicYearList(BaseModel):
    """Paginated list of academic years."""

    items: list[AcademicYearSummary]
    total: int


class TermList(BaseModel):
    """Paginated list of terms."""

    items: list[TermSummary]
    total: int


class DepartmentList(BaseModel):
    """Paginated list of departments."""

    items: list[DepartmentSummary]
    total: int


class ProgramList(BaseModel):
    """Paginated list of programs."""

    items: list[ProgramSummary]
    total: int


class SubjectList(BaseModel):
    """Paginated list of subjects."""

    items: list[SubjectSummary]
    total: int


class BatchList(BaseModel):
    """Paginated list of batches."""

    items: list[BatchSummary]
    total: int


class SectionList(BaseModel):
    """Paginated list of sections."""

    items: list[SectionSummary]
    total: int


class RoomList(BaseModel):
    """Paginated list of rooms."""

    items: list[RoomSummary]
    total: int


class CollegeSettingList(BaseModel):
    """Paginated list of college settings."""

    items: list[CollegeSettingSummary]
    total: int


class RegulationList(BaseModel):
    """Paginated list of regulations."""

    items: list[RegulationSummary]
    total: int


class CurriculumList(BaseModel):
    """Paginated list of curricula."""

    items: list[CurriculumSummary]
    total: int


class CurriculumSubjectList(BaseModel):
    """Paginated list of curriculum-subject mappings."""

    items: list[CurriculumSubjectSummary]
    total: int


class CalendarEventList(BaseModel):
    """Paginated list of calendar events."""

    items: list[CalendarEventSummary]
    total: int


class NumberingFormatList(BaseModel):
    """Paginated list of numbering formats."""

    items: list[NumberingFormatSummary]
    total: int


# Overview response
class AcademicsOverview(BaseModel):
    """Summarize configured academic structure counts for the tenant."""

    campuses: int
    academic_years: int
    terms: int
    departments: int
    programs: int
    subjects: int
    batches: int
    sections: int
    rooms: int
    college_settings: int
    regulations: int
    curricula: int
    curriculum_subjects: int
    calendar_events: int
    numbering_formats: int
