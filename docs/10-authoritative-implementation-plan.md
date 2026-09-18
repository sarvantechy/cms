# Authoritative College Management System Implementation Plan

## Purpose

This document is the implementation source of truth for turning the current visual demo into a PostgreSQL-backed, multi-tenant college management system.

The six accounts visible in the demo are interface personas only. They do not limit the production role model. Roles are configurable permission bundles, and access is further restricted by tenant, campus, department, academic assignment, linked student, or ownership scope.

## Delivery Rules

- Implement one vertical module slice at a time.
- Every tenant-owned table carries `tenant_id` and is protected by forced PostgreSQL Row-Level Security.
- Derive tenant, membership, permissions, and scopes from authenticated `ActorContext`.
- Never authorize an operation from a client-supplied tenant identifier or frontend role check.
- Use Alembic as the only production schema-management mechanism.
- Add docstrings to every function and class.
- Add audit events in the same transaction as sensitive mutations.
- Keep seed and tenant-onboarding commands idempotent.
- Complete implementation first and add the focused unit-test suite at the end of each module slice.
- A module is not complete until its PostgreSQL, API, UI, authorization, audit, seed, documentation, and tests agree.

## Role Model

Access is evaluated as:

$$
\text{Access} = \text{Permissions} + \text{Tenant membership} + \text{Assigned scopes} + \text{Record rules}
$$

One account can have multiple roles in one college and different roles in another college.

### Baseline Roles

| Area | Roles |
| --- | --- |
| Platform | Platform Administrator |
| College leadership | College Administrator, Principal/Management |
| Admissions | Admission Officer |
| Academics | Head of Department, Faculty, Class Advisor |
| Examinations | Examination Controller |
| Finance | Accountant/Cashier |
| Employees | HR/Payroll Officer |
| Campus services | Librarian, Hostel Warden, Transport Manager |
| Career and activities | Placement Officer, Activity Coordinator |
| Portals | Student, Parent/Guardian |

Applicant and Alumni are lifecycle portal profiles rather than privileged staff roles. Colleges may create custom roles from the permission catalogue without requiring code changes.

### Scope Types

- Institution
- Campus
- Department
- Program
- Batch or section
- Subject offering or assigned class
- Linked student
- Own person or employee record

### Separation of Duties

| Workflow | Separate authorities |
| --- | --- |
| Admission | Verify, approve, convert applicant |
| Attendance correction | Request, approve correction |
| Marks | Enter, verify, publish |
| Fee concession | Propose, approve |
| Refund | Request, approve |
| Payroll | Prepare, approve |
| Published-result change | Reopen, modify, republish |

A small college may grant these authorities to one person, but each action must record the role and permission used.

## Implementation Increments

### Increment 0: Product Decisions

Confirm academic patterns, numbering formats, admission and quota rules, attendance treatment, grading, promotion, payment providers, communication providers, retention, reports, and approval levels.

**Gate:** Approved workflow glossary, role-permission matrix, first-release boundary, and initial relationships.

### Increment 1: Tenancy, Identity, and Security

Deliver tenants, campuses, accounts, memberships, roles, permissions, membership role assignments, scoped assignments, JWT sessions, password lifecycle, tenant switching, `ActorContext`, transaction-local tenant context, forced RLS, audit events, login history, and idempotent two-college seeds.

Initially activate Platform Administrator and College Administrator. Seed the complete permission catalogue so later roles can be introduced without changing the authorization architecture.

**Gate:** Automated PostgreSQL checks prove that neither INDUS college can read, mutate, reference, export, or infer the other college's records.

### Increment 2: Institution and Academic Masters

Deliver college settings, campuses, academic years, terms, departments, programs, regulation and curriculum versions, subjects, credits, batches, sections, rooms, calendars, and numbering formats.

Activate Principal/Management and Head of Department scopes.

**Gate:** A college administrator can configure one complete academic year without database access.

### Increment 3: Admissions

Deliver enquiries, applicant accounts, configurable applications, documents, verification, intake campaigns, seats, quota and merit processing, selection and waiting lists, offers, acceptance, rejection, cancellation, initial invoices, and transactional applicant conversion.

Activate Admission Officer and applicant portal access.

**Gate:** An application reaches an accepted offer through auditable state transitions and controlled approvals.

