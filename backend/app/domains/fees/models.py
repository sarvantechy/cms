"""SQLAlchemy models for tenant-scoped fees, invoices, payments, and reversals."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

TENANT_ID_REFERENCE = "tenants.id"


class FeeHead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define one fee category used by fee plans and invoice lines."""

    __tablename__ = "fee_heads"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "code"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FeePlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define one fee plan for a program and academic year combination."""

    __tablename__ = "fee_plans"
    __table_args__ = (
        CheckConstraint(
            "state IN ('draft', 'published', 'archived')",
            name="ck_fee_plans_state",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_from IS NULL OR effective_from <= effective_to",
            name="ck_fee_plans_effective_range",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "code"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    program_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    academic_year_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class FeePlanLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one head-level amount component for a specific fee plan."""

    __tablename__ = "fee_plan_lines"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_fee_plan_lines_amount_non_negative"),
        CheckConstraint("due_in_days IS NULL OR due_in_days >= 0", name="ck_fee_plan_lines_due_days"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "fee_plan_id", "fee_head_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "fee_plan_id"],
            ["fee_plans.tenant_id", "fee_plans.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "fee_head_id"],
            ["fee_heads.tenant_id", "fee_heads.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    fee_plan_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    fee_head_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_in_days: Mapped[int | None] = mapped_column(nullable=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class StudentInvoice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one student invoice bound to enrollment and fee plan context."""

    __tablename__ = "student_invoices"
    __table_args__ = (
        CheckConstraint(
            "state IN ('draft', 'posted', 'partially_paid', 'paid', 'cancelled')",
            name="ck_student_invoices_state",
        ),
        CheckConstraint("due_on IS NULL OR issued_on <= due_on", name="ck_student_invoices_due_window"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "invoice_number"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "enrollment_id"],
            ["student_enrollments.tenant_id", "student_enrollments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "fee_plan_id"],
            ["fee_plans.tenant_id", "fee_plans.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    enrollment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    fee_plan_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    invoice_number: Mapped[str] = mapped_column(String(48), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    issued_on: Mapped[date] = mapped_column(Date, nullable=False)
    due_on: Mapped[date | None] = mapped_column(Date)
    remarks: Mapped[str | None] = mapped_column(Text)


class InvoiceLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one line item for a student invoice."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_invoice_lines_amount_non_negative"),
        CheckConstraint("discount >= 0", name="ck_invoice_lines_discount_non_negative"),
        CheckConstraint("discount <= amount", name="ck_invoice_lines_discount_le_amount"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "invoice_id"],
            ["student_invoices.tenant_id", "student_invoices.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "fee_head_id"],
            ["fee_heads.tenant_id", "fee_heads.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    invoice_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    fee_head_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    description: Mapped[str | None] = mapped_column(String(240))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one posted fee payment transaction with idempotency guarantees."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "method IN ('cash', 'card', 'bank_transfer', 'upi', 'cheque', 'other')",
            name="ck_payments_method",
        ),
        CheckConstraint(
            "state IN ('posted', 'reversed')",
            name="ck_payments_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "reference_number"),
        UniqueConstraint("tenant_id", "idempotency_key"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "cashier_session_id"],
            ["cashier_sessions.tenant_id", "cashier_sessions.id"],
            name="fk_payments_cashier_session",
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    source_payment_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    cashier_session_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    reference_number: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="posted")
    paid_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)


class PaymentAllocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store invoice allocation rows for one payment transaction."""

    __tablename__ = "payment_allocations"
    __table_args__ = (
        CheckConstraint("amount <> 0", name="ck_payment_allocations_amount_non_zero"),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "payment_id", "invoice_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "invoice_id"],
            ["student_invoices.tenant_id", "student_invoices.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    payment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    invoice_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)


class Receipt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one receipt document issued for a payment."""

    __tablename__ = "receipts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "receipt_number"),
        UniqueConstraint("tenant_id", "payment_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "issued_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    payment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    receipt_number: Mapped[str] = mapped_column(String(48), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issued_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))


class FinancialReversal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track immutable payment reversal metadata and compensating transaction links."""

    __tablename__ = "financial_reversals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "source_payment_id"),
        UniqueConstraint("tenant_id", "reversal_payment_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "source_payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reversal_payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reversed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    source_payment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    reversal_payment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reversed_by_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    reversed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FeeConcession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one separately reviewed concession against an invoice line."""

    __tablename__ = "fee_concessions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_fee_concessions_amount_positive"),
        CheckConstraint(
            "state IN ('requested', 'approved', 'rejected')",
            name="ck_fee_concessions_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "invoice_line_id"],
            ["invoice_lines.tenant_id", "invoice_lines.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "requested_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reviewed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    invoice_line_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="requested")
    requested_by_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    reviewed_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FeeRefund(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one partial or full refund request and its compensating payment link."""

    __tablename__ = "fee_refunds"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_fee_refunds_amount_positive"),
        CheckConstraint(
            "state IN ('requested', 'approved', 'rejected')",
            name="ck_fee_refunds_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "refund_payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "requested_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reviewed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    payment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    refund_payment_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="requested")
    requested_by_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    reviewed_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CashierSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track one cashier opening and source-derived closing reconciliation."""

    __tablename__ = "cashier_sessions"
    __table_args__ = (
        CheckConstraint("opening_amount >= 0", name="ck_cashier_sessions_opening_non_negative"),
        CheckConstraint("state IN ('open', 'closed')", name="ck_cashier_sessions_state"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "cashier_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    cashier_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opening_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    expected_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    declared_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    variance_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="open")


class GatewayReconciliation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one provider-independent gateway settlement comparison."""

    __tablename__ = "gateway_reconciliations"
    __table_args__ = (
        CheckConstraint("settled_amount >= 0", name="ck_gateway_reconciliations_amount_non_negative"),
        CheckConstraint(
            "state IN ('matched', 'mismatch', 'unmatched')",
            name="ck_gateway_reconciliations_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "provider", "external_reference"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "payment_id"],
            ["payments.tenant_id", "payments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reconciled_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    payment_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    external_reference: Mapped[str] = mapped_column(String(160), nullable=False)
    settled_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    details: Mapped[str | None] = mapped_column(Text)
    reconciled_by_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    reconciled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
