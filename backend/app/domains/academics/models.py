"""SQLAlchemy models for tenant-scoped academic institutional structure."""

from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

TENANT_ID_REFERENCE = "tenants.id"


class Campus(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represent one physical or virtual learning location within a college."""

    __tablename__ = "campuses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'closed')",
            name="ck_campuses_status",
        ),
        UniqueConstraint("tenant_id", "code"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class AcademicYear(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define one operational academic cycle with a unique code and date range."""

    __tablename__ = "academic_years"
    __table_args__ = (
        CheckConstraint(
            "status IN ('planned', 'active', 'completed', 'archived')",
            name="ck_academic_years_status",
        ),
        UniqueConstraint("tenant_id", "code"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    starts_on: Mapped[str] = mapped_column(Date, nullable=False)
    ends_on: Mapped[str] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="planned")


class Term(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Divide one academic year into operational periods such as semesters or trimesters."""

    __tablename__ = "terms"
    __table_args__ = (
        CheckConstraint(
            "status IN ('planned', 'active', 'completed')",
            name="ck_terms_status",
        ),
        UniqueConstraint("tenant_id", "academic_year_id", "code"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    academic_year_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    starts_on: Mapped[str] = mapped_column(Date, nullable=False)
    ends_on: Mapped[str] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="planned")


class Department(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represent one academic or administrative division within the institution."""

    __tablename__ = "departments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_departments_status",
        ),
        UniqueConstraint("tenant_id", "code"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Program(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define one degree or certificate program offered by a department."""

    __tablename__ = "programs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'discontinued')",
            name="ck_programs_status",
        ),
        UniqueConstraint("tenant_id", "code"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "department_id"],
            ["departments.tenant_id", "departments.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    department_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    degree_level: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_years: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Subject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represent one academic course or subject that can be taught."""

    __tablename__ = "subjects"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'discontinued')",
            name="ck_subjects_status",
        ),
        UniqueConstraint("tenant_id", "code"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "department_id"],
            ["departments.tenant_id", "departments.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    department_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    credits: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Batch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Group students admitted in a specific year for a specific program."""

    __tablename__ = "batches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'graduated', 'archived')",
            name="ck_batches_status",
        ),
        UniqueConstraint("tenant_id", "program_id", "admission_year"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    program_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    admission_year: Mapped[int] = mapped_column(Integer, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Section(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Divide a batch into smaller teaching groups for timetabling and attendance."""

    __tablename__ = "sections"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'merged', 'archived')",
            name="ck_sections_status",
        ),
        UniqueConstraint("tenant_id", "batch_id", "code"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["batches.tenant_id", "batches.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    batch_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    max_capacity: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Room(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define one physical or virtual space available for teaching or events."""

    __tablename__ = "rooms"
    __table_args__ = (
        CheckConstraint(
            "room_type IN ('classroom', 'lab', 'auditorium', 'seminar', 'virtual')",
            name="ck_rooms_type",
        ),
        CheckConstraint(
            "status IN ('available', 'maintenance', 'unavailable')",
            name="ck_rooms_status",
        ),
        UniqueConstraint("tenant_id", "campus_id", "code"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "campus_id"],
            ["campuses.tenant_id", "campuses.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    campus_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    room_type: Mapped[str] = mapped_column(String(32), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer)
    has_projector: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_computers: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="available")


class CollegeSetting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist tenant-wide institution configuration used across academics workflows."""

    __tablename__ = "college_settings"
    __table_args__ = (
        UniqueConstraint("tenant_id"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    institution_name: Mapped[str] = mapped_column(String(240), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(80))
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    locale: Mapped[str] = mapped_column(String(32), nullable=False, default="en-IN")


class Regulation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represent one tenant-owned academic regulation/version policy definition."""

    __tablename__ = "regulations"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'archived')", name="ck_regulations_status"),
        UniqueConstraint("tenant_id", "code"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    effective_from_year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Curriculum(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one curriculum blueprint tied to a program and regulation in a tenant."""

    __tablename__ = "curricula"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'active', 'archived')", name="ck_curricula_status"),
        UniqueConstraint("tenant_id", "program_id", "regulation_id", "code"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "regulation_id"],
            ["regulations.tenant_id", "regulations.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    program_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    regulation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    total_credits: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")


class CurriculumSubject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Map subjects to curricula with term sequencing and elective metadata."""

    __tablename__ = "curriculum_subjects"
    __table_args__ = (
        UniqueConstraint("tenant_id", "curriculum_id", "subject_id"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "subject_id"],
            ["subjects.tenant_id", "subjects.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    curriculum_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    term_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_elective: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    credits_override: Mapped[int | None] = mapped_column(Integer)


class CalendarEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Capture academic calendar milestones and holidays scoped to a tenant year."""

    __tablename__ = "calendar_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('instructional', 'exam', 'holiday', 'deadline', 'other')",
            name="ck_calendar_events_type",
        ),
        CheckConstraint(
            "status IN ('planned', 'published', 'cancelled')",
            name="ck_calendar_events_status",
        ),
        UniqueConstraint("tenant_id", "academic_year_id", "name", "starts_on"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(
            ["tenant_id", "academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["terms.tenant_id", "terms.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    academic_year_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    term_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    event_type: Mapped[str] = mapped_column(String(24), nullable=False)
    starts_on: Mapped[str] = mapped_column(Date, nullable=False)
    ends_on: Mapped[str] = mapped_column(Date, nullable=False)
    is_holiday: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="planned")


class NumberingFormat(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define tenant-scoped sequence format rules for IDs and document numbers."""

    __tablename__ = "numbering_formats"
    __table_args__ = (
        CheckConstraint(
            "reset_frequency IN ('none', 'yearly', 'termly')",
            name="ck_numbering_formats_reset_frequency",
        ),
        UniqueConstraint("tenant_id", "code"),
        UniqueConstraint("tenant_id", "entity_type"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    prefix: Mapped[str | None] = mapped_column(String(40))
    suffix: Mapped[str | None] = mapped_column(String(40))
    padding: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    next_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reset_frequency: Mapped[str] = mapped_column(String(16), nullable=False, default="none")
