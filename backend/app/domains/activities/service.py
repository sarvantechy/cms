"""Business logic for tenant-safe activities, attendance, and achievements."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.domains.academics.models import CollegeSetting
from app.domains.activities.models import (
    Achievement,
    Activity,
    ActivityApprovalRequest,
    ActivityCertificate,
    ActivityClub,
    ActivityExpense,
    ActivityPoint,
    ActivityTeam,
    ActivityTeamMember,
    EventRegistration,
)
from app.domains.activities.schemas import (
    AchievementCreate,
    ActivityApprovalCreate,
    ActivityApprovalReview,
    ActivityCertificateCreate,
    ActivityCertificateDocument,
    ActivityClubCreate,
    ActivityCreate,
    ActivityExpenseCreate,
    ActivityExpenseReview,
    ActivityPointCreate,
    ActivityTeamCreate,
    ActivityTeamMemberCreate,
    ActivityUpdate,
    EventRegistrationCreate,
    EventRegistrationReview,
)
from app.domains.audit.models import AuditEvent
from app.domains.students.models import Person, Student
from app.domains.tenancy.models import Tenant
from app.security_context import ActorContext, resolve_actor_student_ids

INVALID_ACTIVITY_REFERENCE = "Invalid activity reference"


class ActivitiesDomainError(Exception):
    """Represent one controlled activities domain error."""

    def __init__(self, detail: str, status_code: int) -> None:
        """Initialize the error with client-safe detail and HTTP status."""

        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class ActivitiesValidationError(ActivitiesDomainError):
    """Represent one validation error mapped to HTTP 422."""

    def __init__(self, detail: str) -> None:
        """Initialize an activities validation error."""

        super().__init__(detail, 422)


class ActivitiesConflictError(ActivitiesDomainError):
    """Represent one conflict error mapped to HTTP 409."""

    def __init__(self, detail: str) -> None:
        """Initialize an activities conflict error."""

        super().__init__(detail, 409)


class ActivitiesAuthorizationError(ActivitiesDomainError):
    """Represent an activity authorization failure mapped to HTTP 403."""

    def __init__(self, detail: str) -> None:
        """Initialize an activities authorization error."""

        super().__init__(detail, 403)


class ActivitiesService:
    """Manage tenant activities, event registrations, and achievement publication."""

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

    def _get_activity(self, activity_id: UUID) -> Activity | None:
        """Return an activity when it belongs to the actor's tenant."""

        return self.session.scalar(
            select(Activity).where(Activity.tenant_id == self.actor.tenant_id, Activity.id == activity_id)
        )

    def _get_registration(self, registration_id: UUID) -> EventRegistration | None:
        """Return an event registration in the actor's tenant."""

        return self.session.scalar(
            select(EventRegistration).where(
                EventRegistration.tenant_id == self.actor.tenant_id,
                EventRegistration.id == registration_id,
            )
        )

    def _require_student(self, student_id: UUID) -> Student:
        """Return a tenant student or raise a validation error."""

        student = self.session.scalar(
            select(Student).where(Student.tenant_id == self.actor.tenant_id, Student.id == student_id)
        )
        if student is None:
            raise ActivitiesValidationError("Invalid student reference")
        return student

    def _require_participant(
        self,
        activity_id: UUID,
        student_id: UUID,
        states: tuple[str, ...] = ("approved", "attended"),
    ) -> EventRegistration:
        """Return one qualifying participant registration or raise a conflict."""

        registration = self.session.scalar(
            select(EventRegistration).where(
                EventRegistration.tenant_id == self.actor.tenant_id,
                EventRegistration.activity_id == activity_id,
                EventRegistration.student_id == student_id,
                EventRegistration.state.in_(states),
            )
        )
        if registration is None:
            raise ActivitiesConflictError("Operation requires an approved participant")
        return registration

    def list_clubs(self, skip: int = 0, limit: int = 100):
        """List managed activity clubs for the current tenant."""

        query = (
            select(ActivityClub)
            .where(ActivityClub.tenant_id == self.actor.tenant_id)
            .order_by(ActivityClub.name)
        )
        return self._paginate(query, skip, limit)

    def create_club(self, payload: ActivityClubCreate) -> ActivityClub:
        """Create and audit one activity club."""

        item = ActivityClub(tenant_id=self.actor.tenant_id, **payload.model_dump())
        self.session.add(item)
        self.session.flush()
        self._audit("activities.club.create", "activity_club", item.id, {"name": item.name})
        return item

    def list_activities(
        self,
        skip: int = 0,
        limit: int = 100,
        state: str | None = None,
        activity_type: str | None = None,
    ):
        """List tenant activities with optional state and type filters."""

        query = select(Activity).where(Activity.tenant_id == self.actor.tenant_id)
        if not self.actor.has_permission("activities.records.manage"):
            query = query.where(Activity.state == "published")
        if state is not None:
            query = query.where(Activity.state == state)
        if activity_type is not None:
            query = query.where(Activity.activity_type == activity_type)
        query = query.order_by(Activity.activity_date.desc(), Activity.created_at.desc())
        return self._paginate(query, skip, limit)

    def create_activity(self, payload: ActivityCreate) -> Activity:
        """Create and audit a tenant activity."""

        if payload.activity_date < datetime.now(UTC).date() and payload.state == "draft":
            raise ActivitiesValidationError("Past activities cannot be created in draft state")
        if payload.club_id is not None and self.session.scalar(
            select(ActivityClub.id).where(
                ActivityClub.tenant_id == self.actor.tenant_id,
                ActivityClub.id == payload.club_id,
            )
        ) is None:
            raise ActivitiesValidationError("Invalid activity club reference")
        item = Activity(tenant_id=self.actor.tenant_id, **payload.model_dump())
        self.session.add(item)
        self.session.flush()
        self._audit("activities.event.create", "activity", item.id, {"state": item.state})
        return item

    def update_activity(self, activity_id: UUID, payload: ActivityUpdate) -> Activity | None:
        """Update a mutable tenant activity and audit changed fields."""

        item = self._get_activity(activity_id)
        if item is None:
            return None
        if item.state == "completed":
            raise ActivitiesConflictError("Completed activities cannot be modified")

        if payload.state == "published":
            unresolved = self.session.scalar(
                select(func.count())
                .select_from(ActivityApprovalRequest)
                .where(
                    ActivityApprovalRequest.tenant_id == self.actor.tenant_id,
                    ActivityApprovalRequest.activity_id == activity_id,
                    ActivityApprovalRequest.state != "approved",
                )
            ) or 0
            if unresolved:
                raise ActivitiesConflictError("All venue and budget requests must be approved before publication")

        changes: dict[str, object] = {}
        for field, value in payload.model_dump(exclude_unset=True).items():
            current_value = getattr(item, field)
            if current_value != value:
                changes[field] = {"from": str(current_value), "to": str(value)}
                setattr(item, field, value)

        if changes:
            self.session.flush()
            self._audit("activities.event.update", "activity", item.id, changes)
        return item

    def list_registrations(self, activity_id: UUID, skip: int = 0, limit: int = 100):
        """List registrations for one tenant activity."""

        if self._get_activity(activity_id) is None:
            raise ActivitiesValidationError(INVALID_ACTIVITY_REFERENCE)
        query = (
            select(EventRegistration)
            .where(
                EventRegistration.tenant_id == self.actor.tenant_id,
                EventRegistration.activity_id == activity_id,
            )
            .order_by(EventRegistration.created_at.desc())
        )
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            query = query.where(EventRegistration.student_id.in_(student_ids))
        return self._paginate(query, skip, limit)

    def register_student(self, activity_id: UUID, payload: EventRegistrationCreate) -> EventRegistration:
        """Register a tenant student while enforcing capacity and uniqueness."""

        activity = self._get_activity(activity_id)
        if activity is None:
            raise ActivitiesValidationError(INVALID_ACTIVITY_REFERENCE)
        if activity.state in {"cancelled", "completed"}:
            raise ActivitiesConflictError("Registration is not allowed for cancelled or completed activities")
        if not self.actor.has_permission("activities.records.manage"):
            if not self.actor.has_permission("activities.self.register"):
                raise ActivitiesAuthorizationError("Activity registration permission is required")
            if activity.state != "published":
                raise ActivitiesConflictError("Students may register only for published activities")
            student_ids = resolve_actor_student_ids(self.session, self.actor)
            if student_ids is None or payload.student_id not in student_ids:
                raise ActivitiesValidationError("Students may register only their own record")

        self._require_student(payload.student_id)

        existing = self.session.scalar(
            select(EventRegistration).where(
                EventRegistration.tenant_id == self.actor.tenant_id,
                EventRegistration.activity_id == activity_id,
                EventRegistration.student_id == payload.student_id,
            )
        )
        if existing is not None:
            raise ActivitiesConflictError("Student is already registered for this activity")

        approved_count = self.session.scalar(
            select(func.count())
            .select_from(EventRegistration)
            .where(
                EventRegistration.tenant_id == self.actor.tenant_id,
                EventRegistration.activity_id == activity_id,
                EventRegistration.state.in_(("approved", "attended")),
            )
        ) or 0
        if activity.capacity is not None and approved_count >= activity.capacity:
            raise ActivitiesConflictError("Activity capacity reached")

        item = EventRegistration(
            tenant_id=self.actor.tenant_id,
            activity_id=activity_id,
            student_id=payload.student_id,
            state=payload.state,
        )
        self.session.add(item)
        self.session.flush()
        self._audit("activities.registration.create", "event_registration", item.id, {"state": item.state})
        return item

    def approve_registration(self, registration_id: UUID, payload: EventRegistrationReview) -> EventRegistration:
        """Review an event registration while enforcing activity capacity."""

        item = self._get_registration(registration_id)
        if item is None:
            raise ActivitiesValidationError("Invalid registration reference")

        activity = self._get_activity(item.activity_id)
        if activity is None:
            raise ActivitiesValidationError(INVALID_ACTIVITY_REFERENCE)
        if activity.state in {"cancelled", "completed"}:
            raise ActivitiesConflictError("Registration cannot be approved for cancelled or completed activities")

        if payload.state == "approved":
            approved_count = self.session.scalar(
                select(func.count())
                .select_from(EventRegistration)
                .where(
                    EventRegistration.tenant_id == self.actor.tenant_id,
                    EventRegistration.activity_id == item.activity_id,
                    EventRegistration.state.in_(("approved", "attended")),
                    EventRegistration.id != item.id,
                )
            ) or 0
            if activity.capacity is not None and approved_count >= activity.capacity:
                raise ActivitiesConflictError("Activity capacity reached")

        item.state = payload.state
        self.session.flush()
        self._audit("activities.registration.review", "event_registration", item.id, {"state": item.state})
        return item

    def mark_attended(self, registration_id: UUID) -> EventRegistration:
        """Mark an approved registration as attended."""

        item = self._get_registration(registration_id)
        if item is None:
            raise ActivitiesValidationError("Invalid registration reference")
        if item.state != "approved":
            raise ActivitiesConflictError("Only approved registrations can be marked attended")
        item.state = "attended"
        self.session.flush()
        self._audit("activities.registration.attendance", "event_registration", item.id, {"state": item.state})
        return item

    def list_achievements(
        self,
        skip: int = 0,
        limit: int = 100,
        student_id: UUID | None = None,
        activity_id: UUID | None = None,
    ):
        """List tenant achievements with optional student and activity filters."""

        query = select(Achievement).where(Achievement.tenant_id == self.actor.tenant_id)
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            query = query.where(Achievement.student_id.in_(student_ids))
        if student_id is not None:
            query = query.where(Achievement.student_id == student_id)
        if activity_id is not None:
            query = query.where(Achievement.activity_id == activity_id)
        query = query.order_by(Achievement.created_at.desc())
        return self._paginate(query, skip, limit)

    def create_achievement(self, payload: AchievementCreate) -> Achievement:
        """Create an achievement for an approved or attended participant."""

        self._require_student(payload.student_id)
        if self._get_activity(payload.activity_id) is None:
            raise ActivitiesValidationError(INVALID_ACTIVITY_REFERENCE)

        registration = self.session.scalar(
            select(EventRegistration).where(
                EventRegistration.tenant_id == self.actor.tenant_id,
                EventRegistration.activity_id == payload.activity_id,
                EventRegistration.student_id == payload.student_id,
                EventRegistration.state.in_(("approved", "attended")),
            )
        )
        if registration is None:
            raise ActivitiesConflictError("Achievement requires an approved or attended registration")

        item = Achievement(tenant_id=self.actor.tenant_id, **payload.model_dump())
        self.session.add(item)
        self.session.flush()
        self._audit("activities.achievement.create", "achievement", item.id, {"title": item.title})
        return item

    def list_approvals(self, activity_id: UUID, skip: int = 0, limit: int = 100):
        """List venue and budget approval requests for one activity."""

        if self._get_activity(activity_id) is None:
            raise ActivitiesValidationError(INVALID_ACTIVITY_REFERENCE)
        query = (
            select(ActivityApprovalRequest)
            .where(
                ActivityApprovalRequest.tenant_id == self.actor.tenant_id,
                ActivityApprovalRequest.activity_id == activity_id,
            )
            .order_by(ActivityApprovalRequest.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def create_approval(
        self,
        activity_id: UUID,
        payload: ActivityApprovalCreate,
    ) -> ActivityApprovalRequest:
        """Create one venue or budget approval request for a draft activity."""

        activity = self._get_activity(activity_id)
        if activity is None:
            raise ActivitiesValidationError(INVALID_ACTIVITY_REFERENCE)
        if activity.state != "draft":
            raise ActivitiesConflictError("Approval requests can be added only to draft activities")
        if payload.request_type == "budget" and payload.amount is None:
            raise ActivitiesValidationError("Budget approval requires an amount")
        item = ActivityApprovalRequest(
            tenant_id=self.actor.tenant_id,
            activity_id=activity_id,
            **payload.model_dump(),
        )
        self.session.add(item)
        self.session.flush()
        self._audit(
            "activities.approval.create",
            "activity_approval_request",
            item.id,
            {"request_type": item.request_type},
        )
        return item

    def review_approval(
        self,
        approval_id: UUID,
        payload: ActivityApprovalReview,
    ) -> ActivityApprovalRequest:
        """Approve or reject one pending activity resource request."""

        item = self.session.scalar(
            select(ActivityApprovalRequest).where(
                ActivityApprovalRequest.tenant_id == self.actor.tenant_id,
                ActivityApprovalRequest.id == approval_id,
            )
        )
        if item is None:
            raise ActivitiesValidationError("Invalid approval request reference")
        if item.state != "pending":
            raise ActivitiesConflictError("Only pending approval requests can be reviewed")
        item.state = payload.state
        item.review_comment = payload.review_comment
        item.reviewed_by_membership_id = self.actor.membership_id
        item.reviewed_at = datetime.now(UTC)
        self.session.flush()
        self._audit(
            "activities.approval.review",
            "activity_approval_request",
            item.id,
            {"state": item.state},
        )
        return item

    def list_teams(self, activity_id: UUID, skip: int = 0, limit: int = 100):
        """List teams for one activity."""

        if self._get_activity(activity_id) is None:
            raise ActivitiesValidationError(INVALID_ACTIVITY_REFERENCE)
        query = (
            select(ActivityTeam)
            .where(
                ActivityTeam.tenant_id == self.actor.tenant_id,
                ActivityTeam.activity_id == activity_id,
            )
            .order_by(ActivityTeam.name)
        )
        return self._paginate(query, skip, limit)

    def create_team(self, activity_id: UUID, payload: ActivityTeamCreate) -> ActivityTeam:
        """Create one team using an optional approved participant as captain."""

        if self._get_activity(activity_id) is None:
            raise ActivitiesValidationError(INVALID_ACTIVITY_REFERENCE)
        if payload.captain_student_id is not None:
            self._require_participant(activity_id, payload.captain_student_id)
        item = ActivityTeam(
            tenant_id=self.actor.tenant_id,
            activity_id=activity_id,
            **payload.model_dump(),
        )
        self.session.add(item)
        self.session.flush()
        self._audit("activities.team.create", "activity_team", item.id, {"name": item.name})
        return item

    def add_team_member(
        self,
        team_id: UUID,
        payload: ActivityTeamMemberCreate,
    ) -> ActivityTeamMember:
        """Add one approved activity participant to a tenant team."""

        team = self.session.scalar(
            select(ActivityTeam).where(
                ActivityTeam.tenant_id == self.actor.tenant_id,
                ActivityTeam.id == team_id,
            )
        )
        if team is None:
            raise ActivitiesValidationError("Invalid activity team reference")
        self._require_participant(team.activity_id, payload.student_id)
        item = ActivityTeamMember(
            tenant_id=self.actor.tenant_id,
            team_id=team_id,
            student_id=payload.student_id,
        )
        self.session.add(item)
        self.session.flush()
        self._audit("activities.team.member.add", "activity_team_member", item.id, {})
        return item

    def list_team_members(self, team_id: UUID, skip: int = 0, limit: int = 100):
        """List approved participants assigned to one tenant activity team."""

        team_exists = self.session.scalar(
            select(ActivityTeam.id).where(
                ActivityTeam.tenant_id == self.actor.tenant_id,
                ActivityTeam.id == team_id,
            )
        )
        if team_exists is None:
            raise ActivitiesValidationError("Invalid activity team reference")
        query = (
            select(ActivityTeamMember)
            .where(
                ActivityTeamMember.tenant_id == self.actor.tenant_id,
                ActivityTeamMember.team_id == team_id,
            )
            .order_by(ActivityTeamMember.created_at)
        )
        return self._paginate(query, skip, limit)

    def list_expenses(self, activity_id: UUID, skip: int = 0, limit: int = 100):
        """List submitted and reviewed expenses for one activity."""

        if self._get_activity(activity_id) is None:
            raise ActivitiesValidationError(INVALID_ACTIVITY_REFERENCE)
        query = (
            select(ActivityExpense)
            .where(
                ActivityExpense.tenant_id == self.actor.tenant_id,
                ActivityExpense.activity_id == activity_id,
            )
            .order_by(ActivityExpense.created_at.desc())
        )
        return self._paginate(query, skip, limit)

    def create_expense(self, activity_id: UUID, payload: ActivityExpenseCreate) -> ActivityExpense:
        """Submit one expense for an existing activity."""

        if self._get_activity(activity_id) is None:
            raise ActivitiesValidationError(INVALID_ACTIVITY_REFERENCE)
        item = ActivityExpense(
            tenant_id=self.actor.tenant_id,
            activity_id=activity_id,
            **payload.model_dump(),
        )
        self.session.add(item)
        self.session.flush()
        self._audit("activities.expense.create", "activity_expense", item.id, {"amount": str(item.amount)})
        return item

    def review_expense(
        self,
        expense_id: UUID,
        payload: ActivityExpenseReview,
    ) -> ActivityExpense:
        """Approve or reject one submitted expense within the approved budget."""

        item = self.session.scalar(
            select(ActivityExpense).where(
                ActivityExpense.tenant_id == self.actor.tenant_id,
                ActivityExpense.id == expense_id,
            )
        )
        if item is None:
            raise ActivitiesValidationError("Invalid activity expense reference")
        if item.state != "submitted":
            raise ActivitiesConflictError("Only submitted expenses can be reviewed")
        if payload.state == "approved":
            approved_budget = self.session.scalar(
                select(ActivityApprovalRequest.amount).where(
                    ActivityApprovalRequest.tenant_id == self.actor.tenant_id,
                    ActivityApprovalRequest.activity_id == item.activity_id,
                    ActivityApprovalRequest.request_type == "budget",
                    ActivityApprovalRequest.state == "approved",
                )
            )
            approved_spend = self.session.scalar(
                select(func.coalesce(func.sum(ActivityExpense.amount), 0)).where(
                    ActivityExpense.tenant_id == self.actor.tenant_id,
                    ActivityExpense.activity_id == item.activity_id,
                    ActivityExpense.state == "approved",
                    ActivityExpense.id != item.id,
                )
            )
            if approved_budget is None or approved_spend + item.amount > approved_budget:
                raise ActivitiesConflictError("Expense exceeds the approved activity budget")
        item.state = payload.state
        item.reviewed_by_membership_id = self.actor.membership_id
        item.reviewed_at = datetime.now(UTC)
        self.session.flush()
        self._audit("activities.expense.review", "activity_expense", item.id, {"state": item.state})
        return item

    def list_certificates(self, activity_id: UUID, skip: int = 0, limit: int = 100):
        """List verifiable certificates issued for one activity."""

        query = select(ActivityCertificate).where(
            ActivityCertificate.tenant_id == self.actor.tenant_id,
            ActivityCertificate.activity_id == activity_id,
        )
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            query = query.where(ActivityCertificate.student_id.in_(student_ids))
        return self._paginate(query.order_by(ActivityCertificate.issued_at.desc()), skip, limit)

    def issue_certificate(
        self,
        activity_id: UUID,
        payload: ActivityCertificateCreate,
    ) -> ActivityCertificate:
        """Issue one immutable certificate for an attended registration."""

        registration = self._get_registration(payload.registration_id)
        if registration is None or registration.activity_id != activity_id:
            raise ActivitiesValidationError("Invalid attended registration reference")
        if registration.state != "attended":
            raise ActivitiesConflictError("Certificates require attended participation")
        item = ActivityCertificate(
            tenant_id=self.actor.tenant_id,
            activity_id=activity_id,
            student_id=registration.student_id,
            registration_id=registration.id,
            serial_number=f"ACT-{datetime.now(UTC).year}-{uuid4().hex[:12].upper()}",
            issued_at=datetime.now(UTC),
        )
        self.session.add(item)
        self.session.flush()
        self._audit("activities.certificate.issue", "activity_certificate", item.id, {"serial_number": item.serial_number})
        return item

    def verify_certificate(self, serial_number: str) -> ActivityCertificate | None:
        """Resolve one non-revoked certificate by its tenant-unique serial number."""

        return self.session.scalar(
            select(ActivityCertificate).where(
                ActivityCertificate.tenant_id == self.actor.tenant_id,
                ActivityCertificate.serial_number == serial_number,
                ActivityCertificate.revoked_at.is_(None),
            )
        )

    def get_certificate_document(
        self,
        activity_id: UUID,
        certificate_id: UUID,
    ) -> ActivityCertificateDocument | None:
        """Derive one active participation certificate within actor Student scope."""

        query = select(ActivityCertificate).where(
            ActivityCertificate.tenant_id == self.actor.tenant_id,
            ActivityCertificate.id == certificate_id,
            ActivityCertificate.activity_id == activity_id,
            ActivityCertificate.revoked_at.is_(None),
        )
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            query = query.where(ActivityCertificate.student_id.in_(student_ids))
        certificate = self.session.scalar(query)
        if certificate is None:
            return None
        activity = self.session.scalar(
            select(Activity).where(
                Activity.tenant_id == self.actor.tenant_id,
                Activity.id == certificate.activity_id,
            )
        )
        student_row = self.session.execute(
            select(Student, Person)
            .join(
                Person,
                (Person.tenant_id == Student.tenant_id) & (Person.id == Student.person_id),
            )
            .where(
                Student.tenant_id == self.actor.tenant_id,
                Student.id == certificate.student_id,
            )
        ).one_or_none()
        tenant = self.session.scalar(select(Tenant).where(Tenant.id == self.actor.tenant_id))
        setting = self.session.scalar(
            select(CollegeSetting).where(CollegeSetting.tenant_id == self.actor.tenant_id)
        )
        if activity is None or student_row is None or tenant is None:
            raise ActivitiesValidationError("Certificate source records are unavailable")
        return ActivityCertificateDocument(
            certificate_id=certificate.id,
            serial_number=certificate.serial_number,
            verification_reference=certificate.serial_number,
            issued_at=certificate.issued_at,
            institution_name=setting.institution_name if setting else tenant.display_name,
            institution_short_name=(setting.short_name if setting else None) or tenant.short_name,
            primary_color=tenant.primary_color,
            accent_color=tenant.accent_color,
            student_id=student_row.Student.id,
            student_name=student_row.Person.full_name,
            registration_number=student_row.Student.registration_number,
            activity_id=activity.id,
            activity_title=activity.title,
            activity_type=activity.activity_type,
            activity_date=activity.activity_date,
            venue=activity.venue,
        )

    def list_points(self, activity_id: UUID, skip: int = 0, limit: int = 100):
        """List activity-point awards within actor record scope."""

        query = select(ActivityPoint).where(
            ActivityPoint.tenant_id == self.actor.tenant_id,
            ActivityPoint.activity_id == activity_id,
        )
        student_ids = resolve_actor_student_ids(self.session, self.actor)
        if student_ids is not None:
            query = query.where(ActivityPoint.student_id.in_(student_ids))
        return self._paginate(query.order_by(ActivityPoint.created_at.desc()), skip, limit)

    def award_points(self, activity_id: UUID, payload: ActivityPointCreate) -> ActivityPoint:
        """Award positive points to an attended activity participant."""

        self._require_participant(activity_id, payload.student_id, ("attended",))
        item = ActivityPoint(
            tenant_id=self.actor.tenant_id,
            activity_id=activity_id,
            **payload.model_dump(),
        )
        self.session.add(item)
        self.session.flush()
        self._audit("activities.points.award", "activity_point", item.id, {"points": item.points})
        return item
