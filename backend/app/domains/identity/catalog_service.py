"""Synchronization services for the platform authorization catalogue."""

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.domains.identity.catalog import PERMISSIONS, ROLE_TEMPLATES, RoleTemplateDefinition
from app.domains.identity.models import (
    Permission,
    RoleTemplate,
    RoleTemplatePermission,
    TenantRole,
    TenantRolePermission,
)
from app.domains.tenancy.models import Tenant


class AuthorizationCatalogueService:
    """Synchronize stable permissions and role templates without replacing custom roles."""

    def __init__(self, session: Session) -> None:
        """Initialize the service with an owner-level database session."""

        self.session = session

    def sync_global_catalogue(self) -> dict[str, RoleTemplate]:
        """Upsert global permissions, role templates, and exact default mappings."""

        permissions = self._sync_permissions()
        templates = self._sync_role_templates()
        self.session.flush()

        for definition in ROLE_TEMPLATES:
            template = templates[definition.key]
            self.session.execute(
                delete(RoleTemplatePermission).where(
                    RoleTemplatePermission.role_template_id == template.id
                )
            )
            self.session.add_all(
                RoleTemplatePermission(
                    role_template_id=template.id,
                    permission_id=permissions[permission_key].id,
                )
                for permission_key in definition.permission_keys
            )

        self.session.flush()
        return templates

    def adopt_template(self, tenant: Tenant, template: RoleTemplateDefinition) -> TenantRole:
        """Create or refresh one system-managed tenant role from a baseline template."""

        if template.is_platform_role:
            raise ValueError("Platform roles cannot be adopted inside a tenant")

        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant.id)},
        )
        template_record = self.session.scalar(
            select(RoleTemplate).where(RoleTemplate.key == template.key)
        )
        if template_record is None:
            raise RuntimeError("Global authorization catalogue must be synchronized first")

        role = self.session.scalar(
            select(TenantRole).where(
                TenantRole.tenant_id == tenant.id,
                TenantRole.key == template.key,
            )
        )
        if role is None:
            role = TenantRole(tenant_id=tenant.id, key=template.key)
            self.session.add(role)
        elif not role.is_system_managed:
            raise ValueError(f"Tenant role key '{template.key}' is already custom-managed")

        role.template_id = template_record.id
        role.display_name = template.display_name
        role.description = template.description
        role.is_active = True
        role.is_system_managed = True
        self.session.flush()

        permission_ids = tuple(
            self.session.scalars(
                select(Permission.id).where(Permission.key.in_(template.permission_keys))
            )
        )
        if len(permission_ids) != len(template.permission_keys):
            raise RuntimeError(f"Template '{template.key}' references unknown permissions")

        self.session.execute(
            delete(TenantRolePermission).where(
                TenantRolePermission.tenant_id == tenant.id,
                TenantRolePermission.role_id == role.id,
            )
        )
        self.session.add_all(
            TenantRolePermission(
                tenant_id=tenant.id,
                role_id=role.id,
                permission_id=permission_id,
            )
            for permission_id in permission_ids
        )
        self.session.flush()
        return role

    def _sync_permissions(self) -> dict[str, Permission]:
        """Upsert stable permission metadata and return records by key."""

        records = {
            permission.key: permission
            for permission in self.session.scalars(select(Permission)).all()
        }
        for definition in PERMISSIONS:
            permission = records.get(definition.key)
            if permission is None:
                permission = Permission(key=definition.key, description=definition.description)
                self.session.add(permission)
                records[definition.key] = permission
            else:
                permission.description = definition.description
        return records

    def _sync_role_templates(self) -> dict[str, RoleTemplate]:
        """Upsert stable role-template metadata and return records by key."""

        records = {
            template.key: template
            for template in self.session.scalars(select(RoleTemplate)).all()
        }
        for definition in ROLE_TEMPLATES:
            template = records.get(definition.key)
            if template is None:
                template = RoleTemplate(key=definition.key)
                self.session.add(template)
                records[definition.key] = template
            template.display_name = definition.display_name
            template.description = definition.description
            template.is_platform_role = definition.is_platform_role
        return records
