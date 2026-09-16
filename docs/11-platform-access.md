# Platform Access

## Status

Backend implemented in Production Increment 1. The platform management frontend and formal automated suite remain pending.

## Implemented Behavior

- Platform Administrator authentication uses `/api/v1/platform/auth` and independent persisted sessions.
- Platform JWTs carry the `platform` audience and contain no tenant or membership claim.
- Tenant JWTs carry the `tenant` audience. Each audience rejects credentials issued for the other.
- Effective global role assignments resolve an immutable platform actor and explicit permissions.
- Platform administrators can list safe tenant directory fields.
- Tenant lifecycle transitions are explicit: `setup` to `active` or `closed`, `active` to `suspended` or `closed`, and `suspended` to `active` or `closed`.
- `closed` is terminal.
- Suspending or closing a tenant revokes its active authentication sessions under transaction-local forced RLS context.
- Tenant actor resolution requires the tenant to remain active, so an already-issued access token cannot bypass suspension.
- Platform login attempts, logout, and tenant status changes are stored as global security events.
- Platform HTTP operations use the restricted PostgreSQL runtime role. Owner credentials remain limited to migrations and controlled onboarding.

## Security Boundary

Platform credentials authorize only platform routes. They do not produce `ActorContext`, do not set an operational tenant membership, and cannot call tenant-bound endpoints. The tenant directory API returns global tenant metadata only and never queries tenant-owned module tables.

## API Surface

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/platform/auth/login` | Create a revocable platform session |
| `POST` | `/api/v1/platform/auth/refresh` | Rotate the platform refresh token |
| `POST` | `/api/v1/platform/auth/logout` | Revoke the current platform session |
| `GET` | `/api/v1/platform/auth/me` | Resolve current platform roles and permissions |
| `GET` | `/api/v1/platform/tenants` | List the tenant directory |
| `PATCH` | `/api/v1/platform/tenants/{tenant_id}/status` | Apply an allowed tenant lifecycle transition |

## Pending

- Platform management frontend states and navigation.
- Production identity provisioning instead of approved synthetic demo seeding.
- Focused unit, API, permission, migration, and browser tests at the end of Increment 1.
