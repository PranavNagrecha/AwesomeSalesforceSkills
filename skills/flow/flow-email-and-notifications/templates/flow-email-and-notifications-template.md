# Flow Email and Notifications — Work Template

Use this template when designing or reviewing notification actions in a Salesforce Flow.

## Scope

**Skill:** `flow/flow-email-and-notifications`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer each of these before configuring any notification action:

| Question | Answer |
|---|---|
| What notification channel is required? | Email / In-app bell / SMS / Slack |
| Who is the recipient — internal User or external contact? | |
| Is the recipient a Salesforce User with a User ID available? | Yes / No |
| Is Digital Engagement provisioned (for SMS)? | Yes / No / Unknown |
| Is Salesforce for Slack installed and workspace connected (for Slack)? | Yes / No / Unknown |
| What is the email or notification body content? Dynamic or fixed? | |
| Estimated sends per hour at peak? | |

---

## Channel Selection

Based on the context above, select the action:

- [ ] **Send Email** — external contact, arbitrary email address, dynamic body via Text Template
- [ ] **Send Custom Notification** — internal Salesforce User, in-app bell + mobile push; requires Custom Notification Type
- [ ] **Send SMS** — requires Digital Engagement license; recipient must be a phone number
- [ ] **Post Message to Slack** — requires Salesforce for Slack + active workspace connection

---

## Prerequisite Checklist

Complete before building the Flow action:

- [ ] For Send Custom Notification: Custom Notification Type created in Setup > Notification Builder > Custom Notifications
  - Type API Name: ___________________________________
- [ ] For Send SMS: Digital Engagement license confirmed
- [ ] For Post Message to Slack: Connected workspace confirmed in Setup > Slack; Channel ID obtained: ___________________________________
- [ ] For Send Email: Org-Wide Email Address configured for sender identity

---

## Action Configuration Plan

### Notification Action: [Action Name]

| Field | Value / Source |
|---|---|
| Action type | Send Custom Notification / Send Email / Send SMS / Post Message to Slack |
| Recipient source | Field: _____________________________________ |
| Recipient type | User ID / email address / phone number / Slack Channel ID |
| Content source | Text Template: _____________ / Inline text / Formula |
| Subject (email) | |
| Body / Message | |
| Target Record ID (notification) | {!$Record.Id} or other |
| Fault connector target | Log record / Admin email / Other |

---

## Merge Fields Used

List all Flow variables and record fields referenced in the notification content:

| Merge Field | Source | Example Value |
|---|---|---|
| {!variableName} | | |

---

## Limit Review

| Limit | Value | Estimated Usage | OK? |
|---|---|---|---|
| Custom notifications/hour | 1,000 per org | | |
| Daily email sends (standard org) | 1,000 mass emails/day | | |
| Single email size | 5 MB | | |

---

## Fault Handling Plan

- Fault connector destination: ___________________________________
- `$Flow.FaultMessage` captured to: ___________________________________
- Admin notification on failure: Yes / No

---

## Review Checklist

Copy and complete before marking work done:

- [ ] Custom Notification Type exists before Send Custom Notification action is used
- [ ] recipientIds is a User ID collection (not email addresses)
- [ ] Send Email body is a Text Template or inline text — not a Classic Email Template reference
- [ ] Every notification action has a fault connector
- [ ] Volume is within org email and custom notification hourly limits
- [ ] SMS or Slack actions have license/integration prerequisites confirmed
- [ ] Notification body contains no HTML tags (plain text only for bell notifications)

---

## Notes

Record any deviations from the standard pattern and the reason:

-
