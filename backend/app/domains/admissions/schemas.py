"""Pydantic schemas for admissions create, update, list, summary, and transitions."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

CAMPAIGN_STATE_PATTERN = "^(draft|published|closed|archived)$"
APPLICATION_STATE_PATTERN = (
    "^(draft|submitted|under_review|verified|selected|offered|accepted|rejected|"
    "waitlisted|withdrawn|cancelled)$"
)
DOCUMENT_VERIFICATION_STATE_PATTERN = "^(pending|verified|rejected)$"
OFFER_STATE_PATTERN = "^(issued|accepted|declined|expired|cancelled)$"
ENQUIRY_STATE_PATTERN = "^(new|contacted|qualified|converted|closed)$"


class AdmissionEnquiryBase(BaseModel):
    """Collect prospective applicant contact and follow-up details."""

    campaign_id: UUID | None = None
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    email: str | None = Field(None, min_length=3, max_length=320)
    mobile_number: str | None = Field(None, min_length=7, max_length=24)
    source: str = Field(default="direct", min_length=1, max_length=80)
    state: str = Field(default="new", pattern=ENQUIRY_STATE_PATTERN)
    notes: str | None = None
    next_follow_up_at: datetime | None = None

    @model_validator(mode="after")
    def validate_contact_presence(self) -> "AdmissionEnquiryBase":
        """Require at least one enquiry contact channel."""

        if not self.email and not self.mobile_number:
            raise ValueError("either email or mobile_number is required")
        return self


class AdmissionEnquiryCreate(AdmissionEnquiryBase):
    """Create one prospective applicant enquiry."""


class AdmissionEnquiryUpdate(BaseModel):
    """Update mutable enquiry contact and follow-up details."""

    campaign_id: UUID | None = None
    first_name: str | None = Field(None, min_length=1, max_length=120)
    last_name: str | None = Field(None, min_length=1, max_length=120)
    email: str | None = Field(None, min_length=3, max_length=320)
    mobile_number: str | None = Field(None, min_length=7, max_length=24)
    source: str | None = Field(None, min_length=1, max_length=80)
    notes: str | None = None
    next_follow_up_at: datetime | None = None


class AdmissionEnquiryTransition(BaseModel):
    """Request one explicit enquiry lifecycle transition."""

    to_state: str = Field(pattern=ENQUIRY_STATE_PATTERN)
    reason: str | None = Field(None, max_length=500)


class AdmissionEnquirySummary(AdmissionEnquiryBase):
    """Return one tenant-scoped enquiry record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


class AdmissionEnquiryListResponse(BaseModel):
    """Wrap a paginated admissions enquiry collection."""

    items: list[AdmissionEnquirySummary]
    total: int = Field(ge=0)


class AdmissionCampaignBase(BaseModel):
    """Shared campaign fields used by create and summary payloads."""

    academic_year_id: UUID
    program_id: UUID
    code: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=240)
    starts_on: date
    ends_on: date
    state: str = Field(default="draft", pattern=CAMPAIGN_STATE_PATTERN)

    @model_validator(mode="after")
    def validate_campaign_dates(self) -> "AdmissionCampaignBase":
        """Ensure campaign end date is not earlier than start date."""

        if self.ends_on < self.starts_on:
            msg = "ends_on must be greater than or equal to starts_on"
            raise ValueError(msg)
        return self


class AdmissionCampaignCreate(AdmissionCampaignBase):
    """Request body for creating an admission campaign."""


class AdmissionCampaignUpdate(BaseModel):
    """Request body for updating an existing admission campaign."""

    title: str | None = Field(None, min_length=1, max_length=240)
    starts_on: date | None = None
    ends_on: date | None = None
    state: str | None = Field(None, pattern=CAMPAIGN_STATE_PATTERN)

    @model_validator(mode="after")
    def validate_campaign_dates(self) -> "AdmissionCampaignUpdate":
        """Validate date ordering when both start and end dates are provided."""

        if self.starts_on is not None and self.ends_on is not None and self.ends_on < self.starts_on:
            msg = "ends_on must be greater than or equal to starts_on"
            raise ValueError(msg)
        return self


class AdmissionCampaignSummary(AdmissionCampaignBase):
    """Admission campaign response shape returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID


class AdmissionCampaignListItem(BaseModel):
    """Compact campaign projection for list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    title: str
    starts_on: date
    ends_on: date
    state: str


