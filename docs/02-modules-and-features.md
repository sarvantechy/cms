# Modules and Features

This document records the complete expected scope. A feature appearing here does not mean it belongs in the first release; delivery order is defined in the [Implementation Roadmap](06-implementation-roadmap.md).

## 1. Institution and Platform Administration

- College tenant onboarding and status
- Campus and branch management
- College profile, logo, address, contacts, and affiliation details
- Academic years and terms
- Institution numbering formats for applications, registrations, rolls, receipts, and certificates
- Configurable time zone, currency, locale, grading, and attendance rules
- Enabled modules and subscription plan
- User accounts, college memberships, roles, and permissions
- Audit logs, login history, and security settings
- Data import, export, retention, and tenant closure

## 2. Student Management

- Student profile and admission details
- Student documents
- Course allocation
- Registration and roll numbers
- Competition and participation certificates
- Guardians, addresses, emergency contacts, and communication preferences
- Student photograph and identity information
- Program, batch, section, term, and subject enrollment
- Student status history: provisional, active, on leave, detained, discontinued, transferred, graduated, or alumni
- Promotion, section transfer, program transfer, and readmission
- Mentoring, discipline, grievance, and service-request records
- Bonafide, conduct, transfer, and other certificate requests
- Alumni conversion without deleting academic history

## 3. Admission Management

- Applications and enquiries
- Admission approval
- Course and quota allocation
- Admission campaigns, intake periods, and seat capacity
- Applicant account and application fee
- Configurable application forms
- Document checklist and verification
- Entrance score, merit rules, category, and reservation processing
- Rank list, selection list, and waiting list
- Admission offer, expiry, acceptance, and rejection
- Initial fee payment and provisional admission
- Cancellation, seat release, refund, and applicant-to-student conversion
- Complete status and communication history

## 4. Academic Management

- Departments, courses, and subjects
- Faculty allocation
- Timetable and academic calendar
- Lesson plans and syllabus tracking
- Programs, qualifications, regulation versions, and curricula
- Batches, semesters or terms, sections, and student groups
- Credits, subject types, prerequisites, electives, and optional subjects
- Subject offerings for each academic term
- Student subject registration
- Classroom, laboratory, and resource allocation
- Faculty workload and timetable conflict detection
- Class substitutions and timetable changes
- Promotion and progression rules
- Learning materials and assignments at a basic level

## 5. Attendance and Leave

- Student and faculty attendance
- Period-wise attendance
- Leave management
- Attendance percentages
- Parent notifications
- Attendance registers generated from the timetable
- Present, absent, late, on duty, excused, and cancelled-class statuses
- Faculty submission and locking
- Correction requests and approvals
- Daily, subject-wise, and term-wise summaries
- Shortage thresholds and exam eligibility
- Student, staff, and parent notification history
- Optional biometric import with error reconciliation

## 6. Examination and Results

- Exam schedules
- Internal, assignment, seminar, practical, and external marks
- Result processing, grades, and rank lists
- Assessment schemes and weightages by curriculum version
- Exam sessions, registration, eligibility, and hall tickets
- Exam rooms, seating, invigilators, and attendance
- Marks entry, verification, locking, moderation, and approval
- Pass rules, grace rules, credits, GPA, and CGPA
- Result publication and student access
- Withheld, absent, malpractice, and incomplete outcomes
- Revaluation, retotalling, supplementary exams, and arrears
- Grade cards, consolidated transcripts, and certificate verification
- Privacy-aware rank rules and tie handling

## 7. Fees and Finance

- Fee structures and student fee collection
- Online and offline payments
- Receipt generation
- Pending fees
- Scholarships and concessions
- Finance reports
- Fee heads, plans, due dates, instalments, and late fees
- Student invoices and ledger
- Concession, scholarship, sponsor, and approval workflows
- Payment allocation across invoices
- Cash, card, bank, cheque, and payment-gateway methods
- Gateway callbacks, duplicate-payment protection, and reconciliation
- Receipt cancellation, refunds, reversals, and credit notes
- Cashier closing and collection summaries
- Optional general ledger, expenses, vendors, procurement, and bank reconciliation

