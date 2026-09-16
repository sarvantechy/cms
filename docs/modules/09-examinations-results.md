# Examinations and Results

**Status:** Implemented locally for College Administrator and Examination Controller operations with PostgreSQL persistence, forced RLS, protected lifecycle APIs, versioned result snapshots, and source-backed UI controls.

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
`/portal/examinations` supports assessment schemes, versioned grade bands, exam sessions and schedules, eligibility registration, capacity-aware room seating, hall-ticket sources, invigilation, marks entry/verification/locking, reviewed moderation or revaluation, publication, reopening, and republishing. Published aggregates include GPA and retain versioned subject lines and lifecycle snapshots; transcripts derive CGPA from published results.

## Production Completion
The College Administrator/Controller workflow and permission-scoped Student/Guardian result views are complete locally. Printable hall-ticket, grade-card, and transcript document rendering plus a richer Faculty marks workspace remain release work. No deployment claim is made.

## Local Validation
- Alembic upgraded PostgreSQL through `c7d8e9f0a1b2`; metadata drift passed.
- Focused Ruff passed for the complete examinations domain and production OpenAPI generated 160 paths.
- The web production build passed.
- Interactive Playwright loaded all examination and academic source endpoints with `200 OK`, rendered all controller sections, and verified desktop and 390px layouts without horizontal overflow or clipped headings.

## Acceptance Criteria
- Students cannot infer unpublished marks.
- Calculations reproduce exactly from stored inputs and rule version.
- Every published change retains complete history.