class AdmissionCampaignListResponse(BaseModel):
    """List response wrapper for campaign collection queries."""

    items: list[AdmissionCampaignListItem]
    total: int = Field(ge=0)


class ApplicantBase(BaseModel):
    """Shared applicant identity and contact fields."""

    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    email: str | None = Field(None, min_length=3, max_length=320)
    mobile_number: str | None = Field(None, min_length=7, max_length=24)
    date_of_birth: date | None = None

    @model_validator(mode="after")
    def validate_contact_presence(self) -> "ApplicantBase":
        """Require at least one contact channel for applicant communication."""

        if not self.email and not self.mobile_number:
            msg = "either email or mobile_number is required"
            raise ValueError(msg)
        return self


class ApplicantCreate(ApplicantBase):
    """Request body for creating an applicant record."""


class ApplicantUpdate(BaseModel):
    """Request body for updating an applicant record."""

    first_name: str | None = Field(None, min_length=1, max_length=120)
    last_name: str | None = Field(None, min_length=1, max_length=120)
    email: str | None = Field(None, min_length=3, max_length=320)
    mobile_number: str | None = Field(None, min_length=7, max_length=24)
    date_of_birth: date | None = None


class ApplicantSummary(ApplicantBase):
    """Applicant response shape returned by admissions endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID


class ApplicantListItem(BaseModel):
    """Compact applicant projection for list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    email: str | None
    mobile_number: str | None


class ApplicantListResponse(BaseModel):
    """List response wrapper for applicant collection queries."""

    items: list[ApplicantListItem]
    total: int = Field(ge=0)


class ApplicationBase(BaseModel):
    """Shared application fields for create and summary contracts."""

    campaign_id: UUID
    applicant_id: UUID
    program_id: UUID
    application_number: str = Field(min_length=1, max_length=48)
    state: str = Field(default="draft", pattern=APPLICATION_STATE_PATTERN)
    submitted_at: datetime | None = None
    remarks: str | None = None


class ApplicationCreate(ApplicationBase):
    """Request body for creating an application."""


class ApplicationUpdate(BaseModel):
    """Request body for updating mutable application details."""

    remarks: str | None = None
    submitted_at: datetime | None = None


class ApplicationStateTransition(BaseModel):
    """Request body for transitioning an application lifecycle state."""

    to_state: str = Field(pattern=APPLICATION_STATE_PATTERN)
    reason: str | None = Field(None, max_length=500)


class ApplicationSummary(ApplicationBase):
    """Application response shape returned by admissions endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID


class ApplicationListItem(BaseModel):
    """Compact application projection for listing views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_number: str
    state: str
    campaign_id: UUID
    applicant_id: UUID
    submitted_at: datetime | None


class ApplicationListResponse(BaseModel):
    """List response wrapper for application collection queries."""

    items: list[ApplicationListItem]
    total: int = Field(ge=0)


class ApplicationDocumentBase(BaseModel):
    """Shared application document and verification metadata fields."""

    application_id: UUID
    document_type: str = Field(min_length=1, max_length=48)
    document_number: str | None = Field(None, max_length=80)
    file_url: str | None = Field(None, max_length=2048)
    verification_state: str = Field(
        default="pending",
        pattern=DOCUMENT_VERIFICATION_STATE_PATTERN,
    )
    verified_at: datetime | None = None
    verified_by: str | None = Field(None, max_length=240)
    verification_notes: str | None = None


class ApplicationDocumentCreate(ApplicationDocumentBase):
    """Request body for creating an application document record."""


class ApplicationDocumentUpdate(BaseModel):
    """Request body for updating application document metadata."""

    document_number: str | None = Field(None, max_length=80)
    file_url: str | None = Field(None, max_length=2048)
    verification_notes: str | None = None


class ApplicationDocumentVerificationTransition(BaseModel):
    """Request body for changing document verification lifecycle state."""

    to_state: str = Field(pattern=DOCUMENT_VERIFICATION_STATE_PATTERN)
    verified_at: datetime | None = None
    verified_by: str | None = Field(None, max_length=240)
    verification_notes: str | None = None


