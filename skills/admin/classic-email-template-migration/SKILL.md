---
name: classic-email-template-migration
description: "Migrating Classic email templates (Text, HTML with Letterhead, Custom HTML, Visualforce email) to Lightning Email Templates (LET) and the Email Template Builder. Covers merge-field translation, Letterhead-to-Enhanced-Letterhead conversion, Visualforce email retention strategy, folder reorganization, sender-context (OrgWideEmailAddress) preservation, and downstream Email Alert / Process Builder / Flow rewiring. NOT for transactional Apex email sending (use apex/apex-outbound-email-patterns) or marketing email broadcasts (use Marketing Cloud / Account Engagement)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Security
triggers:
  - "How do I migrate Classic email templates to Lightning?"
  - "Convert HTML with Letterhead to Enhanced Letterhead (Lightning)"
  - "What happens to my Visualforce email templates in Lightning Experience?"
  - "Email Alert references a Classic template — how do I switch to Lightning?"
  - "Bulk export Classic templates and re-create as Lightning Email Templates"
  - "we're having issues with email templates"
tags:
  - email-templates
  - lightning-email-template
  - letterhead
  - enhanced-letterhead
  - email-alert
  - merge-fields
  - visualforce-email
inputs:
  - "Inventory of Classic templates by type (Text, HTML w/ Letterhead, Custom HTML, Visualforce)"
  - "Folder structure and sharing permissions on the Classic templates"
  - "Downstream consumers: Email Alerts, Process Builder, Flow, Apex `setTemplateId()`, Marketing campaigns"
  - "Brand assets: existing Letterhead images, logo URLs, color palette"
  - "Whether the org uses OrgWideEmailAddress senders that must be preserved"
outputs:
  - "Lightning Email Templates (`EmailTemplate` records with `UiType='SFX'`) replacing Classic templates"
  - "Enhanced Letterhead records replacing Classic Letterhead (where applicable)"
  - "Updated Email Alerts, Flows, and Apex code referencing the new template IDs"
  - "Visualforce email-template retention list (templates that cannot be migrated)"
  - "Migration audit log mapping each Classic template ID to its Lightning successor"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Classic Email Template Migration

This skill activates when a practitioner needs to convert Classic email templates (Text, HTML with Letterhead, Custom HTML, Visualforce email) to Lightning Email Templates and rewire all downstream consumers.

---

## Before Starting

Gather this context before working on anything in this domain:

