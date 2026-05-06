---
name: apex-outbound-email-patterns
description: "Apex outbound email via Messaging.SingleEmailMessage — OrgWideEmailAddress, ReplyTo and Reply-To header semantics, EmailTemplate merging with whatId/targetObjectId, attachment patterns, daily governor limits, and the difference between transactional sends and Email Alerts. NOT for inbound email handling (use apex/inbound-email-handler) or Marketing Cloud sends (use integration/marketing-cloud-rest-api)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "messaging singleemailmessage send apex"
  - "org wide email address from name in apex"
  - "setReplyTo set reply to address apex"
  - "send email template apex whatid targetobjectid"
  - "apex email daily limit governor"
  - "renderStoredEmailTemplate merge fields apex"
  - "apex email attachment fileattachment contentversion"
tags:
  - email
  - messaging
  - templates
  - org-wide-email
  - governor-limits
inputs:
  - "Recipient identity: User Id, Contact/Lead Id, raw email string, or list of any of those"
  - "Whether the send is transactional (one record context) or bulk"
  - "Whether a reply should land in a shared inbox / On-behalf-of address"
outputs:
  - "Apex builder pattern for Messaging.SingleEmailMessage with safe defaults"
  - "Decision: SingleEmailMessage vs Email Alert (Flow) vs MassEmailMessage"
  - "Daily-limit handling and partial-success error parsing"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Apex Outbound Email Patterns

Outbound email from Apex looks simple — instantiate
`Messaging.SingleEmailMessage`, populate fields, call
`Messaging.sendEmail`. The patterns that turn it into a reliable
production integration are not in the SOAP API guide: they live in
the interaction between `OrgWideEmailAddress`, the
`whatId`/`targetObjectId` merge contract, the daily governor cap
of 5,000 external emails, and the differences between
SingleEmailMessage and Email Alerts triggered from Flow.

The recurring questions are: how do we send "from a shared
support@" address rather than the running user; how do we make
replies go to a routing address rather than the From; how do we
merge an EmailTemplate against an Account when the template is
keyed to a Contact; and why does `setHtmlBody` ignore merge
fields. These have specific answers — most of them involve
`setOrgWideEmailAddressId`, `setReplyTo`, or
`renderStoredEmailTemplate`.

Two governor facts shape every design decision. First, the org's
daily external-email limit is 5,000 and counts every recipient on
every send (a 4-recipient send burns 4 from the bucket). Second,
sending email is treated as a non-transactional side effect — if
your transaction rolls back, the email still goes out. That last
part traps every team at least once.

## Recommended Workflow

1. **Decide the send mechanism first.** If the trigger is admin-
   configurable (a record meeting criteria), use a Flow Email Alert
   — admins can edit the template, the recipient logic, and the
   from-address without a deployment. Reach for `Messaging.SingleEmailMessage`
   only when you need conditional content, attachments computed at
   runtime, or programmatic recipient selection.
2. **Configure the OrgWideEmailAddress before writing Apex.**
   Setup → Email → Organization-Wide Addresses, verify the address,
   note its Id (or query
   `SELECT Id FROM OrgWideEmailAddress WHERE Address='support@acme.com'`).
   Without this, every send shows the running user as From.
3. **Build the message with `setOrgWideEmailAddressId` first, then
   `setReplyTo`.** The OWE controls the visible From; the
   ReplyTo controls where replies land. They are distinct concerns
   and are commonly confused.
4. **For template-merged sends, use `renderStoredEmailTemplate`
   when the merge target is not a Contact/Lead/User.** The
   built-in `setTemplateId` + `setTargetObjectId` path requires a
   Contact, Lead, or User. Anything else (Account, Case, custom
   object) needs the explicit render call with a `whatId`.
5. **Always set `setSaveAsActivity(true)` for record-related sends.**
   This writes an EmailMessage record to the related-to object's
   activity timeline — invaluable for support audits.
6. **Handle the `Messaging.SendEmailResult[]` return value.** It is
   a list parallel to the input — each element carries `isSuccess()`,
   `getErrors()`, and a status code. Treating the call as fire-and-
   forget hides per-recipient failures.
7. **Cap and observe daily-limit errors.** Catch
   `System.HandledException` containing `SINGLE_EMAIL_LIMIT_EXCEEDED`
   and degrade gracefully (queue for retry the next day, surface to
   monitoring). 5,000/day is per-org, not per-user.

## SingleEmailMessage vs Email Alert vs MassEmailMessage

- **SingleEmailMessage**: programmatic; up to 100 recipients per call;
  supports attachments, OWE, ReplyTo, custom merge.
- **Email Alert (Flow)**: declarative; admin-editable template and
  recipient set; respects OWE; cannot conditionally branch attachments.
- **MassEmailMessage**: deprecated for new work; keep only legacy
  references; use SingleEmailMessage in a loop with proper bulkification.

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| Inbound email handling | `apex/inbound-email-handler` |
| Marketing Cloud sends from Salesforce | `integration/marketing-cloud-rest-api` |
| Email-to-Case routing rules | `admin/email-to-case-config` |
| Email Deliverability settings (Setup → Email) | `admin/email-deliverability` |
