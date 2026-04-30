# Gotchas — Classic Email Template Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `UiType` Filter Is the Only Reliable Classic vs Lightning Distinction

**What happens:** A migration script runs `SELECT Id, Name, TemplateType FROM EmailTemplate WHERE TemplateType='html'`. Results include both Classic HTML-with-Letterhead templates and Lightning Email Templates whose `TemplateType` is also `'html'`. The script accidentally re-processes Lightning templates as Classic, corrupting them.

**Why:** `TemplateType` describes the format (text, html, custom, visualforce). Lightning Email Templates can have `TemplateType='html'` exactly like Classic ones. The distinguishing axis is `UiType`: `'Aloha'` for Classic, `'SFX'` for Lightning, `'SFX_Sample'` for system samples.

**Mitigation:** Always include `UiType = 'Aloha'` in migration source queries and `UiType = 'SFX'` in destination queries. Treat `TemplateType` as a content type, not a vintage marker.

## Gotcha 2: Lightning Email Templates Don't Support `{!IF()}` or `{!CASE()}`

**What happens:** A Classic template body has `{!IF(Contact.Email != null, Contact.Email, 'noreply@x.com')}`. Migrated verbatim into a Lightning template, the merge engine does not evaluate the formula — recipients receive the literal text `{!IF(Contact.Email != null, Contact.Email, 'noreply@x.com')}` in the email body.

**Why:** Lightning Email Templates use straight field interpolation. There is no expression engine. `IF`, `CASE`, `BLANKVALUE`, `URLENCODE`, and similar Classic merge formulas are not supported.

**Mitigation:** Pre-compute the conditional value as a formula field on the merge record. `Best_Email__c = IF(Email != null, Email, 'noreply@x.com')` on the Contact, then merge `{{Recipient.Best_Email__c}}`. The migration is the moment to factor expressions out of templates and into the data model where they belong.

## Gotcha 3: `$Setup` and `$User.Profile` Merge Fields Don't Translate

**What happens:** A Classic template references `{!$Setup.SupportConfig__c.Phone__c}` (custom setting field) or `{!$User.Profile.Name}` (running user's profile name). Lightning has no equivalent merge namespace.

**Why:** Classic merge field engine had broad access to org metadata; Lightning template merge engine is intentionally narrow — it merges fields off Recipient, Sender, and Related objects only.

**Mitigation:** Surface the value via a record field. Custom Setting values can be exposed via a formula field on User or another reachable object. Re-architect the template to merge that record field instead.

## Gotcha 4: Folder Sharing Doesn't Auto-Port

**What happens:** Classic templates lived in folders shared with specific roles or groups. Migration creates Lightning Email Templates in new Lightning folders, but the new folders default to "All Internal Users" or to the migrating user's private folder. Users who could send the Classic template now can't see the Lightning template — Email Alerts firing as those users fail with `INVALID_FIELD: TemplateId is invalid`.

**Why:** Lightning Email Template folders are separate `Folder` records with their own `FolderShare` records. Migration scripts that create the templates without recreating the folder sharing produce templates that the original audience can't access.

**Mitigation:** Replicate the folder structure first, including `FolderShare` rows. Then create the Lightning Email Templates in the corresponding folders. Verify with: "log in as a user from each Email Alert's running profile and confirm the template is selectable."

## Gotcha 5: Classic Letterhead Image URLs May Move

**What happens:** Enhanced Letterhead is built; brand looks correct in preview. Real recipients in Outlook see broken image icons for the header. Investigation reveals the Classic Letterhead pulled the header from `/servlet/servlet.ImageServer?id=015...&oid=...` (a Document URL); the Enhanced Letterhead uses a new Document, and the new URL's Document ID differs.

**Why:** Email clients cache image URLs. Some recipient mail servers (corporate Exchange) hot-link-protect or cache aggressively. Cross-org Document IDs differ between sandbox and production, so a sandbox-tested letterhead may have unrenderable URLs in production.

**Mitigation:** Host header/footer images on a stable URL (Salesforce Site, Experience Cloud, or external CDN) referenced by absolute URL in the Enhanced Letterhead. Avoid Document IDs that change across environments. Test on real email clients (not just Salesforce preview) including Outlook (worst HTML rendering), Gmail web, and Apple Mail mobile.

## Gotcha 6: Visualforce Templates Hidden in Lightning UI by Default

**What happens:** A user clicks "Send Email" from a Case in Lightning. The retained Classic Visualforce template doesn't appear in the picker. Users assume it's been deleted.

**Why:** The Lightning Send Email composer filters templates by `UiType='SFX'` by default. Classic templates (`UiType='Aloha'`) — including Visualforce — are hidden unless the user has enabled "Show Classic Templates" in their Email Settings or unless the org has the global toggle enabled.

**Mitigation:** Enable the org-wide setting "Allow Users to Include Classic Templates in Lightning Email Composer" if Classic VF templates must remain accessible. Document this setting in the migration runbook so admins don't accidentally turn it off after the migration "completes."

## Gotcha 7: OrgWideEmailAddress Reset Not Visible in Template Migration

**What happens:** Pre-migration, an Email Alert sent from a "no-reply" OrgWideEmailAddress because the Classic template was paired with that OWA in template setup. Post-migration, alerts now send from the running user's own email — recipients see "fromsales-rep@company.com" instead of "noreply@company.com" and reply to the rep's inbox.

**Why:** Classic templates had a sender field on the template object. Lightning Email Templates do not. The OWA pairing must be re-set on each downstream Email Alert (or on the Apex `setOrgWideEmailAddressId()` call) — it's not stored on the template anymore.

**Mitigation:** Audit every Email Alert that referenced a template paired with an OWA. Update each alert to set the OWA explicitly. Maintain a mapping: template name → expected OWA. Re-test post-migration that every alert sends from the right address.

## Gotcha 8: HTML That Renders in Salesforce Preview Breaks in Outlook

**What happens:** Lightning Email Template Builder preview shows a beautiful template. Recipients on Outlook see broken layouts, missing background colors, misaligned columns.

**Why:** Outlook's HTML rendering engine (based on Word) supports a small subset of CSS. Common issues: `<div>` margins ignored, `<table>`-based layouts required, `display:flex` not supported, background images dropped, modern fonts substituted with Times New Roman. The Salesforce preview uses a modern browser engine and hides these issues.

**Mitigation:** Test on real email clients before declaring migration complete. Use email-tested HTML patterns: `<table cellpadding=0 cellspacing=0>` for layout, inline styles for colors and fonts, web-safe font stacks, MSO conditional comments for Outlook-specific fixes. Consider using a Litmus or Email on Acid testing service if the volume of templates justifies it.
