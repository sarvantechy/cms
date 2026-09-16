from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache
from uuid import UUID

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def _postgresql_engine(database_url: str, setting_name: str) -> Engine:
    """Create a pooled engine after requiring a PostgreSQL connection URL."""

    if not database_url.startswith("postgresql"):
        raise RuntimeError(f"{setting_name} must point to PostgreSQL")
    return create_engine(database_url, pool_pre_ping=True)


@lru_cache
def owner_session_factory() -> sessionmaker[Session]:
    """Return the cached owner session factory for migrations and onboarding."""

    return sessionmaker(
        bind=_postgresql_engine(settings.database_url, "DATABASE_URL"),
        expire_on_commit=False,
    )


@lru_cache
def runtime_session_factory() -> sessionmaker[Session]:
    """Return the cached restricted runtime session factory for API operations."""

    return sessionmaker(
        bind=_postgresql_engine(settings.runtime_database_url, "RUNTIME_DATABASE_URL"),
        expire_on_commit=False,
    )


@contextmanager
def tenant_session(tenant_id: UUID) -> Generator[Session, None, None]:
    """Yield a runtime transaction with PostgreSQL tenant context configured."""

    with runtime_session_factory()() as session, session.begin():
        session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )
        yield session


@contextmanager
def owner_session() -> Generator[Session, None, None]:
    """Yield an owner transaction for controlled platform administration tasks."""

    with owner_session_factory()() as session, session.begin():
        yield session
