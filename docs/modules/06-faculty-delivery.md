# Faculty and Academic Delivery

**Status:** Implemented locally for College Administrator, scoped Faculty/HOD delivery, and Student timetable access with PostgreSQL persistence, forced RLS, protected APIs, audit events, and source-backed UI controls.

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
5. Generate dated class sessions from timetable periods.
6. Record effective-dated department postings and class substitutions.
7. Create lesson plans, linked learning materials, and dated syllabus-progress entries.

## Core Rules
- Tenant and permission context comes from authenticated `ActorContext`, never request tenancy.
- Every delivery table is tenant-owned, protected by forced RLS, and granted only to the runtime role.
- Timetable conflicts are rejected by the service rather than presented as warnings.
- Faculty, department, offering, and class-session references come from tenant-scoped catalogues.
- Delivery mutations produce attributable audit events.
- ORM responses are serialized before commit so transaction-local tenant context remains available.

## Data And APIs
The implemented data includes `FacultyProfile`, `DepartmentPosting`, `SubjectOffering`, `FacultyAllocation`, `TimetablePeriod`, `ClassSession`, `ClassSubstitution`, `LessonPlan`, `LearningMaterial`, and `SyllabusProgress`.

Protected list and create APIs are available for each operational resource. Existing timetable APIs also provide conflict-checked period creation and date-range class-session generation.

## Current UI Behavior
The Faculty and Timetable workspace provides source-backed profile, offering, allocation, timetable, session, posting, substitution, lesson-plan, material, and syllabus-progress forms. It displays workload totals, generated sessions, delivery records, loading and empty states, and server validation feedback.

## Remaining Adjacent Scope
- A distinct Class Advisor workspace and richer Student learning-material presentation remain future portal work.
- Timetable publication/versioning is a future workflow; current periods and generated sessions are operational records, not a separately published snapshot.
- Formal unit, API, permission, RLS, and persisted browser tests remain deferred until closure implementation finishes.

## Acceptance Status
- Overlapping faculty, room, or section periods are rejected: implemented.
- Administrators can build a conflict-free schedule and generate sessions without SQL: implemented.
- Faculty assigned-delivery and Student timetable views: implemented and interactively validated locally.
