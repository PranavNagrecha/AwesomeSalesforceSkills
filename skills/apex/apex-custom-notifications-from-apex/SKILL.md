---
name: apex-custom-notifications-from-apex
description: "Use when sending Custom Notifications (bell icon / mobile push) from Apex via `Messaging.CustomNotification`. Covers target resolution, Notification Type discovery, recipient limits, and async-safe sending. NOT for email (Messaging.SingleEmailMessage), Chatter @mentions, Flow-triggered notifications, or Mobile Publisher push."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "send a bell/push notification to a specific user from Apex"
  - "Custom Notification Type ID lookup is failing in my trigger"
  - "notification body is exceeding the character limit silently"
  - "notify a queue or group of users when a record changes"
  - "Custom Notification failing with INVALID_RECIPIENT_IDS"
tags:
  - apex-custom-notifications-from-apex
  - messaging
  - push-notifications
  - notification-type
inputs:
  - "the Custom Notification Type DeveloperName"
  - "recipient Ids (Users, Groups, or Queue Ids)"
  - "the target record Id and sender's title/body text"
outputs:
  - "a Messaging.CustomNotification builder invocation that respects limits and recipient rules"
  - "async-safe sending patterns for triggers"
  - "error handling that surfaces INVALID_RECIPIENT_IDS / INVALID_NOTIFICATION_TYPE_ID"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Apex Custom Notifications From Apex

Activates when Apex code constructs and sends `Messaging.CustomNotification` — the supported API for bell icon alerts and mobile push from Apex. Produces compliant recipient handling, async-safe sending, and proper error surfacing.

---

## Before Starting

- Does the Custom Notification Type already exist in the org (Setup → Custom Notifications)? You cannot create it from Apex; without it there is nothing to send.
- Who is the intended audience — Users, Queue members, or public/private Group members? Only these Id types are valid.
- Is this fired from a trigger? `send()` can be called synchronously, but failures raise `CustomNotificationException`. In a before trigger or the hot DML path, push to async.
- What's the expected volume? Each `send()` targets a single notification type with a single body — bulk audiences (>100 recipients) use one send per notification with a recipient set.

---

## Core Concepts

### The Notification Type Id Is Required, Fetched At Runtime

Every `Messaging.CustomNotification` must be sent with `setNotificationTypeId(...)` populated. The Id lives on the `CustomNotificationType` SObject — queried by DeveloperName:

```apex
CustomNotificationType t = [SELECT Id FROM CustomNotificationType
                            WHERE DeveloperName = 'Case_Escalation' LIMIT 1];
```

This query consumes 1 SOQL per run. Cache the Id at a class level if you send from a hot path.

### Recipients Are Ids, And They Must Be Valid

`setRecipientIds(Set<String> ids)` accepts User Ids (`005`), Group Ids (`00G`), or Queue Ids (`00G`, since Queues are a Group subtype). Passing a Contact, Account, or arbitrary record Id throws `INVALID_RECIPIENT_IDS`. Deactivated User Ids are accepted but the notification silently disappears.

Maximum 500 recipients per send call. For broader audiences, batch the audience and call `send()` multiple times, or use a Queue Id which expands server-side.

### Body And Title Are Truncated Silently On Mobile Push

The `setTitle` and `setBody` methods accept long strings, but mobile push payloads truncate to a platform-dependent length (roughly 200 characters for body on iOS, shorter on Android). The in-app bell notification retains the full text. Code that assumes the recipient sees the full body is wrong for mobile users.

### Sync Sends Throw On Governor Or Setup Failures

`cn.send(...)` is synchronous and can throw `Messaging.CustomNotificationException` for bad recipient ids, missing notification type, or rate-limit issues. In a trigger, an unhandled exception aborts the DML transaction and confuses the user. Wrap and surface gracefully or move to Queueable.

---

## Common Patterns

### Pattern 1: Send To A Single User With Record Context

**When to use:** Notify the owner of a record when status changes.

**How it works:**

