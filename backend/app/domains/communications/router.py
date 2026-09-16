"""FastAPI routes for tenant-safe notices and portal delivery workflows."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import runtime_session_factory
from app.domains.communications.schemas import (
    ApprovalDecision,
    AudiencePreview,
    AudiencePreviewRequest,
    CommunicationPreferenceSummary,
    CommunicationPreferenceUpdate,
    DeliveryAttemptSummary,
    DeliveryJobSummary,
    MessageTemplateCreate,
    MessageTemplateSummary,
    MessageTemplateUpdate,
    NoticeAcknowledgementSummary,
    NoticeApprovalEventSummary,
    NoticeCreate,
    NoticeDeliverySummary,
    NoticeScheduleRequest,
    NoticeSummary,
    NoticeUpdate,
    PaginatedApprovalEvents,
    PaginatedDeliveryAttempts,
    PaginatedDeliveryJobs,
    PaginatedMessageTemplates,
    PaginatedNoticeDeliveries,
    PaginatedNotices,
)
from app.domains.communications.service import (
    CommunicationsDomainError,
    CommunicationsService,
)
from app.domains.identity.router import require_permission
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/communications", tags=["Communications"])

PaginationSkip = Annotated[int, Query(ge=0)]
PaginationLimit = Annotated[int, Query(ge=1, le=200)]


def get_runtime_session() -> Generator[Session, None, None]:
    """Yield a restricted runtime session with explicit route-level commit control."""

    with runtime_session_factory()() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


def get_communications_service(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("communications.notices.read"))],
) -> CommunicationsService:
    """Build a communications service for read operations under tenant-safe authorization."""

    return CommunicationsService(session, actor)


def _raise_domain_error(error: CommunicationsDomainError) -> None:
    """Translate domain failures into deterministic API responses."""

    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _raise_conflict(error: IntegrityError) -> None:
    """Translate relational uniqueness and integrity failures into HTTP 409."""

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Record conflicts with existing data",
    ) from error


@router.get("/notices", response_model=PaginatedNotices)
def list_notices(
    service: Annotated[CommunicationsService, Depends(get_communications_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    state: str | None = Query(default=None, pattern="^(draft|scheduled|published|archived)$"),
) -> PaginatedNotices:
    """Return a paginated list of notices for the authenticated tenant."""

    items, total = service.list_notices(skip=skip, limit=limit, state=state)
    return PaginatedNotices(items=[NoticeSummary.model_validate(item) for item in items], total=total)


@router.post("/notices", response_model=NoticeSummary, status_code=status.HTTP_201_CREATED)
def create_notice(
    payload: NoticeCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("communications.notices.manage"))],
) -> NoticeSummary:
    """Create one tenant-scoped notice in draft or scheduled state."""

    service = CommunicationsService(session, actor)
    try:
        item = service.create_notice(payload)
        response = NoticeSummary.model_validate(item)
        session.commit()
        return response
    except CommunicationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/audience-preview", response_model=AudiencePreview)
def preview_audience(
    payload: AudiencePreviewRequest,
    service: Annotated[CommunicationsService, Depends(get_communications_service)],
) -> AudiencePreview:
    """Return the server-resolved recipient count for an audience rule."""

    try:
        return AudiencePreview(recipient_count=service.preview_audience(payload.audience_type, payload.audience_ref))
    except CommunicationsDomainError as error:
        _raise_domain_error(error)


@router.get("/templates", response_model=PaginatedMessageTemplates)
def list_templates(service: Annotated[CommunicationsService, Depends(get_communications_service)], skip: PaginationSkip = 0, limit: PaginationLimit = 100) -> PaginatedMessageTemplates:
    """List reusable tenant communication templates."""

    items, total = service.list_templates(skip, limit)
    return PaginatedMessageTemplates(items=[MessageTemplateSummary.model_validate(item) for item in items], total=total)


@router.post("/templates", response_model=MessageTemplateSummary, status_code=status.HTTP_201_CREATED)
def create_template(payload: MessageTemplateCreate, session: Annotated[Session, Depends(get_runtime_session)], actor: Annotated[ActorContext, Depends(require_permission("communications.notices.manage"))]) -> MessageTemplateSummary:
    """Create one reusable tenant communication template."""

    try:
        item = CommunicationsService(session, actor).create_template(payload)
        response = MessageTemplateSummary.model_validate(item)
        session.commit()
        return response
    except CommunicationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/templates/{template_id}", response_model=MessageTemplateSummary)
def update_template(template_id: UUID, payload: MessageTemplateUpdate, session: Annotated[Session, Depends(get_runtime_session)], actor: Annotated[ActorContext, Depends(require_permission("communications.notices.manage"))]) -> MessageTemplateSummary:
    """Update one reusable tenant communication template."""

    try:
        item = CommunicationsService(session, actor).update_template(template_id, payload)
        response = MessageTemplateSummary.model_validate(item)
        session.commit()
        return response
    except CommunicationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/notices/{notice_id}", response_model=NoticeSummary)
def update_notice(
    notice_id: UUID,
    payload: NoticeUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("communications.notices.manage"))],
) -> NoticeSummary:
    """Update mutable notice fields for one tenant notice."""

    service = CommunicationsService(session, actor)
    try:
        item = service.update_notice(notice_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")
        response = NoticeSummary.model_validate(item)
        session.commit()
        return response
    except CommunicationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/notices/{notice_id}/publish", response_model=NoticeSummary)
def publish_notice(
    notice_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("communications.notices.manage"))],
) -> NoticeSummary:
    """Publish one notice and upsert tenant delivery records."""

    service = CommunicationsService(session, actor)
    try:
        item = service.publish_notice(notice_id)
        response = NoticeSummary.model_validate(item)
        session.commit()
        return response
    except CommunicationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


def _transition_notice(notice_id: UUID, payload: ApprovalDecision, session: Session, actor: ActorContext, transition: str) -> NoticeSummary:
    """Apply and commit one notice approval transition."""

    service = CommunicationsService(session, actor)
    item = service.submit_notice(notice_id, payload.comment) if transition == "submit" else service.decide_notice(notice_id, transition == "approve", payload.comment)
    response = NoticeSummary.model_validate(item)
    session.commit()
    return response


@router.post("/notices/{notice_id}/submit", response_model=NoticeSummary)
def submit_notice(notice_id: UUID, payload: ApprovalDecision, session: Annotated[Session, Depends(get_runtime_session)], actor: Annotated[ActorContext, Depends(require_permission("communications.notices.manage"))]) -> NoticeSummary:
    """Submit a draft notice for approval."""

    try:
        return _transition_notice(notice_id, payload, session, actor, "submit")
    except CommunicationsDomainError as error:
        _raise_domain_error(error)


@router.post("/notices/{notice_id}/approve", response_model=NoticeSummary)
def approve_notice(notice_id: UUID, payload: ApprovalDecision, session: Annotated[Session, Depends(get_runtime_session)], actor: Annotated[ActorContext, Depends(require_permission("communications.notices.manage"))]) -> NoticeSummary:
    """Approve one pending notice."""

    try:
        return _transition_notice(notice_id, payload, session, actor, "approve")
    except CommunicationsDomainError as error:
        _raise_domain_error(error)


@router.post("/notices/{notice_id}/reject", response_model=NoticeSummary)
def reject_notice(notice_id: UUID, payload: ApprovalDecision, session: Annotated[Session, Depends(get_runtime_session)], actor: Annotated[ActorContext, Depends(require_permission("communications.notices.manage"))]) -> NoticeSummary:
    """Reject one pending notice back to draft."""

    try:
        return _transition_notice(notice_id, payload, session, actor, "reject")
    except CommunicationsDomainError as error:
        _raise_domain_error(error)


@router.get("/notices/{notice_id}/approval-events", response_model=PaginatedApprovalEvents)
def list_approval_events(notice_id: UUID, service: Annotated[CommunicationsService, Depends(get_communications_service)], skip: PaginationSkip = 0, limit: PaginationLimit = 100) -> PaginatedApprovalEvents:
    """List immutable approval history for one notice."""

    try:
        items, total = service.list_approval_events(notice_id, skip, limit)
        return PaginatedApprovalEvents(items=[NoticeApprovalEventSummary.model_validate(item) for item in items], total=total)
    except CommunicationsDomainError as error:
        _raise_domain_error(error)


@router.post("/notices/{notice_id}/schedule", response_model=NoticeSummary)
def schedule_notice(
    notice_id: UUID,
    payload: NoticeScheduleRequest,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("communications.notices.manage"))],
) -> NoticeSummary:
    """Schedule one notice for future publication and pre-create delivery targets."""

    service = CommunicationsService(session, actor)
    try:
        item = service.schedule_notice(notice_id, payload.publish_at)
        response = NoticeSummary.model_validate(item)
        session.commit()
        return response
    except CommunicationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/notices/{notice_id}/deliveries", response_model=PaginatedNoticeDeliveries)
def list_notice_deliveries(
    notice_id: UUID,
    service: Annotated[CommunicationsService, Depends(get_communications_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedNoticeDeliveries:
    """Return paginated membership delivery records for one notice."""

    try:
        items, total = service.list_deliveries(notice_id=notice_id, skip=skip, limit=limit)
        return PaginatedNoticeDeliveries(
            items=[NoticeDeliverySummary.model_validate(item) for item in items],
            total=total,
        )
    except CommunicationsDomainError as error:
        _raise_domain_error(error)


@router.post("/notices/{notice_id}/read", response_model=NoticeDeliverySummary)
def mark_notice_read(
    notice_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("communications.notices.read"))],
) -> NoticeDeliverySummary:
    """Mark one notice as read for the authenticated tenant membership."""

    service = CommunicationsService(session, actor)
    try:
        item = service.mark_read(notice_id)
        response = NoticeDeliverySummary.model_validate(item)
        session.commit()
        return response
    except CommunicationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/notices/{notice_id}/acknowledge", response_model=NoticeAcknowledgementSummary)
def acknowledge_notice(notice_id: UUID, session: Annotated[Session, Depends(get_runtime_session)], actor: Annotated[ActorContext, Depends(require_permission("communications.notices.read"))]) -> NoticeAcknowledgementSummary:
    """Acknowledge a delivered notice for the authenticated membership."""

    try:
        item = CommunicationsService(session, actor).acknowledge_notice(notice_id)
        response = NoticeAcknowledgementSummary.model_validate(item)
        session.commit()
        return response
    except CommunicationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/preferences", response_model=CommunicationPreferenceSummary)
def get_preferences(session: Annotated[Session, Depends(get_runtime_session)], actor: Annotated[ActorContext, Depends(require_permission("communications.notices.read"))]) -> CommunicationPreferenceSummary:
    """Return the authenticated membership's channel preferences."""

    item = CommunicationsService(session, actor).get_preferences()
    response = CommunicationPreferenceSummary.model_validate(item)
    session.commit()
    return response


@router.put("/preferences", response_model=CommunicationPreferenceSummary)
def update_preferences(payload: CommunicationPreferenceUpdate, session: Annotated[Session, Depends(get_runtime_session)], actor: Annotated[ActorContext, Depends(require_permission("communications.notices.read"))]) -> CommunicationPreferenceSummary:
    """Update the authenticated membership's channel preferences."""

    item = CommunicationsService(session, actor).update_preferences(payload)
    response = CommunicationPreferenceSummary.model_validate(item)
    session.commit()
    return response


@router.get("/notices/{notice_id}/jobs", response_model=PaginatedDeliveryJobs)
def list_delivery_jobs(notice_id: UUID, service: Annotated[CommunicationsService, Depends(get_communications_service)], skip: PaginationSkip = 0, limit: PaginationLimit = 100) -> PaginatedDeliveryJobs:
    """List provider-independent channel jobs for one notice."""

    try:
        items, total = service.list_delivery_jobs(notice_id, skip, limit)
        return PaginatedDeliveryJobs(items=[DeliveryJobSummary.model_validate(item) for item in items], total=total)
    except CommunicationsDomainError as error:
        _raise_domain_error(error)


@router.get("/jobs/{job_id}/attempts", response_model=PaginatedDeliveryAttempts)
def list_delivery_attempts(job_id: UUID, service: Annotated[CommunicationsService, Depends(get_communications_service)], skip: PaginationSkip = 0, limit: PaginationLimit = 100) -> PaginatedDeliveryAttempts:
    """List immutable attempt history for one channel job."""

    try:
        items, total = service.list_delivery_attempts(job_id, skip, limit)
        return PaginatedDeliveryAttempts(items=[DeliveryAttemptSummary.model_validate(item) for item in items], total=total)
    except CommunicationsDomainError as error:
        _raise_domain_error(error)


@router.post("/jobs/{job_id}/retry", response_model=DeliveryJobSummary)
def retry_delivery_job(job_id: UUID, session: Annotated[Session, Depends(get_runtime_session)], actor: Annotated[ActorContext, Depends(require_permission("communications.notices.manage"))]) -> DeliveryJobSummary:
    """Requeue one failed provider job."""

    try:
        item = CommunicationsService(session, actor).retry_delivery_job(job_id)
        response = DeliveryJobSummary.model_validate(item)
        session.commit()
        return response
    except CommunicationsDomainError as error:
        _raise_domain_error(error)
