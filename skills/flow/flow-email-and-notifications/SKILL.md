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
version: 2.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Flow Email and Notifications

Use this skill when a Salesforce Flow needs to deliver a message — email, in-app notification, SMS, or Slack — to users or external addresses. Covers the Send Email action, Send Custom Notification action, SMS via Digital Engagement, and Slack via the Salesforce for Slack integration. NOT for creating or managing email templates in Setup (use admin/email-templates-and-alerts), and NOT for Email Alert workflow actions.

Three design mistakes this skill catches: (1) using Send Email when a Custom Notification would be faster and more actionable for internal users, (2) confusing Flow's Send Email with Email Alerts (different template sources!), (3) designing bulk notifications without respecting the hourly notification-action cap (10,000 per org, pkg2_dev 264 L5916).

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- **Notification channel:** Does the requirement need email, the in-app bell icon, a mobile push, SMS, or Slack? Each uses a different action and has different licensing.
- **Recipient type:** Is the recipient a Salesforce User (requires 15 or 18-char User ID for custom notifications), or an arbitrary email address (plain string for Send Email)?
- **Add-on licenses:** SMS requires Digital Engagement / Messaging. Slack requires the Salesforce for Slack integration configured in the org.
- **Email content source:** Flow's Send Email action uses a plain text body or a Flow `Text Template` resource (`emailSimple` "sends an email by using flow resources", api_meta 264 L71274); that it cannot use Classic Email Templates from Setup is UNVERIFIED (2026-10-20): Help-only. That distinction is a frequent source of confusion.
- **Volume:** "A subscriber org can execute up to 10,000 notification actions per hour" (pkg2_dev 264 L5916); the earlier text said 1,000, CONTRADICTED. Email: each licensed org can send single emails to at most 5,000 external addresses per day (GMT), and for orgs created in Spring '19 or later that daily limit also counts email alerts, simple email actions and Send Email actions in flows (apexdev 264 L20162-20166); mass and list email are also capped at 5,000 external addresses per day (apexdev 264 L20176-20177). The earlier "1,000 mass emails/day" is CONTRADICTED.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which channel does the requirement need: bell, email, SMS or Slack? | Core Concepts: each is a different `actionType` with its own license (api_meta 264 L71245, L71272-71275, L71465) | One action chosen per recipient group |
| Are the recipients Salesforce Users or external addresses? | Gotcha 1: `recipientIds` takes User IDs | A User-ID source or a switch to Send Email |
| Does the content come from a Classic template? | Gotcha 2: `emailSimple` uses flow resources, `emailAlert` references an alert (L71272-71275) | Text Template resource or Email Alert chosen |
| What is the worst-case volume per hour and per day? | Gotcha 3: 10,000 notification actions per hour (pkg2_dev 264 L5916); 5,000 external addresses per day (apexdev 264 L20162-20166) | A volume budget and a digest design |
| Is Digital Engagement or Slack provisioned in this org? | Gotchas 4 and 5 (UNVERIFIED, 2026-10-20) | A license check before design |
| Is the Custom Notification Type deployed and its ID resolvable? | Pattern 1: `CustomNotificationType` is queryable (object_reference 264 L88464-88465) | A deployed `.notiftype` and a lookup step |
| What happens in a sandbox with email deliverability restricted? | Gotcha 7 (UNVERIFIED, 2026-10-20) | A deliverability check in the test plan |

A proper configuration adds a channel decision, a volume budget and a fault path; just dropping an action in gives you none of them.

---

## Core Concepts

| Action | Where the body comes from | Addressed to | License | Ceiling that bites |
|---|---|---|---|---|
| **Send Email** | A Flow Text Template resource, or text typed inline — *not* a Classic Email Template | An email-address string, or a User ID | Standard | The org's daily external-address limit (5,000, apexdev 264 L20162-20166); a 5 MB per-message size is UNVERIFIED (2026-10-20): Help-only; neither corpus holds it |
| **Send Custom Notification** | Plain text carrying `{!variable}` merge fields; HTML is not rendered | A collection of User IDs (the Apex counterpart also takes Account, Opportunity, Group and Queue IDs, apexref 262 L166770-166781) | Standard | 10,000 notification actions per hour (pkg2_dev 264 L5916) |
| **Send SMS** | The message body itself | An E.164 phone number, e.g. `+15551234567` | Digital Engagement add-on | Whatever the messaging channel imposes (the E.164 form, the add-on and the absence of a Send SMS `actionType` in the FlowActionCall list are UNVERIFIED (2026-10-20): Help-only; neither corpus holds it) |
| **Post Message to Slack** | The message text | A Slack channel, by ID or by name | Salesforce for Slack | `slackPostMessage` is the action type, API 54.0+ (api_meta 264 L71465-71466); the 40,000-character figure is UNVERIFIED (2026-10-20): Help-only; neither corpus holds it |

