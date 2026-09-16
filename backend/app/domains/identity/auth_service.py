"""Tenant-bound authentication, session rotation, and actor resolution services."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, or_, select, text
from sqlalchemy.orm import Session

from app.domains.audit.models import AuditEvent
from app.domains.identity.models import (
    Account,
    AuthenticationSession,
    LoginHistory,
    MembershipRoleAssignment,
    MembershipRoleScope,
    Permission,
    TenantMembership,
    TenantRole,
    TenantRolePermission,
)
from app.domains.identity.security import (
    TokenClaims,
    issue_token_pair,
    token_digest,
    verify_password,
)
from app.domains.tenancy.models import Tenant
from app.security_context import ActorContext, ActorScope

INVALID_CREDENTIALS = "Invalid tenant or credentials"


class AuthenticationError(ValueError):
    """Indicate rejected credentials or an unusable authentication session."""


@dataclass(frozen=True, slots=True)
class RequestMetadata:
    """Carry bounded request-origin fields stored in security history."""

    ip_address: str | None = None
    user_agent: str | None = None


@dataclass(frozen=True, slots=True)
class IssuedAuthentication:
    """Return tokens and resolved actor state from authentication operations."""

    access_token: str
    refresh_token: str
    actor: ActorContext


@dataclass(frozen=True, slots=True)
class SelectableMembership:
    """Carry one active tenant membership and its effective roles."""

    membership: TenantMembership
    tenant: Tenant
    roles: tuple[TenantRole, ...]


class AuthenticationService:
    """Authenticate tenant members and maintain revocable refresh sessions."""

    def __init__(self, session: Session) -> None:
        """Initialize the service with one runtime database transaction."""

        self.session = session

    def login(
        self,
        tenant_key: str,
        email: str,
        password: str,
        metadata: RequestMetadata,
    ) -> IssuedAuthentication:
        """Verify tenant credentials and create a new revocable session."""

        normalized_email = email.strip().lower()
        tenant = self.session.scalar(
            select(Tenant).where(Tenant.key == tenant_key.strip().lower(), Tenant.status == "active")
        )
        if tenant is None:
            raise AuthenticationError(INVALID_CREDENTIALS)

        self._set_tenant(tenant.id)
        account = self.session.scalar(select(Account).where(Account.email == normalized_email))
        membership = None
        if account is not None:
            membership = self.session.scalar(
                select(TenantMembership).where(
                    TenantMembership.tenant_id == tenant.id,
                    TenantMembership.account_id == account.id,
                    TenantMembership.status == "active",
                )
            )

        if (
            account is None
            or not account.is_active
            or not account.password_hash
            or not verify_password(password, account.password_hash)
        ):
            self._record_login(tenant.id, account, normalized_email, False, "invalid_credentials", metadata)
            raise AuthenticationError(INVALID_CREDENTIALS)
        if membership is None:
            self._record_login(tenant.id, account, normalized_email, False, "inactive_membership", metadata)
            raise AuthenticationError(INVALID_CREDENTIALS)

        actor = self.resolve_actor(account.id, tenant.id, membership.id)
        authentication_session = AuthenticationSession(
            tenant_id=tenant.id,
            account_id=account.id,
            membership_id=membership.id,
            refresh_token_hash="pending",
            expires_at=datetime.now(UTC),
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
        self.session.add(authentication_session)
        self.session.flush()
        access_token, refresh_token, refresh_expiry = issue_token_pair(
            account.id, tenant.id, authentication_session.id
        )
        authentication_session.refresh_token_hash = token_digest(refresh_token)
        authentication_session.expires_at = refresh_expiry
        account.last_login_at = datetime.now(UTC)
        self._record_login(tenant.id, account, normalized_email, True, None, metadata)
        self._record_audit("auth.login", "authentication_session", authentication_session.id, actor, metadata)
        return IssuedAuthentication(access_token, refresh_token, actor)

    def refresh(
        self,
        claims: TokenClaims,
        refresh_token: str,
        metadata: RequestMetadata,
    ) -> IssuedAuthentication:
        """Rotate a valid refresh token and return newly resolved authorization state."""

        self._set_tenant(claims.tenant_id)
        authentication_session = self._active_session(claims, refresh_token)
        actor = self.resolve_actor(
            claims.account_id,
            claims.tenant_id,
            authentication_session.membership_id,
        )
        access_token, rotated_refresh, refresh_expiry = issue_token_pair(
            claims.account_id, claims.tenant_id, claims.session_id
        )
        authentication_session.refresh_token_hash = token_digest(rotated_refresh)
        authentication_session.expires_at = refresh_expiry
        authentication_session.last_used_at = datetime.now(UTC)
        authentication_session.ip_address = metadata.ip_address
        authentication_session.user_agent = metadata.user_agent
        return IssuedAuthentication(access_token, rotated_refresh, actor)

    def switch_tenant(
        self,
        account_id: UUID,
        source_tenant_id: UUID,
        target_tenant_key: str,
        metadata: RequestMetadata,
    ) -> IssuedAuthentication:
        """Issue a target-bound session only for an active target membership."""

        tenant = self.session.scalar(
            select(Tenant).where(
                Tenant.key == target_tenant_key.strip().lower(),
                Tenant.status == "active",
            )
        )
        if tenant is None:
            raise AuthenticationError("Target tenant membership is unavailable")
        self._set_tenant(tenant.id)
        membership = self.session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant.id,
                TenantMembership.account_id == account_id,
                TenantMembership.status == "active",
            )
        )
        if membership is None:
            raise AuthenticationError("Target tenant membership is unavailable")

        actor = self.resolve_actor(account_id, tenant.id, membership.id)
        authentication_session = AuthenticationSession(
            tenant_id=tenant.id,
            account_id=account_id,
            membership_id=membership.id,
            refresh_token_hash="pending",
            expires_at=datetime.now(UTC),
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
        self.session.add(authentication_session)
        self.session.flush()
        access_token, refresh_token, refresh_expiry = issue_token_pair(
            account_id, tenant.id, authentication_session.id
        )
        authentication_session.refresh_token_hash = token_digest(refresh_token)
        authentication_session.expires_at = refresh_expiry
        self.session.add(
            AuditEvent(
                tenant_id=tenant.id,
                account_id=account_id,
                membership_id=membership.id,
                action="auth.tenant_switch",
                entity_type="authentication_session",
                entity_id=authentication_session.id,
                details={"source_tenant_id": str(source_tenant_id)},
                ip_address=metadata.ip_address,
                user_agent=metadata.user_agent,
            )
        )
        return IssuedAuthentication(access_token, refresh_token, actor)

    def list_selectable_memberships(
        self,
        account_id: UUID,
        source_tenant_id: UUID,
    ) -> tuple[SelectableMembership, ...]:
        """List active tenant memberships without bypassing forced tenant RLS."""

        now = datetime.now(UTC)
        tenants = self.session.scalars(
            select(Tenant).where(Tenant.status == "active").order_by(Tenant.display_name)
        ).all()
        selectable: list[SelectableMembership] = []
        try:
            for tenant in tenants:
                self._set_tenant(tenant.id)
                membership = self.session.scalar(
                    select(TenantMembership).where(
                        TenantMembership.tenant_id == tenant.id,
                        TenantMembership.account_id == account_id,
                        TenantMembership.status == "active",
                    )
                )
                if membership is None:
                    continue
                roles = self.session.scalars(
                    select(TenantRole)
                    .join(
                        MembershipRoleAssignment,
                        and_(
                            MembershipRoleAssignment.tenant_id == TenantRole.tenant_id,
                            MembershipRoleAssignment.role_id == TenantRole.id,
                        ),
                    )
                    .where(
                        TenantRole.tenant_id == tenant.id,
                        TenantRole.is_active,
                        MembershipRoleAssignment.membership_id == membership.id,
                        or_(
                            MembershipRoleAssignment.starts_at.is_(None),
                            MembershipRoleAssignment.starts_at <= now,
                        ),
                        or_(
                            MembershipRoleAssignment.ends_at.is_(None),
                            MembershipRoleAssignment.ends_at > now,
                        ),
                    )
                    .order_by(TenantRole.display_name)
                ).all()
                selectable.append(SelectableMembership(membership, tenant, tuple(roles)))
            return tuple(selectable)
        finally:
            self._set_tenant(source_tenant_id)

    def revoke(
        self,
        claims: TokenClaims,
        refresh_token: str,
        metadata: RequestMetadata,
    ) -> None:
        """Revoke the session represented by a valid current refresh token."""

        self._set_tenant(claims.tenant_id)
        authentication_session = self._active_session(claims, refresh_token)
        actor = self.resolve_actor(
            claims.account_id,
            claims.tenant_id,
            authentication_session.membership_id,
        )
        authentication_session.revoked_at = datetime.now(UTC)
        self._record_audit("auth.logout", "authentication_session", claims.session_id, actor, metadata)

    def actor_from_access_claims(self, claims: TokenClaims) -> ActorContext:
        """Resolve an actor only when its persisted session remains active."""

        self._set_tenant(claims.tenant_id)
        authentication_session = self.session.scalar(
            select(AuthenticationSession).where(
                AuthenticationSession.id == claims.session_id,
                AuthenticationSession.tenant_id == claims.tenant_id,
                AuthenticationSession.account_id == claims.account_id,
                AuthenticationSession.revoked_at.is_(None),
                AuthenticationSession.expires_at > datetime.now(UTC),
            )
        )
        if authentication_session is None:
            raise AuthenticationError("Authentication session is unavailable")
        return self.resolve_actor(
            claims.account_id,
            claims.tenant_id,
            authentication_session.membership_id,
        )

    def resolve_actor(self, account_id: UUID, tenant_id: UUID, membership_id: UUID) -> ActorContext:
        """Resolve active roles, permissions, and scopes for one tenant membership."""

        now = datetime.now(UTC)
        tenant = self.session.scalar(
            select(Tenant).where(Tenant.id == tenant_id, Tenant.status == "active")
        )
        if tenant is None:
            raise AuthenticationError("Active tenant is unavailable")
        active_assignment = and_(
            MembershipRoleAssignment.tenant_id == tenant_id,
            MembershipRoleAssignment.membership_id == membership_id,
            or_(MembershipRoleAssignment.starts_at.is_(None), MembershipRoleAssignment.starts_at <= now),
            or_(MembershipRoleAssignment.ends_at.is_(None), MembershipRoleAssignment.ends_at > now),
        )
        membership = self.session.scalar(
            select(TenantMembership).where(
                TenantMembership.id == membership_id,
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.account_id == account_id,
                TenantMembership.status == "active",
            )
        )
        if membership is None:
            raise AuthenticationError("Active tenant membership is unavailable")

        role_keys = tuple(
            self.session.scalars(
                select(TenantRole.key)
                .join(MembershipRoleAssignment, MembershipRoleAssignment.role_id == TenantRole.id)
                .where(active_assignment, TenantRole.is_active)
                .distinct()
                .order_by(TenantRole.key)
            )
        )
        permissions = frozenset(
            self.session.scalars(
                select(Permission.key)
                .join(TenantRolePermission, TenantRolePermission.permission_id == Permission.id)
                .join(
                    MembershipRoleAssignment,
                    MembershipRoleAssignment.role_id == TenantRolePermission.role_id,
                )
                .where(
                    active_assignment,
                    TenantRolePermission.tenant_id == tenant_id,
                    TenantRolePermission.is_active,
                )
                .distinct()
            )
        )
        scopes = tuple(
            ActorScope(scope_type, reference_id)
            for scope_type, reference_id in self.session.execute(
                select(
                    MembershipRoleScope.scope_type,
                    MembershipRoleScope.scope_reference_id,
                )
                .join(
                    MembershipRoleAssignment,
                    MembershipRoleAssignment.id == MembershipRoleScope.assignment_id,
                )
                .where(active_assignment, MembershipRoleScope.tenant_id == tenant_id)
                .distinct()
            )
        )
        return ActorContext(
            account_id=account_id,
            tenant_id=tenant_id,
            membership_id=membership_id,
            role_keys=role_keys,
            permissions=permissions,
            scopes=scopes,
        )

    def _active_session(
        self, claims: TokenClaims, refresh_token: str
    ) -> AuthenticationSession:
        """Return the current matching refresh session or reject token reuse."""

        authentication_session = self.session.scalar(
            select(AuthenticationSession).where(
                AuthenticationSession.id == claims.session_id,
                AuthenticationSession.tenant_id == claims.tenant_id,
                AuthenticationSession.account_id == claims.account_id,
                AuthenticationSession.refresh_token_hash == token_digest(refresh_token),
                AuthenticationSession.revoked_at.is_(None),
                AuthenticationSession.expires_at > datetime.now(UTC),
            )
        )
        if authentication_session is None:
            raise AuthenticationError("Refresh session is unavailable")
        return authentication_session

    def _set_tenant(self, tenant_id: UUID) -> None:
        """Set transaction-local tenant context before tenant-owned queries."""

        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )

    def _record_login(
        self,
        tenant_id: UUID,
        account: Account | None,
        email: str,
        succeeded: bool,
        failure_reason: str | None,
        metadata: RequestMetadata,
    ) -> None:
        """Append one login attempt to tenant-scoped security history."""

        self.session.add(
            LoginHistory(
                tenant_id=tenant_id,
                account_id=account.id if account else None,
                email=email,
                succeeded=succeeded,
                failure_reason=failure_reason,
                ip_address=metadata.ip_address,
                user_agent=metadata.user_agent,
            )
        )

    def _record_audit(
        self,
        action: str,
        entity_type: str,
        entity_id: UUID,
        actor: ActorContext,
        metadata: RequestMetadata,
    ) -> None:
        """Append one actor-attributed security event in the current transaction."""

        self.session.add(
            AuditEvent(
                tenant_id=actor.tenant_id,
                account_id=actor.account_id,
                membership_id=actor.membership_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details={},
                ip_address=metadata.ip_address,
                user_agent=metadata.user_agent,
            )
        )
