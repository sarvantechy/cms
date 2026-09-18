"""FastAPI routes for tenant-safe events, attendance registration, and achievements."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import runtime_session_factory
from app.domains.activities.schemas import (
    AchievementCreate,
    AchievementSummary,
    ActivityApprovalCreate,
    ActivityApprovalReview,
    ActivityApprovalSummary,
    ActivityCertificateCreate,
    ActivityCertificateDocument,
    ActivityCertificateSummary,
    ActivityClubCreate,
    ActivityClubSummary,
    ActivityCreate,
    ActivityExpenseCreate,
    ActivityExpenseReview,
    ActivityExpenseSummary,
    ActivityPointCreate,
    ActivityPointSummary,
    ActivitySummary,
    ActivityTeamCreate,
    ActivityTeamMemberCreate,
    ActivityTeamMemberSummary,
    ActivityTeamSummary,
    ActivityUpdate,
    EventRegistrationCreate,
    EventRegistrationReview,
    EventRegistrationSummary,
    PaginatedAchievements,
    PaginatedActivities,
    PaginatedActivityApprovals,
    PaginatedActivityCertificates,
    PaginatedActivityClubs,
    PaginatedActivityExpenses,
    PaginatedActivityPoints,
    PaginatedActivityTeamMembers,
    PaginatedActivityTeams,
    PaginatedEventRegistrations,
)
from app.domains.activities.service import ActivitiesDomainError, ActivitiesService
from app.domains.identity.router import require_actor, require_permission
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/activities", tags=["Activities"])

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


def get_activities_service(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.read"))],
) -> ActivitiesService:
    """Build an activities service for read operations under tenant-safe authorization."""

    return ActivitiesService(session, actor)


def _raise_domain_error(error: ActivitiesDomainError) -> None:
    """Translate domain failures into deterministic API responses."""

    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _raise_conflict(error: IntegrityError) -> None:
    """Translate relational uniqueness and integrity failures into HTTP 409."""

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Record conflicts with existing data",
    ) from error


@router.get("/clubs", response_model=PaginatedActivityClubs)
def list_clubs(
    service: Annotated[ActivitiesService, Depends(get_activities_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedActivityClubs:
    """Return tenant activity clubs."""

    items, total = service.list_clubs(skip=skip, limit=limit)
    return PaginatedActivityClubs(
        items=[ActivityClubSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post("/clubs", response_model=ActivityClubSummary, status_code=status.HTTP_201_CREATED)
def create_club(
    payload: ActivityClubCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> ActivityClubSummary:
    """Create one managed activity club."""

    service = ActivitiesService(session, actor)
    try:
        response = ActivityClubSummary.model_validate(service.create_club(payload))
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/events", response_model=PaginatedActivities)
def list_activities(
    service: Annotated[ActivitiesService, Depends(get_activities_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    state: str | None = Query(default=None, pattern="^(draft|published|cancelled|completed)$"),
    activity_type: str | None = None,
) -> PaginatedActivities:
    """Return a paginated list of activities for the authenticated tenant."""

    items, total = service.list_activities(
        skip=skip,
        limit=limit,
        state=state,
        activity_type=activity_type,
    )
    return PaginatedActivities(items=[ActivitySummary.model_validate(item) for item in items], total=total)


@router.post("/events", response_model=ActivitySummary, status_code=status.HTTP_201_CREATED)
def create_activity(
    payload: ActivityCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> ActivitySummary:
    """Create one activity event for the authenticated tenant."""

    service = ActivitiesService(session, actor)
    try:
        item = service.create_activity(payload)
        response = ActivitySummary.model_validate(item)
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/events/{activity_id}", response_model=ActivitySummary)
def update_activity(
    activity_id: UUID,
    payload: ActivityUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> ActivitySummary:
    """Update mutable fields for one tenant activity event."""

    service = ActivitiesService(session, actor)
    try:
        item = service.update_activity(activity_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
        response = ActivitySummary.model_validate(item)
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/events/{activity_id}/registrations", response_model=PaginatedEventRegistrations)
def list_registrations(
    activity_id: UUID,
    service: Annotated[ActivitiesService, Depends(get_activities_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedEventRegistrations:
    """Return paginated event registrations for one activity."""

    try:
        items, total = service.list_registrations(activity_id=activity_id, skip=skip, limit=limit)
        return PaginatedEventRegistrations(
            items=[EventRegistrationSummary.model_validate(item) for item in items],
            total=total,
        )
    except ActivitiesDomainError as error:
        _raise_domain_error(error)


@router.post(
    "/events/{activity_id}/registrations",
    response_model=EventRegistrationSummary,
    status_code=status.HTTP_201_CREATED,
)
def register_student(
    activity_id: UUID,
    payload: EventRegistrationCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_actor)],
) -> EventRegistrationSummary:
    """Register one student for one activity within tenant scope."""

    service = ActivitiesService(session, actor)
    try:
        item = service.register_student(activity_id, payload)
        response = EventRegistrationSummary.model_validate(item)
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/registrations/{registration_id}/approve", response_model=EventRegistrationSummary)
def approve_registration(
    registration_id: UUID,
    payload: EventRegistrationReview,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> EventRegistrationSummary:
    """Approve or cancel one event registration."""

    service = ActivitiesService(session, actor)
    try:
        item = service.approve_registration(registration_id, payload)
        response = EventRegistrationSummary.model_validate(item)
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/registrations/{registration_id}/attendance", response_model=EventRegistrationSummary)
def mark_attendance(
    registration_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> EventRegistrationSummary:
    """Mark one approved registration as attended."""

    service = ActivitiesService(session, actor)
    try:
        item = service.mark_attended(registration_id)
        response = EventRegistrationSummary.model_validate(item)
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/achievements", response_model=PaginatedAchievements)
def list_achievements(
    service: Annotated[ActivitiesService, Depends(get_activities_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    student_id: UUID | None = None,
    activity_id: UUID | None = None,
) -> PaginatedAchievements:
    """Return paginated achievements within tenant-safe filters."""

    items, total = service.list_achievements(
        skip=skip,
        limit=limit,
        student_id=student_id,
        activity_id=activity_id,
    )
    return PaginatedAchievements(
        items=[AchievementSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post("/achievements", response_model=AchievementSummary, status_code=status.HTTP_201_CREATED)
def create_achievement(
    payload: AchievementCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> AchievementSummary:
    """Create one student achievement entry for one activity."""

    service = ActivitiesService(session, actor)
    try:
        item = service.create_achievement(payload)
        response = AchievementSummary.model_validate(item)
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/events/{activity_id}/approvals", response_model=PaginatedActivityApprovals)
def list_approvals(
    activity_id: UUID,
    service: Annotated[ActivitiesService, Depends(get_activities_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedActivityApprovals:
    """Return venue and budget approval requests for one activity."""

    try:
        items, total = service.list_approvals(activity_id, skip, limit)
        return PaginatedActivityApprovals(
            items=[ActivityApprovalSummary.model_validate(item) for item in items],
            total=total,
        )
    except ActivitiesDomainError as error:
        _raise_domain_error(error)


@router.post(
    "/events/{activity_id}/approvals",
    response_model=ActivityApprovalSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_approval(
    activity_id: UUID,
    payload: ActivityApprovalCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> ActivityApprovalSummary:
    """Create one venue or budget approval request."""

    service = ActivitiesService(session, actor)
    try:
        response = ActivityApprovalSummary.model_validate(
            service.create_approval(activity_id, payload)
        )
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/approvals/{approval_id}/review", response_model=ActivityApprovalSummary)
def review_approval(
    approval_id: UUID,
    payload: ActivityApprovalReview,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> ActivityApprovalSummary:
    """Approve or reject one pending activity resource request."""

    service = ActivitiesService(session, actor)
    try:
        response = ActivityApprovalSummary.model_validate(
            service.review_approval(approval_id, payload)
        )
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)


@router.get("/events/{activity_id}/teams", response_model=PaginatedActivityTeams)
def list_teams(
    activity_id: UUID,
    service: Annotated[ActivitiesService, Depends(get_activities_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedActivityTeams:
    """Return teams belonging to one activity."""

    try:
        items, total = service.list_teams(activity_id, skip, limit)
        return PaginatedActivityTeams(
            items=[ActivityTeamSummary.model_validate(item) for item in items],
            total=total,
        )
    except ActivitiesDomainError as error:
        _raise_domain_error(error)


@router.post(
    "/events/{activity_id}/teams",
    response_model=ActivityTeamSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_team(
    activity_id: UUID,
    payload: ActivityTeamCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> ActivityTeamSummary:
    """Create one team for an activity."""

    service = ActivitiesService(session, actor)
    try:
        response = ActivityTeamSummary.model_validate(service.create_team(activity_id, payload))
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/teams/{team_id}/members", response_model=PaginatedActivityTeamMembers)
def list_team_members(
    team_id: UUID,
    service: Annotated[ActivitiesService, Depends(get_activities_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedActivityTeamMembers:
    """Return participants assigned to one activity team."""

    try:
        items, total = service.list_team_members(team_id, skip, limit)
        return PaginatedActivityTeamMembers(
            items=[ActivityTeamMemberSummary.model_validate(item) for item in items],
            total=total,
        )
    except ActivitiesDomainError as error:
        _raise_domain_error(error)


@router.post(
    "/teams/{team_id}/members",
    response_model=ActivityTeamMemberSummary,
    status_code=status.HTTP_201_CREATED,
)
def add_team_member(
    team_id: UUID,
    payload: ActivityTeamMemberCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> ActivityTeamMemberSummary:
    """Add one approved participant to an activity team."""

    service = ActivitiesService(session, actor)
    try:
        response = ActivityTeamMemberSummary.model_validate(
            service.add_team_member(team_id, payload)
        )
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/events/{activity_id}/expenses", response_model=PaginatedActivityExpenses)
def list_expenses(
    activity_id: UUID,
    service: Annotated[ActivitiesService, Depends(get_activities_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedActivityExpenses:
    """Return expenses submitted for one activity."""

    try:
        items, total = service.list_expenses(activity_id, skip, limit)
        return PaginatedActivityExpenses(
            items=[ActivityExpenseSummary.model_validate(item) for item in items],
            total=total,
        )
    except ActivitiesDomainError as error:
        _raise_domain_error(error)


@router.post(
    "/events/{activity_id}/expenses",
    response_model=ActivityExpenseSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_expense(
    activity_id: UUID,
    payload: ActivityExpenseCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> ActivityExpenseSummary:
    """Submit one expense for an activity."""

    service = ActivitiesService(session, actor)
    try:
        response = ActivityExpenseSummary.model_validate(
            service.create_expense(activity_id, payload)
        )
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/expenses/{expense_id}/review", response_model=ActivityExpenseSummary)
def review_expense(
    expense_id: UUID,
    payload: ActivityExpenseReview,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> ActivityExpenseSummary:
    """Approve or reject one submitted activity expense."""

    service = ActivitiesService(session, actor)
    try:
        response = ActivityExpenseSummary.model_validate(
            service.review_expense(expense_id, payload)
        )
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)


@router.get("/events/{activity_id}/certificates", response_model=PaginatedActivityCertificates)
def list_certificates(
    activity_id: UUID,
    service: Annotated[ActivitiesService, Depends(get_activities_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedActivityCertificates:
    """Return certificates issued for one activity within actor scope."""

    items, total = service.list_certificates(activity_id, skip, limit)
    return PaginatedActivityCertificates(
        items=[ActivityCertificateSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post(
    "/events/{activity_id}/certificates",
    response_model=ActivityCertificateSummary,
    status_code=status.HTTP_201_CREATED,
)
def issue_certificate(
    activity_id: UUID,
    payload: ActivityCertificateCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> ActivityCertificateSummary:
    """Issue one verifiable certificate for attended participation."""

    service = ActivitiesService(session, actor)
    try:
        response = ActivityCertificateSummary.model_validate(
            service.issue_certificate(activity_id, payload)
        )
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/certificates/verify/{serial_number}", response_model=ActivityCertificateSummary)
def verify_certificate(
    serial_number: str,
    service: Annotated[ActivitiesService, Depends(get_activities_service)],
) -> ActivityCertificateSummary:
    """Verify one active certificate by serial number."""

    item = service.verify_certificate(serial_number)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    return ActivityCertificateSummary.model_validate(item)


@router.get(
    "/events/{activity_id}/certificates/{certificate_id}/document",
    response_model=ActivityCertificateDocument,
)
def get_certificate_document(
    activity_id: UUID,
    certificate_id: UUID,
    service: Annotated[ActivitiesService, Depends(get_activities_service)],
) -> ActivityCertificateDocument:
    """Return one print-ready participation certificate within actor scope."""

    document = service.get_certificate_document(activity_id, certificate_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    return document


@router.get("/events/{activity_id}/points", response_model=PaginatedActivityPoints)
def list_points(
    activity_id: UUID,
    service: Annotated[ActivitiesService, Depends(get_activities_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedActivityPoints:
    """Return activity-point awards within actor scope."""

    items, total = service.list_points(activity_id, skip, limit)
    return PaginatedActivityPoints(
        items=[ActivityPointSummary.model_validate(item) for item in items],
        total=total,
    )


@router.post(
    "/events/{activity_id}/points",
    response_model=ActivityPointSummary,
    status_code=status.HTTP_201_CREATED,
)
def award_points(
    activity_id: UUID,
    payload: ActivityPointCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("activities.records.manage"))],
) -> ActivityPointSummary:
    """Award points to one attended activity participant."""

    service = ActivitiesService(session, actor)
    try:
        response = ActivityPointSummary.model_validate(service.award_points(activity_id, payload))
        session.commit()
        return response
    except ActivitiesDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)
