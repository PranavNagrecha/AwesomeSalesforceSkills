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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-29
---

# Classic Email Template Migration

This skill activates when a practitioner needs to convert Classic email templates (Text, HTML with Letterhead, Custom HTML, Visualforce email) to Lightning Email Templates and rewire all downstream consumers.

---

## Before Starting

Gather this context before working on anything in this domain:

- Inventory templates by type. `SELECT Id, Name, TemplateType, FolderId, IsActive FROM EmailTemplate WHERE UiType = 'Aloha'` returns Classic templates. `TemplateType` is one of `text`, `html` (with Letterhead), `custom` (raw HTML), `visualforce`.
- Identify the downstream consumers per template: Email Alerts (`SELECT Id, FullName FROM WorkflowAlert WHERE TemplateId = :t`), Flow `Send Email` actions, Process Builder email actions, Apex code calling `Messaging.SingleEmailMessage.setTemplateId(t)`, and any Marketing/CRM campaign that references the template.
- Confirm the org's brand strategy: do you have an Enhanced Letterhead already, or will the migration create one from the existing Classic Letterhead images? Letterhead colors, logos, and footers must survive the migration intact.
- Determine OrgWideEmailAddress usage. Templates often pair with a specific sender ("noreply@", "sales@"). Lightning Email Templates do not store sender — that's set at send time — so the migration must preserve the pairing in downstream Email Alerts and Apex.

---

## Core Concepts

### 1. Template Type Mapping

| Classic Template Type | Lightning Successor | Migration Notes |
|---|---|---|
| Text | Lightning Email Template (text-only mode) | Direct content port; merge fields translate |
| HTML with Letterhead | Lightning Email Template + Enhanced Letterhead | Letterhead must be re-built as Enhanced Letterhead first |
| Custom HTML | Lightning Email Template (HTML mode, no letterhead) | Paste raw HTML into the Email Template Builder; review for inline-style compatibility |
| Visualforce email | NOT migratable — keep as Classic OR rewrite as Lightning Email Template | VF templates support full Apex logic; Lightning has no equivalent server-render |

Visualforce email templates are the only type that cannot be converted automatically. Their power (full Apex controllers, conditional logic, related-list iteration) has no Lightning equivalent. The migration decision is per-template: keep it as Classic (still supported), or rewrite the *required* logic in Lightning + an Apex helper that builds the body string and uses `setHtmlBody()` instead of `setTemplateId()`.

### 2. Merge Field Syntax Translation

| Classic Syntax | Lightning Syntax | Notes |
|---|---|---|
| `{!Account.Name}` | `{{Recipient.Account.Name}}` (when Recipient is the merge object) OR `{{Sender.Account.Name}}` | Lightning explicitly scopes to Recipient / Sender / Related Object |
| `{!Contact.FirstName}` | `{{Recipient.FirstName}}` (if recipient IS the Contact) | Lightning prefers recipient-relative paths |
| `{!Account.Owner.FirstName}` | `{{Recipient.Account.Owner.FirstName}}` | Cross-object spans work the same; just prefix with Recipient/Sender |
| `{!System.URLENCODE($Setup.MyCustomSetting__c.URL__c)}` | NOT supported | Custom setting and System merge fields don't translate; move to a related-record field if needed |
| `{!IF(Contact.Email != null, Contact.Email, 'no-email@example.com')}` | NOT supported in template body | Lightning templates don't support IF/CASE merge formulas; pre-compute on a record formula field |
| `{!Account.LastModifiedDate}` formatted | `{{Recipient.Account.LastModifiedDate}}` | Date formatting in Lightning is via the recipient's locale; no inline format spec |

### 3. Letterhead vs Enhanced Letterhead

Classic Letterhead and Enhanced Letterhead are two different `Letterhead` and `EnhancedLetterhead` sObjects with no auto-conversion path. Migration requires:

| Step | Classic Letterhead | Enhanced Letterhead Outcome |
|---|---|---|
| Header image | Static image referenced by URL | Re-uploaded as Document or referenced via static URL |
| Header background color | Hex / named color | Set in Enhanced Letterhead builder |
| Body color and fonts | Inline-style settings | Lightning Email Template Builder defaults |
| Footer image and text | Static image + text block | Re-built as Enhanced Letterhead footer block |
| Sharing | Folder-based | Folder-based (`EnhancedLetterhead.FolderId`) |

You build the Enhanced Letterhead once per brand; many Lightning Email Templates can reference the same Enhanced Letterhead.

### 4. Downstream Consumer Rewiring

Every reference to a Classic template ID must be updated. Lightning template IDs are different IDs, so blanket text substitution is not enough — you need a mapping table.

