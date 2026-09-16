"""FastAPI routes for tenant-bound authentication and session lifecycle."""

from collections.abc import Callable, Generator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import runtime_session_factory
from app.domains.identity.auth_service import (
    AuthenticationError,
    AuthenticationService,
    IssuedAuthentication,
    RequestMetadata,
)
from app.domains.identity.schemas import (
    ActorSummary,
    LoginRequest,
    LogoutResponse,
    MembershipSummary,
    RefreshRequest,
    RoleSummary,
    TenantSwitchRequest,
    TokenResponse,
)
from app.domains.identity.security import TokenValidationError, decode_token
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
bearer = HTTPBearer(auto_error=False)


def get_runtime_session() -> Generator[Session, None, None]:
    """Yield a restricted runtime session with explicit route-level commit control."""

    with runtime_session_factory()() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


def request_metadata(request: Request) -> RequestMetadata:
    """Extract bounded network metadata for security history."""

    user_agent = request.headers.get("user-agent")
    return RequestMetadata(
        ip_address=request.client.host[:45] if request.client else None,
        user_agent=user_agent[:500] if user_agent else None,
    )


def _token_response(authentication: IssuedAuthentication) -> TokenResponse:
    """Convert issued authentication state into the public API contract."""

    return TokenResponse(
        access_token=authentication.access_token,
        refresh_token=authentication.refresh_token,
        expires_in=settings.access_token_minutes * 60,
        actor=ActorSummary(
            account_id=authentication.actor.account_id,
            tenant_id=authentication.actor.tenant_id,
            membership_id=authentication.actor.membership_id,
            role_keys=list(authentication.actor.role_keys),
            permissions=sorted(authentication.actor.permissions),
            scopes=list(authentication.actor.scopes),
        ),
    )


def require_actor(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> ActorContext:
    """Require a valid access token backed by an active persisted session."""

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        claims = decode_token(credentials.credentials, "access")
        return AuthenticationService(session).actor_from_access_claims(claims)
    except (TokenValidationError, AuthenticationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication",
        ) from exc


def require_permission(permission: str) -> Callable[[ActorContext], ActorContext]:
    """Build a dependency that requires one exact resolved actor permission."""

    def dependency(actor: Annotated[ActorContext, Depends(require_actor)]) -> ActorContext:
        """Return the actor when authorized or reject the request."""

        if not actor.has_permission(permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return actor

    return dependency


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    session: Annotated[Session, Depends(get_runtime_session)],
) -> TokenResponse:
    """Authenticate an active member inside the explicitly selected tenant."""

    try:
        authentication = AuthenticationService(session).login(
            payload.tenant_key,
            payload.email,
            payload.password,
            request_metadata(request),
        )
        session.commit()
        return _token_response(authentication)
    except AuthenticationError as exc:
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant or credentials",
        ) from exc


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest,
    request: Request,
    session: Annotated[Session, Depends(get_runtime_session)],
) -> TokenResponse:
    """Rotate a current refresh token and recompute actor authorization."""

    try:
        claims = decode_token(payload.refresh_token, "refresh")
        authentication = AuthenticationService(session).refresh(
            claims,
            payload.refresh_token,
            request_metadata(request),
        )
        session.commit()
        return _token_response(authentication)
    except (TokenValidationError, AuthenticationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from exc


@router.post("/logout", response_model=LogoutResponse)
def logout(
    payload: RefreshRequest,
    request: Request,
    session: Annotated[Session, Depends(get_runtime_session)],
) -> LogoutResponse:
    """Revoke the persisted session represented by a current refresh token."""

    try:
        claims = decode_token(payload.refresh_token, "refresh")
        AuthenticationService(session).revoke(
            claims,
            payload.refresh_token,
            request_metadata(request),
        )
        session.commit()
        return LogoutResponse(revoked=True)
    except (TokenValidationError, AuthenticationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from exc


@router.post("/switch-tenant", response_model=TokenResponse)
def switch_tenant(
    payload: TenantSwitchRequest,
    request: Request,
    actor: Annotated[ActorContext, Depends(require_actor)],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> TokenResponse:
    """Create a new tenant-bound session after verifying target membership."""

    try:
        authentication = AuthenticationService(session).switch_tenant(
            actor.account_id,
            actor.tenant_id,
            payload.tenant_key,
            request_metadata(request),
        )
        session.commit()
        return _token_response(authentication)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Target tenant membership is unavailable",
        ) from exc


@router.get("/memberships", response_model=list[MembershipSummary])
def selectable_memberships(
    actor: Annotated[ActorContext, Depends(require_actor)],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> list[MembershipSummary]:
    """List active tenant memberships available to the current account."""

    memberships = AuthenticationService(session).list_selectable_memberships(
        actor.account_id,
        actor.tenant_id,
    )
    return [
        MembershipSummary(
            id=item.membership.id,
            status=item.membership.status,
            tenant=item.tenant,
            roles=[RoleSummary.model_validate(role) for role in item.roles],
        )
        for item in memberships
    ]


@router.get("/me", response_model=ActorSummary)
def current_actor(actor: Annotated[ActorContext, Depends(require_actor)]) -> ActorSummary:
    """Return the authorization context resolved for the current access token."""

    return ActorSummary(
        account_id=actor.account_id,
        tenant_id=actor.tenant_id,
        membership_id=actor.membership_id,
        role_keys=list(actor.role_keys),
        permissions=sorted(actor.permissions),
        scopes=list(actor.scopes),
    )
