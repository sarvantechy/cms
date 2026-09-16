"""Add faculty delivery operations.

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e3f4a5b6c7d8"
down_revision: str | None = "d2e3f4a5b6c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = (
    "faculty_department_postings",
    "class_substitutions",
    "lesson_plans",
    "learning_materials",
    "syllabus_progress",
)


def _tenant_columns() -> list[sa.Column]:
    """Return common UUID and timestamp columns for one tenant-owned table."""

    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def _secure_table(table_name: str) -> None:
    """Force tenant RLS and grant restricted runtime data operations."""

    op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {table_name}
        AS PERMISSIVE FOR ALL TO PUBLIC
        USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
        """
    )
    op.execute(
        f"""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_runtime') THEN
                GRANT SELECT, INSERT, UPDATE ON {table_name} TO cms_runtime;
            END IF;
        END $$
        """
    )


def upgrade() -> None:
    """Create forced-RLS delivery operation tables and runtime grants."""

    op.create_table(
        "faculty_department_postings",
        *_tenant_columns(),
        sa.Column("faculty_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.CheckConstraint("ends_on IS NULL OR ends_on >= starts_on", name="ck_faculty_postings_dates"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "faculty_id"], ["faculty_profiles.tenant_id", "faculty_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "department_id"], ["departments.tenant_id", "departments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "faculty_id", "department_id", "starts_on"),
    )
    op.create_table(
        "class_substitutions",
        *_tenant_columns(),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("substitute_faculty_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("state", sa.String(16), server_default="requested", nullable=False),
        sa.CheckConstraint("state IN ('requested', 'approved', 'rejected', 'cancelled')", name="ck_class_substitutions_state"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "session_id"], ["class_sessions.tenant_id", "class_sessions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "substitute_faculty_id"], ["faculty_profiles.tenant_id", "faculty_profiles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "session_id"),
    )
    op.create_table(
        "lesson_plans",
        *_tenant_columns(),
        sa.Column("offering_id", sa.Uuid(), nullable=False),
        sa.Column("faculty_id", sa.Uuid(), nullable=False),
        sa.Column("planned_on", sa.Date(), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("state", sa.String(16), server_default="draft", nullable=False),
        sa.CheckConstraint("state IN ('draft', 'published', 'completed', 'cancelled')", name="ck_lesson_plans_state"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "offering_id"], ["subject_offerings.tenant_id", "subject_offerings.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "faculty_id"], ["faculty_profiles.tenant_id", "faculty_profiles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )
    op.create_table(
        "learning_materials",
        *_tenant_columns(),
        sa.Column("offering_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("material_type", sa.String(24), nullable=False),
        sa.Column("resource_url", sa.String(2048), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.CheckConstraint("material_type IN ('document', 'link', 'video', 'assignment', 'other')", name="ck_learning_materials_type"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "offering_id"], ["subject_offerings.tenant_id", "subject_offerings.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )
    op.create_table(
        "syllabus_progress",
        *_tenant_columns(),
        sa.Column("offering_id", sa.Uuid(), nullable=False),
        sa.Column("faculty_id", sa.Uuid(), nullable=False),
        sa.Column("recorded_on", sa.Date(), nullable=False),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("completion_percentage", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint("completion_percentage BETWEEN 0 AND 100", name="ck_syllabus_progress_percentage"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "offering_id"], ["subject_offerings.tenant_id", "subject_offerings.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "faculty_id"], ["faculty_profiles.tenant_id", "faculty_profiles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )
    for table_name in TABLES:
        _secure_table(table_name)


def downgrade() -> None:
    """Drop faculty delivery operation tables in dependency-safe order."""

    for table_name in reversed(TABLES):
        op.drop_table(table_name)
