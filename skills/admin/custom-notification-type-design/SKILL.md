---
name: custom-notification-type-design
description: "Use when designing Custom Notification Types that fire via Flow, Apex, or Process Builder to Lightning bell, desktop, mobile (push), and Slack. Covers channel enablement, targeting, deliverability, consent, and anti-spam discipline. NOT for actually sending one from Flow or Apex, or the recipient limit — use admin/custom-notification-types. NOT for email templates and alerts — use admin/email-templates-and-alerts."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Security
triggers:
  - "custom notification salesforce setup"
  - "send desktop push notification flow"
  - "salesforce bell notification from apex"
  - "slack custom notification salesforce"
  - "notification fatigue prevention"
  - "custom notification type isn't working"
  - "we're having issues with custom notification type"
tags:
  - admin
  - notifications
  - custom-notification-type
  - push
  - slack
inputs:
  - What triggers the notification
  - Target audience and channels (bell / desktop / mobile / Slack)
  - Frequency expectations
outputs:
  - Custom Notification Type setup (metadata)
  - Targeting and consent design
  - Throttling / de-duplication plan
  - Observability + governance
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Custom Notification Type Design

A Custom Notification Type is the *definition* of a notification: its label, its
API name, and which delivery channels it is allowed to use. It is not the send.
Designing one badly is cheap, invisible, and permanent — the notification still
"works" in the sense that `send()` returns without an exception, and the user
still never sees it, or sees it forty times a day and mutes the whole channel.

Two failure shapes dominate, and they need opposite fixes:

| Symptom | Actual cause | Where it is designed away |
|---|---|---|
| "The notification never arrives" | One of four independent delivery gates is closed | The delivery chain, below |
| "Users muted the bell / uninstalled the app" | Every event became a notification | Targeting, throttling, and the registry |

**Scope.** This skill owns the *design and governance* decisions: which channels
a type should declare, who should receive it, how often, what the deep link
opens, and how the org keeps the set of notification types from sprawling. The
mechanics of the send — `Messaging.CustomNotification`, the Flow
`customNotificationAction`, the 500-value recipient cap, bulk send patterns —
belong to `admin/custom-notification-types`. Those appear below only where they
constrain a design choice. Email alerts are `admin/email-templates-and-alerts`.

---

## Before Starting

1. **Name the action the recipient will take.** If the honest answer is "be
   aware", this is a report subscription, a dashboard, or a Chatter post — not a
   notification. Write the action down; it becomes the review criterion later.

2. **Decide who *cannot* act.** Notifications to people without permission to do
   the thing are the fastest route to mute. The recipient set is the design, not
   an afterthought.

3. **Find out whether the org already has a type that covers this.** A custom
   notification type is org-wide and cheap to create, which is exactly why orgs
   accumulate dozens of near-duplicates that fragment the user's mental model.

4. **Establish the channel budget.** Bell and desktop are one checkbox
   (`desktop`); mobile push is a separate one (`mobile`). Slack is a separate
   notification type entirely — see below. Every channel you enable is a channel
   you have to justify at review.

---

## Core Concepts

### The delivery chain has four independent gates

A notification reaches a human only if *all four* of these are open. Three of
them are outside the sending code, which is why "the Apex ran and nobody got
anything" is the single most common support ticket in this area.

```text
1. Type definition        CustomNotificationType.desktop / .mobile
                          (Setup → Notification Builder → Notification Types)
        ↓
2. Org delivery settings  NotificationTypeConfig → notificationChannels
                          { desktopEnabled, mobileEnabled, slackEnabled }
                          and appSettings → { connectedAppName, enabled }
                          (Setup → Notification Delivery Settings)
        ↓
3. User preference        The recipient's own notification settings
        ↓
4. Device / browser       Mobile app installed with push permission granted;
                          browser notification permission granted
```

