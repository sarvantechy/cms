"""SQLAlchemy models for tenant-scoped attendance records, corrections, and leave."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

TENANT_ID_REFERENCE = "tenants.id"


class AttendanceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one student attendance outcome for one class session."""

    __tablename__ = "attendance_records"
    __table_args__ = (
        CheckConstraint(
            "status IN ('present', 'absent', 'late', 'excused')",
            name="ck_attendance_records_status",
        ),
        CheckConstraint(
            "state IN ('submitted', 'locked')",
            name="ck_attendance_records_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "session_id", "student_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "session_id"],
            ["class_sessions.tenant_id", "class_sessions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    session_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="submitted")


class AttendanceCorrection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track correction requests and approval outcomes for attendance records."""

    __tablename__ = "attendance_corrections"
    __table_args__ = (
        CheckConstraint(
            "state IN ('requested', 'approved', 'rejected')",
            name="ck_attendance_corrections_state",
        ),
        CheckConstraint(
            "original_status IN ('present', 'absent', 'late', 'excused')",
            name="ck_attendance_corrections_original_status",
        ),
        CheckConstraint(
            "requested_status IN ('present', 'absent', 'late', 'excused')",
            name="ck_attendance_corrections_requested_status",
        ),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "record_id"],
            ["attendance_records.tenant_id", "attendance_records.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reviewed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    record_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    original_status: Mapped[str | None] = mapped_column(String(16))
    requested_status: Mapped[str | None] = mapped_column(String(16))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="requested")
    reviewed_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LeaveRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one faculty or staff leave request and approval lifecycle state."""

    __tablename__ = "leave_requests"
    __table_args__ = (
        CheckConstraint("start_date <= end_date", name="ck_leave_requests_date_range"),
        CheckConstraint(
            "leave_type IN ('casual', 'sick', 'earned', 'duty', 'other')",
            name="ck_leave_requests_type",
        ),
        CheckConstraint(
            "state IN ('requested', 'approved', 'rejected', 'cancelled')",
            name="ck_leave_requests_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["people.tenant_id", "people.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "approved_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    person_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    leave_type: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="requested")
    approved_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
