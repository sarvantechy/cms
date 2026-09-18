"""FastAPI routes for tenant-safe faculty delivery and timetable workflows."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import runtime_session_factory
from app.domains.delivery.schemas import (
    ClassSessionCreate,
    ClassSessionGenerateRequest,
    ClassSessionGenerateResponse,
    ClassSessionSummary,
    ClassSessionUpdate,
    ClassSubstitutionCreate,
    ClassSubstitutionSummary,
    DepartmentPostingCreate,
    DepartmentPostingSummary,
    FacultyAllocationCreate,
    FacultyAllocationSummary,
    FacultyAllocationUpdate,
    FacultyProfileCreate,
    FacultyProfileSummary,
    FacultyProfileUpdate,
    LearningMaterialCreate,
    LearningMaterialSummary,
    LessonPlanCreate,
    LessonPlanSummary,
    PaginatedClassSessions,
    PaginatedFacultyAllocations,
    PaginatedFacultyProfiles,
    PaginatedStudentLearningMaterials,
    PaginatedSubjectOfferings,
    PaginatedTimetablePeriods,
    PaginatedTimetablePublications,
    StudentLearningMaterialSummary,
    SubjectOfferingCreate,
    SubjectOfferingSummary,
    SubjectOfferingUpdate,
    SyllabusProgressCreate,
    SyllabusProgressSummary,
    TimetablePeriodCreate,
    TimetablePeriodSummary,
    TimetablePeriodUpdate,
    TimetablePublicationCreate,
    TimetablePublicationDetail,
    TimetablePublicationLineSummary,
    TimetablePublicationSummary,
)
from app.domains.delivery.service import DeliveryDomainError, DeliveryService
from app.domains.identity.router import require_permission
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/delivery", tags=["Delivery"])

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


def get_delivery_service(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("timetable.read"))],
) -> DeliveryService:
    """Build a delivery service for read operations under tenant-safe authorization."""

    return DeliveryService(session, actor)


def _raise_domain_error(error: DeliveryDomainError) -> None:
    """Translate service-level domain errors into stable HTTP API failures."""

    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _raise_conflict(error: IntegrityError) -> None:
    """Translate relational uniqueness and integrity failures into HTTP 409."""

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Record conflicts with existing data",
    ) from error


@router.get("/faculty", response_model=PaginatedFacultyProfiles)
def list_faculty_profiles(
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedFacultyProfiles:
    """Return a paginated list of faculty profiles for the authenticated tenant."""

    items, total = service.list_faculty_profiles(skip=skip, limit=limit)
    return PaginatedFacultyProfiles(
        items=[FacultyProfileSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/faculty/{faculty_id}", response_model=FacultyProfileSummary)
def get_faculty_profile(
    faculty_id: UUID,
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
) -> FacultyProfileSummary:
    """Return one faculty profile by ID for the authenticated tenant."""

    item = service.get_faculty_profile(faculty_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty profile not found")
    return FacultyProfileSummary.model_validate(item)


@router.post("/faculty", response_model=FacultyProfileSummary, status_code=status.HTTP_201_CREATED)
def create_faculty_profile(
    payload: FacultyProfileCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("faculty.delivery.manage"))],
) -> FacultyProfileSummary:
    """Create one faculty profile for the authenticated tenant."""

    service = DeliveryService(session, actor)
    try:
        item = service.create_faculty_profile(payload)
        response = FacultyProfileSummary.model_validate(item)
        session.commit()
        return response
    except DeliveryDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/faculty/{faculty_id}", response_model=FacultyProfileSummary)
def update_faculty_profile(
    faculty_id: UUID,
    payload: FacultyProfileUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("faculty.delivery.manage"))],
) -> FacultyProfileSummary:
    """Update mutable faculty profile fields."""

    service = DeliveryService(session, actor)
    try:
        item = service.update_faculty_profile(faculty_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty profile not found")
        response = FacultyProfileSummary.model_validate(item)
        session.commit()
        return response
    except DeliveryDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/offerings", response_model=PaginatedSubjectOfferings)
def list_subject_offerings(
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedSubjectOfferings:
    """Return a paginated list of subject offerings for the authenticated tenant."""

    items, total = service.list_subject_offerings(skip=skip, limit=limit)
    return PaginatedSubjectOfferings(
        items=[SubjectOfferingSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/offerings/{offering_id}", response_model=SubjectOfferingSummary)
def get_subject_offering(
    offering_id: UUID,
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
) -> SubjectOfferingSummary:
    """Return one subject offering by ID for the authenticated tenant."""

    item = service.get_subject_offering(offering_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject offering not found")
    return SubjectOfferingSummary.model_validate(item)


@router.post("/offerings", response_model=SubjectOfferingSummary, status_code=status.HTTP_201_CREATED)
def create_subject_offering(
    payload: SubjectOfferingCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("timetable.manage"))],
) -> SubjectOfferingSummary:
    """Create one subject offering for the authenticated tenant."""

    service = DeliveryService(session, actor)
    try:
        item = service.create_subject_offering(payload)
        response = SubjectOfferingSummary.model_validate(item)
        session.commit()
        return response
    except DeliveryDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/offerings/{offering_id}", response_model=SubjectOfferingSummary)
def update_subject_offering(
    offering_id: UUID,
    payload: SubjectOfferingUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("timetable.manage"))],
) -> SubjectOfferingSummary:
    """Update one subject offering status."""

    service = DeliveryService(session, actor)
    try:
        item = service.update_subject_offering(offering_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject offering not found")
        response = SubjectOfferingSummary.model_validate(item)
        session.commit()
        return response
    except DeliveryDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/allocations", response_model=PaginatedFacultyAllocations)
def list_faculty_allocations(
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedFacultyAllocations:
    """Return a paginated list of faculty allocations."""

    items, total = service.list_faculty_allocations(skip=skip, limit=limit)
    return PaginatedFacultyAllocations(
        items=[FacultyAllocationSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/allocations/{allocation_id}", response_model=FacultyAllocationSummary)
def get_faculty_allocation(
    allocation_id: UUID,
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
) -> FacultyAllocationSummary:
    """Return one faculty allocation by ID for the authenticated tenant."""

    item = service.get_faculty_allocation(allocation_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty allocation not found")
    return FacultyAllocationSummary.model_validate(item)


@router.post("/allocations", response_model=FacultyAllocationSummary, status_code=status.HTTP_201_CREATED)
def create_faculty_allocation(
    payload: FacultyAllocationCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("faculty.delivery.manage"))],
) -> FacultyAllocationSummary:
    """Create one faculty allocation for the authenticated tenant."""

    service = DeliveryService(session, actor)
    try:
        item = service.create_faculty_allocation(payload)
        response = FacultyAllocationSummary.model_validate(item)
        session.commit()
        return response
    except DeliveryDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/allocations/{allocation_id}", response_model=FacultyAllocationSummary)
def update_faculty_allocation(
    allocation_id: UUID,
    payload: FacultyAllocationUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("faculty.delivery.manage"))],
) -> FacultyAllocationSummary:
    """Update one faculty allocation status."""

    service = DeliveryService(session, actor)
    try:
        item = service.update_faculty_allocation(allocation_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty allocation not found")
        response = FacultyAllocationSummary.model_validate(item)
        session.commit()
        return response
    except DeliveryDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/periods", response_model=PaginatedTimetablePeriods)
def list_timetable_periods(
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedTimetablePeriods:
    """Return a paginated list of timetable periods for the tenant."""

    items, total = service.list_timetable_periods(skip=skip, limit=limit)
    return PaginatedTimetablePeriods(
        items=[TimetablePeriodSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/periods/{period_id}", response_model=TimetablePeriodSummary)
def get_timetable_period(
    period_id: UUID,
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
) -> TimetablePeriodSummary:
    """Return one timetable period by ID for the authenticated tenant."""

    item = service.get_timetable_period(period_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timetable period not found")
    return TimetablePeriodSummary.model_validate(item)


@router.post("/periods", response_model=TimetablePeriodSummary, status_code=status.HTTP_201_CREATED)
def create_timetable_period(
    payload: TimetablePeriodCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("timetable.manage"))],
) -> TimetablePeriodSummary:
    """Create one timetable period with conflict checks for faculty and rooms."""

    service = DeliveryService(session, actor)
    try:
        item = service.create_timetable_period(payload)
        response = TimetablePeriodSummary.model_validate(item)
        session.commit()
        return response
    except DeliveryDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/periods/{period_id}", response_model=TimetablePeriodSummary)
def update_timetable_period(
    period_id: UUID,
    payload: TimetablePeriodUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("timetable.manage"))],
) -> TimetablePeriodSummary:
    """Update one timetable period while preserving conflict guarantees."""

    service = DeliveryService(session, actor)
    try:
        item = service.update_timetable_period(period_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timetable period not found")
        response = TimetablePeriodSummary.model_validate(item)
        session.commit()
        return response
    except DeliveryDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/timetable-publications", response_model=PaginatedTimetablePublications)
def list_timetable_publications(
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedTimetablePublications:
    """Return versioned timetable publications visible to the actor."""

    items, total = service.list_timetable_publications(skip=skip, limit=limit)
    return PaginatedTimetablePublications(
        items=[TimetablePublicationSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get(
    "/timetable-publications/{publication_id}",
    response_model=TimetablePublicationDetail,
)
def get_timetable_publication(
    publication_id: UUID,
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
) -> TimetablePublicationDetail:
    """Return one visible timetable publication with immutable snapshot lines."""

    result = service.get_timetable_publication(publication_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timetable publication not found",
        )
    publication, lines = result
    return TimetablePublicationDetail(
        **TimetablePublicationSummary.model_validate(publication).model_dump(),
        lines=[TimetablePublicationLineSummary.model_validate(line) for line in lines],
    )


@router.post(
    "/timetable-publications",
    response_model=TimetablePublicationDetail,
    status_code=status.HTTP_201_CREATED,
)
def publish_timetable(
    payload: TimetablePublicationCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("timetable.manage"))],
) -> TimetablePublicationDetail:
    """Publish a new immutable timetable version for the actor's scope."""

    service = DeliveryService(session, actor)
    try:
        publication, lines = service.publish_timetable(payload)
        response = TimetablePublicationDetail(
            **TimetablePublicationSummary.model_validate(publication).model_dump(),
            lines=[TimetablePublicationLineSummary.model_validate(line) for line in lines],
        )
        session.commit()
        return response
    except DeliveryDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/sessions", response_model=PaginatedClassSessions)
