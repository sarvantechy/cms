"""platform sessions and security events

Revision ID: 9f86b82c1a47
Revises: 6efef23fdb61
Create Date: 2026-08-28 23:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9f86b82c1a47"
down_revision: str | None = "6efef23fdb61"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamp_columns() -> tuple[sa.Column, sa.Column]:
    """Return standard creation and update columns for a platform security table."""

    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def upgrade() -> None:
    """Create global platform session and security event persistence."""

    op.create_table(
        "platform_authentication_sessions",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("refresh_token_hash"),
    )
    op.create_table(
        "platform_security_events",
        sa.Column("account_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_runtime') THEN
                GRANT SELECT ON platform_role_assignments TO cms_runtime;
                GRANT SELECT, INSERT, UPDATE ON platform_authentication_sessions TO cms_runtime;
                GRANT SELECT, INSERT ON platform_security_events TO cms_runtime;
                GRANT UPDATE ON tenants TO cms_runtime;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    """Remove global platform session and security event persistence."""

    op.drop_table("platform_security_events")
    op.drop_table("platform_authentication_sessions")
