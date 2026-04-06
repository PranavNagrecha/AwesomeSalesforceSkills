# Quote PDF Customization — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `quote-pdf-customization`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Quoting object in use:** Standard `Quote` + `QuoteLineItem` / CPQ `SBQQ__Quote__c` + `SBQQ__QuoteLine__c` / other custom object
- **Delivery mechanism:** Inline browser render / Emailed attachment / Stored as ContentDocument on Quote / All of the above
- **Static resource assets available:** Logo name: ___ / CSS file name: ___ / Font file for non-Latin scripts: ___
- **Locale/language requirements:** Single language / Multi-language — list locales:
- **Conditional sections needed:** (e.g., discount table, payment terms, multi-currency totals)
- **Known constraints:** Governor limits concern? Large line-item volumes? Batch generation required?

## Approach

Which pattern from SKILL.md applies?

- [ ] **Pattern 1 — Standard Controller Extension** (standard Quote, branded layout, conditional sections)
- [ ] **Pattern 2 — Programmatic PDF Attachment via Queueable** (auto-attach on stage change or batch)
- [ ] **Pattern 3 — Multi-Language Quote PDF** (Translation Workbench + `<apex:page language=...>`)
- [ ] Custom combination — describe:

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] `<apex:page>` includes `renderAs="pdf" showHeader="false" sidebar="false"`
- [ ] No `<script>` tags present in the VF page — all logic is server-side Apex
- [ ] SOQL uses `WITH USER_MODE` or explicit FLS checks; no string-concatenated query predicates
- [ ] Logo and images referenced by absolute URL or embedded as base64 data URIs
- [ ] Layout uses CSS 2.1 (tables/floats) — no Flexbox, Grid, or CSS custom properties
- [ ] Conditional sections use `rendered="{!property}"` — no CSS `display:none` hiding sensitive data
- [ ] If programmatic: `getContentAsPDF()` is called from a Queueable or Future method implementing `Database.AllowsCallouts`
- [ ] `getContentAsPDF()` return value checked for null before inserting ContentVersion
- [ ] PDF tested with a non-admin user to verify record access and FLS compliance

## Delivery Artifacts

List the files being produced for this task:

| File | Type | Purpose |
|---|---|---|
| `QuotePdf.page` | Visualforce Page | Main PDF template with conditional sections |
| `QuotePdfController.cls` | Apex Class | Controller/extension with FLS-safe SOQL and section toggles |
| `QuotePdfStyles.css` (Static Resource) | CSS | Table-based layout, font declarations, logo as base64 |
| `QuotePdfAttachmentJob.cls` | Apex Queueable | Async PDF generation and ContentVersion attachment (if needed) |

## Notes

Record any deviations from the standard pattern and why.

- CPQ deviation (if applicable): Using `SBQQ__QuoteLine__c` instead of `QuoteLineItem` because ___
- Logo approach chosen: Absolute URL / Base64 data URI — reason: ___
- Multi-language approach: Custom Labels + Translation Workbench / Hardcoded per-language template — reason: ___
- Scope size for batch generation (should be 1): ___