def list_class_sessions(
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    period_id: UUID | None = None,
) -> PaginatedClassSessions:
    """Return a paginated list of class sessions with optional period filter."""

    items, total = service.list_class_sessions(skip=skip, limit=limit, period_id=period_id)
    return PaginatedClassSessions(
        items=[ClassSessionSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/sessions/{session_id}", response_model=ClassSessionSummary)
def get_class_session(
    session_id: UUID,
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
) -> ClassSessionSummary:
    """Return one class session by ID for the authenticated tenant."""

    item = service.get_class_session(session_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class session not found")
    return ClassSessionSummary.model_validate(item)


@router.post("/sessions", response_model=ClassSessionSummary, status_code=status.HTTP_201_CREATED)
def create_class_session(
    payload: ClassSessionCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("faculty.delivery.manage"))],
) -> ClassSessionSummary:
    """Create one class session manually for the authenticated tenant."""

    service = DeliveryService(session, actor)
    try:
        item = service.create_class_session(payload)
        response = ClassSessionSummary.model_validate(item)
        session.commit()
        return response
    except DeliveryDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/sessions/{session_id}", response_model=ClassSessionSummary)
def update_class_session(
    session_id: UUID,
    payload: ClassSessionUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("faculty.delivery.manage"))],
) -> ClassSessionSummary:
    """Update one class session state for the authenticated tenant."""

    service = DeliveryService(session, actor)
    try:
        item = service.update_class_session(session_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class session not found")
        response = ClassSessionSummary.model_validate(item)
        session.commit()
        return response
    except DeliveryDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/sessions/generate", response_model=ClassSessionGenerateResponse)
def generate_class_sessions(
    payload: ClassSessionGenerateRequest,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("timetable.manage"))],
) -> ClassSessionGenerateResponse:
    """Generate class sessions for an inclusive date range using active timetable periods."""

    service = DeliveryService(session, actor)
    try:
        created_count, session_ids = service.generate_class_sessions(payload)
        session.commit()
        return ClassSessionGenerateResponse(created_count=created_count, session_ids=session_ids)
    except DeliveryDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/postings", response_model=list[DepartmentPostingSummary])
