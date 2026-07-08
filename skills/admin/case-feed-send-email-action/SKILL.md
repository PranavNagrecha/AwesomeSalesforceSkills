---
name: case-feed-send-email-action
description: "Use when configuring the outbound Send Email quick action in Lightning Case Feed — creating the action in Setup on Case (Action Type = Send Email), attaching a default Custom email template, setting predefined To/CC/BCC values, wiring QuickAction.QuickActionDefaultsHandler Apex defaults, respecting the Lightning Experience 10-file / 25 MB attachment limits, and letting agents move an email to a different case. Trigger keywords: Send Email quick action, case email composer, Email action missing from Case Feed, Don't Apply Template Subject, QuickActionDefaultsHandler, SendEmailQuickActionDefaults, move email to another case. NOT for Email-to-Case inbound routing, routing addresses, or thread-ID matching (use admin/email-to-case-configuration), NOT for authoring or migrating the templates themselves (use admin/email-templates-and-alerts and admin/classic-email-template-migration), and NOT for Apex Messaging.SingleEmailMessage sends outside Case Feed."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "set up the Send Email quick action on Case Feed so agents can reply to customers"
  - "apply a default email template automatically when an agent opens the case email composer"
  - "prepopulate the To, CC, and BCC fields on the case Send Email action"
  - "the Email quick action is missing from Case Feed and agents can't email the customer"
  - "move an email that landed on the wrong case over to the correct case"
tags:
  - case-feed
  - send-email-action
  - email-quick-action
  - quickactiondefaultshandler
  - emailmessage
  - move-email
inputs:
  - "The Case object's action inventory and page layout(s) the support personas use"
  - "Whether Email-to-Case is already enabled in the org"
  - "The email template to default onto the action, and its template type"
  - "Recipient-defaulting rules (which contact/lead/person-account field feeds To, CC, BCC)"
  - "Whether defaults are static (predefined field values) or context-dependent (Apex handler)"
outputs:
  - "A `QuickAction` of type `SendEmail` on Case, assigned to the right Case page layout(s)"
  - "A default Custom email template on the action, with the Don't Apply Template Subject decision recorded"
  - "Optional predefined field values (To / CC / BCC / Related To) and/or a `QuickAction.QuickActionDefaultsHandler` Apex class"
  - "A rollout + review checklist covering send limits, layout assignment, and the move-email capability"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# Case Feed Send Email Action

This skill activates when a practitioner needs agents to *send* email from a case — the outbound composer in Lightning Case Feed — rather than to receive email into one. It covers creating the Send Email quick action in Setup, defaulting its template and recipient fields, overriding those defaults programmatically with `QuickAction.QuickActionDefaultsHandler`, and the agent-facing capability to move a misfiled email to a different case.

Inbound routing (routing addresses, thread-ID matching on customer replies, assignment and escalation rules) is a different skill: see `admin/email-to-case-configuration`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm Email-to-Case is enabled.** Salesforce Help states plainly: *"Email-to-Case must be enabled to use the Send Email quick action on the Cases object."* Without it the outbound action has no supported home on Case. Inbound enablement is a prerequisite for the outbound composer, which surprises most people.
- **Decide static vs. context-dependent defaults.** Predefined field values on the action are declarative and static per action. Anything that depends on the case (pick template A on a first touch, template B on a reply; BCC an audit mailbox based on Case Reason) needs the Apex `QuickActionDefaultsHandler`. Don't reach for Apex until the declarative path is genuinely insufficient.
- **Know the attachment limits, and their scope.** Salesforce Knowledge documents these per UI, not platform-wide: in **Lightning Experience**, up to 10 files can be attached to an outbound email and *"the total file size can't exceed 25MB"*; in **Salesforce Classic**, more than 10 files are allowed but *"the total file size can't exceed 18 MB."* Both figures are attachment totals, not whole-message envelopes, and no official source states a per-attachment cap — do not invent one.
- **Know the three documented reasons the Email action goes missing.** Before debugging a layout, check the org-level causes Salesforce Knowledge lists in *"Email Quick Action Not Available on Case Feed"*: the org's email deliverability access level is **System Email Only** rather than **All email**; Email-to-Case isn't enabled (and once enabled it cannot be disabled); **Enable Case Feed Actions and Feed Items** is unchecked in Support Settings. The same article notes that users sending through Office 365 or Gmail need the matching permission set assigned.
- **Check the move-email preconditions.** The Winter '25 release note *"Move Emails Easily to the Relevant Case"* scopes the capability to emails created by **Email-to-Case** in orgs whose email threading is set to **Lightning threading**. Confirm both before promising agents the move path.
- **Do not assert a maturity level.** Salesforce Help documents the Send Email quick action and "Move Emails to a Different Case" as standard Setup / Case Feed features. The docs carry **no GA, Beta, or Pilot label** for either. The Winter '25 release note describes the move capability as shipped, but does not stamp it with a maturity tier. State neither more nor less than that.

