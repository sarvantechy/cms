# Faculty and Academic Delivery

**Status:** Slice 3 delivery hardening is complete locally for College Administrator, scoped Faculty/HOD/Class Advisor delivery, versioned timetables, and Student learning resources.

## Purpose
Manage canonical faculty identities, department postings, subject delivery, workload, timetable periods, class sessions, substitutions, lesson plans, learning materials, and syllabus progress.

## Roles
- College Administrator and HOD: manage appropriately scoped faculty and delivery records.
- Faculty: manage assigned delivery records and view the assigned schedule.
- Student: view enrolled timetable sessions.

## Implemented Workflow
1. Create a faculty profile from a tenant-scoped canonical person.
2. Create term, subject, and section offerings.
3. Allocate faculty to offerings and derive workload from allocation and period counts.
4. Build timetable periods with server-side faculty, room, and section conflict rejection.
5. Publish immutable, versioned timetable snapshots for an institution or assigned Department.
6. Generate dated class sessions from operational timetable periods.
7. Record effective-dated department postings and class substitutions.
8. Create lesson plans, linked learning materials, and dated syllabus-progress entries.

## Core Rules
- Tenant and permission context comes from authenticated `ActorContext`, never request tenancy.
- Every delivery table is tenant-owned, protected by forced RLS, and granted only to the runtime role.
- Timetable conflicts are rejected by the service rather than presented as warnings.
- Faculty, department, offering, and class-session references come from tenant-scoped catalogues.
- Delivery mutations and timetable publication produce attributable audit events.
- Published timetable lines retain source IDs and display-critical labels; later operational edits
	never rewrite a historical version.
- ORM responses are serialized before commit so transaction-local tenant context remains available.

## Data And APIs
The implemented data includes `FacultyProfile`, `DepartmentPosting`, `SubjectOffering`, `FacultyAllocation`, `TimetablePeriod`, `TimetablePublication`, `TimetablePublicationLine`, `ClassSession`, `ClassSubstitution`, `LessonPlan`, `LearningMaterial`, and `SyllabusProgress`.

Protected list and create APIs are available for each operational resource. Existing timetable APIs also provide conflict-checked period creation and date-range class-session generation.

## Current UI Behavior
The Faculty and Timetable workspace provides source-backed profile, offering, allocation, timetable, session, posting, substitution, lesson-plan, material, and syllabus-progress forms. It displays workload totals, generated sessions, delivery records, loading and empty states, and server validation feedback.

Faculty, offering, allocation, period, session-generation, posting, substitution, lesson, material,
and progress editors occupy opaque in-workspace screens. The parent delivery dashboard is not
rendered behind the active editor.

HOD reads and writes are constrained to assigned Department offerings, Faculty allocations and
postings, timetable periods, class sessions, substitutions, lesson plans, materials, and syllabus
progress. Direct IDs outside scope are rejected. HOD can create delivery records only when both
the Subject and Section belong to the assigned Department, and institution-only Faculty profile
creation is hidden and rejected. The initial Class Advisor workspace receives read-only timetable
sessions for its assigned Section.

The Timetable workspace exposes scoped publication history and immutable snapshot lines.
Administrators publish institution versions and HOD users publish their assigned Department;
Faculty, Class Advisor, and Student readers receive only lines visible through offering or
enrollment scope. Republishing increments the scope version and marks the previous version
superseded without changing its lines.

The Student portal exposes a dedicated Learning materials route. Its API joins each scoped
resource to Subject, Section, Term, and assigned Faculty context so the UI never presents opaque
offering IDs. Resources include type, description, course context, and an external Open action,
with explicit loading, empty, error, and retry states.

## Remaining Adjacent Scope
- Formal unit, API, permission, RLS, and persisted browser tests remain deferred until closure implementation finishes.

## Acceptance Status
- Overlapping faculty, room, or section periods are rejected: implemented.
- Administrators can build a conflict-free schedule and generate sessions without SQL: implemented.
- Faculty assigned-delivery and Student timetable views: implemented and interactively validated locally.
- HOD Department scope and Class Advisor Section timetable scope: implemented and interactively validated locally on 16 September 2026.
- Timetable publication/versioning: implemented at revision `c91e4a7d2b60` and interactively
	validated on 17 September 2026. Version 1 remained unchanged after operational-period mutation,
	version 2 superseded version 1, Advisor saw one assigned-Section line without publish controls,
	and Law tenant access returned no history/404 detail.
- Student learning materials: an active class-enrolled Student rendered one labelled Computer
	Science resource with Subject, Section, Term, Faculty, description, type, and Open action. The
	original Student without a current Section rendered the explicit empty state. Arts Advisor and
	Law users received only their own scoped offering resources. Desktop and 390 px layouts passed.
