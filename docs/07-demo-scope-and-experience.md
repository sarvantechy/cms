# Demo Scope and Experience

## Purpose of the Demo

The first demo will be a small but real multi-tenant college management web application. It will show how connected college operations work without attempting to build every planned module at once.

The demo must answer these questions clearly:

1. Can two different colleges use one application without seeing each other's data?
2. Can an administrator configure basic academic information and manage students?
3. Can faculty record attendance for their assigned classes?
4. Can an accountant record student fees and show pending balances?
5. Can students see their own timetable, attendance, fee status, and notices?
6. Can management view useful totals based on real records?

## Demo Tenants

The demo will contain two separate college tenants. Their records, users, branding, academic structures, and operational data will be isolated.

### Tenant A: INDUS ARTS & SCIENCE INTERNATIONAL COLLEGE

Example academic structure:

- Department of Computer Science
- Department of Commerce
- B.Sc. Computer Science
- B.Com.
- Semester pattern
- Sections such as B.Sc. CS I-A and B.Com. I-A

Example subjects:

- Programming Fundamentals
- Digital Principles
- Financial Accounting
- Business Economics

### Tenant B: INDUS LAW COLLEGE

Example academic structure:

- Department of Legal Studies
- Three-year LL.B.
- Five-year B.A. LL.B.
- Semester pattern
- Sections such as LL.B. I-A and B.A. LL.B. I-A

Example subjects:

- Legal Methods
- Law of Contracts
- Constitutional Law
- Political Science for Law

The two tenants will have visibly different names, logos or initials, accent colors, programs, subjects, users, and records. This makes tenant separation easy to demonstrate.

## Demo Roles

| Role | What the user can do in the demo |
| --- | --- |
| College administrator | Manage the active college's academic setup, staff, students, notices, and dashboard |
| Faculty | View assigned classes, timetable, student list, and record attendance |
| Head of department | Review department students, faculty workload, attendance, and academic progress |
| Accountant | View student fee accounts, record payments, issue receipts, and review pending fees |
| Student | View only their own profile, timetable, attendance summary, fees, receipts, and notices |
| Parent | View the linked student's attendance, fees, timetable, and college notices |
| Event coordinator | Manage campus events, participant lists, announcements, and certificates |

A person with access to more than one tenant must explicitly switch the active college. The active college name and branding must remain visible in the application shell.

## Modules Included in the Demo

### 0. Public College Website

- Institution-led homepage for INDUS ARTS & SCIENCE INTERNATIONAL COLLEGE
- Admissions announcement and program discovery
- Academic programs and institutional strengths
- News, upcoming events, and campus-life sections
- College location, address, and contact email
- Responsive public navigation and portal access
- Image-led campus presentation using licensed remote photography

The public homepage is an original INDUS design informed by common higher-education website patterns. It does not copy another institution's branding or content.

### 1. Authentication and Tenant Access

- Login with seeded demo accounts
- Sample login selector for Administrator, Student, Parent, Faculty, HOD, and Event Coordinator
- Visible temporary demo credentials using synthetic accounts only
- Authenticated actor context containing account, tenant membership, role, and permissions
- Tenant switcher only for users with multiple memberships
- Role-aware navigation
- Required password-change support in the data model, but not required for the scripted demo
- Sign out
- Tenant-branded application shell

### 2. College Setup

- College profile and branding
- One campus per demo tenant
- One active academic year
- Departments
- Programs
- Terms or semesters
- Batches and sections
- Subjects
- Faculty-to-subject and section assignment

The demo will use seeded master data. Administrators will be able to view all setup records and edit a deliberately small subset such as college contact details, section advisor, and subject assignment.

### 3. Student Directory and Profile

- Searchable and filterable student matrix
- Student name, registration number, program, batch, section, mobile, email, and status
- Student profile with guardian and contact details
- Academic enrollment summary
- Attendance summary
- Fee account summary
- Create a student through a simplified intake form
- Edit permitted profile fields

The simplified intake represents an already approved admission. Full enquiry, application, document verification, merit, quota, offer, and acceptance workflows are deferred.

### 4. Faculty Directory and Assignment

- Searchable faculty list
- Faculty profile and department
- Assigned subjects and sections
- Weekly timetable view
- Faculty dashboard showing today's classes and attendance tasks

Complete HR, recruitment, leave, payroll, appraisal, and employee document management are not part of this demo.

### 5. Timetable

- Weekly section timetable
- Faculty timetable
- Day, period, subject, section, room, and faculty
- Administrator view of timetable data
- Student view of their section timetable

