---
name: flow-email-and-notifications
description: "Use when sending emails, in-app bell notifications, SMS, or Slack messages from Salesforce Flow. Trigger keywords: 'send email action', 'custom notification', 'bell icon', 'Send Custom Notification', 'SMS from flow', 'Slack notification flow'. NOT for designing or managing email templates from Setup (use admin/email-templates-and-alerts), and NOT for Email Alerts defined in workflow rules."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "how do I send an email from a flow without an email alert"
  - "flow send custom notification bell icon not appearing for user"
  - "how to send Slack message from Salesforce Flow"
  - "flow SMS action not available in my org"
  - "send email action in flow versus email alert in workflow"
  - "custom notification limit per hour exceeded"
  - "how to use merge fields in custom notification body"
tags:
  - flow-email
  - custom-notification
  - send-email-action
  - slack-integration
  - digital-engagement
  - in-app-notification
inputs:
  - "Flow type (record-triggered, autolaunched, screen)"
  - "Notification channel required: email, in-app bell, SMS, or Slack"
  - "Recipient type: User ID, email address string, or contact email"
  - "Org add-ons available: Digital Engagement, Salesforce for Slack"
  - "Email content source: plain text body or Text Template resource"
outputs:
  - "Configured Flow action guidance (Send Email, Send Custom Notification, Send SMS, Post Message to Slack)"
  - "Recipient wiring plan (User ID vs email address)"
  - "Decision table for channel selection"
  - "Limit and license checklist"
dependencies: []
version: 2.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Flow Email and Notifications

Use this skill when a Salesforce Flow needs to deliver a message — email, in-app notification, SMS, or Slack — to users or external addresses. Covers the Send Email action, Send Custom Notification action, SMS via Digital Engagement, and Slack via the Salesforce for Slack integration. NOT for creating or managing email templates in Setup (use admin/email-templates-and-alerts), and NOT for Email Alert workflow actions.

Three design mistakes this skill catches: (1) using Send Email when a Custom Notification would be faster and more actionable for internal users, (2) confusing Flow's Send Email with Email Alerts (different template sources!), (3) designing bulk notifications without respecting the 1,000/hour cap.

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- **Notification channel:** Does the requirement need email, the in-app bell icon, a mobile push, SMS, or Slack? Each uses a different action and has different licensing.
- **Recipient type:** Is the recipient a Salesforce User (requires 15 or 18-char User ID for custom notifications), or an arbitrary email address (plain string for Send Email)?
- **Add-on licenses:** SMS requires Digital Engagement / Messaging. Slack requires the Salesforce for Slack integration configured in the org.
- **Email content source:** Flow's Send Email action uses a plain text body or a Flow `Text Template` resource — it does NOT use Classic Email Templates from Setup. That distinction is a frequent source of confusion.
- **Volume:** Custom Notifications are rate-limited at 1,000 per hour per org. Email sends count against the org's daily email limit (1,000 mass emails/day for standard orgs).

---

## Core Concepts

| Action | Template Source | Recipient Type | License Needed | Key Limit |
|---|---|---|---|---|
| **Send Email** | Text Template resource or inline text (NOT Classic Email Templates) | Email address string or User ID | Standard | 1,000 mass emails/day; 5 MB per message |
| **Send Custom Notification** | Plain-text body with `{!variable}` merge fields (no HTML) | Collection of User IDs (15/18-char) | Standard | 1,000/hour per org |
| **Send SMS** | Message body text | Phone number (E.164: `+15551234567`) | Digital Engagement add-on | Per messaging channel limits |
| **Post Message to Slack** | Message text | Slack Channel ID or name | Salesforce for Slack integration | ~40k chars per message |

**Critical distinctions:** Send Email does NOT use Classic Email Templates from Setup — use a Flow Text Template resource instead. Email Alerts (legacy, from Workflow Rules) DO use Classic Templates but are a different action. Custom Notification `recipientIds` accepts ONLY User IDs, never email addresses or Contact IDs.

> For detailed comparisons, prerequisites, and architectural tradeoffs see `references/well-architected.md`.

---

## Common Patterns

### Pattern 1: In-App Bell Notification on Record Change

**When to use:** A record-triggered or autolaunched Flow needs to alert a specific Salesforce user immediately (e.g., escalation to owner, approval request follow-up).

**Prerequisite — Custom Notification Type metadata (deploy via SFDX or create in Setup):**

```xml
<!-- force-app/main/default/notificationtypes/Case_Escalation_Alert.notiftype-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<CustomNotificationType xmlns="http://soap.sforce.com/2006/04/metadata">
    <customNotifTypeName>Case_Escalation_Alert</customNotifTypeName>
    <desktop>true</desktop>
    <masterLabel>Case Escalation Alert</masterLabel>
    <mobile>true</mobile>
    <slack>false</slack>
</CustomNotificationType>
```

**Flow action field mappings (Send Custom Notification):**

