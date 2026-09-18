# Examinations and Results

**Status:** Implemented locally for College Administrator, Examination Controller, and scoped Student access with PostgreSQL persistence, forced RLS, protected lifecycle APIs, versioned result snapshots, source-backed UI controls, and printable examination documents.

## Purpose
Configure assessments, schedule examinations, control eligibility and marks, calculate grades, publish results, and process revaluation.

## Roles
- Examination Controller: configure, verify, lock, and publish.
- Faculty: enter marks for assigned assessments.
- Student/Guardian: view only published authorized results.

## Workflow
1. Version assessment and grading schemes.
2. Schedule exams, registration, halls, seating, and invigilation.
3. Determine eligibility from enrollment and attendance inputs.
4. Enter, verify, lock, moderate, and approve marks.
5. Calculate grades, GPA/CGPA, ranks, and result status.
6. Publish, revalue, supplement, and issue documents.

## Core Rules
- Published results are reproducible from versioned rules.
- Entry, verification, and publication permissions are distinct.
- Post-publication changes require reopen and republish history.

## Data
AssessmentScheme, ExamSession, ExamSchedule, Eligibility, Registration, Seating, MarkEntry, GradeRule, Result, Publication, Revaluation, and Transcript.

## Current UI Behavior
`/portal/examinations` supports assessment schemes, versioned grade bands, exam sessions and schedules, eligibility registration, capacity-aware room seating, hall-ticket sources, invigilation, marks entry/verification/locking, reviewed moderation or revaluation, publication, reopening, and republishing. Examination Controllers can issue and print hall tickets, grade cards, and transcripts. Students can retrieve only already-issued documents for their own scoped registrations and results. Transcripts derive CGPA from a pinned result-version manifest.

Hall tickets, grade cards, and transcripts render as full-width opaque document screens. The source
workspace is not visible behind the active document, and print media emits only the document.

## Production Completion
The College Administrator/Controller workflow and permission-scoped Student/Guardian result views are complete locally. Revision `e2b7c4d91a60` adds immutable issuance metadata for hall tickets, grade cards, and transcripts with forced RLS and restricted runtime inserts. Hall tickets pin registration manifests, grade cards pin publication versions, and transcripts pin result-version manifests. A richer Faculty marks workspace remains release work. No deployment claim is made.

## Local Validation
- Alembic upgraded PostgreSQL through `e2b7c4d91a60`; metadata drift passed.
- Focused Ruff passed for the examination document changes and production OpenAPI generated 219 paths after the complete Slice 4 document set.
- The web production build passed.
- API validation confirmed replay-safe issuance, linked Student retrieval, Student issuance denial, and unrelated/cross-tenant rejection. Interactive Playwright opened all three Controller and Student documents and verified desktop, 390px, and print-media rendering.
- The seeded legacy result predates subject-line retention, so its grade card and transcript explicitly show an aggregate-only note. Newly published result versions retain and render subject lines.

## Acceptance Criteria
- Students cannot infer unpublished marks.
- Calculations reproduce exactly from stored inputs and rule version.
- Every published change retains complete history.
