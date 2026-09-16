"""FastAPI routes for isolated platform authentication and tenant administration."""

from collections.abc import Callable, Generator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import runtime_session_factory
from app.domains.identity.auth_service import AuthenticationError
from app.domains.identity.platform_service import (
    IssuedPlatformAuthentication,
    PlatformAuthenticationService,
    PlatformTenantService,
)
from app.domains.identity.router import bearer, request_metadata
from app.domains.identity.schemas import (
    LogoutResponse,
    PlatformActorSummary,
    PlatformLoginRequest,
    PlatformTenantStatusRequest,
    PlatformTenantStatusResponse,
    PlatformTokenResponse,
    RefreshRequest,
)
from app.domains.identity.security import TokenValidationError, decode_platform_token
from app.domains.tenancy.schemas import TenantSummary
from app.security_context import PlatformActorContext

router = APIRouter(prefix="/api/v1/platform", tags=["Platform Administration"])


def get_platform_session() -> Generator[Session, None, None]:
    """Yield a restricted runtime session with explicit route-level commit control."""

    with runtime_session_factory()() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


def _token_response(authentication: IssuedPlatformAuthentication) -> PlatformTokenResponse:
    """Convert issued platform authentication into the public response contract."""

    return PlatformTokenResponse(
        access_token=authentication.access_token,
        refresh_token=authentication.refresh_token,
        expires_in=settings.access_token_minutes * 60,
        actor=PlatformActorSummary(
            account_id=authentication.actor.account_id,
            role_keys=list(authentication.actor.role_keys),
            permissions=sorted(authentication.actor.permissions),
        ),
    )


def require_platform_actor(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[Session, Depends(get_platform_session)],
) -> PlatformActorContext:
    """Require a platform access token backed by an effective role assignment."""

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        claims = decode_platform_token(credentials.credentials, "access")
        return PlatformAuthenticationService(session).actor_from_access_claims(claims)
    except (TokenValidationError, AuthenticationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired platform authentication",
        ) from exc


def require_platform_permission(
    permission: str,
) -> Callable[[PlatformActorContext], PlatformActorContext]:
    """Build a dependency requiring one explicit platform permission."""

    def dependency(
        actor: Annotated[PlatformActorContext, Depends(require_platform_actor)],
    ) -> PlatformActorContext:
        """Return an authorized platform actor or reject the request."""

        if not actor.has_permission(permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return actor

    return dependency


@router.post("/auth/login", response_model=PlatformTokenResponse)
def login(
    payload: PlatformLoginRequest,
    request: Request,
    session: Annotated[Session, Depends(get_platform_session)],
) -> PlatformTokenResponse:
    """Authenticate an account with an effective platform role assignment."""

    try:
        authentication = PlatformAuthenticationService(session).login(
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
            detail="Invalid platform credentials",
        ) from exc


@router.post("/auth/refresh", response_model=PlatformTokenResponse)
def refresh(
    payload: RefreshRequest,
    request: Request,
    session: Annotated[Session, Depends(get_platform_session)],
) -> PlatformTokenResponse:
    """Rotate a platform refresh token and recompute platform authorization."""

    try:
        claims = decode_platform_token(payload.refresh_token, "refresh")
        authentication = PlatformAuthenticationService(session).refresh(
            claims,
            payload.refresh_token,
            request_metadata(request),
        )
        session.commit()
        return _token_response(authentication)
    except (TokenValidationError, AuthenticationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired platform refresh token",
        ) from exc


@router.post("/auth/logout", response_model=LogoutResponse)
def logout(
    payload: RefreshRequest,
    request: Request,
    session: Annotated[Session, Depends(get_platform_session)],
) -> LogoutResponse:
    """Revoke the persisted platform session represented by a refresh token."""

    try:
        claims = decode_platform_token(payload.refresh_token, "refresh")
        PlatformAuthenticationService(session).revoke(
            claims,
            payload.refresh_token,
            request_metadata(request),
        )
        session.commit()
        return LogoutResponse(revoked=True)
    except (TokenValidationError, AuthenticationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired platform refresh token",
        ) from exc


@router.get("/auth/me", response_model=PlatformActorSummary)
def current_platform_actor(
    actor: Annotated[PlatformActorContext, Depends(require_platform_actor)],
) -> PlatformActorSummary:
    """Return the current platform authorization context."""

    return PlatformActorSummary(
        account_id=actor.account_id,
        role_keys=list(actor.role_keys),
        permissions=sorted(actor.permissions),
    )


@router.get("/tenants", response_model=list[TenantSummary])
def list_tenants(
    actor: Annotated[
        PlatformActorContext,
        Depends(require_platform_permission("platform.tenants.read")),
    ],
    session: Annotated[Session, Depends(get_platform_session)],
) -> list[TenantSummary]:
    """List the global tenant directory for an authorized platform actor."""

    del actor
    return [TenantSummary.model_validate(tenant) for tenant in PlatformTenantService(session).list_tenants()]


@router.patch("/tenants/{tenant_id}/status", response_model=PlatformTenantStatusResponse)
def change_tenant_status(
    tenant_id: str,
    payload: PlatformTenantStatusRequest,
    request: Request,
    actor: Annotated[
        PlatformActorContext,
        Depends(require_platform_permission("platform.tenants.manage")),
    ],
    session: Annotated[Session, Depends(get_platform_session)],
) -> PlatformTenantStatusResponse:
    """Transition one tenant and revoke its sessions when access is disabled."""

    try:
        parsed_tenant_id = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found") from exc
    try:
        result = PlatformTenantService(session).change_status(
            parsed_tenant_id,
            payload.status,
            actor,
            request_metadata(request),
        )
        session.commit()
        return PlatformTenantStatusResponse(
            tenant_id=result.tenant_id,
            status=result.status,
            revoked_sessions=result.revoked_sessions,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found") from exc
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
