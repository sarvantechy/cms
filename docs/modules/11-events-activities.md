# Events and Activities

**Status:** Implemented and interactively validated locally.

## Purpose
Manage events, clubs, registrations, selection, teams, attendance, achievements, certificates, points, venues, and budgets.

## Roles
- Activity Coordinator: manage authorized activities and participants.
- Approver: approve venue and budget requests.
- Student: discover and register for eligible events.
- Administrator: oversee tenant-wide activity records.

## Workflow
1. Create event with eligibility, capacity, venue, and budget needs.
2. Approve controlled resources and publish registration.
3. Register or select participants and teams.
4. Record attendance, results, achievements, and evidence.
5. Issue verifiable certificates and activity points.

## Core Rules
- Coordinators receive no unrelated academic or financial authority.
- Capacity and duplicate registration are transactionally enforced.
- Certificates derive from approved participation outcomes.

## Data
ActivityClub, Activity, ActivityApprovalRequest, EventRegistration, ActivityTeam,
ActivityTeamMember, ActivityExpense, Achievement, ActivityCertificate, and ActivityPoint.

## Current UI Behavior
`/portal/events` provides a permission-scoped Activity Coordinator workspace for club and event
setup, publication, venue and budget approval, participant review and attendance, teams, expenses,
certificates, points, and achievements. The Student workspace lists published events only and
permits registration through the authenticated student's own record. Selecting an event reloads
its participant and operational records rather than reusing another event's state.

## Implemented Behavior
- Every tenant-owned activity table uses forced PostgreSQL RLS, runtime-role grants, and
	tenant-safe references.
- Event publication is blocked while venue or budget requests remain unresolved.
- Registration prevents duplicate enrollment, enforces capacity, and requires a published event
	for Student self-service.
- Student registration is authorized by `activities.self.register` and the actor's own student
	scope; clients cannot select another student record.
- Expenses cannot be approved beyond the event's approved budget.
- Certificates require attended participation, have unique verification serials, and resolve
	through the protected verification endpoint.
- Certificate issuance, points, and achievements remain visible as persisted participant outcomes.

## Local Validation
On 29 August 2026, the browser journey created and published `Leadership Summit 2026`, approved its
venue and INR 5,000 budget, registered a Student through self-service, approved the registration,
recorded attendance, created a team, approved an INR 1,200 expense, issued and verified a
certificate, awarded 25 points, and recorded an achievement. Mutation responses were `200` or
`201`; reloads preserved every outcome. The Activity Coordinator page had no horizontal overflow
at a 390 px viewport.

## Remaining Release Work
Formal unit, API, permission, RLS, migration, concurrency, and persisted browser suites remain
deferred until the implementation closures are complete. Cross-module event reporting belongs to
the Dashboards and Reports closure.

## Acceptance Criteria
- Eligibility and capacity are enforced under concurrency.
- Participant access is tenant/event scoped.
- Certificate verification resolves to immutable source participation.