Gate 2 is the one nobody remembers. `NotificationTypeConfig` carries an
`appSettings` array of `{ connectedAppName, enabled }` — *per connected app*.
Mobile push does not reach a device because "mobile is checked on the type"; it
reaches a device because a connected app (the Salesforce mobile app, a Field
Service app, a branded app built with the Mobile SDK) is enabled for that
notification type in Notification Delivery Settings. A new notification type
plus an untouched delivery setting is a notification that silently goes nowhere
on mobile.

### The two metadata types, and why deployment surprises people

| Metadata type | Suffix | Directory | Since | Carries |
|---|---|---|---|---|
| `CustomNotificationType` | `.notiftype` | `notificationtypes` | API 46.0 | The type: label, API name, description, `desktop`, `mobile`, action groups |
| `NotificationTypeConfig` | `.config` | `notificationTypeConfig` | API 48.0 | Org delivery settings: which channels and which connected apps are live |

They deploy separately. A change set or package that carries the type but not
the config moves the definition and leaves the delivery settings at whatever the
target org already had — which for a brand-new type is "nothing enabled for any
connected app". Treat the pair as one deployable unit.

### `slack` on the type is not the Slack feature

`CustomNotificationType` has a `slack` field. The Metadata API Developer Guide
describes it as **"Reserved for future use."** Do not check it, do not
reverse-engineer meaning from it, and do not conclude from it that Salesforce
cannot notify Slack — it can.

The real Slack path is a **separate notification type**, created through
Notification Builder's Slack flow ("Create a Slack Notification"), which binds
the notification to a Slack app and a Slack message configuration and is sent by
a Send Notification action. Independently, `NotificationTypeConfig` →
`notificationChannels` does carry a real `slackEnabled` boolean, so Slack is a
first-class delivery channel at the org-settings layer. Design Slack as its own
type with its own audience and its own review — not as a fourth checkbox on the
desktop/mobile type.

### Recipient resolution is polymorphic, and that is a design lever

The Flow action's `recipientIds` input is documented as accepting several ID
kinds, each of which fans out differently:

| ID you pass | Who receives it | Prerequisite |
|---|---|---|
| `UserId` | That user | User must be active |
| `GroupId` | All active group members | — |
| `QueueId` | All active queue members | — |
| `AccountId` | All active **Account Team** members | Account teams enabled |
| `OpportunityId` | All active **Opportunity Team** members | Team selling enabled |

"Values can be combined in a list up to 500 values." That is a cap on the number
of *IDs you pass*, not on the number of humans reached — one `GroupId` can be
hundreds of people. Design the recipient expression at the ID level: passing one
queue ID is both cheaper and more maintainable than resolving 200 user IDs in
Flow, and it stays correct when queue membership changes.

The design consequence: **prefer a group or queue ID over an enumerated user
list**, because membership then has an owner and a maintenance path. An explicit
user list is a snapshot that starts rotting the day it ships.

### Deep links: `targetId` versus `targetPageRef`

Exactly one of the two is required. `targetId` is a record ID and is the right
answer for anything record-shaped — the platform resolves it to the record home
on every surface, so the same notification works on desktop and in the mobile
app without you writing a URL.

`targetPageRef` takes a serialized `PageReference` and is the escape hatch for
non-record destinations (a tab, a custom component page, an external URL). It is
strictly more work and strictly more fragile: you are now maintaining a
navigation contract by hand.

Hand-built `/lightning/r/...` URLs are the worst of both. They are Lightning-only
strings that bypass the platform's own navigation resolution, and they hardcode
an assumption about which app the recipient is in.

### Actionable mobile notifications (action groups, Beta)

`CustomNotificationType` supports an `actionGroups` array — labelled Beta in the
Metadata API Developer Guide — which lets a mobile push carry buttons the user
can press without opening the record. Each action has an `actionLabel`,
`actionName`, an `actionType` of either `NotificationApiAction` or `Share`, and
for `NotificationApiAction` an `actionTarget` naming the Apex class that
implements it. Apex selects the group at send time with `setActionGroupId(...)`.

