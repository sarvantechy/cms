"""Tenant role, permission, and effective assignment administration."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.domains.academics.models import Batch, Campus, Department, Program, Section
from app.domains.audit.models import AuditEvent
from app.domains.delivery.models import SubjectOffering
from app.domains.identity.models import (
    MembershipRoleAssignment,
    MembershipRoleScope,
    Permission,
    TenantMembership,
    TenantRole,
    TenantRolePermission,
)
from app.domains.identity.schemas import (
    MembershipRoleAssignmentInput,
    MembershipRoleAssignmentSummary,
    RoleScopeInput,
    TenantRoleAdminSummary,
    TenantRoleCreate,
    TenantRoleUpdate,
)
from app.domains.students.models import Student
from app.security_context import ActorContext


class IdentityRoleError(ValueError):
    """Represent one controlled role-administration validation failure."""


@dataclass(frozen=True, slots=True)
class ScopeKey:
    """Provide a hashable normalized identity for one assignment scope."""

    scope_type: str
    scope_reference_id: UUID | None


class IdentityRoleService:
    """Manage tenant roles and effective-dated membership assignments."""

    _scope_models: ClassVar[dict[str, type]] = {
        "campus": Campus,
        "department": Department,
        "program": Program,
        "batch": Batch,
        "section": Section,
        "subject_offering": SubjectOffering,
        "linked_student": Student,
    }

    def __init__(self, session: Session, actor: ActorContext) -> None:
        """Initialize the service and apply transaction-local tenant context."""

        self.session = session
        self.actor = actor
        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(actor.tenant_id)},
        )

    def list_permissions(self) -> tuple[Permission, ...]:
        """Return non-platform permissions available to tenant roles."""

        return tuple(
            self.session.scalars(
                select(Permission)
                .where(~Permission.key.startswith("platform."))
                .order_by(Permission.key)
            )
        )

    def list_roles(self) -> list[TenantRoleAdminSummary]:
        """Return tenant roles with their active permission keys."""

        roles = tuple(
            self.session.scalars(
                select(TenantRole)
                .where(TenantRole.tenant_id == self.actor.tenant_id)
                .order_by(TenantRole.display_name, TenantRole.key)
            )
        )
        if not roles:
            return []
        permission_rows = self.session.execute(
            select(TenantRolePermission.role_id, Permission.key)
            .join(Permission, Permission.id == TenantRolePermission.permission_id)
            .where(
                TenantRolePermission.tenant_id == self.actor.tenant_id,
                TenantRolePermission.role_id.in_(role.id for role in roles),
                TenantRolePermission.is_active,
            )
            .order_by(Permission.key)
        )
        permissions_by_role: dict[UUID, list[str]] = {role.id: [] for role in roles}
        for role_id, permission_key in permission_rows:
            permissions_by_role[role_id].append(permission_key)
        return [
            TenantRoleAdminSummary(
                id=role.id,
                key=role.key,
                display_name=role.display_name,
                description=role.description,
                is_active=role.is_active,
                is_system_managed=role.is_system_managed,
                permission_keys=permissions_by_role[role.id],
            )
            for role in roles
        ]

    def create_role(self, payload: TenantRoleCreate) -> TenantRoleAdminSummary:
        """Create and audit a custom tenant role with explicit permissions."""

        existing = self.session.scalar(
            select(TenantRole.id).where(
                TenantRole.tenant_id == self.actor.tenant_id,
                TenantRole.key == payload.key,
            )
        )
        if existing is not None:
            raise IdentityRoleError("Role key already exists")
        permissions = self._resolve_permissions(payload.permission_keys)
        role = TenantRole(
            tenant_id=self.actor.tenant_id,
            key=payload.key,
            display_name=payload.display_name.strip(),
            description=payload.description.strip(),
            is_active=True,
            is_system_managed=False,
        )
        self.session.add(role)
        self.session.flush()
        for permission in permissions:
            self.session.add(
                TenantRolePermission(
                    tenant_id=self.actor.tenant_id,
                    role_id=role.id,
                    permission_id=permission.id,
                    is_active=True,
                )
            )
        self._audit("identity.role.created", "tenant_role", role.id, {"key": role.key})
        self.session.flush()
        return self._role_summary(role)

    def update_role(self, role_id: UUID, payload: TenantRoleUpdate) -> TenantRoleAdminSummary:
        """Update and audit mutable custom-role metadata and permissions."""

        role = self._require_role(role_id, require_active=False)
        if role.is_system_managed:
            raise IdentityRoleError("System-managed roles cannot be edited")
        changes: dict[str, object] = {}
        for field in ("display_name", "description", "is_active"):
            value = getattr(payload, field)
            if value is not None and value != getattr(role, field):
                changes[field] = value
                setattr(role, field, value.strip() if isinstance(value, str) else value)
        if payload.permission_keys is not None:
            permissions = self._resolve_permissions(payload.permission_keys)
            desired_ids = {permission.id for permission in permissions}
            rows = tuple(
                self.session.scalars(
                    select(TenantRolePermission).where(
                        TenantRolePermission.tenant_id == self.actor.tenant_id,
                        TenantRolePermission.role_id == role.id,
                    )
                )
            )
            existing_by_permission = {row.permission_id: row for row in rows}
            for row in rows:
                row.is_active = row.permission_id in desired_ids
            for permission in permissions:
                if permission.id not in existing_by_permission:
                    self.session.add(
                        TenantRolePermission(
                            tenant_id=self.actor.tenant_id,
                            role_id=role.id,
                            permission_id=permission.id,
                            is_active=True,
                        )
                    )
            changes["permission_keys"] = sorted(payload.permission_keys)
        self.session.flush()
        if changes:
            self._audit("identity.role.updated", "tenant_role", role.id, changes)
            self.session.flush()
        return self._role_summary(role)

    def list_assignments(self, membership_id: UUID) -> list[MembershipRoleAssignmentSummary]:
        """Return active role assignments and scopes for one tenant membership."""

        self._require_membership(membership_id)
        assignments = tuple(
            self.session.execute(
                select(MembershipRoleAssignment, TenantRole)
                .join(
                    TenantRole,
                    (TenantRole.tenant_id == MembershipRoleAssignment.tenant_id)
                    & (TenantRole.id == MembershipRoleAssignment.role_id),
                )
                .where(
                    MembershipRoleAssignment.tenant_id == self.actor.tenant_id,
                    MembershipRoleAssignment.membership_id == membership_id,
                    MembershipRoleAssignment.ends_at.is_(None),
                )
                .order_by(TenantRole.display_name)
            )
        )
        scopes_by_assignment = self._scopes_by_assignment(
            tuple(assignment.id for assignment, _ in assignments)
        )
        return [
            MembershipRoleAssignmentSummary(
                assignment_id=assignment.id,
                role_id=role.id,
                role_key=role.key,
                role_name=role.display_name,
                starts_at=assignment.starts_at,
                scopes=[
                    RoleScopeInput(
                        scope_type=scope.scope_type,
                        scope_reference_id=scope.scope_reference_id,
                    )
                    for scope in scopes_by_assignment.get(assignment.id, ())
                ],
            )
            for assignment, role in assignments
        ]

    def replace_assignments(
        self,
        membership_id: UUID,
        desired: list[MembershipRoleAssignmentInput],
    ) -> list[MembershipRoleAssignmentSummary]:
        """Replace active assignments using effective dates without deleting history."""

        membership = self._require_membership(membership_id)
        if membership.id == self.actor.membership_id:
            raise IdentityRoleError("Administrators cannot change their own role assignments")
        if membership.status == "ended":
            raise IdentityRoleError("Ended memberships cannot receive role assignments")
        desired_by_role = {item.role_id: item for item in desired}
        if len(desired_by_role) != len(desired):
            raise IdentityRoleError("Each role may appear only once")
        for item in desired:
            self._require_role(item.role_id, require_active=True)
            self._validate_scopes(item.scopes)

        current = tuple(
            self.session.scalars(
                select(MembershipRoleAssignment).where(
                    MembershipRoleAssignment.tenant_id == self.actor.tenant_id,
                    MembershipRoleAssignment.membership_id == membership_id,
                    MembershipRoleAssignment.ends_at.is_(None),
                )
            )
        )
        scopes_by_assignment = self._scopes_by_assignment(
            tuple(assignment.id for assignment in current)
        )
        now = datetime.now(UTC)
        preserved_role_ids: set[UUID] = set()
        for assignment in current:
            target = desired_by_role.get(assignment.role_id)
            current_scopes = {
                ScopeKey(scope.scope_type, scope.scope_reference_id)
                for scope in scopes_by_assignment.get(assignment.id, ())
            }
            target_scopes = (
                {
                    ScopeKey(scope.scope_type, scope.scope_reference_id)
                    for scope in target.scopes
                }
                if target is not None
                else set()
            )
            if target is not None and current_scopes == target_scopes:
                preserved_role_ids.add(assignment.role_id)
            else:
                assignment.ends_at = now

        for role_id, target in desired_by_role.items():
            if role_id in preserved_role_ids:
                continue
            assignment = MembershipRoleAssignment(
                tenant_id=self.actor.tenant_id,
                membership_id=membership_id,
                role_id=role_id,
                starts_at=now,
            )
            self.session.add(assignment)
            self.session.flush()
            for scope in target.scopes:
                self.session.add(
                    MembershipRoleScope(
                        tenant_id=self.actor.tenant_id,
                        assignment_id=assignment.id,
                        scope_type=scope.scope_type,
                        scope_reference_id=scope.scope_reference_id,
                    )
                )
        self._audit(
            "identity.membership.roles_replaced",
            "tenant_membership",
            membership_id,
            {"role_ids": [str(role_id) for role_id in desired_by_role]},
        )
        self.session.flush()
        return self.list_assignments(membership_id)

    def _role_summary(self, role: TenantRole) -> TenantRoleAdminSummary:
        """Build one role summary from current persisted permission state."""

        return next(item for item in self.list_roles() if item.id == role.id)

    def _resolve_permissions(self, keys: list[str]) -> tuple[Permission, ...]:
        """Resolve distinct tenant-adoptable permission keys or reject the request."""

        normalized = tuple(sorted(set(keys)))
        if not normalized:
            raise IdentityRoleError("At least one role permission is required")
        if any(key.startswith("platform.") for key in normalized):
            raise IdentityRoleError("Platform permissions cannot be assigned to tenant roles")
        permissions = tuple(
            self.session.scalars(select(Permission).where(Permission.key.in_(normalized)))
        )
        if len(permissions) != len(normalized):
            raise IdentityRoleError("One or more permissions are unavailable")
        return permissions

    def _require_role(self, role_id: UUID, *, require_active: bool) -> TenantRole:
        """Return a tenant role while enforcing optional active state."""

        conditions = [TenantRole.tenant_id == self.actor.tenant_id, TenantRole.id == role_id]
        if require_active:
            conditions.append(TenantRole.is_active)
        role = self.session.scalar(select(TenantRole).where(*conditions))
        if role is None:
            raise IdentityRoleError("Tenant role was not found or is inactive")
        return role

    def _require_membership(self, membership_id: UUID) -> TenantMembership:
        """Return a tenant membership without exposing cross-tenant existence."""

        membership = self.session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == self.actor.tenant_id,
                TenantMembership.id == membership_id,
            )
        )
        if membership is None:
            raise IdentityRoleError("Membership was not found")
        return membership

    def _validate_scopes(self, scopes: list[RoleScopeInput]) -> None:
        """Validate uniqueness and tenant ownership of all referenced scopes."""

        keys = {ScopeKey(scope.scope_type, scope.scope_reference_id) for scope in scopes}
        if len(keys) != len(scopes):
            raise IdentityRoleError("Duplicate assignment scopes are not allowed")
        for scope in scopes:
            model = self._scope_models.get(scope.scope_type)
            if model is None:
                continue
            exists = self.session.scalar(
                select(model.id).where(
                    model.tenant_id == self.actor.tenant_id,
                    model.id == scope.scope_reference_id,
                )
            )
            if exists is None:
                raise IdentityRoleError(f"Invalid {scope.scope_type} scope reference")

    def _scopes_by_assignment(
        self,
        assignment_ids: tuple[UUID, ...],
    ) -> dict[UUID, tuple[MembershipRoleScope, ...]]:
        """Load assignment scopes in one query and group them by assignment."""

        grouped: dict[UUID, list[MembershipRoleScope]] = {}
        if not assignment_ids:
            return {}
        for scope in self.session.scalars(
            select(MembershipRoleScope)
            .where(
                MembershipRoleScope.tenant_id == self.actor.tenant_id,
                MembershipRoleScope.assignment_id.in_(assignment_ids),
            )
            .order_by(MembershipRoleScope.scope_type)
        ):
            grouped.setdefault(scope.assignment_id, []).append(scope)
        return {assignment_id: tuple(scopes) for assignment_id, scopes in grouped.items()}

    def _audit(
        self,
        action: str,
        entity_type: str,
        entity_id: UUID,
        details: dict[str, object],
    ) -> None:
        """Stage an actor-attributed identity administration audit event."""

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