### Increment 4: Students and Guardians

Deliver authoritative people, student profiles, guardians, emergency contacts, documents, registration and roll numbers, enrollment, section placement, subject registration, statuses, status history, transfer, readmission, progression preparation, and basic certificate requests.

Activate Student, Parent/Guardian, and Class Advisor access.

**Gate:** Accepted applicant data becomes one student identity without re-entry, and parents see only actively linked students.

### Increment 5: Faculty and Academic Delivery

Deliver faculty profiles, employment references, department postings, subject offerings, faculty allocation, workload, student subject registration, timetable conflict detection, substitutions, lesson plans, learning materials, and syllabus progress.

Activate Faculty and complete Head of Department and Class Advisor academic scopes.

**Gate:** Every scheduled period links the correct term, section, subject, faculty member, student group, and room.

### Increment 6: Attendance and Leave

Deliver timetable-generated class sessions, period-wise student attendance, submission and locking, corrections and approvals, faculty attendance, basic leave, summaries, shortage thresholds, exam eligibility inputs, and parent notifications.

**Gate:** Every percentage is traceable to eligible scheduled sessions and approved corrections.

### Increment 7: Fees and Payments

Deliver fee heads, plans, invoices, instalments, concessions, scholarships, payments, allocations, receipts, cashier closing, reversals, refunds, gateway idempotency, reconciliation, ledgers, pending balances, and collection reports.

Activate Accountant/Cashier and finance approval permissions.

**Gate:** Every balance reconciles to immutable source transactions; financial mistakes are reversed rather than deleted.

### Increment 8: Examinations and Results

Deliver assessment schemes, exam sessions, schedules, eligibility, registration, hall tickets, seating, invigilation, attendance, marks, verification, locking, moderation, grading, GPA/CGPA, results, ranks, publication, revaluation, supplementary examinations, grade cards, and transcripts.

Activate Examination Controller.

**Gate:** Results are reproducible from versioned rules and remain unavailable to students until controlled publication.

### Increment 9: Communication and Portals

Deliver targeted notices, circulars, announcements, templates, approvals, scheduling, in-app delivery, email/SMS integration, retry history, acknowledgements, preferences, and role-specific portals backed by source modules.

**Gate:** Messages reach only their intended tenant and academic or role audience.

### Increment 10: Events and Activities

Deliver events, clubs, NSS/NCC, cultural and sports activities, registration, selection, teams, attendance, venue and budget approval, participation, achievements, verifiable certificates, activity points, and reports.

Activate Activity Coordinator, replacing the demo-only Event Coordinator naming where required by college policy.

**Gate:** Coordinators manage event records without unrelated academic or financial authority.

### Increment 11: Core Dashboards and Reports

Deliver source-derived dashboards and drill-down reports for leadership, admissions, academics, students, attendance, finance, examinations, faculty, departments, events, and communication. Include freshness indicators and calculation definitions.

**Gate:** Every total reconciles with its operational records and respects tenant and record scopes.

Increments 1 through 11 form the recommended first commercial release.

### Increment 12: Library

Deliver cataloguing, copies, barcodes, shelves, circulation, renewals, reservations, fines, losses, stock verification, acquisitions, and reports. Activate Librarian.

### Increment 13: Hostel and Transport

Deliver buildings, rooms, beds, allocations, attendance, visitors, incidents, mess plans, vehicles, routes, stops, drivers, capacity, effective-dated allocations, and linked fees. Activate Hostel Warden and Transport Manager.

### Increment 14: Placement

Deliver companies, opportunities, eligibility, student consent, drives, tests, interviews, outcomes, offers, and reports. Activate Placement Officer.

### Increment 15: HR, Leave, and Payroll

Deliver recruitment, onboarding, employee documents, probation, transfers, exits, leave policies and balances, salary structures, payroll runs, deductions, payslips, statutory records, appraisals, and confidential access boundaries. Activate HR/Payroll Officer.

### Increment 16: Advanced Finance and Integrations

Deliver optional general ledger, expenses, vendors, procurement, bank reconciliation, advanced analytics, scheduled reports, accreditation and university exports, biometric reconciliation, GPS, learning-platform links, and institution-specific integrations.

## Partial-Implementation Closure Plan

