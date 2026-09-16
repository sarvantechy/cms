"""Tenant account invitation, password lifecycle, and session administration."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.domains.audit.models import AuditEvent
from app.domains.identity.auth_service import AuthenticationError, RequestMetadata
from app.domains.identity.models import (
    Account,
    AccountInvitation,
    AuthenticationSession,
    MembershipRoleAssignment,
    MembershipRoleScope,
    TenantMembership,
    TenantRole,
)
from app.domains.identity.security import hash_password, token_digest, verify_password
from app.security_context import ActorContext

INVITATION_LIFETIME = timedelta(hours=48)
INVALID_INVITATION = "Invitation is invalid or expired"
SUPPORTED_SCOPE_TYPES = frozenset(
    {
        "institution",
        "campus",
        "department",
        "program",
        "batch",
        "section",
        "subject_offering",
        "linked_student",
        "own_record",
    }
)


class AccountLifecycleError(ValueError):
    """Indicate an invalid invitation, credential, role, or lifecycle operation."""


@dataclass(frozen=True, slots=True)
class CreatedInvitation:
    """Return a persisted invitation and its one-time plaintext delivery token."""

    invitation_id: UUID
    membership_id: UUID
    token: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class MembershipAdminRecord:
    """Carry an aggregated tenant membership and its assigned role keys."""

    membership: TenantMembership
    account: Account
    role_keys: tuple[str, ...]


class AccountLifecycleService:
    """Manage tenant membership invitations and authenticated account credentials."""

    def __init__(self, session: Session) -> None:
        """Initialize the service with one restricted runtime transaction."""

        self.session = session

    def invite(
        self,
        actor: ActorContext,
        email: str,
        display_name: str,
        role_keys: list[str],
        scope_type: str,
        scope_reference_id: UUID | None,
        metadata: RequestMetadata,
    ) -> CreatedInvitation:
        """Create or renew an invited membership with explicit initial roles and scope."""

        normalized_email = email.strip().lower()
        normalized_roles = tuple(sorted(set(role_keys)))
        if not normalized_roles:
            raise AccountLifecycleError("At least one role is required")
        self._validate_scope(scope_type, scope_reference_id)
        self._set_tenant(actor.tenant_id)

        roles = tuple(
            self.session.scalars(
                select(TenantRole).where(
                    TenantRole.tenant_id == actor.tenant_id,
                    TenantRole.key.in_(normalized_roles),
                    TenantRole.is_active,
                )
            )
        )
        if len(roles) != len(normalized_roles):
            raise AccountLifecycleError("One or more roles are unavailable")

        account = self.session.scalar(select(Account).where(Account.email == normalized_email))
        if account is None:
            account = Account(
                email=normalized_email,
                display_name=display_name.strip(),
                password_hash=None,
                is_active=True,
                must_change_password=True,
            )
            self.session.add(account)
            self.session.flush()

        membership = self.session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == actor.tenant_id,
                TenantMembership.account_id == account.id,
            )
        )
        if membership is None:
            membership = TenantMembership(
                tenant_id=actor.tenant_id,
                account_id=account.id,
                status="invited",
            )
            self.session.add(membership)
            self.session.flush()
        elif membership.status == "active":
            raise AccountLifecycleError("Account already has an active membership")
        else:
            membership.status = "invited"
            membership.ended_at = None

        for role in roles:
            assignment = self.session.scalar(
                select(MembershipRoleAssignment).where(
                    MembershipRoleAssignment.tenant_id == actor.tenant_id,
                    MembershipRoleAssignment.membership_id == membership.id,
                    MembershipRoleAssignment.role_id == role.id,
                )
            )
            if assignment is None:
                assignment = MembershipRoleAssignment(
                    tenant_id=actor.tenant_id,
                    membership_id=membership.id,
                    role_id=role.id,
                )
                self.session.add(assignment)
                self.session.flush()
            assignment.starts_at = None
            assignment.ends_at = None
            existing_scope = self.session.scalar(
                select(MembershipRoleScope).where(
                    MembershipRoleScope.tenant_id == actor.tenant_id,
                    MembershipRoleScope.assignment_id == assignment.id,
                    MembershipRoleScope.scope_type == scope_type,
                    MembershipRoleScope.scope_reference_id == scope_reference_id,
                )
            )
            if existing_scope is None:
                self.session.add(
                    MembershipRoleScope(
                        tenant_id=actor.tenant_id,
                        assignment_id=assignment.id,
                        scope_type=scope_type,
                        scope_reference_id=scope_reference_id,
                    )
                )

        self.session.execute(
            update(AccountInvitation)
            .where(
                AccountInvitation.tenant_id == actor.tenant_id,
                AccountInvitation.membership_id == membership.id,
                AccountInvitation.accepted_at.is_(None),
                AccountInvitation.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        plaintext_token = f"{actor.tenant_id}.{token_urlsafe(32)}"
        expires_at = datetime.now(UTC) + INVITATION_LIFETIME
        invitation = AccountInvitation(
            tenant_id=actor.tenant_id,
            account_id=account.id,
            membership_id=membership.id,
            invited_by_account_id=actor.account_id,
            token_hash=token_digest(plaintext_token),
            expires_at=expires_at,
        )
        self.session.add(invitation)
        self.session.flush()
        self._audit(
            actor,
            "identity.membership.invited",
            "tenant_membership",
            membership.id,
            {"role_keys": list(normalized_roles), "scope_type": scope_type},
            metadata,
        )
        return CreatedInvitation(invitation.id, membership.id, plaintext_token, expires_at)

    def accept_invitation(
        self, invitation_token: str, password: str, metadata: RequestMetadata
    ) -> tuple[UUID, UUID]:
        """Activate a single-use invitation after establishing or proving credentials."""

        tenant_id = self._tenant_id_from_invitation(invitation_token)
        self._set_tenant(tenant_id)
        invitation = self.session.scalar(
            select(AccountInvitation).where(
                AccountInvitation.tenant_id == tenant_id,
                AccountInvitation.token_hash == token_digest(invitation_token),
                AccountInvitation.accepted_at.is_(None),
                AccountInvitation.revoked_at.is_(None),
                AccountInvitation.expires_at > datetime.now(UTC),
            )
        )
        if invitation is None:
            raise AccountLifecycleError(INVALID_INVITATION)
        account = self.session.get(Account, invitation.account_id)
        membership = self.session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.id == invitation.membership_id,
                TenantMembership.status == "invited",
            )
        )
        if account is None or membership is None:
            raise AccountLifecycleError(INVALID_INVITATION)

        if account.password_hash is None:
            account.password_hash = hash_password(password)
            account.must_change_password = False
        elif not verify_password(password, account.password_hash):
            raise AccountLifecycleError("Existing account credentials are invalid")
        account.is_active = True
        membership.status = "active"
        membership.joined_at = datetime.now(UTC)
        membership.ended_at = None
        invitation.accepted_at = datetime.now(UTC)
        self.session.add(
            AuditEvent(
                tenant_id=tenant_id,
                account_id=account.id,
                membership_id=membership.id,
                action="identity.membership.accepted",
                entity_type="tenant_membership",
                entity_id=membership.id,
                details={},
                ip_address=metadata.ip_address,
                user_agent=metadata.user_agent,
            )
        )
        return tenant_id, membership.id

    def change_password(
        self,
        actor: ActorContext,
        current_password: str,
        new_password: str,
        metadata: RequestMetadata,
    ) -> int:
        """Replace the actor password and revoke every active authentication session."""

        self._set_tenant(actor.tenant_id)
        account = self.session.get(Account, actor.account_id)
        if account is None or account.password_hash is None:
            raise AuthenticationError("Current password is invalid")
        if not verify_password(current_password, account.password_hash):
            raise AuthenticationError("Current password is invalid")
        if verify_password(new_password, account.password_hash):
            raise AccountLifecycleError("New password must differ from the current password")

        account.password_hash = hash_password(new_password)
        account.must_change_password = False
        revoked = self._revoke_sessions(actor.tenant_id, actor.account_id)
        self._audit(actor, "identity.password.changed", "account", account.id, {}, metadata)
        return revoked

    def list_sessions(self, actor: ActorContext) -> tuple[AuthenticationSession, ...]:
        """Return the actor's tenant-bound sessions newest first."""

        self._set_tenant(actor.tenant_id)
        return tuple(
            self.session.scalars(
                select(AuthenticationSession)
                .where(
                    AuthenticationSession.tenant_id == actor.tenant_id,
                    AuthenticationSession.account_id == actor.account_id,
                )
                .order_by(AuthenticationSession.created_at.desc())
            )
        )

    def revoke_session(
        self,
        actor: ActorContext,
        session_id: UUID,
        metadata: RequestMetadata,
    ) -> int:
        """Revoke one of the actor's tenant-bound sessions without exposing others."""

        self._set_tenant(actor.tenant_id)
        authentication_session = self.session.scalar(
            select(AuthenticationSession).where(
                AuthenticationSession.id == session_id,
                AuthenticationSession.tenant_id == actor.tenant_id,
                AuthenticationSession.account_id == actor.account_id,
                AuthenticationSession.revoked_at.is_(None),
            )
        )
        if authentication_session is None:
            raise AccountLifecycleError("Active session was not found")
        authentication_session.revoked_at = datetime.now(UTC)
        self._audit(
            actor,
            "identity.session.revoked",
            "authentication_session",
            session_id,
            {},
            metadata,
        )
        return 1

    def list_memberships(self, actor: ActorContext) -> tuple[MembershipAdminRecord, ...]:
        """List tenant memberships and role keys using one tenant-scoped query."""

        self._set_tenant(actor.tenant_id)
        rows = self.session.execute(
            select(TenantMembership, Account, TenantRole.key)
            .join(Account, Account.id == TenantMembership.account_id)
            .outerjoin(
                MembershipRoleAssignment,
                (MembershipRoleAssignment.tenant_id == TenantMembership.tenant_id)
                & (MembershipRoleAssignment.membership_id == TenantMembership.id),
            )
            .outerjoin(
                TenantRole,
                (TenantRole.tenant_id == MembershipRoleAssignment.tenant_id)
                & (TenantRole.id == MembershipRoleAssignment.role_id),
            )
            .where(TenantMembership.tenant_id == actor.tenant_id)
            .order_by(Account.display_name, Account.email, TenantRole.key)
        )
        records: dict[UUID, tuple[TenantMembership, Account, list[str]]] = {}
        for membership, account, role_key in rows:
            record = records.setdefault(membership.id, (membership, account, []))
            if role_key is not None and role_key not in record[2]:
                record[2].append(role_key)
        return tuple(
            MembershipAdminRecord(membership, account, tuple(role_keys))
            for membership, account, role_keys in records.values()
        )

    def change_membership_status(
        self,
        actor: ActorContext,
        membership_id: UUID,
        target_status: str,
        metadata: RequestMetadata,
    ) -> tuple[TenantMembership, int]:
        """Apply a guarded membership transition and revoke access when required."""

        self._set_tenant(actor.tenant_id)
        membership = self.session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == actor.tenant_id,
                TenantMembership.id == membership_id,
            )
        )
        if membership is None:
            raise AccountLifecycleError("Membership was not found")
        if membership.id == actor.membership_id and target_status != "active":
            raise AccountLifecycleError("Administrators cannot suspend or end their own membership")
        allowed_transitions = {
            "invited": {"suspended", "ended"},
            "active": {"suspended", "ended"},
            "suspended": {"active", "ended"},
            "ended": set(),
        }
        if target_status == membership.status:
            return membership, 0
        if target_status not in allowed_transitions[membership.status]:
            raise AccountLifecycleError(
                f"Membership cannot transition from {membership.status} to {target_status}"
            )
        if target_status == "active":
            account = self.session.get(Account, membership.account_id)
            if account is None or account.password_hash is None:
                raise AccountLifecycleError(
                    "Membership cannot activate before invitation acceptance"
                )

        previous_status = membership.status
        now = datetime.now(UTC)
        membership.status = target_status
        revoked_sessions = 0
        if target_status == "active":
            membership.joined_at = membership.joined_at or now
            membership.ended_at = None
        else:
            revoked_sessions = self._revoke_sessions(actor.tenant_id, membership.account_id)
            self.session.execute(
                update(AccountInvitation)
                .where(
                    AccountInvitation.tenant_id == actor.tenant_id,
                    AccountInvitation.membership_id == membership.id,
                    AccountInvitation.accepted_at.is_(None),
                    AccountInvitation.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
            if target_status == "ended":
                membership.ended_at = now
                self.session.execute(
                    update(MembershipRoleAssignment)
                    .where(
                        MembershipRoleAssignment.tenant_id == actor.tenant_id,
                        MembershipRoleAssignment.membership_id == membership.id,
                        MembershipRoleAssignment.ends_at.is_(None),
                    )
                    .values(ends_at=now)
                )

        self._audit(
            actor,
            "identity.membership.status_changed",
            "tenant_membership",
            membership.id,
            {"previous_status": previous_status, "status": target_status},
            metadata,
        )
        return membership, revoked_sessions

    def revoke_membership_sessions(
        self,
        actor: ActorContext,
        membership_id: UUID,
        metadata: RequestMetadata,
    ) -> int:
        """Revoke all active sessions belonging to one membership in the actor's tenant."""

        self._set_tenant(actor.tenant_id)
        membership = self.session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == actor.tenant_id,
                TenantMembership.id == membership_id,
            )
        )
        if membership is None:
            raise AccountLifecycleError("Membership was not found")
        result = self.session.execute(
            update(AuthenticationSession)
            .where(
                AuthenticationSession.tenant_id == actor.tenant_id,
                AuthenticationSession.membership_id == membership.id,
                AuthenticationSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        revoked_sessions = result.rowcount or 0
        self._audit(
            actor,
            "identity.membership.sessions_revoked",
            "tenant_membership",
            membership.id,
            {"revoked_sessions": revoked_sessions},
            metadata,
        )
        return revoked_sessions

    def _revoke_sessions(self, tenant_id: UUID, account_id: UUID) -> int:
        """Revoke all active sessions for an account inside one tenant."""

        result = self.session.execute(
            update(AuthenticationSession)
            .where(
                AuthenticationSession.tenant_id == tenant_id,
                AuthenticationSession.account_id == account_id,
                AuthenticationSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        return result.rowcount or 0

    def _set_tenant(self, tenant_id: UUID) -> None:
        """Set transaction-local tenant context before tenant-owned operations."""

        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )

    def _tenant_id_from_invitation(self, invitation_token: str) -> UUID:
        """Extract the non-authoritative tenant routing prefix from an invitation token."""

        try:
            return UUID(invitation_token.split(".", maxsplit=1)[0])
        except (ValueError, IndexError) as exc:
            raise AccountLifecycleError(INVALID_INVITATION) from exc

    def _validate_scope(self, scope_type: str, scope_reference_id: UUID | None) -> None:
        """Validate scope shape before relying on database constraints."""

        if scope_type not in SUPPORTED_SCOPE_TYPES:
            raise AccountLifecycleError("Unsupported scope type")
        unreferenced = {"institution", "own_record"}
        if (scope_type in unreferenced) != (scope_reference_id is None):
            raise AccountLifecycleError("Scope reference does not match scope type")

    def _audit(
        self,
        actor: ActorContext,
        action: str,
        entity_type: str,
        entity_id: UUID,
        details: dict[str, object],
        metadata: RequestMetadata,
    ) -> None:
        """Append an actor-attributed identity lifecycle event."""

        self.session.add(
            AuditEvent(
                tenant_id=actor.tenant_id,
                account_id=actor.account_id,
                membership_id=actor.membership_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=metadata.ip_address,
                user_agent=metadata.user_agent,
            )
        )
