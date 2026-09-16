# Institution and Academic Masters

**Status:** Implemented locally with PostgreSQL persistence, forced RLS, and administrator configuration UI for all current masters.

## Purpose
Define the institutional and academic structure reused by admissions, enrollment, teaching, attendance, fees, and examinations.

## Implementation Summary
The academics domain provides tenant-safe APIs and administrator forms for the current academic structure tables:
- Campuses: Physical or virtual learning locations
- Academic Years & Terms: Operational cycles and periods
- Departments: Academic divisions
- Programs: Degree offerings with department associations
- Subjects: Course catalog with credits
- Batches & Sections: Student cohorts and teaching groups
- Rooms: Teaching spaces with equipment flags
- Regulations, curricula, curriculum subjects, calendar events, numbering formats, and grading schemes

All tables enforce tenant isolation via PostgreSQL RLS policies. The College Administrator role has read and manage permissions. Representative seed data is integrated with tenant onboarding for both INDUS demo colleges.

The `/portal/academics` UI exposes 15 API-backed master groups with list and configuration forms, plus loading, empty, error, and retry states.

## Roles
- College Administrator: institution-wide configuration.
- Principal/Management: read configuration.
- Head of Department: manage authorized department structures.

## Workflow
1. Configure campuses, academic years, terms, and calendars.
2. Create departments and programs.
3. Version regulations, curricula, subjects, and credits.
4. Create batches, sections, rooms, and numbering formats.
5. Activate a complete academic year after validation.

## Core Rules
- Versions are preserved after operational use.
- Codes are tenant-unique and relationships are tenant-safe.
- All tenant tables use forced RLS and effective status.

## Data
Campus, AcademicYear, Term, Department, Program, Regulation, Curriculum, Subject, Batch, Section, Room, CalendarEvent, and NumberingFormat.

## Current UI Behavior
The Academics route reads and mutates PostgreSQL-backed master data for the authenticated tenant. Browser validation covered all 15 groups and a tenant-isolated program creation.

## Production Completion
Add richer dependency editing, destructive-change safeguards for records already in use, and scoped HOD workflows. No deployment claim is made.

## Acceptance Criteria
- An administrator configures one full academic year without database access.
- Cross-tenant references fail at both API and database layers.
- In-use structures cannot be destructively deleted.
