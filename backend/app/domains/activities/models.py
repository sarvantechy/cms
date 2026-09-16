"""SQLAlchemy models for tenant-scoped activities, registrations, and achievements."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
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


class ActivityClub(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Organize recurring tenant activities under one managed club."""

    __tablename__ = "activity_clubs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'archived')",
            name="ck_activity_clubs_status",
        ),
        UniqueConstraint("tenant_id", "name"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Activity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one event or activity record with operational lifecycle state."""

    __tablename__ = "activities"
    __table_args__ = (
        CheckConstraint("capacity IS NULL OR capacity > 0", name="ck_activities_capacity_positive"),
        CheckConstraint(
            "state IN ('draft', 'published', 'cancelled', 'completed')",
            name="ck_activities_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "club_id"],
            ["activity_clubs.tenant_id", "activity_clubs.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    club_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    venue: Mapped[str | None] = mapped_column(String(240))
    capacity: Mapped[int | None] = mapped_column(Integer)
    eligibility_notes: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")


class EventRegistration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Register one student against one tenant activity participation flow."""

    __tablename__ = "event_registrations"
    __table_args__ = (
        CheckConstraint(
            "state IN ('registered', 'approved', 'attended', 'cancelled')",
            name="ck_event_registrations_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "activity_id", "student_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "activity_id"],
            ["activities.tenant_id", "activities.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    activity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="registered")


class Achievement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one student achievement outcome linked to an activity."""

    __tablename__ = "achievements"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "student_id", "activity_id", "title"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "activity_id"],
            ["activities.tenant_id", "activities.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    activity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    certificate_ref: Mapped[str | None] = mapped_column(String(255))


class ActivityApprovalRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track one venue or budget approval decision for an activity."""

    __tablename__ = "activity_approval_requests"
    __table_args__ = (
        CheckConstraint(
            "request_type IN ('venue', 'budget')",
            name="ck_activity_approvals_type",
        ),
        CheckConstraint(
            "state IN ('pending', 'approved', 'rejected')",
            name="ck_activity_approvals_state",
        ),
        CheckConstraint("amount IS NULL OR amount >= 0", name="ck_activity_approvals_amount"),
        UniqueConstraint("tenant_id", "activity_id", "request_type"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "activity_id"],
            ["activities.tenant_id", "activities.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reviewed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    activity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    request_type: Mapped[str] = mapped_column(String(16), nullable=False)
    requested_value: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    reviewed_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_comment: Mapped[str | None] = mapped_column(Text)


class ActivityTeam(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represent one named team participating in an activity."""

    __tablename__ = "activity_teams"
    __table_args__ = (
        UniqueConstraint("tenant_id", "activity_id", "name"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "activity_id"],
            ["activities.tenant_id", "activities.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "captain_student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    activity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    captain_student_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))


class ActivityTeamMember(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Associate one approved participant with an activity team."""

    __tablename__ = "activity_team_members"
    __table_args__ = (
        UniqueConstraint("tenant_id", "team_id", "student_id"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "team_id"],
            ["activity_teams.tenant_id", "activity_teams.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    team_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)


class ActivityExpense(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one reviewed expense against an activity budget."""

    __tablename__ = "activity_expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_activity_expenses_amount"),
        CheckConstraint(
            "state IN ('submitted', 'approved', 'rejected')",
            name="ck_activity_expenses_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "activity_id"],
            ["activities.tenant_id", "activities.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reviewed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    activity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="submitted")
    reviewed_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ActivityCertificate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Issue a uniquely verifiable certificate from attended participation."""

    __tablename__ = "activity_certificates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "registration_id"),
        UniqueConstraint("tenant_id", "serial_number"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "activity_id"],
            ["activities.tenant_id", "activities.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "registration_id"],
            ["event_registrations.tenant_id", "event_registrations.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    activity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    registration_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(96), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ActivityPoint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Award immutable positive activity points for one student outcome."""

    __tablename__ = "activity_points"
    __table_args__ = (
        CheckConstraint("points > 0", name="ck_activity_points_positive"),
        UniqueConstraint("tenant_id", "activity_id", "student_id", "reason"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "activity_id"],
            ["activities.tenant_id", "activities.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    activity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(240), nullable=False)
