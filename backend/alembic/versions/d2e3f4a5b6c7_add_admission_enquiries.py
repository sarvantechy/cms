"""Add tenant admissions enquiry lifecycle.

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d2e3f4a5b6c7"
down_revision: str | None = "c1d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create forced-RLS enquiry storage and restricted runtime grants."""

    op.create_table(
        "admission_enquiries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=True),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("mobile_number", sa.String(length=24), nullable=True),
        sa.Column("source", sa.String(length=80), server_default="direct", nullable=False),
        sa.Column("state", sa.String(length=16), server_default="new", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("next_follow_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("email IS NOT NULL OR mobile_number IS NOT NULL", name="ck_admission_enquiries_contact_present"),
        sa.CheckConstraint("state IN ('new', 'contacted', 'qualified', 'converted', 'closed')", name="ck_admission_enquiries_state"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["admission_campaigns.tenant_id", "admission_campaigns.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )
    op.execute("ALTER TABLE admission_enquiries ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE admission_enquiries FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON admission_enquiries
        AS PERMISSIVE FOR ALL TO PUBLIC
        USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_runtime') THEN
                GRANT SELECT, INSERT, UPDATE ON admission_enquiries TO cms_runtime;
            END IF;
        END $$
        """
    )


def downgrade() -> None:
    """Drop tenant admissions enquiry storage."""

    op.drop_table("admission_enquiries")