def list_department_postings(
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
) -> list[DepartmentPostingSummary]:
    """List effective-dated faculty department postings."""

    items, _ = service.list_department_postings(limit=200)
    return [DepartmentPostingSummary.model_validate(item) for item in items]


@router.post("/postings", response_model=DepartmentPostingSummary, status_code=status.HTTP_201_CREATED)
def create_department_posting(
    payload: DepartmentPostingCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("faculty.delivery.manage"))],
) -> DepartmentPostingSummary:
    """Create one effective-dated faculty department posting."""

    item = DeliveryService(session, actor).create_department_posting(payload)
    response = DepartmentPostingSummary.model_validate(item)
    session.commit()
    return response


@router.get("/substitutions", response_model=list[ClassSubstitutionSummary])
def list_substitutions(
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
) -> list[ClassSubstitutionSummary]:
    """List class-session substitution requests."""

    items, _ = service.list_substitutions(limit=200)
    return [ClassSubstitutionSummary.model_validate(item) for item in items]


@router.post("/substitutions", response_model=ClassSubstitutionSummary, status_code=status.HTTP_201_CREATED)
def create_substitution(
    payload: ClassSubstitutionCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("timetable.manage"))],
) -> ClassSubstitutionSummary:
    """Create one class-session substitution request."""

    item = DeliveryService(session, actor).create_substitution(payload)
    response = ClassSubstitutionSummary.model_validate(item)
    session.commit()
    return response


