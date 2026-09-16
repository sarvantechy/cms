"""add communications and activities

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-08-29 20:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: str | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
TENANT_ID_REFERENCE = "tenants.id"


def _timestamp_columns() -> tuple[sa.Column, sa.Column]:
    """Return standard creation and update timestamp columns for tenant tables."""

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


def _apply_tenant_rls(table_names: list[str]) -> None:
    """Enable forced RLS and apply null-safe tenant policies to all roles."""

    for table_name in table_names:
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY")
        op.execute(
            sa.text(
                f"""
                CREATE POLICY tenant_isolation ON {table_name}
                AS PERMISSIVE
                FOR ALL
                TO PUBLIC
                USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
                WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
                """
            )
        )


def upgrade() -> None:
    """Create communications and activities tables with tenant-safe RLS and grants."""

    op.create_table(
        "notices",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("publish_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("audience_type", sa.String(length=24), nullable=False),
        sa.Column("audience_ref", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "state IN ('draft', 'scheduled', 'published', 'archived')",
            name="ck_notices_state",
        ),
        sa.CheckConstraint(
            "audience_type IN ('all', 'role', 'membership')",
            name="ck_notices_audience_type",
        ),
        sa.CheckConstraint(
            "((audience_type = 'all' AND audience_ref IS NULL) "
            "OR (audience_type <> 'all' AND audience_ref IS NOT NULL))",
            name="ck_notices_audience_ref",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "notice_deliveries",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("notice_id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "state IN ('pending', 'sent', 'failed', 'read')",
            name="ck_notice_deliveries_state",
        ),
        sa.CheckConstraint("attempts >= 0", name="ck_notice_deliveries_attempts_non_negative"),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "notice_id"],
            ["notices.tenant_id", "notices.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "notice_id", "membership_id"),
    )

    op.create_table(
        "activities",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("activity_type", sa.String(length=80), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("venue", sa.String(length=240), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("capacity IS NULL OR capacity > 0", name="ck_activities_capacity_positive"),
        sa.CheckConstraint(
            "state IN ('draft', 'published', 'cancelled', 'completed')",
            name="ck_activities_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "event_registrations",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "state IN ('registered', 'approved', 'attended', 'cancelled')",
            name="ck_event_registrations_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "activity_id"],
            ["activities.tenant_id", "activities.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "activity_id", "student_id"),
    )

    op.create_table(
        "achievements",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("certificate_ref", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "activity_id"],
            ["activities.tenant_id", "activities.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "student_id", "activity_id", "title"),
    )

    tenant_tables = [
        "notices",
        "notice_deliveries",
        "activities",
        "event_registrations",
        "achievements",
    ]
    _apply_tenant_rls(tenant_tables)

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_runtime') THEN
                GRANT SELECT, INSERT, UPDATE ON
                    notices,
                    notice_deliveries,
                    activities,
                    event_registrations,
                    achievements
                TO cms_runtime;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    """Drop communications and activities tables created by this revision."""

    op.drop_table("achievements")
    op.drop_table("event_registrations")
    op.drop_table("activities")
    op.drop_table("notice_deliveries")
    op.drop_table("notices")