| Consumer | Where the template ID lives | How to update |
|---|---|---|
| Email Alert | `WorkflowAlert.TemplateId` | Edit each alert in Setup; programmatic update via Metadata API |
| Flow `Send Email` action | Flow XML (`emailTemplateId`) | Edit each Flow; deploy via Metadata API |
| Process Builder email action | Process XML | Edit; ideally migrate to Flow first |
| Apex `Messaging.SingleEmailMessage.setTemplateId()` | Code | Find/replace by old → new ID, deploy with the rest of the code |
| Approval Process email actions | Approval XML | Edit and deploy |
| Marketing tools (Account Engagement, Marketing Cloud) | External system | Update the integration mapping |

### 5. UiType: The Single Distinguishing Field

`EmailTemplate.UiType` distinguishes Classic from Lightning:

| UiType | Meaning |
|---|---|
| `Aloha` | Classic email template |
| `SFX` | Lightning Email Template (Email Template Builder) |
| `SFX_Sample` | Lightning sample template (read-only system templates) |

Filter queries by `UiType` to operate on the right cohort. A `WHERE UiType = 'Aloha'` query is your migration source set; `WHERE UiType = 'SFX'` is the destination set.

---

## Common Patterns

### Pattern 1: Direct Conversion of Custom HTML Template

**When to use:** Classic Custom HTML templates without Visualforce or merge formulas.

**How it works:**
1. Open the Classic template; copy the raw HTML body.
2. In Setup → Email Template Builder, create a new Lightning Email Template; choose the "HTML" type with no letterhead (or with the new Enhanced Letterhead if applicable).
3. Switch the builder to source-code view; paste the HTML.
4. Replace merge fields per the syntax table (Section 2).
5. Send a test email to a sandbox user; verify rendering across major clients (Outlook, Gmail, mobile).
6. Save and capture the new template ID for downstream rewiring.

**Why not the alternative:** The Lightning Email Template Builder's WYSIWYG editor cannot import a Classic template directly — it can only build from blocks or accept HTML source. Trying to recreate the layout in the visual editor is slower and lossy compared to pasting the original HTML.

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
3. Category (b): Decide if Lightning Email Template's `{{#each}}` over a related list is sufficient (it can iterate, but not all relationships); if not, keep VF or move logic to an Apex helper that builds the body string.
4. Category (c): Keep as Classic Visualforce email template. Document the retention reason. Salesforce continues to support these.