Complete the following slices before starting Library, Hostel, Transport, Placement, HR/Payroll,
Advanced Finance, or other mostly missing modules. Each slice extends the existing PostgreSQL and
forced-RLS production path; it must not introduce a parallel demo runtime.

### Closure 1: Identity Administration

**Status:** Implemented locally and interactively validated on 2026-08-29.

- Add College Administrator screens for invitations, membership lifecycle, role/scope assignment,
  password change, session review and revocation, forced member logout, and tenant switching.
- Add a separate Platform Administrator login and tenant lifecycle workspace.
- Add any missing role, permission, assignment, and invitation-list APIs needed by those screens.
- Gate: an administrator can onboard, scope, suspend, reactivate, and force-sign-out a member
  without database access, while self-protection and cross-tenant concealment remain enforced.

### Closure 2: Admissions Operations

**Status:** Implemented locally and interactively validated on 2026-08-29.

- Add campaign, enquiry, applicant, application, document-verification, seat-pool, selection,
  offer issuance/acceptance, cancellation, and conversion workspaces.
- Surface transition history, capacity outcomes, validation errors, and idempotent conversion state.
- Gate: staff can complete the accepted-application-to-student journey entirely through the UI
  without an invalid direct application transition or duplicate seat/student record.

### Closure 3: Student and Guardian Operations

**Partial-surface status:** Existing student-domain capabilities are fully surfaced and
interactively validated on 2026-08-29. New document, registration, progression, transfer,
readmission, certificate, and role-portal domains remain in the entirely missing phase.

- Add searchable student lists, profile/detail editing, guardians and emergency contacts,
  documents, enrollments, placements, subject registrations, status history, transfers,
  readmission, progression preparation, and certificate requests.
- Gate: one authoritative student identity and its history can be maintained without direct SQL.

### Closure 4: Faculty and Academic Delivery

**Status:** College Administrator operations plus scoped Faculty, HOD, and Student delivery views
are implemented and interactively validated locally. A distinct Class Advisor demo workspace is
not part of the current eight-role portal set.

- Add faculty profiles/postings, offerings, allocations, timetable builder, substitutions, lesson
  plans, learning materials, syllabus progress, workload, and conflict-resolution feedback.
- Gate: administrators can build and publish a conflict-free teaching schedule through the UI.

### Closure 5: Attendance and Leave

**Status:** Student attendance, register locking, corrections, person leave, source-derived
summaries, shortage, and exam-eligibility inputs are implemented locally for College Administrator.
Role portals and notification delivery history remain in Closure 8; employee attendance remains
in Increment 15.

- Add timetable-derived session generation, bulk attendance entry, submission and locking,
  correction creation/review, faculty attendance, leave, traceable summaries, shortage and exam
  eligibility views, and notification history.
- Gate: every displayed percentage traces to eligible sessions and approved corrections.

### Closure 6: Fees and Payments

**Status:** College Administrator fee setup, invoicing, collection, immutable allocations,
receipts, reversals, concession/refund approvals, cashier reconciliation, gateway comparisons, and
source-derived student ledgers are implemented and interactively validated locally.

- Add fee heads/plans, invoices, concessions, collection desk, allocations, receipts, reversals,
  refund approvals, cashier closing, gateway idempotency/reconciliation, and student-ledger UI.
- Gate: every displayed balance reconciles to immutable source transactions and compensating
  corrections; no financial source record is silently overwritten or deleted.

### Closure 7: Examinations and Results

**Status:** Controller configuration, scheduling, candidate eligibility, capacity-aware seating,
invigilation, marks lifecycle, reviewed adjustments, versioned grading, reproducible publication,
GPA/CGPA, detailed result snapshots, hall-ticket sources, and transcript APIs/UI are implemented
and interactively validated locally.

- Add scheme/session/schedule setup, eligibility, registration, hall tickets, rooms, seating,
  invigilation, marks entry, verification, locking, moderation, publication, GPA/CGPA, ranking,
  revaluation, supplementary exams, grade cards, transcripts, and controlled republishing.
- Gate: a configured exam reaches reproducible publication entirely through permission-separated
  UI actions, and unpublished marks cannot be inferred.

### Closure 8: Communications and Role Portals

