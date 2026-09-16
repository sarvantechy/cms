"""add advanced academic masters

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-29 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
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
    """Enable, force, and define null-safe tenant policies for each table."""

    for table_name in table_names:
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY")
        op.execute(
            sa.text(
                f"""
                CREATE POLICY tenant_isolation ON {table_name}
                USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
                WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
                """
            )
        )


def upgrade() -> None:
    """Create advanced academic master tables with tenant-safe constraints and RLS."""

    op.create_table(
        "college_settings",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("institution_name", sa.String(length=240), nullable=False),
        sa.Column("short_name", sa.String(length=80), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("locale", sa.String(length=32), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "regulations",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("effective_from_year", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("status IN ('active', 'inactive', 'archived')", name="ck_regulations_status"),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "curricula",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("regulation_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("total_credits", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("status IN ('draft', 'active', 'archived')", name="ck_curricula_status"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "regulation_id"],
            ["regulations.tenant_id", "regulations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "program_id", "regulation_id", "code"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "curriculum_subjects",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("curriculum_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("term_number", sa.Integer(), nullable=False),
        sa.Column("is_elective", sa.Boolean(), nullable=False),
        sa.Column("credits_override", sa.Integer(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["tenant_id", "curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "subject_id"],
            ["subjects.tenant_id", "subjects.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "curriculum_id", "subject_id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "calendar_events",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("term_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("event_type", sa.String(length=24), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("is_holiday", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "event_type IN ('instructional', 'exam', 'holiday', 'deadline', 'other')",
            name="ck_calendar_events_type",
        ),
        sa.CheckConstraint(
            "status IN ('planned', 'published', 'cancelled')",
            name="ck_calendar_events_status",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["terms.tenant_id", "terms.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "academic_year_id", "name", "starts_on"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "numbering_formats",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("prefix", sa.String(length=40), nullable=True),
        sa.Column("suffix", sa.String(length=40), nullable=True),
        sa.Column("padding", sa.Integer(), nullable=False),
        sa.Column("next_number", sa.Integer(), nullable=False),
        sa.Column("reset_frequency", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "reset_frequency IN ('none', 'yearly', 'termly')",
            name="ck_numbering_formats_reset_frequency",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code"),
        sa.UniqueConstraint("tenant_id", "entity_type"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    tenant_tables = [
        "college_settings",
        "regulations",
        "curricula",
        "curriculum_subjects",
        "calendar_events",
        "numbering_formats",
    ]
    _apply_tenant_rls(tenant_tables)

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_runtime') THEN
                GRANT SELECT, INSERT, UPDATE ON
                    college_settings,
                    regulations,
                    curricula,
                    curriculum_subjects,
                    calendar_events,
                    numbering_formats
                TO cms_runtime;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    """Remove advanced academic master tables and related access control policies."""

    op.drop_table("numbering_formats")
    op.drop_table("calendar_events")
    op.drop_table("curriculum_subjects")
    op.drop_table("curricula")
    op.drop_table("regulations")
    op.drop_table("college_settings")