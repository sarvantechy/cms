"""add delivery attendance

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-29 22:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
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
    """Create delivery and attendance tables with tenant-safe constraints and RLS."""

    op.create_table(
        "faculty_profiles",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("employee_code", sa.String(length=48), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('active', 'on_leave', 'inactive')",
            name="ck_faculty_profiles_status",
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
        sa.UniqueConstraint("tenant_id", "employee_code"),
    )

    op.create_table(
        "subject_offerings",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("term_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('planned', 'active', 'completed', 'cancelled')",
            name="ck_subject_offerings_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["terms.tenant_id", "terms.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "subject_id"],
            ["subjects.tenant_id", "subjects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "section_id"],
            ["sections.tenant_id", "sections.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "term_id", "subject_id", "section_id"),
    )

    op.create_table(
        "faculty_allocations",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("offering_id", sa.Uuid(), nullable=False),
        sa.Column("faculty_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_faculty_allocations_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "offering_id"],
            ["subject_offerings.tenant_id", "subject_offerings.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "faculty_id"],
            ["faculty_profiles.tenant_id", "faculty_profiles.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "offering_id", "faculty_id"),
    )

    op.create_table(
        "timetable_periods",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("offering_id", sa.Uuid(), nullable=False),
        sa.Column("faculty_id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=True),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("day_of_week BETWEEN 1 AND 7", name="ck_timetable_periods_day_of_week"),
        sa.CheckConstraint("start_time < end_time", name="ck_timetable_periods_time_range"),
        sa.CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_timetable_periods_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "offering_id"],
            ["subject_offerings.tenant_id", "subject_offerings.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "faculty_id"],
            ["faculty_profiles.tenant_id", "faculty_profiles.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "room_id"],
            ["rooms.tenant_id", "rooms.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint(
            "tenant_id",
            "offering_id",
            "faculty_id",
            "day_of_week",
            "start_time",
            "end_time",
            name="uq_timetable_period_slot",
        ),
    )

    op.create_table(
        "class_sessions",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("period_id", sa.Uuid(), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "state IN ('scheduled', 'submitted', 'locked', 'cancelled')",
            name="ck_class_sessions_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "period_id"],
            ["timetable_periods.tenant_id", "timetable_periods.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "period_id", "session_date"),
    )

    op.create_table(
        "attendance_records",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('present', 'absent', 'late', 'excused')",
            name="ck_attendance_records_status",
        ),
        sa.CheckConstraint(
            "state IN ('submitted', 'locked')",
            name="ck_attendance_records_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "session_id"],
            ["class_sessions.tenant_id", "class_sessions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "session_id", "student_id"),
    )

    op.create_table(
        "attendance_corrections",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("reviewed_by_membership_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "state IN ('requested', 'approved', 'rejected')",
            name="ck_attendance_corrections_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "record_id"],
            ["attendance_records.tenant_id", "attendance_records.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reviewed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "leave_requests",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("leave_type", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("approved_by_membership_id", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("start_date <= end_date", name="ck_leave_requests_date_range"),
        sa.CheckConstraint(
            "leave_type IN ('casual', 'sick', 'earned', 'duty', 'other')",
            name="ck_leave_requests_type",
        ),
        sa.CheckConstraint(
            "state IN ('requested', 'approved', 'rejected', 'cancelled')",
            name="ck_leave_requests_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["people.tenant_id", "people.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "approved_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    tenant_tables = [
        "faculty_profiles",
        "subject_offerings",
        "faculty_allocations",
        "timetable_periods",
        "class_sessions",
        "attendance_records",
        "attendance_corrections",
        "leave_requests",
    ]
    _apply_tenant_rls(tenant_tables)

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_runtime') THEN
                GRANT SELECT, INSERT, UPDATE ON
                    faculty_profiles,
                    subject_offerings,
                    faculty_allocations,
                    timetable_periods,
                    class_sessions,
                    attendance_records,
                    attendance_corrections,
                    leave_requests
                TO cms_runtime;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    """Drop delivery and attendance tables created by this revision."""

    op.drop_table("leave_requests")
    op.drop_table("attendance_corrections")
    op.drop_table("attendance_records")
    op.drop_table("class_sessions")
    op.drop_table("timetable_periods")
    op.drop_table("faculty_allocations")
    op.drop_table("subject_offerings")
    op.drop_table("faculty_profiles")
