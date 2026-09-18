"""SQLAlchemy models for tenant-scoped examinations scheduling, marks, and published results."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

TENANT_ID_REFERENCE = "tenants.id"


class AssessmentScheme(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define one subject-level assessment scheme per program and term."""

    __tablename__ = "assessment_schemes"
    __table_args__ = (
        CheckConstraint("max_marks > 0", name="ck_assessment_schemes_max_marks_positive"),
        CheckConstraint("pass_marks >= 0", name="ck_assessment_schemes_pass_marks_non_negative"),
        CheckConstraint("pass_marks <= max_marks", name="ck_assessment_schemes_pass_marks_le_max"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "subject_id", "program_id", "term_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "subject_id"],
            ["subjects.tenant_id", "subjects.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["terms.tenant_id", "terms.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    program_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    term_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    pass_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)


class ExamSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define one exam session for one term with controlled publication lifecycle."""

    __tablename__ = "exam_sessions"
    __table_args__ = (
        CheckConstraint(
            "state IN ('draft', 'active', 'published', 'closed')",
            name="ck_exam_sessions_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "term_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["terms.tenant_id", "terms.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    term_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")


class ExamSchedule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Schedule one subject offering exam occurrence under one exam session."""

    __tablename__ = "exam_schedules"
    __table_args__ = (
        CheckConstraint("max_marks > 0", name="ck_exam_schedules_max_marks_positive"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "session_id", "offering_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "session_id"],
            ["exam_sessions.tenant_id", "exam_sessions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "offering_id"],
            ["subject_offerings.tenant_id", "subject_offerings.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "room_id"],
            ["rooms.tenant_id", "rooms.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    session_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    offering_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    room_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    max_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)


class ExamRegistration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Register one student for one scheduled exam with eligibility state."""

    __tablename__ = "exam_registrations"
    __table_args__ = (
        CheckConstraint(
            "eligibility IN ('eligible', 'ineligible', 'withheld')",
            name="ck_exam_registrations_eligibility",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "schedule_id", "student_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "schedule_id"],
            ["exam_schedules.tenant_id", "exam_schedules.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    schedule_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    eligibility: Mapped[str] = mapped_column(String(16), nullable=False, default="eligible")


class MarkEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one marks lifecycle entry for one exam registration."""

    __tablename__ = "mark_entries"
    __table_args__ = (
        CheckConstraint("marks_obtained >= 0", name="ck_mark_entries_marks_non_negative"),
        CheckConstraint(
            "state IN ('entered', 'verified', 'locked')",
            name="ck_mark_entries_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "registration_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "registration_id"],
            ["exam_registrations.tenant_id", "exam_registrations.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "verified_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "locked_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    registration_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="entered")
    verified_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PublishedResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist published student exam outcomes by session with reopen controls."""

    __tablename__ = "published_results"
    __table_args__ = (
        CheckConstraint(
            "result IN ('pass', 'fail')",
            name="ck_published_results_result",
        ),
        CheckConstraint(
            "state IN ('published', 'reopened')",
            name="ck_published_results_state",
        ),
        CheckConstraint("total_marks >= 0", name="ck_published_results_total_marks_non_negative"),
        CheckConstraint("total_max_marks > 0", name="ck_published_results_total_max_marks_positive"),
        CheckConstraint("percentage >= 0", name="ck_published_results_percentage_non_negative"),
        CheckConstraint("percentage <= 100", name="ck_published_results_percentage_le_hundred"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "student_id", "session_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "session_id"],
            ["exam_sessions.tenant_id", "exam_sessions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "published_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reopened_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    session_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    total_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_max_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    grade: Mapped[str] = mapped_column(String(8), nullable=False)
    gpa: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("0.00"))
    result: Mapped[str] = mapped_column(String(8), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="published")
    publication_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reopened_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))


class GradeRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define one versioned term grade band and grade point."""

    __tablename__ = "grade_rules"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_grade_rules_version_positive"),
        CheckConstraint("min_percentage >= 0 AND max_percentage <= 100", name="ck_grade_rules_range"),
        CheckConstraint("min_percentage <= max_percentage", name="ck_grade_rules_range_order"),
        CheckConstraint("grade_point >= 0", name="ck_grade_rules_point_non_negative"),
        CheckConstraint("state IN ('draft', 'published', 'archived')", name="ck_grade_rules_state"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "term_id", "version", "letter_grade"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "term_id"], ["terms.tenant_id", "terms.id"], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    term_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    min_percentage: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    max_percentage: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    letter_grade: Mapped[str] = mapped_column(String(8), nullable=False)
    grade_point: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")


class ExamSeatAllocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Assign one eligible exam registration to a room seat."""

    __tablename__ = "exam_seat_allocations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "registration_id"),
        UniqueConstraint("tenant_id", "schedule_id", "room_id", "seat_number"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "schedule_id"], ["exam_schedules.tenant_id", "exam_schedules.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "registration_id"], ["exam_registrations.tenant_id", "exam_registrations.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "room_id"], ["rooms.tenant_id", "rooms.id"], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    schedule_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    registration_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    room_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    seat_number: Mapped[str] = mapped_column(String(32), nullable=False)


class InvigilationAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Assign one faculty member to invigilate a scheduled examination room."""

    __tablename__ = "invigilation_assignments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "schedule_id", "faculty_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "schedule_id"], ["exam_schedules.tenant_id", "exam_schedules.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "faculty_id"], ["faculty_profiles.tenant_id", "faculty_profiles.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "room_id"], ["rooms.tenant_id", "rooms.id"], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    schedule_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    faculty_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    room_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)


class MarkAdjustment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one reviewed moderation or revaluation without overwriting locked marks."""

    __tablename__ = "mark_adjustments"
    __table_args__ = (
        CheckConstraint("original_marks >= 0 AND revised_marks >= 0", name="ck_mark_adjustments_non_negative"),
        CheckConstraint("state IN ('requested', 'approved', 'rejected')", name="ck_mark_adjustments_state"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "registration_id"], ["exam_registrations.tenant_id", "exam_registrations.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "requested_by_membership_id"], ["tenant_memberships.tenant_id", "tenant_memberships.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "reviewed_by_membership_id"], ["tenant_memberships.tenant_id", "tenant_memberships.id"], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    registration_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    original_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    revised_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="requested")
    requested_by_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    reviewed_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PublishedResultLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Snapshot one subject outcome used by a published aggregate result."""

    __tablename__ = "published_result_lines"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint(
            "tenant_id",
            "result_id",
            "publication_version",
            "registration_id",
            name="uq_published_result_lines_result_version_registration",
        ),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "result_id"], ["published_results.tenant_id", "published_results.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["tenant_id", "registration_id"], ["exam_registrations.tenant_id", "exam_registrations.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "subject_id"], ["subjects.tenant_id", "subjects.id"], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    result_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    publication_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    registration_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    pass_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    grade: Mapped[str] = mapped_column(String(8), nullable=False)
    grade_point: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)


class ResultPublicationEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Retain one immutable publication, reopen, or republish snapshot."""

    __tablename__ = "result_publication_events"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_result_publication_events_version_positive"),
        CheckConstraint("event_type IN ('published', 'reopened', 'republished')", name="ck_result_publication_events_type"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "result_id", "version", "event_type"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "result_id"], ["published_results.tenant_id", "published_results.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["tenant_id", "performed_by_membership_id"], ["tenant_memberships.tenant_id", "tenant_memberships.id"], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    result_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    performed_by_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)


class HallTicketIssuance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Record one immutable hall-ticket issuance for a Student exam session."""

    __tablename__ = "hall_ticket_issuances"
    __table_args__ = (
        Index("ix_hall_ticket_issuances_student", "tenant_id", "student_id", "issued_at"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "ticket_number"),
        UniqueConstraint("tenant_id", "student_id", "session_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "session_id"],
            ["exam_sessions.tenant_id", "exam_sessions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "issued_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    session_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    ticket_number: Mapped[str] = mapped_column(String(64), nullable=False)
    registration_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issued_by_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)


class GradeCardIssuance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Record one immutable grade-card issuance for a published result version."""

    __tablename__ = "grade_card_issuances"
    __table_args__ = (
        CheckConstraint("publication_version > 0", name="ck_grade_card_issuances_version"),
        Index(
            "ix_grade_card_issuances_result",
            "tenant_id",
            "result_id",
            "publication_version",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "card_number"),
        UniqueConstraint("tenant_id", "result_id", "publication_version"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "result_id"],
            ["published_results.tenant_id", "published_results.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "issued_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    result_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    publication_version: Mapped[int] = mapped_column(Integer, nullable=False)
    card_number: Mapped[str] = mapped_column(String(64), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issued_by_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)


class TranscriptIssuance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Record one immutable transcript issuance against a result-version manifest."""

    __tablename__ = "transcript_issuances"
    __table_args__ = (
        Index("ix_transcript_issuances_student", "tenant_id", "student_id", "issued_at"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "transcript_number"),
        UniqueConstraint("tenant_id", "student_id", "version_hash"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "issued_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    transcript_number: Mapped[str] = mapped_column(String(64), nullable=False)
    version_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    result_versions: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issued_by_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
