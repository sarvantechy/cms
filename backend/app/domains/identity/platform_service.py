"""Platform-only authentication and tenant directory administration."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, or_, select, text, update
from sqlalchemy.orm import Session

from app.domains.identity.auth_service import AuthenticationError, RequestMetadata
from app.domains.identity.models import (
    Account,
    AuthenticationSession,
    Permission,
    PlatformAuthenticationSession,
    PlatformRoleAssignment,
    PlatformSecurityEvent,
    RoleTemplate,
    RoleTemplatePermission,
)
from app.domains.identity.security import (
    PlatformTokenClaims,
    issue_platform_token_pair,
    token_digest,
    verify_password,
)
from app.domains.tenancy.models import Tenant
from app.security_context import PlatformActorContext

INVALID_PLATFORM_CREDENTIALS = "Invalid platform credentials"


@dataclass(frozen=True, slots=True)
class IssuedPlatformAuthentication:
    """Return platform tokens and their resolved actor context."""

    access_token: str
    refresh_token: str
    actor: PlatformActorContext


@dataclass(frozen=True, slots=True)
class TenantStatusResult:
    """Return one tenant transition and its invalidated session count."""

    tenant_id: UUID
    status: str
    revoked_sessions: int


class PlatformAuthenticationService:
    """Authenticate platform administrators outside tenant authorization."""

    def __init__(self, session: Session) -> None:
        """Initialize the service with a restricted runtime transaction."""

        self.session = session

    def login(
        self,
        email: str,
        password: str,
        metadata: RequestMetadata,
    ) -> IssuedPlatformAuthentication:
        """Verify platform credentials and create a revocable global session."""

        normalized_email = email.strip().lower()
        account = self.session.scalar(select(Account).where(Account.email == normalized_email))
        if (
            account is None
            or not account.is_active
            or not account.password_hash
            or not verify_password(password, account.password_hash)
        ):
            self._record_event(
                account.id if account else None,
                "platform.auth.login_failed",
                "account",
                account.id if account else None,
                {"email": normalized_email},
                metadata,
            )
            raise AuthenticationError(INVALID_PLATFORM_CREDENTIALS)

        try:
            actor = self.resolve_actor(account.id)
        except AuthenticationError:
            self._record_event(
                account.id,
                "platform.auth.login_failed",
                "account",
                account.id,
                {"email": normalized_email},
                metadata,
            )
            raise AuthenticationError(INVALID_PLATFORM_CREDENTIALS) from None

        authentication_session = PlatformAuthenticationSession(
            account_id=account.id,
            refresh_token_hash="pending",
            expires_at=datetime.now(UTC),
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
        )
        self.session.add(authentication_session)
        self.session.flush()
        access_token, refresh_token, refresh_expiry = issue_platform_token_pair(
            account.id,
            authentication_session.id,
        )
        authentication_session.refresh_token_hash = token_digest(refresh_token)
        authentication_session.expires_at = refresh_expiry
        account.last_login_at = datetime.now(UTC)
        self._record_event(
            account.id,
            "platform.auth.login",
            "platform_authentication_session",
            authentication_session.id,
            {},
            metadata,
        )
        return IssuedPlatformAuthentication(access_token, refresh_token, actor)

    def refresh(
        self,
        claims: PlatformTokenClaims,
        refresh_token: str,
        metadata: RequestMetadata,
    ) -> IssuedPlatformAuthentication:
        """Rotate a platform refresh token and recompute platform permissions."""

        authentication_session = self._active_session(claims, refresh_token)
        actor = self.resolve_actor(claims.account_id)
        access_token, rotated_refresh, refresh_expiry = issue_platform_token_pair(
            claims.account_id,
            claims.session_id,
        )
        authentication_session.refresh_token_hash = token_digest(rotated_refresh)
        authentication_session.expires_at = refresh_expiry
        authentication_session.last_used_at = datetime.now(UTC)
        authentication_session.ip_address = metadata.ip_address
        authentication_session.user_agent = metadata.user_agent
        return IssuedPlatformAuthentication(access_token, rotated_refresh, actor)

    def revoke(
        self,
        claims: PlatformTokenClaims,
        refresh_token: str,
        metadata: RequestMetadata,
    ) -> None:
        """Revoke a current platform refresh session."""

        authentication_session = self._active_session(claims, refresh_token)
        self.resolve_actor(claims.account_id)
        authentication_session.revoked_at = datetime.now(UTC)
        self._record_event(
            claims.account_id,
            "platform.auth.logout",
            "platform_authentication_session",
            claims.session_id,
            {},
            metadata,
        )

    def actor_from_access_claims(self, claims: PlatformTokenClaims) -> PlatformActorContext:
        """Resolve a platform actor backed by an active persisted session."""

        authentication_session = self.session.scalar(
            select(PlatformAuthenticationSession).where(
                PlatformAuthenticationSession.id == claims.session_id,
                PlatformAuthenticationSession.account_id == claims.account_id,
                PlatformAuthenticationSession.revoked_at.is_(None),
                PlatformAuthenticationSession.expires_at > datetime.now(UTC),
            )
        )
        if authentication_session is None:
            raise AuthenticationError("Platform authentication session is unavailable")
        return self.resolve_actor(claims.account_id)

    def resolve_actor(self, account_id: UUID) -> PlatformActorContext:
        """Resolve effective platform roles and their explicit permissions."""

        now = datetime.now(UTC)
        effective_assignment = and_(
            PlatformRoleAssignment.account_id == account_id,
            PlatformRoleAssignment.revoked_at.is_(None),
            or_(PlatformRoleAssignment.starts_at.is_(None), PlatformRoleAssignment.starts_at <= now),
            or_(PlatformRoleAssignment.ends_at.is_(None), PlatformRoleAssignment.ends_at > now),
        )
        account = self.session.scalar(
            select(Account).where(Account.id == account_id, Account.is_active)
        )
        role_keys = tuple(
            self.session.scalars(
                select(RoleTemplate.key)
                .join(
                    PlatformRoleAssignment,
                    PlatformRoleAssignment.role_template_id == RoleTemplate.id,
                )
                .where(effective_assignment, RoleTemplate.is_platform_role)
                .distinct()
                .order_by(RoleTemplate.key)
            )
        )
        if account is None or not role_keys:
            raise AuthenticationError("Active platform assignment is unavailable")
        permissions = frozenset(
            self.session.scalars(
                select(Permission.key)
                .join(
                    RoleTemplatePermission,
                    RoleTemplatePermission.permission_id == Permission.id,
                )
                .join(
                    PlatformRoleAssignment,
                    PlatformRoleAssignment.role_template_id
                    == RoleTemplatePermission.role_template_id,
                )
                .where(effective_assignment)
                .distinct()
            )
        )
        return PlatformActorContext(account.id, role_keys, permissions)

    def _active_session(
        self,
        claims: PlatformTokenClaims,
        refresh_token: str,
    ) -> PlatformAuthenticationSession:
        """Return a matching active platform session or reject token reuse."""

        authentication_session = self.session.scalar(
            select(PlatformAuthenticationSession).where(
                PlatformAuthenticationSession.id == claims.session_id,
                PlatformAuthenticationSession.account_id == claims.account_id,
                PlatformAuthenticationSession.refresh_token_hash == token_digest(refresh_token),
                PlatformAuthenticationSession.revoked_at.is_(None),
                PlatformAuthenticationSession.expires_at > datetime.now(UTC),
            )
        )
        if authentication_session is None:
            raise AuthenticationError("Platform refresh session is unavailable")
        return authentication_session

    def _record_event(
        self,
        account_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: UUID | None,
        details: dict[str, object],
        metadata: RequestMetadata,
    ) -> None:
        """Append one global platform security event."""

        self.session.add(
            PlatformSecurityEvent(
                account_id=account_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=metadata.ip_address,
                user_agent=metadata.user_agent,
            )
        )


class PlatformTenantService:
    """Manage the global tenant directory without reading tenant-owned records."""

    def __init__(self, session: Session) -> None:
        """Initialize the service with a restricted runtime transaction."""

        self.session = session

    def list_tenants(self) -> tuple[Tenant, ...]:
        """Return all tenant directory entries in stable display order."""

        return tuple(self.session.scalars(select(Tenant).order_by(Tenant.display_name, Tenant.id)))

    def change_status(
        self,
        tenant_id: UUID,
        target_status: str,
        actor: PlatformActorContext,
        metadata: RequestMetadata,
    ) -> TenantStatusResult:
        """Apply an allowed tenant transition and invalidate unusable sessions."""

        tenant = self.session.get(Tenant, tenant_id)
        if tenant is None:
            raise LookupError("Tenant not found")
        allowed_transitions = {
            "setup": {"active", "closed"},
            "active": {"suspended", "closed"},
            "suspended": {"active", "closed"},
            "closed": set(),
        }
        if target_status not in allowed_transitions[tenant.status]:
            raise AuthenticationError(
                f"Tenant cannot transition from {tenant.status} to {target_status}"
            )

        previous_status = tenant.status
        tenant.status = target_status
        revoked_sessions = 0
        if target_status in {"suspended", "closed"}:
            self.session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant.id)},
            )
            result = self.session.execute(
                update(AuthenticationSession)
                .where(
                    AuthenticationSession.tenant_id == tenant.id,
                    AuthenticationSession.revoked_at.is_(None),
                )
                .values(revoked_at=datetime.now(UTC))
            )
            revoked_sessions = result.rowcount
        self.session.add(
            PlatformSecurityEvent(
                account_id=actor.account_id,
                action="platform.tenant.status_changed",
                entity_type="tenant",
                entity_id=tenant.id,
                details={
                    "previous_status": previous_status,
                    "status": target_status,
                    "revoked_sessions": revoked_sessions,
                },
                ip_address=metadata.ip_address,
                user_agent=metadata.user_agent,
            )
        )
        return TenantStatusResult(tenant.id, target_status, revoked_sessions)
