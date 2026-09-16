"""Add examination grading, logistics, adjustment, and publication records.

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b6c7d8e9f0a1"
down_revision: str | None = "a5b6c7d8e9f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_TABLES = (
    "grade_rules",
    "exam_seat_allocations",
    "invigilation_assignments",
    "mark_adjustments",
    "published_result_lines",
    "result_publication_events",
)


def _tenant_columns() -> list[sa.Column]:
    """Return common columns for one tenant-owned operational table."""

    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def _tenant_constraints() -> list[sa.Constraint]:
    """Return shared tenant identity constraints."""

    return [
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
    ]


def _tenant_fk(column: str, table: str, *, ondelete: str = "RESTRICT") -> sa.ForeignKeyConstraint:
    """Build one composite tenant-safe foreign key."""

    return sa.ForeignKeyConstraint(
        ["tenant_id", column],
        [f"{table}.tenant_id", f"{table}.id"],
        ondelete=ondelete,
    )


def _enable_forced_rls(table_name: str) -> None:
    """Enable forced tenant RLS and least-privilege runtime grants."""

    op.execute(sa.text(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text(
            f'CREATE POLICY "{table_name}_tenant_isolation" ON "{table_name}" '
            "USING (tenant_id = current_setting('app.tenant_id', true)::uuid) "
            "WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"
        )
    )
    op.execute(sa.text(f'GRANT SELECT, INSERT, UPDATE, DELETE ON "{table_name}" TO cms_runtime'))


def upgrade() -> None:
    """Create auditable examination grading, logistics, and publication records."""

    op.create_table(
        "grade_rules",
        *_tenant_columns(),
        sa.Column("term_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("min_percentage", sa.Numeric(6, 2), nullable=False),
        sa.Column("max_percentage", sa.Numeric(6, 2), nullable=False),
        sa.Column("letter_grade", sa.String(8), nullable=False),
        sa.Column("grade_point", sa.Numeric(4, 2), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="draft"),
        sa.CheckConstraint("version > 0", name="ck_grade_rules_version_positive"),
        sa.CheckConstraint("min_percentage >= 0 AND max_percentage <= 100", name="ck_grade_rules_range"),
        sa.CheckConstraint("min_percentage <= max_percentage", name="ck_grade_rules_range_order"),
        sa.CheckConstraint("grade_point >= 0", name="ck_grade_rules_point_non_negative"),
        sa.CheckConstraint("state IN ('draft', 'published', 'archived')", name="ck_grade_rules_state"),
        sa.UniqueConstraint("tenant_id", "term_id", "version", "letter_grade"),
        _tenant_fk("term_id", "terms"),
        *_tenant_constraints(),
    )
    op.create_table(
        "exam_seat_allocations",
        *_tenant_columns(),
        sa.Column("schedule_id", sa.Uuid(), nullable=False),
        sa.Column("registration_id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("seat_number", sa.String(32), nullable=False),
        sa.UniqueConstraint("tenant_id", "registration_id"),
        sa.UniqueConstraint("tenant_id", "schedule_id", "room_id", "seat_number"),
        _tenant_fk("schedule_id", "exam_schedules"),
        _tenant_fk("registration_id", "exam_registrations"),
        _tenant_fk("room_id", "rooms"),
        *_tenant_constraints(),
    )
    op.create_table(
        "invigilation_assignments",
        *_tenant_columns(),
        sa.Column("schedule_id", sa.Uuid(), nullable=False),
        sa.Column("faculty_id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.UniqueConstraint("tenant_id", "schedule_id", "faculty_id"),
        _tenant_fk("schedule_id", "exam_schedules"),
        _tenant_fk("faculty_id", "faculty_profiles"),
        _tenant_fk("room_id", "rooms"),
        *_tenant_constraints(),
    )
    op.create_table(
        "mark_adjustments",
        *_tenant_columns(),
        sa.Column("registration_id", sa.Uuid(), nullable=False),
        sa.Column("original_marks", sa.Numeric(8, 2), nullable=False),
        sa.Column("revised_marks", sa.Numeric(8, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="requested"),
        sa.Column("requested_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("reviewed_by_membership_id", sa.Uuid()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("original_marks >= 0 AND revised_marks >= 0", name="ck_mark_adjustments_non_negative"),
        sa.CheckConstraint("state IN ('requested', 'approved', 'rejected')", name="ck_mark_adjustments_state"),
        _tenant_fk("registration_id", "exam_registrations"),
        _tenant_fk("requested_by_membership_id", "tenant_memberships"),
        _tenant_fk("reviewed_by_membership_id", "tenant_memberships"),
        *_tenant_constraints(),
    )
    op.add_column("published_results", sa.Column("gpa", sa.Numeric(4, 2), nullable=False, server_default="0"))
    op.add_column("published_results", sa.Column("publication_version", sa.Integer(), nullable=False, server_default="1"))
    op.create_table(
        "published_result_lines",
        *_tenant_columns(),
        sa.Column("result_id", sa.Uuid(), nullable=False),
        sa.Column("registration_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(8, 2), nullable=False),
        sa.Column("max_marks", sa.Numeric(8, 2), nullable=False),
        sa.Column("pass_marks", sa.Numeric(8, 2), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("grade", sa.String(8), nullable=False),
        sa.Column("grade_point", sa.Numeric(4, 2), nullable=False),
        sa.UniqueConstraint("tenant_id", "result_id", "registration_id"),
        _tenant_fk("result_id", "published_results", ondelete="CASCADE"),
        _tenant_fk("registration_id", "exam_registrations"),
        _tenant_fk("subject_id", "subjects"),
        *_tenant_constraints(),
    )
    op.create_table(
        "result_publication_events",
        *_tenant_columns(),
        sa.Column("result_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(16), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("performed_by_membership_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("version > 0", name="ck_result_publication_events_version_positive"),
        sa.CheckConstraint("event_type IN ('published', 'reopened', 'republished')", name="ck_result_publication_events_type"),
        sa.UniqueConstraint("tenant_id", "result_id", "version", "event_type"),
        _tenant_fk("result_id", "published_results", ondelete="CASCADE"),
        _tenant_fk("performed_by_membership_id", "tenant_memberships"),
        *_tenant_constraints(),
    )
    for table_name in TENANT_TABLES:
        _enable_forced_rls(table_name)


def downgrade() -> None:
    """Remove examination operation records and aggregate publication metadata."""

    for table_name in reversed(TENANT_TABLES):
        op.drop_table(table_name)
    op.drop_column("published_results", "publication_version")
    op.drop_column("published_results", "gpa")