- Inventory templates by type. `SELECT Id, Name, TemplateType, FolderId, IsActive FROM EmailTemplate WHERE UiType = 'Aloha'` returns Classic templates. `TemplateType` is one of `text`, `html` (based on a letterhead), `custom` (HTML without a letterhead), `visualforce` (api_meta 264 L59137-59145); the object's `UIType` picklist holds `Aloha`, `SFX`, `SFX_Sample` (object_reference 264 L106729-106749).
- Identify the downstream consumers per template: Email Alerts (retrieve Workflow metadata and read each alert's `<template>`, a named reference to the template, api_meta 264 L143888; UNVERIFIED (2026-10-20): a Tooling API `WorkflowAlert` query by `TemplateId` — the Tooling API is not in the corpus), Flow `Send Email` actions, Process Builder email actions, Apex code calling `Messaging.SingleEmailMessage.setTemplateId(t)`, and any Marketing/CRM campaign that references the template.
- Confirm the org's brand strategy: do you have an Enhanced Letterhead already, or will the migration create one from the existing Classic Letterhead images? Letterhead colors, logos, and footers must survive the migration intact.
- Determine OrgWideEmailAddress usage. Neither Classic nor Lightning templates store a sender — EmailTemplate has no sender field (object_reference 264 L106331-106749). The From address lives on the Email Alert (`senderType`, `senderAddress`, api_meta 264 L143859-143886) or the Apex call (`setOrgWideEmailAddressId`, apexdev 264 L27130-27133), so swapping the template leaves it unchanged — record it and verify it after the swap.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is the inventory filtered by `UiType` rather than `TemplateType`? | Classic custom-HTML and every Lightning template share `type` custom (Gotcha 4) | A source set that cannot pick up Lightning rows |
| Which templates use IF/CASE, `$Setup` or `System.` merge expressions? | Their Lightning support has no corpus line (Gotchas 1-2) | A per-template list to sandbox-test or pre-compute on a formula field |
| Which folders hold the templates and who are they shared with? | Lightning templates sit in `EmailTemplate`-type folders that must be recreated with sharing (Gotcha 5) | The folder plan, deployed as `EmailTemplateFolder` with `sharedTo` |
| Which approval processes use a template as their approval-request email? | `ApprovalProcess.emailTemplate` takes a Classic template (Core Concepts 4) | The templates that must stay Classic |
| Which Email Alerts send from an OrgWideEmailAddress? | The sender is on the alert, not the template (Gotcha 8) | A before/after check that `senderType` and `senderAddress` did not change |
| Will the templates or alerts ship in a package? | The guide says Lightning templates are not packageable and also allows first-generation packaging (Gotcha 9) | The packaging route decided before migration, not after |
| Which Visualforce templates carry controller logic, and do users pick them in the Lightning composer? | VF stays a supported type; its visibility in the composer is unverified (Gotcha 3) | The retain-as-VF list and a user test of the composer |

A proper configuration adds an ID-to-name mapping, recreated folder sharing and an unchanged sender per alert; "just doing it" re-creates the bodies and leaves alerts, approvals and folders pointing at the old world.

---

## Core Concepts

### 1. Template Type Mapping

| Classic Template Type | Lightning Successor | Migration Notes |
|---|---|---|
| Text | Lightning Email Template (`type` custom) | Direct content port; merge fields need review (Section 2) |
| HTML with Letterhead | Lightning Email Template + Enhanced Letterhead | Letterhead must be re-built as Enhanced Letterhead first |
| Custom HTML | Lightning Email Template (`type` custom, no letterhead) | Paste raw HTML into the Email Template Builder; review for inline-style compatibility |
| Visualforce email | NOT migratable — keep as Classic OR rewrite as Lightning Email Template | VF templates support full Apex logic; Lightning has no equivalent server-render |

Whatever the Classic type, a template whose `UiType` is `SFX` must have `type` custom (api_meta 264 L59152). UNVERIFIED (2026-10-20): that Lightning offers no server-side render equivalent to a VF controller, and that no automatic conversion exists — no corpus line.

Visualforce stays a valid template type at API 68.0 (api_meta 264 L59144-59145), and VF templates cannot be used for mass email (object_reference 264 L106309). Their power (full Apex controllers, conditional logic, related-list iteration) may have no Lightning equivalent (UNVERIFIED (2026-10-20), as above). The migration decision is per-template: keep it as Classic (still supported), or rewrite the *required* logic in Lightning + an Apex helper that builds the body string and uses `setHtmlBody()` instead of `setTemplateId()`.

### 2. Merge Field Syntax Translation

| Classic Syntax | Lightning Syntax | Notes |
|---|---|---|
| `{!Account.Name}` | `{{Recipient.Account.Name}}` (when Recipient is the merge object) OR `{{Sender.Account.Name}}` | Lightning explicitly scopes to Recipient / Sender / Related Object |
| `{!Contact.FirstName}` | `{{Recipient.FirstName}}` (if recipient IS the Contact) | Lightning prefers recipient-relative paths |
| `{!Account.Owner.FirstName}` | `{{Recipient.Account.Owner.FirstName}}` | Cross-object spans work the same; just prefix with Recipient/Sender |
| `{!System.URLENCODE($Setup.MyCustomSetting__c.URL__c)}` | NOT supported | Custom setting and System merge fields don't translate; move to a related-record field if needed |
| `{!IF(Contact.Email != null, Contact.Email, 'no-email@example.com')}` | NOT supported in template body | Lightning templates don't support IF/CASE merge formulas; pre-compute on a record formula field |
| `{!Account.LastModifiedDate}` formatted | `{{Recipient.Account.LastModifiedDate}}` | Date formatting in Lightning is via the recipient's locale; no inline format spec |

Lightning templates use one of two merge languages: SML or HML (UNVERIFIED (2026-10-20): the `{!...}` form for SML — the corpus names the languages, not their syntax) — an enhanced letterhead attaches only to an HML template (object_reference 264 L106414-106415, L110801-110802) — and pkg2_dev 264 L8196-8197 names a Recipients merge prefix for leads and contacts. UNVERIFIED (2026-10-20): the rest of this table — the `{{...}}` brace form, the Sender and Related scopes, and the unsupported IF/CASE/`$Setup`/`System.`/date-format rows — has no corpus line; sandbox-test each row.

### 3. Letterhead vs Enhanced Letterhead

A Classic letterhead is a `BrandTemplate` record (object_reference 264 L51116; Metadata API type `Letterhead`, api_meta 264 L86358-86359); an enhanced letterhead is an `EnhancedLetterhead` record, API 46.0+ (object_reference 264 L110801-110802). UNVERIFIED (2026-10-20): that no conversion path exists between them. Migration requires:

| Step | Classic Letterhead | Enhanced Letterhead Outcome |
|---|---|---|
| Header image | Static image referenced by URL | Re-uploaded as Document or referenced via static URL |
| Header background color | Hex / named color | Set in Enhanced Letterhead builder |
| Body color and fonts | Inline-style settings | Lightning Email Template Builder defaults |
| Footer image and text | Static image + text block | Re-built as Enhanced Letterhead footer block |
| Sharing | Not folder-based: `BrandTemplate` has no folder field (object_reference 264 L51137-51203) and `Letterhead` metadata sits in the `letterhead` directory (api_meta 264 L86365-86366) | No folder field: EnhancedLetterhead lists Description, LetterheadHeader, LetterheadFooter, Name (object_reference 264 L110812-110863) |

You build the Enhanced Letterhead once per brand; many Lightning Email Templates can reference the same Enhanced Letterhead.

### 4. Downstream Consumer Rewiring

Every reference to a Classic template ID must be updated. Lightning template IDs are different IDs, so blanket text substitution is not enough — you need a mapping table.

| Consumer | Where the template ID lives | How to update |
|---|---|---|
| Email Alert | `<template>` in the Workflow file's `<alerts>` — a named reference (api_meta 264 L143888) | Edit each alert in Setup; programmatic update via Metadata API |
| Flow `Send Email` action | Flow XML (`emailTemplateId`) | Edit each Flow; deploy via Metadata API |
| Process Builder email action | Process XML | Edit; ideally migrate to Flow first |
| Apex `Messaging.SingleEmailMessage.setTemplateId()` | Code | Find/replace by old → new ID, deploy with the rest of the code |
| Approval process | `emailTemplate` (approval-request email) and alert actions | `emailTemplate` takes a Classic template (api_meta 264 L25167-25168) — keep that one Classic; repoint the alerts |
| Marketing tools (Account Engagement, Marketing Cloud) | External system | Update the integration mapping |

UNVERIFIED (2026-10-20): the Flow parameter name `emailTemplateId` — the Metadata API guide does not list Send Email action inputs.

### 5. UiType: The Single Distinguishing Field

`EmailTemplate.UiType` distinguishes Classic from Lightning:

| UiType | Meaning |
|---|---|
| `Aloha` | Classic email template |
| `SFX` | Lightning Email Template (Email Template Builder) |
| `SFX_Sample` | Lightning Experience Sample (api_meta 264 L59151) |

Filter queries by `UiType` to operate on the right cohort. A `WHERE UiType = 'Aloha'` query is your migration source set; `WHERE UiType = 'SFX'` is the destination set.

---

## Common Patterns

### Pattern 1: Direct Conversion of Custom HTML Template

**When to use:** Classic Custom HTML templates without Visualforce or merge formulas.

**How it works:**
1. Open the Classic template; copy the raw HTML body.
2. Create a new Lightning Email Template (saved as `type` custom, api_meta 264 L59152), with no letterhead or with the new Enhanced Letterhead.
3. Switch the builder to source-code view; paste the HTML.
4. Replace merge fields per the syntax table (Section 2).
5. Send a test email to a sandbox user; verify rendering across major clients (Outlook, Gmail, mobile).
6. Save and capture the new template ID for downstream rewiring.

**Why not the alternative:** UNVERIFIED (2026-10-20): that the Email Template Builder cannot import a Classic template and accepts only blocks or HTML source. Trying to recreate the layout in the visual editor is slower and lossy compared to pasting the original HTML.

### Pattern 2: HTML-with-Letterhead Template + Enhanced Letterhead Build-Out

**When to use:** Classic templates that share a single Letterhead (typical: one corporate Letterhead + 30 templates that reference it).

**How it works:**
1. Build ONE Enhanced Letterhead first. In Setup → Enhanced Letterheads, recreate the brand (header image, colors, footer).
2. Verify rendering by attaching the Enhanced Letterhead to a single test Lightning Email Template.
3. For each Classic template that referenced the Classic Letterhead, create a new Lightning Email Template that uses the Enhanced Letterhead.
4. Copy the body HTML from the Classic template into the Lightning template body block.
5. Translate merge fields.
6. Map each old → new template ID for downstream rewiring.

**Why not the alternative:** Building Enhanced Letterheads per template scatters brand maintenance and makes future brand updates painful. One Enhanced Letterhead serving N templates is the right architecture.

### Pattern 3: Visualforce Email Template — Decide Per Template

**When to use:** Classic templates with `TemplateType='visualforce'` that contain Apex controller logic (related-list iteration, conditional content, complex formatting).

**How it works:**
1. For each VF template, audit what the controller does. Categorize: (a) simple merge fields (no real Apex needed), (b) related-list rendering, (c) genuine business logic.
2. Category (a): Re-create as Lightning Email Template with merge fields. Discard the VF template.
3. Category (b): Decide if Lightning Email Template iteration over a related list is sufficient (UNVERIFIED (2026-10-20): the `{{#each}}` form and its relationship limits have no corpus line); if not, keep VF or move logic to an Apex helper that builds the body string.
4. Category (c): Keep as Classic Visualforce email template. Document the retention reason. `visualforce` is still a valid type (api_meta 264 L59144-59145).

**Why not the alternative:** Forcing a category (c) template into Lightning by hand-coding the logic in Apex `setHtmlBody()` is technically possible but loses the template-builder maintenance UX (admins can't tweak the email; only developers can). Keep VF when the logic justifies it.

### Pattern 4: Bulk Email Alert Repointing

**When to use:** After templates are migrated, dozens or hundreds of Email Alerts still point at Classic template IDs.

**How it works:**
1. Build the old → new template ID mapping table (CSV or `Map<Id, Id>` in Apex).
2. Retrieve all Email Alerts via Metadata API as XML.
3. For each `<alerts>` entry (a `WorkflowAlert`, api_meta 264 L143765) referencing an old template, update the `<template>` element to the new template's full name.
4. Deploy the updated metadata in a single change set or DevOps Center release.
5. Verify by re-retrieving the Workflow files and searching every `<template>` for the old template names — expect zero hits.

**Why not the alternative:** Editing each Email Alert in the Setup UI is feasible at <10 alerts; at scale it is error-prone and slow. Metadata API is the right tool above ~10 alerts.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Classic Text template | Direct re-creation as Lightning text template | Lowest-effort migration; merge fields translate cleanly |
| Classic HTML w/ Letterhead, single brand | Build one Enhanced Letterhead + re-create templates | Brand maintenance stays centralized |
| Classic Custom HTML | Paste HTML into Lightning Email Template source view | Faster than rebuilding in WYSIWYG |
| Visualforce template, simple merge fields only | Re-create as Lightning template; discard VF | Simpler maintenance; admin-editable |
| Visualforce template, related-list iteration | Try Lightning template iteration first; keep VF if Lightning can't model the relationship | UNVERIFIED (2026-10-20): Lightning iteration limits |
| Visualforce template, complex Apex logic | Keep as Classic VF template | UNVERIFIED (2026-10-20): that Lightning has no controller equivalent |
| 100+ Classic templates, all use one Letterhead | Bulk Enhanced Letterhead + scripted template creation | Manual UI re-creation doesn't scale |
| Email Alerts reference Classic templates | Metadata API bulk update with mapping table | Editing in Setup is per-alert and slow |
| Apex code uses `setTemplateId(<Classic ID>)` | Find/replace with new IDs; deploy as code change | Code change is the canonical update mechanism |
| OrgWideEmailAddress sender pairing must persist | Leave the alert's `senderType`/`senderAddress` and the Apex `setOrgWideEmailAddressId` call untouched; diff them after deploy | No template type stores a sender (Gotcha 8) |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory and categorize.** Run the `WHERE UiType='Aloha'` SOQL. Group by `TemplateType`. Generate a CSV with columns: ID, Name, Type, Folder, downstream consumers (count of Email Alerts, Flows, Apex references). This drives the migration plan.
2. **Build Enhanced Letterhead(s).** For each unique brand layout in Classic Letterheads, create an Enhanced Letterhead. Keep the count low (1–3 per org); resist per-department variants that fragment brand.
3. **Migrate templates by type.** Start with Text and Custom HTML (lowest risk, highest volume) — paste body, translate merge fields, send test, capture new ID. Then HTML-with-Letterhead per Pattern 2: each new Lightning template references the Enhanced Letterhead; body content ports directly.
4. **Triage Visualforce templates.** Categorize each per Pattern 3. Most simple ones become Lightning; complex ones stay as VF with a documented retention rationale.
5. **Build the old → new ID mapping table.** Persist as a custom object (`Email_Template_Migration_Map__c`) for ongoing reference and audit.
6. **Rewire downstream consumers.** Email Alerts via Metadata API (Pattern 4), Flows via Flow XML edit, Apex via code change. Verify zero references to old template IDs remain.
7. **Verify and deactivate Classic templates.** Send test emails through every Email Alert and Flow path. Once confirmed, set Classic template `IsActive=false` (don't delete — keep as audit trail). Schedule deletion after a soak window if storage is a concern.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every Classic template has either a Lightning equivalent OR a documented "keep as VF" retention reason
- [ ] Enhanced Letterhead(s) match the original brand (header image, colors, footer); rendered tested in Outlook, Gmail, Apple Mail
- [ ] Merge fields translated to the template's merge language and sandbox-tested (the `{{Recipient.X}}` / `{{Sender.X}}` / `{{Related.X}}` forms are UNVERIFIED (2026-10-20))
- [ ] Every `{!IF(...)}`, `{!CASE(...)}`, or `{!System.X}` expression pre-computed or sandbox-tested (UNVERIFIED (2026-10-20): Lightning support for them)
- [ ] Old → new template ID mapping table is committed and accessible to ongoing operations
- [ ] All Email Alerts updated via Metadata API; re-retrieved Workflow files name no old template
- [ ] Approval processes' `emailTemplate` still names a Classic template
- [ ] All Flow `Send Email` actions updated to new template IDs
- [ ] All Apex `setTemplateId()` calls updated and deployed
- [ ] Each alert's `senderType`/`senderAddress` and each Apex OWA call unchanged after the swap
- [ ] Test email path validated end-to-end for at least one alert per template
- [ ] Classic templates set to `IsActive=false` after verification (not deleted yet)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Lightning Email Templates may not evaluate IF/CASE merge formulas** (UNVERIFIED (2026-10-20): no corpus line documents Lightning merge-function support either way). Classic templates often used `{!IF(Contact.Email != null, Contact.Email, 'fallback')}` for inline conditional content. Sandbox-test each one; the safe route is to migrate the conditional logic upstream: create a formula field on the record (`Best_Contact_Email__c = IF(Email != null, Email, 'fallback')`) and merge that field instead.

2. **Custom Setting and `$Setup` merge fields may not translate** (UNVERIFIED (2026-10-20): no corpus line on Lightning `$Setup` support). Classic templates could reference `{!$Setup.MyCustomSetting__c.URL__c}`. The safe fix is to surface the value via a record field (formula or text) on whatever record is being merged.

3. **Visualforce email templates remain a valid type but may be hidden in the Lightning composer** (`visualforce`, api_meta 264 L59144-59145). UNVERIFIED (2026-10-20): that the Lightning Send Email picker shows only Lightning templates by default and that a "Show Classic Templates" setting reveals Classic ones — Help-only. Users may report "the template is missing" when it actually exists but is hidden.

4. **`UiType` is a separate field from `TemplateType`.** Classic custom-HTML templates and every Lightning template both have `type` custom — a template with `UiType` `SFX` must be `custom` (api_meta 264 L59140-59143, L59152). The distinguishing field is `UiType` — Classic is `'Aloha'`, Lightning is `'SFX'` (api_meta 264 L59147-59151). Migration scripts that filter only by `TemplateType` will mix Classic and Lightning templates and produce wrong results.

5. **Folder permissions don't auto-port.** A Folder's `Type` is `Email` for Classic templates and `EmailTemplate` for Lightning templates (object_reference 264 L146139-146140), so Lightning folders are new records; deploy them as `EmailTemplateFolder` (api_meta 264 L77398-77399) with `sharedTo` (L77441) — the Folder sObject API cannot view or set which group or role a folder is shared with (object_reference 264 L146045-146047). Replicating the folder structure and folder-level sharing is a manual step in the migration; otherwise users may not see migrated templates they had access to in Classic.

6. **Letterhead images served from old URLs may be cached or moved.** Classic Letterhead headers/footers were often hosted as Documents or external URLs. After migration to Enhanced Letterhead, if the image URL changed (e.g., new Document ID), some recipients' email clients may have cached the old URL with broken-link indicators. Test rendering on real email clients, not just the Salesforce preview.

7. **An Email Alert may fail if the running user cannot see the template's folder.** UNVERIFIED (2026-10-20): the send-time folder-access check and the `INVALID_FIELD: TemplateId is invalid` error text have no corpus line. Share Lightning template folders to the users who fire the alerts and test-send as one of them.

8. **OrgWideEmailAddress is set on the Email Alert / Apex call, never on the template.** EmailTemplate has no sender field in either UI (object_reference 264 L106331-106749); an alert's From comes from `senderType` (default `CurrentUser`) and `senderAddress` (api_meta 264 L143859-143886), and Apex sets it with `setOrgWideEmailAddressId()` (apexdev 264 L27130-27133). Swapping `<template>` does not touch them — diff them after deploy rather than re-setting them.

9. **The packaging guidance pulls both ways.** WorkflowAlert `template` and ApprovalProcess `emailTemplate` say Lightning email templates aren't packageable and recommend a Classic template (api_meta 264 L143891-143892, L25169-25170), while the EmailTemplate type says first-generation packaging is supported for Lightning templates (api_meta 264 L58976) and `UiType` says packaging is supported for Classic only (L59153). For a package, keep the alert's template Classic.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Lightning Email Template records | `EmailTemplate` rows with `UiType='SFX'` replacing each Classic template |
| Enhanced Letterhead record(s) | One per brand; referenced by all branded Lightning templates |
| `Email_Template_Migration_Map__c` records | Old Classic ID → new Lightning ID, plus migration date and outcome |
| Updated Email Alerts (Metadata API package) | `WorkflowAlert.template` references switched to new template fullnames |
| Updated Flows | Send Email actions repointed to new template IDs |
| Updated Apex | `setTemplateId` calls switched to new IDs |
| Visualforce template retention list | Documented set of VF templates kept with rationale |
| Test plan results | Per-alert send test confirming end-to-end rendering and recipient delivery |

---

## Related Skills

- `admin/email-templates-and-alerts` — Use when designing new Lightning templates and Email Alerts (post-migration)
- `apex/apex-outbound-email-patterns` — Use when Apex code sends transactional email; affected by template ID changes
- `flow/flow-email-and-notifications` — Use when Flow's Send Email actions need to be updated to new template IDs
- `admin/email-deliverability-strategy` — Use to verify post-migration deliverability and bounce-rate baselines remain stable
- `lwc/visualforce-to-lwc-migration` — Use when retained Visualforce email templates also have associated VF UI pages being migrated
