"""FastAPI routes for tenant-safe admissions campaigns and application lifecycle workflows."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import runtime_session_factory
from app.domains.admissions.schemas import (
    AdmissionCampaignCreate,
    AdmissionCampaignListResponse,
    AdmissionCampaignSummary,
    AdmissionCampaignUpdate,
    AdmissionEnquiryCreate,
    AdmissionEnquiryListResponse,
    AdmissionEnquirySummary,
    AdmissionEnquiryTransition,
    AdmissionEnquiryUpdate,
    AdmissionOfferCreate,
    AdmissionOfferListResponse,
    AdmissionOfferStateTransition,
    AdmissionOfferSummary,
    AdmissionOfferUpdate,
    AdmissionsHistoryEntry,
    ApplicantCreate,
    ApplicantListResponse,
    ApplicantSummary,
    ApplicantUpdate,
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationDocumentCreate,
    ApplicationDocumentListResponse,
    ApplicationDocumentSummary,
    ApplicationDocumentUpdate,
    ApplicationDocumentVerificationTransition,
    ApplicationListResponse,
    ApplicationStateTransition,
    ApplicationSummary,
    ApplicationUpdate,
    SeatPoolCreate,
    SeatPoolListResponse,
    SeatPoolSummary,
    SeatPoolUpdate,
)
from app.domains.admissions.service import (
    AdmissionsDomainError,
    AdmissionsService,
)
from app.domains.identity.router import require_permission
from app.media_storage import MAX_MEDIA_BYTES, LocalMediaStorage, MediaValidationError
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/admissions", tags=["Admissions"])

PaginationSkip = Annotated[int, Query(ge=0)]
PaginationLimit = Annotated[int, Query(ge=1, le=200)]
OptionalCampaignId = Annotated[UUID | None, Query()]
OptionalApplicantId = Annotated[UUID | None, Query()]
OptionalApplicationId = Annotated[UUID | None, Query()]
OptionalApplicationState = Annotated[str | None, Query(max_length=20)]
OptionalOfferState = Annotated[str | None, Query(max_length=16)]
OptionalEnquiryState = Annotated[str | None, Query(max_length=16)]


def get_runtime_session() -> Generator[Session, None, None]:
    """Yield a restricted runtime session with explicit route-level commit control."""

    with runtime_session_factory()() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


def get_admissions_service(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.read"))],
) -> AdmissionsService:
    """Build a tenant-bound admissions service for read-only operations."""

    return AdmissionsService(session, actor)


def _raise_domain_error(error: AdmissionsDomainError) -> None:
    """Translate service-level domain errors into stable HTTP API failures."""

    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _raise_conflict(error: IntegrityError) -> None:
    """Translate database integrity exceptions into deterministic conflict responses."""

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Record conflicts with existing data",
    ) from error


def _application_detail_response(
    detail: tuple[object, object, list[object]],
) -> ApplicationDetailResponse:
    """Serialize one service-level application detail tuple."""

    application, applicant, documents = detail
    return ApplicationDetailResponse(
        application=ApplicationSummary.model_validate(application),
        applicant=ApplicantSummary.model_validate(applicant),
        documents=[ApplicationDocumentSummary.model_validate(item) for item in documents],
    )


@router.get("/self-service/application", response_model=ApplicationDetailResponse)
def get_own_application(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.own"))],
) -> ApplicationDetailResponse:
    """Return only the application bound to the authenticated applicant."""

    detail = AdmissionsService(session, actor).get_own_application_detail()
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return _application_detail_response(detail)


@router.patch("/self-service/applicant", response_model=ApplicantSummary)
def update_own_applicant(
    payload: ApplicantUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.own"))],
) -> ApplicantSummary:
    """Update the identity bound to the authenticated applicant membership."""

    try:
        applicant = AdmissionsService(session, actor).update_own_applicant(payload)
        if applicant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        response = ApplicantSummary.model_validate(applicant)
        session.commit()
        return response
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/self-service/application", response_model=ApplicationSummary)
def update_own_application(
    payload: ApplicationUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.own"))],
) -> ApplicationSummary:
    """Update applicant-editable fields on the authenticated applicant's draft."""

    try:
        application = AdmissionsService(session, actor).update_own_application(payload)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        response = ApplicationSummary.model_validate(application)
        session.commit()
        return response
    except AdmissionsDomainError as error:
        _raise_domain_error(error)


