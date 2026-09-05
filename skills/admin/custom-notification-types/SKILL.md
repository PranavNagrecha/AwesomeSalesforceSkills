---
name: custom-notification-types
description: "Custom Notification Types for desktop/mobile push alerts from Flow or Apex: type creation, target channels, Messaging.CustomNotification invocation, recipient limits, bulk notification patterns. NOT for choosing channels, consent, or notification-fatigue policy — use admin/custom-notification-type-design. NOT for email alerts — use admin/email-templates-and-alerts. Trigger keywords: notiftype, notificationtypes directory, customNotifTypeName, customNotificationAction, setNotificationTypeId, targetPageRef, NotificationTypeConfig."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
tags:
  - custom-notifications
  - messaging-customnotification
  - flow-actions
  - push-notifications
  - mobile
triggers:
  - "send custom notification from flow to record owner"
  - "messaging.customnotification apex bulk recipient limit"
  - "custom notification type setup for desktop and mobile"
  - "notification type id dynamic lookup flow apex"
  - "push notification salesforce mobile app flow"
  - "delivery guarantee and retry for custom notifications"
  - "custom notification type 500 recipient limit apex"
  - "notiftype file suffix and folder for custom notification type"
  - "custom notification deployed but nobody receives it"
  - "bell notification works but mobile push never arrives"
  - "send custom notification throws exception no target specified"
inputs:
  - Event triggering the notification
  - Target recipients (users, queues, groups)
  - Channels desired (desktop, mobile push)
  - Volume per day
outputs:
  - Custom Notification Type metadata
  - Flow action or Apex invocation pattern
  - Bulk send strategy
  - Monitoring and delivery verification plan
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Custom Notification Types

Activate when designing push or desktop notifications triggered from Flow, Apex, or process automation. Custom Notification Types replaced the older Chatter-only notification path; they support both desktop and mobile push channels, can be invoked from Flow or Apex, and have specific recipient limits that bite at scale.

## Before Starting

- **Define the notification type in Setup first.** Without a CustomNotificationType record, neither Flow nor Apex can send.
- **Know what the 500 cap counts.** `send(Set<String> users)` takes at most 500 *values*, and a Group or Queue Id is one value that fans out to every active member (Apex Reference Guide, `apexrefguide.txt:166766-166781`).
- **Choose channels.** Desktop and Mobile are independent checkboxes; Mobile requires the Salesforce mobile app and enabled push notifications.

## Questions to Ask Before Configuring

Ask these before creating the type; the answers decide the metadata, the send path, and the test. An LLM that skips them produces a type that deploys clean and delivers to nobody.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which channels must this reach — desktop bell, mobile push, or both?" | `desktop` and `mobile` are required booleans on the type and both default to `false` on the sObject; the send call cannot override them | The two flags on the `.notiftype`, and whether a real-device test is in scope |
| "Is the audience a list of people, or a membership?" | The 500 cap counts Ids, not recipients — one Queue or Group Id covers thousands, a hand-built user set does not | Whether a chunking loop is needed at all, or one group Id replaces it |
| "What does the recipient open when they tap it?" | A target is mandatory: omitting both `targetId` and `targetPageRef` throws, and a target the recipient can't read lands them on Insufficient Privileges | A record Id, a `pageReference`, or the documented dummy Id — decided, not defaulted |
| "How many notifications does the worst-hour burst produce?" | Ten push notification method calls per Apex transaction, and an hourly org push allocation that fails open to the bell | A fan-out sized in send *calls*, and a decision on suppressing bulk-load traffic |
| "Who is the running user when this fires — system context, or an end user?" | Sending needs the Send Custom Notifications permission, and the type lookup runs in user mode; both fail as something other than a permission error | The permission set that grants it, and a least-privileged test user |
| "Does this org already have a type that means the same thing?" | Type names are unique org-wide and not namespaced, so the second team to want "case escalated" collides with the first | A reuse-or-create decision before the name is burned |
| "Which orgs will this deploy to, and what resolves the type Id in each?" | The `0ML…` Id is org-specific; the manifest can't wildcard the type | A run-time lookup by `DeveloperName` and an explicit `package.xml` member list |

