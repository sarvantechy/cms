"""Pydantic schemas for examinations configuration, marks workflow, and published results."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

MONEY_MAX_DIGITS = 10
MONEY_DECIMAL_PLACES = 2
SESSION_STATE_PATTERN = "^(draft|active|published|closed)$"
ELIGIBILITY_PATTERN = "^(eligible|ineligible|withheld)$"
MARK_STATE_PATTERN = "^(entered|verified|locked)$"
RESULT_STATE_PATTERN = "^(published|reopened)$"
RESULT_PATTERN = "^(pass|fail)$"


class AssessmentSchemeCreate(BaseModel):
    """Payload for creating one assessment scheme."""

    subject_id: UUID
    program_id: UUID
    term_id: UUID
    max_marks: Decimal = Field(gt=0, max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    pass_marks: Decimal = Field(ge=0, max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)


class AssessmentSchemeSummary(BaseModel):
    """Response shape for one assessment scheme."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    subject_id: UUID
    program_id: UUID
    term_id: UUID
    max_marks: Decimal
    pass_marks: Decimal


class ExamSessionCreate(BaseModel):
    """Payload for creating one exam session."""

    term_id: UUID
    state: str = Field(default="draft", pattern=SESSION_STATE_PATTERN)


class ExamSessionSummary(BaseModel):
    """Response shape for one exam session."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    term_id: UUID
    state: str = Field(pattern=SESSION_STATE_PATTERN)


class ExamScheduleCreate(BaseModel):
    """Payload for creating one exam schedule."""

    session_id: UUID
    offering_id: UUID
    exam_date: date
    room_id: UUID | None = None
    max_marks: Decimal = Field(gt=0, max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)


class ExamScheduleSummary(BaseModel):
    """Response shape for one exam schedule."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    session_id: UUID
    offering_id: UUID
    exam_date: date
    room_id: UUID | None
    max_marks: Decimal


class ExamRegistrationCreate(BaseModel):
    """Payload for creating one exam registration."""

    schedule_id: UUID
    student_id: UUID
    eligibility: str = Field(default="eligible", pattern=ELIGIBILITY_PATTERN)


class ExamRegistrationSummary(BaseModel):
    """Response shape for one exam registration."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    schedule_id: UUID
    student_id: UUID
    eligibility: str = Field(pattern=ELIGIBILITY_PATTERN)


class MarkEntryUpsert(BaseModel):
    """Payload for entering marks on one registration."""

    marks_obtained: Decimal = Field(
        ge=0,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
    )


class MarkEntrySummary(BaseModel):
    """Response shape for one mark entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    registration_id: UUID
    marks_obtained: Decimal
    state: str = Field(pattern=MARK_STATE_PATTERN)
    verified_by_membership_id: UUID | None
    locked_by_membership_id: UUID | None


class GradeRuleCreate(BaseModel):
    """Payload for creating one versioned grade band."""

    term_id: UUID
    version: int = Field(ge=1)
    min_percentage: Decimal = Field(ge=0, le=100)
    max_percentage: Decimal = Field(ge=0, le=100)
    letter_grade: str = Field(min_length=1, max_length=8)
    grade_point: Decimal = Field(ge=0, le=10)
    state: str = Field(default="draft", pattern="^(draft|published|archived)$")


class GradeRuleSummary(BaseModel):
    """Response shape for one versioned grade band."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    term_id: UUID
    version: int
    min_percentage: Decimal
    max_percentage: Decimal
    letter_grade: str
    grade_point: Decimal
    state: str


class ExamSeatAllocationCreate(BaseModel):
    """Payload for assigning one registration to a room seat."""

    registration_id: UUID
    room_id: UUID
    seat_number: str = Field(min_length=1, max_length=32)


class ExamSeatAllocationSummary(BaseModel):
    """Response shape for one examination seat assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    schedule_id: UUID
    registration_id: UUID
    room_id: UUID
    seat_number: str


