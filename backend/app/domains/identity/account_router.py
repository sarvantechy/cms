"""FastAPI routes for tenant account and session lifecycle administration."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.domains.identity.account_service import (
    AccountLifecycleError,
    AccountLifecycleService,
    MembershipAdminRecord,
)
from app.domains.identity.auth_service import AuthenticationError
from app.domains.identity.router import (
    get_runtime_session,
    request_metadata,
    require_actor,
    require_permission,
)
from app.domains.identity.schemas import (
    InvitationAcceptanceRequest,
    InvitationAcceptanceResponse,
    InvitationRequest,
    InvitationResponse,
    MembershipAdminSummary,
    MembershipStatusRequest,
    MembershipStatusResponse,
    PasswordChangeRequest,
    SessionRevocationResponse,
    SessionSummary,
)
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/identity", tags=["Identity"])


def _membership_summary(record: MembershipAdminRecord) -> MembershipAdminSummary:
    """Convert an aggregated membership service record into the public contract."""

    membership = record.membership
    account = record.account
    return MembershipAdminSummary(
        id=membership.id,
        account_id=account.id,
        email=account.email,
        display_name=account.display_name,
        status=membership.status,
        joined_at=membership.joined_at,
        ended_at=membership.ended_at,
        role_keys=list(record.role_keys),
    )


@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def create_invitation(
    payload: InvitationRequest,
    request: Request,
    actor: Annotated[
        ActorContext,
        Depends(require_permission("identity.memberships.manage")),
    ],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> InvitationResponse:
    """Invite an account into the actor's tenant with explicit roles and scope."""

    try:
        invitation = AccountLifecycleService(session).invite(
            actor,
            payload.email,
            payload.display_name,
            payload.role_keys,
            payload.scope_type,
            payload.scope_reference_id,
            request_metadata(request),
        )
        session.commit()
        return InvitationResponse(
            invitation_id=invitation.invitation_id,
            membership_id=invitation.membership_id,
            invitation_token=invitation.token,
            expires_at=invitation.expires_at,
        )
    except AccountLifecycleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/invitations/accept", response_model=InvitationAcceptanceResponse)
def accept_invitation(
    payload: InvitationAcceptanceRequest,
    request: Request,
    session: Annotated[Session, Depends(get_runtime_session)],
) -> InvitationAcceptanceResponse:
    """Activate an invitation after setting or proving global account credentials."""

    try:
        tenant_id, membership_id = AccountLifecycleService(session).accept_invitation(
            payload.invitation_token,
            payload.password,
            request_metadata(request),
        )
        session.commit()
        return InvitationAcceptanceResponse(
            tenant_id=tenant_id,
            membership_id=membership_id,
            activated=True,
        )
    except AccountLifecycleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/password/change", response_model=SessionRevocationResponse)
def change_password(
    payload: PasswordChangeRequest,
    request: Request,
    actor: Annotated[ActorContext, Depends(require_actor)],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> SessionRevocationResponse:
    """Change the current account password and revoke its tenant sessions."""

    try:
        revoked = AccountLifecycleService(session).change_password(
            actor,
            payload.current_password,
            payload.new_password,
            request_metadata(request),
        )
        session.commit()
        return SessionRevocationResponse(revoked_sessions=revoked)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except AccountLifecycleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/sessions", response_model=list[SessionSummary])
def list_sessions(
    actor: Annotated[ActorContext, Depends(require_actor)],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> list[SessionSummary]:
    """List only the current account's sessions in the active tenant."""

    records = AccountLifecycleService(session).list_sessions(actor)
    return [
        SessionSummary(
            id=record.id,
            created_at=record.created_at,
            expires_at=record.expires_at,
            last_used_at=record.last_used_at,
            revoked_at=record.revoked_at,
            ip_address=record.ip_address,
            user_agent=record.user_agent,
        )
        for record in records
    ]


@router.delete("/sessions/{session_id}", response_model=SessionRevocationResponse)
def revoke_session(
    session_id: UUID,
    request: Request,
    actor: Annotated[ActorContext, Depends(require_actor)],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> SessionRevocationResponse:
    """Revoke one current-account session inside the active tenant."""

    try:
        revoked = AccountLifecycleService(session).revoke_session(
            actor,
            session_id,
            request_metadata(request),
        )
        session.commit()
        return SessionRevocationResponse(revoked_sessions=revoked)
    except AccountLifecycleError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/memberships", response_model=list[MembershipAdminSummary])
def list_memberships(
    actor: Annotated[
        ActorContext,
        Depends(require_permission("identity.accounts.read")),
    ],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> list[MembershipAdminSummary]:
    """List memberships and assigned role keys inside the actor's tenant."""

    records = AccountLifecycleService(session).list_memberships(actor)
    return [_membership_summary(record) for record in records]


@router.patch("/memberships/{membership_id}/status", response_model=MembershipStatusResponse)
def change_membership_status(
    membership_id: UUID,
    payload: MembershipStatusRequest,
    request: Request,
    actor: Annotated[
        ActorContext,
        Depends(require_permission("identity.memberships.manage")),
    ],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> MembershipStatusResponse:
    """Apply an allowed membership lifecycle transition in the actor's tenant."""

    try:
        membership, revoked = AccountLifecycleService(session).change_membership_status(
            actor,
            membership_id,
            payload.status,
            request_metadata(request),
        )
        session.commit()
        return MembershipStatusResponse(
            membership_id=membership.id,
            status=membership.status,
            revoked_sessions=revoked,
        )
    except AccountLifecycleError as exc:
        detail = str(exc)
        response_status = (
            status.HTTP_404_NOT_FOUND
            if detail == "Membership was not found"
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=response_status, detail=detail) from exc


@router.post(
    "/memberships/{membership_id}/revoke-sessions",
    response_model=SessionRevocationResponse,
)
def revoke_membership_sessions(
    membership_id: UUID,
    request: Request,
    actor: Annotated[
        ActorContext,
        Depends(require_permission("identity.memberships.manage")),
    ],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> SessionRevocationResponse:
    """Revoke all active sessions for one membership in the actor's tenant."""

    try:
        revoked = AccountLifecycleService(session).revoke_membership_sessions(
            actor,
            membership_id,
            request_metadata(request),
        )
        session.commit()
        return SessionRevocationResponse(revoked_sessions=revoked)
    except AccountLifecycleError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
