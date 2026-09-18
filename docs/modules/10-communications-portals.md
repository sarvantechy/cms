# Communications and Role Portals

**Status:** Communications and nine permission-scoped tenant role portals are implemented and interactively validated locally with PostgreSQL persistence and forced RLS. External email/SMS provider adapters remain release work.

## Purpose
Deliver targeted notices, circulars, announcements, acknowledgements, and role-specific portal experiences backed by source modules.

## Roles
- Authorized publisher: draft, approve, schedule, and publish.
- Tenant users: receive only messages matching role and record scope.
- Student and Parent/Guardian: view own or explicitly linked academic, attendance, fee, result, notice, and event records.
- Faculty and HOD: use assignment- or department-scoped teaching workspaces.
- Class Advisor: view assigned-Section Students, timetable, attendance, and delivered notices.
- Accountant, Examination Controller, Admission Officer, and Activity Coordinator: use permission-specific operational workspaces.

## Workflow
1. Create content from a controlled template.
2. Select tenant-scoped audience by role, academic structure, or explicit recipient.
3. Approve and schedule publication.
4. Deliver in-app and through configured email/SMS providers.
5. Track retries, delivery, read state, and acknowledgement.

## Core Rules
- Audience resolution occurs server-side from authoritative records.
- Provider retries are idempotent.
- Portal widgets never fabricate records after API failure.

## Data
MessageTemplate, Notice, NoticeApprovalEvent, NoticeDelivery, CommunicationDeliveryJob, DeliveryAttempt, NoticeAcknowledgement, and CommunicationPreference.

## Current UI Behavior
`/portal/notices` supports templates, preferences, draft creation, server-resolved audience preview, submission, approval/rejection, scheduling or publication, acknowledgement, delivery-job inspection, attempt history, and retry with retained success/error feedback.

Notice and event creation use opaque workspace screens instead of popup dialogs. Across the portal,
create, edit, detail, and document workflows replace their parent content while active. This is the
approved interaction model; unique nested URLs are deferred unless deep linking becomes necessary.

The shared portal shell derives its role label, navigation, dashboard requests, and mutation controls from authenticated role, permission, and scope claims. Seeded Student, Parent/Guardian, Faculty, HOD, Class Advisor, Accountant, Examination Controller, Admission Officer, and Activity Coordinator identities authenticate through the production API. Student and guardian reads resolve canonical own/linked student IDs; attendance, invoices, published results, and timetable delivery are filtered to those records. Faculty delivery reads and writes are limited to assigned subject offerings, HOD delivery and academic reads resolve assigned Departments, and Class Advisor records resolve one assigned Section.

Read-only portal users list only notices delivered to their membership. Class Advisor notice
authoring remains disabled because the current communication audience model does not yet support a
Section audience; this prevents a scoped role from creating institution-wide notices.

## Production Completion
Core communication workflow and role portals are complete locally. External email/SMS provider adapters, production credentials, provider callbacks, and the deferred formal automated suites remain release work. No deployment claim is made.

## Local Validation
- Communication migrations remain applied and forced-RLS protected; the complete production application now exposes 219 OpenAPI paths.
- Interactive Playwright completed the administrator draft-to-approval-to-publication workflow and displayed two immutable approval events plus three channel jobs.
- Ten non-administrator demo identities spanning nine role workspaces authenticated and rendered permission-derived navigation.
- Student attendance and timetable screens returned one own-record source row with no mutation controls; Faculty timetable returned one assigned offering, period, and session with only assigned-delivery actions.
- The validated portal requests returned no unexpected `401`, `403`, or `404` responses, and desktop plus 390px checks had no horizontal overflow.
- On 16 September 2026, the Class Advisor journey rendered four scoped dashboard totals, one assigned Student, two class sessions, one attendance row, and read-only delivered notices with no Academics, Fees, attendance-entry, leave-request, correction-request, or notice-create controls. HOD rendered one Department, one Program, three Subjects, one Faculty profile, and scoped delivery controls with no cross-department records or institution-only Faculty creation.

## Acceptance Criteria
- Messages reach only intended tenant and audience.
- Delivery failures are visible and retryable.
- Every portal total links to authoritative module data.
