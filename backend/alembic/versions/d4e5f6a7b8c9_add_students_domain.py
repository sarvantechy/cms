"""add students domain

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-29 19:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
TENANT_ID_REFERENCE = "tenants.id"
STUDENTS_TENANT_ID_REFERENCE = "students.tenant_id"
STUDENTS_ID_REFERENCE = "students.id"


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
    """Enable forced RLS with null-safe tenant policies scoped to all roles."""

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
    """Create students and guardians tables with tenant-safe constraints and RLS."""

    op.create_table(
        "people",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(length=240), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("mobile_number", sa.String(length=24), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "email IS NOT NULL OR mobile_number IS NOT NULL",
            name="ck_people_contact_present",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "email"),
        sa.UniqueConstraint("tenant_id", "mobile_number"),
    )

    op.create_table(
        "students",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("source_application_id", sa.Uuid(), nullable=True),
        sa.Column("registration_number", sa.String(length=48), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('prospective', 'active', 'on_hold', 'graduated', 'discontinued')",
            name="ck_students_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["people.tenant_id", "people.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_application_id"],
            ["applications.tenant_id", "applications.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "person_id"),
        sa.UniqueConstraint("tenant_id", "registration_number"),
        sa.UniqueConstraint("tenant_id", "source_application_id"),
    )

    op.create_table(
        "guardians",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("mobile_number", sa.String(length=24), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "email IS NOT NULL OR mobile_number IS NOT NULL",
            name="ck_guardians_contact_present",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["people.tenant_id", "people.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "person_id"),
    )

    op.create_table(
        "student_guardians",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("guardian_id", sa.Uuid(), nullable=False),
        sa.Column("relationship", sa.String(length=32), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            [STUDENTS_TENANT_ID_REFERENCE, STUDENTS_ID_REFERENCE],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "guardian_id"],
            ["guardians.tenant_id", "guardians.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "student_id", "guardian_id"),
    )

    op.create_table(
        "student_enrollments",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=True),
        sa.Column("section_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'cancelled', 'transferred')",
            name="ck_student_enrollments_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            [STUDENTS_TENANT_ID_REFERENCE, STUDENTS_ID_REFERENCE],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["batches.tenant_id", "batches.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "section_id"],
            ["sections.tenant_id", "sections.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "student_id", "academic_year_id"),
    )

    op.create_table(
        "student_status_history",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", sa.String(length=16), nullable=False),
        sa.Column("to_status", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("changed_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "from_status IN ('prospective', 'active', 'on_hold', 'graduated', 'discontinued')",
            name="ck_student_status_history_from_status",
        ),
        sa.CheckConstraint(
            "to_status IN ('prospective', 'active', 'on_hold', 'graduated', 'discontinued')",
            name="ck_student_status_history_to_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            [STUDENTS_TENANT_ID_REFERENCE, STUDENTS_ID_REFERENCE],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "changed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    tenant_tables = [
        "people",
        "students",
        "guardians",
        "student_guardians",
        "student_enrollments",
        "student_status_history",
    ]
    _apply_tenant_rls(tenant_tables)

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_runtime') THEN
                GRANT SELECT, INSERT, UPDATE ON
                    people,
                    students,
                    guardians,
                    student_guardians,
                    student_enrollments,
                    student_status_history
                TO cms_runtime;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    """Drop students and guardians domain tables created by this revision."""

    op.drop_table("student_status_history")
    op.drop_table("student_enrollments")
    op.drop_table("student_guardians")
    op.drop_table("guardians")
    op.drop_table("students")
    op.drop_table("people")