This is the one lever that genuinely raises mobile notification value rather than
just its volume: "Approve / Reject" in the notification shade is a different
product from "tap to open a record and hunt for the button". Being Beta, it is a
design option to *evaluate*, not to assume, and it is worth confirming current
status before committing a roadmap to it.

---

## Common Patterns

### Pattern A — one type per *audience contract*, not per feature

Create a notification type for a class of interruption a user can reason about
("Case escalation", "Approval needed"), not for each Flow that wants to send
something. Users tune preferences per type, so a type is the unit of consent. Ten
types with clear names beat forty named after the projects that shipped them.

### Pattern B — the throttle lives on the record, not in the sender

A `Last_Notified_At__c` datetime plus a `Notification_Count_Today__c` on the
subject record makes suppression a data question rather than a code question,
survives across Flow and Apex senders, and is queryable when someone asks "why
did this fire six times". Detail in
[`references/examples.md`](references/examples.md), Example 3.

### Pattern C — digest for anything that is not time-critical

A scheduled job that sends one notification listing N items, deep-linked to a
list view or a report, converts N interruptions into one. This is the single
highest-leverage design move available and it is almost never taken, because
per-event notification is what the requirement literally said.

### Pattern D — registry as custom metadata, not as a wiki page

A `Notification_Registry__mdt` record per type — owner, trigger, intended
recipient action, channels, review date — deploys with the org, is readable from
Apex with `getAll()` at no SOQL cost, and can be asserted on in a test. A
spreadsheet cannot.

### Pattern E — separate the "urgent" type from the "informational" type

If one type carries both, users have exactly two options: mute everything or
tolerate everything. Splitting by urgency lets a user keep the pager and silence
the newsletter, which is what they wanted the whole time.

---

## Decision Guidance

| Situation | Design | Why |
|---|---|---|
| Recipient must act within minutes | Own type, `desktop` + `mobile`, deep link to the record | Interruption is justified; make acting one tap |
| Recipient should know today | Own type, `desktop` only | Bell persists; push does not need to |
| Recipient should know this week | Digest, or no notification at all | A report subscription is the honest tool |
| Audience is a role, queue, or team | Pass the `GroupId` / `QueueId` | Membership has an owner |
| Audience is "these five people" | Still a group | The list will be wrong within a quarter |
| Destination is a record | `targetId` | Platform resolves it per surface |
| Destination is a tab or custom page | `targetPageRef` | The only supported alternative |
| Destination is a filtered list | Reconsider the notification | If you cannot name the record, the recipient cannot act |
| Target is a Slack channel | Separate Slack notification type | The `slack` field on `CustomNotificationType` is reserved |
| Volume could exceed a few hundred sends per hour | Digest or queue-level fan-out | Notification actions are rate-limited org-wide |
| Same event already notified in the last N minutes | Suppress | Duplicate interruption costs more than a missed one |

---

## Recommended Workflow

1. **Write the recipient's action in one sentence.** "The on-call agent
   reassigns the case." If you cannot write it, stop — the requirement is
   reporting, not notification, and building it as a notification will make the
   org's real notifications less effective.
2. **Choose the audience as an ID expression**, preferring a queue or public
   group ID over enumerated users, and record which prerequisite each ID kind
   needs (account teams enabled, team selling enabled) so the design is
   reproducible in another org.
3. **Declare the minimum channels on the type** — `desktop` first, `mobile` only
   when the action is time-critical — and design Slack, if needed, as its own
   notification type rather than a channel on this one.
4. **Configure and deploy `NotificationTypeConfig` alongside the type**, naming
   each connected app that must be enabled. Verify on a real device, not in the
   browser: gates 2 and 4 fail silently and independently.
