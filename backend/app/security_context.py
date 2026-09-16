from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass(frozen=True, slots=True)
class ActorScope:
    """Describe one institutional boundary assigned to an actor role."""

    scope_type: str
    scope_reference_id: UUID | None


@dataclass(frozen=True, slots=True)
class ActorContext:
    """Carry immutable authenticated identity and authorization state for a request."""

    account_id: UUID
    tenant_id: UUID
    membership_id: UUID
    role_keys: tuple[str, ...]
    permissions: frozenset[str]
    scopes: tuple[ActorScope, ...]

    def has_permission(self, permission: str) -> bool:
        """Return whether the actor holds an explicitly resolved permission."""

        return permission in self.permissions

    def scopes_of_type(self, scope_type: str) -> tuple[ActorScope, ...]:
        """Return the actor scopes matching one supported scope type."""

        return tuple(scope for scope in self.scopes if scope.scope_type == scope_type)

    def student_scope_ids(self) -> tuple[UUID, ...] | None:
        """Return explicit linked-student IDs or None for non-self-service actors."""

        if not ({"students.own.read", "students.linked.read"} & self.permissions):
            return None
        scope_types = {"own_record", "linked_student"}
        return tuple(scope.scope_reference_id for scope in self.scopes if scope.scope_type in scope_types and scope.scope_reference_id is not None)


def resolve_actor_student_ids(session: Session, actor: ActorContext) -> tuple[UUID, ...] | None:
    """Resolve self-service student IDs from explicit links or canonical account identity."""

    explicit_ids = actor.student_scope_ids()
    if explicit_ids is None:
        return None
    if explicit_ids:
        return explicit_ids
    if not actor.scopes_of_type("own_record"):
        return ()
    from app.domains.identity.models import Account
    from app.domains.students.models import Person, Student

    return tuple(session.scalars(select(Student.id).join(Person, (Person.tenant_id == Student.tenant_id) & (Person.id == Student.person_id)).join(Account, Account.email == Person.email).where(Student.tenant_id == actor.tenant_id, Account.id == actor.account_id)))


@dataclass(frozen=True, slots=True)
class PlatformActorContext:
    """Carry an authenticated platform identity without tenant data access."""

    account_id: UUID
    role_keys: tuple[str, ...]
    permissions: frozenset[str]

    def has_permission(self, permission: str) -> bool:
        """Return whether the platform actor holds an explicit permission."""

        return permission in self.permissions
