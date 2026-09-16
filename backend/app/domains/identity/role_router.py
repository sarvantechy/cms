"""Protected APIs for tenant role and assignment administration."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.domains.identity.role_service import IdentityRoleError, IdentityRoleService
from app.domains.identity.router import get_runtime_session, require_permission
from app.domains.identity.schemas import (
    MembershipRoleAssignmentsReplace,
    MembershipRoleAssignmentSummary,
    PermissionAdminSummary,
    TenantRoleAdminSummary,
    TenantRoleCreate,
    TenantRoleUpdate,
)
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/identity", tags=["Identity roles"])


@router.get("/permissions", response_model=list[PermissionAdminSummary])
def list_permissions(
    actor: Annotated[ActorContext, Depends(require_permission("identity.roles.read"))],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> list[PermissionAdminSummary]:
    """List tenant-adoptable permissions for role configuration."""

    return [
        PermissionAdminSummary(key=item.key, description=item.description)
        for item in IdentityRoleService(session, actor).list_permissions()
    ]


@router.get("/roles", response_model=list[TenantRoleAdminSummary])
def list_roles(
    actor: Annotated[ActorContext, Depends(require_permission("identity.roles.read"))],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> list[TenantRoleAdminSummary]:
    """List tenant roles and active permissions."""

    return IdentityRoleService(session, actor).list_roles()


@router.post("/roles", response_model=TenantRoleAdminSummary, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: TenantRoleCreate,
    actor: Annotated[ActorContext, Depends(require_permission("identity.roles.manage"))],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> TenantRoleAdminSummary:
    """Create one custom role inside the actor's tenant."""

    try:
        result = IdentityRoleService(session, actor).create_role(payload)
        session.commit()
        return result
    except IdentityRoleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/roles/{role_id}", response_model=TenantRoleAdminSummary)
def update_role(
    role_id: UUID,
    payload: TenantRoleUpdate,
    actor: Annotated[ActorContext, Depends(require_permission("identity.roles.manage"))],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> TenantRoleAdminSummary:
    """Update one custom tenant role without deleting permission history."""

    try:
        result = IdentityRoleService(session, actor).update_role(role_id, payload)
        session.commit()
        return result
    except IdentityRoleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get(
    "/memberships/{membership_id}/role-assignments",
    response_model=list[MembershipRoleAssignmentSummary],
)
def list_membership_role_assignments(
    membership_id: UUID,
    actor: Annotated[ActorContext, Depends(require_permission("identity.roles.read"))],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> list[MembershipRoleAssignmentSummary]:
    """List one membership's active roles and scopes."""

    try:
        return IdentityRoleService(session, actor).list_assignments(membership_id)
    except IdentityRoleError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put(
    "/memberships/{membership_id}/role-assignments",
    response_model=list[MembershipRoleAssignmentSummary],
)
def replace_membership_role_assignments(
    membership_id: UUID,
    payload: MembershipRoleAssignmentsReplace,
    actor: Annotated[ActorContext, Depends(require_permission("identity.roles.manage"))],
    session: Annotated[Session, Depends(get_runtime_session)],
) -> list[MembershipRoleAssignmentSummary]:
    """Replace active membership roles and scopes using effective dates."""

    try:
        result = IdentityRoleService(session, actor).replace_assignments(
            membership_id,
            payload.assignments,
        )
        session.commit()
        return result
    except IdentityRoleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc