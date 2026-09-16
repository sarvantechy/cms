"""Pydantic schemas for fees, invoices, payments, reversals, and ledger views."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

MONEY_MAX_DIGITS = 12
MONEY_DECIMAL_PLACES = 2
PAYMENT_METHOD_PATTERN = "^(cash|card|bank_transfer|upi|cheque|other)$"
PAYMENT_STATE_PATTERN = "^(posted|reversed)$"
INVOICE_STATE_PATTERN = "^(draft|posted|partially_paid|paid|cancelled)$"
FEE_PLAN_STATE_PATTERN = "^(draft|published|archived)$"


class FeeHeadCreate(BaseModel):
    """Payload for creating one fee head."""

    code: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(None, max_length=2000)
    is_active: bool = True


class FeeHeadSummary(BaseModel):
    """Response shape for one fee head."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    title: str
    description: str | None
    is_active: bool


class FeePlanLineCreate(BaseModel):
    """Payload for creating one fee plan line."""

    fee_head_id: UUID
    amount: Decimal = Field(ge=0, max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    due_in_days: int | None = Field(None, ge=0)
    is_optional: bool = False


class FeePlanLineSummary(BaseModel):
    """Response shape for one fee plan line."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    fee_plan_id: UUID
    fee_head_id: UUID
    amount: Decimal
    due_in_days: int | None
    is_optional: bool


class FeePlanCreate(BaseModel):
    """Payload for creating one fee plan with lines."""

    program_id: UUID
    academic_year_id: UUID
    code: str = Field(min_length=1, max_length=48)
    title: str = Field(min_length=1, max_length=200)
    state: str = Field(default="draft", pattern=FEE_PLAN_STATE_PATTERN)
    effective_from: date | None = None
    effective_to: date | None = None
    lines: list[FeePlanLineCreate] = Field(default_factory=list, min_length=1)

    @model_validator(mode="after")
    def validate_effective_dates(self) -> "FeePlanCreate":
        """Require effective_to to be on or after effective_from when both are provided."""

        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            msg = "effective_to must be on or after effective_from"
            raise ValueError(msg)
        return self


class FeePlanSummary(BaseModel):
    """Response shape for one fee plan including optional lines."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    academic_year_id: UUID
    code: str
    title: str
    state: str
    effective_from: date | None
    effective_to: date | None
    lines: list[FeePlanLineSummary] = Field(default_factory=list)


class InvoiceLineCreate(BaseModel):
    """Payload for creating one invoice line."""

    fee_head_id: UUID
    description: str | None = Field(None, max_length=240)
    amount: Decimal = Field(ge=0, max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    discount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
    )

    @model_validator(mode="after")
    def validate_discount(self) -> "InvoiceLineCreate":
        """Require line discount to be less than or equal to line amount."""

        if self.discount > self.amount:
            msg = "discount must be less than or equal to amount"
            raise ValueError(msg)
        return self


class InvoiceLineSummary(BaseModel):
    """Response shape for one invoice line."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    invoice_id: UUID
    fee_head_id: UUID
    description: str | None
    amount: Decimal
    discount: Decimal


class StudentInvoiceCreate(BaseModel):
    """Payload for creating one student invoice."""

    student_id: UUID
    enrollment_id: UUID
    fee_plan_id: UUID | None = None
    invoice_number: str | None = Field(None, min_length=1, max_length=48)
    state: str = Field(default="posted", pattern=INVOICE_STATE_PATTERN)
    issued_on: date
    due_on: date | None = None
    remarks: str | None = Field(None, max_length=2000)
    lines: list[InvoiceLineCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_invoice_payload(self) -> "StudentInvoiceCreate":
        """Require due date ordering and a source for line items."""

        if self.due_on and self.due_on < self.issued_on:
            msg = "due_on must be on or after issued_on"
            raise ValueError(msg)
        if self.fee_plan_id is None and len(self.lines) == 0:
            msg = "Either fee_plan_id or lines must be provided"
            raise ValueError(msg)
        return self


class StudentInvoiceSummary(BaseModel):
    """Response shape for one student invoice with totals and line items."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    enrollment_id: UUID
    fee_plan_id: UUID | None
    invoice_number: str
    state: str
    issued_on: date
    due_on: date | None
    remarks: str | None
    total_amount: Decimal
    allocated_amount: Decimal
    outstanding_amount: Decimal
    lines: list[InvoiceLineSummary] = Field(default_factory=list)


class PaymentAllocationCreate(BaseModel):
    """Payload for creating one payment allocation."""

    invoice_id: UUID
    amount: Decimal = Field(gt=0, max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)


class PaymentAllocationSummary(BaseModel):
    """Response shape for one payment allocation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    payment_id: UUID
    invoice_id: UUID
    amount: Decimal


class PaymentCreate(BaseModel):
    """Payload for posting one payment with invoice allocations."""

    student_id: UUID
    cashier_session_id: UUID | None = None
    reference_number: str = Field(min_length=1, max_length=64)
    idempotency_key: str = Field(min_length=8, max_length=120)
    method: str = Field(pattern=PAYMENT_METHOD_PATTERN)
    paid_on: datetime | None = None
    note: str | None = Field(None, max_length=2000)
    allocations: list[PaymentAllocationCreate] = Field(min_length=1)


class PaymentSummary(BaseModel):
    """Response shape for one payment with allocation details."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    source_payment_id: UUID | None
    cashier_session_id: UUID | None
    reference_number: str
    idempotency_key: str
    method: str
    state: str = Field(pattern=PAYMENT_STATE_PATTERN)
    paid_on: datetime
    note: str | None
    allocations: list[PaymentAllocationSummary] = Field(default_factory=list)


class PaymentPostResponse(BaseModel):
    """Response shape for idempotent payment posting requests."""

    payment: PaymentSummary
    idempotent_replay: bool


class ReceiptSummary(BaseModel):
    """Response shape for one payment receipt."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    payment_id: UUID
    receipt_number: str
    issued_at: datetime
    issued_by_membership_id: UUID | None


class FinancialReversalCreate(BaseModel):
    """Payload for reversing one payment."""

    reason: str = Field(min_length=3, max_length=2000)


class FinancialReversalSummary(BaseModel):
    """Response shape for one payment reversal linkage record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    source_payment_id: UUID
    reversal_payment_id: UUID
    reason: str
    reversed_by_membership_id: UUID
    reversed_at: datetime


class FeeConcessionCreate(BaseModel):
    """Payload for requesting a concession against one invoice line."""

    invoice_line_id: UUID
    amount: Decimal = Field(gt=0, max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    reason: str = Field(min_length=3, max_length=2000)


class FeeConcessionReview(BaseModel):
    """Payload for approving or rejecting one concession request."""

    state: str = Field(pattern="^(approved|rejected)$")


class FeeConcessionSummary(BaseModel):
    """Response shape for one auditable concession request."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    invoice_line_id: UUID
    amount: Decimal
    reason: str
    state: str
    requested_by_membership_id: UUID
    reviewed_by_membership_id: UUID | None
    reviewed_at: datetime | None


class FeeRefundCreate(BaseModel):
    """Payload for requesting a partial or full payment refund."""

    payment_id: UUID
    amount: Decimal = Field(gt=0, max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    reason: str = Field(min_length=3, max_length=2000)


class FeeRefundReview(BaseModel):
    """Payload for approving or rejecting one refund request."""

    state: str = Field(pattern="^(approved|rejected)$")


class FeeRefundSummary(BaseModel):
    """Response shape for one refund request and compensating payment link."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    payment_id: UUID
    refund_payment_id: UUID | None
    amount: Decimal
    reason: str
    state: str
    requested_by_membership_id: UUID
    reviewed_by_membership_id: UUID | None
    reviewed_at: datetime | None


class CashierSessionOpen(BaseModel):
    """Payload for opening one cashier collection session."""

    opening_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
    )


class CashierSessionClose(BaseModel):
    """Payload for closing one cashier session with a declared amount."""

    declared_amount: Decimal = Field(
        ge=0,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
    )


class CashierSessionSummary(BaseModel):
    """Response shape for one cashier opening and closing reconciliation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    cashier_membership_id: UUID
    opened_at: datetime
    closed_at: datetime | None
    opening_amount: Decimal
    expected_amount: Decimal | None
    declared_amount: Decimal | None
    variance_amount: Decimal | None
    state: str


class GatewayReconciliationCreate(BaseModel):
    """Payload for reconciling one provider settlement reference."""

    payment_id: UUID | None = None
    provider: str = Field(min_length=1, max_length=64)
    external_reference: str = Field(min_length=1, max_length=160)
    settled_amount: Decimal = Field(
        ge=0,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
    )
    details: str | None = Field(None, max_length=4000)


class GatewayReconciliationSummary(BaseModel):
    """Response shape for a provider-independent settlement comparison."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    payment_id: UUID | None
    provider: str
    external_reference: str
    settled_amount: Decimal
    state: str
    details: str | None
    reconciled_by_membership_id: UUID
    reconciled_at: datetime


class StudentLedgerEntry(BaseModel):
    """One derived student ledger movement from invoices or payment allocations."""

    entry_date: datetime
    entry_type: str
    reference_id: UUID
    reference_number: str
    amount: Decimal


class StudentLedgerResponse(BaseModel):
    """Derived ledger and running balance summary for one student."""

    student_id: UUID
    invoiced_total: Decimal
    paid_total: Decimal
    balance: Decimal
    items: list[StudentLedgerEntry]
    total: int = Field(ge=0)


class PaginatedFeeHeads(BaseModel):
    """Paginated wrapper for fee heads listing."""

    items: list[FeeHeadSummary]
    total: int = Field(ge=0)


class PaginatedFeePlans(BaseModel):
    """Paginated wrapper for fee plans listing."""

    items: list[FeePlanSummary]
    total: int = Field(ge=0)


class PaginatedStudentInvoices(BaseModel):
    """Paginated wrapper for student invoice listing."""

    items: list[StudentInvoiceSummary]
    total: int = Field(ge=0)


class PaginatedPayments(BaseModel):
    """Paginated wrapper for payments listing."""

    items: list[PaymentSummary]
    total: int = Field(ge=0)


class PaginatedFeeConcessions(BaseModel):
    """Paginated wrapper for concession requests."""

    items: list[FeeConcessionSummary]
    total: int = Field(ge=0)


class PaginatedFeeRefunds(BaseModel):
    """Paginated wrapper for refund requests."""

    items: list[FeeRefundSummary]
    total: int = Field(ge=0)


class PaginatedCashierSessions(BaseModel):
    """Paginated wrapper for cashier collection sessions."""

    items: list[CashierSessionSummary]
    total: int = Field(ge=0)


class PaginatedGatewayReconciliations(BaseModel):
    """Paginated wrapper for gateway settlement comparisons."""

    items: list[GatewayReconciliationSummary]
    total: int = Field(ge=0)


def default_payment_time() -> datetime:
    """Return a timezone-aware default timestamp for payment posting."""

    return datetime.now(UTC)
