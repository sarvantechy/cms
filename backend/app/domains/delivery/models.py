"""SQLAlchemy models for tenant-scoped faculty delivery and timetable entities."""

from datetime import date, time
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKeyConstraint,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

TENANT_ID_REFERENCE = "tenants.id"


class FacultyProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one tenant faculty profile linked to a canonical person record."""

    __tablename__ = "faculty_profiles"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'on_leave', 'inactive')",
            name="ck_faculty_profiles_status",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "person_id"),
        UniqueConstraint("tenant_id", "employee_code"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["people.tenant_id", "people.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    person_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    employee_code: Mapped[str] = mapped_column(String(48), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class SubjectOffering(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define one subject delivery assignment for one term and section."""

    __tablename__ = "subject_offerings"
    __table_args__ = (
        CheckConstraint(
            "status IN ('planned', 'active', 'completed', 'cancelled')",
            name="ck_subject_offerings_status",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "term_id", "subject_id", "section_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["terms.tenant_id", "terms.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "subject_id"],
            ["subjects.tenant_id", "subjects.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "section_id"],
            ["sections.tenant_id", "sections.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    term_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    section_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="planned")


class FacultyAllocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Associate one faculty profile with one subject offering."""

    __tablename__ = "faculty_allocations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_faculty_allocations_status",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "offering_id", "faculty_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "offering_id"],
            ["subject_offerings.tenant_id", "subject_offerings.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "faculty_id"],
            ["faculty_profiles.tenant_id", "faculty_profiles.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    offering_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    faculty_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class TimetablePeriod(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define one recurring weekly delivery period bound to a faculty and offering."""

    __tablename__ = "timetable_periods"
    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 1 AND 7", name="ck_timetable_periods_day_of_week"),
        CheckConstraint("start_time < end_time", name="ck_timetable_periods_time_range"),
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_timetable_periods_status",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint(
            "tenant_id",
            "offering_id",
            "faculty_id",
            "day_of_week",
            "start_time",
            "end_time",
            name="uq_timetable_period_slot",
        ),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "offering_id"],
            ["subject_offerings.tenant_id", "subject_offerings.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "faculty_id"],
            ["faculty_profiles.tenant_id", "faculty_profiles.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "room_id"],
            ["rooms.tenant_id", "rooms.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    offering_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    faculty_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    room_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    day_of_week: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class ClassSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one dated class occurrence generated from a timetable period."""

    __tablename__ = "class_sessions"
    __table_args__ = (
        CheckConstraint(
            "state IN ('scheduled', 'submitted', 'locked', 'cancelled')",
            name="ck_class_sessions_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "period_id", "session_date"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "period_id"],
            ["timetable_periods.tenant_id", "timetable_periods.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    period_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="scheduled")


class DepartmentPosting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Effective-date one faculty member's posting in an academic department."""

    __tablename__ = "faculty_department_postings"
    __table_args__ = (
        CheckConstraint("ends_on IS NULL OR ends_on >= starts_on", name="ck_faculty_postings_dates"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "faculty_id", "department_id", "starts_on"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "faculty_id"], ["faculty_profiles.tenant_id", "faculty_profiles.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "department_id"], ["departments.tenant_id", "departments.id"], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    faculty_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    department_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date | None] = mapped_column(Date)


class ClassSubstitution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Record an auditable substitute faculty assignment for one dated class session."""

    __tablename__ = "class_substitutions"
    __table_args__ = (
        CheckConstraint("state IN ('requested', 'approved', 'rejected', 'cancelled')", name="ck_class_substitutions_state"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "session_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "session_id"], ["class_sessions.tenant_id", "class_sessions.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "substitute_faculty_id"], ["faculty_profiles.tenant_id", "faculty_profiles.id"], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    session_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    substitute_faculty_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="requested")


class LessonPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one faculty lesson plan against a subject offering and planned date."""

    __tablename__ = "lesson_plans"
    __table_args__ = (
        CheckConstraint("state IN ('draft', 'published', 'completed', 'cancelled')", name="ck_lesson_plans_state"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "offering_id"], ["subject_offerings.tenant_id", "subject_offerings.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "faculty_id"], ["faculty_profiles.tenant_id", "faculty_profiles.id"], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    offering_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    faculty_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    planned_on: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")


class LearningMaterial(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Reference one learning resource published for a subject offering."""

    __tablename__ = "learning_materials"
    __table_args__ = (
        CheckConstraint("material_type IN ('document', 'link', 'video', 'assignment', 'other')", name="ck_learning_materials_type"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "offering_id"], ["subject_offerings.tenant_id", "subject_offerings.id"], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    offering_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    material_type: Mapped[str] = mapped_column(String(24), nullable=False)
    resource_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class SyllabusProgress(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Capture dated syllabus completion evidence for one offering and faculty member."""

    __tablename__ = "syllabus_progress"
    __table_args__ = (
        CheckConstraint("completion_percentage BETWEEN 0 AND 100", name="ck_syllabus_progress_percentage"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "offering_id"], ["subject_offerings.tenant_id", "subject_offerings.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "faculty_id"], ["faculty_profiles.tenant_id", "faculty_profiles.id"], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    offering_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    faculty_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    recorded_on: Mapped[date] = mapped_column(Date, nullable=False)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    completion_percentage: Mapped[int] = mapped_column(nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