What a proper configuration adds over just clicking "New Custom Notification Type": the channels are asserted rather than assumed, the audience is expressed as the smallest set of Ids that describes it, the deploy carries the type *and* its delivery settings, and the failure modes that report as success are caught before a user does.

---

## Core Concepts

### Notification Type record

Created in Setup → Custom Notifications. Has a Name (label), API Name (DeveloperName), and channel checkboxes. DeveloperName is the handle used in Apex/Flow.

### Messaging.CustomNotification (Apex)

```
Messaging.CustomNotification n = new Messaging.CustomNotification();
n.setTitle('Opportunity Closed');
n.setBody('Opportunity ' + oppName + ' was won.');
n.setNotificationTypeId(typeId);
n.setTargetId(oppId);
n.send(new Set<String>{ userId });
```

`setNotificationTypeId` takes the `CustomNotificationType.Id`; resolve via SOQL or describe.

### Send Custom Notification (Flow Action)

Core action in Flow Builder. Accepts type API name, recipients (user ids, queue ids, group ids), title, body, target record id. Good for no-code paths.

### Recipient resolution

Recipient IDs can be User, Group (queue or public group). Notifications deliver to active users in the group.

## Common Patterns

### Pattern: Owner notification on record change

Record-triggered Flow → Decision → Send Custom Notification with `[$Record.OwnerId]`.

### Pattern: Apex bulk fan-out

Aggregate target user IDs into sets of 500; loop `n.send(batch)` per batch. Do not exceed 500 per call.

### Pattern: Type ID resolution via Custom Metadata

Store `NotificationTypes__mdt` with DeveloperName; Apex helper queries once per transaction and caches.

## Decision Guidance

| Need | Mechanism |
|---|---|
| No-code notification on record change | Flow + Send Custom Notification action |
| Bulk programmatic send (dozens+) | Apex Messaging.CustomNotification |
| Email + push | Separate email alert + custom notification |
| Delivery guarantee with retry | Queueable wrapper with retry; not built-in |
| Notifications only on desktop | Type with Desktop channel checked, Mobile unchecked |

## Recommended Workflow

1. **Answer the questions above**, then check whether the org already has a type that means the same thing: `SELECT DeveloperName, MasterLabel, Desktop, Mobile FROM CustomNotificationType`. Names are unique org-wide and not namespaced.
2. **Author the type**, not just the checkbox. Write `notificationtypes/<DevName>.notiftype-meta.xml` from `references/metadata-examples.md` §1 — `customNotifTypeName`, `masterLabel` as customer copy, `description`, and both channel booleans set deliberately. If the org manages delivery settings as metadata, add the paired `NotificationTypeConfig` entry from §2.
3. **Pick the send path.** Flow for record-triggered, single-audience sends (`references/metadata-examples.md` §3, and `flow/flow-email-and-notifications` for the Builder-side inputs); Apex when the audience is computed, the volume needs async placement, or you need try/catch around the send (§4, and `apex/apex-custom-notifications-from-apex` for the class). Either way the type Id is resolved at run time by `DeveloperName` — never pasted.
4. **Resolve the audience and the target** using §5 and §6: the smallest set of Ids that describes the audience, and an explicit `targetId`, `targetPageRef`, or documented dummy Id.
5. **Lint before deploy.** `python3 scripts/check_custom_notification_types.py --manifest-dir force-app/main/default` — it fails on a type with no channel enabled and on a hard-coded `0ML…` Id in Apex or in a Flow's `customNotificationAction`, and reports types no Flow or class references.
6. **Deploy the type before its callers** with the explicit `package.xml` from §7 (this type has no wildcard support), using the retrieve/validate/deploy commands in §8.
7. **Verify three separate things** per §9: the row exists with a channel enabled, the bell lights up for a real recipient, and the tap lands on the target as that recipient — not as an admin. A green bell is not evidence that push works.

