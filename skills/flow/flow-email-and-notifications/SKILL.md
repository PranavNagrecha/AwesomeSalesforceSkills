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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Flow Email and Notifications

Use this skill when a Salesforce Flow needs to deliver a message — email, in-app notification, SMS, or Slack — to users or external addresses. Covers the Send Email action, Send Custom Notification action, SMS via Digital Engagement, and Slack via the Salesforce for Slack integration. NOT for creating or managing email templates in Setup (use admin/email-templates-and-alerts), and NOT for Email Alert workflow actions.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Notification channel:** Does the requirement need email, the in-app bell icon, a mobile push, SMS, or Slack? Each uses a different action and has different licensing.
- **Recipient type:** Is the recipient a Salesforce User (requires 15 or 18-char User ID for custom notifications), or an arbitrary email address (plain string for Send Email)?
- **Add-on licenses:** SMS requires Digital Engagement / Messaging. Slack requires the Salesforce for Slack integration configured in the org.
- **Email content source:** Flow's Send Email action uses a plain text body or a Flow `Text Template` resource — it does NOT use Classic Email Templates from Setup. That distinction is a frequent source of confusion.
- **Volume:** Custom Notifications are rate-limited at 1,000 per hour per org. Email sends count against the org's daily email limit (1,000 mass emails/day for standard orgs).

---

## Core Concepts

### Send Email Action vs Email Alert

Flow's **Send Email** core action is a standalone action element distinct from the **Email Alert** used in Workflow Rules and Process Builder. Key differences:

- Send Email in Flow supports a plain text body written inline or via a Text Template resource. It does NOT reference Classic Email Templates from Setup.
- Send Email supports recipients as either a literal email address string or a User record ID.
- Email Alerts (legacy) reference a Classic Email Template and are configured in Setup under Workflow. They can be invoked from Flow as an action but that is a different pattern.
- Single outbound email size limit is 5 MB. Daily org limit for standard orgs is 1,000 mass emails per day; individual transactional sends are higher but still subject to SendEmailException limits.

### Custom Notifications (Bell Icon)

**Send Custom Notification** is a Flow core action that delivers a message to the in-app notification bell and, if the user has the Salesforce mobile app installed, as a push notification.

Requirements and constraints:
- A **Custom Notification Type** metadata record must exist before the action can be configured. Create it in Setup under Notification Builder > Custom Notifications.
- The `recipientIds` input must be a **collection of User IDs** (15-char or 18-char Salesforce User IDs). It does not accept email addresses or Contact IDs.
- The notification `body` supports `{!variable}` merge fields from the Flow. HTML is NOT rendered — the body is plain text.
- The `targetId` field (optional) links the notification to a specific record, so tapping the bell icon on mobile navigates to that record.
- Org limit: **1,000 custom notifications per hour** per org. Exceeding this causes the action to fail and the Flow will follow its fault path.

### SMS via Flow

Flow does not include a native SMS action. Sending SMS requires:

1. **Digital Engagement** (also called Messaging) add-on license.
2. With the add-on, a **Send SMS** action becomes available in Flow Builder.
3. The recipient must be a phone number in the format the messaging channel supports (typically E.164 format: `+15551234567`).
4. Without this license, the Send SMS action is absent from the action palette. Do not attempt workarounds using Apex callouts inside Flow without understanding callout limits and async requirements.

### Slack Notifications via Flow

Flow can post messages to Slack when the **Salesforce for Slack** integration is installed and a Slack workspace is connected:

1. Connect a Slack workspace in Setup under Slack > Connected Slack Apps.
2. The **Post Message to Slack** action becomes available in Flow Builder.
3. The action requires a Slack Channel ID or channel name, and the message text.
4. The integration uses OAuth-based Slack app authentication; the connected workspace must be active.
5. Without the integration, the action is not available.

---

## Common Patterns

### Pattern 1: In-App Bell Notification on Record Change

**When to use:** A record-triggered or autolaunched Flow needs to alert a specific Salesforce user immediately (e.g., escalation to owner, approval request follow-up).

