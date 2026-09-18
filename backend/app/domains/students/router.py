"""FastAPI routes for tenant-safe student records, guardian links, and admissions conversion."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import runtime_session_factory
from app.domains.identity.router import require_actor, require_permission
from app.domains.students.schemas import (
    PersonListResponse,
    PersonSummary,
    StudentCertificateDecision,
    StudentCertificateDocument,
    StudentCertificateRequestCreate,
    StudentCertificateRequestSummary,
    StudentConversionFromApplication,
    StudentCreate,
    StudentDetailResponse,
    StudentDocumentCreate,
    StudentDocumentReview,
    StudentDocumentSummary,
    StudentEnrollmentCreate,
    StudentEnrollmentSummary,
    StudentGuardianLinkCreate,
    StudentGuardianSummary,
    StudentLifecycleDecision,
    StudentLifecycleRequestCreate,
    StudentLifecycleRequestSummary,
    StudentLifecycleResponse,
    StudentListResponse,
    StudentProgressionCreate,
    StudentProgressionDecision,
    StudentProgressionSummary,
    StudentStatusHistorySummary,
    StudentStatusTransition,
    StudentSubjectRegistrationCreate,
    StudentSubjectRegistrationDecision,
    StudentSubjectRegistrationSummary,
    StudentSummary,
    StudentUpdate,
)
from app.domains.students.service import StudentsDomainError, StudentsService
from app.media_storage import MAX_MEDIA_BYTES, LocalMediaStorage, MediaValidationError
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/students", tags=["Students"])

PaginationSkip = Annotated[int, Query(ge=0)]
PaginationLimit = Annotated[int, Query(ge=1, le=200)]
OptionalStudentStatus = Annotated[str | None, Query(max_length=16)]
OptionalStudentSearch = Annotated[str | None, Query(min_length=1, max_length=240)]
STUDENT_NOT_FOUND = "Student not found"


def get_runtime_session() -> Generator[Session, None, None]:
    """Yield a restricted runtime session with explicit route-level commit control."""

    with runtime_session_factory()() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


def get_students_service(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.read"))],
) -> StudentsService:
    """Build a students service for read operations under tenant-bound authorization."""

    return StudentsService(session, actor)


def _raise_domain_error(error: StudentsDomainError) -> None:
    """Translate service-level domain errors into stable HTTP API failures."""

    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _raise_conflict(error: IntegrityError) -> None:
    """Translate relational uniqueness and integrity failures into HTTP 409."""

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Record conflicts with existing data",
    ) from error


@router.get("", response_model=StudentListResponse)
def list_students(
    service: Annotated[StudentsService, Depends(get_students_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    status_value: OptionalStudentStatus = None,
    search: OptionalStudentSearch = None,
) -> StudentListResponse:
    """Return a paginated list of students for the authenticated tenant."""

    items, total = service.list_students(skip=skip, limit=limit, status=status_value, search=search)
    return StudentListResponse(
        items=[StudentSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/people", response_model=PersonListResponse)
def list_people(
    service: Annotated[StudentsService, Depends(get_students_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PersonListResponse:
    """Return canonical tenant people for authorized assignment forms."""

    items, total = service.list_people(skip=skip, limit=limit)
    return PersonListResponse(
        items=[PersonSummary.model_validate(item) for item in items], total=total
    )


@router.get("/me", response_model=StudentListResponse)
def list_own_students(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.own.read"))],
) -> StudentListResponse:
    """Return students explicitly assigned to the actor's own-record scope."""

    items, total = StudentsService(session, actor).list_scoped_students("own_record")
    return StudentListResponse(
        items=[StudentSummary.model_validate(item) for item in items], total=total
    )


@router.get("/linked", response_model=StudentListResponse)
def list_linked_students(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.linked.read"))],
) -> StudentListResponse:
    """Return students explicitly assigned to the actor's guardian link scopes."""

    items, total = StudentsService(session, actor).list_scoped_students("linked_student")
    return StudentListResponse(
        items=[StudentSummary.model_validate(item) for item in items], total=total
    )


@router.get("/{student_id}", response_model=StudentSummary)
def get_student(
    student_id: UUID,
    service: Annotated[StudentsService, Depends(get_students_service)],
) -> StudentSummary:
    """Return one student by ID for the authenticated tenant."""

    student = service.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=STUDENT_NOT_FOUND)
    return StudentSummary.model_validate(student)


@router.get("/{student_id}/detail", response_model=StudentDetailResponse)
def get_student_detail(
    student_id: UUID,
    service: Annotated[StudentsService, Depends(get_students_service)],
) -> StudentDetailResponse:
    """Return one student profile with guardians, enrollments, and lifecycle history."""

    detail = service.get_student_detail(student_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=STUDENT_NOT_FOUND)
    student, guardians, enrollments, history = detail
    return StudentDetailResponse(
        student=StudentSummary.model_validate(student),
        guardians=[StudentGuardianSummary.model_validate(link) for link in guardians],
        enrollments=[StudentEnrollmentSummary.model_validate(item) for item in enrollments],
        status_history=[StudentStatusHistorySummary.model_validate(item) for item in history],
    )