**Status:** Implemented and interactively validated locally. External email/SMS provider adapters
and formal automated coverage remain release work.

- Add templates, approval, audience preview, scheduling, acknowledgement, preferences, delivery
  retry history, and provider-independent email/SMS job interfaces.
- Add permission-scoped Student, Parent/Guardian, Faculty, HOD, Accountant, Examination Controller,
  Admission Officer, and Activity Coordinator portal navigation and source-backed views.
- Gate: every role sees only authorized records and failed delivery never becomes silent success.

### Closure 9: Events and Activities

**Status:** Implemented and interactively validated locally on 29 August 2026. Formal automated
coverage and cross-module event reports remain release work.

- Add clubs, event editing/publication, eligibility, student registration, selection, teams,
  participant management, venue/budget approval, expenses, outcomes, evidence, verifiable
  certificates, activity points, and reports.
- Gate: capacity and eligibility survive concurrent registration, and certificates resolve to
  approved immutable participation outcomes.

### Closure 10: Dashboards and Reports

**Status:** Implemented and interactively validated locally on 29 August 2026. Background provider
delivery, college-specific statutory templates, and formal automated coverage remain release work.

- Add date and academic filters, calculation definitions, freshness timestamps, source drill-down,
  saved filters, permission-scoped exports, scheduled delivery, and configured statutory reports.
- Gate: every total reconciles to source records and export scope matches on-screen authorization.

### Closure Validation and Documentation

- Maintain docstrings on every function and class and update the relevant module document after
  each closure slice.
- Continue focused build, lint, migration-drift, PostgreSQL, and interactive browser checks while
  implementation is in progress.
- Add the deferred unit, API, permission, RLS, migration, and persisted Playwright suites after the
  closure implementation surface is complete, before any production-release claim.

## Standard Module Delivery Sequence

1. Approve workflow states, permissions, scopes, and acceptance criteria.
2. Design tenant-safe tables and relationships.
3. Add a forward-safe Alembic migration and forced RLS policies.
4. Add ORM models, schemas, repositories, and services.
5. Add protected, versioned API routes.
6. Add audit, document, notification, and idempotency behavior where relevant.
7. Connect the shared frontend API client and typed contracts.
8. Implement loading, empty, failure, retry, unauthorized, and populated states. Use opaque
  in-workspace screens for create, edit, detail, and document workflows; do not overlay portal
  content with popup dialogs.
9. Add synthetic data for both INDUS colleges.
10. Update module and implementation-status documentation.
11. Add unit, API, RLS, permission, and Playwright tests at the end of the slice.
12. Run the review gate before starting another module.

## Definition of Done

A module is complete only when business transitions are explicit, database migrations are safe, tenant and permission barriers are enforced in PostgreSQL and the backend, sensitive operations are audited, calculations reconcile to source transactions, the UI handles all operational states, documentation is current, and focused tests cover successful, invalid, unauthorized, and cross-tenant behavior.

## Current Delivery Status

Increments 1 through 10 have local PostgreSQL-backed implementation coverage for their current
data, services, protected APIs, forced RLS, audit, two-tenant seed, and permission-scoped frontend
paths. The current Alembic head is `e2b7c4d91a60`, and the production FastAPI application exposes
219 OpenAPI paths.

Academic Masters covers all 15 current master groups. Admissions, Student, Faculty and Delivery,
Attendance and Leave, Fees and Payments, Examinations and Results, Communications, role portals,
and Events and Activities now expose their implemented workflows through source-backed local UI.
Identity administration includes college and platform workspaces. All planned implementation
closures are now represented locally; external providers, selected uploads, statutory report
configuration, and the formal automated test suites remain release work.

Interactive browser validation has covered the completed operational journeys, permission-derived
portals, record scoping, tenant isolation, retained success feedback, and responsive operation at
390 px. The Events journey additionally covered approval, Student self-registration, attendance,
team membership, budget-bounded expense approval, certificate verification, points, and
achievement outcomes. This is local validation only and is not a deployment claim. Because
provider-backed delivery and the deferred formal suites remain pending, the product does not yet
satisfy the full commercial Definition of Done above.

## Remaining Development Execution Plan

