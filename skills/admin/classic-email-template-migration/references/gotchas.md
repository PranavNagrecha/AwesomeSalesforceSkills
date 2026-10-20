# Gotchas — Classic Email Template Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `UiType` Filter Is the Only Reliable Classic vs Lightning Distinction

**What happens:** A migration script runs `SELECT Id, Name, TemplateType FROM EmailTemplate WHERE TemplateType='html'`. Results include only Classic HTML-with-Letterhead templates — so a script that switches to `TemplateType='custom'` to catch custom HTML also catches every Lightning template, because a template with `UiType` `SFX` must be `custom` (api_meta 264 L59152). The script re-processes Lightning templates as Classic, corrupting them.

**Why:** `TemplateType` describes the format (text, html, custom, visualforce; api_meta 264 L59137-59145). Lightning Email Templates share `custom` with Classic custom-HTML templates. The distinguishing axis is `UiType`: `'Aloha'` for Classic, `'SFX'` for Lightning, `'SFX_Sample'` for Lightning Experience Sample (api_meta 264 L59147-59151).

**Mitigation:** Always include `UiType = 'Aloha'` in migration source queries and `UiType = 'SFX'` in destination queries. Treat `TemplateType` as a content type, not a vintage marker.

## Gotcha 2: Lightning Email Templates May Not Evaluate `{!IF()}` or `{!CASE()}`

UNVERIFIED (2026-10-20): this gotcha's claims — Lightning merge-function support, the literal-text outcome, and the list of unsupported functions — have no corpus line; the corpus says only that Lightning templates use SML or HML (object_reference 264 L110801-110802).

**What happens:** A Classic template body has `{!IF(Contact.Email != null, Contact.Email, 'noreply@x.com')}`. Migrated verbatim into a Lightning template, the merge engine may not evaluate the formula — recipients receive the literal text `{!IF(Contact.Email != null, Contact.Email, 'noreply@x.com')}` in the email body.

**Why:** Lightning Email Templates use straight field interpolation. There is no expression engine. `IF`, `CASE`, `BLANKVALUE`, `URLENCODE`, and similar Classic merge formulas are not supported.

**Mitigation:** Pre-compute the conditional value as a formula field on the merge record. `Best_Email__c = IF(Email != null, Email, 'noreply@x.com')` on the Contact, then merge `{{Recipient.Best_Email__c}}`. The migration is the moment to factor expressions out of templates and into the data model where they belong.

## Gotcha 3: `$Setup` and `$User.Profile` Merge Fields May Not Translate