**Three distinctions cause most of the failures here.** In FlowActionCall the two email action types are distinct: `emailAlert` "sends an email by referencing a workflow email alert" and `emailSimple` "sends an email by using flow resources" and is not available for flows with processType Workflow (api_meta 264 L71272-71275); `customNotificationAction` sends a custom notification, API 46.0+ (L71245). Send Email ignores the Classic Email Templates sitting in Setup (UNVERIFIED, 2026-10-20: no corpus passage says a template cannot be used) — point it at a Flow Text Template resource instead. Email Alerts *do* read those Classic templates, but an Email Alert is a separate action inherited from Workflow Rules, and reaching for one when you meant the other is an easy slip. And `recipientIds` on a Custom Notification takes record IDs that resolve to users, never email addresses or Contact IDs: the Apex counterpart, `Messaging.CustomNotification.send()`, accepts User, Account (team), Opportunity (team), Group and Queue IDs, up to 500 values, and sends only to active users (apexref 262 L166767-166781); that the Flow action accepts the same set is UNVERIFIED (2026-10-20).

> `references/well-architected.md` carries the fuller comparison, the prerequisites, and the architectural tradeoffs.

---

## Common Patterns

### Pattern 1: In-App Bell Notification on Record Change

**When to use:** A record-triggered or autolaunched Flow needs to alert a specific Salesforce user immediately (e.g., escalation to owner, approval request follow-up).

**Prerequisite — a Custom Notification Type must exist first.** Build it in Setup, or deploy the metadata:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Path: force-app/main/default/notificationtypes/
     File: Case_Escalation_Alert.notiftype-meta.xml
     desktop and mobile are the delivery channels; slack is "Reserved for future use"
     (api_meta 264 L43967), so leave it false. -->
<CustomNotificationType xmlns="http://soap.sforce.com/2006/04/metadata">
    <customNotifTypeName>Case_Escalation_Alert</customNotifTypeName>
    <desktop>true</desktop>
    <masterLabel>Case Escalation Alert</masterLabel>
    <mobile>true</mobile>
    <slack>false</slack>
