# Providers and Background Jobs

**Status:** Planned as Slice 5; existing notice delivery-job records and manual reconciliation/report schedule sources are implemented locally, while provider adapters and worker execution remain pending.

## Purpose

Deliver external email/SMS communication, membership invitations, payment callbacks, and scheduled report exports through durable, provider-independent jobs without exposing provider credentials or losing retry history.

## Roles

- College Administrator: inspect invitation delivery and retry authorized failures.
- Communication Manager: inspect notice delivery attempts and retry failed channel jobs.
- Accountant/Cashier: inspect authenticated gateway callbacks and reconciliation outcomes.
- Leadership: configure report schedules and inspect delivery history.
- Background worker: claim due jobs through a restricted service identity and record immutable attempts.

## Delivery Order

1. Introduce a small provider interface and development recording provider.
2. Queue membership invitation email delivery transactionally without returning plaintext tokens to normal UI responses.
3. Process communication and invitation jobs with immutable attempts, bounded retries, and exponential backoff.
4. Add authenticated, provider-specific payment callback adapters with signature verification and independent callback idempotency.
5. Convert validated callbacks into existing idempotent Payment operations and retain reconciliation/audit links.
6. Queue due report schedules, regenerate scoped CSV exports, and deliver them through the email provider.
7. Add operator status screens for pending, sent, failed, next-attempt, and provider-reference outcomes.
8. Add worker health, stale-job recovery, quotas, metrics, and deployment service definitions.

## Architecture Rules

- Provider integrations remain behind small interfaces; domain services do not import provider SDKs directly.
- Secrets come only from environment or an approved secret store and never enter source, browser state, job payloads, logs, or audit details.
- Jobs are created in the same transaction as the authoritative command that requires the external effect.
- Callback receipt idempotency is separate from Payment command idempotency.
- Provider callbacks verify signatures and authoritative amount, currency, reference, and target records before changing financial state.
- Every retry creates an immutable attempt record. Operators may retry safely but may not overwrite history.
- Workers claim jobs atomically, recover stale processing leases, cap retries, and use deterministic backoff.
- Tenant context is set before every tenant-owned job query; forced RLS remains enabled for worker access.
- Development providers record payload metadata locally without contacting external services.

## Planned Data

- InvitationDeliveryJob and InvitationDeliveryAttempt, or a generalized delivery job that can safely reference invitation effects without weakening existing notice constraints.
- PaymentCallback with provider, external event ID, payload digest, verification state, processing state, linked payment, error detail, and timestamps.
- ReportDeliveryJob and ReportDeliveryAttempt linked to ReportSchedule and generated ReportExport records.
- ProviderHealthEvent or equivalent operational metrics only if required after the first worker is exercised.

## Planned APIs and Commands

- Invitation creation returns delivery status/reference rather than a plaintext token after provider delivery is enabled.
- Protected invitation delivery history and retry operations.
- Public provider-specific webhook endpoints that resolve tenant through configured provider account metadata, verify signatures, and return replay-safe acknowledgement.
- Protected callback inspection and reconciliation endpoints.
- Protected report delivery history, pause/resume, and send-now operations.
- Idempotent worker commands that support `--once`, bounded batch limits, and dry-run inspection.

## Validation Gate

- Replaying an invitation, callback, or report job does not duplicate delivery, payment, allocation, export, or receipt records.
- Invalid callback signatures and mismatched amount/currency/reference data cannot mutate financial records.
- Failed provider calls remain visible, retryable, and attributable without logging secrets or private payload content.
- Cross-tenant job, attempt, callback, export, and provider-reference reads are blocked by service scope and forced RLS.
- A due report schedule creates one scoped CSV export and one auditable delivery outcome.
- Worker restart recovers stale jobs without double-processing.
- The local development provider makes the complete workflow testable without external credentials.

## Deferred Provider Choices

Production email, SMS, payment, and scheduling infrastructure vendors are not selected in source code. Vendor onboarding, production credentials, sender/domain verification, callback registration, quotas, and deployment services require explicit environment approval and remain separate from local implementation status.
