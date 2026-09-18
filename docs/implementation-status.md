# Implementation Status

## Current Increment

### Operational College Management Foundation

Status: Core closures plus Slices 1 through 4 are implemented locally; Slice 5 provider execution and later release hardening remain

The production FastAPI path, PostgreSQL schema, forced tenant RLS, authenticated College Administrator workspace, and nine requested operational areas are implemented locally. This is a repository and local-validation statement, not an AWS deployment claim.

An AWS stakeholder-demo plan is prepared in `docs/12-aws-demo-deployment-plan.md`. The existing
deployment script and Nginx file are frontend-only prototypes and are not yet an approved full-stack
release path. No AWS deployment, provisioning, DNS change, database migration, or service restart
has been performed for this CMS.

## Implemented

- React and TypeScript frontend scaffolded with Vite.
- Responsive CMS application shell with desktop sidebar and mobile drawer.
- Opaque in-workspace create, edit, detail, and document screens replace every portal popup,
  native dialog, and translucent overlay; Back or Cancel restores the owning workspace.
- Grouped college navigation using Lucide icons.
- Authenticated synthetic College Administrator identities for INDUS ARTS & SCIENCE INTERNATIONAL COLLEGE and INDUS LAW COLLEGE.
- College-specific source-backed management and role dashboards with operational briefs,
  role-colored metric links, priority queues, quick access, and responsive layouts.
- Three visual themes built with shared CSS variables.
- Stable frontend routes for the implemented administrator workspaces.
- FastAPI backend scaffold with CORS and a live health endpoint.
- Local PostgreSQL 16 service configuration using port `5434`.
- Separate PostgreSQL owner and runtime roles prepared for migration and forced RLS work.
- Frontend production build and lint pass.
- Backend Ruff and health checks pass.
- Live browser review covers both tenant logins, real mutations, cross-tenant isolation, desktop rendering, and 390px mobile overflow.
- Public institutional website for INDUS ARTS & SCIENCE INTERNATIONAL COLLEGE.
- Public admissions, academics, events, campus-life, address, and contact sections.
- Demo login page with visible synthetic sample accounts and a shared temporary demo password.
- Permission-aware College Administrator navigation and API-backed operational screens.
- Idempotent synthetic operational seed records for both INDUS tenants, created only through explicit `--seed-demo` onboarding.

## Production Foundation Implemented

- Authoritative role and module plan covering 17 baseline roles and tenant-configurable custom roles.
- SQLAlchemy declarative base, UUID primary-key mixin, and database-managed timestamp mixin.
- Separate cached owner and restricted runtime PostgreSQL session factories.
- Transaction-scoped runtime session helper that sets `app.tenant_id` locally.
- Tenant persistence with lifecycle status, timezone, demo marker, and branding fields.
- Global account and permission persistence.
- Global baseline role templates and default template-permission mapping.
- Tenant-customizable roles and explicit tenant role permissions.
- Account-to-tenant memberships with lifecycle and effective dates.
- Multiple role assignments per membership rather than one hard-coded role column.
- Role assignment scopes for institution, campus, department, program, batch, section, subject offering, linked student, and own-record access.
- Tenant-safe composite foreign keys between memberships, tenant roles, assignments, and scopes.
- Initial Alembic environment and platform identity migration.
- Forced PostgreSQL RLS policies on all tenant-owned foundation tables.
- Restricted `cms_runtime` grants and global-reference read grants.
- Immutable `ActorContext` and `ActorScope` contracts.
- Typed tenant, role, membership, and actor response schemas.
- Initial migration applied successfully to the local PostgreSQL 16 database.
- Stable catalogue of 58 backend permission keys covering all planned product modules.
- All 17 baseline role templates with explicit default permission mappings.
- Platform permissions separated from tenant-adoptable College Administrator permissions.
- Idempotent catalogue synchronization that refreshes platform definitions without changing
  tenant-created custom roles.
- Idempotent onboarding for INDUS ARTS & SCIENCE INTERNATIONAL COLLEGE and INDUS LAW COLLEGE.
- One system-managed College Administrator role adopted independently inside each initial tenant.
- Local onboarding command: `cd backend && ../.venv/bin/python -m app.commands.onboard_tenants`.
- Tenant-bound authentication sessions with persisted one-way refresh-token digests and revocation.
- Tenant-scoped successful and failed login history with generic external credential errors.
- Append-only tenant audit events for login, logout, and tenant switching.
- Bcrypt password hashing with explicit 12-to-72-byte input limits.
- Signed access and refresh tokens bound to account, tenant, and persisted session identifiers.
- Refresh-token rotation rejects reuse of the preceding refresh token.
- Revoked sessions invalidate still-unexpired access tokens through persisted session checks.
- Tenant switching verifies an active target membership and recomputes target roles and permissions.
- Reusable `require_actor()` and exact `require_permission()` FastAPI dependencies.
- Production authentication routes for login, refresh, logout, tenant switching, and current actor.
- Explicit `--seed-demo` administrator seeding controlled by `DEMO_SEED_PASSWORD`.
- Synthetic administrators, active memberships, College Administrator assignments, and institution
  scopes for both initial INDUS tenants.
