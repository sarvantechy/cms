"""FastAPI routes for tenant-safe fee planning, invoicing, payments, and ledger views."""

from collections.abc import Generator
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import runtime_session_factory
from app.domains.fees.schemas import (
    CashierSessionClose,
    CashierSessionOpen,
    CashierSessionSummary,
    FeeConcessionCreate,
    FeeConcessionReview,
    FeeConcessionSummary,
    FeeHeadCreate,
    FeeHeadSummary,
    FeePlanCreate,
    FeePlanSummary,
    FeeRefundCreate,
    FeeRefundReview,
    FeeRefundSummary,
    FinancialReversalCreate,
    FinancialReversalSummary,
    GatewayReconciliationCreate,
    GatewayReconciliationSummary,
    InvoiceLineSummary,
    PaginatedCashierSessions,
    PaginatedFeeConcessions,
    PaginatedFeeHeads,
    PaginatedFeePlans,
    PaginatedFeeRefunds,
    PaginatedGatewayReconciliations,
    PaginatedPayments,
    PaginatedStudentInvoices,
    PaymentCreate,
    PaymentPostResponse,
    PaymentSummary,
    ReceiptDocument,
    ReceiptSummary,
    StudentInvoiceCreate,
    StudentInvoiceSummary,
    StudentLedgerResponse,
)
from app.domains.fees.service import (
    FeesDomainError,
    FeesService,
)
from app.domains.identity.router import require_permission
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/fees", tags=["Fees"])

PaginationSkip = Annotated[int, Query(ge=0)]
PaginationLimit = Annotated[int, Query(ge=1, le=200)]
OptionalStudentId = Annotated[UUID | None, Query()]


def get_runtime_session() -> Generator[Session, None, None]:
    """Yield a restricted runtime session with explicit route-level commit control."""

    with runtime_session_factory()() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


def get_fees_service(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.records.read"))],
) -> FeesService:
    """Build a tenant-bound fees service for read operations."""

    return FeesService(session, actor)


def _raise_domain_error(error: FeesDomainError) -> None:
    """Translate domain failures to deterministic HTTP responses."""

    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _raise_conflict(error: IntegrityError) -> None:
    """Translate relational integrity failures into HTTP 409 responses."""

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Record conflicts with existing data",
    ) from error