| Input Field | Value | Notes |
|---|---|---|
| `Custom Notification Type ID` | `{!customNotifTypeId}` | Query `CustomNotificationType` where `DeveloperName = 'Case_Escalation_Alert'` |
| `Recipient IDs` | `{!recipientCollection}` | Text Collection of 15/18-char User IDs |
| `Title` | `"Case Escalation — Action Required"` | Max 75 characters (silently truncates) |
| `Body` | `{!notificationBody}` | Text Template with merge fields; plain text only |
| `Target ID` | `{!$Record.Id}` | Tapping the notification navigates to this record |

**Why not email:** Bell notifications are synchronous with the transaction, appear immediately in the app, and do not require an email address. Email adds latency and inbox noise for internal user alerts.

> Full step-by-step walkthrough: `references/examples.md` — Example 1.

### Pattern 2: Confirmation Email to External Contact

**When to use:** A Flow needs to email a non-Salesforce user (customer, partner, applicant) with dynamic content after a record creation or form submission.

**Flow action field mappings (Send Email):**

| Input Field | Value | Notes |
|---|---|---|
| `Email Addresses (To)` | `{!$Record.Applicant_Email__c}` | Single email string or comma-separated list |
| `Subject` | `"Application Received — {!jobTitle}"` | Supports merge fields via formula or text |
| `Body` | `{!applicantEmailBody}` | Use a Text Template resource — NOT a Classic Email Template ID |
| `Email Template ID` | *(leave blank)* | Send Email does not accept Classic Template IDs |
| `Sender Address` | Org-Wide Email Address | Configure in Setup; do not use personal email |

Always add a fault connector — `SendEmailException` faults when limits are exceeded or the address is invalid.

**Why not Email Alert:** Send Email is more flexible for dynamic recipients and body. Email Alerts require a template fixed at design time in Setup.

> Full step-by-step walkthrough: `references/examples.md` — Example 2.

### Pattern 3: Bulk Internal Alert With Rate-Limit Awareness

**When to use:** Record-triggered Flow needs to notify many users during a bulk save (e.g., data-load alert to 200 case owners).

**Structure:**
1. Compute the User ID collection in advance.
2. Check the collection size; if > hourly limit threshold, aggregate to a digest (single notification to a manager role rather than per-user).
3. For approved bulk sends, fire Send Custom Notification with the collection.
4. Track hourly volume via a custom `Notification_Log__c` object so the next bulk run can back off if near cap.

**Why not unbounded:** 200 record load with per-record notification × 5 cascading automations = bell-cap exhaustion quickly.

### Pattern 4: Slack Channel Post for Cross-Team Awareness

**When to use:** Internal teams not on Salesforce (dev, finance, security) need awareness of a Salesforce event.

**Structure:** Flow uses `Post Message to Slack` with a pre-provisioned channel. Message contains a link back to the record (includes the `recordUrl` merge pattern).

---

## Decision Guidance

| Requirement | Recommended Channel | Key Condition |
|---|---|---|
| Notify internal Salesforce user in-app | Send Custom Notification (Pattern 1) | User ID must be available; Custom Notification Type must exist |
| Email external contact or customer | Send Email action in Flow (Pattern 2) | Recipient is an email address string; body is a Text Template |
| Email from a fixed, managed template | Email Alert invoked from Flow | Template is a Classic Email Template; recipient is defined by the alert |
| Send SMS to a phone number | Send SMS action | Requires Digital Engagement add-on license |
| Post to Slack channel | Post Message to Slack (Pattern 4) | Requires Salesforce for Slack connected workspace |
| Bulk alert to many users at once | Custom Notification (Pattern 3) with rate-limit gate | Up to org limit; watch 1,000/hour cap |
| Alert to inactive Salesforce user | Email only | Custom Notification won't deliver to inactive users |
| HTML-rich email to external | Email Alert with Classic Template | Flow's Send Email is plain-text / text-template only |

---

## Recommended Workflow

1. **Confirm the channel and license:** Determine which notification channel the requirement calls for and verify the org has the required add-ons (Digital Engagement for SMS, Salesforce for Slack for Slack). Do not proceed with unavailable actions.
2. **Identify recipient wiring:** For Send Custom Notification, locate the User ID source on the triggering record. For Send Email, locate the email address field. Confirm whether a collection or single value is needed.
3. **Create prerequisite metadata:** For custom notifications, create the Custom Notification Type in Setup before building the Flow action. For Slack, confirm the workspace connection is active.
4. **Configure the action:** Add the appropriate action element (Send Email, Send Custom Notification, Send SMS, Post Message to Slack). Map all required inputs. For email, set Subject, Body (Text Template), and To address. For notifications, set recipientIds (collection), title, body, and optionally targetId.
5. **Add a fault connector:** Every notification action can fail. Wire a fault connector to capture `$Flow.FaultMessage`, log or notify an admin, and avoid silent failures.
6. **Test with real User IDs and addresses:** Activate the Flow in a sandbox and trigger the notification. Verify delivery in the notification bell, inbox, Slack, or SMS as appropriate. Debug mode shows the action execution but not delivery confirmation.
7. **Review limits before go-live:** Confirm email volumes are within org limits. For custom notifications on high-volume automations, calculate worst-case hourly send rate against the 1,000/hour cap.

