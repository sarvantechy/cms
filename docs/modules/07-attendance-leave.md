# Attendance and Leave

**Status:** Implemented locally for College Administrator student-attendance and person-leave operations with PostgreSQL persistence, forced RLS, protected APIs, and source-backed UI controls.

## Purpose
Generate class sessions from timetables, capture period attendance, lock registers, control corrections, review leave, and derive traceable attendance and examination-eligibility inputs.

## Roles
- College Administrator: implemented operational workspace.
- Faculty and HOD: scoped entry and review workspaces.
- Student and guardian: own-record or linked-student read workspaces.

## Implemented Workflow
1. Generate dated class sessions from conflict-checked timetable periods in Academic Delivery.
2. Enter present, absent, late, or excused status against a student and class session.
3. Submit attendance and lock all submitted rows for a session.
4. Request a reasoned correction with its original and proposed outcome, then approve or reject it through a protected review action.
5. Create person-linked leave requests and approve or reject pending requests.
6. Select a student and view counts and percentage derived from submitted or locked source rows.
7. Compare the result with the server-owned `75%` default policy threshold and expose shortage percentage points and an explicit examination-eligibility input.

## Core Rules
- Every percentage traces to submitted or locked attendance rows joined to submitted or locked class sessions.
- Locked records change only when an approved correction still matches its captured original outcome.
- Tenant and permission context comes from authenticated `ActorContext`; cross-tenant references are rejected by schema constraints and forced RLS.
- A student with no eligible source rows is not marked examination eligible.
- The threshold is server-owned so clients do not independently calculate eligibility.
- ORM responses are serialized before commit so transaction-local tenant context remains available.

## Data And APIs
The implemented data includes `ClassSession`, `AttendanceRecord`, `AttendanceCorrection`, and `LeaveRequest`. Protected APIs cover attendance listing and submission, register locking, correction creation and review, leave creation and review, and per-student source-derived summaries.

## Current UI Behavior
The Attendance workspace provides source-backed attendance entry, register locking, correction requests and review, leave requests and review, session and record lists, and a student selector with percentage, threshold, shortage, outcomes, and eligibility presentation.

## Remaining Adjacent Scope
- Faculty/staff clock or daily attendance is a separate HR attendance domain and remains in Increment 15.
- Parent notification delivery is provider-independent and traceable locally; external email/SMS adapters remain release work.
- Institution-configurable threshold policy can replace the current server-owned `75%` default without changing the summary contract.
- Formal unit, API, permission, RLS, and persisted browser tests remain deferred until closure implementation finishes.

## Acceptance Status
- Every displayed percentage traces to eligible source records: implemented.
- Corrections preserve original and requested outcomes, reason, state, reviewer, and timestamps; approval applies the requested outcome: implemented.
- Cross-tenant writes are blocked by tenant-safe constraints and forced RLS: implemented locally.
- Role-scoped attendance access: implemented and interactively validated locally.