class ApplicationDocumentSummary(ApplicationDocumentBase):
    """Application document response shape returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    media_object_id: UUID | None = None


class ApplicationDocumentListItem(BaseModel):
    """Compact application document projection for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    document_type: str
    verification_state: str
    verified_at: datetime | None


class ApplicationDocumentListResponse(BaseModel):
    """List response wrapper for application document collection queries."""

    items: list[ApplicationDocumentListItem]
    total: int = Field(ge=0)


class ApplicationDetailResponse(BaseModel):
    """Combine one application with its applicant and submitted documents."""

    application: ApplicationSummary
    applicant: ApplicantSummary
    documents: list[ApplicationDocumentSummary]


class AdmissionsHistoryEntry(BaseModel):
    """Expose one append-only admissions audit event without request metadata."""

    id: UUID
    action: str
    entity_type: str
    entity_id: UUID | None
    account_id: UUID | None
    membership_id: UUID | None
    created_at: datetime
    details: dict[str, object]


class SeatPoolBase(BaseModel):
    """Shared category-wise seat capacity fields."""

    campaign_id: UUID
    category_code: str = Field(min_length=1, max_length=24)
    category_name: str = Field(min_length=1, max_length=120)
    seat_capacity: int = Field(ge=0)
    filled_seats: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_capacity(self) -> "SeatPoolBase":
        """Ensure filled seats never exceed configured seat capacity."""

        if self.filled_seats > self.seat_capacity:
            msg = "filled_seats must be less than or equal to seat_capacity"
            raise ValueError(msg)
        return self


class SeatPoolCreate(SeatPoolBase):
    """Request body for creating a seat pool."""


class SeatPoolUpdate(BaseModel):
    """Request body for updating category seat allocation counts."""

    category_name: str | None = Field(None, min_length=1, max_length=120)
    seat_capacity: int | None = Field(None, ge=0)
    filled_seats: int | None = Field(None, ge=0)

    @model_validator(mode="after")
    def validate_capacity(self) -> "SeatPoolUpdate":
        """Validate provided capacity and filled seats when both are present."""

        if (
            self.seat_capacity is not None
            and self.filled_seats is not None
            and self.filled_seats > self.seat_capacity
        ):
            msg = "filled_seats must be less than or equal to seat_capacity"
            raise ValueError(msg)
        return self


class SeatPoolSummary(SeatPoolBase):
    """Seat pool response shape returned by admissions endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID


class SeatPoolListItem(BaseModel):
    """Compact seat pool projection for listing views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    campaign_id: UUID
    category_code: str
    seat_capacity: int
    filled_seats: int


class SeatPoolListResponse(BaseModel):
    """List response wrapper for seat pool collection queries."""

    items: list[SeatPoolListItem]
    total: int = Field(ge=0)


class AdmissionOfferBase(BaseModel):
    """Shared offer fields for create and summary payloads."""

    application_id: UUID
    seat_pool_id: UUID
    offer_number: str = Field(min_length=1, max_length=48)
    offered_on: date
    expires_on: date
    state: str = Field(default="issued", pattern=OFFER_STATE_PATTERN)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_offer_dates(self) -> "AdmissionOfferBase":
        """Ensure offer expiry date is not earlier than the offered date."""

        if self.expires_on < self.offered_on:
            msg = "expires_on must be greater than or equal to offered_on"
            raise ValueError(msg)
        return self


class AdmissionOfferCreate(AdmissionOfferBase):
    """Request body for creating an admission offer."""


class AdmissionOfferUpdate(BaseModel):
    """Request body for updating mutable offer details."""

    expires_on: date | None = None
    notes: str | None = None


class AdmissionOfferStateTransition(BaseModel):
    """Request body for transitioning admission offer lifecycle state."""

    to_state: str = Field(pattern=OFFER_STATE_PATTERN)
    reason: str | None = Field(None, max_length=500)


class AdmissionOfferSummary(AdmissionOfferBase):
    """Admission offer response shape returned by admissions endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID


class AdmissionOfferListItem(BaseModel):
    """Compact offer projection for listing views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_number: str
    application_id: UUID
    state: str
    offered_on: date
    expires_on: date


class AdmissionOfferListResponse(BaseModel):
    """List response wrapper for admission offer collection queries."""

    items: list[AdmissionOfferListItem]
    total: int = Field(ge=0)
