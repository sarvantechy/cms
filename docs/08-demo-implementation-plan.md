# Demo Implementation Plan

## Delivery Rule

The demo will be implemented one vertical slice at a time. A slice includes its PostgreSQL migration, backend model and rules, API, frontend screens, permission checks, seed data, and focused tests. We will review each slice before starting the next one.

No production deployment is included unless it is requested separately after the local demo is accepted.

## Technical Baseline

The implementation will follow the proven structure of the Himalayan Access application while remaining a separate codebase.

### Frontend

- React 19 and TypeScript
- Vite
- React Router for URL-based pages and refresh-safe navigation
- Axios API client in one shared module
- Lucide icons
- CSS variables and responsive domain-specific styles
- Playwright for critical browser journeys

The CMS will reuse the interaction language, not copy business-specific components. The application shell retains grouped role-aware navigation, operational dashboards, tables, profile context, responsive behavior, and selectable themes. Create, edit, detail, and document workflows use opaque in-workspace screens in normal page flow; portal popups, native dialogs, and translucent overlays are not used.

### Backend

- Python and FastAPI
- SQLAlchemy 2.x
- PostgreSQL
- Alembic migrations
- Pydantic request and response schemas
- JWT-based authenticated sessions for the demo
- Domain-organized routers and services
- Pytest for service, API, permission, and tenant-isolation tests

### Initial Project Shape

```text
4by4-cms/
  backend/
    alembic/
    app/
      domains/
        tenancy/
        identity/
        academics/
        people/
        attendance/
        finance/
        communications/
        reporting/
      commands/
      db/
      production_main.py
      security_context.py
    tests/
  web/
    e2e/
    src/
      components/
      features/
      api.ts
      types.ts
      App.tsx
      App.css
  docs/
```

## Non-Negotiable Multi-Tenant Foundation

The demo must be structurally safe enough to grow into the full product.

- Every college-owned record has `tenant_id`.
- Authentication resolves an active tenant membership.
- `ActorContext` contains account, tenant, membership, and permissions.
- Protected routes use `require_actor()` or `require_permission()`.
- The backend derives tenant identity; clients do not choose arbitrary tenant IDs.
- PostgreSQL Row-Level Security is forced on tenant-owned tables.
- Runtime database sessions set `app.tenant_id` transaction-locally.
- Unique constraints include tenant scope.
- Tenant-safe foreign keys prevent cross-college relationships.
- Seed commands are idempotent and safe to rerun locally.
- Automated tests deliberately attempt cross-tenant reads and writes.

## Demo Roles and Initial Permissions

```text
tenant.manage
membership.manage
academics.read
academics.manage
student.read
student.manage
faculty.read
faculty.manage
timetable.read
timetable.manage
attendance.read
attendance.write
fees.read
fees.collect
notice.read
notice.manage
dashboard.read
audit.read
```

Role mapping:

| Role | Permission summary |
| --- | --- |
| Platform administrator | Tenant directory and lifecycle only |
| College administrator | All tenant permissions |
| Faculty | Academic assignments, timetable, assigned attendance, notices, own dashboard |
| Accountant | Student fee accounts, collections, receipts, notices, finance dashboard |
| Student | Own profile, timetable, attendance, fees, receipts, notices, and dashboard |

Backend record scope remains mandatory even when a role has a general read permission.

## Increment 1: Repository and Application Shell

Deliver:

- Backend and frontend project scaffolding
- Local PostgreSQL Docker service
- Environment examples without secrets
- Health endpoint
- Frontend shell with sidebar, mobile drawer, top context, theme variables, and routing
- Shared loading, empty, error, confirmation, table, pagination, and form patterns
- Basic build, lint, backend test, and Playwright commands

Acceptance check:

- The backend health endpoint responds.
- The frontend loads on desktop and mobile.
- All placeholder pages are reachable by stable URLs.
- The shell matches the Himalayan Access interaction pattern with CMS branding.

Review gate: approve navigation, density, typography, theme direction, and mobile shell before domain screens are built.

### Increment 1A: Public Website and Role Demonstration

Deliver:

