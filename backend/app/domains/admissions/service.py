"""Business logic and tenant-safe state transitions for admissions workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypeVar
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.domains.academics.models import AcademicYear, Program
from app.domains.admissions.models import (
    AdmissionCampaign,
    AdmissionEnquiry,
    AdmissionOffer,
    Applicant,
    ApplicantAccess,
    Application,
    ApplicationDocument,
    SeatPool,
    TenantMediaObject,
)
from app.domains.admissions.schemas import (
    AdmissionCampaignCreate,
    AdmissionCampaignUpdate,
    AdmissionEnquiryCreate,
    AdmissionEnquiryTransition,
    AdmissionEnquiryUpdate,
    AdmissionOfferCreate,
    AdmissionOfferStateTransition,
    AdmissionOfferUpdate,
    ApplicantCreate,
    ApplicantUpdate,
    ApplicationCreate,
    ApplicationDocumentCreate,
    ApplicationDocumentUpdate,
    ApplicationDocumentVerificationTransition,
    ApplicationStateTransition,
    ApplicationUpdate,
    SeatPoolCreate,
    SeatPoolUpdate,
)
from app.domains.audit.models import AuditEvent
from app.media_storage import StoredMedia
from app.security_context import ActorContext

ModelType = TypeVar("ModelType")

APPLICATION_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"submitted", "withdrawn", "cancelled"}),
    "submitted": frozenset({"under_review", "rejected", "withdrawn", "cancelled"}),
    "under_review": frozenset({"verified", "waitlisted", "rejected", "withdrawn", "cancelled"}),
    "verified": frozenset({"selected", "waitlisted", "rejected", "withdrawn", "cancelled"}),
    "waitlisted": frozenset({"selected", "rejected", "withdrawn", "cancelled"}),
    "selected": frozenset({"offered", "rejected", "withdrawn", "cancelled"}),
    "offered": frozenset({"accepted", "withdrawn", "cancelled"}),
    "accepted": frozenset(),
    "rejected": frozenset(),
    "withdrawn": frozenset(),
    "cancelled": frozenset(),
}

DOCUMENT_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"verified", "rejected"}),
    "rejected": frozenset({"verified"}),
    "verified": frozenset(),
}

OFFER_TRANSITIONS: dict[str, frozenset[str]] = {
    "issued": frozenset({"accepted", "declined", "expired", "cancelled"}),
    "accepted": frozenset(),
    "declined": frozenset(),
    "expired": frozenset(),
    "cancelled": frozenset(),
}

ENQUIRY_TRANSITIONS: dict[str, frozenset[str]] = {
    "new": frozenset({"contacted", "closed"}),
    "contacted": frozenset({"qualified", "closed"}),
    "qualified": frozenset({"converted", "closed"}),
    "converted": frozenset(),
    "closed": frozenset(),
}


class AdmissionsDomainError(Exception):
    """Represent a controlled domain error mapped to a specific API status code."""

    def __init__(self, detail: str, status_code: int) -> None:
        """Initialize a domain error with a stable response message and status code."""

        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class AdmissionsValidationError(AdmissionsDomainError):
    """Represent a request validation failure mapped to HTTP 422."""

    def __init__(self, detail: str) -> None:
        """Initialize a 422 validation error for business-rule violations."""

        super().__init__(detail=detail, status_code=422)


class AdmissionsConflictError(AdmissionsDomainError):
    """Represent a resource-state conflict mapped to HTTP 409."""

    def __init__(self, detail: str) -> None:
        """Initialize a 409 conflict error for non-idempotent state collisions."""

        super().__init__(detail=detail, status_code=409)


class AdmissionsService:
    """Coordinate tenant-safe admissions persistence and lifecycle transitions."""

    def __init__(self, session: Session, actor: ActorContext) -> None:
        """Initialize the service with a runtime session and authenticated actor context."""

        self.session = session
        self.actor = actor
        self._set_tenant_context()

    def _set_tenant_context(self) -> None:
        """Set transaction-local PostgreSQL tenant context for all subsequent queries."""

        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self.actor.tenant_id)},
        )

    def _audit(self, action: str, entity_type: str, entity_id: UUID, details: dict[str, object]) -> None:
        """Persist one tenant-scoped audit event inside the active transaction."""

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

    def _require_entity(self, model: type[ModelType], entity_id: UUID, label: str) -> ModelType:
        """Return one tenant-scoped parent entity or raise a controlled 422 error."""

        entity = self.session.scalar(
            select(model).where(  # type: ignore[arg-type]
                model.id == entity_id,  # type: ignore[attr-defined]
                model.tenant_id == self.actor.tenant_id,  # type: ignore[attr-defined]
            )
        )
        if entity is None:
            raise AdmissionsValidationError(f"Invalid {label} reference")
        return entity

    def list_enquiries(
        self,
        skip: int = 0,
        limit: int = 100,
        state: str | None = None,
    ) -> tuple[list[AdmissionEnquiry], int]:
        """List tenant enquiries with an optional lifecycle filter."""

        query = select(AdmissionEnquiry).where(AdmissionEnquiry.tenant_id == self.actor.tenant_id)
        if state is not None:
            query = query.where(AdmissionEnquiry.state == state)
        query = query.order_by(AdmissionEnquiry.created_at.desc())
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        return list(self.session.scalars(query.offset(skip).limit(limit))), total

    def get_enquiry(self, enquiry_id: UUID) -> AdmissionEnquiry | None:
        """Return one enquiry inside the active tenant."""

        return self.session.scalar(
            select(AdmissionEnquiry).where(
                AdmissionEnquiry.id == enquiry_id,
                AdmissionEnquiry.tenant_id == self.actor.tenant_id,
            )
        )

    def create_enquiry(self, payload: AdmissionEnquiryCreate) -> AdmissionEnquiry:
        """Create one enquiry after validating an optional campaign."""

        if payload.campaign_id is not None:
            self._require_entity(AdmissionCampaign, payload.campaign_id, "campaign_id")
        enquiry = AdmissionEnquiry(tenant_id=self.actor.tenant_id, **payload.model_dump())
        self.session.add(enquiry)
        self.session.flush()
        self._audit(
            "admissions.enquiry.create",
            "admission_enquiry",
            enquiry.id,
            {"source": enquiry.source, "state": enquiry.state},
        )
        return enquiry

    def update_enquiry(
        self,
        enquiry_id: UUID,
        payload: AdmissionEnquiryUpdate,
    ) -> AdmissionEnquiry | None:
        """Update enquiry contact and follow-up fields without changing lifecycle state."""

        enquiry = self.get_enquiry(enquiry_id)
        if enquiry is None:
            return None
        values = payload.model_dump(exclude_unset=True)
        if "campaign_id" in values and values["campaign_id"] is not None:
            self._require_entity(AdmissionCampaign, values["campaign_id"], "campaign_id")
        changes: dict[str, object] = {}
        for field, value in values.items():
            previous = getattr(enquiry, field)
            if previous != value:
                changes[field] = {"from": str(previous) if previous is not None else None, "to": str(value)}
                setattr(enquiry, field, value)
        if not enquiry.email and not enquiry.mobile_number:
            raise AdmissionsValidationError("either email or mobile_number is required")
        if changes:
            self.session.flush()
            self._audit("admissions.enquiry.update", "admission_enquiry", enquiry.id, changes)
        return enquiry

    def transition_enquiry(
        self,
        enquiry_id: UUID,
        payload: AdmissionEnquiryTransition,
    ) -> AdmissionEnquiry | None:
        """Apply one controlled enquiry state transition and audit its reason."""

        enquiry = self.get_enquiry(enquiry_id)
        if enquiry is None:
            return None
        self._validate_transition(ENQUIRY_TRANSITIONS, enquiry.state, payload.to_state, "enquiry")
        if enquiry.state == payload.to_state:
            return enquiry
        previous = enquiry.state
        enquiry.state = payload.to_state
        enquiry.notes = self._append_reason(enquiry.notes, payload.reason)
        self.session.flush()
        self._audit(
            "admissions.enquiry.transition",
            "admission_enquiry",
            enquiry.id,
            {"from_state": previous, "to_state": payload.to_state, "reason": payload.reason},
        )
        return enquiry

    def _validate_transition(
        self,
        transitions: dict[str, frozenset[str]],
        from_state: str,
        to_state: str,
        label: str,
    ) -> None:
        """Validate lifecycle transitions and raise 422 on disallowed movements."""

        if to_state == from_state:
            return
        allowed = transitions.get(from_state, frozenset())
        if to_state not in allowed:
            raise AdmissionsValidationError(
                f"Cannot transition {label} from {from_state} to {to_state}"
            )

    def _append_reason(self, remarks: str | None, reason: str | None) -> str | None:
        """Append a textual reason to existing remarks using a predictable delimiter."""

        if reason is None or reason.strip() == "":
            return remarks
        reason_text = reason.strip()
        if not remarks:
            return reason_text
        return f"{remarks}\n{reason_text}"

    def _offer_for_update(self, offer_id: UUID) -> AdmissionOffer | None:
        """Load one offer row with a write lock for atomic state updates."""

        return self.session.scalar(
            select(AdmissionOffer)
            .where(
                AdmissionOffer.id == offer_id,
                AdmissionOffer.tenant_id == self.actor.tenant_id,
            )
            .with_for_update()
        )

    def _application_for_update(self, application_id: UUID) -> Application | None:
        """Load one application row with a write lock for atomic offer acceptance."""

        return self.session.scalar(
            select(Application)
            .where(
                Application.id == application_id,
                Application.tenant_id == self.actor.tenant_id,
            )
            .with_for_update()
        )

    def _seat_pool_for_update(self, seat_pool_id: UUID) -> SeatPool | None:
        """Load one seat pool row with a write lock for seat allocation updates."""

        return self.session.scalar(
            select(SeatPool)
            .where(SeatPool.id == seat_pool_id, SeatPool.tenant_id == self.actor.tenant_id)
            .with_for_update()
        )

    def list_campaigns(self, skip: int = 0, limit: int = 100) -> tuple[list[AdmissionCampaign], int]:
        """List admission campaigns for the current tenant with bounded pagination."""

        query = (
            select(AdmissionCampaign)
            .where(AdmissionCampaign.tenant_id == self.actor.tenant_id)
            .order_by(AdmissionCampaign.starts_on.desc(), AdmissionCampaign.code)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_campaign(self, campaign_id: UUID) -> AdmissionCampaign | None:
        """Return one campaign by ID for the authenticated tenant."""

        return self.session.scalar(
            select(AdmissionCampaign).where(
                AdmissionCampaign.id == campaign_id,
                AdmissionCampaign.tenant_id == self.actor.tenant_id,
            )
        )

    def create_campaign(self, payload: AdmissionCampaignCreate) -> AdmissionCampaign:
        """Create one admission campaign after validating academic references."""

        academic_year = self._require_entity(AcademicYear, payload.academic_year_id, "academic_year_id")
        program = self._require_entity(Program, payload.program_id, "program_id")
        if payload.ends_on < payload.starts_on:
            raise AdmissionsValidationError("ends_on must be greater than or equal to starts_on")

        campaign = AdmissionCampaign(
            tenant_id=self.actor.tenant_id,
            academic_year_id=academic_year.id,
            program_id=program.id,
            code=payload.code,
            title=payload.title,
            starts_on=payload.starts_on,
            ends_on=payload.ends_on,
            state=payload.state,
        )
        self.session.add(campaign)
        self.session.flush()
        self._audit(
            "admissions.campaign.create",
            "admission_campaign",
            campaign.id,
            {
                "code": campaign.code,
                "academic_year_id": str(campaign.academic_year_id),
                "program_id": str(campaign.program_id),
            },
        )
        return campaign

    def update_campaign(
        self,
        campaign_id: UUID,
        payload: AdmissionCampaignUpdate,
    ) -> AdmissionCampaign | None:
        """Update mutable campaign fields and audit only changed properties."""

        campaign = self.get_campaign(campaign_id)
        if campaign is None:
            return None

        changes: dict[str, object] = {}
        starts_on = payload.starts_on if payload.starts_on is not None else campaign.starts_on
        ends_on = payload.ends_on if payload.ends_on is not None else campaign.ends_on
        if ends_on < starts_on:
            raise AdmissionsValidationError("ends_on must be greater than or equal to starts_on")

        if payload.title is not None and payload.title != campaign.title:
            changes["title"] = {"from": campaign.title, "to": payload.title}
            campaign.title = payload.title
        if payload.starts_on is not None and payload.starts_on != campaign.starts_on:
            changes["starts_on"] = {"from": str(campaign.starts_on), "to": str(payload.starts_on)}
            campaign.starts_on = payload.starts_on
        if payload.ends_on is not None and payload.ends_on != campaign.ends_on:
            changes["ends_on"] = {"from": str(campaign.ends_on), "to": str(payload.ends_on)}
            campaign.ends_on = payload.ends_on
        if payload.state is not None and payload.state != campaign.state:
            changes["state"] = {"from": campaign.state, "to": payload.state}
            campaign.state = payload.state

        if changes:
            self.session.flush()
            self._audit("admissions.campaign.update", "admission_campaign", campaign.id, changes)
        return campaign

    def list_applicants(self, skip: int = 0, limit: int = 100) -> tuple[list[Applicant], int]:
        """List applicants for the current tenant with bounded pagination."""

        query = (
            select(Applicant)
            .where(Applicant.tenant_id == self.actor.tenant_id)
            .order_by(Applicant.first_name, Applicant.last_name)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_own_application_detail(
        self,
    ) -> tuple[Application, Applicant, list[ApplicationDocument]] | None:
        """Return the application bound to the authenticated applicant membership."""

        access = self.session.scalar(
            select(ApplicantAccess).where(
                ApplicantAccess.tenant_id == self.actor.tenant_id,
                ApplicantAccess.membership_id == self.actor.membership_id,
            )
        )
        if access is None:
            return None
        application = self.session.scalar(
            select(Application)
            .where(
                Application.tenant_id == self.actor.tenant_id,
                Application.applicant_id == access.applicant_id,
            )
            .order_by(Application.created_at.desc())
        )
        if application is None:
            return None
        return self.get_application_detail(application.id)

    def update_own_applicant(self, payload: ApplicantUpdate) -> Applicant | None:
        """Update only the applicant identity bound to the actor's membership."""

        detail = self.get_own_application_detail()
        if detail is None:
            return None
        return self.update_applicant(detail[1].id, payload)

    def update_own_application(self, payload: ApplicationUpdate) -> Application | None:
        """Update applicant-editable fields on the bound draft application."""

        detail = self.get_own_application_detail()
        if detail is None:
            return None
        application = detail[0]
        if application.state != "draft":
            raise AdmissionsConflictError("Only draft applications can be edited")
        return self.update_application(application.id, payload)

    def submit_own_application(self) -> Application | None:
        """Submit the bound draft application through the existing state machine."""

        detail = self.get_own_application_detail()
        if detail is None:
            return None
        return self.transition_application_state(
            detail[0].id,
            ApplicationStateTransition(to_state="submitted", reason="Applicant submission"),
        )

    def create_own_uploaded_document(
        self,
        document_type: str,
        document_number: str | None,
        original_filename: str,
        content_type: str,
        stored: StoredMedia,
    ) -> ApplicationDocument | None:
        """Attach one validated private media object to the bound application."""

        detail = self.get_own_application_detail()
        if detail is None:
            return None
        application = detail[0]
        if application.state not in {"draft", "submitted", "under_review"}:
            raise AdmissionsConflictError("Documents cannot be uploaded in the current application state")
        existing = self.session.scalar(
            select(ApplicationDocument).where(
                ApplicationDocument.tenant_id == self.actor.tenant_id,
                ApplicationDocument.application_id == application.id,
                ApplicationDocument.document_type == document_type,
            )
        )
        if existing is not None:
            raise AdmissionsConflictError("A document of this type already exists")
        media = TenantMediaObject(
            tenant_id=self.actor.tenant_id,
            uploaded_by_membership_id=self.actor.membership_id,
            provider=stored.provider,
            object_key=stored.object_key,
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=stored.size_bytes,
            checksum_sha256=stored.checksum_sha256,
            state="available",
        )
        self.session.add(media)
        self.session.flush()
        document = ApplicationDocument(
            tenant_id=self.actor.tenant_id,
            application_id=application.id,
            document_type=document_type,
            document_number=document_number,
            media_object_id=media.id,
            verification_state="pending",
        )
        self.session.add(document)
        self.session.flush()
        self._audit(
            "admissions.document.upload",
            "application_document",
            document.id,
            {
                "application_id": str(application.id),
                "document_type": document_type,
                "media_object_id": str(media.id),
                "size_bytes": media.size_bytes,
            },
        )
        return document

    def get_own_document_media(
        self, document_id: UUID
    ) -> tuple[ApplicationDocument, TenantMediaObject] | None:
        """Return media only when its document belongs to the bound applicant."""

        detail = self.get_own_application_detail()
        if detail is None:
            return None
        document = self.session.scalar(
            select(ApplicationDocument).where(
                ApplicationDocument.tenant_id == self.actor.tenant_id,
                ApplicationDocument.application_id == detail[0].id,
                ApplicationDocument.id == document_id,
                ApplicationDocument.media_object_id.is_not(None),
            )
        )
        if document is None or document.media_object_id is None:
            return None
        media = self.session.scalar(
            select(TenantMediaObject).where(
                TenantMediaObject.tenant_id == self.actor.tenant_id,
                TenantMediaObject.id == document.media_object_id,
                TenantMediaObject.state == "available",
            )
        )
        return (document, media) if media is not None else None

    def get_applicant(self, applicant_id: UUID) -> Applicant | None:
        """Return one applicant by ID for the authenticated tenant."""

        return self.session.scalar(
            select(Applicant).where(
                Applicant.id == applicant_id,
                Applicant.tenant_id == self.actor.tenant_id,
            )
        )

    def create_applicant(self, payload: ApplicantCreate) -> Applicant:
        """Create one applicant while enforcing tenant-safe contact requirements."""

        if not payload.email and not payload.mobile_number:
            raise AdmissionsValidationError("either email or mobile_number is required")
        applicant = Applicant(
            tenant_id=self.actor.tenant_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            mobile_number=payload.mobile_number,
            date_of_birth=payload.date_of_birth,
        )
        self.session.add(applicant)
        self.session.flush()
        self._audit(
            "admissions.applicant.create",
            "applicant",
            applicant.id,
            {"email": applicant.email, "mobile_number": applicant.mobile_number},
        )
        return applicant

    def update_applicant(self, applicant_id: UUID, payload: ApplicantUpdate) -> Applicant | None:
        """Update applicant details and ensure at least one contact channel remains."""

        applicant = self.get_applicant(applicant_id)
        if applicant is None:
            return None

        changes: dict[str, object] = {}
        if payload.first_name is not None and payload.first_name != applicant.first_name:
            changes["first_name"] = {"from": applicant.first_name, "to": payload.first_name}
            applicant.first_name = payload.first_name
        if payload.last_name is not None and payload.last_name != applicant.last_name:
            changes["last_name"] = {"from": applicant.last_name, "to": payload.last_name}
            applicant.last_name = payload.last_name
        if payload.email is not None and payload.email != applicant.email:
            changes["email"] = {"from": applicant.email, "to": payload.email}
            applicant.email = payload.email
        if payload.mobile_number is not None and payload.mobile_number != applicant.mobile_number:
            changes["mobile_number"] = {"from": applicant.mobile_number, "to": payload.mobile_number}
            applicant.mobile_number = payload.mobile_number
        if payload.date_of_birth is not None and payload.date_of_birth != applicant.date_of_birth:
            changes["date_of_birth"] = {
                "from": str(applicant.date_of_birth) if applicant.date_of_birth else None,
                "to": str(payload.date_of_birth),
            }
            applicant.date_of_birth = payload.date_of_birth

        if not applicant.email and not applicant.mobile_number:
            raise AdmissionsValidationError("either email or mobile_number is required")

        if changes:
            self.session.flush()
            self._audit("admissions.applicant.update", "applicant", applicant.id, changes)
        return applicant

    def list_applications(
        self,
        skip: int = 0,
        limit: int = 100,
        campaign_id: UUID | None = None,
        applicant_id: UUID | None = None,
        state: str | None = None,
    ) -> tuple[list[Application], int]:
        """List applications with optional tenant-safe campaign, applicant, and state filters."""

        query = select(Application).where(Application.tenant_id == self.actor.tenant_id)
        if campaign_id is not None:
            query = query.where(Application.campaign_id == campaign_id)
        if applicant_id is not None:
            query = query.where(Application.applicant_id == applicant_id)
        if state is not None:
            query = query.where(Application.state == state)
        query = query.order_by(Application.created_at.desc(), Application.application_number)

        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_application(self, application_id: UUID) -> Application | None:
        """Return one application by ID for the authenticated tenant."""

        return self.session.scalar(
            select(Application).where(
                Application.id == application_id,
                Application.tenant_id == self.actor.tenant_id,
            )
        )

    def get_application_detail(
        self,
        application_id: UUID,
    ) -> tuple[Application, Applicant, list[ApplicationDocument]] | None:
        """Return one application with its applicant and documents in bounded queries."""

        application = self.get_application(application_id)
        if application is None:
            return None
        applicant = self.session.scalar(
            select(Applicant).where(
                Applicant.id == application.applicant_id,
                Applicant.tenant_id == self.actor.tenant_id,
            )
        )
        if applicant is None:
            return None
        documents = list(
            self.session.scalars(
                select(ApplicationDocument)
                .where(
                    ApplicationDocument.tenant_id == self.actor.tenant_id,
                    ApplicationDocument.application_id == application.id,
                )
                .order_by(ApplicationDocument.document_type)
            )
        )
        return application, applicant, documents

    def get_application_history(
        self,
        application_id: UUID,
        limit: int = 100,
    ) -> list[AuditEvent] | None:
        """Return application and child-document audit history in reverse chronology."""

        application = self.get_application(application_id)
        if application is None:
            return None
        document_ids = select(ApplicationDocument.id).where(
            ApplicationDocument.tenant_id == self.actor.tenant_id,
            ApplicationDocument.application_id == application.id,
        )
        return list(
            self.session.scalars(
                select(AuditEvent)
                .where(
                    AuditEvent.tenant_id == self.actor.tenant_id,
                    (
                        (AuditEvent.entity_type == "application")
                        & (AuditEvent.entity_id == application.id)
                    )
                    | (
                        (AuditEvent.entity_type == "application_document")
                        & AuditEvent.entity_id.in_(document_ids)
                    ),
                )
                .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
                .limit(limit)
            )
        )

    def create_application(self, payload: ApplicationCreate) -> Application:
        """Create one application and validate campaign, applicant, and program references."""

        campaign = self._require_entity(AdmissionCampaign, payload.campaign_id, "campaign_id")
        applicant = self._require_entity(Applicant, payload.applicant_id, "applicant_id")
        program = self._require_entity(Program, payload.program_id, "program_id")

        if campaign.academic_year_id != self._require_entity(
            AcademicYear, campaign.academic_year_id, "academic_year_id"
        ).id:
            raise AdmissionsValidationError("Campaign academic year is not valid for this tenant")
        if campaign.program_id != program.id:
            raise AdmissionsValidationError("Application program_id must match campaign program")

        submitted_at = payload.submitted_at
        if payload.state == "submitted" and submitted_at is None:
            submitted_at = datetime.now(UTC)

        application = Application(
            tenant_id=self.actor.tenant_id,
            campaign_id=campaign.id,
            applicant_id=applicant.id,
            program_id=program.id,
            application_number=payload.application_number,
            state=payload.state,
            submitted_at=submitted_at,
            remarks=payload.remarks,
        )
        self.session.add(application)
        self.session.flush()
        self._audit(
            "admissions.application.create",
            "application",
            application.id,
            {
                "application_number": application.application_number,
                "state": application.state,
                "campaign_id": str(application.campaign_id),
                "applicant_id": str(application.applicant_id),
            },
        )
        return application

    def update_application(
        self,
        application_id: UUID,
        payload: ApplicationUpdate,
    ) -> Application | None:
        """Update mutable application attributes without bypassing lifecycle transitions."""

        application = self.get_application(application_id)
        if application is None:
            return None

        changes: dict[str, object] = {}
        if payload.remarks is not None and payload.remarks != application.remarks:
            changes["remarks"] = {"from": application.remarks, "to": payload.remarks}
            application.remarks = payload.remarks
        if payload.submitted_at is not None and payload.submitted_at != application.submitted_at:
            changes["submitted_at"] = {
                "from": application.submitted_at.isoformat() if application.submitted_at else None,
                "to": payload.submitted_at.isoformat(),
            }
            application.submitted_at = payload.submitted_at

        if changes:
            self.session.flush()
            self._audit("admissions.application.update", "application", application.id, changes)
        return application

    def transition_application_state(
        self,
        application_id: UUID,
        payload: ApplicationStateTransition,
    ) -> Application | None:
        """Apply a controlled application state transition following the required state machine."""

        application = self.get_application(application_id)
        if application is None:
            return None

        if payload.to_state in {"offered", "accepted"}:
            raise AdmissionsValidationError(
                "Use offer issuance/acceptance workflows for offered and accepted states"
            )

        self._validate_transition(
            APPLICATION_TRANSITIONS,
            from_state=application.state,
            to_state=payload.to_state,
            label="application",
        )
        if payload.to_state == application.state:
            return application

        previous_state = application.state
        application.state = payload.to_state
        if payload.to_state == "submitted" and application.submitted_at is None:
            application.submitted_at = datetime.now(UTC)
        application.remarks = self._append_reason(application.remarks, payload.reason)
        self.session.flush()
        self._audit(
            "admissions.application.transition",
            "application",
            application.id,
            {
                "from_state": previous_state,
                "to_state": payload.to_state,
                "reason": payload.reason,
            },
        )
        return application

    def list_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        application_id: UUID | None = None,
    ) -> tuple[list[ApplicationDocument], int]:
        """List application documents with optional tenant-safe application filtering."""

        query = select(ApplicationDocument).where(ApplicationDocument.tenant_id == self.actor.tenant_id)
        if application_id is not None:
            query = query.where(ApplicationDocument.application_id == application_id)
        query = query.order_by(ApplicationDocument.created_at.desc(), ApplicationDocument.document_type)

        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_document(self, document_id: UUID) -> ApplicationDocument | None:
        """Return one application document by ID for the authenticated tenant."""

        return self.session.scalar(
            select(ApplicationDocument).where(
                ApplicationDocument.id == document_id,
                ApplicationDocument.tenant_id == self.actor.tenant_id,
            )
        )

    def get_document_media(
        self, document_id: UUID
    ) -> tuple[ApplicationDocument, TenantMediaObject] | None:
        """Return available private media for one tenant document."""

        document = self.get_document(document_id)
        if document is None or document.media_object_id is None:
            return None
        media = self.session.scalar(
            select(TenantMediaObject).where(
                TenantMediaObject.tenant_id == self.actor.tenant_id,
                TenantMediaObject.id == document.media_object_id,
                TenantMediaObject.state == "available",
            )
        )
        return (document, media) if media is not None else None

    def create_document(self, payload: ApplicationDocumentCreate) -> ApplicationDocument:
        """Create one application document after validating its parent application."""

        application = self._require_entity(Application, payload.application_id, "application_id")
        document = ApplicationDocument(
            tenant_id=self.actor.tenant_id,
            application_id=application.id,
            document_type=payload.document_type,
            document_number=payload.document_number,
            file_url=payload.file_url,
            verification_state=payload.verification_state,
            verified_at=payload.verified_at,
            verified_by=payload.verified_by,
            verification_notes=payload.verification_notes,
        )
        self.session.add(document)
        self.session.flush()
        self._audit(
            "admissions.document.create",
            "application_document",
            document.id,
            {
                "application_id": str(document.application_id),
                "document_type": document.document_type,
                "verification_state": document.verification_state,
            },
        )
        return document

    def update_document(
        self,
        document_id: UUID,
        payload: ApplicationDocumentUpdate,
    ) -> ApplicationDocument | None:
        """Update mutable document fields and preserve verification workflow integrity."""

        document = self.get_document(document_id)
        if document is None:
            return None

        changes: dict[str, object] = {}
        if payload.document_number is not None and payload.document_number != document.document_number:
            changes["document_number"] = {"from": document.document_number, "to": payload.document_number}
            document.document_number = payload.document_number
        if payload.file_url is not None and payload.file_url != document.file_url:
            changes["file_url"] = {"from": document.file_url, "to": payload.file_url}
            document.file_url = payload.file_url
        if payload.verification_notes is not None and payload.verification_notes != document.verification_notes:
            changes["verification_notes"] = {
                "from": document.verification_notes,
                "to": payload.verification_notes,
            }
            document.verification_notes = payload.verification_notes

        if changes:
            self.session.flush()
            self._audit("admissions.document.update", "application_document", document.id, changes)
        return document

    def transition_document_verification(
        self,
        document_id: UUID,
        payload: ApplicationDocumentVerificationTransition,
    ) -> ApplicationDocument | None:
        """Transition application document verification state with controlled lifecycle rules."""

        document = self.get_document(document_id)
        if document is None:
            return None

        self._validate_transition(
            DOCUMENT_TRANSITIONS,
            from_state=document.verification_state,
            to_state=payload.to_state,
            label="document",
        )
        if payload.to_state == document.verification_state:
            return document

        previous_state = document.verification_state
        document.verification_state = payload.to_state
        if payload.to_state == "verified":
            document.verified_at = payload.verified_at or datetime.now(UTC)
            document.verified_by = payload.verified_by or str(self.actor.account_id)
        else:
            document.verified_at = payload.verified_at
            document.verified_by = payload.verified_by
        if payload.verification_notes is not None:
            document.verification_notes = payload.verification_notes

        self.session.flush()
        self._audit(
            "admissions.document.transition",
            "application_document",
            document.id,
            {
                "from_state": previous_state,
                "to_state": payload.to_state,
            },
        )
        return document

    def list_seat_pools(
        self,
        skip: int = 0,
        limit: int = 100,
        campaign_id: UUID | None = None,
    ) -> tuple[list[SeatPool], int]:
        """List seat pools with optional tenant-safe campaign filtering."""

        query = select(SeatPool).where(SeatPool.tenant_id == self.actor.tenant_id)
        if campaign_id is not None:
            query = query.where(SeatPool.campaign_id == campaign_id)
        query = query.order_by(SeatPool.category_code)

        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_seat_pool(self, seat_pool_id: UUID) -> SeatPool | None:
        """Return one seat pool by ID for the authenticated tenant."""

        return self.session.scalar(
            select(SeatPool).where(SeatPool.id == seat_pool_id, SeatPool.tenant_id == self.actor.tenant_id)
        )

    def create_seat_pool(self, payload: SeatPoolCreate) -> SeatPool:
        """Create one seat pool for a tenant campaign and enforce capacity bounds."""

        campaign = self._require_entity(AdmissionCampaign, payload.campaign_id, "campaign_id")
        if payload.filled_seats > payload.seat_capacity:
            raise AdmissionsValidationError("filled_seats must be less than or equal to seat_capacity")

        seat_pool = SeatPool(
            tenant_id=self.actor.tenant_id,
            campaign_id=campaign.id,
            category_code=payload.category_code,
            category_name=payload.category_name,
            seat_capacity=payload.seat_capacity,
            filled_seats=payload.filled_seats,
        )
        self.session.add(seat_pool)
        self.session.flush()
        self._audit(
            "admissions.seat_pool.create",
            "seat_pool",
            seat_pool.id,
            {
                "campaign_id": str(seat_pool.campaign_id),
                "category_code": seat_pool.category_code,
                "seat_capacity": seat_pool.seat_capacity,
            },
        )
        return seat_pool

    def update_seat_pool(self, seat_pool_id: UUID, payload: SeatPoolUpdate) -> SeatPool | None:
        """Update seat pool capacity details while preserving non-negative seat availability."""

        seat_pool = self.get_seat_pool(seat_pool_id)
        if seat_pool is None:
            return None

        next_capacity = payload.seat_capacity if payload.seat_capacity is not None else seat_pool.seat_capacity
        next_filled = payload.filled_seats if payload.filled_seats is not None else seat_pool.filled_seats
        if next_filled > next_capacity:
            raise AdmissionsValidationError("filled_seats must be less than or equal to seat_capacity")

        changes: dict[str, object] = {}
        if payload.category_name is not None and payload.category_name != seat_pool.category_name:
            changes["category_name"] = {"from": seat_pool.category_name, "to": payload.category_name}
            seat_pool.category_name = payload.category_name
        if payload.seat_capacity is not None and payload.seat_capacity != seat_pool.seat_capacity:
            changes["seat_capacity"] = {"from": seat_pool.seat_capacity, "to": payload.seat_capacity}
            seat_pool.seat_capacity = payload.seat_capacity
        if payload.filled_seats is not None and payload.filled_seats != seat_pool.filled_seats:
            changes["filled_seats"] = {"from": seat_pool.filled_seats, "to": payload.filled_seats}
            seat_pool.filled_seats = payload.filled_seats

        if changes:
            self.session.flush()
            self._audit("admissions.seat_pool.update", "seat_pool", seat_pool.id, changes)
        return seat_pool

    def list_offers(
        self,
        skip: int = 0,
        limit: int = 100,
        application_id: UUID | None = None,
        state: str | None = None,
    ) -> tuple[list[AdmissionOffer], int]:
        """List admission offers with optional tenant-safe filters by application and state."""

        query = select(AdmissionOffer).where(AdmissionOffer.tenant_id == self.actor.tenant_id)
        if application_id is not None:
            query = query.where(AdmissionOffer.application_id == application_id)
        if state is not None:
            query = query.where(AdmissionOffer.state == state)
        query = query.order_by(AdmissionOffer.created_at.desc(), AdmissionOffer.offer_number)

        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return items, total

    def get_offer(self, offer_id: UUID) -> AdmissionOffer | None:
        """Return one admission offer by ID for the authenticated tenant."""

        return self.session.scalar(
            select(AdmissionOffer).where(
                AdmissionOffer.id == offer_id,
                AdmissionOffer.tenant_id == self.actor.tenant_id,
            )
        )

    def create_offer(self, payload: AdmissionOfferCreate) -> AdmissionOffer:
        """Issue one admission offer for a selected application and set application to offered."""

        application = self._require_entity(Application, payload.application_id, "application_id")
        seat_pool = self._require_entity(SeatPool, payload.seat_pool_id, "seat_pool_id")

        if payload.state != "issued":
            raise AdmissionsValidationError("New offers must start in issued state")
        if application.state != "selected":
            raise AdmissionsValidationError("Application must be in selected state before issuing an offer")
        if application.campaign_id != seat_pool.campaign_id:
            raise AdmissionsValidationError("seat_pool_id must belong to the same campaign as the application")

        existing_offer = self.session.scalar(
            select(AdmissionOffer).where(
                AdmissionOffer.tenant_id == self.actor.tenant_id,
                AdmissionOffer.application_id == application.id,
            )
        )
        if existing_offer is not None:
            raise AdmissionsConflictError("An offer already exists for this application")

        previous_state = application.state
        application.state = "offered"
        offer = AdmissionOffer(
            tenant_id=self.actor.tenant_id,
            application_id=application.id,
            seat_pool_id=seat_pool.id,
            offer_number=payload.offer_number,
            offered_on=payload.offered_on,
            expires_on=payload.expires_on,
            state="issued",
            notes=payload.notes,
        )
        self.session.add(offer)
        self.session.flush()

        self._audit(
            "admissions.offer.issue",
            "admission_offer",
            offer.id,
            {
                "application_id": str(offer.application_id),
                "seat_pool_id": str(offer.seat_pool_id),
                "from_state": None,
                "to_state": "issued",
            },
        )
        self._audit(
            "admissions.application.transition",
            "application",
            application.id,
            {
                "from_state": previous_state,
                "to_state": application.state,
                "reason": "offer issued",
            },
        )
        return offer

    def update_offer(self, offer_id: UUID, payload: AdmissionOfferUpdate) -> AdmissionOffer | None:
        """Update mutable offer details without changing controlled lifecycle state."""

        offer = self.get_offer(offer_id)
        if offer is None:
            return None

        if payload.expires_on is not None and payload.expires_on < offer.offered_on:
            raise AdmissionsValidationError("expires_on must be greater than or equal to offered_on")

        changes: dict[str, object] = {}
        if payload.expires_on is not None and payload.expires_on != offer.expires_on:
            changes["expires_on"] = {"from": str(offer.expires_on), "to": str(payload.expires_on)}
            offer.expires_on = payload.expires_on
        if payload.notes is not None and payload.notes != offer.notes:
            changes["notes"] = {"from": offer.notes, "to": payload.notes}
            offer.notes = payload.notes

        if changes:
            self.session.flush()
            self._audit("admissions.offer.update", "admission_offer", offer.id, changes)
        return offer

    def transition_offer_state(
        self,
        offer_id: UUID,
        payload: AdmissionOfferStateTransition,
    ) -> AdmissionOffer | None:
        """Transition offer state, including atomic acceptance with seat allocation."""

        if payload.to_state == "accepted":
            return self.accept_offer(offer_id)

        offer = self.get_offer(offer_id)
        if offer is None:
            return None

        self._validate_transition(
            OFFER_TRANSITIONS,
            from_state=offer.state,
            to_state=payload.to_state,
            label="offer",
        )
        if payload.to_state == offer.state:
            return offer

        previous_state = offer.state
        offer.state = payload.to_state
        if payload.reason:
            offer.notes = self._append_reason(offer.notes, payload.reason)
        self.session.flush()
        self._audit(
            "admissions.offer.transition",
            "admission_offer",
            offer.id,
            {
                "from_state": previous_state,
                "to_state": payload.to_state,
                "reason": payload.reason,
            },
        )
        return offer

    def accept_offer(self, offer_id: UUID) -> AdmissionOffer | None:
        """Accept an issued offer atomically, allocate one seat, and accept the application."""

        offer = self._offer_for_update(offer_id)
        if offer is None:
            return None
        if offer.state != "issued":
            raise AdmissionsValidationError("Only issued offers can be accepted")

        application = self._application_for_update(offer.application_id)
        if application is None:
            raise AdmissionsValidationError("Offer references a missing application")
        if application.state != "offered":
            raise AdmissionsValidationError("Application must be in offered state to accept an offer")

        seat_pool = self._seat_pool_for_update(offer.seat_pool_id)
        if seat_pool is None:
            raise AdmissionsValidationError("Offer references a missing seat pool")
        if application.campaign_id != seat_pool.campaign_id:
            raise AdmissionsValidationError("Seat pool campaign does not match application campaign")

        available_seats = seat_pool.seat_capacity - seat_pool.filled_seats
        if available_seats <= 0:
            raise AdmissionsConflictError("No seats available in the selected seat pool")

        offer_previous_state = offer.state
        application_previous_state = application.state
        seat_pool_previous_filled = seat_pool.filled_seats

        seat_pool.filled_seats += 1
        offer.state = "accepted"
        application.state = "accepted"
        self.session.flush()

        self._audit(
            "admissions.offer.transition",
            "admission_offer",
            offer.id,
            {"from_state": offer_previous_state, "to_state": offer.state, "reason": "offer accepted"},
        )
        self._audit(
            "admissions.application.transition",
            "application",
            application.id,
            {
                "from_state": application_previous_state,
                "to_state": application.state,
                "reason": "offer accepted",
            },
        )
        self._audit(
            "admissions.seat_pool.allocate",
            "seat_pool",
            seat_pool.id,
            {
                "from_filled_seats": seat_pool_previous_filled,
                "to_filled_seats": seat_pool.filled_seats,
                "offer_id": str(offer.id),
            },
        )
        return offer