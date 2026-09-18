"""Business logic for tenant-safe fee plans, invoicing, payments, and reversals."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.domains.academics.models import AcademicYear, CollegeSetting, Program
from app.domains.audit.models import AuditEvent
from app.domains.fees.models import (
    CashierSession,
    FeeConcession,
    FeeHead,
    FeePlan,
    FeePlanLine,
    FeeRefund,
    FinancialReversal,
    GatewayReconciliation,
    InvoiceLine,
    Payment,
    PaymentAllocation,
    Receipt,
    StudentInvoice,
)
from app.domains.fees.schemas import (
    CashierSessionClose,
    CashierSessionOpen,
    FeeConcessionCreate,
    FeeConcessionReview,
    FeeHeadCreate,
    FeePlanCreate,
    FeeRefundCreate,
    FeeRefundReview,
    FinancialReversalCreate,
    GatewayReconciliationCreate,
    InvoiceLineCreate,
    PaymentCreate,
    ReceiptDocument,
    ReceiptDocumentAllocation,
    StudentInvoiceCreate,
    StudentLedgerEntry,
)
from app.domains.students.models import Person, Student, StudentEnrollment
from app.domains.tenancy.models import Tenant
from app.security_context import ActorContext, resolve_actor_student_ids

ZERO = Decimal("0.00")


class FeesDomainError(Exception):
    """Represent one controlled fees-domain error with stable HTTP translation data."""

    def __init__(self, detail: str, status_code: int) -> None:
        """Initialize a deterministic domain error with detail and status code."""

        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class FeesValidationError(FeesDomainError):
    """Represent one fees validation error mapped to HTTP 422."""

    def __init__(self, detail: str) -> None:
        """Initialize a deterministic validation error for request/domain issues."""

        super().__init__(detail=detail, status_code=422)


class FeesConflictError(FeesDomainError):
    """Represent one fees state conflict mapped to HTTP 409."""

    def __init__(self, detail: str) -> None:
        """Initialize a deterministic conflict error for non-idempotent collisions."""

        super().__init__(detail=detail, status_code=409)


class FeesService:
    """Manage tenant-safe fees lifecycle operations and derived ledger computations."""

    def __init__(self, session: Session, actor: ActorContext) -> None:
        """Initialize the service with runtime session and authenticated actor context."""

        self.session = session
        self.actor = actor
        self._set_tenant_context()

    def _set_tenant_context(self) -> None:
        """Set transaction-local tenant context for forced PostgreSQL RLS."""

        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self.actor.tenant_id)},
        )

    def _audit(self, action: str, entity_type: str, entity_id: UUID, details: dict[str, object]) -> None:
        """Persist one tenant-scoped audit event in the active transaction."""

        self.session.add(
            AuditEvent(
                tenant_id=self.actor.tenant_id,
                account_id=self.actor.account_id,
                membership_id=self.actor.membership_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
            )
        )

    def _paginate(self, query, skip: int, limit: int):
        """Return paginated results and total count for a SQLAlchemy selectable."""

        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def _invoice_total(self, invoice_id: UUID) -> Decimal:
        """Return one invoice total computed from source invoice lines."""

        total = self.session.scalar(
            select(func.coalesce(func.sum(InvoiceLine.amount - InvoiceLine.discount), 0)).where(
                InvoiceLine.tenant_id == self.actor.tenant_id,
                InvoiceLine.invoice_id == invoice_id,
            )
        )
        concessions = self.session.scalar(
            select(func.coalesce(func.sum(FeeConcession.amount), 0))
            .join(
                InvoiceLine,
                (InvoiceLine.tenant_id == FeeConcession.tenant_id)
                & (InvoiceLine.id == FeeConcession.invoice_line_id),
            )
            .where(
                FeeConcession.tenant_id == self.actor.tenant_id,
                InvoiceLine.invoice_id == invoice_id,
                FeeConcession.state == "approved",
            )
        )
        return (Decimal(total or 0) - Decimal(concessions or 0)).quantize(Decimal("0.01"))

    def _invoice_allocated(self, invoice_id: UUID) -> Decimal:
        """Return net allocated amount for one invoice from payment allocations."""

        allocated = self.session.scalar(
            select(func.coalesce(func.sum(PaymentAllocation.amount), 0)).where(
                PaymentAllocation.tenant_id == self.actor.tenant_id,
                PaymentAllocation.invoice_id == invoice_id,
            )
        )
        return Decimal(allocated or 0).quantize(Decimal("0.01"))

    def _refresh_invoice_state(self, invoice: StudentInvoice) -> None:
        """Recompute invoice state from line totals and payment allocations."""

        total = self._invoice_total(invoice.id)
        allocated = self._invoice_allocated(invoice.id)
        if total <= ZERO:
            invoice.state = "paid"
            return
        if allocated <= ZERO:
            if invoice.state != "cancelled":
                invoice.state = "posted"
            return
        if allocated >= total:
            invoice.state = "paid"
        else:
            invoice.state = "partially_paid"

    def _generate_invoice_number(self) -> str:
        """Generate one deterministic tenant invoice number."""

        stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        return f"INV-{stamp}-{str(self.actor.membership_id).split('-')[0].upper()}"

    def _generate_receipt_number(self) -> str:
        """Generate one deterministic tenant receipt number."""

        stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        return f"RCT-{stamp}-{str(self.actor.membership_id).split('-')[0].upper()}"

    def _require_student(self, student_id: UUID) -> Student:
        """Return one tenant student or raise a controlled validation error."""

        student = self.session.scalar(
            select(Student).where(Student.tenant_id == self.actor.tenant_id, Student.id == student_id)
        )
        if student is None:
            raise FeesValidationError("Invalid student_id reference")
        return student

    def _require_enrollment(self, enrollment_id: UUID, student_id: UUID) -> StudentEnrollment:
        """Return one student enrollment row bound to the same tenant and student."""

        enrollment = self.session.scalar(
            select(StudentEnrollment).where(
                StudentEnrollment.tenant_id == self.actor.tenant_id,
                StudentEnrollment.id == enrollment_id,
                StudentEnrollment.student_id == student_id,
            )
        )
        if enrollment is None:
            raise FeesValidationError("Invalid enrollment_id reference")
        return enrollment

    def _require_fee_head(self, fee_head_id: UUID) -> FeeHead:
        """Return one fee head or raise a controlled validation error."""

        fee_head = self.session.scalar(
            select(FeeHead).where(FeeHead.tenant_id == self.actor.tenant_id, FeeHead.id == fee_head_id)
        )
        if fee_head is None:
            raise FeesValidationError("Invalid fee_head_id reference")
        return fee_head

    def _require_program_year(self, program_id: UUID, academic_year_id: UUID) -> None:
        """Validate program and academic year references for plan creation."""

        program = self.session.scalar(
            select(Program).where(Program.tenant_id == self.actor.tenant_id, Program.id == program_id)
        )
        if program is None:
            raise FeesValidationError("Invalid program_id reference")
        year = self.session.scalar(
            select(AcademicYear).where(
                AcademicYear.tenant_id == self.actor.tenant_id,
                AcademicYear.id == academic_year_id,
            )
        )
        if year is None:
            raise FeesValidationError("Invalid academic_year_id reference")

    def list_fee_heads(self, skip: int = 0, limit: int = 100) -> tuple[list[FeeHead], int]:
        """List fee heads for the authenticated tenant."""

        query = (
            select(FeeHead)
            .where(FeeHead.tenant_id == self.actor.tenant_id)
            .order_by(FeeHead.code)
        )
        return self._paginate(query, skip, limit)

    def create_fee_head(self, payload: FeeHeadCreate) -> FeeHead:
        """Create one fee head for the current tenant."""

        fee_head = FeeHead(
            tenant_id=self.actor.tenant_id,
            code=payload.code,
            title=payload.title,
            description=payload.description,
            is_active=payload.is_active,
        )
        self.session.add(fee_head)
        self.session.flush()
        self._audit("fees.head.create", "fee_head", fee_head.id, {"code": fee_head.code})
        return fee_head

    def list_fee_plans(self, skip: int = 0, limit: int = 100) -> tuple[list[FeePlan], int]:
        """List fee plans for the authenticated tenant."""

        query = (
            select(FeePlan)
            .where(FeePlan.tenant_id == self.actor.tenant_id)
            .order_by(FeePlan.created_at.desc(), FeePlan.code)
        )
        return self._paginate(query, skip, limit)

    def get_fee_plan(self, fee_plan_id: UUID) -> FeePlan | None:
        """Return one fee plan by ID for the authenticated tenant."""

        return self.session.scalar(
            select(FeePlan).where(FeePlan.tenant_id == self.actor.tenant_id, FeePlan.id == fee_plan_id)
        )

    def list_fee_plan_lines(self, fee_plan_id: UUID) -> list[FeePlanLine]:
        """Return fee plan lines for one tenant-scoped fee plan."""

        return list(
            self.session.scalars(
                select(FeePlanLine)
                .where(
                    FeePlanLine.tenant_id == self.actor.tenant_id,
                    FeePlanLine.fee_plan_id == fee_plan_id,
                )
                .order_by(FeePlanLine.created_at.asc())
            )
        )

    def create_fee_plan(self, payload: FeePlanCreate) -> FeePlan:
        """Create one fee plan and all supplied fee plan lines."""

        self._require_program_year(payload.program_id, payload.academic_year_id)

        plan = FeePlan(
            tenant_id=self.actor.tenant_id,
            program_id=payload.program_id,
            academic_year_id=payload.academic_year_id,
            code=payload.code,
            title=payload.title,
            state=payload.state,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
        )
        self.session.add(plan)
        self.session.flush()

        for line in payload.lines:
            self._require_fee_head(line.fee_head_id)
            self.session.add(
                FeePlanLine(
                    tenant_id=self.actor.tenant_id,
                    fee_plan_id=plan.id,
                    fee_head_id=line.fee_head_id,
                    amount=line.amount,
                    due_in_days=line.due_in_days,
                    is_optional=line.is_optional,
                )
            )

        self.session.flush()
        self._audit(
            "fees.plan.create",
            "fee_plan",
            plan.id,
            {"line_count": len(payload.lines), "code": plan.code},
        )
        return plan

    def _materialize_invoice_lines(
        self,
        invoice: StudentInvoice,
        payload_lines: list[InvoiceLineCreate],
        fee_plan_id: UUID | None,
    ) -> None:
        """Create invoice lines either from payload lines or from fee plan defaults."""

        if payload_lines:
            for line in payload_lines:
                self._require_fee_head(line.fee_head_id)
                self.session.add(
                    InvoiceLine(
                        tenant_id=self.actor.tenant_id,
                        invoice_id=invoice.id,
                        fee_head_id=line.fee_head_id,
                        description=line.description,
                        amount=line.amount,
                        discount=line.discount,
                    )
                )
            return

        if fee_plan_id is None:
            raise FeesValidationError("Either fee_plan_id or lines must be provided")

        plan_lines = list(
            self.session.scalars(
                select(FeePlanLine).where(
                    FeePlanLine.tenant_id == self.actor.tenant_id,
                    FeePlanLine.fee_plan_id == fee_plan_id,
                )
            )
        )
        if len(plan_lines) == 0:
            raise FeesValidationError("Selected fee plan has no fee lines")

        for line in plan_lines:
            self.session.add(
                InvoiceLine(
                    tenant_id=self.actor.tenant_id,
                    invoice_id=invoice.id,
                    fee_head_id=line.fee_head_id,
                    description=None,
                    amount=line.amount,
                    discount=ZERO,
                )
            )

    def list_invoices(
        self,
        skip: int = 0,
        limit: int = 100,
        student_id: UUID | None = None,
    ) -> tuple[list[StudentInvoice], int]:
        """List student invoices for the tenant with optional student filter."""

        query = select(StudentInvoice).where(StudentInvoice.tenant_id == self.actor.tenant_id)
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            query = query.where(StudentInvoice.student_id.in_(student_ids))
        if student_id is not None:
            query = query.where(StudentInvoice.student_id == student_id)
        query = query.order_by(StudentInvoice.created_at.desc(), StudentInvoice.invoice_number)
        return self._paginate(query, skip, limit)

    def get_invoice(self, invoice_id: UUID) -> StudentInvoice | None:
        """Return one student invoice by ID for the authenticated tenant."""

        query = select(StudentInvoice).where(
                StudentInvoice.tenant_id == self.actor.tenant_id,
                StudentInvoice.id == invoice_id,
            )
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            query = query.where(StudentInvoice.student_id.in_(student_ids))
        return self.session.scalar(query)

    def list_invoice_lines(self, invoice_id: UUID) -> list[InvoiceLine]:
        """Return invoice lines for one tenant invoice."""

        return list(
            self.session.scalars(
                select(InvoiceLine)
                .where(InvoiceLine.tenant_id == self.actor.tenant_id, InvoiceLine.invoice_id == invoice_id)
                .order_by(InvoiceLine.created_at.asc())
            )
        )

    def create_invoice(self, payload: StudentInvoiceCreate) -> StudentInvoice:
        """Create one invoice and derived line items from explicit lines or a fee plan."""

        self._require_student(payload.student_id)
        enrollment = self._require_enrollment(payload.enrollment_id, payload.student_id)

        if payload.fee_plan_id is not None:
            fee_plan = self.get_fee_plan(payload.fee_plan_id)
            if fee_plan is None:
                raise FeesValidationError("Invalid fee_plan_id reference")
            if fee_plan.program_id != enrollment.program_id:
                raise FeesValidationError("fee_plan_id program must match enrollment program")
            if fee_plan.academic_year_id != enrollment.academic_year_id:
                raise FeesValidationError("fee_plan_id academic year must match enrollment")

        invoice = StudentInvoice(
            tenant_id=self.actor.tenant_id,
            student_id=payload.student_id,
            enrollment_id=payload.enrollment_id,
            fee_plan_id=payload.fee_plan_id,
            invoice_number=payload.invoice_number or self._generate_invoice_number(),
            state=payload.state,
            issued_on=payload.issued_on,
            due_on=payload.due_on,
            remarks=payload.remarks,
        )
        self.session.add(invoice)
        self.session.flush()

        self._materialize_invoice_lines(invoice, payload.lines, payload.fee_plan_id)
        self._refresh_invoice_state(invoice)
        self.session.flush()
        self._audit(
            "fees.invoice.create",
            "student_invoice",
            invoice.id,
            {"invoice_number": invoice.invoice_number},
        )
        return invoice

    def _payment_for_update(self, payment_id: UUID) -> Payment | None:
        """Load one payment row with write lock for deterministic transitions."""

        return self.session.scalar(
            select(Payment)
            .where(Payment.tenant_id == self.actor.tenant_id, Payment.id == payment_id)
            .with_for_update()
        )

    def _invoice_for_update(self, invoice_id: UUID) -> StudentInvoice | None:
        """Load one invoice row with write lock for payment allocation operations."""

        return self.session.scalar(
            select(StudentInvoice)
            .where(StudentInvoice.tenant_id == self.actor.tenant_id, StudentInvoice.id == invoice_id)
            .with_for_update()
        )

    def list_payments(
        self,
        skip: int = 0,
        limit: int = 100,
        student_id: UUID | None = None,
    ) -> tuple[list[Payment], int]:
        """List posted and reversed payments for the current tenant."""

        query = select(Payment).where(Payment.tenant_id == self.actor.tenant_id)
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            query = query.where(Payment.student_id.in_(student_ids))
        if student_id is not None:
            query = query.where(Payment.student_id == student_id)
        query = query.order_by(Payment.paid_on.desc(), Payment.created_at.desc())
        return self._paginate(query, skip, limit)

    def get_payment(self, payment_id: UUID) -> Payment | None:
        """Return one payment by ID for the authenticated tenant."""

        query = select(Payment).where(
            Payment.tenant_id == self.actor.tenant_id,
            Payment.id == payment_id,
        )
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            query = query.where(Payment.student_id.in_(student_ids))
        return self.session.scalar(query)

    def list_payment_allocations(self, payment_id: UUID) -> list[PaymentAllocation]:
        """Return payment allocation rows for one payment."""

        return list(
            self.session.scalars(
                select(PaymentAllocation)
                .where(
                    PaymentAllocation.tenant_id == self.actor.tenant_id,
                    PaymentAllocation.payment_id == payment_id,
                )
                .order_by(PaymentAllocation.created_at.asc())
            )
        )

    def post_payment(self, payload: PaymentCreate) -> tuple[Payment, bool]:
        """Post one payment atomically with idempotent replay by idempotency key."""

        existing = self.session.scalar(
            select(Payment).where(
                Payment.tenant_id == self.actor.tenant_id,
                Payment.idempotency_key == payload.idempotency_key,
            )
        )
        if existing is not None:
            return existing, True

        self._require_student(payload.student_id)
        if payload.cashier_session_id is not None:
            cashier_session = self.get_cashier_session(payload.cashier_session_id)
            if cashier_session is None:
                raise FeesValidationError("Invalid cashier_session_id reference")
            if cashier_session.state != "open":
                raise FeesConflictError("Cashier session is already closed")
        invoice_ids = [allocation.invoice_id for allocation in payload.allocations]
        if len(set(invoice_ids)) != len(invoice_ids):
            raise FeesValidationError("allocations must contain unique invoice_id values")

        payment = Payment(
            tenant_id=self.actor.tenant_id,
            student_id=payload.student_id,
            source_payment_id=None,
            cashier_session_id=payload.cashier_session_id,
            reference_number=payload.reference_number,
            idempotency_key=payload.idempotency_key,
            method=payload.method,
            state="posted",
            paid_on=payload.paid_on or datetime.now(UTC),
            note=payload.note,
        )
        self.session.add(payment)
        self.session.flush()

        touched_invoice_ids: list[UUID] = []
        for allocation in payload.allocations:
            invoice = self._invoice_for_update(allocation.invoice_id)
            if invoice is None:
                raise FeesValidationError("Invalid invoice_id reference")
            if invoice.student_id != payload.student_id:
                raise FeesValidationError("All allocations must belong to payload student_id")
            if invoice.state == "cancelled":
                raise FeesConflictError("Cannot allocate payment to a cancelled invoice")

            self.session.add(
                PaymentAllocation(
                    tenant_id=self.actor.tenant_id,
                    payment_id=payment.id,
                    invoice_id=allocation.invoice_id,
                    amount=allocation.amount,
                )
            )
            touched_invoice_ids.append(invoice.id)

        self.session.flush()
        for invoice_id in touched_invoice_ids:
            invoice = self._invoice_for_update(invoice_id)
            if invoice is not None:
                self._refresh_invoice_state(invoice)

        self.session.flush()
        self._audit(
            "fees.payment.post",
            "payment",
            payment.id,
            {
                "reference_number": payment.reference_number,
                "allocation_count": len(payload.allocations),
            },
        )
        return payment, False

    def issue_receipt(self, payment_id: UUID) -> Receipt:
        """Issue one receipt for a payment, returning existing receipt on replay."""

        payment = self.get_payment(payment_id)
        if payment is None:
            raise FeesValidationError("Invalid payment_id reference")

        existing = self.session.scalar(
            select(Receipt).where(Receipt.tenant_id == self.actor.tenant_id, Receipt.payment_id == payment_id)
        )
        if existing is not None:
            return existing

        receipt = Receipt(
            tenant_id=self.actor.tenant_id,
            payment_id=payment_id,
            receipt_number=self._generate_receipt_number(),
            issued_at=datetime.now(UTC),
            issued_by_membership_id=self.actor.membership_id,
        )
        self.session.add(receipt)
        self.session.flush()
        self._audit(
            "fees.receipt.issue",
            "receipt",
            receipt.id,
            {"receipt_number": receipt.receipt_number, "payment_id": str(payment_id)},
        )
        return receipt

    def get_receipt_document(self, payment_id: UUID) -> ReceiptDocument | None:
        """Derive one printable receipt from an authorized issued payment and source allocations."""

        payment = self.get_payment(payment_id)
        if payment is None:
            return None
        receipt = self.session.scalar(
            select(Receipt).where(
                Receipt.tenant_id == self.actor.tenant_id,
                Receipt.payment_id == payment.id,
            )
        )
        if receipt is None:
            return None
        student_row = self.session.execute(
            select(Student, Person)
            .join(
                Person,
                (Person.tenant_id == Student.tenant_id)
                & (Person.id == Student.person_id),
            )
            .where(
                Student.tenant_id == self.actor.tenant_id,
                Student.id == payment.student_id,
            )
        ).one()
        allocation_rows = list(
            self.session.execute(
                select(PaymentAllocation, StudentInvoice)
                .join(
                    StudentInvoice,
                    (StudentInvoice.tenant_id == PaymentAllocation.tenant_id)
                    & (StudentInvoice.id == PaymentAllocation.invoice_id),
                )
                .where(
                    PaymentAllocation.tenant_id == self.actor.tenant_id,
                    PaymentAllocation.payment_id == payment.id,
                )
                .order_by(StudentInvoice.invoice_number),
            )
        )
        tenant = self.session.scalar(select(Tenant).where(Tenant.id == self.actor.tenant_id))
        setting = self.session.scalar(
            select(CollegeSetting).where(CollegeSetting.tenant_id == self.actor.tenant_id)
        )
        if tenant is None:
            raise FeesValidationError("Tenant branding is unavailable")
        allocations = [
            ReceiptDocumentAllocation(
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                amount=allocation.amount,
            )
            for allocation, invoice in allocation_rows
        ]
        return ReceiptDocument(
            receipt_id=receipt.id,
            receipt_number=receipt.receipt_number,
            verification_reference=receipt.receipt_number,
            issued_at=receipt.issued_at,
            issued_by_membership_id=receipt.issued_by_membership_id,
            institution_name=setting.institution_name if setting else tenant.display_name,
            institution_short_name=(setting.short_name if setting else None) or tenant.short_name,
            primary_color=tenant.primary_color,
            accent_color=tenant.accent_color,
            student_id=student_row.Student.id,
            student_name=student_row.Person.full_name,
            registration_number=student_row.Student.registration_number,
            payment_id=payment.id,
            payment_reference=payment.reference_number,
            payment_method=payment.method,
            payment_state=payment.state,
            paid_on=payment.paid_on,
            payment_note=payment.note,
            total_amount=sum((item.amount for item in allocations), ZERO),
            allocations=allocations,
        )

    def get_reversal(self, source_payment_id: UUID) -> FinancialReversal | None:
        """Return one reversal row for a source payment when it exists."""

        return self.session.scalar(
            select(FinancialReversal).where(
                FinancialReversal.tenant_id == self.actor.tenant_id,
                FinancialReversal.source_payment_id == source_payment_id,
            )
        )

    def reverse_payment(self, source_payment_id: UUID, payload: FinancialReversalCreate) -> FinancialReversal:
        """Reverse one payment by creating a compensating negative payment transaction."""

        source = self._payment_for_update(source_payment_id)
        if source is None:
            raise FeesValidationError("Invalid source payment reference")
        if source.source_payment_id is not None:
            raise FeesConflictError("Compensating payments cannot be reversed again")
        if source.state == "reversed":
            raise FeesConflictError("Payment is already reversed")
        if self.get_reversal(source_payment_id) is not None:
            raise FeesConflictError("A reversal already exists for this payment")

        source_allocations = self.list_payment_allocations(source_payment_id)
        if len(source_allocations) == 0:
            raise FeesConflictError("Cannot reverse a payment without allocations")

        reversal = Payment(
            tenant_id=self.actor.tenant_id,
            student_id=source.student_id,
            source_payment_id=source.id,
            cashier_session_id=None,
            reference_number=f"REV-{source.reference_number}",
            idempotency_key=f"reversal:{source.id}",
            method=source.method,
            state="posted",
            paid_on=datetime.now(UTC),
            note=payload.reason,
        )
        self.session.add(reversal)
        self.session.flush()

        touched_invoice_ids: list[UUID] = []
        for allocation in source_allocations:
            self.session.add(
                PaymentAllocation(
                    tenant_id=self.actor.tenant_id,
                    payment_id=reversal.id,
                    invoice_id=allocation.invoice_id,
                    amount=-allocation.amount,
                )
            )
            touched_invoice_ids.append(allocation.invoice_id)

        source.state = "reversed"
        reversal_record = FinancialReversal(
            tenant_id=self.actor.tenant_id,
            source_payment_id=source.id,
            reversal_payment_id=reversal.id,
            reason=payload.reason,
            reversed_by_membership_id=self.actor.membership_id,
            reversed_at=datetime.now(UTC),
        )
        self.session.add(reversal_record)
        self.session.flush()

        for invoice_id in touched_invoice_ids:
            invoice = self._invoice_for_update(invoice_id)
            if invoice is not None:
                self._refresh_invoice_state(invoice)

        self.session.flush()
        self._audit(
            "fees.payment.reverse",
            "financial_reversal",
            reversal_record.id,
            {
                "source_payment_id": str(source.id),
                "reversal_payment_id": str(reversal.id),
            },
        )
        return reversal_record

    def list_concessions(self, skip: int = 0, limit: int = 100) -> tuple[list[FeeConcession], int]:
        """List concession requests for the authenticated tenant."""

        query = (
            select(FeeConcession)
            .where(FeeConcession.tenant_id == self.actor.tenant_id)
            .order_by(FeeConcession.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def get_concession(self, concession_id: UUID) -> FeeConcession | None:
        """Return one concession request by tenant-safe identifier."""

        return self.session.scalar(
            select(FeeConcession).where(
                FeeConcession.tenant_id == self.actor.tenant_id,
                FeeConcession.id == concession_id,
            )
        )

    def create_concession(self, payload: FeeConcessionCreate) -> FeeConcession:
        """Request a concession while reserving against the invoice line balance."""

        invoice_line = self.session.scalar(
            select(InvoiceLine).where(
                InvoiceLine.tenant_id == self.actor.tenant_id,
                InvoiceLine.id == payload.invoice_line_id,
            )
        )
        if invoice_line is None:
            raise FeesValidationError("Invalid invoice_line_id reference")
        reserved = self.session.scalar(
            select(func.coalesce(func.sum(FeeConcession.amount), 0)).where(
                FeeConcession.tenant_id == self.actor.tenant_id,
                FeeConcession.invoice_line_id == payload.invoice_line_id,
                FeeConcession.state.in_(("requested", "approved")),
            )
        )
        available = invoice_line.amount - invoice_line.discount - Decimal(reserved or 0)
        if payload.amount > available:
            raise FeesConflictError("Concession exceeds the remaining invoice line amount")
        concession = FeeConcession(
            tenant_id=self.actor.tenant_id,
            invoice_line_id=payload.invoice_line_id,
            amount=payload.amount,
            reason=payload.reason,
            state="requested",
            requested_by_membership_id=self.actor.membership_id,
        )
        self.session.add(concession)
        self.session.flush()
        self._audit(
            "fees.concession.request",
            "fee_concession",
            concession.id,
            {"amount": str(concession.amount), "invoice_line_id": str(concession.invoice_line_id)},
        )
        return concession

    def review_concession(
        self,
        concession_id: UUID,
        payload: FeeConcessionReview,
    ) -> FeeConcession | None:
        """Approve or reject one concession and refresh its invoice state."""

        concession = self.get_concession(concession_id)
        if concession is None:
            return None
        if concession.state != "requested":
            raise FeesConflictError("Concession request is already reviewed")
        concession.state = payload.state
        concession.reviewed_by_membership_id = self.actor.membership_id
        concession.reviewed_at = datetime.now(UTC)
        invoice_id = self.session.scalar(
            select(InvoiceLine.invoice_id).where(
                InvoiceLine.tenant_id == self.actor.tenant_id,
                InvoiceLine.id == concession.invoice_line_id,
            )
        )
        if invoice_id is not None:
            invoice = self._invoice_for_update(invoice_id)
            if invoice is not None:
                self._refresh_invoice_state(invoice)
        self.session.flush()
        self._audit(
            "fees.concession.review",
            "fee_concession",
            concession.id,
            {"state": concession.state, "amount": str(concession.amount)},
        )
        return concession

    def list_refunds(self, skip: int = 0, limit: int = 100) -> tuple[list[FeeRefund], int]:
        """List refund requests for the authenticated tenant."""

        query = (
            select(FeeRefund)
            .where(FeeRefund.tenant_id == self.actor.tenant_id)
            .order_by(FeeRefund.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def get_refund(self, refund_id: UUID) -> FeeRefund | None:
        """Return one refund request by tenant-safe identifier."""

        return self.session.scalar(
            select(FeeRefund).where(
                FeeRefund.tenant_id == self.actor.tenant_id,
                FeeRefund.id == refund_id,
            )
        )

    def create_refund(self, payload: FeeRefundCreate) -> FeeRefund:
        """Request a refund bounded by the payment's unrefunded allocations."""

        payment = self._payment_for_update(payload.payment_id)
        if payment is None:
            raise FeesValidationError("Invalid payment_id reference")
        if payment.source_payment_id is not None or payment.state != "posted":
            raise FeesConflictError("Only posted source payments can be refunded")
        paid_amount = sum((item.amount for item in self.list_payment_allocations(payment.id)), ZERO)
        reserved = self.session.scalar(
            select(func.coalesce(func.sum(FeeRefund.amount), 0)).where(
                FeeRefund.tenant_id == self.actor.tenant_id,
                FeeRefund.payment_id == payment.id,
                FeeRefund.state.in_(("requested", "approved")),
            )
        )
        if payload.amount > paid_amount - Decimal(reserved or 0):
            raise FeesConflictError("Refund exceeds the payment's remaining refundable amount")
        refund = FeeRefund(
            tenant_id=self.actor.tenant_id,
            payment_id=payment.id,
            amount=payload.amount,
            reason=payload.reason,
            state="requested",
            requested_by_membership_id=self.actor.membership_id,
        )
        self.session.add(refund)
        self.session.flush()
        self._audit(
            "fees.refund.request",
            "fee_refund",
            refund.id,
            {"payment_id": str(payment.id), "amount": str(refund.amount)},
        )
        return refund

    def review_refund(self, refund_id: UUID, payload: FeeRefundReview) -> FeeRefund | None:
        """Approve or reject one refund and create negative allocations on approval."""

        refund = self.get_refund(refund_id)
        if refund is None:
            return None
        if refund.state != "requested":
            raise FeesConflictError("Refund request is already reviewed")
        if payload.state == "approved":
            source = self._payment_for_update(refund.payment_id)
            if source is None:
                raise FeesValidationError("Refund source payment no longer exists")
            refund_payment = Payment(
                tenant_id=self.actor.tenant_id,
                student_id=source.student_id,
                source_payment_id=source.id,
                cashier_session_id=None,
                reference_number=f"REF-{str(refund.id).split('-')[0].upper()}",
                idempotency_key=f"refund:{refund.id}",
                method=source.method,
                state="posted",
                paid_on=datetime.now(UTC),
                note=refund.reason,
            )
            self.session.add(refund_payment)
            self.session.flush()
            remaining = refund.amount
            touched_invoice_ids: list[UUID] = []
            for source_allocation in self.list_payment_allocations(source.id):
                if remaining <= ZERO:
                    break
                refunded_amount = min(source_allocation.amount, remaining)
                self.session.add(
                    PaymentAllocation(
                        tenant_id=self.actor.tenant_id,
                        payment_id=refund_payment.id,
                        invoice_id=source_allocation.invoice_id,
                        amount=-refunded_amount,
                    )
                )
                touched_invoice_ids.append(source_allocation.invoice_id)
                remaining -= refunded_amount
            refund.refund_payment_id = refund_payment.id
            self.session.flush()
            for invoice_id in touched_invoice_ids:
                invoice = self._invoice_for_update(invoice_id)
                if invoice is not None:
                    self._refresh_invoice_state(invoice)
        refund.state = payload.state
        refund.reviewed_by_membership_id = self.actor.membership_id
        refund.reviewed_at = datetime.now(UTC)
        self.session.flush()
        self._audit(
            "fees.refund.review",
            "fee_refund",
            refund.id,
            {"state": refund.state, "amount": str(refund.amount)},
        )
        return refund

    def list_cashier_sessions(self, skip: int = 0, limit: int = 100) -> tuple[list[CashierSession], int]:
        """List cashier collection sessions for the authenticated tenant."""

        query = (
            select(CashierSession)
            .where(CashierSession.tenant_id == self.actor.tenant_id)
            .order_by(CashierSession.opened_at.desc())
        )
        return self._paginate(query, skip, limit)

    def get_cashier_session(self, cashier_session_id: UUID) -> CashierSession | None:
        """Return one cashier session by tenant-safe identifier."""

        return self.session.scalar(
            select(CashierSession).where(
                CashierSession.tenant_id == self.actor.tenant_id,
                CashierSession.id == cashier_session_id,
            )
        )

    def open_cashier_session(self, payload: CashierSessionOpen) -> CashierSession:
        """Open one collection session for the authenticated membership."""

        existing = self.session.scalar(
            select(CashierSession).where(
                CashierSession.tenant_id == self.actor.tenant_id,
                CashierSession.cashier_membership_id == self.actor.membership_id,
                CashierSession.state == "open",
            )
        )
        if existing is not None:
            raise FeesConflictError("This cashier already has an open session")
        cashier_session = CashierSession(
            tenant_id=self.actor.tenant_id,
            cashier_membership_id=self.actor.membership_id,
            opened_at=datetime.now(UTC),
            opening_amount=payload.opening_amount,
            state="open",
        )
        self.session.add(cashier_session)
        self.session.flush()
        self._audit("fees.cashier.open", "cashier_session", cashier_session.id, {})
        return cashier_session

    def close_cashier_session(
        self,
        cashier_session_id: UUID,
        payload: CashierSessionClose,
    ) -> CashierSession | None:
        """Close one cashier session against source-derived cash collections."""

        cashier_session = self.get_cashier_session(cashier_session_id)
        if cashier_session is None:
            return None
        if cashier_session.state != "open":
            raise FeesConflictError("Cashier session is already closed")
        collected = self.session.scalar(
            select(func.coalesce(func.sum(PaymentAllocation.amount), 0))
            .join(
                Payment,
                (Payment.tenant_id == PaymentAllocation.tenant_id)
                & (Payment.id == PaymentAllocation.payment_id),
            )
            .where(
                Payment.tenant_id == self.actor.tenant_id,
                Payment.cashier_session_id == cashier_session.id,
                Payment.method == "cash",
            )
        )
        expected = cashier_session.opening_amount + Decimal(collected or 0)
        cashier_session.expected_amount = expected
        cashier_session.declared_amount = payload.declared_amount
        cashier_session.variance_amount = payload.declared_amount - expected
        cashier_session.closed_at = datetime.now(UTC)
        cashier_session.state = "closed"
        self.session.flush()
        self._audit(
            "fees.cashier.close",
            "cashier_session",
            cashier_session.id,
            {"expected_amount": str(expected), "variance_amount": str(cashier_session.variance_amount)},
        )
        return cashier_session

    def list_reconciliations(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[GatewayReconciliation], int]:
        """List gateway settlement comparisons for the authenticated tenant."""

        query = (
            select(GatewayReconciliation)
            .where(GatewayReconciliation.tenant_id == self.actor.tenant_id)
            .order_by(GatewayReconciliation.reconciled_at.desc())
        )
        return self._paginate(query, skip, limit)

    def reconcile_gateway(self, payload: GatewayReconciliationCreate) -> GatewayReconciliation:
        """Compare one provider settlement to an optional posted payment."""

        state = "unmatched"
        if payload.payment_id is not None:
            payment = self.get_payment(payload.payment_id)
            if payment is None:
                raise FeesValidationError("Invalid payment_id reference")
            payment_total = sum((item.amount for item in self.list_payment_allocations(payment.id)), ZERO)
            state = "matched" if payment_total == payload.settled_amount else "mismatch"
        reconciliation = GatewayReconciliation(
            tenant_id=self.actor.tenant_id,
            payment_id=payload.payment_id,
            provider=payload.provider,
            external_reference=payload.external_reference,
            settled_amount=payload.settled_amount,
            state=state,
            details=payload.details,
            reconciled_by_membership_id=self.actor.membership_id,
            reconciled_at=datetime.now(UTC),
        )
        self.session.add(reconciliation)
        self.session.flush()
        self._audit(
            "fees.gateway.reconcile",
            "gateway_reconciliation",
            reconciliation.id,
            {"provider": reconciliation.provider, "state": reconciliation.state},
        )
        return reconciliation

    def build_student_ledger(
        self,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[StudentLedgerEntry], int, Decimal, Decimal, Decimal]:
        """Return derived ledger entries and balance summary for one student."""

        self._require_student(student_id)
        invoices = list(
            self.session.scalars(
                select(StudentInvoice)
                .where(
                    StudentInvoice.tenant_id == self.actor.tenant_id,
                    StudentInvoice.student_id == student_id,
                )
                .order_by(StudentInvoice.issued_on.asc(), StudentInvoice.created_at.asc())
            )
        )

        entries: list[StudentLedgerEntry] = []
        invoiced_total = ZERO
        paid_total = ZERO

        for invoice in invoices:
            invoice_total = self._invoice_total(invoice.id)
            invoiced_total += invoice_total
            entries.append(
                StudentLedgerEntry(
                    entry_date=datetime.combine(invoice.issued_on, datetime.min.time(), tzinfo=UTC),
                    entry_type="invoice",
                    reference_id=invoice.id,
                    reference_number=invoice.invoice_number,
                    amount=invoice_total,
                )
            )

        allocations = list(
            self.session.scalars(
                select(PaymentAllocation)
                .join(
                    Payment,
                    (PaymentAllocation.tenant_id == Payment.tenant_id)
                    & (PaymentAllocation.payment_id == Payment.id),
                )
                .where(
                    PaymentAllocation.tenant_id == self.actor.tenant_id,
                    Payment.student_id == student_id,
                )
                .order_by(Payment.paid_on.asc(), PaymentAllocation.created_at.asc())
            )
        )

        payment_map = {
            payment.id: payment
            for payment in self.session.scalars(
                select(Payment).where(
                    Payment.tenant_id == self.actor.tenant_id,
                    Payment.student_id == student_id,
                )
            )
        }

        for allocation in allocations:
            payment = payment_map.get(allocation.payment_id)
            if payment is None:
                continue
            paid_total += allocation.amount
            entries.append(
                StudentLedgerEntry(
                    entry_date=payment.paid_on,
                    entry_type="payment_allocation",
                    reference_id=payment.id,
                    reference_number=payment.reference_number,
                    amount=-allocation.amount,
                )
            )

        entries.sort(key=lambda item: (item.entry_date, item.reference_number))
        total = len(entries)
        paginated_entries = entries[skip : skip + limit]
        balance = (invoiced_total - paid_total).quantize(Decimal("0.01"))
        return paginated_entries, total, invoiced_total, paid_total, balance