---

## Core Concepts

### The action is a quick action on Case, not an email setting

The composer is created the same way any other quick action is: **Setup → Object Manager → Case → Buttons, Links, and Actions → New Action**, then select **Send Email** in the **Action Type** picklist. In Metadata API terms this is a `QuickAction` with `<type>SendEmail</type>` (available in API version 31.0 and later).

Two consequences follow, and both are common support tickets:

1. **Creating the action does not surface it.** Salesforce Help carries a separate procedure — *"Add Quick Actions to the Case Page Layout for Lightning Experience"* — because placing the action on the Case page layout is its own step. Note that the org-level troubleshooting article *"Email Quick Action Not Available on Case Feed"* does **not** prescribe a layout change: its documented resolution is to raise the email deliverability access level to **All email**, enable Email-to-Case, and check **Enable Case Feed Actions and Feed Items** in Support Settings. Both surfaces can hide the action, so triage both rather than assuming the layout.
2. **The action layout is the field contract.** Which of From / To / CC / BCC / Subject / Body / Related To / Attachments an agent sees, and whether each is editable or read-only, is governed by the action's layout. A field that is read-only on the layout silently discards any prepopulated value pushed into it.

The drafted message materializes as an `EmailMessage` record — not a `Messaging.SingleEmailMessage` — and that record is the durable artifact the case feed renders. Be precise about where that is documented. The Metadata API defines `targetObject` generically (*"The object for which the action is created and performed"*) and states no value for `SendEmail`; the `EmailMessage` claim comes from the Apex reference, where `QuickAction.QuickActionDefaults.getTargetSObject()` is *"The target object of the standard Email Action on Case Feed (EmailMessage)."* Verify the type in the handler rather than asserting it from metadata.

### Defaulting a template: Custom type only

The action exposes a **Default Email Template** lookup. Salesforce Help is explicit about the eligible type: *"create an email template of the type **Custom**. Only Custom type templates are supported."* Pointing the field at a Lightning or HTML template is a configuration dead end, not a fallback.

Alongside the lookup sits the **Don't Apply Template Subject** checkbox. Selecting it suppresses the template's subject line so the composer keeps the subject already in play — the behavior you want on a *reply*, where overwriting the subject breaks the visual thread for the customer.

Note that the Metadata API `QuickAction` documentation does not list a template field, so treat the Default Email Template as a Setup-surface configuration and verify it after any org migration rather than assuming it rode along in a change set.

### Two defaulting mechanisms, two blast radii

| Mechanism | Where configured | Scope | Context-aware? |
|---|---|---|---|
| Predefined Field Values | On the quick action, Setup | That one action | No — same value every time |
| `QuickAction.QuickActionDefaultsHandler` | Apex class | The standard **Email** and **Send Email** case-feed actions org-wide | Yes — sees the case via `getContextId()` |