class HallTicketSummary(BaseModel):
    """Derived hall-ticket details for one exam registration."""

    registration_id: UUID
    student_id: UUID
    schedule_id: UUID
    exam_date: date
    room_id: UUID | None
    seat_number: str | None
    eligibility: str


class HallTicketIssuanceSummary(BaseModel):
    """Return immutable hall-ticket issuance metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    session_id: UUID
    ticket_number: str
    issued_at: datetime
    issued_by_membership_id: UUID


class HallTicketDocumentExam(BaseModel):
    """Present one scheduled examination on a hall ticket."""

    registration_id: UUID
    subject_code: str
    subject_name: str
    exam_date: date
    room_code: str | None
    room_name: str | None
    seat_number: str | None


class HallTicketDocument(BaseModel):
    """Compose one printable hall ticket from issued and academic source records."""

    issuance_id: UUID
    ticket_number: str
    verification_reference: str
    issued_at: datetime
    issued_by_membership_id: UUID
    institution_name: str
    institution_short_name: str
    primary_color: str
    accent_color: str
    student_id: UUID
    student_name: str
    registration_number: str
    session_id: UUID
    term_name: str
    exams: list[HallTicketDocumentExam]


class InvigilationAssignmentCreate(BaseModel):
    """Payload for assigning one faculty invigilator."""

    schedule_id: UUID
    faculty_id: UUID
    room_id: UUID


class InvigilationAssignmentSummary(BaseModel):
    """Response shape for one invigilation assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    schedule_id: UUID
    faculty_id: UUID
    room_id: UUID


