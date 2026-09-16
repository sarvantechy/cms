# Placement

**Status:** Planned and hidden from current navigation.

## Purpose
Manage employers, opportunities, eligibility, consent, drives, selection stages, outcomes, and offers.

## Roles
- Placement Officer: manage employers, drives, stages, and outcomes.
- Student: maintain consent and apply to eligible opportunities.
- Leadership: view authorized outcome reports.

## Workflow
1. Register employer and opportunity.
2. Define versioned eligibility rules.
3. Resolve eligible consenting students.
4. Track application, test, interview, outcome, and offer stages.
5. Verify outcomes and report placement measures.

## Core Rules
- Eligibility is reproducible from effective student data.
- Sensitive student data requires consent and scoped access.
- Outcomes preserve stage history.

## Data
Employer, Contact, Opportunity, EligibilityRule, Consent, Application, DriveStage, StageOutcome, and Offer.

## Current UI Behavior
No placement screen exists.

## Production Completion
Implement employer CRM, opportunity builder, eligibility preview, student portal, stage tracking, offer evidence, and reports.

## Acceptance Criteria
- Ineligible or nonconsenting students are not disclosed.
- Stage transitions are explicit and audited.
- Reports reconcile to verified outcomes.
