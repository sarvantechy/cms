# Fees and Payments

**Status:** Implemented locally for College Administrator operations with PostgreSQL persistence, forced RLS, immutable financial source records, protected APIs, approval workflows, audit events, and source-backed UI controls.

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
`/portal/fees` provides source-backed controls for fee heads and published plans, enrollment-linked invoices, idempotent allocated payments, receipts, compensating reversals, concession and refund request/review, cashier opening and variance-aware closing, gateway settlement reconciliation, and selectable student ledgers. Metrics and ledger balances are derived from invoice lines, approved concessions, and signed payment allocations.

## Production Completion
The College Administrator finance workflow and permission-scoped Student, Guardian, and Accountant workspaces are complete locally. Printable receipt documents, provider callback adapters, and formal automated coverage remain release work. No deployment claim is made.

## Local Validation
- Alembic upgraded PostgreSQL to `a5b6c7d8e9f0`; metadata drift passed.
- Focused Ruff validation passed for the complete fees domain and production OpenAPI generated 152 paths.
- The web production build passed.
- Interactive Playwright loaded every finance source endpoint, verified desktop and 390px rendering without horizontal overflow, issued receipt `RCT-INDUS-ARTS-SCIENCE-0001` through the UI, and confirmed balances remained unchanged.

## Acceptance Criteria
- Every balance reconciles to immutable transactions.
- Duplicate gateway callbacks create no duplicate payment.
- Refund approval is separate from request and fully audited.
