# Platform Access

**Status:** Implemented locally across backend and frontend; no deployment claim.

## Purpose
Authenticate platform operators and manage the global tenant directory without granting tenant-data access.

## Roles
- Platform Administrator: view tenants and apply controlled tenant lifecycle transitions.

## Workflow
1. Authenticate through the platform-only audience.
2. Review safe tenant directory fields.
3. Activate, suspend, restore, or close a tenant.
4. Revoke tenant sessions automatically when access is disabled.

## Core Rules
- Platform and tenant JWT audiences reject each other.
- Platform actors contain no tenant or membership claim.
- `closed` is terminal; every transition is globally audited.

## Data
`PlatformRoleAssignment`, `PlatformAuthenticationSession`, `PlatformSecurityEvent`, and `Tenant`.

## Current UI Behavior

- `/platform` provides isolated Platform Administrator login, tab-scoped refresh rotation, logout,
	tenant directory, and active/suspended/closed lifecycle controls.
- College Access provides invitations with one-time token delivery, membership activation,
	suspension and ending, forced logout, current-session revocation, password change, custom roles,
	permission grants, and effective-dated role/scope replacement.
- The college shell lists only active memberships discovered through forced RLS and rotates into a
	selected tenant through `/api/v1/auth/switch-tenant`.
- Platform and college credentials use separate clients, storage keys, token audiences, and routes.

## Production Completion

Replace the temporary one-time invitation-token display with a configured delivery provider and add
the deferred persisted automated test suite before a production-release claim.

## Acceptance Criteria
- Platform credentials cannot call tenant APIs.
- Suspending one tenant revokes only that tenant's sessions.
- Tenant lifecycle events retain actor and before/after state.

## Local Validation

- Backend Ruff and production OpenAPI import passed with 133 registered paths.
- Frontend TypeScript production build and Oxlint passed.
- Interactive Playwright validated Platform Administrator login and the two-tenant directory.
- Interactive Playwright validated College Access actor/session/membership data, invitation role
	choices, and the 61-permission custom-role catalogue without failed requests.
