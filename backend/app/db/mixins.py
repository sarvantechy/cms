from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """Add a generated UUID primary key to an ORM model."""

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)


class TimestampMixin:
    """Add database-managed creation and update timestamps to an ORM model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