Financial transactions must not be silently edited or deleted. Corrections should use controlled reversals with an audit history.

## 8. Faculty, Staff, HR, and Payroll

- Faculty profile, attendance, leave, payroll, work allocation, and performance
- Employee database and recruitment
- College details
- Separate employee identity, employment, and teaching-assignment records
- Qualifications, experience, department postings, and staff documents
- Recruitment, offer, onboarding, probation, confirmation, transfer, and exit
- Leave types, balances, requests, approvals, and holiday calendars
- Workload and substitutions
- Salary structures, payroll runs, earnings, deductions, payslips, and statutory reporting
- Goals, appraisals, training, and disciplinary records
- Separation of confidential HR access from general academic access

## 9. Communication and Portals

- Circulars, announcements, events, notices, and university information
- Email or courier updates
- Student portal
- Student, parent, faculty, staff, and administrator dashboards
- Targeting by campus, department, program, batch, section, role, or individual
- In-app, email, SMS, and optional push notifications
- Templates, scheduling, delivery status, retry, and failure history
- Read acknowledgement for important notices
- Notification preferences and emergency communication
- Portal access to relevant timetable, attendance, fees, results, requests, and documents

The student portal is a secure view of other modules, not a separate duplicate database.

## 10. Library Management

- Book titles, authors, publishers, categories, and physical copies
- Accession numbers, barcodes, shelves, and stock verification
- Search and availability
- Member rules for students and staff
- Issue, return, renewal, reservation, and circulation history
- Overdue fines, payment linkage, lost books, and damaged books
- Library visit history where required
- Acquisition, vendor, and inventory reports

## 11. Transport Management

- Vehicles, insurance, permits, maintenance, and capacity
- Routes, stops, schedules, and fares
- Drivers and support staff
- Student and staff route allocation with effective dates
- Transport fee linkage
- Capacity and allocation reports
- Optional GPS and live tracking integration

## 12. Hostel and Mess Management

- Hostel buildings, floors, rooms, beds, and capacity
- Student allocation, transfer, vacation, and checkout
- Warden and caretaker assignments
- Hostel attendance, visitor, incident, and maintenance records
- Mess plans and vegetarian/non-vegetarian preferences
- Hostel and mess fee linkage
- Room occupancy and availability reports

## 13. Placement Management

- Company and recruiter registration
- Job, internship, and training opportunities
- Eligibility rules based on program, marks, arrears, and other criteria
- Eligible-student calculation and consent
- Student applications and placement-drive stages
- Tests, assignments, interviews, results, and offers
- Offer acceptance and placement history
- Company, program, batch, and outcome reports

## 14. Events and Activities

- College events and calendars
- NSS, NCC, clubs, cultural activities, and sports
- Registration, selection, team allocation, and attendance
- Student participation and achievement records
- Approval, venue, budget, and expense tracking
- Certificates with verifiable identifiers
- Activity points and reports where applicable

## 15. Reports and Dashboards

- Totals and statistics for students, admissions, attendance, fees, examinations, faculty, departments, and placements
- Role-specific dashboards
- Filters by tenant, campus, academic year, department, program, batch, and term
- Drill-down from totals to source records
- Downloadable and printable reports where appropriate
- Scheduled reports and controlled distribution
- Statutory, university, accreditation, NAAC, and NBA formats where configured
- Data freshness indicators and calculation definitions

Reports must derive from operational records. Manually maintained totals will eventually disagree with actual transactions.

## Additional Cross-Cutting Capabilities

These are not standalone college departments, but every module depends on them:

- Search and record history
- File and document storage
- Configurable approvals
- Comments and internal notes
- Audit logging
- Imports, duplicate detection, and validation
- Exports and scheduled jobs
- Notification delivery
- Privacy, consent, and retention
- API and external integrations
- Accessible, responsive user interfaces
