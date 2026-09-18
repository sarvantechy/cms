# Admissions

**Status:** Staff operations and Applicant self-service are implemented locally with PostgreSQL persistence, forced RLS, private uploads, and interactive browser validation.

## Purpose
Move enquiries through application, verification, selection, offer, acceptance, and transactional student conversion.

## Roles
- Admission Officer: manage and verify applications.
- Approver: approve selection and offers.
- Applicant: maintain own application and documents.

## Workflow
1. Capture enquiry and intake campaign.
2. Submit configurable application and documents.
3. Verify eligibility and documents.
4. Rank against seats, quota, and merit rules.
5. Issue and accept an offer.
6. Convert once to person, student, enrollment, and initial invoice records.

## Core Rules
- Verify, approve, and convert are distinct auditable permissions.
- Conversion is idempotent and never duplicates identity.
- Seat counts derive from accepted workflow records.

## Data
Enquiry, IntakeCampaign, Application, ApplicationDocument, Verification, SeatRule, Selection, Offer, and ConversionRecord.

## Current UI Behavior
`/portal/admissions` provides source-backed creation forms for enquiries, campaigns, applicants,
applications, document metadata, category seat pools, and offers. Staff can manage enquiry,
application, document-verification, and offer lifecycles through only the transitions allowed by
the backend. The workspace also presents remaining seat capacity, application details, append-only
history, validation failures, authenticated private-document downloads, and idempotent
accepted-application conversion results.

Staff creation forms and application detail are full-width in-workspace screens. Opening a form or
record hides the admissions list until Cancel, Close, or Back is selected; no application popup or
transparent overlay is used.

`/portal/my-application` binds an authenticated Applicant membership to exactly one tenant-owned
Applicant record. The Applicant can edit profile and statement data while the application is a
draft, upload validated PDF/JPEG/PNG documents up to 5 MiB, submit once, track verification state,
and download only their own private media. Admissions staff use the same source application and
verification workflow. Private downloads are authorized per request and return `private, no-store`
with `Vary: Authorization` so browser caches cannot reuse one actor's response for another actor.

## Remaining Release Work
The current private-media provider stores opaque objects on the local filesystem for development.
A production object-storage provider, retention execution, malware scanning, external
notifications, and the deferred formal test suites remain release work. Legacy externally managed
document URLs remain supported for existing metadata records.

## Local Validation
- Alembic upgraded to `f8cd51ae2d03`; migration drift is clean and Applicant-access, media, and
	application-document RLS is forced.
- The production FastAPI application exposes 219 OpenAPI paths, including five Applicant
	self-service routes and authenticated Applicant/staff media downloads.
- Frontend TypeScript production build and focused backend Ruff pass.
- Interactive Playwright created a PostgreSQL enquiry, reloaded it, transitioned it from `new` to
	`contacted`, and verified source-backed campaign, applicant, academic-year, and programme choices.
- Browser validation also showed 59 of 60 seats available and one submitted document without API
	or rendered-page errors after the transition response fix.
- Interactive Playwright validated draft editing, magic-byte rejection, PDF upload, submission,
	reload persistence, read-only post-submit behavior, staff visibility, authenticated download,
	390 px layout, and Arts/Law isolation. A same-URL two-token check found and fixed private response
	cache reuse; Arts now receives 200 and Law receives 404.
- Repeated two-tenant `--seed-demo` onboarding preserved the submitted application and uploaded
	media instead of resetting user-modified workflow state.
- On 16 September 2026, interactive Playwright opened the submitted portal application through the
	College Administrator workspace, rendered its media-backed Download action, and received the
	authorized PDF with `private, no-store` cache control.

## Acceptance Criteria
- One application reaches accepted offer through explicit transitions.
- Concurrent acceptance cannot oversubscribe controlled seats.
- Conversion can be safely retried without duplicate students.
