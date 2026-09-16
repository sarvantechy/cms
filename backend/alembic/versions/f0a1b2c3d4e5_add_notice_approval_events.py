"""Add immutable notice approval events.

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f0a1b2c3d4e5"
down_revision: str | None = "e9f0a1b2c3d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create immutable notice approval history."""

    op.create_table(
        "notice_approval_events",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("notice_id", sa.Uuid(), nullable=False), sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(16), nullable=False), sa.Column("comment", sa.Text()),
        sa.CheckConstraint("action IN ('submitted', 'approved', 'rejected')", name="ck_notice_approval_events_action"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "notice_id"], ["notices.tenant_id", "notices.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "membership_id"], ["tenant_memberships.tenant_id", "tenant_memberships.id"], ondelete="RESTRICT"),
    )
    op.execute(sa.text("ALTER TABLE notice_approval_events ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE notice_approval_events FORCE ROW LEVEL SECURITY"))
    op.execute(sa.text("CREATE POLICY notice_approval_events_tenant_isolation ON notice_approval_events USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"))
    op.execute(sa.text("GRANT SELECT, INSERT ON notice_approval_events TO cms_runtime"))


def downgrade() -> None:
    """Remove immutable notice approval history."""

    op.drop_table("notice_approval_events")