- Global, effective-dated Platform Administrator assignments kept outside tenant role tables.
- Owner-only synthetic Platform Administrator seeding with no tenant membership or tenant JWT path.
- Tenant-scoped, single-use membership invitations stored only as token digests.
- Forty-eight-hour invitation expiry, prior invitation revocation, and role/scope validation.
- Safe invitation acceptance for both new and existing global accounts without tenant-driven
  replacement of an existing account password.
- Authenticated password changes that revoke every active session in the current tenant.
- Self-service session listing and selected-session revocation without exposing another account's
  sessions.
- Audited membership invitation, acceptance, password change, and session revocation operations.
- Production identity routes for invitation creation/acceptance, password change, session listing,
  and selected-session revocation.
- Tenant-scoped administrative membership listing with account, role, scope, and lifecycle details.
- Administrative suspension, reactivation, and terminal membership ending with explicit transition
  rules, self-protection, and cross-tenant concealment.
- Tenant-wide forced logout for a selected membership, including automatic session revocation on
  suspension or ending.
- Membership ending closes active role assignments, while suspension and ending revoke pending
  invitations and preserve attributable audit history.
- Reactivation requires previously established account credentials; invitation acceptance remains
  the only first-activation path.
- Platform-only login, refresh rotation, logout, and current-actor APIs backed by independent
  revocable sessions and audience-restricted JWTs.
- Immutable platform actor context resolved from effective global role assignments and explicit
  platform permissions, without tenant or membership claims.
- Platform tenant-directory listing and controlled setup, active, suspended, and closed lifecycle
  transitions; closed tenants are terminal.
- Tenant suspension and closure transactionally revoke tenant authentication sessions under forced
  RLS, while tenant authentication also rechecks active tenant status on every request.
- Global platform security events for login attempts, logout, and tenant status transitions.
- Least-privilege platform API operation through `cms_runtime`; migration-owner credentials remain
  reserved for migrations and controlled onboarding.

## Operational Domains Implemented Locally

- Academic masters: campuses, years, terms, departments, programs, subjects, batches, sections,
  rooms, regulations, curricula, curriculum subjects, calendars, numbering formats, and grading.
- Admissions: enquiries, campaigns, applicants, applications, documents, verification, seat pools,
  offers, controlled lifecycle transitions, atomic seat allocation, append-only history, and
  idempotent accepted-applicant conversion. The College Administrator has source-backed creation,
  review, capacity, transition, private-document download, and conversion screens for this staff
  workflow. An authenticated Applicant portal provides membership-bound profile editing,
  validated private uploads, submission, status tracking, and own-document downloads.
- Students and guardians: people, students, guardians, links, enrollment, placement, lifecycle
  history, documents, subject registrations, progression, transfer/readmission requests, and
  certificate requests. The searchable administrator profile exposes reviewed lifecycle
  transitions, while Student-own, Guardian-linked, HOD Department, and Class Advisor Section reads
  remain permission and record scoped. Issued certificate requests have branded printable
  documents available through the Student My records route.
- Faculty and delivery: canonical-person faculty profiles, department postings, offerings,
  allocations, derived workload, timetable conflict detection, class-session generation,
  substitutions, lesson plans, learning materials, and syllabus progress. These operations are
  source-backed in the College Administrator workspace. HOD reads and mutations are constrained to
  assigned Department offerings, Faculty, timetable, and delivery records.
- Attendance and leave: attendance records, register locking, correction approval/rejection, and
  leave review workflows. The College Administrator workspace supports attendance entry,
  correction and leave creation/review, before/after correction outcomes, and source-derived
  percentage, threshold, shortage, and examination-eligibility presentation. Class Advisor and HOD
  attendance records, corrections, leave, sessions, Students, and summaries are server scoped.
- Fees and payments: fee-head and plan configuration, enrollment-linked invoices, idempotent
  allocated payments, receipts, compensating reversals, concession/refund request and approval,
  cashier close variance, gateway reconciliation, and derived student ledgers. The complete College
  Administrator and Accountant collection workflows are source-backed in the UI. Payment receipt
  documents derive tenant branding, Student identity, payment facts, and invoice allocations from
  authoritative records; Student and Guardian access remains linked-record scoped.
- Examinations and results: schemes, versioned grade rules, sessions, schedules, eligibility,
  capacity-aware seating, invigilation, marks entry/verification/locking, reviewed adjustments,
  reproducible versioned publication, GPA/CGPA, hall-ticket sources, result detail, reopening,
  republishing, and transcripts. Controller operations are source-backed in the UI. Immutable
  issuance metadata and printable hall tickets, grade cards, and result-version-manifest
  transcripts are available to Controllers and scoped Students.
- Communications: notice CRUD, server-side audience resolution, scheduling, publication, in-app
  delivery, approval history, durable provider jobs, retry visibility, preferences,
  acknowledgement, and read state. Nine non-administrator role portals derive navigation and
  source requests from backend permissions and scopes; read-only users list only delivered notices.