- Public INDUS Arts & Science college homepage
- Admissions, academics, events, campus life, location, and contact sections
- Demo login page with clearly labeled synthetic credentials
- Administrator, Student, Parent, Faculty, HOD, and Event Coordinator workspaces
- Role-specific navigation, dashboard metrics, action queues, and sample module rows

Important limitation:

- Authentication and records remain frontend demo data until Increment 2.
- Sample login details are visible by design for stakeholder demonstrations only.
- The demo does not claim real authorization or tenant isolation until PostgreSQL-backed memberships and RLS are implemented.

## Increment 2: Tenancy, Authentication, and Access

Deliver:

- Tenant, campus, account, membership, role, permission, and assignment tables
- Forced Row-Level Security
- Login and session refresh
- Actor-context middleware
- Permission dependencies
- Active-tenant switching for multi-membership users
- Role-aware navigation
- Audit-event foundation
- Idempotent seed command for both demo tenants and users

Acceptance check:

- Each role can sign in.
- A user sees only permitted navigation.
- A multi-tenant user can switch only between their memberships.
- Tenant branding updates after switching.
- Cross-tenant API attempts return no data or an authorization error.

Review gate: demonstrate tenant A, tenant B, role restrictions, and a deliberate cross-tenant test.

## Increment 3: Academic Setup

Deliver:

- Academic years, terms, departments, programs, batches, sections, subjects, rooms, and subject offerings
- Faculty academic assignments
- Administrator list and detail screens
- Filters by academic year, department, program, and section
- Arts and science and law college seed structures

Acceptance check:

- Each tenant shows only its own academic vocabulary and records.
- Administrators can inspect the hierarchy from department to subject offering.
- Faculty assignments connect a faculty member, subject, and section.

Review gate: approve whether both college structures accurately represent the intended demo customers.

## Increment 4: Students and Faculty

Deliver:

- Person, student, guardian, enrollment, faculty, and faculty-assignment records
- Student matrix with search, filters, and pagination
- Student profile with academic, attendance, and fee tabs prepared for later increments
- Simplified student intake and profile edit
- Faculty matrix, profile, assignment summary, and timetable placeholder
- Synthetic people seed data for both tenants

Acceptance check:

- An administrator can create and find a student.
- Registration numbers are unique within a tenant.
- Student and faculty records never appear in the other tenant.
- Faculty and student users can access only their own permitted workspace.

Review gate: approve the student matrix, profile layout, intake form, and faculty assignment view.

## Increment 5: Timetable and Attendance

Deliver:

- Timetable entries and class sessions
- Weekly views for section, faculty, and student
- Seeded representative timetable for both tenants
- Faculty attendance register for assigned sessions
- Present, absent, late, and on-duty statuses
- Duplicate-submission protection
- Student overall and subject-wise summaries
- Administrator attendance dashboard and shortage list

Attendance formula:

$$
\text{Attendance percentage} =
\frac{\text{attended sessions}}{\text{eligible conducted sessions}} \times 100
$$

The exact treatment of late and on-duty statuses will be configurable later. For the demo, both count as attended, while cancelled classes are excluded.

Acceptance check:

- Faculty sees only assigned sessions.
- Recording attendance updates the student summary.
- Repeating the same submission does not create duplicate rows.
- Dashboard totals reconcile with class-session records.

Review gate: run the faculty-to-student attendance journey on desktop and mobile.

## Increment 6: Student Fees and Receipts

Deliver:

- Fee heads, fee plans, invoices, invoice lines, concessions, payments, allocations, and receipts
- Seeded invoices with paid, partially paid, concession, and unpaid examples
- Accountant pending-fee matrix
- Payment form for offline collection
- Unique tenant-scoped receipt numbering
- Printable receipt page
- Student fee ledger and dashboard summary
- Collection and pending totals on administrator and accountant dashboards

Balance formula:

$$
\text{Balance} = \text{invoice charges} - \text{approved concessions} - \text{allocated payments}
$$

Acceptance check:

- An accountant can collect against an outstanding invoice.
- The receipt, ledger, balance, and dashboards update together.
- Overpayment and duplicate submission are rejected.
- Students see only their own fee records.

