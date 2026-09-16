"""Persistence models for actor-owned report views, exports, and schedules."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

TENANT_ID_REFERENCE = "tenants.id"
MEMBERSHIP_TENANT_REFERENCE = "tenant_memberships.tenant_id"
MEMBERSHIP_ID_REFERENCE = "tenant_memberships.id"


class SavedReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one named report filter owned by a tenant membership."""

    __tablename__ = "saved_reports"
    __table_args__ = (
        UniqueConstraint("tenant_id", "owner_membership_id", "name"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "owner_membership_id"],
            [MEMBERSHIP_TENANT_REFERENCE, MEMBERSHIP_ID_REFERENCE],
            ondelete="CASCADE",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    owner_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    filters: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)


class ReportExport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Audit one permission-scoped report export request."""

    __tablename__ = "report_exports"
    __table_args__ = (
        CheckConstraint("export_format IN ('csv')", name="ck_report_exports_format"),
        CheckConstraint("state IN ('completed', 'failed')", name="ck_report_exports_state"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "requested_by_membership_id"],
            [MEMBERSHIP_TENANT_REFERENCE, MEMBERSHIP_ID_REFERENCE],
            ondelete="CASCADE",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    requested_by_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(80), nullable=False)
    filters: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    export_format: Mapped[str] = mapped_column(String(8), nullable=False, default="csv")
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="completed")
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ReportSchedule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store recurring report-delivery configuration for one actor."""

    __tablename__ = "report_schedules"
    __table_args__ = (
        CheckConstraint("export_format IN ('csv')", name="ck_report_schedules_format"),
        CheckConstraint(
            "frequency IN ('daily', 'weekly', 'monthly')",
            name="ck_report_schedules_frequency",
        ),
        UniqueConstraint("tenant_id", "owner_membership_id", "name"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "owner_membership_id"],
            [MEMBERSHIP_TENANT_REFERENCE, MEMBERSHIP_ID_REFERENCE],
            ondelete="CASCADE",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    owner_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(80), nullable=False)
    filters: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    export_format: Mapped[str] = mapped_column(String(8), nullable=False, default="csv")
    frequency: Mapped[str] = mapped_column(String(16), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(320), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))