from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.tenancy.schemas import TenantSummary
from app.security_context import ActorScope


class RoleSummary(BaseModel):
    """Describe one resolved tenant role without exposing persistence internals."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    display_name: str
    description: str


class MembershipSummary(BaseModel):
    """Describe an account's selectable membership in one college tenant."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    tenant: TenantSummary
    roles: list[RoleSummary]


class ActorSummary(BaseModel):
    """Expose the active authenticated actor context used by the frontend shell."""

    account_id: UUID
    tenant_id: UUID
    membership_id: UUID
    role_keys: list[str]
    permissions: list[str]
    scopes: list[ActorScope]


class LoginRequest(BaseModel):
    """Collect tenant and account credentials for a tenant-bound login."""

    tenant_key: str = Field(min_length=1, max_length=64)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=72)


class RefreshRequest(BaseModel):
    """Carry a refresh token for rotation or revocation."""

    refresh_token: str = Field(min_length=1)


class TenantSwitchRequest(BaseModel):
    """Select a target tenant for an authenticated account by stable tenant key."""

    tenant_key: str = Field(min_length=1, max_length=64)


class TokenResponse(BaseModel):
    """Return rotated bearer credentials and the resolved actor context."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    actor: ActorSummary


class LogoutResponse(BaseModel):
    """Confirm that an authentication session has been revoked."""

    revoked: bool


class InvitationRequest(BaseModel):
    """Request a tenant membership with one or more initial role assignments."""

    email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=1, max_length=160)
    role_keys: list[str] = Field(min_length=1, max_length=8)
    scope_type: str = Field(default="institution", max_length=32)
    scope_reference_id: UUID | None = None

    @model_validator(mode="after")
    def validate_scope_reference(self) -> "InvitationRequest":
        """Require identifiers only for scope types that reference domain records."""

        unreferenced = {"institution", "own_record"}
        if (self.scope_type in unreferenced) != (self.scope_reference_id is None):
            raise ValueError("Scope reference does not match scope type")
        return self


class InvitationResponse(BaseModel):
    """Return an invitation token for delivery by a future communication provider."""

    invitation_id: UUID
    membership_id: UUID
    invitation_token: str
    expires_at: datetime


class InvitationAcceptanceRequest(BaseModel):
    """Accept an invitation using new or existing account credentials."""

    invitation_token: str = Field(min_length=1)
    password: str = Field(min_length=1, max_length=72)


class InvitationAcceptanceResponse(BaseModel):
    """Confirm activation of an invited tenant membership."""

    tenant_id: UUID
    membership_id: UUID
    activated: bool


class PasswordChangeRequest(BaseModel):
    """Collect current and replacement credentials for an authenticated account."""

    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=1, max_length=72)


class SessionSummary(BaseModel):
    """Describe one authentication session without exposing token material."""

    id: UUID
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None
    ip_address: str | None
    user_agent: str | None


class SessionRevocationResponse(BaseModel):
    """Report how many active sessions were revoked by an operation."""

    revoked_sessions: int


class MembershipAdminSummary(BaseModel):
    """Describe one tenant membership for authorized identity administration."""

    id: UUID
    account_id: UUID
    email: str
    display_name: str
    status: str
    joined_at: datetime | None
    ended_at: datetime | None
    role_keys: list[str]


class MembershipStatusRequest(BaseModel):
    """Request an allowed administrative membership lifecycle transition."""

    status: Literal["active", "suspended", "ended"]


class MembershipStatusResponse(BaseModel):
    """Return the resulting membership state and revoked-session count."""

    membership_id: UUID
    status: str
    revoked_sessions: int


class PermissionAdminSummary(BaseModel):
    """Describe one tenant-adoptable permission for role configuration."""

    key: str
    description: str


class TenantRoleAdminSummary(BaseModel):
    """Describe one tenant role and its currently active permissions."""

    id: UUID
    key: str
    display_name: str
    description: str
    is_active: bool
    is_system_managed: bool
    permission_keys: list[str]


class TenantRoleCreate(BaseModel):
    """Create one custom tenant role with explicit permissions."""

    key: str = Field(min_length=3, max_length=80, pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=300)
    permission_keys: list[str] = Field(min_length=1)


class TenantRoleUpdate(BaseModel):
    """Update mutable custom-role metadata or active permissions."""

    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=300)
    is_active: bool | None = None
    permission_keys: list[str] | None = None

    @model_validator(mode="after")
    def require_change(self) -> "TenantRoleUpdate":
        """Reject empty role updates that cannot change persisted state."""

        if not self.model_fields_set:
            raise ValueError("At least one role field is required")
        if self.permission_keys is not None and not self.permission_keys:
            raise ValueError("At least one role permission is required")
        return self


ScopeType = Literal[
    "institution",
    "campus",
    "department",
    "program",
    "batch",
    "section",
    "subject_offering",
    "linked_student",
    "own_record",
]


class RoleScopeInput(BaseModel):
    """Select one supported scope for a membership role assignment."""

    scope_type: ScopeType
    scope_reference_id: UUID | None = None

    @model_validator(mode="after")
    def validate_reference_shape(self) -> "RoleScopeInput":
        """Require references only for scopes that target domain records."""

        unreferenced = {"institution", "own_record"}
        if (self.scope_type in unreferenced) != (self.scope_reference_id is None):
            raise ValueError("Scope reference does not match scope type")
        return self


class MembershipRoleAssignmentInput(BaseModel):
    """Select one tenant role and its complete active scope set."""

    role_id: UUID
    scopes: list[RoleScopeInput] = Field(min_length=1)


class MembershipRoleAssignmentsReplace(BaseModel):
    """Replace the active role assignments for one tenant membership."""

    assignments: list[MembershipRoleAssignmentInput] = Field(min_length=1)


class MembershipRoleAssignmentSummary(BaseModel):
    """Describe one effective membership role assignment and its scopes."""

    assignment_id: UUID
    role_id: UUID
    role_key: str
    role_name: str
    starts_at: datetime | None
    scopes: list[RoleScopeInput]


class PlatformLoginRequest(BaseModel):
    """Collect credentials for platform-only authentication."""

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=72)


class PlatformActorSummary(BaseModel):
    """Expose a platform actor without tenant or membership claims."""

    account_id: UUID
    role_keys: list[str]
    permissions: list[str]


class PlatformTokenResponse(BaseModel):
    """Return credentials restricted to platform administration routes."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    actor: PlatformActorSummary


class PlatformTenantStatusRequest(BaseModel):
    """Request an allowed tenant lifecycle transition."""

    status: Literal["active", "suspended", "closed"]


class PlatformTenantStatusResponse(BaseModel):
    """Return a tenant lifecycle result and invalidated session count."""

    tenant_id: UUID
    status: str
    revoked_sessions: int