@router.post("/self-service/application/submit", response_model=ApplicationSummary)
def submit_own_application(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.own"))],
) -> ApplicationSummary:
    """Submit the authenticated applicant's draft through the admissions state machine."""

    try:
        application = AdmissionsService(session, actor).submit_own_application()
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        response = ApplicationSummary.model_validate(application)
        session.commit()
        return response
    except AdmissionsDomainError as error:
        _raise_domain_error(error)


@router.post(
    "/self-service/documents",
    response_model=ApplicationDocumentSummary,
    status_code=status.HTTP_201_CREATED,
)
async def upload_own_document(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.own"))],
    document_type: Annotated[str, Form(min_length=1, max_length=48)],
    file: Annotated[UploadFile, File()],
    document_number: Annotated[str | None, Form(max_length=80)] = None,
) -> ApplicationDocumentSummary:
    """Validate and privately store a document for the authenticated applicant."""

    storage = LocalMediaStorage()
    stored = None
    try:
        content = await file.read(MAX_MEDIA_BYTES + 1)
        stored = storage.store(actor.tenant_id, content, file.content_type or "")
        document = AdmissionsService(session, actor).create_own_uploaded_document(
            document_type=document_type,
            document_number=document_number,
            original_filename=file.filename or "upload",
            content_type=file.content_type or "application/octet-stream",
            stored=stored,
        )
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        response = ApplicationDocumentSummary.model_validate(document)
        session.commit()
        return response
    except MediaValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except AdmissionsDomainError as error:
        if stored is not None:
            storage.delete(stored.object_key)
        _raise_domain_error(error)
    except IntegrityError as error:
        if stored is not None:
            storage.delete(stored.object_key)
        _raise_conflict(error)


