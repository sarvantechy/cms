"""Pydantic schemas for student, guardian, enrollment, and status lifecycle APIs."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

STUDENT_STATUS_PATTERN = "^(prospective|active|on_hold|graduated|discontinued)$"
ENROLLMENT_STATUS_PATTERN = "^(active|completed|cancelled|transferred)$"


class PersonBase(BaseModel):
    """Shared person identity and contact fields used across student workflows."""

    full_name: str = Field(min_length=1, max_length=240)
    email: str | None = Field(None, min_length=3, max_length=320)
    mobile_number: str | None = Field(None, min_length=7, max_length=24)
    date_of_birth: date | None = None

    @model_validator(mode="after")
    def validate_contact(self) -> "PersonBase":
        """Require at least one contact channel for identity records."""

        if not self.email and not self.mobile_number:
            msg = "either email or mobile_number is required"
            raise ValueError(msg)
        return self


class PersonCreate(PersonBase):
    """Request payload for creating one canonical person record."""


class PersonUpdate(BaseModel):
    """Request payload for updating mutable person fields."""

    full_name: str | None = Field(None, min_length=1, max_length=240)
    email: str | None = Field(None, min_length=3, max_length=320)
    mobile_number: str | None = Field(None, min_length=7, max_length=24)
    date_of_birth: date | None = None


class PersonSummary(PersonBase):
    """API response shape for a person record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID


class PersonListResponse(BaseModel):
    """Paginate canonical tenant people for authorized operational selectors."""

    items: list[PersonSummary]
    total: int = Field(ge=0)


class StudentBase(BaseModel):
    """Shared student core fields used by create and summary contracts."""

    registration_number: str = Field(min_length=1, max_length=48)
    status: str = Field(default="active", pattern=STUDENT_STATUS_PATTERN)


class StudentCreate(StudentBase):
    """Request body for direct student creation."""

    person: PersonCreate
    source_application_id: UUID | None = None


class StudentUpdate(BaseModel):
    """Request body for mutable student and optional person updates."""

    registration_number: str | None = Field(None, min_length=1, max_length=48)
    status: str | None = Field(None, pattern=STUDENT_STATUS_PATTERN)
    person: PersonUpdate | None = None


class StudentSummary(StudentBase):
    """Student response shape returned by list and detail endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    person_id: UUID
    source_application_id: UUID | None
    person: PersonSummary


class StudentListResponse(BaseModel):
    """Paginated response wrapper for student list queries."""

    items: list[StudentSummary]
    total: int = Field(ge=0)


class GuardianBase(BaseModel):
    """Shared guardian contact fields backed by one person identity."""

    email: str | None = Field(None, min_length=3, max_length=320)
    mobile_number: str | None = Field(None, min_length=7, max_length=24)

    @model_validator(mode="after")
    def validate_contact(self) -> "GuardianBase":
        """Require at least one guardian contact channel."""

        if not self.email and not self.mobile_number:
            msg = "either email or mobile_number is required"
            raise ValueError(msg)
        return self


class GuardianCreate(GuardianBase):
    """Payload to create a guardian profile with a nested person identity."""

    person: PersonCreate


class GuardianSummary(GuardianBase):
    """Guardian response shape returned by students APIs."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    person_id: UUID
    person: PersonSummary


class StudentGuardianLinkCreate(BaseModel):
    """Payload for linking a guardian to a student, optionally creating the guardian."""

    guardian_id: UUID | None = None
    guardian: GuardianCreate | None = None
    relationship: str = Field(min_length=1, max_length=32)
    is_primary: bool = False

    @model_validator(mode="after")
    def validate_guardian_source(self) -> "StudentGuardianLinkCreate":
        """Ensure exactly one guardian source is provided for the link request."""

        source_count = int(self.guardian_id is not None) + int(self.guardian is not None)
        if source_count != 1:
            msg = "provide exactly one of guardian_id or guardian"
            raise ValueError(msg)
        return self


class StudentGuardianSummary(BaseModel):
    """Student-to-guardian link response with relationship metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    guardian_id: UUID
    relationship: str
    is_primary: bool
    guardian: GuardianSummary


class StudentEnrollmentCreate(BaseModel):
    """Payload for creating one student enrollment record."""

    academic_year_id: UUID
    program_id: UUID
    batch_id: UUID | None = None
    section_id: UUID | None = None
    status: str = Field(default="active", pattern=ENROLLMENT_STATUS_PATTERN)


class StudentEnrollmentSummary(BaseModel):
    """Enrollment response shape returned by student APIs."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    academic_year_id: UUID
    program_id: UUID
    batch_id: UUID | None
    section_id: UUID | None
    status: str


class StudentStatusTransition(BaseModel):
    """Payload for student lifecycle status transition requests."""

    to_status: str = Field(pattern=STUDENT_STATUS_PATTERN)
    reason: str | None = Field(None, max_length=500)
    changed_at: datetime | None = None