Complete the remaining work one independently reviewable vertical slice at a time. Do not begin
the next slice until the current slice has matching PostgreSQL schema, forced RLS, protected API,
permission-scoped UI, audit behavior, two-tenant seed behavior, interactive validation, and
updated module documentation. Formal automated suites remain grouped in Slice 8 by project
decision, but every implementation slice still requires focused executable checks.

### Slice 0: Documentation Baseline

Reconcile stale module catalogue and implementation-status statements with the locally verified
closures. Keep current repository behavior, deferred release work, and deployment state distinct.

**Gate:** The authoritative plan, implementation status, and module catalogue report the same
module boundaries and no completed closure is still labelled partial.

### Slice 1: Student Lifecycle Expansion

**Status:** Complete and locally validated on 30 August 2026.

Implement student documents, subject registrations, progression preparation, transfer,
readmission, and certificate requests. Preserve one canonical person/student identity,
effective-dated enrollment history, linked-guardian access, and tenant-safe academic references.

**Gate:** An administrator can complete each lifecycle operation without SQL; Student and Guardian
portals expose only authorized outcomes; history remains reproducible after reload.

**Gate result:** Passed. Alembic revision `d684eaa982fa` adds the tenant-safe lifecycle schema with
forced RLS and runtime grants. Protected APIs, audited transitions, administrator controls,
Student-own and Guardian-linked reads, two-tenant seed records, cross-tenant isolation, enrollment
side effects, reload persistence, frontend build, and desktop/mobile Playwright journeys were
validated locally. Formal persisted suites remain assigned to Slice 8.

### Slice 2: Applicant Self-Service And Uploads

**Status:** Complete and locally validated on 30 August 2026.

Add applicant authentication and self-service application/document workflows. Introduce secure
tenant-owned media metadata and provider-backed binary storage shared by admissions and student
documents, with explicit file validation, authorization, retention, and audit behavior.

**Gate:** An applicant can submit and track only their own application and documents, while staff
can verify them without exposing storage credentials or cross-tenant objects.

**Gate result:** Passed. Revisions `47a171da8ce2` and `f8cd51ae2d03` add membership-to-Applicant
binding and shared tenant media with forced RLS and restricted runtime grants. Applicant draft
editing, validated PDF/JPEG/PNG upload, submission, reload persistence, own-document retrieval,
staff visibility and private-document download, Student private uploads, authorization-aware
no-store downloads, two-tenant isolation, and idempotent seed preservation were exercised through
local PostgreSQL and interactive Playwright. The final staff Download control was revalidated on
16 September 2026. Focused Ruff, clean Alembic drift at `f8cd51ae2d03`, 207 production OpenAPI
paths, and the frontend production build pass. Production object-storage configuration, retention
execution, malware scanning, and formal persisted suites remain assigned to later release slices.

### Slice 3: Academic And Delivery Hardening

**Status:** Complete and locally validated on 17 September 2026.

Add academic-master dependency editing and in-use mutation safeguards, scoped HOD controls, a
Class Advisor workspace, timetable publication/versioning, and richer Student learning-material
presentation.

**Current checkpoint:** Every parent-bearing academic master exposes tenant-scoped relationship
editing. Matching structural, operational, result, and authorization-scope references return 409
without mutation. Curriculum Subject mappings support Curriculum/Subject changes, and Calendar
Events support consistent Academic Year/Term changes plus explicit optional-Term clearing.
Cross-tenant or mismatched parent references return 422. HOD Department and Class Advisor Section
scopes now constrain Student, Person, Faculty, delivery, timetable, attendance, correction, leave,
summary, marks, Academic Masters, and notice reads or mutations at the service boundary. The
section-scoped Advisor portal provides source-backed dashboard, Student, timetable, attendance, and
read-only delivered-notice journeys. Focused Ruff, frontend build, API denial checks, and
interactive role journeys pass. Revision `c91e4a7d2b60` adds forced-RLS timetable publication
metadata and immutable snapshot lines. HOD publication produced versions 1 and 2, superseded the
prior version, retained both snapshots after a live-period edit, and exposed only the assigned
Section line to Class Advisor. The Student Learning materials route exposes scoped resources with
Subject, Section, Term, Faculty, description, type, and link context; an active class Student saw
one resource while a Student without a current Section saw the explicit empty state.

