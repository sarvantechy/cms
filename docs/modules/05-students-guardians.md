# Students and Guardians

**Status:** Student and guardian operations plus the Student Lifecycle Expansion are implemented and interactively validated locally.

## Purpose

Maintain authoritative student identity, guardian links, enrollment, academic placement, and lifecycle history.

## Roles

- College Administrator and authorized staff: manage student records.
- Class Advisor and HOD: view scoped students.
- Student: view own record.
- Parent/Guardian: view actively linked students only.

## Workflow

1. Create from accepted applicant or controlled direct entry.
2. Assign registration and roll numbers.
3. Link guardians and emergency contacts.
4. Enroll into program, batch, section, and subjects.
5. Record status changes, progression, transfer, exit, and readmission.

## Core Rules

- Person identity is entered once and reused.
- Status and placement changes are effective-dated history.
- Parent access requires an active explicit link.

## Data

Person, Student, Guardian, StudentGuardian, Enrollment, SectionPlacement, SubjectRegistration, StudentStatusHistory, and StudentDocument.

## Current UI Behavior

`/portal/students` provides source-backed search, direct student entry, and a composed student
profile. Administrators can edit canonical identity and registration details, create and link a
guardian or emergency contact, add an academic-year enrollment with programme/batch/section
placement, and perform only allowed lifecycle transitions. The profile displays guardian,
enrollment, placement, and append-only status history without direct database access.

Student creation, profile detail, lifecycle operations, and printable certificate views use opaque
workspace screens that replace the Student list while active. This avoids hidden background
controls and gives mobile forms the full content width.

## Lifecycle Expansion

Tenant-owned student documents, subject registrations, progressions, transfer/readmission
requests, and certificate requests are implemented through Alembic revision `d684eaa982fa`.
Each table has tenant-safe references, forced RLS, restricted runtime grants, protected service
transitions, and same-transaction audit behavior. Scoped Student and Guardian portals resolve own
or explicitly linked students. Persisted unit/API/RLS/browser suites remain deferred by project
decision.

Student documents share the tenant-owned private-media model introduced by Slice 2 through
revision `f8cd51ae2d03`. Authorized staff can upload PDF/JPEG/PNG files up to 5 MiB, and Student-own
or permitted staff scopes can download the content without receiving provider credentials or
object keys. Downloads disable browser caching and vary by bearer authorization. The local
filesystem provider is for development; production object storage and retention execution remain
release configuration work.

Issued certificate requests now expose a source-derived printable document using the durable
`issued_reference`, review timestamp, tenant branding, and canonical Student identity. The Student
portal includes a permission-filtered My records route and shows Print certificate only for issued
requests; requested and approved records remain non-printable. Linked Student and tenant isolation
are enforced by the existing service scope boundary.

## Slice 1 Completion

Student Lifecycle Expansion was completed and locally validated on 30 August 2026:

- [x] Approve document categories, subject-registration states, progression outcomes,
  transfer/readmission transitions, certificate types, permissions, and record scopes.
- [x] Add tenant-safe PostgreSQL tables, composite foreign keys, indexes, uniqueness constraints,
  forced RLS policies, and restricted runtime grants through one forward-safe Alembic revision.
- [x] Add documented ORM models, Pydantic contracts, domain services, explicit transitions,
  protected routes, and same-transaction audit events.
- [x] Extend idempotent two-tenant demo onboarding with representative lifecycle records.
- [x] Add administrator controls and authorized Student/Guardian read outcomes with explicit
  loading, empty, validation, unauthorized, and retry states.
- [x] Run focused Ruff, migration upgrade/drift, production OpenAPI, TypeScript build, and
  interactive desktop/mobile Playwright checks against local PostgreSQL.
- [x] Reconcile this module, the implementation status, module catalogue, and authoritative plan
  before starting Applicant Self-Service and Uploads.

The slice passes only when each operation works without direct SQL, history survives reload, and
own-record, linked-student, department, tenant, and cross-tenant boundaries are verified.

## Local Validation

- The composed detail endpoint returns the canonical student, guardian links, enrollment placement,
  and status history under the existing forced-RLS runtime.
- Student mutation responses are serialized before commit so transaction-local tenant context is
  never weakened for post-commit ORM reloads.
- Interactive Playwright opened the seeded profile and showed one primary guardian, one active
  B.Sc. Computer Science enrollment in Section A, and its prospective-to-active history.
- The edit form restored persisted identity values; focused Oxlint and the production frontend
  build pass.
- Document verification, subject completion, progression apply, transfer completion, certificate
  approval/issuance, and readmission completion were exercised through the administrator UI.
- Progression completed its source enrollment and created an active target enrollment. Transfer
  marked its source enrollment transferred and created its target enrollment. Readmission
  cancelled the supplied enrollment, restored the Student to active, created the new active
  enrollment, and appended status history; all outcomes survived profile reload.
- Student-own and Guardian-linked reads returned only authorized lifecycle outcomes. Cross-tenant
  Arts/Law records remained isolated under the restricted runtime role.
- Focused Ruff, Alembic head/drift, production OpenAPI, and frontend build checks pass. The
  production app exposes 219 paths, and repeated two-tenant demo onboarding remains idempotent.
- Interactive validation at 390 px reports matching 390 px client and document widths with no
  horizontal overflow.
- On 17 September 2026, one approved Bonafide request was completed through its normal issuance
  transition with synthetic reference `CERT-INDUS-2026-0001`. Administrator and linked Student
  document reads returned `200`; unrelated Student and cross-tenant reads returned `404`; the
  responsive and print-isolated document rendered through the Student My records page.

## Slice 2 Validation

On 30 August 2026, interactive Playwright uploaded a media-backed Residence proof through the
administrator Student profile, displayed its pending state and Download action, and confirmed both
Student-own and Administrator content access. Cross-tenant media access returns 404. Repeated
two-tenant demo onboarding preserved the uploaded document. Focused Ruff, Alembic head/drift,
production OpenAPI, and frontend build checks pass at revision `f8cd51ae2d03` and 207 paths.

## Slice 3 Role Scoping

Department, program, batch, section, and subject-offering scopes now constrain Student list,
detail, lifecycle, Person selector, and attendance-summary access on the server. HOD and Class
Advisor portal journeys each returned one assigned active Student and rejected direct access to an
unassigned Student with 404. Institution-scoped Administrators retain complete tenant visibility.
The Class Advisor demo seed uses a dedicated active class-enrolled Student so repeated onboarding
does not rewrite previously validated Student lifecycle history.

## Acceptance Criteria

- Applicant conversion creates one student without re-entry.
- Department and linked-student scopes cannot infer unrelated records.
- Historical registrations and statuses remain reproducible.
