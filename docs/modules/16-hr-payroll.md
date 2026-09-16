# HR, Leave, and Payroll

**Status:** Planned and hidden from current navigation.

## Purpose
Manage employee lifecycle, confidential records, postings, leave, salary structures, payroll, statutory deductions, payslips, and appraisal.

## Roles
- HR/Payroll Officer: manage authorized employee and payroll records.
- Approver: approve leave and payroll runs.
- Employee: view own profile, leave, and payslips.

## Workflow
1. Recruit and onboard employee with controlled documents.
2. Track postings, probation, transfer, appraisal, and exit.
3. Configure leave policies and balances.
4. Version salary structures and deductions.
5. Prepare, approve, publish, and reconcile payroll.

## Core Rules
- Confidential fields use stricter permissions than general faculty records.
- Payroll preparation and approval are separate authorities.
- Published payroll changes use adjustment runs.

## Data
Employee, EmploymentHistory, EmployeeDocument, LeavePolicy, LeaveBalance, LeaveRequest, SalaryStructure, PayrollRun, PayrollLine, Deduction, and Payslip.

## Current UI Behavior
No HR or payroll screen exists.

## Production Completion
Build employee directory/profile, confidential document controls, leave self-service, approval queues, payroll workbench, payslips, and reports.

## Acceptance Criteria
- Unauthorized roles cannot infer compensation or confidential records.
- Payroll totals reconcile to lines, deductions, and payments.
- Published runs are immutable and attributable.