**Gate result:** Passed. Published versions remained reproducible after mutable period changes,
in-use academic relationships rejected unsafe reassignment, and HOD, Class Advisor, Faculty, and
Student records remained constrained to assigned scopes. Formal persisted suites remain assigned
to Slice 8.

**Gate:** Published timetable versions remain reproducible; in-use academic structures cannot be
destructively changed; every scoped role sees only assigned academic records.

### Slice 4: Operational Documents

**Status:** Complete and locally validated on 17 September 2026.

Generate printable receipts, hall tickets, grade cards, transcripts, participation certificates,
and requested student certificates from authoritative versioned records. Record issuance and
verification metadata rather than storing hand-maintained document facts.

**Gate result:** Passed. Existing Receipt, ActivityCertificate, and issued StudentCertificateRequest
records anchor source-derived documents. Revision `e2b7c4d91a60` adds forced-RLS issuance metadata
for hall tickets, publication-version grade cards, and result-version-manifest transcripts. Issuance
is replay safe, Student/Guardian reads remain own/linked scoped, and unrelated or cross-tenant
references are rejected. Focused Ruff, clean Alembic drift, a 219-path production OpenAPI import,
frontend builds, API matrices, and Controller/Student Playwright journeys pass at desktop, 390px,
and print media. Legacy aggregate-only results disclose missing subject-level snapshots rather than
inventing marks.

**Gate:** Every generated document reconciles to its source record, carries tenant branding, and
cannot reveal unpublished or unauthorized information.

### Slice 5: Providers And Background Jobs

Implement invitation delivery, email/SMS adapters, payment callbacks, communication retries, and
scheduled report execution through provider-independent durable jobs. Keep callbacks authenticated
and idempotent and keep secrets outside source code and browser state.

**Execution order:**

1. Define a provider interface and a development recording provider with no external credentials.
2. Queue invitation email delivery transactionally and stop exposing plaintext invitation tokens
  through the normal administrator UI once provider delivery is enabled.
3. Add one bounded worker command for communication and invitation delivery, immutable attempts,
  retry backoff, stale-job recovery, and operator-visible failure state.
4. Add provider-specific payment callback adapters with tenant resolution, signature verification,
  callback idempotency, authoritative amount/currency checks, and links to existing Payment and
  reconciliation records.
5. Queue due report schedules, regenerate authorization-scoped CSV exports, deliver them through
  the same email provider boundary, and retain immutable delivery attempts.
6. Add worker health, quotas, telemetry, deployment service definitions, and full replay/failure
  validation before selecting production vendors.

See `docs/modules/19-providers-background-jobs.md` for the detailed data, API, worker, security,
and validation plan.

**Gate:** Provider failure is visible and safely retryable; duplicate callbacks are harmless; a
configured report schedule produces an auditable authorized export.

### Slice 6: Public Multi-Tenant CMS

Replace source-coded public content with tenant-owned pages, blocks, media, preview, approval, and
publication. Resolve colleges by approved host or slug and add Law College public routing and SEO
metadata.

**Gate:** Each college serves only its published content and branding; drafts and operational data
remain inaccessible to public requests.

### Slice 7: Policy Configuration And Role Refinement

Make attendance thresholds institution-configurable, complete the richer Faculty marks workspace,
and close any remaining role-specific presentation gaps found during stakeholder review. Employee
attendance remains owned by HR and Payroll rather than student attendance.

**Gate:** Configured policy versions drive calculations consistently, and no role requires a
College Administrator workspace to perform its assigned duties.

### Slice 8: Automated Release Hardening

Add unit, API, permission, forced-RLS, migration, onboarding-idempotency, concurrency, and persisted
Playwright suites. Complete accessibility, secrets/configuration, backup/restore, monitoring,
provider-failure, and fresh-install release checks.

**Gate:** The complete commercial Definition of Done passes against a fresh local PostgreSQL
database before any production deployment is considered.

### Expansion Queue

After Slices 0 through 8 pass, implement each expansion module as its own vertical slice in this
order unless stakeholder approval changes the business priority:

1. Library.
2. HR, employee attendance, leave, and Payroll.
3. Hostel.
4. Transport.
5. Placement.
6. Advanced Finance and institution-specific integrations.

Each expansion module must follow the Standard Module Delivery Sequence and receive its own module
documentation and review gate before the next module starts.