5. **Design the deep link as `targetId` where the destination is a record**, and
   only fall back to `targetPageRef` for non-record destinations. Never build a
   raw Lightning URL.
6. **Specify the throttle before the first send** — minimum interval per record,
   daily cap per user, and what happens to suppressed events (dropped, or rolled
   into a digest).
7. **Register the type** with owner, intended action, channels, and a review
   date, and define what "working" will be measured by so the quarterly review
   has evidence instead of opinions.

---

## Review Checklist

- [ ] The recipient's action is written down and the recipient has permission to do it
- [ ] Audience is expressed as group/queue IDs where possible, not enumerated users
- [ ] Prerequisites for the chosen ID kinds are recorded (account teams, team selling)
- [ ] `mobile` is enabled only where the action is time-critical
- [ ] `NotificationTypeConfig` is part of the same deployable unit as the type
- [ ] Every connected app that must deliver this type is enabled in delivery settings
- [ ] Delivery verified end-to-end on a real mobile device, not just desktop
- [ ] `slack` is unchecked on the `CustomNotificationType`; Slack has its own type if needed
- [ ] Deep link uses `targetId` for record destinations
- [ ] Title fits within 250 characters and body within 750 *after* merge fields resolve
- [ ] Throttle interval and daily cap are specified, and suppressed events have a defined fate
- [ ] A digest alternative was explicitly considered and rejected with a reason
- [ ] Registry entry exists with owner, intended action, and review date
- [ ] Success metric is defined and instrumented before launch
- [ ] Notification body leaks no field the recipient may not have access to

---

## Salesforce-Specific Gotchas

Full detail in [`references/gotchas.md`](references/gotchas.md).

1. **Four independent delivery gates**, three of them outside your code.
2. **`NotificationTypeConfig` does not travel with the type** unless you deploy it.
3. **Mobile push needs the connected app enabled** for that notification type.
4. **`slack` on `CustomNotificationType` is "Reserved for future use"** — Slack is a separate type.
5. **500 is a cap on IDs passed, not on humans reached.**
6. **`AccountId` and `OpportunityId` recipients need teams enabled** or they resolve to nobody.
7. **Title 250 / body 750** — merge fields make this a runtime property, not a design-time one.
8. **`WITH USER_MODE` on the type lookup** turns a missing permission into a query that returns no rows.
9. **Notification actions are rate-limited org-wide**, so one bulk job can starve every other notification.
10. **Inactive users silently drop out** of every recipient expression.
11. **The bell has no acknowledgement**; delivery is not readership, and neither is measurable without instrumentation you add.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Notification design record | Recipient action, audience expression + prerequisites, channels, deep-link target, throttle rule, success metric |
| `CustomNotificationType` metadata | `.notiftype` with `desktop` / `mobile` set deliberately, `slack` left alone, and a description written as prose a human reads next to the type name |
| `NotificationTypeConfig` metadata | `.config` enumerating enabled channels and every connected app that must deliver |
| Throttle design | Field(s) on the subject record, suppression window, and the fate of suppressed events |
| Registry entry | `Notification_Registry__mdt` row: owner, trigger, intended action, channels, review date |
| Measurement plan | What is counted, where it is stored, and the engagement threshold that triggers redesign |
| Deployment note | The type and its config as one unit, plus the post-deploy device verification step |

---

## Related Skills

- `admin/custom-notification-types` — the send itself: `Messaging.CustomNotification`,
  the Flow action, the 500-value recipient cap, bulk send patterns. Read it when
  you are writing the sender rather than deciding what the notification should be.
- `admin/chatter-notification-tuning` — the other org-wide notification surface
  competing for the same attention budget
- `admin/email-templates-and-alerts` — the channel to route non-urgent content to
  instead of adding another push
- `admin/approval-processes` — the most common legitimate source of an actionable
  notification, and the one where action groups pay off most
- `admin/permission-sets-vs-profiles` — the access model that decides whether a
  recipient can act on what you notified them about
