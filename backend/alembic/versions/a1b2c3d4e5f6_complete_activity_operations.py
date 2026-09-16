"""Complete activity operations and participation outcomes.

Revision ID: 1a2b3c4d5e6f
Revises: f0a1b2c3d4e5
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "1a2b3c4d5e6f"
down_revision: str | None = "f0a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = (
    "activity_clubs",
    "activity_approval_requests",
    "activity_teams",
    "activity_team_members",
    "activity_expenses",
    "activity_certificates",
    "activity_points",
)


def _tenant_columns() -> tuple[sa.Column, ...]:
    """Return standard identity, tenant, and timestamp columns for activity tables."""

    return (
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
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


def _tenant_constraints() -> tuple[sa.Constraint, ...]:
    """Return the standard primary, tenant identity, and tenant foreign-key constraints."""

    return (
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
    )


def _secure_table(table_name: str) -> None:
    """Enable forced tenant RLS and grant runtime access to one activity table."""

    op.execute(sa.text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY"))
    op.execute(
        sa.text(
            f"CREATE POLICY {table_name}_tenant_isolation ON {table_name} "
            "USING (tenant_id = current_setting('app.tenant_id', true)::uuid) "
            "WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"
        )
    )
    op.execute(sa.text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table_name} TO cms_runtime"))


def upgrade() -> None:
    """Create complete tenant-owned activity workflow persistence."""

    op.create_table(
        "activity_clubs",
        *_tenant_columns(),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.CheckConstraint("status IN ('active', 'inactive', 'archived')", name="ck_activity_clubs_status"),
        sa.UniqueConstraint("tenant_id", "name"),
        *_tenant_constraints(),
    )
    op.add_column("activities", sa.Column("club_id", sa.Uuid()))
    op.add_column("activities", sa.Column("eligibility_notes", sa.Text()))
    op.create_foreign_key(
        "fk_activities_club",
        "activities",
        "activity_clubs",
        ["tenant_id", "club_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )

    op.create_table(
        "activity_approval_requests",
        *_tenant_columns(),
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("request_type", sa.String(16), nullable=False),
        sa.Column("requested_value", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2)),
        sa.Column("state", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("reviewed_by_membership_id", sa.Uuid()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("review_comment", sa.Text()),
        sa.CheckConstraint("request_type IN ('venue', 'budget')", name="ck_activity_approvals_type"),
        sa.CheckConstraint("state IN ('pending', 'approved', 'rejected')", name="ck_activity_approvals_state"),
        sa.CheckConstraint("amount IS NULL OR amount >= 0", name="ck_activity_approvals_amount"),
        sa.UniqueConstraint("tenant_id", "activity_id", "request_type"),
        sa.ForeignKeyConstraint(["tenant_id", "activity_id"], ["activities.tenant_id", "activities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "reviewed_by_membership_id"], ["tenant_memberships.tenant_id", "tenant_memberships.id"], ondelete="RESTRICT"),
        *_tenant_constraints(),
    )
    op.create_table(
        "activity_teams",
        *_tenant_columns(),
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("captain_student_id", sa.Uuid()),
        sa.UniqueConstraint("tenant_id", "activity_id", "name"),
        sa.ForeignKeyConstraint(["tenant_id", "activity_id"], ["activities.tenant_id", "activities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "captain_student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"),
        *_tenant_constraints(),
    )
    op.create_table(
        "activity_team_members",
        *_tenant_columns(),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.UniqueConstraint("tenant_id", "team_id", "student_id"),
        sa.ForeignKeyConstraint(["tenant_id", "team_id"], ["activity_teams.tenant_id", "activity_teams.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"),
        *_tenant_constraints(),
    )
    op.create_table(
        "activity_expenses",
        *_tenant_columns(),
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.String(240), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="submitted"),
        sa.Column("reviewed_by_membership_id", sa.Uuid()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("amount > 0", name="ck_activity_expenses_amount"),
        sa.CheckConstraint("state IN ('submitted', 'approved', 'rejected')", name="ck_activity_expenses_state"),
        sa.ForeignKeyConstraint(["tenant_id", "activity_id"], ["activities.tenant_id", "activities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "reviewed_by_membership_id"], ["tenant_memberships.tenant_id", "tenant_memberships.id"], ondelete="RESTRICT"),
        *_tenant_constraints(),
    )
    op.create_table(
        "activity_certificates",
        *_tenant_columns(),
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("registration_id", sa.Uuid(), nullable=False),
        sa.Column("serial_number", sa.String(96), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("tenant_id", "registration_id"),
        sa.UniqueConstraint("tenant_id", "serial_number"),
        sa.ForeignKeyConstraint(["tenant_id", "activity_id"], ["activities.tenant_id", "activities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "registration_id"], ["event_registrations.tenant_id", "event_registrations.id"], ondelete="RESTRICT"),
        *_tenant_constraints(),
    )
    op.create_table(
        "activity_points",
        *_tenant_columns(),
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(240), nullable=False),
        sa.CheckConstraint("points > 0", name="ck_activity_points_positive"),
        sa.UniqueConstraint("tenant_id", "activity_id", "student_id", "reason"),
        sa.ForeignKeyConstraint(["tenant_id", "activity_id"], ["activities.tenant_id", "activities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "student_id"], ["students.tenant_id", "students.id"], ondelete="RESTRICT"),
        *_tenant_constraints(),
    )

    for table_name in TABLES:
        _secure_table(table_name)


def downgrade() -> None:
    """Remove complete activity workflow persistence."""

    for table_name in reversed(TABLES[1:]):
        op.drop_table(table_name)
    op.drop_constraint("fk_activities_club", "activities", type_="foreignkey")
    op.drop_column("activities", "eligibility_notes")
    op.drop_column("activities", "club_id")
    op.drop_table("activity_clubs")