**Why not the alternative:** Forcing a category (c) template into Lightning by hand-coding the logic in Apex `setHtmlBody()` is technically possible but loses the template-builder maintenance UX (admins can't tweak the email; only developers can). Keep VF when the logic justifies it.

### Pattern 4: Bulk Email Alert Repointing

**When to use:** After templates are migrated, dozens or hundreds of Email Alerts still point at Classic template IDs.

**How it works:**
1. Build the old → new template ID mapping table (CSV or `Map<Id, Id>` in Apex).
2. Retrieve all Email Alerts via Metadata API as XML.
3. For each `<workflowAlert>` referencing an old template ID, update the `<template>` element to the new template's full name.
4. Deploy the updated metadata in a single change set or DevOps Center release.
5. Verify via SOQL: `SELECT Id, FullName, TemplateId FROM WorkflowAlert WHERE TemplateId IN :oldIds` should return zero after deploy.

**Why not the alternative:** Editing each Email Alert in the Setup UI is feasible at <10 alerts; at scale it is error-prone and slow. Metadata API is the right tool above ~10 alerts.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Classic Text template | Direct re-creation as Lightning text template | Lowest-effort migration; merge fields translate cleanly |
| Classic HTML w/ Letterhead, single brand | Build one Enhanced Letterhead + re-create templates | Brand maintenance stays centralized |
| Classic Custom HTML | Paste HTML into Lightning Email Template source view | Faster than rebuilding in WYSIWYG |
| Visualforce template, simple merge fields only | Re-create as Lightning template; discard VF | Simpler maintenance; admin-editable |
| Visualforce template, related-list iteration | Try Lightning template iteration first; keep VF if Lightning can't model the relationship | Lightning iteration is limited to direct related lists |
| Visualforce template, complex Apex logic | Keep as Classic VF template | Lightning has no controller equivalent |
| 100+ Classic templates, all use one Letterhead | Bulk Enhanced Letterhead + scripted template creation | Manual UI re-creation doesn't scale |
| Email Alerts reference Classic templates | Metadata API bulk update with mapping table | Editing in Setup is per-alert and slow |
| Apex code uses `setTemplateId(<Classic ID>)` | Find/replace with new IDs; deploy as code change | Code change is the canonical update mechanism |
| OrgWideEmailAddress sender pairing must persist | Re-set the sender on the Email Alert / Apex call | Lightning templates don't store sender |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory and categorize.** Run the `WHERE UiType='Aloha'` SOQL. Group by `TemplateType`. Generate a CSV with columns: ID, Name, Type, Folder, downstream consumers (count of Email Alerts, Flows, Apex references). This drives the migration plan.
2. **Build Enhanced Letterhead(s).** For each unique brand layout in Classic Letterheads, create an Enhanced Letterhead. Keep the count low (1–3 per org); resist per-department variants that fragment brand.
3. **Migrate Text and Custom HTML first.** These are the lowest-risk, highest-volume cohort. Paste body, translate merge fields, send test, capture new ID.
4. **Migrate HTML-with-Letterhead.** Apply Pattern 2: each new Lightning template references the Enhanced Letterhead; body content ports directly.
5. **Triage Visualforce templates.** Categorize each per Pattern 3. Most simple ones become Lightning; complex ones stay as VF with a documented retention rationale.
6. **Build the old → new ID mapping table.** Persist as a custom object (`Email_Template_Migration_Map__c`) for ongoing reference and audit.
7. **Rewire downstream consumers.** Email Alerts via Metadata API (Pattern 4), Flows via Flow XML edit, Apex via code change. Verify zero references to old template IDs remain.
8. **Verify and deactivate Classic templates.** Send test emails through every Email Alert and Flow path. Once confirmed, set Classic template `IsActive=false` (don't delete — keep as audit trail). Schedule deletion after a soak window if storage is a concern.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every Classic template has either a Lightning equivalent OR a documented "keep as VF" retention reason
- [ ] Enhanced Letterhead(s) match the original brand (header image, colors, footer); rendered tested in Outlook, Gmail, Apple Mail
- [ ] Merge fields translated to `{{Recipient.X}}` / `{{Sender.X}}` / `{{Related.X}}` syntax
- [ ] No `{!IF(...)}`, `{!CASE(...)}`, or `{!System.X}` merge formulas remain (Lightning doesn't support them)
- [ ] Old → new template ID mapping table is committed and accessible to ongoing operations
- [ ] All Email Alerts updated via Metadata API; verification SOQL returns zero references to old template IDs
- [ ] All Flow `Send Email` actions updated to new template IDs
- [ ] All Apex `setTemplateId()` calls updated and deployed
- [ ] OrgWideEmailAddress sender pairings preserved on each downstream consumer
- [ ] Test email path validated end-to-end for at least one alert per template
- [ ] Classic templates set to `IsActive=false` after verification (not deleted yet)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Lightning Email Templates have no IF/CASE merge formula support.** Classic templates often used `{!IF(Contact.Email != null, Contact.Email, 'fallback')}` for inline conditional content. Lightning templates have no equivalent — the merge engine is straight field interpolation. Migrate the conditional logic upstream: create a formula field on the record (`Best_Contact_Email__c = IF(Email != null, Email, 'fallback')`) and merge that field instead.

2. **Custom Setting and `$Setup` merge fields don't translate.** Classic templates could reference `{!$Setup.MyCustomSetting__c.URL__c}`. Lightning has no equivalent merge namespace for custom settings. The fix is to surface the value via a record field (formula or text) on whatever record is being merged.

3. **Visualforce email templates remain functional but invisible in some Lightning UIs.** When you select a template in the Lightning Send Email composer, only Lightning templates appear in the picker by default. Visualforce templates show only when explicitly enabled in the user's Email Settings or via the "Show Classic Templates" toggle. Users may report "the template is missing" when it actually exists but is hidden.

4. **`UiType` is a separate field from `TemplateType`.** Classic and Lightning templates can both have `TemplateType='html'`. The distinguishing field is `UiType` — Classic is `'Aloha'`, Lightning is `'SFX'`. Migration scripts that filter only by `TemplateType` will mix Classic and Lightning templates and produce wrong results.

5. **Folder permissions don't auto-port.** Classic templates lived in Email Template Folders with their own sharing model. Lightning templates also use folders, but a Lightning Email Template Folder is a separate `Folder` object record. Replicating the folder structure and folder-level sharing is a manual step in the migration; otherwise users may not see migrated templates they had access to in Classic.

6. **Letterhead images served from old URLs may be cached or moved.** Classic Letterhead headers/footers were often hosted as Documents or external URLs. After migration to Enhanced Letterhead, if the image URL changed (e.g., new Document ID), some recipients' email clients may have cached the old URL with broken-link indicators. Test rendering on real email clients, not just the Salesforce preview.

7. **Email Alert `setTemplateId` requires the template to be in a folder the running user has access to.** Even when an Email Alert references the new Lightning template by ID, send-time access is checked against the user firing the alert. Lightning Email Template folders need explicit sharing to the running profiles or permission sets, or alerts will fail with `INVALID_FIELD: TemplateId is invalid`.

8. **OrgWideEmailAddress is set on the Email Alert / Apex call, not the template.** Classic templates were sometimes paired with a specific from-address via the template setup screen. Lightning templates have no sender field. Re-setting the OrgWideEmailAddress on the downstream Email Alert (or in `Messaging.SingleEmailMessage.setOrgWideEmailAddressId()` in Apex) is part of the migration — it's not preserved automatically because it was never on the template object.

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
- `admin/email-deliverability-monitoring` — Use to verify post-migration deliverability and bounce-rate baselines remain stable
- `lwc/visualforce-to-lwc-migration` — Use when retained Visualforce email templates also have associated VF UI pages being migrated