**Predefined field values** let you set To, CC, or BCC using ID fields (such as `Contact.Id`) or string fields (such as a custom email field on Contact). Contact, lead, and person-account IDs are supported. `AttachmentId` and `ContentDocumentIds` are **not** supported, because they aren't part of the email quick action layout. The `RelatedToId` field preselects the account associated with the case's contact when one is available.

**The Apex handler** implements a single method:

```apex
global void onInitDefaults(QuickAction.QuickActionDefaults[] defaults)
```

Each element is a `QuickAction.QuickActionDefaults`, exposing `getActionName()` (returns `Case.Email` for the standard case-feed Email action), `getActionType()` (returns `Email`), `getContextId()` (the Case Id), and `getTargetSObject()` (the `EmailMessage` being drafted). Cast to `QuickAction.SendEmailQuickActionDefaults` for the email-specific surface: `getFromAddressList()`, `getInReplyToId()`, `setTemplateId(Id)`, `setInsertTemplateBody(Boolean keepOriginalBodyContent)`, and `setIgnoreTemplateSubject(Boolean useOriginalSubject)`.

The interface requires *"an empty parameterless constructor"* and works in both Salesforce Classic and Lightning Experience.

### Moving an email to a different case

Agents misfile email. Salesforce ships a first-class capability for the correction rather than requiring a data fix: an admin turns it on (*"Let Agents Move Emails to a Different Case"*), and the agent moves the email from inside Case Feed (*"Move Emails to a Different Case"*). The Winter '25 release note *"Move Emails Easily to the Relevant Case"* scopes it to emails created by Email-to-Case in orgs using Lightning threading.

Follow the admin enablement steps as written. Salesforce Help titles that procedure as an admin setting, not as a user permission — no official source describes a permission set or user permission that governs the move. Don't design an access model around one you haven't seen in Setup.

This is a *correction* tool, not a routing tool. If emails routinely land on the wrong case, the defect is in Email-to-Case matching, not in Case Feed.

### The Classic-era publisher is not the Lightning composer

`apex:emailPublisher` is a Visualforce component that renders the Case Feed email publisher. Its field-visibility attributes do not share one enum: `toVisibility`, `ccVisibility`, and `bccVisibility` each take `editable`, `editableWithLookup`, `readOnly`, or `hidden`, while `subjectVisibility` takes only `editable`, `readOnly`, or `hidden` — `editableWithLookup` is not a legal subject value. Body format (`emailBodyFormat`) takes `text`, `HTML`, or `textAndHTML`. The component also exposes `enableQuickText`, `showTemplates`, `showAttachments`, and `showSendButton`, and requires an `entityId` (API 25.0+). It belongs to the Visualforce-era Case Feed customization path. Reach for it only when maintaining that surface — not when building a Lightning composer today.

---

## Common Patterns

### Pattern: declarative reply composer

**When to use:** the standard case, and the one to try first — agents reply to customers with a branded template, recipients default off the case contact, and nothing varies by case attribute.

**How it works:** create the Send Email action (Action Type = Send Email), set **Default Email Template** to a **Custom** template, select **Don't Apply Template Subject** so replies keep their subject, add predefined field values for To (from the case contact) and any standing CC, then add the action to every Case page layout the support personas use.

**Why not the alternative:** an Apex `QuickActionDefaultsHandler` for this is org-wide code that fires on every case-feed Email action init, for a result the Setup UI produces with no deployment, no test class, and no failure mode.

### Pattern: context-dependent defaults via Apex

**When to use:** the template or the BCC audit mailbox depends on the case (`Reason`, `RecordType`, first touch vs. reply), or you must restrict the From list.