@router.post("", response_model=StudentSummary, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentSummary:
    """Create one student record with nested person identity details."""

    service = StudentsService(session, actor)
    try:
        student = service.create_student(payload)
        response = StudentSummary.model_validate(student)
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/{student_id}", response_model=StudentSummary)
def update_student(
    student_id: UUID,
    payload: StudentUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentSummary:
    """Update mutable student record and person identity fields."""

    service = StudentsService(session, actor)
    try:
        student = service.update_student(student_id, payload)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=STUDENT_NOT_FOUND)
        response = StudentSummary.model_validate(student)
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post(
    "/{student_id}/guardians",
    response_model=StudentGuardianSummary,
    status_code=status.HTTP_201_CREATED,
)
def link_guardian(
    student_id: UUID,
    payload: StudentGuardianLinkCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentGuardianSummary:
    """Create or link a guardian record to a student with relationship metadata."""

    service = StudentsService(session, actor)
    try:
        link = service.create_or_link_guardian(student_id, payload)
        response = StudentGuardianSummary.model_validate(link)
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post(
    "/{student_id}/enrollments",
    response_model=StudentEnrollmentSummary,
    status_code=status.HTTP_201_CREATED,
)
def enroll_student(
    student_id: UUID,
    payload: StudentEnrollmentCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentEnrollmentSummary:
    """Create one enrollment record for the specified student."""

    service = StudentsService(session, actor)
    try:
        enrollment = service.enroll_student(student_id, payload)
        response = StudentEnrollmentSummary.model_validate(enrollment)
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/{student_id}/transition", response_model=StudentStatusHistorySummary)
def transition_student_status(
    student_id: UUID,
    payload: StudentStatusTransition,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentStatusHistorySummary:
    """Transition one student lifecycle status and persist history."""

    service = StudentsService(session, actor)
    try:
        history = service.transition_student_status(student_id, payload)
        if history is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=STUDENT_NOT_FOUND)
        response = StudentStatusHistorySummary.model_validate(history)
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/{student_id}/lifecycle", response_model=StudentLifecycleResponse)
def get_student_lifecycle(
    student_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_actor)],
) -> StudentLifecycleResponse:
    """Return lifecycle records under management, own-record, or linked-student scope."""

    try:
        documents, registrations, progressions, requests, certificates = StudentsService(
            session, actor
        ).get_student_lifecycle(student_id)
        return StudentLifecycleResponse(
            documents=[StudentDocumentSummary.model_validate(item) for item in documents],
            subject_registrations=[
                StudentSubjectRegistrationSummary.model_validate(item) for item in registrations
            ],
            progressions=[StudentProgressionSummary.model_validate(item) for item in progressions],
            lifecycle_requests=[
                StudentLifecycleRequestSummary.model_validate(item) for item in requests
            ],
            certificate_requests=[
                StudentCertificateRequestSummary.model_validate(item) for item in certificates
            ],
        )
    except StudentsDomainError as error:
        _raise_domain_error(error)


@router.post(
    "/{student_id}/documents",
    response_model=StudentDocumentSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_student_document(
    student_id: UUID,
    payload: StudentDocumentCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentDocumentSummary:
    """Create one student document metadata record for later verification."""

    try:
        response = StudentDocumentSummary.model_validate(
            StudentsService(session, actor).create_document(student_id, payload)
        )
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post(
    "/{student_id}/documents/upload",
    response_model=StudentDocumentSummary,
    status_code=status.HTTP_201_CREATED,
)
async def upload_student_document(
    student_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
    category: Annotated[str, Form(min_length=1, max_length=48)],
    title: Annotated[str, Form(min_length=1, max_length=160)],
    file: Annotated[UploadFile, File()],
    document_number: Annotated[str | None, Form(max_length=80)] = None,
    notes: Annotated[str | None, Form()] = None,
) -> StudentDocumentSummary:
    """Privately store and attach one validated student document."""

    storage = LocalMediaStorage()
    stored = None
    try:
        content = await file.read(MAX_MEDIA_BYTES + 1)
        stored = storage.store(actor.tenant_id, content, file.content_type or "")
        payload = StudentDocumentCreate(
            category=category,
            title=title,
            document_number=document_number,
            reference_url=None,
            issued_on=None,
            expires_on=None,
            notes=notes,
        )
        item = StudentsService(session, actor).create_uploaded_document(
            student_id,
            payload,
            file.filename or "upload",
            file.content_type or "application/octet-stream",
            stored,
        )
        response = StudentDocumentSummary.model_validate(item)
        session.commit()
        return response
    except MediaValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except StudentsDomainError as error:
        if stored is not None:
            storage.delete(stored.object_key)
        _raise_domain_error(error)
    except IntegrityError as error:
        if stored is not None:
            storage.delete(stored.object_key)
        _raise_conflict(error)


@router.get("/documents/{document_id}/content", response_class=FileResponse)
def download_student_document(
    document_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_actor)],
) -> FileResponse:
    """Download private student media when existing record scopes authorize it."""

    try:
        result = StudentsService(session, actor).get_document_media(document_id)
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
    except StudentsDomainError as error:
        _raise_domain_error(error)


@router.patch("/documents/{document_id}", response_model=StudentDocumentSummary)
def review_student_document(
    document_id: UUID,
    payload: StudentDocumentReview,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentDocumentSummary:
    """Verify or reject one pending student document."""

    try:
        response = StudentDocumentSummary.model_validate(
            StudentsService(session, actor).review_document(document_id, payload)
        )
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)


@router.post(
    "/{student_id}/subject-registrations",
    response_model=StudentSubjectRegistrationSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_subject_registration(
    student_id: UUID,
    payload: StudentSubjectRegistrationCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentSubjectRegistrationSummary:
    """Register one active student enrollment into a compatible offering."""

    try:
        response = StudentSubjectRegistrationSummary.model_validate(
            StudentsService(session, actor).register_subject(student_id, payload)
        )
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch(
    "/subject-registrations/{registration_id}", response_model=StudentSubjectRegistrationSummary
)
def transition_subject_registration(
    registration_id: UUID,
    payload: StudentSubjectRegistrationDecision,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentSubjectRegistrationSummary:
    """Drop or complete one active subject registration."""

    try:
        response = StudentSubjectRegistrationSummary.model_validate(
            StudentsService(session, actor).transition_subject_registration(
                registration_id, payload
            )
        )
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)


@router.post(
    "/{student_id}/progressions",
    response_model=StudentProgressionSummary,
    status_code=status.HTTP_201_CREATED,
)
def prepare_student_progression(
    student_id: UUID,
    payload: StudentProgressionCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentProgressionSummary:
    """Prepare one student progression target for review."""

    try:
        response = StudentProgressionSummary.model_validate(
            StudentsService(session, actor).prepare_progression(student_id, payload)
        )
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/progressions/{progression_id}", response_model=StudentProgressionSummary)
def decide_student_progression(
    progression_id: UUID,
    payload: StudentProgressionDecision,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentProgressionSummary:
    """Approve, reject, or apply one prepared student progression."""

    try:
        response = StudentProgressionSummary.model_validate(
            StudentsService(session, actor).decide_progression(progression_id, payload)
        )
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post(
    "/{student_id}/lifecycle-requests",
    response_model=StudentLifecycleRequestSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_lifecycle_request(
    student_id: UUID,
    payload: StudentLifecycleRequestCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentLifecycleRequestSummary:
    """Create one transfer or readmission request."""

    try:
        response = StudentLifecycleRequestSummary.model_validate(
            StudentsService(session, actor).create_lifecycle_request(student_id, payload)
        )
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/lifecycle-requests/{request_id}", response_model=StudentLifecycleRequestSummary)
def decide_lifecycle_request(
    request_id: UUID,
    payload: StudentLifecycleDecision,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentLifecycleRequestSummary:
    """Approve, reject, or complete one transfer/readmission request."""

    try:
        response = StudentLifecycleRequestSummary.model_validate(
            StudentsService(session, actor).decide_lifecycle_request(request_id, payload)
        )
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post(
    "/{student_id}/certificate-requests",
    response_model=StudentCertificateRequestSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_certificate_request(
    student_id: UUID,
    payload: StudentCertificateRequestCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_actor)],
) -> StudentCertificateRequestSummary:
    """Create one staff-managed or own-student certificate request."""

    if not (
        actor.has_permission("students.records.manage") or actor.has_permission("students.own.read")
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    try:
        response = StudentCertificateRequestSummary.model_validate(
            StudentsService(session, actor).request_certificate(student_id, payload)
        )
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/certificate-requests/{request_id}", response_model=StudentCertificateRequestSummary)
def decide_certificate_request(
    request_id: UUID,
    payload: StudentCertificateDecision,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("students.records.manage"))],
) -> StudentCertificateRequestSummary:
    """Approve, reject, or issue one student certificate request."""

    try:
        response = StudentCertificateRequestSummary.model_validate(
            StudentsService(session, actor).decide_certificate_request(request_id, payload)
        )
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get(
    "/certificate-requests/{request_id}/document",
    response_model=StudentCertificateDocument,
)
def get_certificate_document(
    request_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_actor)],
) -> StudentCertificateDocument:
    """Return one issued Student certificate document within actor scope."""

    if not (
        actor.has_permission("students.records.read")
        or actor.has_permission("students.own.read")
        or actor.has_permission("students.linked.read")
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    try:
        document = StudentsService(session, actor).get_certificate_document(request_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
        return document
    except StudentsDomainError as error:
        _raise_domain_error(error)


@router.post(
    "/convert/{application_id}", response_model=StudentSummary, status_code=status.HTTP_201_CREATED
)
def convert_from_application(
    application_id: UUID,
    payload: StudentConversionFromApplication,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("admissions.applications.convert"))],
) -> StudentSummary:
    """Convert one accepted admissions application to student records atomically."""

    service = StudentsService(session, actor)
    try:
        student = service.convert_application_to_student(application_id, payload)
        response = StudentSummary.model_validate(student)
        session.commit()
        return response
    except StudentsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)
