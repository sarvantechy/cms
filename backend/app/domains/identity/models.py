from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

TENANT_ID_REFERENCE = "tenants.id"
ACCOUNT_ID_REFERENCE = "accounts.id"
ROLE_TEMPLATE_ID_REFERENCE = "role_templates.id"
TENANT_MEMBERSHIP_REFERENCE = (
    "tenant_memberships.tenant_id",
    "tenant_memberships.id",
)
ON_DELETE_SET_NULL = "SET NULL"


class Account(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represent one global login identity that may join multiple colleges."""

    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint("email = lower(email)", name="ck_accounts_normalized_email"),)

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define one stable action that backend authorization can enforce."""

    __tablename__ = "permissions"

    key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(300), nullable=False)


class RoleTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define a platform-provided baseline role that tenants may adopt."""

    __tablename__ = "role_templates"

    key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    is_platform_role: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class RoleTemplatePermission(Base):
    """Associate a baseline role template with one default permission."""

    __tablename__ = "role_template_permissions"

    role_template_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(ROLE_TEMPLATE_ID_REFERENCE, ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )


class PlatformRoleAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Assign a platform-only role template outside normal tenant authorization."""

    __tablename__ = "platform_role_assignments"
    __table_args__ = (UniqueConstraint("account_id", "role_template_id"),)

    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(ACCOUNT_ID_REFERENCE, ondelete="CASCADE"), nullable=False
    )
    role_template_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(ROLE_TEMPLATE_ID_REFERENCE, ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_by_account_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(ACCOUNT_ID_REFERENCE, ondelete=ON_DELETE_SET_NULL)
    )
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PlatformAuthenticationSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one revocable session for the isolated platform audience."""

    __tablename__ = "platform_authentication_sessions"

    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(ACCOUNT_ID_REFERENCE, ondelete="CASCADE"), nullable=False
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))


class PlatformSecurityEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Record platform authentication and administration events globally."""

    __tablename__ = "platform_security_events"

    account_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(ACCOUNT_ID_REFERENCE, ondelete=ON_DELETE_SET_NULL)
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    details: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))


class TenantMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Grant an account lifecycle-managed access to one tenant."""

    __tablename__ = "tenant_memberships"
    __table_args__ = (
        CheckConstraint(
            "status IN ('invited', 'active', 'suspended', 'ended')",
            name="ck_tenant_memberships_status",
        ),
        UniqueConstraint("tenant_id", "account_id"),
        UniqueConstraint("tenant_id", "id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(TENANT_ID_REFERENCE, ondelete="RESTRICT"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(ACCOUNT_ID_REFERENCE, ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="invited")
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TenantRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represent a tenant-owned role assembled from explicit permissions."""

    __tablename__ = "tenant_roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "key"),
        UniqueConstraint("tenant_id", "id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(TENANT_ID_REFERENCE, ondelete="RESTRICT"), nullable=False
    )
    template_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(ROLE_TEMPLATE_ID_REFERENCE, ondelete=ON_DELETE_SET_NULL)
    )
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_system_managed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class TenantRolePermission(Base):
    """Grant one permission to a role while retaining tenant-safe linkage."""

    __tablename__ = "tenant_role_permissions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "role_id"],
            ["tenant_roles.tenant_id", "tenant_roles.id"],
            ondelete="CASCADE",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(TENANT_ID_REFERENCE, ondelete="RESTRICT"), primary_key=True
    )
    role_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    permission_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class MembershipRoleAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Assign one tenant role to a membership with effective dates."""

    __tablename__ = "membership_role_assignments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            TENANT_MEMBERSHIP_REFERENCE,
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "role_id"],
            ["tenant_roles.tenant_id", "tenant_roles.id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id"),
        Index(
            "uq_membership_role_assignments_active",
            "tenant_id",
            "membership_id",
            "role_id",
            unique=True,
            postgresql_where=text("ends_at IS NULL"),
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(TENANT_ID_REFERENCE, ondelete="RESTRICT"), nullable=False
    )
    membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    role_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MembershipRoleScope(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Restrict one role assignment to a supported institutional boundary."""

    __tablename__ = "membership_role_scopes"
    __table_args__ = (
        CheckConstraint(
            "scope_type IN ('institution', 'campus', 'department', 'program', "
            "'batch', 'section', 'subject_offering', 'linked_student', 'own_record')",
            name="ck_membership_role_scopes_type",
        ),
        CheckConstraint(
            "(scope_type IN ('institution', 'own_record') AND scope_reference_id IS NULL) "
            "OR (scope_type NOT IN ('institution', 'own_record') "
            "AND scope_reference_id IS NOT NULL)",
            name="ck_membership_role_scopes_reference",
        ),
        UniqueConstraint(
            "tenant_id",
            "assignment_id",
            "scope_type",
            "scope_reference_id",
            name="uq_membership_role_scopes_resolved",
            postgresql_nulls_not_distinct=True,
        ),
        ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["membership_role_assignments.tenant_id", "membership_role_assignments.id"],
            ondelete="CASCADE",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(TENANT_ID_REFERENCE, ondelete="RESTRICT"), nullable=False
    )
    assignment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_reference_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))


class AuthenticationSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one revocable refresh-token session bound to a tenant membership."""

    __tablename__ = "authentication_sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            TENANT_MEMBERSHIP_REFERENCE,
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(TENANT_ID_REFERENCE, ondelete="RESTRICT"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(ACCOUNT_ID_REFERENCE, ondelete="RESTRICT"), nullable=False
    )
    membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))


class LoginHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Record successful and failed tenant login attempts without storing credentials."""

    __tablename__ = "login_history"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(TENANT_ID_REFERENCE, ondelete="RESTRICT"), nullable=False
    )
    account_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(ACCOUNT_ID_REFERENCE, ondelete=ON_DELETE_SET_NULL)
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    succeeded: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(80))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))


class AccountInvitation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist a single-use tenant membership invitation as a token digest."""

    __tablename__ = "account_invitations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            TENANT_MEMBERSHIP_REFERENCE,
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(TENANT_ID_REFERENCE, ondelete="RESTRICT"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(ACCOUNT_ID_REFERENCE, ondelete="CASCADE"), nullable=False
    )
    membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    invited_by_account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(ACCOUNT_ID_REFERENCE, ondelete="RESTRICT"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