def _build_invoice_summary(service: FeesService, invoice_id: UUID) -> StudentInvoiceSummary:
    """Return invoice summary with derived totals and line items."""

    invoice = service.get_invoice(invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    lines = service.list_invoice_lines(invoice.id)
    total_amount = sum((line.amount - line.discount for line in lines), start=Decimal("0.00"))
    allocated_amount = service._invoice_allocated(invoice.id)
    outstanding_amount = total_amount - allocated_amount
    return StudentInvoiceSummary(
        id=invoice.id,
        tenant_id=invoice.tenant_id,
        student_id=invoice.student_id,
        enrollment_id=invoice.enrollment_id,
        fee_plan_id=invoice.fee_plan_id,
        invoice_number=invoice.invoice_number,
        state=invoice.state,
        issued_on=invoice.issued_on,
        due_on=invoice.due_on,
        remarks=invoice.remarks,
        total_amount=total_amount,
        allocated_amount=allocated_amount,
        outstanding_amount=outstanding_amount,
        lines=[InvoiceLineSummary.model_validate(item) for item in lines],
    )


def _build_payment_summary(service: FeesService, payment_id: UUID) -> PaymentSummary:
    """Return payment summary including allocation rows."""

    payment = service.get_payment(payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    allocations = service.list_payment_allocations(payment.id)
    return PaymentSummary(
        id=payment.id,
        tenant_id=payment.tenant_id,
        student_id=payment.student_id,
        source_payment_id=payment.source_payment_id,
        cashier_session_id=payment.cashier_session_id,
        reference_number=payment.reference_number,
        idempotency_key=payment.idempotency_key,
        method=payment.method,
        state=payment.state,
        paid_on=payment.paid_on,
        note=payment.note,
        allocations=[item for item in allocations],
    )


@router.get("/heads", response_model=PaginatedFeeHeads)
def list_fee_heads(
    service: Annotated[FeesService, Depends(get_fees_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedFeeHeads:
    """Return a paginated list of fee heads for the authenticated tenant."""

    items, total = service.list_fee_heads(skip=skip, limit=limit)
    return PaginatedFeeHeads(items=[FeeHeadSummary.model_validate(item) for item in items], total=total)


@router.post("/heads", response_model=FeeHeadSummary, status_code=status.HTTP_201_CREATED)
def create_fee_head(
    payload: FeeHeadCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.invoices.manage"))],
) -> FeeHeadSummary:
    """Create one fee head for the authenticated tenant."""

    service = FeesService(session, actor)
    try:
        item = service.create_fee_head(payload)
        response = FeeHeadSummary.model_validate(item)
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/plans", response_model=PaginatedFeePlans)
def list_fee_plans(
    service: Annotated[FeesService, Depends(get_fees_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedFeePlans:
    """Return a paginated list of fee plans with line components."""

    plans, total = service.list_fee_plans(skip=skip, limit=limit)
    items: list[FeePlanSummary] = []
    for plan in plans:
        lines = service.list_fee_plan_lines(plan.id)
        items.append(
            FeePlanSummary(
                id=plan.id,
                tenant_id=plan.tenant_id,
                program_id=plan.program_id,
                academic_year_id=plan.academic_year_id,
                code=plan.code,
                title=plan.title,
                state=plan.state,
                effective_from=plan.effective_from,
                effective_to=plan.effective_to,
                lines=[item for item in lines],
            )
        )
    return PaginatedFeePlans(items=items, total=total)


@router.get("/plans/{fee_plan_id}", response_model=FeePlanSummary)
def get_fee_plan(
    fee_plan_id: UUID,
    service: Annotated[FeesService, Depends(get_fees_service)],
) -> FeePlanSummary:
    """Return one fee plan by ID for the authenticated tenant."""

    plan = service.get_fee_plan(fee_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee plan not found")
    lines = service.list_fee_plan_lines(plan.id)
    return FeePlanSummary(
        id=plan.id,
        tenant_id=plan.tenant_id,
        program_id=plan.program_id,
        academic_year_id=plan.academic_year_id,
        code=plan.code,
        title=plan.title,
        state=plan.state,
        effective_from=plan.effective_from,
        effective_to=plan.effective_to,
        lines=[item for item in lines],
    )


@router.post("/plans", response_model=FeePlanSummary, status_code=status.HTTP_201_CREATED)
def create_fee_plan(
    payload: FeePlanCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.invoices.manage"))],
) -> FeePlanSummary:
    """Create one fee plan and line breakdown for the authenticated tenant."""

    service = FeesService(session, actor)
    try:
        plan = service.create_fee_plan(payload)
        lines = service.list_fee_plan_lines(plan.id)
        response = FeePlanSummary(
            id=plan.id,
            tenant_id=plan.tenant_id,
            program_id=plan.program_id,
            academic_year_id=plan.academic_year_id,
            code=plan.code,
            title=plan.title,
            state=plan.state,
            effective_from=plan.effective_from,
            effective_to=plan.effective_to,
            lines=[item for item in lines],
        )
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/invoices", response_model=PaginatedStudentInvoices)
def list_invoices(
    service: Annotated[FeesService, Depends(get_fees_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    student_id: OptionalStudentId = None,
) -> PaginatedStudentInvoices:
    """Return a paginated list of student invoices with derived totals."""

    invoices, total = service.list_invoices(skip=skip, limit=limit, student_id=student_id)
    items = [_build_invoice_summary(service, invoice.id) for invoice in invoices]
    return PaginatedStudentInvoices(items=items, total=total)


@router.get("/invoices/{invoice_id}", response_model=StudentInvoiceSummary)
def get_invoice(
    invoice_id: UUID,
    service: Annotated[FeesService, Depends(get_fees_service)],
) -> StudentInvoiceSummary:
    """Return one student invoice with source-derived totals and lines."""

    return _build_invoice_summary(service, invoice_id)


@router.post("/invoices", response_model=StudentInvoiceSummary, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: StudentInvoiceCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.invoices.manage"))],
) -> StudentInvoiceSummary:
    """Create one student invoice from fee plan defaults or explicit line items."""

    service = FeesService(session, actor)
    try:
        invoice = service.create_invoice(payload)
        response = _build_invoice_summary(service, invoice.id)
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/payments", response_model=PaginatedPayments)
def list_payments(
    service: Annotated[FeesService, Depends(get_fees_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    student_id: OptionalStudentId = None,
) -> PaginatedPayments:
    """Return a paginated list of payment transactions with allocations."""

    payments, total = service.list_payments(skip=skip, limit=limit, student_id=student_id)
    items = [_build_payment_summary(service, payment.id) for payment in payments]
    return PaginatedPayments(items=items, total=total)


@router.get("/payments/{payment_id}", response_model=PaymentSummary)
def get_payment(
    payment_id: UUID,
    service: Annotated[FeesService, Depends(get_fees_service)],
) -> PaymentSummary:
    """Return one payment transaction with all allocation rows."""

    return _build_payment_summary(service, payment_id)


@router.post("/payments", response_model=PaymentPostResponse, status_code=status.HTTP_201_CREATED)
def post_payment(
    payload: PaymentCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.payments.collect"))],
) -> PaymentPostResponse:
    """Post one payment atomically with allocation rows and idempotent replay behavior."""

    service = FeesService(session, actor)
    try:
        payment, idempotent_replay = service.post_payment(payload)
        response = PaymentPostResponse(
            payment=_build_payment_summary(service, payment.id),
            idempotent_replay=idempotent_replay,
        )
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/payments/{payment_id}/receipt", response_model=ReceiptSummary)
def issue_receipt(
    payment_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.payments.collect"))],
) -> ReceiptSummary:
    """Issue a receipt for one payment and return existing receipt on replay."""

    service = FeesService(session, actor)
    try:
        receipt = service.issue_receipt(payment_id)
        response = ReceiptSummary.model_validate(receipt)
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/payments/{payment_id}/receipt-document", response_model=ReceiptDocument)
def get_receipt_document(
    payment_id: UUID,
    service: Annotated[FeesService, Depends(get_fees_service)],
) -> ReceiptDocument:
    """Return a print-ready receipt derived from authorized financial source records."""

    document = service.get_receipt_document(payment_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    return document


@router.post("/payments/{payment_id}/reverse", response_model=FinancialReversalSummary)
def reverse_payment(
    payment_id: UUID,
    payload: FinancialReversalCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.refunds.approve"))],
) -> FinancialReversalSummary:
    """Reverse one payment by writing a compensating transaction and reversal record."""

    service = FeesService(session, actor)
    try:
        reversal = service.reverse_payment(payment_id, payload)
        response = FinancialReversalSummary.model_validate(reversal)
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)


@router.get("/concessions", response_model=PaginatedFeeConcessions)
def list_concessions(
    service: Annotated[FeesService, Depends(get_fees_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedFeeConcessions:
    """Return concession requests for the authenticated tenant."""

    items, total = service.list_concessions(skip=skip, limit=limit)
    return PaginatedFeeConcessions(
        items=[FeeConcessionSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post("/concessions", response_model=FeeConcessionSummary, status_code=status.HTTP_201_CREATED)
def create_concession(
    payload: FeeConcessionCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.invoices.manage"))],
) -> FeeConcessionSummary:
    """Request one concession against an invoice line."""

    service = FeesService(session, actor)
    try:
        item = service.create_concession(payload)
        response = FeeConcessionSummary.model_validate(item)
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/concessions/{concession_id}/review", response_model=FeeConcessionSummary)
def review_concession(
    concession_id: UUID,
    payload: FeeConcessionReview,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.refunds.approve"))],
) -> FeeConcessionSummary:
    """Approve or reject one concession request."""

    service = FeesService(session, actor)
    try:
        item = service.review_concession(concession_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concession not found")
        response = FeeConcessionSummary.model_validate(item)
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)


@router.get("/refunds", response_model=PaginatedFeeRefunds)
def list_refunds(
    service: Annotated[FeesService, Depends(get_fees_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedFeeRefunds:
    """Return refund requests for the authenticated tenant."""

    items, total = service.list_refunds(skip=skip, limit=limit)
    return PaginatedFeeRefunds(
        items=[FeeRefundSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post("/refunds", response_model=FeeRefundSummary, status_code=status.HTTP_201_CREATED)
def create_refund(
    payload: FeeRefundCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.refunds.request"))],
) -> FeeRefundSummary:
    """Request a partial or full refund against one source payment."""

    service = FeesService(session, actor)
    try:
        item = service.create_refund(payload)
        response = FeeRefundSummary.model_validate(item)
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/refunds/{refund_id}/review", response_model=FeeRefundSummary)
def review_refund(
    refund_id: UUID,
    payload: FeeRefundReview,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.refunds.approve"))],
) -> FeeRefundSummary:
    """Approve or reject one refund and return its compensating payment link."""

    service = FeesService(session, actor)
    try:
        item = service.review_refund(refund_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund not found")
        response = FeeRefundSummary.model_validate(item)
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/cashier-sessions", response_model=PaginatedCashierSessions)
def list_cashier_sessions(
    service: Annotated[FeesService, Depends(get_fees_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedCashierSessions:
    """Return cashier collection sessions for the authenticated tenant."""

    items, total = service.list_cashier_sessions(skip=skip, limit=limit)
    return PaginatedCashierSessions(
        items=[CashierSessionSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post("/cashier-sessions", response_model=CashierSessionSummary, status_code=status.HTTP_201_CREATED)
def open_cashier_session(
    payload: CashierSessionOpen,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.payments.collect"))],
) -> CashierSessionSummary:
    """Open one cashier collection session for the authenticated membership."""

    service = FeesService(session, actor)
    try:
        item = service.open_cashier_session(payload)
        response = CashierSessionSummary.model_validate(item)
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/cashier-sessions/{cashier_session_id}/close", response_model=CashierSessionSummary)
def close_cashier_session(
    cashier_session_id: UUID,
    payload: CashierSessionClose,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.payments.collect"))],
) -> CashierSessionSummary:
    """Close one cashier session with expected and declared balances."""

    service = FeesService(session, actor)
    try:
        item = service.close_cashier_session(cashier_session_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cashier session not found")
        response = CashierSessionSummary.model_validate(item)
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)


@router.get("/gateway-reconciliations", response_model=PaginatedGatewayReconciliations)
def list_gateway_reconciliations(
    service: Annotated[FeesService, Depends(get_fees_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedGatewayReconciliations:
    """Return provider settlement comparisons for the authenticated tenant."""

    items, total = service.list_reconciliations(skip=skip, limit=limit)
    return PaginatedGatewayReconciliations(
        items=[GatewayReconciliationSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post(
    "/gateway-reconciliations",
    response_model=GatewayReconciliationSummary,
    status_code=status.HTTP_201_CREATED,
)
def reconcile_gateway(
    payload: GatewayReconciliationCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("fees.payments.collect"))],
) -> GatewayReconciliationSummary:
    """Persist one computed gateway settlement comparison."""

    service = FeesService(session, actor)
    try:
        item = service.reconcile_gateway(payload)
        response = GatewayReconciliationSummary.model_validate(item)
        session.commit()
        return response
    except FeesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/students/{student_id}/ledger", response_model=StudentLedgerResponse)
def get_student_ledger(
    student_id: UUID,
    service: Annotated[FeesService, Depends(get_fees_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> StudentLedgerResponse:
    """Return source-derived student ledger entries and current fee balance."""

    try:
        items, total, invoiced_total, paid_total, balance = service.build_student_ledger(
            student_id=student_id,
            skip=skip,
            limit=limit,
        )
        return StudentLedgerResponse(
            student_id=student_id,
            invoiced_total=invoiced_total,
            paid_total=paid_total,
            balance=balance,
            items=items,
            total=total,
        )
    except FeesDomainError as error:
        _raise_domain_error(error)