```apex
public with sharing class CaseEscalationNotifier {
    private static final String TYPE_DEV_NAME = 'Case_Escalation';
    @TestVisible private static Id typeId;

    private static Id getTypeId() {
        if (typeId == null) {
            typeId = [SELECT Id FROM CustomNotificationType
                      WHERE DeveloperName = :TYPE_DEV_NAME LIMIT 1].Id;
        }
        return typeId;
    }

    public static void notifyOwner(Case c) {
        Messaging.CustomNotification n = new Messaging.CustomNotification();
        n.setNotificationTypeId(getTypeId());
        n.setTargetId(c.Id);
        n.setTitle('Case Escalated: ' + c.CaseNumber);
        n.setBody('This case is now Priority 1.');
        n.send(new Set<String>{ c.OwnerId });
    }
}
```

**Why not the alternative:** Hardcoding the notification type Id breaks on sandbox refresh (Ids change). Querying per record wastes SOQL in bulk triggers; caching at class scope amortizes.

### Pattern 2: Queueable Wrapper For Trigger Use

**When to use:** Any notification fired from a trigger context to avoid sync failures blocking the DML.

**How it works:**

```apex
public class CaseNotificationQueueable implements Queueable {
    private final List<Id> caseIds;
    public CaseNotificationQueueable(List<Id> caseIds) { this.caseIds = caseIds; }
    public void execute(QueueableContext ctx) {
        for (Case c : [SELECT Id, OwnerId, CaseNumber FROM Case WHERE Id IN :caseIds]) {
            try { CaseEscalationNotifier.notifyOwner(c); }
            catch (Exception e) { System.debug(LoggingLevel.WARN, e.getMessage()); }
        }
    }
}
```

**Why not the alternative:** Direct sync sending in the trigger propagates platform-level notification failures into user-facing DML errors.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Notify 1–10 specific users | `send(Set<String>{userIds})` | One synchronous call is fine |
| Notify a whole team | `send(Set<String>{queueId})` | Queue expansion is server-side |
| Notify 100+ dynamically computed users | Enqueue a Queueable that batches sends | Avoids governor limits and surfaces errors |
| Notify external parties | Email or callout, not Custom Notification | Custom Notifications are for Salesforce users |
| Need retries on failure | Queueable + `Database.Stateful` | Sync throw loses the attempt |

---

## Recommended Workflow

1. Confirm the Custom Notification Type exists in target orgs (Setup → Custom Notifications) — DeveloperName is stable, Id is not.
2. Decide recipients: Users, Queues, or Groups. Validate Id prefixes before sending.
3. Decide sync vs async. Anything in a trigger or post-DML hot path goes async.
4. Cache the `CustomNotificationType.Id` by DeveloperName at class scope.
5. Truncate body to ~200 chars if mobile push is in scope.
6. Wrap `send()` in try/catch; log via your standard logger, do not rethrow into user context.
7. Write a test using `Test.startTest()` / `Test.stopTest()` — Custom Notifications are mockable with `Test.setMock` for `HttpCalloutMock`? No; they use `Messaging.sendNotificationsEmulated = true` in test context — assert no exception thrown.

---

## Review Checklist

- [ ] `DeveloperName` is used (not hardcoded Id) to resolve `CustomNotificationType`.
- [ ] Recipient set contains only User/Group/Queue Ids.
- [ ] Sends from triggers are delegated to a Queueable.
- [ ] Body is within the mobile push limit (~200 chars) or split into title + short body.
- [ ] Exceptions are caught and logged; not rethrown into the DML transaction.
- [ ] Tests cover success and `INVALID_RECIPIENT_IDS` paths.

---

## Salesforce-Specific Gotchas

See `references/gotchas.md` for the full list.

1. **Notification Type Id changes per org** — query by DeveloperName, never hardcode.
2. **Deactivated users silently swallow the notification** — no exception, just nothing delivered.
3. **Mobile push truncates the body** — in-app bell keeps the full text.
4. **500-recipient limit per `send()` call** — batch above that.
5. **No way to retrieve sent history via Apex** — the platform does not expose a notification log.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `references/examples.md` | Single-user, queue, and trigger-to-Queueable patterns |
| `references/gotchas.md` | Platform gotchas around Ids, limits, and silent failures |
| `references/llm-anti-patterns.md` | Common LLM mistakes: hardcoded Type Id, missing try/catch |
| `references/well-architected.md` | Reliability / Security framing |
| `scripts/check_apex_custom_notifications_from_apex.py` | Stdlib lint for notification pitfalls |

---

## Related Skills

- **apex-single-email-message** — for email instead of push
- **apex-queueable-basics** — for async wrapping
- **apex-async-architecture** — choosing the right async technology
