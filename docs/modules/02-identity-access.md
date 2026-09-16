# Identity and Access

**Status:** Authentication, College Access administration, tenant switching, and role portals are implemented and interactively validated locally; provider delivery remains release work.

## Purpose

Provide tenant-bound authentication, memberships, configurable roles, scopes, invitations, passwords, and revocable sessions.

## Roles

- College Administrator: manage memberships and delegated tenant roles.
- Every tenant user: authenticate, rotate tokens, change password, and manage own sessions.

## Workflow

1. Select a college and authenticate an active membership.
2. Resolve roles, permissions, and scopes into immutable `ActorContext`.
3. Rotate refresh credentials on browser restoration.
4. Revoke the persisted session on sign-out.
5. Invite, suspend, restore, end, or force-logout memberships through protected APIs.

## Core Rules

- Tenant identity comes from `ActorContext`, never client input.
- Access tokens are memory-only; refresh tokens are tab-scoped and rotated.
- Ended memberships are terminal and self-suspension is blocked.

## Data

Accounts, memberships, roles, role permissions, scoped assignments, invitations, sessions, login history, and audit events.

## Current UI Behavior

`/login` authenticates seeded tenant roles against PostgreSQL. Reload restores the session and
logout revokes it. College Access provides invitations, membership lifecycle, role/permission/scope
editing, password change, session management, forced logout, and tenant switching. Navigation and
source requests derive from the authenticated actor's permissions and record scopes.

## Production Completion

Replace temporary one-time invitation-token display with configured provider delivery and add the
deferred automated permission, session, RLS, and browser suites.

## Acceptance Criteria

- Invalid and cross-tenant credentials reveal no account details.
- Revocation invalidates unexpired access credentials.
- UI navigation follows resolved permissions, not role labels.
