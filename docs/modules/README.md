# Module Catalogue

Each document is the source of truth for one product area. Status statements distinguish repository behavior, local PostgreSQL validation, and deployment. No local implementation is an AWS deployment claim.

Portal interaction conventions are defined in [Portal UI and UX Decisions](../11-portal-ui-ux-decisions.md).
Demo-only AWS preparation is defined in [AWS Demo Deployment Plan](../12-aws-demo-deployment-plan.md).

| Module | Primary screens | Status |
| --- | --- | --- |
| [01 Platform Access](01-platform-access.md) | Platform login, tenant directory | Implemented locally; provider delivery pending |
| [02 Identity and Access](02-identity-access.md) | College login, memberships, sessions | Implemented and interactively validated locally |
| [03 Institution and Academics](03-institution-academics.md) | Academics setup | Implemented locally; administrator UI implemented |
| [04 Admissions](04-admissions.md) | Campaigns, applications, offers | Staff workflow and Applicant self-service/private uploads implemented locally |
| [05 Students and Guardians](05-students-guardians.md) | Students, profiles, guardians | Lifecycle, private uploads, and requested certificate documents implemented locally |
| [06 Faculty and Delivery](06-faculty-delivery.md) | Faculty, timetable, delivery | Slice 3 hardening complete: scoped roles, versioned timetable, Student materials |
| [07 Attendance and Leave](07-attendance-leave.md) | Attendance, corrections, leave | Scoped role workflows implemented; policy/provider refinements pending |
| [08 Fees and Payments](08-fees-payments.md) | Fees, receipts, reversals | Implemented locally; source-derived printable receipts complete |
| [09 Examinations and Results](09-examinations-results.md) | Exams, marks, results | Implemented locally; hall tickets, grade cards, and transcripts complete |
| [10 Communications and Portals](10-communications-portals.md) | Notices and role portals | Implemented and interactively validated locally |
| [11 Events and Activities](11-events-activities.md) | Events and participants | Implemented locally with printable participation certificates |
| [12 Dashboards and Reports](12-dashboards-reports.md) | Scoped dashboards and reports | Implemented and interactively validated locally |
| [13 Library](13-library.md) | Catalogue and circulation | Planned |
| [14 Hostel and Transport](14-hostel-transport.md) | Accommodation and routes | Planned |
| [15 Placement](15-placement.md) | Opportunities and drives | Planned |
| [16 HR and Payroll](16-hr-payroll.md) | Employees, leave, payroll | Planned |
| [17 Finance and Integrations](17-finance-integrations.md) | Ledger, procurement, integrations | Planned |
| [18 Public Institution Site](18-public-institution-site.md) | Public college website | Static Arts site implemented; multi-tenant CMS pending |
| [19 Providers and Background Jobs](19-providers-background-jobs.md) | Email/SMS, callbacks, workers | Planned next as Slice 5 |
