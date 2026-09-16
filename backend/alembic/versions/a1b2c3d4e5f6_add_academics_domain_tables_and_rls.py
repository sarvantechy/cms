"""add academics domain tables and rls

Revision ID: a1b2c3d4e5f6
Revises: 9f86b82c1a47
Create Date: 2026-08-28 23:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "9f86b82c1a47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamp_columns() -> tuple[sa.Column, sa.Column]:
    """Return standard creation and update columns for a tenant table."""

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
    """Create academic structure tables with tenant isolation and RLS policies."""

    # Campuses
    op.create_table(
        "campuses",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("status IN ('active', 'inactive', 'closed')", name="ck_campuses_status"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    # Academic Years
    op.create_table(
        "academic_years",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('planned', 'active', 'completed', 'archived')",
            name="ck_academic_years_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    # Terms
    op.create_table(
        "terms",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('planned', 'active', 'completed')", name="ck_terms_status"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "academic_year_id", "code"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    # Departments
    op.create_table(
        "departments",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_departments_status"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    # Programs
    op.create_table(
        "programs",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("degree_level", sa.String(length=32), nullable=False),
        sa.Column("duration_years", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'discontinued')", name="ck_programs_status"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "department_id"],
            ["departments.tenant_id", "departments.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    # Subjects
    op.create_table(
        "subjects",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'discontinued')", name="ck_subjects_status"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "department_id"],
            ["departments.tenant_id", "departments.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    # Batches
    op.create_table(
        "batches",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("admission_year", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('active', 'graduated', 'archived')", name="ck_batches_status"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "program_id", "admission_year"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    # Sections
    op.create_table(
        "sections",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("max_capacity", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('active', 'merged', 'archived')", name="ck_sections_status"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["batches.tenant_id", "batches.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "batch_id", "code"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    # Rooms
    op.create_table(
        "rooms",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campus_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("room_type", sa.String(length=32), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("has_projector", sa.Boolean(), nullable=False),
        sa.Column("has_computers", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "room_type IN ('classroom', 'lab', 'auditorium', 'seminar', 'virtual')",
            name="ck_rooms_type",
        ),
        sa.CheckConstraint(
            "status IN ('available', 'maintenance', 'unavailable')", name="ck_rooms_status"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campus_id"],
            ["campuses.tenant_id", "campuses.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "campus_id", "code"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    # Enable RLS on all academic tables
    op.execute(
        """
        ALTER TABLE campuses ENABLE ROW LEVEL SECURITY; ALTER TABLE campuses FORCE ROW LEVEL SECURITY;
        ALTER TABLE academic_years ENABLE ROW LEVEL SECURITY; ALTER TABLE academic_years FORCE ROW LEVEL SECURITY;
        ALTER TABLE terms ENABLE ROW LEVEL SECURITY; ALTER TABLE terms FORCE ROW LEVEL SECURITY;
        ALTER TABLE departments ENABLE ROW LEVEL SECURITY; ALTER TABLE departments FORCE ROW LEVEL SECURITY;
        ALTER TABLE programs ENABLE ROW LEVEL SECURITY; ALTER TABLE programs FORCE ROW LEVEL SECURITY;
        ALTER TABLE subjects ENABLE ROW LEVEL SECURITY; ALTER TABLE subjects FORCE ROW LEVEL SECURITY;
        ALTER TABLE batches ENABLE ROW LEVEL SECURITY; ALTER TABLE batches FORCE ROW LEVEL SECURITY;
        ALTER TABLE sections ENABLE ROW LEVEL SECURITY; ALTER TABLE sections FORCE ROW LEVEL SECURITY;
        ALTER TABLE rooms ENABLE ROW LEVEL SECURITY; ALTER TABLE rooms FORCE ROW LEVEL SECURITY;
        """
    )

    # Create RLS policies for tenant isolation
    op.execute(
        """
        DO $$
        DECLARE
            t text;
        BEGIN
            FOR t IN SELECT unnest(ARRAY[
                'campuses', 'academic_years', 'terms', 'departments', 
                'programs', 'subjects', 'batches', 'sections', 'rooms'
            ])
            LOOP
                EXECUTE format(
                    'CREATE POLICY tenant_isolation ON %I USING (tenant_id = NULLIF(current_setting(''app.tenant_id'', true), '''')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting(''app.tenant_id'', true), '''')::uuid)',
                    t
                );
            END LOOP;
        END
        $$;
        """
    )

    # Grant runtime permissions
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_runtime') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON 
                    campuses, academic_years, terms, departments, 
                    programs, subjects, batches, sections, rooms 
                TO cms_runtime;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    """Remove academic structure tables and their policies."""

    op.drop_table("rooms")
    op.drop_table("sections")
    op.drop_table("batches")
    op.drop_table("subjects")
    op.drop_table("programs")
    op.drop_table("departments")
    op.drop_table("terms")
    op.drop_table("academic_years")
    op.drop_table("campuses")
