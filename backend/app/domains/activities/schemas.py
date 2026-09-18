"""Pydantic schemas for activities, participation, and achievements."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ACTIVITY_STATE_PATTERN = "^(draft|published|cancelled|completed)$"
REGISTRATION_STATE_PATTERN = "^(registered|approved|attended|cancelled)$"


class ActivityCreate(BaseModel):
    """Payload for creating one activity event."""

    club_id: UUID | None = None
    title: str = Field(min_length=1, max_length=240)
    activity_type: str = Field(min_length=1, max_length=80)
    activity_date: date
    venue: str | None = Field(None, max_length=240)
    capacity: int | None = Field(None, gt=0)
    eligibility_notes: str | None = None
    state: str = Field(default="draft", pattern=ACTIVITY_STATE_PATTERN)


class ActivityUpdate(BaseModel):
    """Payload for updating mutable activity fields."""

    club_id: UUID | None = None
    title: str | None = Field(None, min_length=1, max_length=240)
    activity_type: str | None = Field(None, min_length=1, max_length=80)
    activity_date: date | None = None
    venue: str | None = Field(None, max_length=240)
    capacity: int | None = Field(None, gt=0)
    eligibility_notes: str | None = None
    state: str | None = Field(None, pattern=ACTIVITY_STATE_PATTERN)


class ActivitySummary(BaseModel):
    """Response shape for one activity event."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    club_id: UUID | None
    title: str
    activity_type: str
    activity_date: date
    venue: str | None
    capacity: int | None
    eligibility_notes: str | None
    state: str


class ActivityClubCreate(BaseModel):
    """Payload for creating one managed activity club."""

    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)
    description: str | None = None
    status: str = Field(default="active", pattern="^(active|inactive|archived)$")


class ActivityClubSummary(BaseModel):
    """Response shape for one activity club."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    category: str
    description: str | None
    status: str


class ActivityApprovalCreate(BaseModel):
    """Payload for requesting venue or budget approval."""

    request_type: str = Field(pattern="^(venue|budget)$")
    requested_value: str = Field(min_length=1)
    amount: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)


class ActivityApprovalReview(BaseModel):
    """Payload for approving or rejecting one activity resource request."""

    state: str = Field(pattern="^(approved|rejected)$")
    review_comment: str | None = None


class ActivityApprovalSummary(BaseModel):
    """Response shape for one activity approval request."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    activity_id: UUID
    request_type: str
    requested_value: str
    amount: Decimal | None
    state: str
    reviewed_by_membership_id: UUID | None
    reviewed_at: datetime | None
    review_comment: str | None


class ActivityTeamCreate(BaseModel):
    """Payload for creating one activity team."""

    name: str = Field(min_length=1, max_length=160)
    captain_student_id: UUID | None = None


class ActivityTeamMemberCreate(BaseModel):
    """Payload for adding one approved participant to a team."""

    student_id: UUID


class ActivityTeamSummary(BaseModel):
    """Response shape for one activity team."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    activity_id: UUID
    name: str
    captain_student_id: UUID | None


class ActivityTeamMemberSummary(BaseModel):
    """Response shape for one activity team membership."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    team_id: UUID
    student_id: UUID


class ActivityExpenseCreate(BaseModel):
    """Payload for submitting one activity expense."""

    description: str = Field(min_length=1, max_length=240)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class ActivityExpenseReview(BaseModel):
    """Payload for approving or rejecting one submitted activity expense."""

    state: str = Field(pattern="^(approved|rejected)$")


class ActivityExpenseSummary(BaseModel):
    """Response shape for one reviewed activity expense."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    activity_id: UUID
    description: str
    amount: Decimal
    state: str
    reviewed_by_membership_id: UUID | None
    reviewed_at: datetime | None


class ActivityCertificateCreate(BaseModel):
    """Payload for issuing a certificate from an attended registration."""

    registration_id: UUID


class ActivityCertificateSummary(BaseModel):
    """Response shape for one verifiable activity certificate."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    activity_id: UUID
    student_id: UUID
    registration_id: UUID
    serial_number: str
    issued_at: datetime
    revoked_at: datetime | None


class ActivityCertificateDocument(BaseModel):
    """Compose one printable participation certificate from authoritative records."""

    certificate_id: UUID
    serial_number: str
    verification_reference: str
    issued_at: datetime
    institution_name: str
    institution_short_name: str
    primary_color: str
    accent_color: str
    student_id: UUID
    student_name: str
    registration_number: str
    activity_id: UUID
    activity_title: str
    activity_type: str
    activity_date: date
    venue: str | None


class ActivityPointCreate(BaseModel):
    """Payload for awarding activity points to an attended participant."""

    student_id: UUID
    points: int = Field(gt=0)
    reason: str = Field(min_length=1, max_length=240)


class ActivityPointSummary(BaseModel):
    """Response shape for one immutable activity-point award."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    activity_id: UUID
    student_id: UUID
    points: int
    reason: str


class EventRegistrationCreate(BaseModel):
    """Payload for registering one student to one activity."""

    student_id: UUID
    state: str = Field(default="registered", pattern="^(registered|cancelled)$")


class EventRegistrationReview(BaseModel):
    """Payload for approving or cancelling one event registration."""

    state: str = Field(pattern="^(approved|cancelled)$")


class EventRegistrationSummary(BaseModel):
    """Response shape for one event registration."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    activity_id: UUID
    student_id: UUID
    state: str


class AchievementCreate(BaseModel):
    """Payload for creating one student achievement record."""

    student_id: UUID
    activity_id: UUID
    title: str = Field(min_length=1, max_length=240)
    certificate_ref: str | None = Field(None, max_length=255)


class AchievementSummary(BaseModel):
    """Response shape for one student achievement."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    activity_id: UUID
    title: str
    certificate_ref: str | None


class PaginatedActivities(BaseModel):
    """Paginated wrapper for activity listings."""

    items: list[ActivitySummary]
    total: int = Field(ge=0)


class PaginatedEventRegistrations(BaseModel):
    """Paginated wrapper for event registration listings."""

    items: list[EventRegistrationSummary]
    total: int = Field(ge=0)


class PaginatedAchievements(BaseModel):
    """Paginated wrapper for achievement listings."""

    items: list[AchievementSummary]
    total: int = Field(ge=0)


class PaginatedActivityClubs(BaseModel):
    """Paginated wrapper for activity clubs."""

    items: list[ActivityClubSummary]
    total: int = Field(ge=0)


class PaginatedActivityApprovals(BaseModel):
    """Paginated wrapper for activity approval requests."""

    items: list[ActivityApprovalSummary]
    total: int = Field(ge=0)


class PaginatedActivityTeams(BaseModel):
    """Paginated wrapper for activity teams."""

    items: list[ActivityTeamSummary]
    total: int = Field(ge=0)


class PaginatedActivityTeamMembers(BaseModel):
    """Paginated wrapper for activity team memberships."""

    items: list[ActivityTeamMemberSummary]
    total: int = Field(ge=0)


class PaginatedActivityExpenses(BaseModel):
    """Paginated wrapper for activity expenses."""

    items: list[ActivityExpenseSummary]
    total: int = Field(ge=0)


class PaginatedActivityCertificates(BaseModel):
    """Paginated wrapper for activity certificates."""

    items: list[ActivityCertificateSummary]
    total: int = Field(ge=0)


class PaginatedActivityPoints(BaseModel):
    """Paginated wrapper for activity point awards."""

    items: list[ActivityPointSummary]
    total: int = Field(ge=0)
