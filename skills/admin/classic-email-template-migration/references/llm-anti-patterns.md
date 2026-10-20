# LLM Anti-Patterns — Classic Email Template Migration

Common mistakes AI coding assistants make when generating or advising on Classic-to-Lightning email template migrations.

## Anti-Pattern 1: Verbatim Copy of `{!IF()}` and `{!CASE()}` Merge Formulas

**What the LLM generates:** A migrated Lightning template that retains `{!IF(Contact.Email != null, Contact.Email, 'fallback@x.com')}` in the body, assuming Lightning supports the same merge engine.

**Why it happens:** Merge formulas look like inline expressions; the model doesn't recognize that Lightning's merge engine is a strict subset.

**Correct pattern:** UNVERIFIED (2026-10-20): that Lightning supports straight field interpolation only — no corpus line documents Lightning merge-function support; Lightning templates use SML or HML (object_reference 264 L110801-110802). Sandbox-test, and pre-compute conditional values as formula fields on the merge record (Contact, Account, etc.) and merge the formula field. The migration is the moment to factor expressions into the data model.

## Anti-Pattern 2: Assuming `TemplateType` Distinguishes Classic from Lightning

**What the LLM generates:** Migration script with `WHERE TemplateType IN ('text', 'html', 'custom', 'visualforce')` to "find all Classic templates."

**Why it happens:** `TemplateType` is the more obvious axis; `UiType` is a less-known field.

**Correct pattern:** Use `WHERE UiType = 'Aloha'` for Classic and `WHERE UiType = 'SFX'` for Lightning. `TemplateType` describes content format, not vintage. Every Lightning Email Template has `TemplateType='custom'` (a `UiType` `SFX` template must be `custom`, api_meta 264 L59152) — a script filtering by `TemplateType` will mix Classic custom-HTML and Lightning rows.

## Anti-Pattern 3: Translating `{!Account.Name}` to `{{Account.Name}}` Without Recipient Scoping

**What the LLM generates:**

```
Hello {{Contact.FirstName}}, your account {{Account.Name}} has been updated.
```

**Why it happens:** Mechanical bracket substitution.

**Correct pattern:** Lightning merge fields are scoped to a prefix — pkg2_dev 264 L8196-8197 names the Recipients prefix for leads and contacts. UNVERIFIED (2026-10-20): the Sender and Related scopes, the `{{...}}` brace form below, and the claim that an unprefixed field fails to resolve. The form:

```
Hello {{Recipient.FirstName}}, your account {{Recipient.Account.Name}} has been updated.
```

The Recipient object IS the Contact when the email targets a Contact; field paths span from there. Without the scope prefix, the merge engine cannot resolve the field.

## Anti-Pattern 4: Re-creating Per-Department Letterheads Instead of One Centralized Enhanced Letterhead

**What the LLM generates:** A migration plan that recreates one Enhanced Letterhead per Classic Letterhead, preserving the proliferation.

**Why it happens:** Treating the migration as a 1:1 port without re-architecting the brand.

**Correct pattern:** Classic Letterheads often proliferated because the editor was clunky and copying was easier than maintaining one. Migration is the chance to consolidate. Build 1–3 Enhanced Letterheads per org (typically: corporate, transactional/no-reply, support). Templates reference the shared Letterhead. Future brand updates touch one record, not 30.

## Anti-Pattern 5: Re-implementing Visualforce Templates as Hand-Coded Apex String Builders

**What the LLM generates:** For every Classic VF email template, a new Apex class that builds the body via `String.format()` and sets `Messaging.SingleEmailMessage.setHtmlBody()` instead of `setTemplateId()`.

**Why it happens:** Goal of "no remaining VF" pushes the model to find an Apex equivalent for every template.

**Correct pattern:** Visualforce email templates are still supported. Keep the simple ones; rewrite only the ones whose Apex logic is excessive for what they do. Hand-coded string builders lose the admin-editable surface (admins can no longer tweak the email; only developers can) and are harder to test. Default: keep VF unless the migration plan specifically justifies the rewrite.

## Anti-Pattern 6: Skipping the Folder-Sharing Replication Step

**What the LLM generates:** A script that creates Lightning Email Templates in a single new folder (e.g., "Migrated Templates") without recreating the original folder structure or sharing rules.

**Why it happens:** Folder structure feels like an admin concern, not a migration step.

**Correct pattern:** Replicate folders BEFORE creating templates. For each Classic folder, create a Lightning folder (`EmailTemplateFolder`, api_meta 264 L77398-77399) with the same name and its `sharedTo` sharing (L77441) — not `FolderShare`, which covers report and dashboard folders (L77496-77497). Place migrated templates in the corresponding folder. Without this, users who relied on Classic folder permissions lose access to migrated templates (UNVERIFIED (2026-10-20): that their Email Alerts then fail at send time — no corpus line).

## Anti-Pattern 7: Editing Email Alerts in the Setup UI for Bulk Updates

**What the LLM generates:** A step-by-step plan that says "Open each Email Alert in Setup; replace template; save." for 100+ alerts.

**Why it happens:** Setup UI is the obvious admin tool.

**Correct pattern:** Use Metadata API for any update touching more than ~10 alerts. Retrieve all `WorkflowAlert` metadata, transform the `<template>` references via the old → new mapping, deploy as a single change set. Setup-UI editing is per-alert and error-prone at scale; one missed alert silently sends the wrong template.

## Anti-Pattern 8: Claiming the Sender Moves From the Template to the Alert

**What the LLM generates:** "Classic templates stored the OrgWideEmailAddress; Lightning templates don't, so re-set the OWA on every alert."

**Why it happens:** The model pairs the sender with the template because both appear on the send screen.

**Correct pattern:** No email template, Classic or Lightning, has a sender field (object_reference 264 L106331-106749). The alert's `senderType` (default `CurrentUser`) and `senderAddress` set the From (api_meta 264 L143859-143886); Apex uses `setOrgWideEmailAddressId()` (apexdev 264 L27130-27133). Swapping `<template>` leaves them as they were — change only `<template>`, then diff `senderType`/`senderAddress` before and after deploy.

## Anti-Pattern 9: Trusting the Salesforce Preview for Cross-Client Rendering

**What the LLM generates:** A workflow that says "Preview the template in the Email Template Builder; if it looks right, mark migrated."

**Why it happens:** Preview is the easiest verification.

**Correct pattern:** The Salesforce preview uses a modern browser engine that hides Outlook rendering issues. Always test on real email clients (Outlook, Gmail web, Apple Mail mobile) before declaring migration complete for any visually-complex template. Outlook's HTML engine is the lowest common denominator — table-based layouts and inline styles are required, modern CSS (flexbox, grid, custom fonts) silently degrades.

## Anti-Pattern 10: Deleting Classic Templates Immediately After Migration

**What the LLM generates:** A migration script that, after confirming Lightning templates are created, deletes the Classic source templates.

**Why it happens:** "Cleanup" instinct.

**Correct pattern:** Set Classic templates to `IsActive = false` instead of deleting. Reasons: (a) audit trail — you may need to compare original vs migrated content; (b) Email Alerts that haven't been rewired yet may suddenly fail when the template disappears; (c) UNVERIFIED (2026-10-20): that historical Activity records reference the original template. Schedule deletion only after a documented soak period (typically 90+ days) and a confirmation that no downstream consumer still references the old IDs.
