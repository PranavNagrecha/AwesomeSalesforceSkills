# PDF Generation Patterns — Work Template

Use this template when working on a PDF generation task in Salesforce.

## Scope

**Skill:** `apex/pdf-generation-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer the Before Starting questions from SKILL.md before writing any code:

- **Source record type and Id:** (e.g., Opportunity, Account, custom object `Invoice__c`)
- **Delivery mechanism:** browser download | ContentVersion attachment | email attachment
- **LWC involvement:** yes / no — if yes, which component triggers the PDF
- **Async or sync:** triggered automatically (async Queueable required) / triggered by user (sync VF page OK)
- **Design assets:** logo URL / static resource name / base64 available?
- **Known constraints:** (callout limits, record count, special CSS requirements)

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1 — On-Demand PDF rendered directly in the browser (VF page with renderAs='pdf')
- [ ] Pattern 2 — Programmatic PDF attached via Queueable (ContentVersion + ContentDocumentLink)
- [ ] Pattern 3 — LWC-initiated PDF (NavigationMixin to VF URL or headless Queueable via @AuraEnabled)

**Why this pattern:** (explain the choice based on delivery mechanism and trigger)

## Delivery Artifacts

List the files being produced for this task:

| File | Type | Purpose |
|---|---|---|
| `YourPdfPage.page` | Visualforce Page | PDF template with server-side data binding |
| `YourPdfController.cls` | Apex Class | Controller loading all data, building logo URL, computing conditional flags |
| `YourPdfAttachmentJob.cls` | Apex Queueable | Calls getContentAsPDF(), null-checks, inserts ContentVersion + ContentDocumentLink |
| `YourPdfTriggerHandler.cls` | Apex Trigger Handler | Enqueues YourPdfAttachmentJob on record state change (if applicable) |

## Review Checklist

Tick each item before marking the task complete:

- [ ] `<apex:page>` has `renderAs="pdf" showHeader="false" sidebar="false"`
- [ ] No `<script>` tags in the VF page — all logic is server-side Apex
- [ ] SOQL uses `WITH USER_MODE` or explicit FLS/CRUD checks
- [ ] Logo/images use absolute URL built in Apex or base64 data URI — not `{!$Resource.X}` in `<img src>`
- [ ] CSS uses CSS 2.1 table layout — no Flexbox, Grid, or CSS custom properties
- [ ] Conditional sections use `rendered="{!boolProp}"` — not CSS `display:none`
- [ ] If programmatic: `getContentAsPDF()` called from Queueable/Future with `Database.AllowsCallouts`
- [ ] `getContentAsPDF()` return value null-checked before use
- [ ] ContentDocumentLink inserted with correct `LinkedEntityId` and minimum required `ShareType`
- [ ] Tested as a non-admin user — no FLS violations or data exposure

## Notes

Record any deviations from the standard pattern and why:

- (e.g., "Using base64 logo because static resource is a zip file with a subdirectory path")
- (e.g., "Scope=1 used in Batch Apex because 200+ records need PDFs — callout limit mitigation")