**How it works:** implement `QuickAction.QuickActionDefaultsHandler` with an empty parameterless constructor. In `onInitDefaults`, filter the array down to the entry that is a `QuickAction.SendEmailQuickActionDefaults`, whose `getTargetSObject().getSObjectType() == EmailMessage.sObjectType`, whose `getActionName()` is `Case.Email`, and whose `getActionType()` is `Email`. Query the case once by `getContextId()`. Mutate the `EmailMessage` for field defaults (for example `BccAddress`), and use `setTemplateId` / `setInsertTemplateBody` / `setIgnoreTemplateSubject` for template behavior. Branch on `getInReplyToId() == null` to distinguish a first touch from a reply. See `references/examples.md` for a complete class.

**Why not the alternative:** predefined field values are static; a formula cannot see whether the agent clicked Reply on an existing feed item.

### Pattern: correcting a misfiled email

**When to use:** an inbound email threaded onto the wrong case and the conversation history needs to be repaired.

**How it works:** confirm the two documented preconditions (the email was created by Email-to-Case; the org uses Lightning threading), enable the capability by following Salesforce Help's *"Let Agents Move Emails to a Different Case"*, then have the agent move the email to the correct case from Case Feed.

**Why not the alternative:** re-sending the email from the correct case duplicates outbound traffic to the customer and leaves the original on the wrong record; an `EmailMessage.ParentId` data fix bypasses the agent-facing path Salesforce ships for it.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Same recipients / template on every send | Predefined field values + Default Email Template | Declarative, no code, no deployment |
| Template varies by case attribute or reply-vs-first-touch | `QuickAction.QuickActionDefaultsHandler` | Only Apex sees `getContextId()` and `getInReplyToId()` |
| Need to default `AttachmentId` or `ContentDocumentIds` | Not supported — redesign | Those fields aren't part of the email quick action layout |
| Reply must keep the customer's subject line | Select **Don't Apply Template Subject** (or `setIgnoreTemplateSubject(true)`) | Overwriting the subject breaks the thread the customer sees |
| Template is Lightning or HTML type | Re-author it as a **Custom** template | *"Only Custom type templates are supported"* for the action default |
| Agents report a custom Email action is missing | Add the action to the Case page layout | Creating an action does not place it on a layout |
| Agents report the *standard* Email action is missing | Check deliverability access level, Email-to-Case, and **Enable Case Feed Actions and Feed Items** | The three causes the troubleshooting article documents |
| Email landed on the wrong case | Enable and use the move-email capability | Purpose-built, agent-facing correction path (Email-to-Case + Lightning threading only) |
| Maintaining a Visualforce Case Feed page | `apex:emailPublisher` attributes | The Lightning composer is configured by action layout, not by VF attributes |

---

## Recommended Workflow