class MarkAdjustmentCreate(BaseModel):
    """Payload for requesting moderation or revaluation of locked marks."""

    registration_id: UUID
    revised_marks: Decimal = Field(ge=0, max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    reason: str = Field(min_length=3, max_length=2000)


class MarkAdjustmentReview(BaseModel):
    """Payload for approving or rejecting one mark adjustment."""

    state: str = Field(pattern="^(approved|rejected)$")


class MarkAdjustmentSummary(BaseModel):
    """Response shape for one auditable mark adjustment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    registration_id: UUID
    original_marks: Decimal
    revised_marks: Decimal
    reason: str
    state: str
    requested_by_membership_id: UUID
    reviewed_by_membership_id: UUID | None
    reviewed_at: datetime | None


class PublishedResultLineSummary(BaseModel):
    """Response shape for one snapshotted subject result line."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    publication_version: int
    registration_id: UUID
    subject_id: UUID
    marks_obtained: Decimal
    max_marks: Decimal
    pass_marks: Decimal
    credits: int
    grade: str
    grade_point: Decimal


class PublishedResultSummary(BaseModel):
    """Response shape for one published result."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    session_id: UUID
    total_marks: Decimal
    total_max_marks: Decimal
    percentage: Decimal
    grade: str
    gpa: Decimal
    result: str = Field(pattern=RESULT_PATTERN)
    state: str = Field(pattern=RESULT_STATE_PATTERN)
    publication_version: int


class PublishedResultDetail(PublishedResultSummary):
    """Response shape for one result with subject snapshots and publication history."""

    lines: list[PublishedResultLineSummary]
    history: list["ResultPublicationEventSummary"]


class ResultPublicationEventSummary(BaseModel):
    """Response shape for one immutable result lifecycle snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    result_id: UUID
    version: int
    event_type: str
    reason: str | None
    snapshot: dict[str, object]
    performed_by_membership_id: UUID
    created_at: datetime


class TranscriptSummary(BaseModel):
    """Derived transcript across published session results for one student."""

    student_id: UUID
    cgpa: Decimal
    results: list[PublishedResultSummary]


class GradeCardIssuanceSummary(BaseModel):
    """Return immutable grade-card issuance metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    result_id: UUID
    publication_version: int
    card_number: str
    issued_at: datetime
    issued_by_membership_id: UUID


class GradeCardDocumentLine(BaseModel):
    """Present one snapshotted subject outcome on a grade card."""

    subject_code: str
    subject_name: str
    marks_obtained: Decimal
    max_marks: Decimal
    credits: int
    grade: str
    grade_point: Decimal


class GradeCardDocument(BaseModel):
    """Compose one printable grade card from an issued result version."""

    issuance_id: UUID
    card_number: str
    verification_reference: str
    issued_at: datetime
    issued_by_membership_id: UUID
    institution_name: str
    institution_short_name: str
    primary_color: str
    accent_color: str
    student_id: UUID
    student_name: str
    registration_number: str
    result_id: UUID
    session_id: UUID
    term_name: str
    publication_version: int
    total_marks: Decimal
    total_max_marks: Decimal
    percentage: Decimal
    grade: str
    gpa: Decimal
    result: str
    lines: list[GradeCardDocumentLine]


class TranscriptIssuanceSummary(BaseModel):
    """Return immutable transcript issuance metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    transcript_number: str
    version_hash: str
    issued_at: datetime
    issued_by_membership_id: UUID


class TranscriptDocumentResult(BaseModel):
    """Present one published term result in an issued transcript."""

    result_id: UUID
    session_id: UUID
    term_name: str
    publication_version: int
    total_marks: Decimal
    total_max_marks: Decimal
    percentage: Decimal
    grade: str
    gpa: Decimal
    result: str
    lines: list[GradeCardDocumentLine]


class TranscriptDocument(BaseModel):
    """Compose one printable transcript from an issued result-version manifest."""

    issuance_id: UUID
    transcript_number: str
    verification_reference: str
    issued_at: datetime
    issued_by_membership_id: UUID
    institution_name: str
    institution_short_name: str
    primary_color: str
    accent_color: str
    student_id: UUID
    student_name: str
    registration_number: str
    cgpa: Decimal
    results: list[TranscriptDocumentResult]


class PublishResultsRequest(BaseModel):
    """Payload for publishing results for one session."""

    session_id: UUID


class PublishResultsResponse(BaseModel):
    """Response shape for one publish operation."""

    session_id: UUID
    published_count: int = Field(ge=0)


class ResultReopenRequest(BaseModel):
    """Payload for reopening one immutable published result."""

    reason: str = Field(min_length=3, max_length=2000)


class PaginatedAssessmentSchemes(BaseModel):
    """Paginated wrapper for assessment schemes."""

    items: list[AssessmentSchemeSummary]
    total: int = Field(ge=0)


class PaginatedExamSessions(BaseModel):
    """Paginated wrapper for exam sessions."""

    items: list[ExamSessionSummary]
    total: int = Field(ge=0)


class PaginatedExamSchedules(BaseModel):
    """Paginated wrapper for exam schedules."""

    items: list[ExamScheduleSummary]
    total: int = Field(ge=0)


class PaginatedExamRegistrations(BaseModel):
    """Paginated wrapper for exam registrations."""

    items: list[ExamRegistrationSummary]
    total: int = Field(ge=0)


class PaginatedPublishedResults(BaseModel):
    """Paginated wrapper for published results."""

    items: list[PublishedResultSummary]
    total: int = Field(ge=0)


class PaginatedGradeRules(BaseModel):
    """Paginated wrapper for grade rules."""

    items: list[GradeRuleSummary]
    total: int = Field(ge=0)


class PaginatedExamSeatAllocations(BaseModel):
    """Paginated wrapper for examination seats."""

    items: list[ExamSeatAllocationSummary]
    total: int = Field(ge=0)


class PaginatedInvigilationAssignments(BaseModel):
    """Paginated wrapper for invigilation assignments."""

    items: list[InvigilationAssignmentSummary]
    total: int = Field(ge=0)


class PaginatedMarkAdjustments(BaseModel):
    """Paginated wrapper for mark adjustment requests."""

    items: list[MarkAdjustmentSummary]
    total: int = Field(ge=0)