@router.get("/lesson-plans", response_model=list[LessonPlanSummary])
def list_lesson_plans(
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
) -> list[LessonPlanSummary]:
    """List dated lesson plans for the active tenant."""

    items, _ = service.list_lesson_plans(limit=200)
    return [LessonPlanSummary.model_validate(item) for item in items]


@router.post("/lesson-plans", response_model=LessonPlanSummary, status_code=status.HTTP_201_CREATED)
def create_lesson_plan(
    payload: LessonPlanCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("faculty.delivery.manage"))],
) -> LessonPlanSummary:
    """Create one dated lesson plan."""

    item = DeliveryService(session, actor).create_lesson_plan(payload)
    response = LessonPlanSummary.model_validate(item)
    session.commit()
    return response


@router.get("/materials", response_model=list[LearningMaterialSummary])
def list_learning_materials(
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
) -> list[LearningMaterialSummary]:
    """List learning material references for the active tenant."""

    items, _ = service.list_learning_materials(limit=200)
    return [LearningMaterialSummary.model_validate(item) for item in items]


@router.get("/student-learning-materials", response_model=PaginatedStudentLearningMaterials)
def list_student_learning_materials(
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedStudentLearningMaterials:
    """Return scoped learning resources with readable course context."""

    rows, total = service.list_student_learning_materials(skip=skip, limit=limit)
    items = [
        StudentLearningMaterialSummary(
            id=row.LearningMaterial.id,
            offering_id=row.LearningMaterial.offering_id,
            title=row.LearningMaterial.title,
            material_type=row.LearningMaterial.material_type,
            resource_url=row.LearningMaterial.resource_url,
            description=row.LearningMaterial.description,
            subject_code=row.subject_code,
            subject_name=row.subject_name,
            section_code=row.section_code,
            section_name=row.section_name,
            term_code=row.term_code,
            term_name=row.term_name,
            faculty_employee_code=row.faculty_employee_code,
        )
        for row in rows
    ]
    return PaginatedStudentLearningMaterials(items=items, total=total)


@router.post("/materials", response_model=LearningMaterialSummary, status_code=status.HTTP_201_CREATED)
def create_learning_material(
    payload: LearningMaterialCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("faculty.delivery.manage"))],
) -> LearningMaterialSummary:
    """Create one learning material reference."""

    item = DeliveryService(session, actor).create_learning_material(payload)
    response = LearningMaterialSummary.model_validate(item)
    session.commit()
    return response


@router.get("/syllabus-progress", response_model=list[SyllabusProgressSummary])
def list_syllabus_progress(
    service: Annotated[DeliveryService, Depends(get_delivery_service)],
) -> list[SyllabusProgressSummary]:
    """List dated syllabus completion records for the active tenant."""

    items, _ = service.list_syllabus_progress(limit=200)
    return [SyllabusProgressSummary.model_validate(item) for item in items]


@router.post("/syllabus-progress", response_model=SyllabusProgressSummary, status_code=status.HTTP_201_CREATED)
def create_syllabus_progress(
    payload: SyllabusProgressCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("faculty.delivery.manage"))],
) -> SyllabusProgressSummary:
    """Create one dated syllabus completion record."""

    item = DeliveryService(session, actor).create_syllabus_progress(payload)
    response = SyllabusProgressSummary.model_validate(item)
    session.commit()
    return response