1. **Verify the prerequisite and the inventory.** Confirm Email-to-Case is enabled, then list the Case object's existing actions and the Case page layouts assigned to each support persona. An org frequently already has an Email action; a second one confuses agents more than it helps.
2. **Create the action.** Setup → Object Manager → Case → Buttons, Links, and Actions → New Action → **Action Type = Send Email**. Name it per `templates/admin/naming-conventions.md`.
3. **Shape the action layout.** Place only the fields agents need (From, To, CC, BCC, Subject, Body, Related To, Attachments) and set editability deliberately. Anything you plan to prepopulate must not be read-only.
4. **Default the content.** Set **Default Email Template** to a **Custom**-type template and decide **Don't Apply Template Subject** (select it for reply-oriented actions). Add predefined field values for To / CC / BCC using contact, lead, or person-account ID fields or string email fields.
5. **Escalate to Apex only if needed.** If defaults must vary by case context, implement `QuickAction.QuickActionDefaultsHandler` (empty parameterless constructor; filter on `Case.Email` / `Email`; single SOQL per init; enforce CRUD/FLS per `templates/apex/SecurityUtils.cls` and log failures via `templates/apex/ApplicationLogger.cls`).
6. **Assign and enable.** Add the action to every relevant Case page layout. If agents need to correct misfiled email, confirm the Email-to-Case and Lightning-threading preconditions, then enable the move-email capability by following Salesforce Help's *"Let Agents Move Emails to a Different Case"*.
7. **Validate.** Run `python3 scripts/check_case_feed_send_email_action.py --manifest-dir force-app/main/default`, then send a real test email inside the Lightning Experience limits (10 files, 25 MB total file size), reply to it, and confirm the subject, template body, and BCC behave as designed.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Email-to-Case is enabled in the target org
- [ ] The quick action's `<type>` is `SendEmail`
- [ ] The action appears on every Case page layout assigned to a support persona
- [ ] If the *standard* Email action is missing, the three documented org-level causes were checked (deliverability access level, Email-to-Case, **Enable Case Feed Actions and Feed Items**) — not just the layout
- [ ] The **Default Email Template** is a **Custom**-type template (not Lightning, not HTML)
- [ ] **Don't Apply Template Subject** matches intent — selected for replies, cleared for first-touch templates
- [ ] No predefined field value targets `AttachmentId` or `ContentDocumentIds`
- [ ] No field that is prepopulated (declaratively or by Apex) is read-only on the action layout
- [ ] Any `QuickActionDefaultsHandler` has an empty parameterless constructor and confirms `getTargetSObject()` is an `EmailMessage` and `getActionName() == 'Case.Email'` before casting
- [ ] The handler issues bounded SOQL (no query inside a loop) and enforces CRUD/FLS
- [ ] Agents are trained on the Lightning Experience limits — 10 files per email, 25 MB total file size (Classic differs: more than 10 files, 18 MB total)
- [ ] The move-email capability was enabled per the admin procedure, its documented preconditions (Email-to-Case, Lightning threading) hold, and its usage is monitored as a signal of upstream routing defects
- [ ] No GA / Beta / Pilot claim appears in any artifact — the docs make none

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **The outbound composer depends on the inbound feature.** Email-to-Case must be enabled before the Send Email quick action can be used on Case. Teams that only ever send email from cases still have to turn on the inbound channel.
2. **A created action is an invisible action, but the layout isn't the only culprit.** Nothing places a custom action on a layout for you. The org-level article *"Email Quick Action Not Available on Case Feed"* points somewhere else entirely — deliverability access level, Email-to-Case enablement, and the **Enable Case Feed Actions and Feed Items** setting. Assuming "it's the layout" burns an afternoon when it's the deliverability setting.
3. **Read-only wins over prepopulation, silently.** A field marked read-only on the action layout drops the value you predefined or set in Apex. There is no error; the composer simply opens with the field blank.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `quickActions/<Name>.quickAction-meta.xml` | `QuickAction` with `<type>SendEmail</type>` (API 31.0+), its `quickActionLayout`, and any `fieldOverrides` |
| Case page layout assignment | The action placed on every layout a support persona uses; without this the action is invisible |
| Default Email Template setting | Setup-surface lookup to a **Custom**-type template, plus the Don't Apply Template Subject decision |
| `classes/<Name>.cls` | Optional `QuickAction.QuickActionDefaultsHandler` implementation for context-dependent defaults |
| `templates/case-feed-send-email-action-template.md` | Config worksheet: action, layout, template, defaults, permissions, rollout checklist |
| `scripts/check_case_feed_send_email_action.py` | Static checker for the metadata tree (action type, layout assignment, unsupported field overrides, handler shape) |

---

## Related Skills

- `admin/email-to-case-configuration` — the *inbound* half: routing addresses, thread-ID matching, and the rules that create the case this action replies from.
- `admin/case-management-setup` — case assignment, escalation, and entitlement setup that surrounds the feed.
- `admin/email-templates-and-alerts` — authoring the **Custom**-type template this action defaults to.
- `admin/classic-email-template-migration` — moving legacy templates into a type this action can consume.
- `admin/global-actions-and-quick-actions` — the general quick-action model (layouts, predefined field values) this action is one instance of.
- `admin/service-console-configuration` — macros and the quick text panel agents use alongside the composer.
