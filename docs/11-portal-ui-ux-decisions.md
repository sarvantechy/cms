# Portal UI and UX Decisions

## Status

Implemented and interactively validated locally on 17 September 2026.

## Decision: Workspace Screens, Not Popups

Authenticated portal workflows do not use native dialogs, translucent modal backdrops, or fixed popup panels. Create, edit, detail, assignment, and printable-document experiences render as opaque screens in the normal workspace flow.

When a screen is active:

- the owning list or dashboard is not rendered behind it;
- the screen uses the full available workspace width;
- Back, Cancel, or Close restores the owning workspace;
- validation and submission state remains local to the workflow;
- desktop and mobile layouts use the same semantic structure;
- printable documents continue to isolate document content through print media rules.

This approach is preferred for the CMS because most workflows are operational forms or record reviews rather than short confirmations. It improves mobile space, focus, accessibility, error recovery, and visual clarity. Unique nested URLs are not required for the current implementation; they may be added later if deep links, shareable record locations, or browser-history restoration become product requirements.

## Affected Workspaces

- Access administration: invitation, password, role, and assignment screens.
- Academic Masters: create and edit screens.
- Admissions: enquiry and resource creation plus application detail.
- Students: creation, profile, guardian, enrollment, lifecycle, and certificate screens.
- Faculty and Delivery: faculty, offering, allocation, timetable, session, posting, substitution, lesson, material, and progress screens.
- Attendance: attendance entry, correction, and leave screens.
- Communications and Events: notice and event creation screens.
- Fees and Examinations: receipt, hall-ticket, grade-card, and transcript screens.
- Activities and Students: participation and requested-certificate screens.

## Dashboard Direction

Dashboards are operational work surfaces, not marketing pages. The implemented design uses:

- a role-specific identity and date brief;
- source-backed metric links using the current role accent;
- a priority queue derived only from records already authorized for the actor;
- quick-access links to the same source modules;
- a management command view above institution-wide report controls;
- explicit empty and error states;
- stable one-column mobile behavior at 390 px.

The dashboard does not introduce decorative charts or duplicate aggregate storage. New visualizations should be added only when the underlying metric definition, freshness, authorization, and source drill-down are available.

## Validation

- Frontend production build passes.
- Source search finds no native `<dialog>`, popup backdrop, or `::backdrop` usage in `web/src`.
- College Administrator dashboard renders the management command view and report metrics.
- Class Advisor and Faculty dashboards render four scoped metric links, a priority state, and four quick-access links.
- A representative notice editor is a static opaque `SECTION`; sibling workspace content is hidden while it is active.
- Academic Masters and Access editors use the same replacement-screen interaction model.
- Desktop and 390 px checks report no horizontal overflow.
