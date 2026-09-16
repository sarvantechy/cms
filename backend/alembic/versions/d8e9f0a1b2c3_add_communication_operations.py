"""Add communication templates, preferences, acknowledgements, and delivery attempts.

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d8e9f0a1b2c3"
down_revision: str | None = "c7d8e9f0a1b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_TABLES = (
    "message_templates",
    "communication_preferences",
    "notice_acknowledgements",
    "delivery_attempts",
)


def _common() -> list[sa.Column]:
    """Return common tenant-owned table columns."""

    return [sa.Column("id", sa.Uuid(), nullable=False), sa.Column("tenant_id", sa.Uuid(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)]


def _constraints() -> list[sa.Constraint]:
    """Return shared tenant identity constraints."""

    return [sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("tenant_id", "id"), sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT")]


def _fk(column: str, table: str) -> sa.ForeignKeyConstraint:
    """Build one composite tenant foreign key."""

    return sa.ForeignKeyConstraint(["tenant_id", column], [f"{table}.tenant_id", f"{table}.id"], ondelete="RESTRICT")


def _rls(table: str) -> None:
    """Enable forced tenant RLS and runtime grants."""

    op.execute(sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'CREATE POLICY "{table}_tenant_isolation" ON "{table}" USING (tenant_id = current_setting(\'app.tenant_id\', true)::uuid) WITH CHECK (tenant_id = current_setting(\'app.tenant_id\', true)::uuid)'))
    op.execute(sa.text(f'GRANT SELECT, INSERT, UPDATE, DELETE ON "{table}" TO cms_runtime'))


def upgrade() -> None:
    """Create provider-independent communication workflow persistence."""

    op.add_column("notices", sa.Column("template_id", sa.Uuid()))
    op.add_column("notices", sa.Column("requires_acknowledgement", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("notices", sa.Column("approved_by_membership_id", sa.Uuid()))
    op.add_column("notices", sa.Column("approved_at", sa.DateTime(timezone=True)))
    op.create_table("message_templates", *_common(), sa.Column("code", sa.String(48), nullable=False), sa.Column("title_template", sa.String(240), nullable=False), sa.Column("body_template", sa.Text(), nullable=False), sa.Column("channel", sa.String(16), nullable=False, server_default="in_app"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.CheckConstraint("channel IN ('in_app', 'email', 'sms')", name="ck_message_templates_channel"), sa.UniqueConstraint("tenant_id", "code"), *_constraints())
    op.create_foreign_key("fk_notices_template", "notices", "message_templates", ["tenant_id", "template_id"], ["tenant_id", "id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_notices_approver", "notices", "tenant_memberships", ["tenant_id", "approved_by_membership_id"], ["tenant_id", "id"], ondelete="RESTRICT")
    op.create_table("communication_preferences", *_common(), sa.Column("membership_id", sa.Uuid(), nullable=False), sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("sms_enabled", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default=sa.true()), sa.UniqueConstraint("tenant_id", "membership_id"), _fk("membership_id", "tenant_memberships"), *_constraints())
    op.create_table("notice_acknowledgements", *_common(), sa.Column("notice_id", sa.Uuid(), nullable=False), sa.Column("membership_id", sa.Uuid(), nullable=False), sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("tenant_id", "notice_id", "membership_id"), _fk("notice_id", "notices"), _fk("membership_id", "tenant_memberships"), *_constraints())
    op.create_table("delivery_attempts", *_common(), sa.Column("delivery_id", sa.Uuid(), nullable=False), sa.Column("channel", sa.String(16), nullable=False), sa.Column("attempt_number", sa.Integer(), nullable=False), sa.Column("state", sa.String(16), nullable=False, server_default="pending"), sa.Column("provider_reference", sa.String(160)), sa.Column("error_detail", sa.Text()), sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False), sa.CheckConstraint("channel IN ('in_app', 'email', 'sms')", name="ck_delivery_attempts_channel"), sa.CheckConstraint("state IN ('pending', 'sent', 'failed')", name="ck_delivery_attempts_state"), sa.CheckConstraint("attempt_number > 0", name="ck_delivery_attempts_number_positive"), sa.UniqueConstraint("tenant_id", "delivery_id", "channel", "attempt_number"), _fk("delivery_id", "notice_deliveries"), *_constraints())
    for table in TENANT_TABLES:
        _rls(table)


def downgrade() -> None:
    """Remove communication workflow persistence."""

    for table in reversed(TENANT_TABLES):
        op.drop_table(table)
    op.drop_constraint("fk_notices_approver", "notices", type_="foreignkey")
    op.drop_constraint("fk_notices_template", "notices", type_="foreignkey")
    op.drop_column("notices", "approved_at")
    op.drop_column("notices", "approved_by_membership_id")
    op.drop_column("notices", "requires_acknowledgement")
    op.drop_column("notices", "template_id")