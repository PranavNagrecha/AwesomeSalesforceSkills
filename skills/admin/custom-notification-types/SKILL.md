---
name: custom-notification-types
description: "Custom Notification Types for desktop/mobile push alerts from Flow or Apex: type creation, target channels, Messaging.CustomNotification invocation, recipient limits, bulk notification patterns. NOT for email alerts (use email-templates-and-alerts). NOT for in-app bell notifications alone (use chatter-feed-customization)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Custom Notification Types

Activate when designing push or desktop notifications triggered from Flow, Apex, or process automation. Custom Notification Types replaced the older Chatter-only notification path; they support both desktop and mobile push channels, can be invoked from Flow or Apex, and have specific recipient limits that bite at scale.

## Before Starting

- **Define the notification type in Setup first.** Without a CustomNotificationType record, neither Flow nor Apex can send.
- **Know the recipient limit.** Up to 500 recipients per `send()` call.
- **Choose channels.** Desktop and Mobile are independent checkboxes; Mobile requires the Salesforce mobile app and enabled push notifications.

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

1. Create Custom Notification Type in Setup with appropriate channels.
2. Decide Flow vs Apex invocation path based on declarative vs code context.
3. Resolve Notification Type ID dynamically (SOQL or CMDT).
4. Build invocation with proper title / body / target record.
5. For bulk: batch recipients in chunks of 500.
6. Test delivery on desktop and mobile (requires app + push permissions).
7. Add monitoring — notification failures are silent; check debug logs.

## Review Checklist

- [ ] Custom Notification Type exists with correct channels
- [ ] Type ID resolved dynamically, not hard-coded
- [ ] Recipients bulked into 500-per-send chunks
- [ ] Title and body under character limits (Title ≤ 64 chars, Body ≤ 750)
- [ ] Target record ID set for deep-linking on mobile
- [ ] Mobile channel verified with mobile push enabled
- [ ] Error handling for send() failures

## Salesforce-Specific Gotchas

1. **Send failures are silent.** The send() call does not throw on invalid recipient IDs; monitor via debug log or platform events.
2. **Mobile push requires Connected App push credentials.** Setup → Mobile → Notification Settings must be configured.
3. **Custom notifications do not respect user notification preferences for desktop.** Users cannot opt out per-type from the bell.

## Output Artifacts

| Artifact | Description |
|---|---|
| Notification Type catalog | Type × channel × recipients × business event |
| Apex helper class | Type ID resolver + bulk send wrapper |
| Flow action template | Reusable subflow for record-owner notifications |

## Related Skills

- `flow/flow-actions-core` — Flow core actions
- `admin/email-templates-and-alerts` — email path
- `mobile/mobile-push-configuration` — mobile push setup
