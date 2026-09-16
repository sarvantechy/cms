"""Add actor-owned reporting views, exports, and schedules.

Revision ID: 2b3c4d5e6f7a
Revises: 1a2b3c4d5e6f
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "2b3c4d5e6f7a"
down_revision: str | None = "1a2b3c4d5e6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("saved_reports", "report_exports", "report_schedules")


def _base_columns() -> tuple[sa.Column, ...]:
    """Return standard identity, tenant, and timestamp columns."""

    return (
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def _base_constraints() -> tuple[sa.Constraint, ...]:
    """Return primary and tenant ownership constraints."""

    return (
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
    )


def _secure_table(table_name: str) -> None:
    """Enable forced tenant RLS and grant runtime access."""

    op.execute(sa.text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY"))
    op.execute(sa.text(f"CREATE POLICY {table_name}_tenant_isolation ON {table_name} USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"))
    op.execute(sa.text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table_name} TO cms_runtime"))


def upgrade() -> None:
    """Create reporting persistence with tenant-safe ownership."""

    membership_fk = lambda column: sa.ForeignKeyConstraint(
        ["tenant_id", column], ["tenant_memberships.tenant_id", "tenant_memberships.id"], ondelete="CASCADE"
    )
    op.create_table(
        "saved_reports", *_base_columns(),
        sa.Column("owner_membership_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.UniqueConstraint("tenant_id", "owner_membership_id", "name"),
        membership_fk("owner_membership_id"), *_base_constraints(),
    )
    op.create_table(
        "report_exports", *_base_columns(),
        sa.Column("requested_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("metric_key", sa.String(80), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("export_format", sa.String(8), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.CheckConstraint("export_format IN ('csv')", name="ck_report_exports_format"),
        sa.CheckConstraint("state IN ('completed', 'failed')", name="ck_report_exports_state"),
        membership_fk("requested_by_membership_id"), *_base_constraints(),
    )
    op.create_table(
        "report_schedules", *_base_columns(),
        sa.Column("owner_membership_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("metric_key", sa.String(80), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("export_format", sa.String(8), nullable=False),
        sa.Column("frequency", sa.String(16), nullable=False),
        sa.Column("recipient_email", sa.String(320), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_delivered_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("export_format IN ('csv')", name="ck_report_schedules_format"),
        sa.CheckConstraint("frequency IN ('daily', 'weekly', 'monthly')", name="ck_report_schedules_frequency"),
        sa.UniqueConstraint("tenant_id", "owner_membership_id", "name"),
        membership_fk("owner_membership_id"), *_base_constraints(),
    )
    for table_name in TABLES:
        _secure_table(table_name)


def downgrade() -> None:
    """Remove reporting persistence tables."""

    for table_name in reversed(TABLES):
        op.drop_table(table_name)