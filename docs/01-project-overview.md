# End-to-End Platform Overview

Portal interaction and dashboard conventions are maintained in
`docs/11-portal-ui-ux-decisions.md`. Provider, callback, and worker scope is maintained in
`docs/modules/19-providers-background-jobs.md`.

## Purpose

The 4by4 College Management System will give a college one reliable place to manage its student and administrative operations. It replaces disconnected spreadsheets, paper registers, and repeated data entry with linked workflows.

For example, an accepted admission application should become a student record without staff typing the same details again. That student can then be assigned to a program and section, added to attendance registers, invoiced for fees, registered for examinations, and shown relevant information through the student portal.

## The Problem Being Solved

Colleges often maintain separate records for admissions, departments, attendance, fees, examinations, library services, transport, and placement. This causes:

- Duplicate and inconsistent student details
- Delays caused by paper-based approvals
- Difficulty finding the current status of an application or payment
- Attendance and marks calculation errors
- Limited visibility for students and parents
- Reports that require manual reconciliation
- Security and privacy risks from uncontrolled files

The CMS will connect these areas through a shared, controlled data model.

## Product Goals

1. Manage the complete student journey from enquiry to alumni status.
2. Give each staff member only the access needed for their job.
3. Allow several colleges to use the same product while keeping their data isolated.
4. Reduce duplicate entry by passing verified information between modules.
5. Provide students and parents with timely academic and financial information.
6. Create trustworthy operational and management reports.
7. Preserve a clear audit history for sensitive changes.

## Intended Customers

The product is intended for colleges and higher-education institutions that may have:

- One or more campuses
- Multiple departments and programs
- Semester, trimester, or annual academic patterns
- Institution-specific grading, fee, quota, and approval rules
- Day scholars, hostel residents, and transport users

Rules that vary between institutions must be configurable rather than hard-coded for one college.

## Product Boundaries

The product will manage college operations, but the first release will not attempt to be all of the following:

- A complete online learning platform with live classes and rich course authoring
- A general-purpose accounting replacement for every institution
- A university-wide affiliation system connecting unrelated colleges
- A government regulatory portal
- A biometric or GPS hardware product

The CMS may integrate with learning, accounting, university, biometric, payment, email, SMS, and GPS services where required.

## Core Concepts

| Term | Plain-language meaning |
| --- | --- |
| Tenant | One college or institution using the hosted product |
| Campus | A physical or administrative branch of a college |
| Academic year | The period in which teaching and examinations are organized |
| Program | A qualification such as B.Sc. Computer Science |
| Curriculum | The versioned set of subjects and rules for a program |
| Batch | Students who joined a program in the same intake period |
| Section | A teaching group within a batch |
| Enrollment | A student's participation in a program for a defined period |
| Subject offering | A subject taught to a particular group in a particular term |
| Role | A job-based collection of permissions, such as Accountant |
| Audit log | A record of who changed important information and when |

## Success Criteria

The product is successful when:

- A college can configure a new academic year without developer assistance.
- An application can progress to enrollment without duplicate student entry.
- Attendance, fee balances, and published results can be traced to source transactions.
- Two colleges using the same deployment cannot access each other's data.
- Staff can complete common tasks without relying on hidden spreadsheet calculations.
- Students can see their own timetable, attendance, fees, notices, and published results.
- Management reports agree with the underlying operational records.
