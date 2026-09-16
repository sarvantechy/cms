"""add examinations results

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-30 00:35:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: str | None = "f6a7b8c9d0e1"
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
    """Create examinations and published results tables with tenant-safe RLS and grants."""

    op.create_table(
        "assessment_schemes",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("term_id", sa.Uuid(), nullable=False),
        sa.Column("max_marks", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("pass_marks", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("max_marks > 0", name="ck_assessment_schemes_max_marks_positive"),
        sa.CheckConstraint("pass_marks >= 0", name="ck_assessment_schemes_pass_marks_non_negative"),
        sa.CheckConstraint("pass_marks <= max_marks", name="ck_assessment_schemes_pass_marks_le_max"),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "subject_id"],
            ["subjects.tenant_id", "subjects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["terms.tenant_id", "terms.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "subject_id", "program_id", "term_id"),
    )

    op.create_table(
        "exam_sessions",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("term_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "state IN ('draft', 'active', 'published', 'closed')",
            name="ck_exam_sessions_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["terms.tenant_id", "terms.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "term_id"),
    )

    op.create_table(
        "exam_schedules",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("offering_id", sa.Uuid(), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=True),
        sa.Column("max_marks", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("max_marks > 0", name="ck_exam_schedules_max_marks_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "session_id"],
            ["exam_sessions.tenant_id", "exam_sessions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "offering_id"],
            ["subject_offerings.tenant_id", "subject_offerings.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "room_id"],
            ["rooms.tenant_id", "rooms.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "session_id", "offering_id"),
    )

    op.create_table(
        "exam_registrations",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("schedule_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("eligibility", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "eligibility IN ('eligible', 'ineligible', 'withheld')",
            name="ck_exam_registrations_eligibility",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "schedule_id"],
            ["exam_schedules.tenant_id", "exam_schedules.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "schedule_id", "student_id"),
    )

    op.create_table(
        "mark_entries",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("registration_id", sa.Uuid(), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("verified_by_membership_id", sa.Uuid(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by_membership_id", sa.Uuid(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("marks_obtained >= 0", name="ck_mark_entries_marks_non_negative"),
        sa.CheckConstraint(
            "state IN ('entered', 'verified', 'locked')",
            name="ck_mark_entries_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "registration_id"],
            ["exam_registrations.tenant_id", "exam_registrations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "verified_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "locked_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "registration_id"),
    )

    op.create_table(
        "published_results",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("total_marks", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("total_max_marks", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("percentage", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("grade", sa.String(length=8), nullable=False),
        sa.Column("result", sa.String(length=8), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_by_membership_id", sa.Uuid(), nullable=True),
        sa.Column("reopened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reopened_by_membership_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("result IN ('pass', 'fail')", name="ck_published_results_result"),
        sa.CheckConstraint("state IN ('published', 'reopened')", name="ck_published_results_state"),
        sa.CheckConstraint("total_marks >= 0", name="ck_published_results_total_marks_non_negative"),
        sa.CheckConstraint("total_max_marks > 0", name="ck_published_results_total_max_marks_positive"),
        sa.CheckConstraint("percentage >= 0", name="ck_published_results_percentage_non_negative"),
        sa.CheckConstraint("percentage <= 100", name="ck_published_results_percentage_le_hundred"),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "session_id"],
            ["exam_sessions.tenant_id", "exam_sessions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "published_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reopened_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "student_id", "session_id"),
    )

    tenant_tables = [
        "assessment_schemes",
        "exam_sessions",
        "exam_schedules",
        "exam_registrations",
        "mark_entries",
        "published_results",
    ]
    _apply_tenant_rls(tenant_tables)

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_runtime') THEN
                GRANT SELECT, INSERT, UPDATE ON
                    assessment_schemes,
                    exam_sessions,
                    exam_schedules,
                    exam_registrations,
                    mark_entries,
                    published_results
                TO cms_runtime;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    """Drop examinations and published results tables created by this revision."""

    op.drop_table("published_results")
    op.drop_table("mark_entries")
    op.drop_table("exam_registrations")
    op.drop_table("exam_schedules")
    op.drop_table("exam_sessions")
    op.drop_table("assessment_schemes")
