# Fees and Payments

**Status:** Implemented locally for College Administrator and Accountant operations with PostgreSQL persistence, forced RLS, immutable financial source records, protected APIs, approval workflows, audit events, source-backed UI controls, and printable payment receipts.

## Purpose
Manage fee plans, invoices, concessions, payments, allocations, receipts, cashier closing, reversals, refunds, and reconciliation.

## Roles
- Accountant/Cashier: invoice, collect, allocate, and close cashier sessions.
- Approver: approve concessions, reversals, and refunds.
- Student/Guardian: view authorized ledger, dues, and receipts.

## Workflow
1. Define fee heads, plans, instalments, and applicability.
2. Generate immutable invoices.
3. Propose and approve concessions or scholarships.
4. Collect idempotent payment and allocate to invoice lines.
5. Issue receipt and reconcile cashier or gateway settlement.
6. Reverse or refund through compensating transactions.

## Core Rules
- Financial source transactions are never deleted or overwritten.
- Balances derive from invoices, allocations, reversals, and refunds.
- Payment idempotency prevents duplicate collection.

## Data
FeeHead, FeePlan, Invoice, InvoiceLine, Concession, Payment, PaymentAllocation, Receipt, CashierSession, Reversal, Refund, and Reconciliation.

## Current UI Behavior
`/portal/fees` provides source-backed controls for fee heads and published plans, enrollment-linked invoices, idempotent allocated payments, receipts, compensating reversals, concession and refund request/review, cashier opening and variance-aware closing, gateway settlement reconciliation, and selectable student ledgers. Operators can issue a receipt idempotently and open a responsive print document. Student and Guardian workspaces list only their scoped invoices and payments and can print only previously issued receipts. Metrics, ledger balances, and receipt totals are derived from invoice lines, approved concessions, and signed payment allocations.

Printable receipts open as opaque document screens in the workspace rather than popups. The Fees
workspace is hidden while the document is active, and print media still emits only the receipt.

## Production Completion
The College Administrator finance workflow and permission-scoped Student, Guardian, and Accountant workspaces are complete locally. Printable payment receipts are derived at read time from the immutable receipt, payment, allocation, invoice, Student, tenant, and college-setting records; no duplicate document facts are stored. Provider callback adapters and formal automated coverage remain release work. No deployment claim is made.

## Local Validation
- Alembic remains at `c91e4a7d2b60`; no receipt schema migration was required because immutable receipt issuance metadata already exists.
- Focused Ruff validation passed for the fees domain, shared Student-scope resolver, and Accountant role catalogue; the production application now exposes 219 paths.
- The web production build passed.
- API validation confirmed idempotent issuance replay, a source-derived `INR 30,000.00` total matching its allocation, Student and Guardian access, unrelated-Student and cross-tenant 404 responses, and restored institution-scoped Administrator reads.
- Interactive Playwright loaded the Accountant finance workspace, issued and opened receipt `RCT-INDUS-ARTS-SCIENCE-0001`, verified the Student read-only receipt journey, and confirmed desktop, 390px, and print-media rendering without horizontal overflow or application chrome in printed output.

## Acceptance Criteria
- Every balance reconciles to immutable transactions.
- Duplicate gateway callbacks create no duplicate payment.
- Refund approval is separate from request and fully audited.
