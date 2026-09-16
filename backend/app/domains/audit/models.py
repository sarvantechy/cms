"""Persistence models for tenant-scoped security and business audit events."""

from uuid import UUID

from sqlalchemy import JSON, ForeignKey, ForeignKeyConstraint, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AuditEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Record an append-only tenant event attributable to an actor when available."""

    __tablename__ = "audit_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    account_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL")
    )
    membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    details: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