- Events and activities: club and event setup, publication, eligibility, capacity-safe Student
  self-registration, participant review and attendance, venue/budget approval, teams, expenses,
  achievements, verifiable certificates, and activity points. The complete Activity Coordinator
  and Student journeys are source-backed and interactively validated locally. Active participation
  certificates now render from the existing serial and attended participation sources.
- Reporting: management-only source aggregates, inclusive date and academic-year filters,
  calculation freshness and definitions, source drill-down, actor-owned saved views, audited CSV
  exports, recurring delivery configuration, and permission-scoped operational dashboards.
- Alembic head is `e2b7c4d91a60`; local migration drift checks pass and the production API exposes
  219 OpenAPI paths.
- The frontend uses real APIs for every listed operational route. Academic master configuration is
  comprehensive; role workspaces expose only permission-authorized navigation, source records,
  and actions.
- Access, Academic Masters, admissions, Students, delivery, attendance, communication, event, and
  printable-document workflows use normal page flow. Active screens hide their parent list and do
  not render controls behind a translucent layer.

The college frontend authenticates the two seeded College Administrators through the production
tenant API, retains access credentials in memory, stores refresh credentials only for the browser
tab, rotates them during page restoration, and revokes the persisted session on sign-out. Identity
Closure 1 is locally implemented: invitations, membership lifecycle, role/permission/scope editing,
password change, session and forced-logout controls, RLS-safe tenant switching, and the isolated
Platform Administrator tenant-lifecycle workspace are source-backed frontend behaviors.

## Important Current Limitations

- The visible credentials and seeded records are approved synthetic demo behavior and must not be
  reused as production secrets or created without explicit `--seed-demo` onboarding.
- Invitation delivery currently exposes the one-time token to an authorized administrator until a
  provider-independent delivery worker is implemented.
- Applicant self-service and shared private Applicant/Student uploads are implemented locally with
  membership binding, magic-byte validation, tenant metadata, authenticated downloads, forced RLS,
  and no-store authorization-aware cache controls. The filesystem provider is development-only;
  production object storage, retention execution, and malware scanning remain release work.
- Employee attendance remains part of HR rather than the student class-register workflow.
- External communication and payment providers, binary uploads, scheduled-report execution,
  statutory report templates, and the deferred formal test suite remain release work.
  Permission-scoped report CSV export is implemented locally.
- Full-stack AWS demo automation remains preparation work: backend artifact installation, isolated
  systemd service, `/api` proxying, remote migration/onboarding, private media persistence, backup,
  rollback, and non-destructive public verification must be implemented and reviewed before use.

## Deferred Testing Decision

Broad unit-test coverage remains deferred by project decision. Current executable validation includes:

- Alembic upgrade and drift checks against local PostgreSQL.
- Backend Ruff checks and production-app import/OpenAPI checks.
- Frontend TypeScript production build and Oxlint.
- Interactive Playwright route, mutation, retained-feedback, two-tenant isolation, API-failure, and
  390px mobile-overflow checks without persisted UI test files.
- Idempotent two-tenant demo onboarding runs.

Formal unit, API, permission, RLS, and persisted browser suites still need to be written before a
production release.

## Next Review Gate

Follow the one-by-one queue in the authoritative implementation plan. Slice 3, Academic and
Delivery Hardening, passed locally. Its first increment passed on 16 September 2026:
Program-to-Department editing succeeds for an unused Program, returns a controlled 409 after any
direct structural or operational dependency exists, and rejects cross-tenant Department references
with 422. Subject-to-Department editing now follows the same boundary for curriculum mappings,
delivery offerings, assessment schemes, and published-result lines. Batch-to-Program editing now
blocks changes after Section, Student enrollment/progression/lifecycle, or role-scope dependencies
exist. Section-to-Batch editing blocks changes after subject-offering, Student placement/lifecycle,
or role-scope dependencies exist. Term-to-Academic-Year, Room-to-Campus, and
Curriculum-to-Program/Regulation editing now block changes after their delivery, calendar,
examination, or subject-mapping dependencies exist. Curriculum Subject and Calendar Event parent
editing provide tenant-safe mapping changes, consistent Academic Year/Term selection, and explicit
optional-Term clearing. Academic-master dependency editing, scoped HOD controls, and the initial
Class Advisor workspace are complete. Timetable publication/versioning is complete through
immutable scoped snapshots at revision `c91e4a7d2b60`. The Student Learning materials route joins
scoped resources to readable Subject, Section, Term, and Faculty context. Slice 3 is complete.
Slice 4, Operational Documents, is complete locally. Payment receipts, hall tickets, grade cards,
transcripts, activity participation certificates, and issued Student-request certificates derive
from authoritative versioned or immutable records, carry tenant branding and verification
references, and enforce Student and tenant scope. The next feature is Slice 5, Providers and
Background Jobs. Its ordered design and validation gate are recorded in
`docs/modules/19-providers-background-jobs.md`.

The later release gate must cover automated unit, API, permission, RLS, migration, concurrency,
and browser suites together with fresh-database migration, onboarding idempotency, accessibility,
mobile interaction, external-provider failure behavior, backup/restore, monitoring, and production
secret/configuration review.