@router.get("/self-service/documents/{document_id}/content", response_class=FileResponse)
def download_own_document(
    document_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.own"))],
) -> FileResponse:
    """Download one private document belonging to the authenticated applicant."""

    result = AdmissionsService(session, actor).get_own_document_media(document_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    _, media = result
    path = LocalMediaStorage().resolve(media.object_key)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document content not found")
    return FileResponse(
        path,
        media_type=media.content_type,
        filename=media.original_filename,
        headers={"Cache-Control": "private, no-store", "Vary": "Authorization"},
    )


@router.get("/documents/{document_id}/content", response_class=FileResponse)
def download_application_document(
    document_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.read"))],
) -> FileResponse:
    """Download private application media for authorized admissions staff."""

    result = AdmissionsService(session, actor).get_document_media(document_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    _, media = result
    path = LocalMediaStorage().resolve(media.object_key)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document content not found")
    return FileResponse(
        path,
        media_type=media.content_type,
        filename=media.original_filename,
        headers={"Cache-Control": "private, no-store", "Vary": "Authorization"},
    )


@router.get("/enquiries", response_model=AdmissionEnquiryListResponse)
def list_enquiries(
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    state: OptionalEnquiryState = None,
) -> AdmissionEnquiryListResponse:
    """Return tenant enquiries with an optional lifecycle filter."""

    items, total = service.list_enquiries(skip, limit, state)
    return AdmissionEnquiryListResponse(
        items=[AdmissionEnquirySummary.model_validate(item) for item in items],
        total=total,
    )


@router.post("/enquiries", response_model=AdmissionEnquirySummary, status_code=status.HTTP_201_CREATED)
def create_enquiry(
    payload: AdmissionEnquiryCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> AdmissionEnquirySummary:
    """Create one tenant admissions enquiry."""

    try:
        enquiry = AdmissionsService(session, actor).create_enquiry(payload)
        session.commit()
        return AdmissionEnquirySummary.model_validate(enquiry)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/enquiries/{enquiry_id}", response_model=AdmissionEnquirySummary)
def update_enquiry(
    enquiry_id: UUID,
    payload: AdmissionEnquiryUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> AdmissionEnquirySummary:
    """Update one tenant enquiry's contact and follow-up details."""

    try:
        enquiry = AdmissionsService(session, actor).update_enquiry(enquiry_id, payload)
        if enquiry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enquiry not found")
        session.commit()
        return AdmissionEnquirySummary.model_validate(enquiry)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/enquiries/{enquiry_id}/transition", response_model=AdmissionEnquirySummary)
def transition_enquiry(
    enquiry_id: UUID,
    payload: AdmissionEnquiryTransition,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> AdmissionEnquirySummary:
    """Transition one enquiry through its controlled lifecycle."""

    try:
        enquiry = AdmissionsService(session, actor).transition_enquiry(enquiry_id, payload)
        if enquiry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enquiry not found")
        response = AdmissionEnquirySummary.model_validate(enquiry)
        session.commit()
        return response
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/campaigns", response_model=AdmissionCampaignListResponse)
def list_campaigns(
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> AdmissionCampaignListResponse:
    """Return a paginated list of admission campaigns for the authenticated tenant."""

    items, total = service.list_campaigns(skip, limit)
    return AdmissionCampaignListResponse(
        items=[AdmissionCampaignSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/campaigns/{campaign_id}", response_model=AdmissionCampaignSummary)
def get_campaign(
    campaign_id: UUID,
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
) -> AdmissionCampaignSummary:
    """Return one campaign by ID for the authenticated tenant."""

    campaign = service.get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return AdmissionCampaignSummary.model_validate(campaign)


@router.post("/campaigns", response_model=AdmissionCampaignSummary, status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: AdmissionCampaignCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> AdmissionCampaignSummary:
    """Create one campaign after validating tenant-scoped academic-year and program references."""

    service = AdmissionsService(session, actor)
    try:
        campaign = service.create_campaign(payload)
        session.commit()
        return AdmissionCampaignSummary.model_validate(campaign)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/campaigns/{campaign_id}", response_model=AdmissionCampaignSummary)
def update_campaign(
    campaign_id: UUID,
    payload: AdmissionCampaignUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> AdmissionCampaignSummary:
    """Update mutable campaign fields for the authenticated tenant."""

    service = AdmissionsService(session, actor)
    try:
        campaign = service.update_campaign(campaign_id, payload)
        if campaign is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        session.commit()
        return AdmissionCampaignSummary.model_validate(campaign)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/applicants", response_model=ApplicantListResponse)
def list_applicants(
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> ApplicantListResponse:
    """Return a paginated list of applicants for the authenticated tenant."""

    items, total = service.list_applicants(skip, limit)
    return ApplicantListResponse(
        items=[ApplicantSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/applicants/{applicant_id}", response_model=ApplicantSummary)
def get_applicant(
    applicant_id: UUID,
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
) -> ApplicantSummary:
    """Return one applicant by ID for the authenticated tenant."""

    applicant = service.get_applicant(applicant_id)
    if applicant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant not found")
    return ApplicantSummary.model_validate(applicant)


@router.post("/applicants", response_model=ApplicantSummary, status_code=status.HTTP_201_CREATED)
def create_applicant(
    payload: ApplicantCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> ApplicantSummary:
    """Create one applicant for the authenticated tenant."""

    service = AdmissionsService(session, actor)
    try:
        applicant = service.create_applicant(payload)
        session.commit()
        return ApplicantSummary.model_validate(applicant)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/applicants/{applicant_id}", response_model=ApplicantSummary)
def update_applicant(
    applicant_id: UUID,
    payload: ApplicantUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> ApplicantSummary:
    """Update one applicant record for the authenticated tenant."""

    service = AdmissionsService(session, actor)
    try:
        applicant = service.update_applicant(applicant_id, payload)
        if applicant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant not found")
        session.commit()
        return ApplicantSummary.model_validate(applicant)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/applications", response_model=ApplicationListResponse)
def list_applications(
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    campaign_id: OptionalCampaignId = None,
    applicant_id: OptionalApplicantId = None,
    state: OptionalApplicationState = None,
) -> ApplicationListResponse:
    """Return applications with optional campaign, applicant, and state filters."""

    items, total = service.list_applications(skip, limit, campaign_id, applicant_id, state)
    return ApplicationListResponse(
        items=[ApplicationSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/applications/{application_id}", response_model=ApplicationSummary)
def get_application(
    application_id: UUID,
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
) -> ApplicationSummary:
    """Return one application by ID for the authenticated tenant."""

    application = service.get_application(application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return ApplicationSummary.model_validate(application)


@router.get("/applications/{application_id}/detail", response_model=ApplicationDetailResponse)
def get_application_detail(
    application_id: UUID,
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
) -> ApplicationDetailResponse:
    """Return one application with applicant identity and submitted documents."""

    detail = service.get_application_detail(application_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    application, applicant, documents = detail
    return ApplicationDetailResponse(
        application=ApplicationSummary.model_validate(application),
        applicant=ApplicantSummary.model_validate(applicant),
        documents=[ApplicationDocumentSummary.model_validate(item) for item in documents],
    )


@router.get(
    "/applications/{application_id}/history",
    response_model=list[AdmissionsHistoryEntry],
)
def get_application_history(
    application_id: UUID,
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
) -> list[AdmissionsHistoryEntry]:
    """Return append-only application and document workflow history."""

    history = service.get_application_history(application_id)
    if history is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return [AdmissionsHistoryEntry.model_validate(item, from_attributes=True) for item in history]


@router.post("/applications", response_model=ApplicationSummary, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> ApplicationSummary:
    """Create one application after validating all tenant-scoped parent references."""

    service = AdmissionsService(session, actor)
    try:
        application = service.create_application(payload)
        session.commit()
        return ApplicationSummary.model_validate(application)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/applications/{application_id}", response_model=ApplicationSummary)
def update_application(
    application_id: UUID,
    payload: ApplicationUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> ApplicationSummary:
    """Update mutable application fields for the authenticated tenant."""

    service = AdmissionsService(session, actor)
    try:
        application = service.update_application(application_id, payload)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        session.commit()
        return ApplicationSummary.model_validate(application)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/applications/{application_id}/transition", response_model=ApplicationSummary)
def transition_application_state(
    application_id: UUID,
    payload: ApplicationStateTransition,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.approve"))],
) -> ApplicationSummary:
    """Transition an application lifecycle state using controlled state-machine rules."""

    service = AdmissionsService(session, actor)
    try:
        application = service.transition_application_state(application_id, payload)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        session.commit()
        return ApplicationSummary.model_validate(application)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/documents", response_model=ApplicationDocumentListResponse)
def list_documents(
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    application_id: OptionalApplicationId = None,
) -> ApplicationDocumentListResponse:
    """Return documents with optional application filter for the tenant."""

    items, total = service.list_documents(skip, limit, application_id)
    return ApplicationDocumentListResponse(
        items=[ApplicationDocumentSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/documents/{document_id}", response_model=ApplicationDocumentSummary)
def get_document(
    document_id: UUID,
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
) -> ApplicationDocumentSummary:
    """Return one application document by ID for the authenticated tenant."""

    document = service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return ApplicationDocumentSummary.model_validate(document)


@router.post("/documents", response_model=ApplicationDocumentSummary, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: ApplicationDocumentCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> ApplicationDocumentSummary:
    """Create one application document for the authenticated tenant."""

    service = AdmissionsService(session, actor)
    try:
        document = service.create_document(payload)
        session.commit()
        return ApplicationDocumentSummary.model_validate(document)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/documents/{document_id}", response_model=ApplicationDocumentSummary)
def update_document(
    document_id: UUID,
    payload: ApplicationDocumentUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> ApplicationDocumentSummary:
    """Update mutable document fields for the authenticated tenant."""

    service = AdmissionsService(session, actor)
    try:
        document = service.update_document(document_id, payload)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        session.commit()
        return ApplicationDocumentSummary.model_validate(document)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/documents/{document_id}/transition", response_model=ApplicationDocumentSummary)
def transition_document_verification(
    document_id: UUID,
    payload: ApplicationDocumentVerificationTransition,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.approve"))],
) -> ApplicationDocumentSummary:
    """Transition a document verification state for the authenticated tenant."""

    service = AdmissionsService(session, actor)
    try:
        document = service.transition_document_verification(document_id, payload)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        session.commit()
        return ApplicationDocumentSummary.model_validate(document)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/seat-pools", response_model=SeatPoolListResponse)
def list_seat_pools(
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    campaign_id: OptionalCampaignId = None,
) -> SeatPoolListResponse:
    """Return tenant seat pools with optional campaign filtering."""

    items, total = service.list_seat_pools(skip, limit, campaign_id)
    return SeatPoolListResponse(
        items=[SeatPoolSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/seat-pools/{seat_pool_id}", response_model=SeatPoolSummary)
def get_seat_pool(
    seat_pool_id: UUID,
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
) -> SeatPoolSummary:
    """Return one seat pool by ID for the authenticated tenant."""

    seat_pool = service.get_seat_pool(seat_pool_id)
    if seat_pool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat pool not found")
    return SeatPoolSummary.model_validate(seat_pool)


@router.post("/seat-pools", response_model=SeatPoolSummary, status_code=status.HTTP_201_CREATED)
def create_seat_pool(
    payload: SeatPoolCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> SeatPoolSummary:
    """Create one seat pool for the authenticated tenant."""

    service = AdmissionsService(session, actor)
    try:
        seat_pool = service.create_seat_pool(payload)
        session.commit()
        return SeatPoolSummary.model_validate(seat_pool)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/seat-pools/{seat_pool_id}", response_model=SeatPoolSummary)
def update_seat_pool(
    seat_pool_id: UUID,
    payload: SeatPoolUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> SeatPoolSummary:
    """Update one seat pool for the authenticated tenant."""

    service = AdmissionsService(session, actor)
    try:
        seat_pool = service.update_seat_pool(seat_pool_id, payload)
        if seat_pool is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat pool not found")
        session.commit()
        return SeatPoolSummary.model_validate(seat_pool)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/offers", response_model=AdmissionOfferListResponse)
def list_offers(
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    application_id: OptionalApplicationId = None,
    state: OptionalOfferState = None,
) -> AdmissionOfferListResponse:
    """Return admission offers with optional application and state filters."""

    items, total = service.list_offers(skip, limit, application_id, state)
    return AdmissionOfferListResponse(
        items=[AdmissionOfferSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/offers/{offer_id}", response_model=AdmissionOfferSummary)
def get_offer(
    offer_id: UUID,
    service: Annotated[AdmissionsService, Depends(get_admissions_service)],
) -> AdmissionOfferSummary:
    """Return one admission offer by ID for the authenticated tenant."""

    offer = service.get_offer(offer_id)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    return AdmissionOfferSummary.model_validate(offer)


@router.post("/offers", response_model=AdmissionOfferSummary, status_code=status.HTTP_201_CREATED)
def create_offer(
    payload: AdmissionOfferCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.approve"))],
) -> AdmissionOfferSummary:
    """Issue one offer for a selected application within the tenant context."""

    service = AdmissionsService(session, actor)
    try:
        offer = service.create_offer(payload)
        session.commit()
        return AdmissionOfferSummary.model_validate(offer)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/offers/{offer_id}", response_model=AdmissionOfferSummary)
def update_offer(
    offer_id: UUID,
    payload: AdmissionOfferUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.manage"))],
) -> AdmissionOfferSummary:
    """Update mutable offer details for the authenticated tenant."""

    service = AdmissionsService(session, actor)
    try:
        offer = service.update_offer(offer_id, payload)
        if offer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
        session.commit()
        return AdmissionOfferSummary.model_validate(offer)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/offers/{offer_id}/transition", response_model=AdmissionOfferSummary)
def transition_offer_state(
    offer_id: UUID,
    payload: AdmissionOfferStateTransition,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.approve"))],
) -> AdmissionOfferSummary:
    """Transition an offer state, including atomic acceptance with seat allocation."""

    service = AdmissionsService(session, actor)
    try:
        offer = service.transition_offer_state(offer_id, payload)
        if offer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
        session.commit()
        return AdmissionOfferSummary.model_validate(offer)
    except AdmissionsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)