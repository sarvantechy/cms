# Public Institution Site

**Status:** Implemented locally as a static Arts & Science college site; CMS-backed content and Law College public routing are pending.

## Purpose
Present institution identity, programs, admissions, events, campus life, contact information, and portal entry to the public.

## Roles
- Public visitor: browse published content.
- Authorized publisher: manage approved tenant content in a future CMS workflow.

## Workflow
1. Resolve institution host or public slug.
2. Render only approved, published content.
3. Link admissions enquiries and portal entry.
4. Preserve accessible responsive navigation and media.

## Core Rules
- Public queries never expose tenant-owned draft or operational records.
- Content publication is explicit and attributable.
- Images have accessible alternatives and stable responsive dimensions.

## Data
Tenant branding today; future PublicPage, ContentBlock, MediaAsset, ProgramSummary, PublicEvent, and Publication records.

## Current UI Behavior
`/` renders a responsive Arts & Science site with navigation, programs, admissions, events, campus life, maps, and portal login. Content is source-coded and not tenant-selectable.

## Production Completion
Add host/slug tenant resolution, content management, preview/publish workflow, Law College public site, SEO metadata, and backend media storage.

## Acceptance Criteria
- Only published content is public.
- Each college resolves to its own branding and content.
- Desktop and mobile navigation remain usable with no overflow or overlap.