class StudentStatusHistorySummary(BaseModel):
    """Response shape for one persisted student status history entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    from_status: str
    to_status: str
    reason: str | None
    changed_at: datetime
    changed_by_membership_id: UUID


class StudentDocumentCreate(BaseModel):
    """Create student document metadata before binary storage is introduced."""

    category: str = Field(min_length=1, max_length=48)
    title: str = Field(min_length=1, max_length=160)
    document_number: str | None = Field(None, max_length=80)
    reference_url: str | None = Field(None, max_length=500)
    issued_on: date | None = None
    expires_on: date | None = None
    notes: str | None = Field(None, max_length=1000)


class StudentDocumentReview(BaseModel):
    """Verify or reject one student document record."""

    status: str = Field(pattern="^(verified|rejected)$")
    notes: str | None = Field(None, max_length=1000)


class StudentDocumentSummary(StudentDocumentCreate):
    """Return persisted student document and verification metadata."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    media_object_id: UUID | None = None
    tenant_id: UUID
    student_id: UUID
    status: str
    verified_by_membership_id: UUID | None
    verified_at: datetime | None


class StudentSubjectRegistrationCreate(BaseModel):
    """Register one student enrollment for an available subject offering."""

    enrollment_id: UUID
    subject_offering_id: UUID
    registered_on: date


class StudentSubjectRegistrationDecision(BaseModel):
    """Drop or complete one active subject registration."""

    status: str = Field(pattern="^(dropped|completed)$")


class StudentSubjectRegistrationSummary(StudentSubjectRegistrationCreate):
    """Return one persisted student subject registration."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    student_id: UUID
    status: str


class StudentProgressionCreate(BaseModel):
    """Prepare a next-academic-year enrollment target."""

    from_enrollment_id: UUID
    target_academic_year_id: UUID
    target_program_id: UUID
    target_batch_id: UUID | None = None
    target_section_id: UUID | None = None


class StudentProgressionDecision(BaseModel):
    """Approve, reject, or apply one prepared progression."""

    state: str = Field(pattern="^(approved|rejected|applied)$")
    reason: str | None = Field(None, max_length=1000)


class StudentProgressionSummary(StudentProgressionCreate):
    """Return one progression preparation and decision state."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    student_id: UUID
    state: str
    decision_reason: str | None
    applied_enrollment_id: UUID | None


class StudentLifecycleRequestCreate(BaseModel):
    """Request a transfer or readmission into a validated academic target."""

    request_type: str = Field(pattern="^(transfer|readmission)$")
    from_enrollment_id: UUID | None = None
    target_academic_year_id: UUID
    target_program_id: UUID
    target_batch_id: UUID | None = None
    target_section_id: UUID | None = None
    reason: str = Field(min_length=1, max_length=1000)


class StudentLifecycleDecision(BaseModel):
    """Approve, reject, or complete a transfer/readmission request."""

    state: str = Field(pattern="^(approved|rejected|completed)$")
    reason: str | None = Field(None, max_length=1000)


class StudentLifecycleRequestSummary(StudentLifecycleRequestCreate):
    """Return a persisted transfer or readmission request."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    student_id: UUID
    state: str
    decision_reason: str | None
    reviewed_by_membership_id: UUID | None
    reviewed_at: datetime | None


class StudentCertificateRequestCreate(BaseModel):
    """Submit one student certificate request."""

    certificate_type: str = Field(min_length=1, max_length=48)
    purpose: str = Field(min_length=1, max_length=1000)


class StudentCertificateDecision(BaseModel):
    """Approve, reject, or issue a student certificate request."""

    state: str = Field(pattern="^(approved|rejected|issued)$")
    reason: str | None = Field(None, max_length=1000)
    issued_reference: str | None = Field(None, max_length=80)

    @model_validator(mode="after")
    def validate_issued_reference(self) -> "StudentCertificateDecision":
        """Require a durable reference when a certificate is issued."""

        if self.state == "issued" and not self.issued_reference:
            msg = "issued_reference is required when state is issued"
            raise ValueError(msg)
        return self


class StudentCertificateRequestSummary(StudentCertificateRequestCreate):
    """Return one persisted certificate request and decision state."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    student_id: UUID
    state: str
    decision_reason: str | None
    issued_reference: str | None
    reviewed_by_membership_id: UUID | None
    reviewed_at: datetime | None


class StudentCertificateDocument(BaseModel):
    """Compose one printable requested Student certificate from issued records."""

    request_id: UUID
    certificate_type: str
    purpose: str
    issued_reference: str
    verification_reference: str
    issued_at: datetime
    issued_by_membership_id: UUID | None
    institution_name: str
    institution_short_name: str
    primary_color: str
    accent_color: str
    student_id: UUID
    student_name: str
    registration_number: str


class StudentLifecycleResponse(BaseModel):
    """Return all lifecycle expansion records authorized for one student."""

    documents: list[StudentDocumentSummary]
    subject_registrations: list[StudentSubjectRegistrationSummary]
    progressions: list[StudentProgressionSummary]
    lifecycle_requests: list[StudentLifecycleRequestSummary]
    certificate_requests: list[StudentCertificateRequestSummary]


class StudentDetailResponse(BaseModel):
    """Return one canonical student with guardian, enrollment, and status history records."""

    student: StudentSummary
    guardians: list[StudentGuardianSummary]
    enrollments: list[StudentEnrollmentSummary]
    status_history: list[StudentStatusHistorySummary]


class StudentConversionFromApplication(BaseModel):
    """Payload for converting an accepted application into a student record."""

    registration_number: str | None = Field(None, min_length=1, max_length=48)
    status: str = Field(default="active", pattern=STUDENT_STATUS_PATTERN)
    batch_id: UUID | None = None
    section_id: UUID | None = None
    enrollment_status: str = Field(default="active", pattern=ENROLLMENT_STATUS_PATTERN)
