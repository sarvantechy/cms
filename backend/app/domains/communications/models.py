"""SQLAlchemy models for tenant-scoped communications notices and deliveries."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
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


class Notice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one tenant notice and its publication lifecycle metadata."""

    __tablename__ = "notices"
    __table_args__ = (
        CheckConstraint(
            "state IN ('draft', 'scheduled', 'published', 'archived')",
            name="ck_notices_state",
        ),
        CheckConstraint(
            "audience_type IN ('all', 'role', 'membership')",
            name="ck_notices_audience_type",
        ),
        CheckConstraint(
            "((audience_type = 'all' AND audience_ref IS NULL) "
            "OR (audience_type <> 'all' AND audience_ref IS NOT NULL))",
            name="ck_notices_audience_ref",
        ),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "template_id"], ["message_templates.tenant_id", "message_templates.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["tenant_id", "approved_by_membership_id"], ["tenant_memberships.tenant_id", "tenant_memberships.id"], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    template_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    audience_type: Mapped[str] = mapped_column(String(24), nullable=False)
    audience_ref: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    requires_acknowledgement: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NoticeDelivery(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track one membership-level delivery state for one tenant notice."""

    __tablename__ = "notice_deliveries"
    __table_args__ = (
        CheckConstraint(
            "state IN ('pending', 'sent', 'failed', 'read')",
            name="ck_notice_deliveries_state",
        ),
        CheckConstraint("attempts >= 0", name="ck_notice_deliveries_attempts_non_negative"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "notice_id", "membership_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "notice_id"],
            ["notices.tenant_id", "notices.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    notice_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MessageTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one reusable channel-specific communication template."""

    __tablename__ = "message_templates"
    __table_args__ = (CheckConstraint("channel IN ('in_app', 'email', 'sms')", name="ck_message_templates_channel"), UniqueConstraint("tenant_id", "code"), UniqueConstraint("tenant_id", "id"), ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"))

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    title_template: Mapped[str] = mapped_column(String(240), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False, default="in_app")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CommunicationPreference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one membership's channel preferences."""

    __tablename__ = "communication_preferences"
    __table_args__ = (UniqueConstraint("tenant_id", "membership_id"), UniqueConstraint("tenant_id", "id"), ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"), ForeignKeyConstraint(["tenant_id", "membership_id"], ["tenant_memberships.tenant_id", "tenant_memberships.id"], ondelete="RESTRICT"))

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class NoticeAcknowledgement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Record one membership acknowledgement of a notice."""

    __tablename__ = "notice_acknowledgements"
    __table_args__ = (UniqueConstraint("tenant_id", "notice_id", "membership_id"), UniqueConstraint("tenant_id", "id"), ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"), ForeignKeyConstraint(["tenant_id", "notice_id"], ["notices.tenant_id", "notices.id"], ondelete="RESTRICT"), ForeignKeyConstraint(["tenant_id", "membership_id"], ["tenant_memberships.tenant_id", "tenant_memberships.id"], ondelete="RESTRICT"))

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    notice_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DeliveryAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track one provider-independent channel delivery attempt."""

    __tablename__ = "delivery_attempts"
    __table_args__ = (CheckConstraint("channel IN ('in_app', 'email', 'sms')", name="ck_delivery_attempts_channel"), CheckConstraint("state IN ('pending', 'sent', 'failed')", name="ck_delivery_attempts_state"), CheckConstraint("attempt_number > 0", name="ck_delivery_attempts_number_positive"), UniqueConstraint("tenant_id", "delivery_id", "channel", "attempt_number"), UniqueConstraint("tenant_id", "id"), ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"), ForeignKeyConstraint(["tenant_id", "delivery_id"], ["notice_deliveries.tenant_id", "notice_deliveries.id"], ondelete="RESTRICT"), ForeignKeyConstraint(["tenant_id", "job_id"], ["communication_delivery_jobs.tenant_id", "communication_delivery_jobs.id"], ondelete="RESTRICT"))

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    delivery_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    job_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    provider_reference: Mapped[str | None] = mapped_column(String(160))
    error_detail: Mapped[str | None] = mapped_column(Text)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CommunicationDeliveryJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Queue one idempotent provider-channel delivery for a notice recipient."""

    __tablename__ = "communication_delivery_jobs"
    __table_args__ = (CheckConstraint("channel IN ('in_app', 'email', 'sms')", name="ck_communication_delivery_jobs_channel"), CheckConstraint("state IN ('pending', 'processing', 'sent', 'failed')", name="ck_communication_delivery_jobs_state"), CheckConstraint("retry_count >= 0", name="ck_communication_delivery_jobs_retry_non_negative"), UniqueConstraint("tenant_id", "delivery_id", "channel"), UniqueConstraint("tenant_id", "idempotency_key"), UniqueConstraint("tenant_id", "id"), ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"), ForeignKeyConstraint(["tenant_id", "delivery_id"], ["notice_deliveries.tenant_id", "notice_deliveries.id"], ondelete="RESTRICT"))

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    delivery_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)


class NoticeApprovalEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Preserve one immutable notice approval workflow transition."""

    __tablename__ = "notice_approval_events"
    __table_args__ = (CheckConstraint("action IN ('submitted', 'approved', 'rejected')", name="ck_notice_approval_events_action"), UniqueConstraint("tenant_id", "id"), ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"), ForeignKeyConstraint(["tenant_id", "notice_id"], ["notices.tenant_id", "notices.id"], ondelete="RESTRICT"), ForeignKeyConstraint(["tenant_id", "membership_id"], ["tenant_memberships.tenant_id", "tenant_memberships.id"], ondelete="RESTRICT"))

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    notice_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