</CustomNotificationType>
```

**What to put in each Send Custom Notification input:**

| Input Field | Value | What to watch |
|---|---|---|
| `Custom Notification Type ID` | `{!customNotifTypeId}` | Resolve it by querying `CustomNotificationType` for `DeveloperName = 'Case_Escalation_Alert'` (queryable sObject, API 47.0+, `DeveloperName` field: object_reference 264 L88452, L88464-88465, L88495-88500) |
| `Recipient IDs` | `{!recipientCollection}` | A Text Collection holding User IDs, 15- or 18-character |
| `Title` | `"Case Escalation — Action Required"` | 250 characters is the cap (the Apex `CustomNotification` title, apexref 262 L166708) and "a client may see a truncated notification title or body depending on the delivery channel or app" (L166724); the ~120-character desktop cut-off is UNVERIFIED (2026-10-20): Help-only — front-load the part the reader must act on |
| `Body` | `{!notificationBody}` | 750 characters allowed (apexref 262 L166711); roughly 320 shown on desktop is UNVERIFIED (2026-10-20): Help-only; plain-text Text Template with merge fields |
| `Target ID` | `{!$Record.Id}` | The record the notification opens when tapped |

**Why not email:** Bell notifications are synchronous with the transaction (UNVERIFIED (2026-10-20): Help-only; neither corpus holds it), appear immediately in the app, and do not require an email address. Email adds latency and inbox noise for internal user alerts.

> Walked through end to end in `references/examples.md`, Example 1.

### Pattern 2: Confirmation Email to External Contact

**When to use:** A Flow needs to email a non-Salesforce user (customer, partner, applicant) with dynamic content after a record creation or form submission.

**What to put in each Send Email input:**

| Input Field | Value | What to watch |
|---|---|---|
| `Email Addresses (To)` | `{!$Record.Applicant_Email__c}` | One address, or several separated by commas |
| `Subject` | `"Application Received — {!jobTitle}"` | Merge fields work, whether via formula or plain text |
| `Body` | `{!applicantEmailBody}` | Must be a Text Template resource; a Classic Email Template ID will not do |
| `Email Template ID` | *(leave blank)* | Classic Template IDs are not accepted by this action |
| `Sender Address` | Org-Wide Email Address | Set one up in Setup rather than sending from a personal address |

Wire a fault connector every time. `SendEmailException` as the failure type is UNVERIFIED (2026-10-20): Help-only; neither corpus holds it; the guide says only that the daily limit applies to Send Email actions in flows and that the org is notified by email and a debug-log entry when a counted email can't be sent (apexdev 264 L20162-20166).

**Why not an Email Alert:** an Email Alert binds its template at design time in Setup. Send Email lets both the recipient and the body vary at run time, which is the whole point here.

> Walked through end to end in `references/examples.md`, Example 2.

### Pattern 3: Bulk Internal Alert With Rate-Limit Awareness

**When to use:** Record-triggered Flow needs to notify many users during a bulk save (e.g., data-load alert to 200 case owners).

**Structure:**
1. Compute the User ID collection in advance.
2. Check the collection size; if > hourly limit threshold (10,000 notification actions, one action may carry many recipients: UNVERIFIED (2026-10-20): Help-only; neither corpus holds it for the fan-out), aggregate to a digest (single notification to a manager role rather than per-user).
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
| Bulk alert to many users at once | Custom Notification (Pattern 3) with rate-limit gate | Up to org limit; watch the 10,000 notification-actions/hour cap (pkg2_dev 264 L5916) |
| Alert to inactive Salesforce user | Email only | The Apex counterpart sends to a User ID "if this user is active" (apexref 262 L166770); that the Flow action behaves the same is UNVERIFIED (2026-10-20) |
| HTML-rich email to external | Email Alert with Classic Template | Flow's Send Email is plain-text / text-template only (UNVERIFIED (2026-10-20): Help-only; neither corpus holds it) |

---

## Recommended Workflow

1. **Confirm the channel and license:** Determine which notification channel the requirement calls for and verify the org has the required add-ons (Digital Engagement for SMS, Salesforce for Slack for Slack). Do not proceed with unavailable actions.
2. **Identify recipient wiring:** For Send Custom Notification, locate the User ID source on the triggering record. For Send Email, locate the email address field. Confirm whether a collection or single value is needed.
3. **Create prerequisite metadata:** For custom notifications, create the Custom Notification Type in Setup before building the Flow action. For Slack, confirm the workspace connection is active.
4. **Configure the action:** Add the appropriate action element (Send Email, Send Custom Notification, Send SMS, Post Message to Slack). Map all required inputs. For email, set Subject, Body (Text Template), and To address. For notifications, set recipientIds (collection), title, body, and optionally targetId.
5. **Add a fault connector:** Every notification action can fail. Wire a fault connector to capture the fault message (`$Flow.FaultMessage` is UNVERIFIED, 2026-10-20: not in either corpus), log or notify an admin, and avoid silent failures.
6. **Test with real User IDs and addresses:** Activate the Flow in a sandbox and trigger the notification. Verify delivery in the notification bell, inbox, Slack, or SMS as appropriate. Debug mode shows the action execution but not delivery confirmation.
7. **Review limits before go-live:** Confirm email volumes are within org limits. For custom notifications on high-volume automations, calculate worst-case hourly send rate against the 10,000 notification-actions/hour cap (pkg2_dev 264 L5916).

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

1. **Custom Notification recipientIds must be User IDs, not email addresses** — The Send Custom Notification action requires Salesforce User record IDs (15 or 18-character), or IDs that resolve to users: the Apex `send()` takes User, Account-team, Opportunity-team, Group and Queue IDs, up to 500 (apexref 262 L166767-166781). UNVERIFIED (2026-10-20): the Flow action's exact input contract and its runtime-error behavior.
2. **Send Email does not use Classic Email Templates** — UNVERIFIED (2026-10-20): Help-only; neither corpus holds it that it cannot reference a Letterhead or Classic template; `emailSimple` "sends an email by using flow resources" and `emailAlert` references a workflow email alert (api_meta 264 L71272-71275). Body content comes from a Flow Text Template resource or inline text; practitioners who expect template-driven emails use an Email Alert action instead.
3. **The 10,000 notification-actions/hour org limit** (pkg2_dev 264 L5916) **may drop notifications without a fault** — the limit figure is grounded; the quoted behavior ("no more notifications are sent in that hour, and all unsent notifications are lost"), the absence of an exception and of a fault email are UNVERIFIED (2026-10-20): Help-only; neither corpus holds it. Plan your own instrumentation rather than relying on a fault connector.
4. **SMS is invisible without Digital Engagement — no fallback action appears** — UNVERIFIED (2026-10-20): Help-only; neither corpus holds it.
5. **Slack Post Message requires an active connected workspace, not just package installation** — UNVERIFIED (2026-10-20): Help-only; neither corpus holds it (the `slackPostMessage` action type itself is grounded, api_meta 264 L71465-71466).
6. **Custom Notification title is capped at 250 characters (body 750), but clients truncate the *display* earlier** — the 250/750 caps are the Apex `CustomNotification` limits (apexref 262 L166708, L166711) and truncation by channel or app is documented (L166724); UNVERIFIED (2026-10-20): Help-only for the 120/320 display figures. Titles render to about 120 characters and bodies to about 320 before an ellipsis. Do not conflate the two numbers: 250/750 is what the API accepts, 120/320 is what a user reads. Front-load the actionable text.
7. **Email deliverability setting "No access" blocks all outbound emails** — UNVERIFIED (2026-10-20): Help-only; neither corpus holds it (the corpus names Deliverability only as a Setup page, api_meta 264 L118088). Sandbox orgs default to this setting; Flow's Send Email succeeds in the flow but nothing leaves the org. Verify deliverability is `All email` in Setup before testing.
8. **Custom Notifications to inactive users don't deliver** — the Apex `send()` delivers to a User ID only "if this user is active" (apexref 262 L166770); that the Flow action raises no error is UNVERIFIED (2026-10-20). Filter recipient collections by `IsActive=true` before passing to the action.
9. **Slack message character limit (~40k) + formatting caveats** — UNVERIFIED (2026-10-20): Help-only; neither corpus holds it.
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