## Review Checklist

- [ ] Custom Notification Type exists with correct channels
- [ ] Type ID resolved dynamically, not hard-coded
- [ ] Recipients bulked into 500-per-send chunks
- [ ] Title and body within the documented caps — title ≤ 250 characters, body ≤ 750 (`apexrefguide.txt:166830`, `apexrefguide.txt:166860`); both are required to send
- [ ] Target set deliberately — a record Id for deep-linking, a `targetPageRef`, or the documented dummy Id `000000000000000AAA`; omitting both throws (`apexrefguide.txt:166572-166575`)
- [ ] Mobile channel verified with mobile push enabled
- [ ] Error handling for send() failures

## Salesforce-Specific Gotchas

1. **`send()` throws for some failures and stays silent for others.** It does throw when no target is set at all (`apexrefguide.txt:166573`) and can throw generally (`apexrefguide.txt:166648`) — but a recipient who is inactive is simply skipped, because delivery is documented as "sent to this user, if this user is active" (`apexrefguide.txt:166770`). A clean `send()` is not evidence anyone received it; monitor via debug log or platform events.
2. **Mobile push requires Connected App push credentials.** Setup → Mobile → Notification Settings must be configured.
3. **Custom notifications do not respect user notification preferences for desktop.** Users cannot opt out per-type from the bell.

## Output Artifacts

| Artifact | Description |
|---|---|
| Notification Type catalog | Type × channel × recipients × business event |
| Apex helper class | Type ID resolver + bulk send wrapper |
| Flow action template | Reusable subflow for record-owner notifications |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing the `.notiftype` XML, the `NotificationTypeConfig` pairing, the Flow `customNotificationAction` element, the Apex send, `package.xml`, the retrieve/deploy commands, or the post-deploy verification |
| `references/gotchas.md` | A notification deploys and delivers to nobody, the bell works but push doesn't, `send()` throws, the fan-out dies partway, or the type lookup fails for non-admins |
| `references/examples.md` | Sizing a requirement: which shapes fit a Flow send, which need Apex, and when a custom notification is the wrong channel entirely |
| `references/llm-anti-patterns.md` | Reviewing AI-generated notification code before you run it |
| `references/well-architected.md` | Justifying the channel choice against the pillars, or chasing the official source behind a claim here |
| `templates/custom-notification-types-template.md` | Capturing the decisions — channels, audience shape, target, volume — before any XML is written |
| `scripts/check_custom_notification_types.py` | Linting `notificationtypes/`, `flows/`, and `classes/` in a DX tree before deploying |

---

## Related Skills

- `admin/custom-notification-type-design` — the design layer above this one: which notifications should exist at all, the four delivery gates, consent, and notification-fatigue policy. This skill owns the type metadata, the Flow/Apex send, the channels, and the limits; that one owns whether to send.
- `apex/apex-custom-notifications-from-apex` — owns the Apex send code: the class, the bulk wrapper, async placement, and error handling. `references/metadata-examples.md` §4 keeps only a call-shape excerpt.
- `flow/flow-email-and-notifications` — the Flow Builder view of the Send Custom Notification action, its input labels, and the other Flow-side notification channels.
- `lwc/lwc-toast-and-notifications` — a different mechanism: `ShowToastEvent` toasts render inside one open component in one browser tab and vanish. They are not custom notifications, do not reach the bell, and never reach a phone.
- `admin/chatter-notification-tuning` — the Chatter side of org notification volume, when the real complaint is "too many notifications" rather than "this one won't send".
- `admin/email-templates-and-alerts` — the email path, for audit-trail messages and recipients without a Salesforce license.