Review gate: demonstrate partial payment, full payment, receipt print view, and updated pending totals.

## Increment 7: Notices and Complete Dashboards

Deliver:

- Notice drafts, target audiences, publish and expiry dates
- College-wide, role, department, program, and section targeting
- Administrator compose and publish flow
- Relevant notices on faculty, accountant, and student dashboards
- Completed role dashboards using database aggregates
- Quick links and recent activity

Acceptance check:

- A targeted notice appears only for intended users in the same tenant.
- Expired and draft notices are hidden from normal recipients.
- Dashboard cards drill into filtered source lists where practical.
- No dashboard count is hard-coded.

Review gate: complete both tenant walkthroughs and compare their distinct data and branding.

## Increment 8: Demo Hardening

Deliver:

- Full focused backend test suite
- Cross-tenant RLS and API tests
- Role-permission tests
- Playwright journeys for administrator, faculty, accountant, student, and tenant switching
- Desktop and mobile screenshot review
- Accessibility checks for labels, focus, contrast, and keyboard use
- Seed reset command and documented local startup
- Loading, empty, failure, retry, unauthorized, and not-found states
- Final demo script and known-limitations page

Acceptance check:

- A fresh local environment can migrate and seed predictably.
- All focused tests pass.
- The scripted demo can be repeated without manual database repair.
- The user interface remains usable at representative desktop and mobile widths.

Review gate: stakeholder demo and written selection of the next module.

## Seed Data Strategy

Create one explicit command, for example:

```text
python -m app.commands.seed_demo
```

The command will:

- Create or update both demo tenants by stable keys.
- Create roles and permissions idempotently.
- Create synthetic users and tenant memberships.
- Create academic master data before dependent records.
- Create students, faculty, timetable, attendance, invoices, payments, and notices.
- Use a demo password supplied through an environment variable.
- Never store a real password or customer data in source control.
- Be disabled or guarded in production environments.

## Demo Walkthrough

### Journey A: Arts and Science College

1. Sign in as the college administrator.
2. Confirm INDUS ARTS & SCIENCE INTERNATIONAL COLLEGE branding and dashboard totals.
3. Open the B.Sc. Computer Science section and inspect its students and subjects.
4. Open one student and review enrollment, attendance, and fee summary.
5. Sign in as a Computer Science faculty member and record attendance for Programming Fundamentals.
6. Sign in as the student and confirm the updated attendance percentage.
7. Sign in as the accountant, collect a partial fee, and open the printable receipt.
8. Return as the student and confirm the reduced balance and receipt.
9. Publish a section notice and verify it appears for the intended student.

### Journey B: Law College

1. Switch or sign in to INDUS LAW COLLEGE.
2. Confirm law programs, subjects, branding, and dashboard values replace the arts and science data.
3. Open the LL.B. section and inspect Legal Methods attendance.
4. Record attendance as the assigned law faculty member.
5. Review a law student's fee ledger and notices.
6. Attempt a known Arts and Science record URL and confirm access is denied or the record is not found.

## Documentation During Implementation

Documentation will be updated with each increment rather than postponed until the end.

For every completed increment:

- Update this plan with actual status and deviations.
- Add or update a module document describing implemented behavior.
- Update the database relationship document when schema changes.
- Update the user guide for visible workflows.
- Record setup, migration, seed, test, and run commands.
- Mark deferred behavior clearly; do not describe placeholders as complete.

Suggested implementation documents as work begins:

```text
docs/implementation-status.md
docs/database-relationships.md
docs/user-guide.md
docs/modules/01-platform-access.md
docs/modules/02-academic-setup.md
docs/modules/03-students-faculty.md
docs/modules/04-timetable-attendance.md
docs/modules/05-fees-receipts.md
docs/modules/06-notices-dashboards.md
```

## Decision After the Demo

Stakeholder feedback should select the next module based on operational value. Likely choices are:

1. Full admissions workflow
2. Examinations and results
3. Parent portal and notifications
4. Library
5. Hostel and transport

Only one major module should enter implementation at a time unless dependencies require a paired delivery.
