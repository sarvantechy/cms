"""Pydantic schemas for notices and delivery tracking workflows."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

NOTICE_STATE_PATTERN = "^(draft|pending_approval|approved|scheduled|published|archived)$"
NOTICE_AUDIENCE_PATTERN = "^(all|role|membership)$"
NOTICE_DELIVERY_STATE_PATTERN = "^(pending|sent|failed|read)$"


class NoticeCreate(BaseModel):
    """Payload for creating one notice in draft or scheduled state."""

    title: str = Field(min_length=1, max_length=240)
    body: str = Field(min_length=1, max_length=20000)
    state: str = Field(default="draft", pattern=NOTICE_STATE_PATTERN)
    publish_at: datetime | None = None
    audience_type: str = Field(pattern=NOTICE_AUDIENCE_PATTERN)
    audience_ref: UUID | None = None
    template_id: UUID | None = None
    requires_acknowledgement: bool = False


class NoticeUpdate(BaseModel):
    """Payload for updating mutable notice fields."""

    title: str | None = Field(None, min_length=1, max_length=240)
    body: str | None = Field(None, min_length=1, max_length=20000)
    state: str | None = Field(None, pattern=NOTICE_STATE_PATTERN)
    publish_at: datetime | None = None
    audience_type: str | None = Field(None, pattern=NOTICE_AUDIENCE_PATTERN)
    audience_ref: UUID | None = None


class NoticeScheduleRequest(BaseModel):
    """Payload for scheduling one notice publication time."""

    publish_at: datetime


class NoticeSummary(BaseModel):
    """Response shape for one tenant notice."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    title: str
    body: str
    state: str
    publish_at: datetime | None
    audience_type: str
    audience_ref: UUID | None
    template_id: UUID | None
    requires_acknowledgement: bool
    approved_by_membership_id: UUID | None
    approved_at: datetime | None


class AudiencePreviewRequest(BaseModel):
    """Payload for previewing a server-resolved notice audience."""

    audience_type: str = Field(pattern=NOTICE_AUDIENCE_PATTERN)
    audience_ref: UUID | None = None


class AudiencePreview(BaseModel):
    """Return the authoritative recipient count for an audience rule."""

    recipient_count: int = Field(ge=0)


class ApprovalDecision(BaseModel):
    """Carry an optional approval workflow comment."""

    comment: str | None = Field(None, max_length=2000)


class NoticeApprovalEventSummary(BaseModel):
    """Response shape for one immutable notice approval event."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    notice_id: UUID
    membership_id: UUID
    action: str
    comment: str | None
    created_at: datetime


class MessageTemplateCreate(BaseModel):
    """Payload for creating a reusable communication template."""

    code: str = Field(min_length=1, max_length=48, pattern="^[a-z0-9_]+$")
    title_template: str = Field(min_length=1, max_length=240)
    body_template: str = Field(min_length=1, max_length=20000)
    channel: str = Field(default="in_app", pattern="^(in_app|email|sms)$")


class MessageTemplateUpdate(BaseModel):
    """Payload for updating a reusable communication template."""

    title_template: str | None = Field(None, min_length=1, max_length=240)
    body_template: str | None = Field(None, min_length=1, max_length=20000)
    channel: str | None = Field(None, pattern="^(in_app|email|sms)$")
    is_active: bool | None = None


class MessageTemplateSummary(BaseModel):
    """Response shape for one communication template."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    title_template: str
    body_template: str
    channel: str
    is_active: bool


class CommunicationPreferenceUpdate(BaseModel):
    """Payload for updating the actor's delivery preferences."""

    email_enabled: bool
    sms_enabled: bool
    in_app_enabled: bool


class CommunicationPreferenceSummary(CommunicationPreferenceUpdate):
    """Response shape for membership delivery preferences."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    membership_id: UUID


class NoticeAcknowledgementSummary(BaseModel):
    """Response shape for one notice acknowledgement."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    notice_id: UUID
    membership_id: UUID
    acknowledged_at: datetime


class DeliveryJobSummary(BaseModel):
    """Response shape for one provider-independent delivery job."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    delivery_id: UUID
    channel: str
    state: str
    retry_count: int
    next_attempt_at: datetime | None


class DeliveryAttemptSummary(BaseModel):
    """Response shape for one immutable provider delivery attempt."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    delivery_id: UUID
    job_id: UUID | None
    channel: str
    attempt_number: int
    state: str
    provider_reference: str | None
    error_detail: str | None
    attempted_at: datetime


class NoticeDeliverySummary(BaseModel):
    """Response shape for one membership notice delivery record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    notice_id: UUID
    membership_id: UUID
    state: str = Field(pattern=NOTICE_DELIVERY_STATE_PATTERN)
    attempts: int = Field(ge=0)
    read_at: datetime | None


class PaginatedNotices(BaseModel):
    """Paginated wrapper for notice listings."""

    items: list[NoticeSummary]
    total: int = Field(ge=0)


class PaginatedNoticeDeliveries(BaseModel):
    """Paginated wrapper for notice delivery listings."""

    items: list[NoticeDeliverySummary]
    total: int = Field(ge=0)


class PaginatedMessageTemplates(BaseModel):
    """Paginated wrapper for communication templates."""

    items: list[MessageTemplateSummary]
    total: int = Field(ge=0)


class PaginatedApprovalEvents(BaseModel):
    """Paginated wrapper for notice approval history."""

    items: list[NoticeApprovalEventSummary]
    total: int = Field(ge=0)


class PaginatedDeliveryJobs(BaseModel):
    """Paginated wrapper for delivery jobs."""

    items: list[DeliveryJobSummary]
    total: int = Field(ge=0)


class PaginatedDeliveryAttempts(BaseModel):
    """Paginated wrapper for immutable delivery attempts."""

    items: list[DeliveryAttemptSummary]
    total: int = Field(ge=0)