**How it works:**
1. Create a Custom Notification Type in Setup (e.g., "Case Escalation Alert").
2. In the Flow, use **Get Records** to retrieve the User record associated with the target (e.g., Case Owner).
3. Create a Text Collection variable and assign the User ID (`{!caseOwner.Id}`) to it.
4. Add a **Send Custom Notification** action. Set `Notification Type` to the Custom Notification Type API name, `recipientIds` to the User ID collection, `title` to a short label, `body` to a Text Template or formula with merge fields.
5. Add a fault connector on the action — if the hourly limit is reached, it will fault.

**Why not email:** Bell notifications are synchronous with the transaction, appear immediately in the app, and do not require an email address. Email adds latency and inbox noise for internal user alerts.

### Pattern 2: Confirmation Email to External Contact

**When to use:** A Flow needs to email a non-Salesforce user (customer, partner, applicant) with dynamic content after a record creation or form submission.

**How it works:**
1. In the Flow, retrieve the email address from the record (e.g., `{!contact.Email}`) or from a screen Flow input variable.
2. Create a **Text Template** resource in Flow to compose the body with merge fields.
3. Add a **Send Email** core action. Set `To` to the email address string, `Subject` to a formula or text, and `Body` to the Text Template resource.
4. Keep the sender as the org-wide email address or default sender — do not use a user's personal email unless configured.
5. Add a fault connector — SendEmailException will fault the action if limits are exceeded or the address is invalid.

**Why not Email Alert:** Send Email in Flow is more flexible for dynamic recipient and dynamic body. Email Alerts require a template fixed at design time in Setup.

---

## Decision Guidance

| Requirement | Recommended Channel | Key Condition |
|---|---|---|
| Notify internal Salesforce user in-app | Send Custom Notification | User ID must be available; Custom Notification Type must exist |
| Email external contact or customer | Send Email action (Flow) | Recipient is an email address string; body is a Text Template |
| Email from a fixed, managed template | Email Alert invoked from Flow | Template is a Classic Email Template; recipient is defined by the alert |
| Send SMS to a phone number | Send SMS action | Requires Digital Engagement add-on license |
| Post to Slack channel | Post Message to Slack | Requires Salesforce for Slack connected workspace |
| Bulk alert to many users at once | Custom Notification (collection) | Up to org limit; watch the 1,000/hour cap |

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

---

## Salesforce-Specific Gotchas

1. **Custom Notification recipientIds must be User IDs, not email addresses** — The Send Custom Notification action requires Salesforce User record IDs (15 or 18-character). Passing an email address string causes a runtime error that is often reported as "notification not delivered" rather than a clear field-level error.

2. **Send Email does not use Classic Email Templates** — Flow's Send Email action cannot reference a Letterhead or Classic HTML template from Setup. Body content must come from a Flow Text Template resource or an inline text value. Practitioners who expect template-driven emails must use an Email Alert action instead.

3. **1,000 custom notifications/hour org limit can fail silently without a fault connector** — When the limit is exceeded, the action faults. Without a fault connector, the Flow fails or rolls back (in record-triggered context), and the only trace is the Flow debug log or a system admin fault email.

4. **SMS is invisible without Digital Engagement — no fallback action appears** — If the Digital Engagement add-on is not provisioned, the Send SMS action does not appear in Flow Builder at all. There is no placeholder or error message. Practitioners who cannot find the action may not realize it is a license issue.

5. **Slack Post Message requires an active connected workspace, not just package installation** — Installing the Salesforce for Slack managed package does not automatically make the action work. An admin must authenticate and connect a Slack workspace in Setup. Flows built before the connection is established will fault at runtime.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Channel decision table | Which action to use for email, bell, SMS, or Slack |
| Recipient wiring plan | How to source User IDs or email addresses from the Flow context |
| Prerequisite checklist | Custom Notification Type setup, add-on licenses, Slack workspace |
| Limit review | Email daily limit, custom notification hourly cap, message size |

---

## Related Skills

- **admin/email-templates-and-alerts** — Use when the requirement involves managing Classic Email Templates, Email Alerts, or letterhead templates in Setup. NOT this skill.
- **flow/fault-handling** — Use alongside this skill: every notification action needs a fault connector designed intentionally.
- **admin/flow-for-admins** — Use for broader Flow type selection when notification is one of several automation requirements.
