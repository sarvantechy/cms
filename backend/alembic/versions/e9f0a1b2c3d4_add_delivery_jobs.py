"""Add notice approval states and durable channel delivery jobs.

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e9f0a1b2c3d4"
down_revision: str | None = "d8e9f0a1b2c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create provider delivery jobs and extend notice approval states."""

    op.drop_constraint("ck_notices_state", "notices", type_="check")
    op.create_check_constraint("ck_notices_state", "notices", "state IN ('draft', 'pending_approval', 'approved', 'scheduled', 'published', 'archived')")
    op.create_table(
        "communication_delivery_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("delivery_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.CheckConstraint("channel IN ('in_app', 'email', 'sms')", name="ck_communication_delivery_jobs_channel"),
        sa.CheckConstraint("state IN ('pending', 'processing', 'sent', 'failed')", name="ck_communication_delivery_jobs_state"),
        sa.CheckConstraint("retry_count >= 0", name="ck_communication_delivery_jobs_retry_non_negative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "delivery_id", "channel"),
        sa.UniqueConstraint("tenant_id", "idempotency_key"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "delivery_id"], ["notice_deliveries.tenant_id", "notice_deliveries.id"], ondelete="RESTRICT"),
    )
    op.add_column("delivery_attempts", sa.Column("job_id", sa.Uuid()))
    op.create_foreign_key("fk_delivery_attempts_job", "delivery_attempts", "communication_delivery_jobs", ["tenant_id", "job_id"], ["tenant_id", "id"], ondelete="RESTRICT")
    op.execute(sa.text("ALTER TABLE communication_delivery_jobs ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE communication_delivery_jobs FORCE ROW LEVEL SECURITY"))
    op.execute(sa.text("CREATE POLICY communication_delivery_jobs_tenant_isolation ON communication_delivery_jobs USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"))
    op.execute(sa.text("GRANT SELECT, INSERT, UPDATE, DELETE ON communication_delivery_jobs TO cms_runtime"))


def downgrade() -> None:
    """Remove delivery jobs and restore the original notice states."""

    op.drop_constraint("fk_delivery_attempts_job", "delivery_attempts", type_="foreignkey")
    op.drop_column("delivery_attempts", "job_id")
    op.drop_table("communication_delivery_jobs")
    op.drop_constraint("ck_notices_state", "notices", type_="check")
    op.create_check_constraint("ck_notices_state", "notices", "state IN ('draft', 'scheduled', 'published', 'archived')")