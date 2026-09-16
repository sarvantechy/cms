"""add fees payments

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-29 23:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
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
    """Create fees and payments tables with tenant-safe constraints and forced RLS."""

    op.create_table(
        "fee_heads",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "code"),
    )

    op.create_table(
        "fee_plans",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=48), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("state IN ('draft', 'published', 'archived')", name="ck_fee_plans_state"),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_from IS NULL OR effective_from <= effective_to",
            name="ck_fee_plans_effective_range",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "code"),
    )

    op.create_table(
        "fee_plan_lines",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("fee_plan_id", sa.Uuid(), nullable=False),
        sa.Column("fee_head_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("due_in_days", sa.Integer(), nullable=True),
        sa.Column("is_optional", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("amount >= 0", name="ck_fee_plan_lines_amount_non_negative"),
        sa.CheckConstraint("due_in_days IS NULL OR due_in_days >= 0", name="ck_fee_plan_lines_due_days"),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "fee_plan_id"],
            ["fee_plans.tenant_id", "fee_plans.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "fee_head_id"],
            ["fee_heads.tenant_id", "fee_heads.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "fee_plan_id", "fee_head_id"),
    )

    op.create_table(
        "student_invoices",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("enrollment_id", sa.Uuid(), nullable=False),
        sa.Column("fee_plan_id", sa.Uuid(), nullable=True),
        sa.Column("invoice_number", sa.String(length=48), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "state IN ('draft', 'posted', 'partially_paid', 'paid', 'cancelled')",
            name="ck_student_invoices_state",
        ),
        sa.CheckConstraint("due_on IS NULL OR issued_on <= due_on", name="ck_student_invoices_due_window"),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "enrollment_id"],
            ["student_enrollments.tenant_id", "student_enrollments.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "fee_plan_id"],
            ["fee_plans.tenant_id", "fee_plans.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "invoice_number"),
    )

    op.create_table(
        "invoice_lines",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("fee_head_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.String(length=240), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("discount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("amount >= 0", name="ck_invoice_lines_amount_non_negative"),
        sa.CheckConstraint("discount >= 0", name="ck_invoice_lines_discount_non_negative"),
        sa.CheckConstraint("discount <= amount", name="ck_invoice_lines_discount_le_amount"),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "invoice_id"],
            ["student_invoices.tenant_id", "student_invoices.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "fee_head_id"],
            ["fee_heads.tenant_id", "fee_heads.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "payments",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("source_payment_id", sa.Uuid(), nullable=True),
        sa.Column("reference_number", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=120), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("paid_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "method IN ('cash', 'card', 'bank_transfer', 'upi', 'cheque', 'other')",
            name="ck_payments_method",
        ),
        sa.CheckConstraint("state IN ('posted', 'reversed')", name="ck_payments_state"),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "reference_number"),
        sa.UniqueConstraint("tenant_id", "idempotency_key"),
    )

    op.create_table(
        "payment_allocations",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=False),
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("amount <> 0", name="ck_payment_allocations_amount_non_zero"),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "invoice_id"],
            ["student_invoices.tenant_id", "student_invoices.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "payment_id", "invoice_id"),
    )

    op.create_table(
        "receipts",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=False),
        sa.Column("receipt_number", sa.String(length=48), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issued_by_membership_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "issued_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "receipt_number"),
        sa.UniqueConstraint("tenant_id", "payment_id"),
    )

    op.create_table(
        "financial_reversals",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("source_payment_id", sa.Uuid(), nullable=False),
        sa.Column("reversal_payment_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("reversed_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reversal_payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reversed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "source_payment_id"),
        sa.UniqueConstraint("tenant_id", "reversal_payment_id"),
    )

    tenant_tables = [
        "fee_heads",
        "fee_plans",
        "fee_plan_lines",
        "student_invoices",
        "invoice_lines",
        "payments",
        "payment_allocations",
        "receipts",
        "financial_reversals",
    ]
    _apply_tenant_rls(tenant_tables)

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_runtime') THEN
                GRANT SELECT, INSERT, UPDATE ON
                    fee_heads,
                    fee_plans,
                    fee_plan_lines,
                    student_invoices,
                    invoice_lines,
                    payments,
                    payment_allocations,
                    receipts,
                    financial_reversals
                TO cms_runtime;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    """Drop fees and payment tables created by this revision."""

    op.drop_table("financial_reversals")
    op.drop_table("receipts")
    op.drop_table("payment_allocations")
    op.drop_table("payments")
    op.drop_table("invoice_lines")
    op.drop_table("student_invoices")
    op.drop_table("fee_plan_lines")
    op.drop_table("fee_plans")
    op.drop_table("fee_heads")
