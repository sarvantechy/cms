# 4by4 End-to-End College Management Platform

4by4 College Management System (CMS) is a planned multi-tenant web platform for managing the complete academic and administrative operations of colleges. It will bring admissions, students, academics, attendance, fees, examinations, staff, communication, and campus services into one connected system.

This repository currently contains the product and technical planning documents. Implementation will be delivered module by module, beginning with the common platform and the core student journey.

## What Multi-Tenant Means

One hosted application can serve many colleges. Each college is a separate **tenant** with its own users, branding, settings, campuses, students, and records. A user from one college must never be able to view or change another college's data.

## Documentation Guide

| Document | Audience | Purpose |
| --- | --- | --- |
| [Project Overview](docs/01-project-overview.md) | Everyone | Vision, goals, boundaries, and success criteria |
| [Modules and Features](docs/02-modules-and-features.md) | College management and product team | Complete functional scope and identified gaps |
| [Users and Permissions](docs/03-users-and-permissions.md) | College management and developers | System users, responsibilities, and access rules |
| [Business Workflows](docs/04-business-workflows.md) | Everyone | Correct end-to-end operational flows |
| [Multi-Tenant Architecture](docs/05-multi-tenant-architecture.md) | Developers and technical reviewers | Application, data, security, and integration design |
| [Implementation Roadmap](docs/06-implementation-roadmap.md) | Product and delivery teams | Module order, releases, dependencies, and completion criteria |
| [Demo Scope and Experience](docs/07-demo-scope-and-experience.md) | Everyone | Exact scope, users, screens, and boundaries of the first demo |
| [Demo Implementation Plan](docs/08-demo-implementation-plan.md) | Product and development teams | Build sequence, acceptance criteria, tests, and demo walkthrough |
| [Multi-Tenant Demo Decision](docs/09-multi-tenant-demo-decision.md) | Product and development teams | Tenant identity, isolation, switching, branding, and seed strategy |
| [Authoritative Implementation Plan](docs/10-authoritative-implementation-plan.md) | Product and engineering teams | Complete role model, module sequence, delivery rules, and completion gates |
| [Implementation Status](docs/implementation-status.md) | Everyone | Current implementation state, limitations, validation, and next review gate |
| [Module Catalogue](docs/modules/README.md) | Product and engineering | Per-screen purpose, workflows, rules, data, UI status, and acceptance criteria |

## Proposed First Release

The first useful release will include:

1. College onboarding, campuses, academic years, and branding
2. User accounts, roles, permissions, and audit history
3. Departments, programs, curricula, batches, sections, and subjects
4. Enquiries, applications, document verification, and admission approval
5. Student, guardian, document, and enrollment records
6. Faculty records, subject allocation, timetable, and academic calendar
7. Period-wise attendance, leave, and notifications
8. Fee invoicing, concessions, payments, receipts, and pending-fee tracking
9. Basic examinations, marks, grades, results, and student portal
10. Notices and essential management reports

Library, hostel, transport, placement, activities, complete HR/payroll, and full accounting will follow after the academic core is stable.

## Current Delivery Focus

Before building the complete first release, the project will deliver a smaller working demo for two college tenants: **INDUS ARTS & SCIENCE INTERNATIONAL COLLEGE** and **INDUS LAW COLLEGE**. The demo will prove tenant isolation and show connected student, academic, attendance, fee, notice, and dashboard workflows using realistic sample data.

The demo boundary is defined in [Demo Scope and Experience](docs/07-demo-scope-and-experience.md). Production implementation now follows the [Authoritative Implementation Plan](docs/10-authoritative-implementation-plan.md); the older demo plan remains a record of the prototype scope.

Production Increment 1 now includes the PostgreSQL tenancy and authorization foundation, the full
baseline permission and role-template catalogue, and idempotent onboarding for both initial INDUS
tenants. With the backend environment configured, synchronize these records from the repository root:

```bash
cd backend && ../.venv/bin/python -m app.commands.onboard_tenants
```

For an explicitly controlled local demo, provide a temporary password of 12 to 72 UTF-8 bytes and
opt in to synthetic administrator creation:

```bash
cd backend && DEMO_SEED_PASSWORD='temporary-demo-password' \
  ../.venv/bin/python -m app.commands.onboard_tenants --seed-demo
```

Running onboarding without `--seed-demo` continues to synchronize only tenants and authorization
definitions. Authentication is exposed under `/api/v1/auth`, and account invitations, password
changes, and session management are exposed under `/api/v1/identity`. Invitation tokens are returned
to the authorized administrator until a communication provider is configured. Authorized tenant
administrators can also list memberships, suspend or end access, reactivate eligible memberships,
and revoke all sessions for a selected membership. Platform authentication is isolated under
`/api/v1/platform`: its audience-restricted credentials can list the tenant directory and control
tenant lifecycle, but cannot access tenant-bound routes or tenant-owned records. The college login
frontend now authenticates the two seeded College Administrators, restores sessions through refresh
rotation, and revokes the backend session on sign-out. Operational module records remain previews.

## Guiding Principles

- Enter information once and reuse it across modules.
- Preserve history instead of overwriting important academic or financial records.
- Make every sensitive action attributable to a user.
- Enforce college separation in the database and the application.
- Use approval workflows for admissions, attendance corrections, marks, refunds, and other controlled actions.
- Keep the web application responsive, accessible, and understandable on desktop and mobile devices.
- Build reports from verified operational data rather than maintaining duplicate totals.