---

## Review Checklist

- [ ] Custom Notification Type exists in Setup before the Send Custom Notification action is used
- [ ] recipientIds for Send Custom Notification is a User ID collection, not email addresses or Contact IDs
- [ ] Send Email body uses a Text Template resource or inline text — not a Classic Email Template reference
- [ ] Every notification action has a fault connector wired to a log or admin alert
- [ ] Estimated send volume is within org email limits and custom notification hourly limit
- [ ] SMS or Slack actions are only configured in orgs with the required add-on or integration
- [ ] Merge fields in notification body use `{!variableName}` syntax (HTML tags are ignored in bell notifications)
- [ ] External-email recipients come from validated fields (not free-text user input)
- [ ] Bulk notifications have a rate-limit gate (Pattern 3)

---

## Salesforce-Specific Gotchas

1. **Custom Notification recipientIds must be User IDs, not email addresses** — The Send Custom Notification action requires Salesforce User record IDs (15 or 18-character). Passing an email address string causes a runtime error that is often reported as "notification not delivered" rather than a clear field-level error.
2. **Send Email does not use Classic Email Templates** — Flow's Send Email action cannot reference a Letterhead or Classic HTML template from Setup. Body content must come from a Flow Text Template resource or an inline text value. Practitioners who expect template-driven emails must use an Email Alert action instead.
3. **1,000 custom notifications/hour org limit can fail silently without a fault connector** — When the limit is exceeded, the action faults. Without a fault connector, the Flow fails or rolls back (in record-triggered context), and the only trace is the Flow debug log or a system admin fault email.
4. **SMS is invisible without Digital Engagement — no fallback action appears** — If the Digital Engagement add-on is not provisioned, the Send SMS action does not appear in Flow Builder at all. There is no placeholder or error message.
5. **Slack Post Message requires an active connected workspace, not just package installation** — Installing the Salesforce for Slack managed package does not automatically make the action work. An admin must authenticate and connect a Slack workspace in Setup.
6. **Custom Notification title max length is 75 characters** — longer titles silently truncate. Validate string length.
7. **Email deliverability setting "No access" blocks all outbound emails** — Sandbox orgs default to this setting; Flow's Send Email succeeds in the flow but nothing leaves the org. Verify deliverability is `All email` in Setup before testing.
8. **Custom Notifications to inactive users don't error but don't deliver** — Filter recipient collections by `IsActive=true` before passing to the action.
9. **Slack message character limit (~40k) + formatting caveats** — Slack truncates long messages; BlockKit JSON isn't supported from the standard Flow action.
10. **Digest patterns need state to work correctly** — aggregating notifications across flow runs requires a counter object; don't try to do it within a single run.

---

## Proactive Triggers

Surface these WITHOUT being asked:

- **Send Email action without fault connector** → Flag as High. Failed sends silent.
- **Send Custom Notification sending to email-address string (wrong input type)** → Flag as Critical. Will fail at runtime.
- **Bulk notification in record-triggered Flow without rate-limit awareness** → Flag as High. Risk of cap exhaustion.
- **Digital Engagement / Slack action used without license check** → Flag as Critical. Deploy-time failure.
- **Inactive-user filter missing on notification recipient collection** → Flag as Medium. Wasted notification attempts.
- **Sandbox testing without deliverability check** → Flag as High. Flow works in sandbox but doesn't actually send.
- **Custom Notification Type not version-controlled** → Flag as Low. Deployment drift risk.
- **Slack channel ID hardcoded instead of pulled from Custom Metadata** → Flag as Medium. Environment-brittle.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Channel decision table | Which action to use for email, bell, SMS, or Slack |
| Recipient wiring plan | How to source User IDs or email addresses from the Flow context |
| Prerequisite checklist | Custom Notification Type setup, add-on licenses, Slack workspace |
| Limit review | Email daily limit, custom notification hourly cap, message size |
| Rate-limit gate design | Pattern 3's counter / digest approach if bulk alerts required |

---

## Related Skills

- **admin/email-templates-and-alerts** — Use when the requirement involves managing Classic Email Templates, Email Alerts, or letterhead templates in Setup.
- **flow/fault-handling** — Use alongside this skill: every notification action needs a fault connector designed intentionally.
- **admin/flow-for-admins** — Use for broader Flow type selection when notification is one of several automation requirements.
- **flow/record-triggered-flow-patterns** — when the notification fires from a record trigger and must be bulk-safe.
- **flow/flow-bulkification** — when bulk notification volume is approaching limits.
