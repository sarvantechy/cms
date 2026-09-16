"""FastAPI routes for tenant-safe examinations setup, marks workflow, and results."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import runtime_session_factory
from app.domains.examinations.schemas import (
    AssessmentSchemeCreate,
    AssessmentSchemeSummary,
    ExamRegistrationCreate,
    ExamRegistrationSummary,
    ExamScheduleCreate,
    ExamScheduleSummary,
    ExamSeatAllocationCreate,
    ExamSeatAllocationSummary,
    ExamSessionCreate,
    ExamSessionSummary,
    GradeRuleCreate,
    GradeRuleSummary,
    HallTicketSummary,
    InvigilationAssignmentCreate,
    InvigilationAssignmentSummary,
    MarkAdjustmentCreate,
    MarkAdjustmentReview,
    MarkAdjustmentSummary,
    MarkEntrySummary,
    MarkEntryUpsert,
    PaginatedAssessmentSchemes,
    PaginatedExamRegistrations,
    PaginatedExamSchedules,
    PaginatedExamSeatAllocations,
    PaginatedExamSessions,
    PaginatedGradeRules,
    PaginatedInvigilationAssignments,
    PaginatedMarkAdjustments,
    PaginatedPublishedResults,
    PublishedResultDetail,
    PublishedResultLineSummary,
    PublishedResultSummary,
    PublishResultsRequest,
    PublishResultsResponse,
    ResultPublicationEventSummary,
    ResultReopenRequest,
    TranscriptSummary,
)
from app.domains.examinations.service import (
    ExaminationsDomainError,
    ExaminationsService,
)
from app.domains.identity.router import require_permission
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/examinations", tags=["Examinations"])

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


def get_examinations_service(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.results.read"))],
) -> ExaminationsService:
    """Build an examinations service for read operations under tenant-safe authorization."""

    return ExaminationsService(session, actor)


def _raise_domain_error(error: ExaminationsDomainError) -> None:
    """Translate domain failures into deterministic API responses."""

    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _raise_conflict(error: IntegrityError) -> None:
    """Translate relational uniqueness and integrity failures into HTTP 409."""

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Record conflicts with existing data",
    ) from error


@router.get("/assessment-schemes", response_model=PaginatedAssessmentSchemes)
def list_assessment_schemes(
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedAssessmentSchemes:
    """Return a paginated list of assessment schemes for the authenticated tenant."""

    items, total = service.list_assessment_schemes(skip=skip, limit=limit)
    return PaginatedAssessmentSchemes(
        items=[AssessmentSchemeSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post(
    "/assessment-schemes",
    response_model=AssessmentSchemeSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment_scheme(
    payload: AssessmentSchemeCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.configuration.manage"))],
) -> AssessmentSchemeSummary:
    """Create one assessment scheme for the authenticated tenant."""

    service = ExaminationsService(session, actor)
    try:
        item = service.create_assessment_scheme(payload)
        response = AssessmentSchemeSummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/grade-rules", response_model=PaginatedGradeRules)
def list_grade_rules(
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedGradeRules:
    """Return versioned grade bands for the authenticated tenant."""

    items, total = service.list_grade_rules(skip=skip, limit=limit)
    return PaginatedGradeRules(items=[GradeRuleSummary.model_validate(item) for item in items], total=total)


@router.post("/grade-rules", response_model=GradeRuleSummary, status_code=status.HTTP_201_CREATED)
def create_grade_rule(
    payload: GradeRuleCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.configuration.manage"))],
) -> GradeRuleSummary:
    """Create one versioned grade band for the authenticated tenant."""

    service = ExaminationsService(session, actor)
    try:
        item = service.create_grade_rule(payload)
        response = GradeRuleSummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/sessions", response_model=PaginatedExamSessions)
def list_exam_sessions(
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedExamSessions:
    """Return a paginated list of exam sessions for the authenticated tenant."""

    items, total = service.list_exam_sessions(skip=skip, limit=limit)
    return PaginatedExamSessions(items=[ExamSessionSummary.model_validate(item) for item in items], total=total)


@router.post("/sessions", response_model=ExamSessionSummary, status_code=status.HTTP_201_CREATED)
def create_exam_session(
    payload: ExamSessionCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.configuration.manage"))],
) -> ExamSessionSummary:
    """Create one exam session for the authenticated tenant."""

    service = ExaminationsService(session, actor)
    try:
        item = service.create_exam_session(payload)
        response = ExamSessionSummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/schedules", response_model=PaginatedExamSchedules)
def list_exam_schedules(
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    session_id: UUID | None = None,
) -> PaginatedExamSchedules:
    """Return a paginated list of exam schedules for the authenticated tenant."""

    items, total = service.list_exam_schedules(skip=skip, limit=limit, session_id=session_id)
    return PaginatedExamSchedules(items=[ExamScheduleSummary.model_validate(item) for item in items], total=total)


@router.post("/schedules", response_model=ExamScheduleSummary, status_code=status.HTTP_201_CREATED)
def create_exam_schedule(
    payload: ExamScheduleCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.configuration.manage"))],
) -> ExamScheduleSummary:
    """Create one exam schedule for the authenticated tenant."""

    service = ExaminationsService(session, actor)
    try:
        item = service.create_exam_schedule(payload)
        response = ExamScheduleSummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/registrations", response_model=PaginatedExamRegistrations)
def list_exam_registrations(
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    schedule_id: UUID | None = None,
) -> PaginatedExamRegistrations:
    """Return a paginated list of exam registrations for the authenticated tenant."""

    items, total = service.list_exam_registrations(skip=skip, limit=limit, schedule_id=schedule_id)
    return PaginatedExamRegistrations(
        items=[ExamRegistrationSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post("/registrations", response_model=ExamRegistrationSummary, status_code=status.HTTP_201_CREATED)
def create_exam_registration(
    payload: ExamRegistrationCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.registrations.manage"))],
) -> ExamRegistrationSummary:
    """Create one exam registration for the authenticated tenant."""

    service = ExaminationsService(session, actor)
    try:
        item = service.create_exam_registration(payload)
        response = ExamRegistrationSummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/seats", response_model=PaginatedExamSeatAllocations)
def list_seat_allocations(
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedExamSeatAllocations:
    """Return examination seat allocations for the authenticated tenant."""

    items, total = service.list_seat_allocations(skip=skip, limit=limit)
    return PaginatedExamSeatAllocations(
        items=[ExamSeatAllocationSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post("/seats", response_model=ExamSeatAllocationSummary, status_code=status.HTTP_201_CREATED)
def allocate_seat(
    payload: ExamSeatAllocationCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.registrations.manage"))],
) -> ExamSeatAllocationSummary:
    """Assign one eligible registration to an examination room seat."""

    service = ExaminationsService(session, actor)
    try:
        item = service.allocate_seat(payload)
        response = ExamSeatAllocationSummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/hall-tickets/{registration_id}", response_model=HallTicketSummary)
def get_hall_ticket(
    registration_id: UUID,
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
) -> HallTicketSummary:
    """Return one source-derived hall ticket for an exam registration."""

    try:
        return HallTicketSummary.model_validate(service.get_hall_ticket(registration_id))
    except ExaminationsDomainError as error:
        _raise_domain_error(error)


@router.get("/invigilation", response_model=PaginatedInvigilationAssignments)
def list_invigilation_assignments(
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedInvigilationAssignments:
    """Return invigilation assignments for the authenticated tenant."""

    items, total = service.list_invigilation_assignments(skip=skip, limit=limit)
    return PaginatedInvigilationAssignments(
        items=[InvigilationAssignmentSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post(
    "/invigilation",
    response_model=InvigilationAssignmentSummary,
    status_code=status.HTTP_201_CREATED,
)
def assign_invigilator(
    payload: InvigilationAssignmentCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.configuration.manage"))],
) -> InvigilationAssignmentSummary:
    """Assign one faculty member to an examination room."""

    service = ExaminationsService(session, actor)
    try:
        item = service.assign_invigilator(payload)
        response = InvigilationAssignmentSummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/registrations/{registration_id}/marks", response_model=MarkEntrySummary)
def get_marks(
    registration_id: UUID,
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
) -> MarkEntrySummary:
    """Return one mark entry by registration ID for the authenticated tenant."""

    item = service.get_mark_entry_by_registration(registration_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mark entry not found")
    return MarkEntrySummary.model_validate(item)


@router.put("/registrations/{registration_id}/marks", response_model=MarkEntrySummary)
def enter_marks(
    registration_id: UUID,
    payload: MarkEntryUpsert,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.marks.enter"))],
) -> MarkEntrySummary:
    """Create or update one marks entry for an eligible registration."""

    service = ExaminationsService(session, actor)
    try:
        item = service.enter_marks(registration_id, payload)
        response = MarkEntrySummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/registrations/{registration_id}/marks/verify", response_model=MarkEntrySummary)
def verify_marks(
    registration_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.marks.verify"))],
) -> MarkEntrySummary:
    """Verify one entered marks record for the authenticated tenant."""

    service = ExaminationsService(session, actor)
    try:
        item = service.verify_marks(registration_id)
        response = MarkEntrySummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/registrations/{registration_id}/marks/lock", response_model=MarkEntrySummary)
def lock_marks(
    registration_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.marks.verify"))],
) -> MarkEntrySummary:
    """Lock one verified marks record for the authenticated tenant."""

    service = ExaminationsService(session, actor)
    try:
        item = service.lock_marks(registration_id)
        response = MarkEntrySummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/mark-adjustments", response_model=PaginatedMarkAdjustments)
def list_mark_adjustments(
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedMarkAdjustments:
    """Return moderation and revaluation requests for the authenticated tenant."""

    items, total = service.list_mark_adjustments(skip=skip, limit=limit)
    return PaginatedMarkAdjustments(
        items=[MarkAdjustmentSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post(
    "/mark-adjustments",
    response_model=MarkAdjustmentSummary,
    status_code=status.HTTP_201_CREATED,
)
def request_mark_adjustment(
    payload: MarkAdjustmentCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.marks.enter"))],
) -> MarkAdjustmentSummary:
    """Request a reviewed adjustment without overwriting locked marks."""

    service = ExaminationsService(session, actor)
    try:
        item = service.request_mark_adjustment(payload)
        response = MarkAdjustmentSummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/mark-adjustments/{adjustment_id}/review", response_model=MarkAdjustmentSummary)
def review_mark_adjustment(
    adjustment_id: UUID,
    payload: MarkAdjustmentReview,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.marks.verify"))],
) -> MarkAdjustmentSummary:
    """Approve or reject one mark adjustment request."""

    service = ExaminationsService(session, actor)
    try:
        item = service.review_mark_adjustment(adjustment_id, payload)
        response = MarkAdjustmentSummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/results", response_model=PaginatedPublishedResults)
def list_results(
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    session_id: UUID | None = None,
) -> PaginatedPublishedResults:
    """Return a paginated list of published results for the authenticated tenant."""

    items, total = service.list_published_results(skip=skip, limit=limit, session_id=session_id)
    return PaginatedPublishedResults(
        items=[PublishedResultSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post("/results/publish", response_model=PublishResultsResponse)
def publish_results(
    payload: PublishResultsRequest,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.results.publish"))],
) -> PublishResultsResponse:
    """Publish results from locked marks for one exam session."""

    service = ExaminationsService(session, actor)
    try:
        published_count = service.publish_results(payload.session_id)
        session.commit()
        return PublishResultsResponse(session_id=payload.session_id, published_count=published_count)
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/results/{result_id}/reopen", response_model=PublishedResultSummary)
def reopen_result(
    result_id: UUID,
    payload: ResultReopenRequest,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.results.publish"))],
) -> PublishedResultSummary:
    """Reopen one published result to permit an explicit republish."""

    service = ExaminationsService(session, actor)
    try:
        item = service.reopen_result(result_id, payload)
        response = PublishedResultSummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/results/{result_id}/republish", response_model=PublishedResultSummary)
def republish_result(
    result_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("examinations.results.publish"))],
) -> PublishedResultSummary:
    """Republish one explicitly reopened result from current locked marks."""

    service = ExaminationsService(session, actor)
    try:
        item = service.republish_result(result_id)
        response = PublishedResultSummary.model_validate(item)
        session.commit()
        return response
    except ExaminationsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/result-details/{result_id}", response_model=PublishedResultDetail)
def get_result_detail(
    result_id: UUID,
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
) -> PublishedResultDetail:
    """Return current subject snapshots and publication history for one result."""

    try:
        result, lines, history = service.get_result_detail(result_id)
        return PublishedResultDetail(
            **PublishedResultSummary.model_validate(result).model_dump(),
            lines=[PublishedResultLineSummary.model_validate(item) for item in lines],
            history=[ResultPublicationEventSummary.model_validate(item) for item in history],
        )
    except ExaminationsDomainError as error:
        _raise_domain_error(error)


@router.get("/transcripts/{student_id}", response_model=TranscriptSummary)
def get_transcript(
    student_id: UUID,
    service: Annotated[ExaminationsService, Depends(get_examinations_service)],
) -> TranscriptSummary:
    """Return one source-derived student transcript and cumulative GPA."""

    try:
        results, cgpa = service.build_transcript(student_id)
        return TranscriptSummary(
            student_id=student_id,
            cgpa=cgpa,
            results=[PublishedResultSummary.model_validate(item) for item in results],
        )
    except ExaminationsDomainError as error:
        _raise_domain_error(error)