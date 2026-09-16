from sqlalchemy import Boolean, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represent one independently secured college using the platform."""

    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint("key = lower(key)", name="ck_tenants_normalized_key"),
        CheckConstraint(
            "status IN ('setup', 'active', 'suspended', 'closed')",
            name="ck_tenants_status",
        ),
    )

    key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(240), nullable=False)
    short_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="setup")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Kolkata")
    primary_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#172d43")
    accent_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#ef5b3f")
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
