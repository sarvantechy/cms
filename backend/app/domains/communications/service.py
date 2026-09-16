"""Business logic for tenant-safe communications notices and portal delivery states."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.domains.audit.models import AuditEvent
from app.domains.communications.models import (
    CommunicationDeliveryJob,
    CommunicationPreference,
    DeliveryAttempt,
    MessageTemplate,
    Notice,
    NoticeAcknowledgement,
    NoticeApprovalEvent,
    NoticeDelivery,
)
from app.domains.communications.schemas import (
    CommunicationPreferenceUpdate,
    MessageTemplateCreate,
    MessageTemplateUpdate,
    NoticeCreate,
    NoticeUpdate,
)
from app.domains.identity.models import MembershipRoleAssignment, TenantMembership
from app.domains.identity.models import TenantRole as TenantRoleModel
from app.security_context import ActorContext

INVALID_NOTICE_REFERENCE = "Invalid notice reference"


class CommunicationsDomainError(Exception):
    """Represent one controlled communications domain error."""

    def __init__(self, detail: str, status_code: int) -> None:
        """Initialize the error with client-safe detail and HTTP status."""

        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class CommunicationsValidationError(CommunicationsDomainError):
    """Represent one validation error mapped to HTTP 422."""

    def __init__(self, detail: str) -> None:
        """Initialize a communications validation error."""

        super().__init__(detail, 422)


class CommunicationsConflictError(CommunicationsDomainError):
    """Represent one conflict error mapped to HTTP 409."""

    def __init__(self, detail: str) -> None:
        """Initialize a communications conflict error."""

        super().__init__(detail, 409)


class CommunicationsService:
    """Manage tenant notices, publication lifecycle, and delivery read state."""

    def __init__(self, session: Session, actor: ActorContext) -> None:
        """Initialize the service and scope its session to the actor's tenant."""

        self.session = session
        self.actor = actor
        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(actor.tenant_id)},
        )

    def _paginate(self, query, skip: int, limit: int):
        """Return one page of query results and the unpaginated total."""

        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def _audit(self, action: str, entity_type: str, entity_id: UUID, details: dict[str, object]) -> None:
        """Stage a tenant-scoped audit event for the current transaction."""

        self.session.add(
            AuditEvent(
                tenant_id=self.actor.tenant_id,
                account_id=self.actor.account_id,
                membership_id=self.actor.membership_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
            )
        )

    def _get_notice(self, notice_id: UUID) -> Notice | None:
        """Return a notice when it belongs to the actor's tenant."""

        return self.session.scalar(
            select(Notice).where(Notice.tenant_id == self.actor.tenant_id, Notice.id == notice_id)
        )

    def _validate_audience(self, audience_type: str, audience_ref: UUID | None) -> None:
        """Validate a notice audience and its optional tenant reference."""

        if audience_type == "all":
            if audience_ref is not None:
                raise CommunicationsValidationError("audience_ref must be null when audience_type is all")
            return

        if audience_ref is None:
            raise CommunicationsValidationError("audience_ref is required when audience_type is not all")

        if audience_type == "membership":
            membership = self.session.scalar(
                select(TenantMembership).where(
                    TenantMembership.tenant_id == self.actor.tenant_id,
                    TenantMembership.id == audience_ref,
                    TenantMembership.status == "active",
                )
            )
            if membership is None:
                raise CommunicationsValidationError("Invalid audience membership reference")
            return

        if audience_type == "role":
            role = self.session.scalar(
                select(TenantRoleModel).where(
                    TenantRoleModel.tenant_id == self.actor.tenant_id,
                    TenantRoleModel.id == audience_ref,
                    TenantRoleModel.is_active.is_(True),
                )
            )
            if role is None:
                raise CommunicationsValidationError("Invalid audience role reference")
            return

        raise CommunicationsValidationError("Unsupported audience_type")

    def _resolve_membership_ids(self, notice: Notice) -> tuple[UUID, ...]:
        """Resolve active tenant memberships targeted by a notice."""

        if notice.audience_type == "all":
            return tuple(
                self.session.scalars(
                    select(TenantMembership.id).where(
                        TenantMembership.tenant_id == self.actor.tenant_id,
                        TenantMembership.status == "active",
                    )
                )
            )

        if notice.audience_type == "membership":
            return (notice.audience_ref,) if notice.audience_ref is not None else ()

        if notice.audience_type == "role":
            if notice.audience_ref is None:
                return ()
            return tuple(
                self.session.scalars(
                    select(MembershipRoleAssignment.membership_id)
                    .join(
                        TenantMembership,
                        (TenantMembership.tenant_id == MembershipRoleAssignment.tenant_id)
                        & (TenantMembership.id == MembershipRoleAssignment.membership_id),
                    )
                    .where(
                        MembershipRoleAssignment.tenant_id == self.actor.tenant_id,
                        MembershipRoleAssignment.role_id == notice.audience_ref,
                        TenantMembership.status == "active",
                    )
                    .distinct()
                )
            )

        return ()

    def preview_audience(self, audience_type: str, audience_ref: UUID | None) -> int:
        """Validate and count recipients for one audience rule."""

        self._validate_audience(audience_type, audience_ref)
        notice = Notice(tenant_id=self.actor.tenant_id, title="preview", body="preview", audience_type=audience_type, audience_ref=audience_ref)
        return len(self._resolve_membership_ids(notice))

    def _queue_delivery_jobs(self, notice: Notice) -> int:
        """Create idempotent provider-independent jobs for resolved deliveries."""

        deliveries = list(self.session.scalars(select(NoticeDelivery).where(NoticeDelivery.tenant_id == self.actor.tenant_id, NoticeDelivery.notice_id == notice.id)))
        membership_ids = [delivery.membership_id for delivery in deliveries]
        preferences = {item.membership_id: item for item in self.session.scalars(select(CommunicationPreference).where(CommunicationPreference.tenant_id == self.actor.tenant_id, CommunicationPreference.membership_id.in_(membership_ids)))} if membership_ids else {}
        created = 0
        for delivery in deliveries:
            preference = preferences.get(delivery.membership_id)
            channels = ["in_app"]
            if preference is None or preference.email_enabled:
                channels.append("email")
            if preference is None or preference.sms_enabled:
                channels.append("sms")
            if preference is not None and not preference.in_app_enabled:
                channels.remove("in_app")
            existing_channels = set(self.session.scalars(select(CommunicationDeliveryJob.channel).where(CommunicationDeliveryJob.tenant_id == self.actor.tenant_id, CommunicationDeliveryJob.delivery_id == delivery.id)))
            for channel in channels:
                if channel in existing_channels:
                    continue
                job = CommunicationDeliveryJob(tenant_id=self.actor.tenant_id, delivery_id=delivery.id, channel=channel, state="sent" if channel == "in_app" else "pending", idempotency_key=f"{delivery.id}:{channel}")
                self.session.add(job)
                self.session.flush()
                if channel == "in_app":
                    self.session.add(DeliveryAttempt(tenant_id=self.actor.tenant_id, delivery_id=delivery.id, job_id=job.id, channel=channel, attempt_number=1, state="sent", provider_reference="in-app", attempted_at=datetime.now(UTC)))
                created += 1
        self.session.flush()
        return created

    def _upsert_deliveries_for_notice(self, notice: Notice, sent: bool) -> int:
        """Create or update notice deliveries and return the changed count."""

        membership_ids = self._resolve_membership_ids(notice)
        if not membership_ids:
            return 0

        existing_rows = list(
            self.session.scalars(
                select(NoticeDelivery).where(
                    NoticeDelivery.tenant_id == self.actor.tenant_id,
                    NoticeDelivery.notice_id == notice.id,
                    NoticeDelivery.membership_id.in_(membership_ids),
                )
            )
        )
        existing_by_membership = {row.membership_id: row for row in existing_rows}
        count = 0

        for membership_id in membership_ids:
            row = existing_by_membership.get(membership_id)
            if row is None:
                row = NoticeDelivery(
                    tenant_id=self.actor.tenant_id,
                    notice_id=notice.id,
                    membership_id=membership_id,
                    state="sent" if sent else "pending",
                    attempts=1 if sent else 0,
                )
                self.session.add(row)
                count += 1
                continue

            if sent and row.state != "read":
                row.state = "sent"
                row.attempts += 1
                count += 1

        self.session.flush()
        return count

    def list_notices(self, skip: int = 0, limit: int = 100, state: str | None = None):
        """List tenant notices with an optional lifecycle-state filter."""

        query = select(Notice).where(Notice.tenant_id == self.actor.tenant_id)
        if state is not None:
            query = query.where(Notice.state == state)
        query = query.order_by(Notice.created_at.desc())
        return self._paginate(query, skip, limit)

    def create_notice(self, payload: NoticeCreate) -> Notice:
        """Create a validated tenant notice and initialize scheduled deliveries."""

        self._validate_audience(payload.audience_type, payload.audience_ref)
        if payload.state != "draft":
            raise CommunicationsValidationError("New notices must start in draft state")
        if payload.template_id is not None:
            template = self.session.scalar(select(MessageTemplate).where(MessageTemplate.tenant_id == self.actor.tenant_id, MessageTemplate.id == payload.template_id, MessageTemplate.is_active.is_(True)))
            if template is None:
                raise CommunicationsValidationError("Invalid active template reference")

        notice = Notice(tenant_id=self.actor.tenant_id, **payload.model_dump())
        self.session.add(notice)
        self.session.flush()

        self._audit("communications.notice.create", "notice", notice.id, {"state": notice.state})
        return notice

    def update_notice(self, notice_id: UUID, payload: NoticeUpdate) -> Notice | None:
        """Update a mutable tenant notice and audit changed fields."""

        notice = self._get_notice(notice_id)
        if notice is None:
            return None
        if notice.state != "draft":
            raise CommunicationsConflictError("Only draft notices can be modified")

        changes: dict[str, object] = {}
        updates = payload.model_dump(exclude_unset=True)
        if "audience_type" in updates or "audience_ref" in updates:
            next_audience_type = updates.get("audience_type", notice.audience_type)
            next_audience_ref = updates.get("audience_ref", notice.audience_ref)
            self._validate_audience(next_audience_type, next_audience_ref)

        for field, value in updates.items():
            current_value = getattr(notice, field)
            if current_value != value:
                changes[field] = {"from": str(current_value), "to": str(value)}
                setattr(notice, field, value)

        if notice.state == "scheduled" and notice.publish_at is None:
            raise CommunicationsValidationError("publish_at is required when notice is scheduled")

        if changes:
            self.session.flush()
            self._audit("communications.notice.update", "notice", notice.id, changes)
        return notice

    def publish_notice(self, notice_id: UUID) -> Notice:
        """Publish a notice immediately and mark target deliveries sent."""

        notice = self._get_notice(notice_id)
        if notice is None:
            raise CommunicationsValidationError(INVALID_NOTICE_REFERENCE)
        if notice.state != "approved":
            raise CommunicationsConflictError("Only approved notices can be published")

        notice.state = "published"
        notice.publish_at = datetime.now(UTC)
        delivery_count = self._upsert_deliveries_for_notice(notice, sent=True)
        job_count = self._queue_delivery_jobs(notice)
        self.session.flush()
        self._audit(
            "communications.notice.publish",
            "notice",
            notice.id,
            {"delivery_count": delivery_count, "job_count": job_count},
        )
        return notice

    def schedule_notice(self, notice_id: UUID, publish_at: datetime) -> Notice:
        """Schedule a notice for future publication and prepare deliveries."""

        notice = self._get_notice(notice_id)
        if notice is None:
            raise CommunicationsValidationError(INVALID_NOTICE_REFERENCE)
        if notice.state != "approved":
            raise CommunicationsConflictError("Only approved notices can be scheduled")

        if publish_at <= datetime.now(UTC):
            raise CommunicationsValidationError("publish_at must be in the future")

        notice.state = "scheduled"
        notice.publish_at = publish_at
        delivery_count = self._upsert_deliveries_for_notice(notice, sent=False)
        self.session.flush()
        self._audit(
            "communications.notice.schedule",
            "notice",
            notice.id,
            {"delivery_count": delivery_count},
        )
        return notice

    def submit_notice(self, notice_id: UUID, comment: str | None) -> Notice:
        """Submit one draft notice for approval and append history."""

        notice = self._get_notice(notice_id)
        if notice is None:
            raise CommunicationsValidationError(INVALID_NOTICE_REFERENCE)
        if notice.state != "draft":
            raise CommunicationsConflictError("Only draft notices can be submitted")
        notice.state = "pending_approval"
        self.session.add(NoticeApprovalEvent(tenant_id=self.actor.tenant_id, notice_id=notice.id, membership_id=self.actor.membership_id, action="submitted", comment=comment))
        self.session.flush()
        self._audit("communications.notice.submit", "notice", notice.id, {})
        return notice

    def decide_notice(self, notice_id: UUID, approved: bool, comment: str | None) -> Notice:
        """Approve or reject one pending notice and append history."""

        notice = self._get_notice(notice_id)
        if notice is None:
            raise CommunicationsValidationError(INVALID_NOTICE_REFERENCE)
        if notice.state != "pending_approval":
            raise CommunicationsConflictError("Only pending notices can be reviewed")
        notice.state = "approved" if approved else "draft"
        notice.approved_by_membership_id = self.actor.membership_id if approved else None
        notice.approved_at = datetime.now(UTC) if approved else None
        action = "approved" if approved else "rejected"
        self.session.add(NoticeApprovalEvent(tenant_id=self.actor.tenant_id, notice_id=notice.id, membership_id=self.actor.membership_id, action=action, comment=comment))
        self.session.flush()
        self._audit(f"communications.notice.{action}", "notice", notice.id, {})
        return notice

    def list_approval_events(self, notice_id: UUID, skip: int, limit: int):
        """List immutable approval events for one notice."""

        if self._get_notice(notice_id) is None:
            raise CommunicationsValidationError(INVALID_NOTICE_REFERENCE)
        query = select(NoticeApprovalEvent).where(NoticeApprovalEvent.tenant_id == self.actor.tenant_id, NoticeApprovalEvent.notice_id == notice_id).order_by(NoticeApprovalEvent.created_at.desc())
        return self._paginate(query, skip, limit)

    def list_templates(self, skip: int, limit: int):
        """List tenant communication templates."""

        return self._paginate(select(MessageTemplate).where(MessageTemplate.tenant_id == self.actor.tenant_id).order_by(MessageTemplate.code), skip, limit)

    def create_template(self, payload: MessageTemplateCreate) -> MessageTemplate:
        """Create one tenant communication template."""

        item = MessageTemplate(tenant_id=self.actor.tenant_id, **payload.model_dump())
        self.session.add(item)
        self.session.flush()
        self._audit("communications.template.create", "message_template", item.id, {"code": item.code})
        return item

    def update_template(self, template_id: UUID, payload: MessageTemplateUpdate) -> MessageTemplate:
        """Update one tenant communication template."""

        item = self.session.scalar(select(MessageTemplate).where(MessageTemplate.tenant_id == self.actor.tenant_id, MessageTemplate.id == template_id))
        if item is None:
            raise CommunicationsValidationError("Invalid template reference")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self.session.flush()
        self._audit("communications.template.update", "message_template", item.id, {})
        return item

    def get_preferences(self) -> CommunicationPreference:
        """Return the actor's preferences, creating defaults when absent."""

        item = self.session.scalar(select(CommunicationPreference).where(CommunicationPreference.tenant_id == self.actor.tenant_id, CommunicationPreference.membership_id == self.actor.membership_id))
        if item is None:
            item = CommunicationPreference(tenant_id=self.actor.tenant_id, membership_id=self.actor.membership_id)
            self.session.add(item)
            self.session.flush()
        return item

    def update_preferences(self, payload: CommunicationPreferenceUpdate) -> CommunicationPreference:
        """Update the actor's communication channel preferences."""

        item = self.get_preferences()
        for field, value in payload.model_dump().items():
            setattr(item, field, value)
        self.session.flush()
        self._audit("communications.preference.update", "communication_preference", item.id, payload.model_dump())
        return item

    def acknowledge_notice(self, notice_id: UUID) -> NoticeAcknowledgement:
        """Acknowledge one delivered notice idempotently for the actor."""

        notice = self._get_notice(notice_id)
        if notice is None or notice.state != "published":
            raise CommunicationsValidationError(INVALID_NOTICE_REFERENCE)
        if not notice.requires_acknowledgement:
            raise CommunicationsConflictError("This notice does not require acknowledgement")
        delivery = self.session.scalar(select(NoticeDelivery.id).where(NoticeDelivery.tenant_id == self.actor.tenant_id, NoticeDelivery.notice_id == notice_id, NoticeDelivery.membership_id == self.actor.membership_id))
        if delivery is None:
            raise CommunicationsConflictError("Notice was not delivered to this membership")
        item = self.session.scalar(select(NoticeAcknowledgement).where(NoticeAcknowledgement.tenant_id == self.actor.tenant_id, NoticeAcknowledgement.notice_id == notice_id, NoticeAcknowledgement.membership_id == self.actor.membership_id))
        if item is None:
            item = NoticeAcknowledgement(tenant_id=self.actor.tenant_id, notice_id=notice_id, membership_id=self.actor.membership_id, acknowledged_at=datetime.now(UTC))
            self.session.add(item)
            self.session.flush()
            self._audit("communications.notice.acknowledge", "notice_acknowledgement", item.id, {"notice_id": str(notice_id)})
        return item

    def list_delivery_jobs(self, notice_id: UUID, skip: int, limit: int):
        """List channel jobs for one notice."""

        if self._get_notice(notice_id) is None:
            raise CommunicationsValidationError(INVALID_NOTICE_REFERENCE)
        query = select(CommunicationDeliveryJob).join(NoticeDelivery, (NoticeDelivery.tenant_id == CommunicationDeliveryJob.tenant_id) & (NoticeDelivery.id == CommunicationDeliveryJob.delivery_id)).where(CommunicationDeliveryJob.tenant_id == self.actor.tenant_id, NoticeDelivery.notice_id == notice_id).order_by(CommunicationDeliveryJob.created_at.desc())
        return self._paginate(query, skip, limit)

    def list_delivery_attempts(self, job_id: UUID, skip: int, limit: int):
        """List immutable attempts for one tenant delivery job."""

        job = self.session.scalar(select(CommunicationDeliveryJob).where(CommunicationDeliveryJob.tenant_id == self.actor.tenant_id, CommunicationDeliveryJob.id == job_id))
        if job is None:
            raise CommunicationsValidationError("Invalid delivery job reference")
        query = select(DeliveryAttempt).where(DeliveryAttempt.tenant_id == self.actor.tenant_id, DeliveryAttempt.job_id == job_id).order_by(DeliveryAttempt.attempt_number.desc())
        return self._paginate(query, skip, limit)

    def retry_delivery_job(self, job_id: UUID) -> CommunicationDeliveryJob:
        """Requeue one failed provider job idempotently."""

        job = self.session.scalar(select(CommunicationDeliveryJob).where(CommunicationDeliveryJob.tenant_id == self.actor.tenant_id, CommunicationDeliveryJob.id == job_id))
        if job is None:
            raise CommunicationsValidationError("Invalid delivery job reference")
        if job.state != "failed":
            raise CommunicationsConflictError("Only failed delivery jobs can be retried")
        job.state = "pending"
        job.retry_count += 1
        job.next_attempt_at = None
        self.session.flush()
        self._audit("communications.delivery.retry", "communication_delivery_job", job.id, {"retry_count": job.retry_count})
        return job

    def list_deliveries(self, notice_id: UUID, skip: int = 0, limit: int = 100):
        """List delivery records for one tenant notice."""

        notice = self._get_notice(notice_id)
        if notice is None:
            raise CommunicationsValidationError(INVALID_NOTICE_REFERENCE)

        query = (
            select(NoticeDelivery)
            .where(
                NoticeDelivery.tenant_id == self.actor.tenant_id,
                NoticeDelivery.notice_id == notice_id,
            )
            .order_by(NoticeDelivery.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def mark_read(self, notice_id: UUID) -> NoticeDelivery:
        """Mark the actor's notice delivery as read idempotently."""

        notice = self._get_notice(notice_id)
        if notice is None:
            raise CommunicationsValidationError(INVALID_NOTICE_REFERENCE)
        if notice.state not in {"published", "scheduled"}:
            raise CommunicationsConflictError("Only scheduled or published notices can be marked read")

        delivery = self.session.scalar(
            select(NoticeDelivery).where(
                NoticeDelivery.tenant_id == self.actor.tenant_id,
                NoticeDelivery.notice_id == notice_id,
                NoticeDelivery.membership_id == self.actor.membership_id,
            )
        )
        if delivery is None:
            delivery = NoticeDelivery(
                tenant_id=self.actor.tenant_id,
                notice_id=notice_id,
                membership_id=self.actor.membership_id,
                state="read",
                attempts=1,
                read_at=datetime.now(UTC),
            )
            self.session.add(delivery)
        else:
            delivery.state = "read"
            delivery.read_at = datetime.now(UTC)
            if delivery.attempts == 0:
                delivery.attempts = 1

        self.session.flush()
        self._audit("communications.notice.read", "notice_delivery", delivery.id, {"notice_id": str(notice_id)})
        return delivery
