# Dashboards and Reports

**Status:** Implemented and interactively validated locally.

## Purpose

Provide role-specific, source-derived operational dashboards and auditable reports with drill-down and freshness indicators.

## Roles

- Leadership: institution-wide management measures.
- Operational staff: module and scope-specific queues.
- Students and guardians: own or linked-student summaries.

## Workflow

1. Resolve actor permissions and scopes.
2. Query authoritative module records and calculation definitions.
3. Display freshness, filters, totals, and exceptions.
4. Drill into the exact source records.
5. Export only the actor-authorized result set.

## Core Rules

- No dashboard stores duplicate hand-maintained totals.
- Every metric has a definition, timestamp, and source drill-down.
- Export uses the same authorization and filters as screen data.

## Data

SavedReport, ReportExport, ReportSchedule, request-time metric definitions, and module-owned aggregate queries.

## Current UI Behavior

`/portal/dashboard` renders source-backed totals for students, attendance, fees, examinations,
communications, and activities. College Administrators can filter by inclusive dates and academic
year, inspect calculation time and definitions, drill into source records, save named views,
download CSV, and configure recurring delivery. Operational roles receive permission-scoped links
and counts instead of institution-wide aggregates. Management receives an institution command-view
brief above the report controls. Student, Faculty, HOD, Class Advisor, Accountant, Examination,
Admissions, Activity, and Guardian dashboards use the actor's role accent, a compact identity/date
brief, styled metric links, source-derived priority signals, and quick-access actions. API failures
are never replaced with fabricated records.

## Implemented Behavior

- Management totals and drill-down require `reports.management.read`.
- Operational dashboards use each actor's authorized module APIs and record scopes.
- Dashboard cards are actionable links rather than decorative totals and keep stable dimensions at
  desktop, tablet, and 390 px mobile widths.
- Priority items derive only from already-authorized correction, leave, fee, application, and
  result records; an empty queue is shown explicitly.
- Date and academic-year filters are shared by totals, drill-down, saved views, and exports.
- Every metric returns a calculation timestamp, formula description, and authoritative source.
- Saved views, export audit records, and schedules are actor-owned and protected by forced tenant RLS.
- CSV exports contain up to 10,000 rows from the same scoped source query used by drill-down, and
  the audit record stores the number of rows actually emitted.

## Local Validation

On 29 August 2026, a College Administrator loaded all six metric definitions, applied a date
filter, opened Student, Attendance, Fees, and Activities drill-downs, saved a named view, persisted
a weekly schedule from the six available metrics, and generated a CSV with
`id,label,detail,occurred_on` columns. All permitted requests returned `200` or `201`. At 390 px
the page had no horizontal overflow. Activity Coordinator validation displayed only its authorized
Events count and a direct management-overview request returned `403`. A Law College Administrator
could not see the Arts College saved view or schedule.

On 17 September 2026, interactive Playwright revalidated the redesigned College Administrator,
Class Advisor, and Faculty dashboards. Administrator rendered the management command view and four
report metrics; Advisor and Faculty rendered four scoped metric cards, priority state, and four
quick-access links. Desktop and 390 px views had no horizontal overflow or API alerts.

## Remaining Release Work

Background delivery execution and institution-specific statutory templates require provider and
college configuration. Formal unit, API, permission, RLS, migration, and browser suites remain
deferred until the final test phase.

## Acceptance Criteria

- Every total reconciles to operational records.
- Scoped users cannot infer broader counts through reports.
- Failed data requests never fall back to sample records.
