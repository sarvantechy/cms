# Library

**Status:** Planned and hidden from current navigation.

## Purpose
Manage catalogue, copies, shelves, circulation, reservations, fines, losses, acquisitions, and stock verification.

## Roles
- Librarian: manage catalogue and circulation.
- Student and faculty: search, reserve, and view own loans.

## Workflow
1. Catalogue titles and physical/digital copies.
2. Barcode and place copies.
3. Issue, renew, return, reserve, or mark loss.
4. Calculate policy-based fines and approved waivers.
5. Acquire stock and perform verification.

## Core Rules
- Copy availability derives from circulation state.
- Fine adjustments are compensating, attributable records.
- Borrowers see only their own account.

## Data
CatalogueTitle, Author, Copy, Shelf, Loan, Reservation, Fine, Acquisition, and StockVerification.

## Current UI Behavior
No library screen exists.

## Production Completion
Implement librarian workbench, public catalogue, circulation desk, borrower account, policies, stock workflows, and reports.

## Acceptance Criteria
- A copy cannot be concurrently issued twice.
- Reservations and renewals follow effective policy.
- Inventory and circulation reconcile by copy.
