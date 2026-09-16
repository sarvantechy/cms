"""Add concession, refund, cashier, and gateway reconciliation operations.

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a5b6c7d8e9f0"
down_revision: str | None = "f4a5b6c7d8e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_TABLES = (
    "fee_concessions",
    "fee_refunds",
    "cashier_sessions",
    "gateway_reconciliations",
)


def _tenant_columns() -> list[sa.Column]:
    """Return common columns for a tenant-owned operational table."""

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
    """Create the missing auditable finance workflow records."""

    op.create_table(
        "cashier_sessions",
        *_tenant_columns(),
        sa.Column("cashier_membership_id", sa.Uuid(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("opening_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("expected_amount", sa.Numeric(12, 2)),
        sa.Column("declared_amount", sa.Numeric(12, 2)),
        sa.Column("variance_amount", sa.Numeric(12, 2)),
        sa.Column("state", sa.String(16), nullable=False, server_default="open"),
        sa.CheckConstraint("opening_amount >= 0", name="ck_cashier_sessions_opening_non_negative"),
        sa.CheckConstraint("state IN ('open', 'closed')", name="ck_cashier_sessions_state"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "cashier_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        *_tenant_constraints(),
    )
    op.add_column("payments", sa.Column("cashier_session_id", sa.Uuid()))
    op.create_foreign_key(
        "fk_payments_cashier_session",
        "payments",
        "cashier_sessions",
        ["tenant_id", "cashier_session_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_table(
        "fee_concessions",
        *_tenant_columns(),
        sa.Column("invoice_line_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="requested"),
        sa.Column("requested_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("reviewed_by_membership_id", sa.Uuid()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("amount > 0", name="ck_fee_concessions_amount_positive"),
        sa.CheckConstraint(
            "state IN ('requested', 'approved', 'rejected')",
            name="ck_fee_concessions_state",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "invoice_line_id"],
            ["invoice_lines.tenant_id", "invoice_lines.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "requested_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reviewed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        *_tenant_constraints(),
    )
    op.create_table(
        "fee_refunds",
        *_tenant_columns(),
        sa.Column("payment_id", sa.Uuid(), nullable=False),
        sa.Column("refund_payment_id", sa.Uuid()),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="requested"),
        sa.Column("requested_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("reviewed_by_membership_id", sa.Uuid()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("amount > 0", name="ck_fee_refunds_amount_positive"),
        sa.CheckConstraint("state IN ('requested', 'approved', 'rejected')", name="ck_fee_refunds_state"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "refund_payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "requested_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reviewed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        *_tenant_constraints(),
    )
    op.create_table(
        "gateway_reconciliations",
        *_tenant_columns(),
        sa.Column("payment_id", sa.Uuid()),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("external_reference", sa.String(160), nullable=False),
        sa.Column("settled_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("details", sa.Text()),
        sa.Column("reconciled_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("settled_amount >= 0", name="ck_gateway_reconciliations_amount_non_negative"),
        sa.CheckConstraint(
            "state IN ('matched', 'mismatch', 'unmatched')",
            name="ck_gateway_reconciliations_state",
        ),
        sa.UniqueConstraint("tenant_id", "provider", "external_reference"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reconciled_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        *_tenant_constraints(),
    )
    for table_name in TENANT_TABLES:
        _enable_forced_rls(table_name)


def downgrade() -> None:
    """Remove the finance workflow records and cashier payment linkage."""

    for table_name in reversed(TENANT_TABLES):
        op.drop_table(table_name)
    op.drop_constraint("fk_payments_cashier_session", "payments", type_="foreignkey")
    op.drop_column("payments", "cashier_session_id")