The first demo will use seeded timetable entries. A full timetable builder, automated generation, substitutions, and conflict-resolution interface are deferred.

### 6. Student Attendance

- Faculty sees only assigned class sessions
- Faculty records present, absent, late, or on-duty status
- Attendance submission prevents accidental duplicate records
- Student profile shows overall and subject-wise percentage
- Administrator dashboard shows today's attendance and shortage count
- Attendance history can be filtered by date and section

Attendance correction approval, biometric import, parent alerts, and faculty attendance are deferred.

### 7. Fees and Receipts

- Fee heads and one fee plan per example program
- Student invoice and due amount
- Scholarship or concession value already applied to selected demo students
- Accountant records an offline payment
- Receipt number and printable receipt view
- Student ledger showing charges and payments
- Pending-fee list and dashboard total

Online payment gateway, refunds, reversals, cashier closing, reconciliation, general ledger, expenses, and procurement are deferred.

### 8. Notices and Communication

- College-wide and targeted notices
- Audience by role, department, program, or section
- Publish date and expiry date
- Administrator creates and publishes a notice
- Student and faculty dashboards show relevant active notices

Email, SMS, push notifications, delivery retries, and acknowledgement tracking are deferred.

### 9. Role-Based Dashboards

College administrator dashboard:

- Total active students
- New student intakes
- Departments and programs
- Today's attendance percentage
- Students below the attendance threshold
- Fees collected and pending
- Recent notices
- Quick links to common tasks

Faculty dashboard:

- Today's classes
- Attendance awaiting entry
- Assigned subjects and sections
- Recent notices

Accountant dashboard:

- Today's collection
- Total pending amount
- Students with pending fees
- Recent receipts

Student dashboard:

- Personal and enrollment summary
- Today's classes
- Overall attendance and subject-wise attendance
- Fee due and recent receipts
- Relevant notices

Dashboards must calculate their values from seeded and entered records. They must not display hard-coded totals.

## Navigation and Visual Direction

The web application will follow the established Himalayan Access interaction pattern while using college-specific content:

- Compact left sidebar on desktop and drawer navigation on mobile
- Grouped navigation with Lucide icons
- Tenant identity and logged-in user shown in the sidebar
- Dense operational tables designed for repeated daily use
- Clear page title, context, filters, and primary action
- Explicit loading, empty, error, and retry states
- Responsive mobile layouts with no overlapping controls
- Accessible form labels, keyboard navigation, focus states, and color contrast
- Theme variables rather than hard-coded component colors

Navigation groups for the demo:

```text
Overview
  Dashboard
  Notices

People
  Students
  Faculty

Academics
  Departments and Programs
  Subjects and Sections
  Timetable
  Attendance

Finance
  Student Fees
  Receipts

Administration
  College Settings
  Users and Access
```

Users see only groups and pages allowed by their permissions.

## Data Volume for the Demo

Each tenant should contain enough data to make lists, filters, and dashboards believable:

| Record type | Per tenant target |
| --- | --- |
| Campuses | 1 |
| Departments | 2 |
| Programs | 2 |
| Sections | 2-4 |
| Subjects | 4-8 |
| Faculty | 4-6 |
| Students | 20-30 |
| Timetable entries | One representative week |
| Attendance history | At least 10 class days |
| Student invoices | One per student |
| Payments and receipts | Mixed paid, partial, and unpaid examples |
| Notices | 4-6 active and expired examples |

All people and contact details must be clearly synthetic.

## Demo Boundaries

The following modules will not be implemented in the first demo:

- Full admissions and quota processing
- Examinations, marks, grades, and results
- Real email/password authentication and password recovery during the visual demo increment
- Library
- Hostel and mess
- Transport
- Placement
- Clubs, sports, and activities
- Complete HR, leave, and payroll
- Full institutional accounting
- Online payment gateway
- Email, SMS, and push delivery
- Accreditation and university integrations
- Advanced analytics and scheduled reports

These remain in the overall product scope and will be selected one by one after stakeholder feedback on the demo.

## Demo Success Criteria

The demo is ready to show when:

- Both colleges can sign in with their own seeded users.
- College branding and navigation change with the active tenant.
- Cross-tenant API access is rejected even when identifiers are manually changed.
- An administrator can find a student and view connected academic, attendance, and fee information.
- A faculty user can record attendance only for an assigned class.
- Attendance percentages update from the recorded session.
- An accountant can record a payment and produce a receipt.
- The student's fee balance and receipt history update correctly.
- An administrator can publish a targeted notice that appears to the intended users only.
- All role dashboards show real values from the database.
- Core desktop and mobile journeys pass automated browser tests.
