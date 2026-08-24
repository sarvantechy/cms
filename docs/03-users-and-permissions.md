# Users and Permissions

## Why Permissions Matter

Not every employee should see or change every record. A faculty member may enter attendance for an assigned class but should not change student fee payments. An accountant may collect fees but should not alter published marks. A parent should see only linked children.

The system will use **role-based access control**. Roles provide a convenient starting set of permissions, while the backend checks the exact permission and the user's college, campus, department, class, or record scope.

## Main User Types

| User | Typical responsibilities |
| --- | --- |
| Platform administrator | Onboard and support college tenants without performing normal college operations |
| College administrator | Configure the institution, users, roles, campuses, and modules |
| Principal/management | Approve controlled actions and view institution-wide reports |
| Admission officer | Manage enquiries, applications, verification, selection, and offers |
| Head of department | Manage department academics, faculty allocation, and approvals |
| Faculty member | View timetable, record attendance, maintain lesson progress, and enter assigned marks |
| Class advisor | Monitor a defined student group, attendance, and student concerns |
| Examination controller | Configure examinations, control marks workflows, and publish results |
| Accountant/cashier | Configure permitted fees, collect payments, issue receipts, and reconcile collections |
| HR/payroll officer | Manage confidential employment, leave, and payroll information |
| Librarian | Manage library stock, circulation, reservations, and fines |
| Hostel warden | Manage assigned hostel occupancy, attendance, and incidents |
| Transport manager | Manage routes, vehicles, drivers, and allocations |
| Placement officer | Manage companies, opportunities, drives, and placement outcomes |
| Activity coordinator | Manage clubs, events, participation, and certificates |
| Student | Access only their own academic, attendance, fee, request, and published-result information |
| Parent/guardian | Access approved information for linked students only |

## Permission Model

Permissions should describe actions, for example:

```text
student.view
student.create
student.update
admission.verify_documents
admission.approve
attendance.record
attendance.correct
attendance.approve_correction
fees.collect
fees.approve_concession
fees.refund
marks.enter
marks.verify
results.publish
```

Possessing a permission is only the first check. The request must also be within the user's allowed scope.

Examples:

- Faculty can record attendance only for assigned subject offerings.
- A department head can approve work only within assigned departments.
- A campus accountant may see only that campus unless granted institution-wide scope.
- Parents can view only students with an active, verified guardian link.
- Students cannot see draft or unapproved results.
- Platform support access to tenant data must be exceptional, time-limited, and audited.

## Separation of Duties

High-risk workflows should not depend on one unchecked action.

| Workflow | Recommended separation |
| --- | --- |
| Admission | Officer verifies; authorized approver accepts |
| Attendance correction | Faculty requests; advisor or HOD approves |
| Marks | Faculty enters; verifier checks; controller publishes |
| Fee concession | Accountant proposes or records; authorized manager approves |
| Refund | Authorized user requests; separate approver confirms |
| Payroll | HR prepares; authorized management approves |
| Result changes after publication | Controlled reopening, reason, approval, and audit entry |

Small colleges may assign several roles to one person, but the system should still record which authority was used for each action.

## Account Lifecycle

1. An authorized administrator invites or creates a user.
2. The user verifies identity and sets credentials.
3. The administrator assigns one or more tenant memberships and roles.
4. Access is narrowed by campus, department, or operational assignment where needed.
5. Role changes and temporary access are recorded.
6. Leaving users are disabled; historical actions remain attributed to them.

User accounts should not be deleted merely because an employee or student leaves.

## Security Rules

- Never accept a college identifier from the browser as proof of access.
- Determine the active tenant from the authenticated membership.
- Require stronger authentication for privileged users where possible.
- Rate-limit login and sensitive public operations.
- Store passwords with a modern password-hashing algorithm.
- Expire sessions after appropriate inactivity and support forced logout.
- Audit logins, exports, approvals, publications, reversals, and permission changes.
- Mask sensitive personal and financial fields from users who do not need them.
- Treat exports as sensitive actions and record who generated them.