**What happens:** A Classic template references `{!$Setup.SupportConfig__c.Phone__c}` (custom setting field) or `{!$User.Profile.Name}` (running user's profile name). UNVERIFIED (2026-10-20): that Lightning has no equivalent merge namespace, and the Recipient/Sender/Related-only scope below — no corpus line.

**Why:** Classic merge field engine had broad access to org metadata; Lightning template merge engine is intentionally narrow — it merges fields off Recipient, Sender, and Related objects only.

**Mitigation:** Surface the value via a record field. Custom Setting values can be exposed via a formula field on User or another reachable object. Re-architect the template to merge that record field instead.

## Gotcha 4: Folder Sharing Doesn't Auto-Port

**What happens:** Classic templates lived in folders shared with specific roles or groups. Migration creates Lightning Email Templates in new Lightning folders, and the new folders carry none of the old sharing (Classic folders have `Type` `Email`, Lightning folders `EmailTemplate`, object_reference 264 L146139-146140). Users who could send the Classic template now can't see the Lightning template. UNVERIFIED (2026-10-20): the folders' default access and the alert error `INVALID_FIELD: TemplateId is invalid`.

**Why:** Lightning Email Template folders are separate `Folder` records. Their sharing is the folder metadata's `sharedTo` field (api_meta 264 L77441), not `FolderShare` — FolderShare is enhanced analytics sharing for report and dashboard folders (api_meta 264 L77496-77497) — and the Folder sObject API cannot view or set which group or role a folder is shared with (object_reference 264 L146045-146047). Migration scripts that create the templates without recreating the folder sharing produce templates that the original audience can't access.

**Mitigation:** Replicate the folder structure first as `EmailTemplateFolder` metadata (api_meta 264 L77398-77399) with `sharedTo`. Then create the Lightning Email Templates in the corresponding folders. Verify with: "log in as a user from each Email Alert's running profile and confirm the template is selectable."

## Gotcha 5: Classic Letterhead Image URLs May Move

**What happens:** Enhanced Letterhead is built; brand looks correct in preview. Real recipients in Outlook see broken image icons for the header. Investigation reveals the Classic Letterhead pulled the header from `/servlet/servlet.ImageServer?id=015...&oid=...` (a Document URL; UNVERIFIED (2026-10-20): this URL form has no corpus line); the Enhanced Letterhead uses a new Document, and the new URL's Document ID differs.

**Why:** Email clients cache image URLs. Some recipient mail servers (corporate Exchange) hot-link-protect or cache aggressively. Cross-org Document IDs differ between sandbox and production, so a sandbox-tested letterhead may have unrenderable URLs in production.

**Mitigation:** Host header/footer images on a stable URL (Salesforce Site, Experience Cloud, or external CDN) referenced by absolute URL in the Enhanced Letterhead. Avoid Document IDs that change across environments. Test on real email clients (not just Salesforce preview) including Outlook (worst HTML rendering), Gmail web, and Apple Mail mobile.

## Gotcha 6: Visualforce Templates May Be Hidden in the Lightning Composer

**What happens:** A user clicks "Send Email" from a Case in Lightning. The retained Classic Visualforce template doesn't appear in the picker. Users assume it's been deleted.

**Why:** UNVERIFIED (2026-10-20): that the Lightning Send Email composer filters to `UiType='SFX'` by default, and the "Show Classic Templates" user setting and the org setting named below — Help-only, no corpus line.

**Mitigation:** Enable the org-wide setting "Allow Users to Include Classic Templates in Lightning Email Composer" (UNVERIFIED (2026-10-20): setting name) if Classic VF templates must remain accessible. Document this setting in the migration runbook so admins don't accidentally turn it off after the migration "completes."

## Gotcha 7: The Sender Lives on the Alert, So a Rebuilt Alert Loses It

**What happens:** Pre-migration, an Email Alert sent from a "no-reply" OrgWideEmailAddress. During migration someone recreates the alert instead of editing its `<template>`; the new alert defaults to `senderType` `CurrentUser` and recipients see the rep's address and reply to the rep's inbox.

**Why:** No email template, Classic or Lightning, has a sender field (object_reference 264 L106331-106749). The From comes from the alert's `senderType` — default `CurrentUser` — and `senderAddress`, which is set only when `senderType` is `OrgWideEmailAddress` (api_meta 264 L143859-143886), or from Apex `setOrgWideEmailAddressId()` (apexdev 264 L27130-27133).

**Mitigation:** Change only `<template>` on existing alerts. Snapshot each alert's `senderType` and `senderAddress` before the deploy and diff them after; re-test that every alert sends from the right address.

## Gotcha 8: HTML That Renders in Salesforce Preview Breaks in Outlook

**What happens:** Lightning Email Template Builder preview shows a beautiful template. Recipients on Outlook see broken layouts, missing background colors, misaligned columns.

**Why:** Outlook's HTML rendering engine (based on Word) supports a small subset of CSS. Common issues: `<div>` margins ignored, `<table>`-based layouts required, `display:flex` not supported, background images dropped, modern fonts substituted with Times New Roman. The Salesforce preview uses a modern browser engine and hides these issues.

**Mitigation:** Test on real email clients before declaring migration complete. Use email-tested HTML patterns: `<table cellpadding=0 cellspacing=0>` for layout, inline styles for colors and fonts, web-safe font stacks, MSO conditional comments for Outlook-specific fixes. Consider using a Litmus or Email on Acid testing service if the volume of templates justifies it.
