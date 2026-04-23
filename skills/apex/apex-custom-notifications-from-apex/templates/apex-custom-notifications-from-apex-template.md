# Apex Custom Notifications From Apex — Work Template

Use this template when designing or reviewing any Apex code that sends a `Messaging.CustomNotification`.

## Scope

**Skill:** `apex-custom-notifications-from-apex`

**Request summary:** (fill in — what should trigger the notification? who receives it?)

## Context Gathered

- **Notification Type DeveloperName:**
- **Trigger event:** (Case status → Escalated? Opportunity closed-won? Manual action?)
- **Recipients:** (specific users? queue? group? dynamic audience?)
- **Expected volume per event:** (1? 10? 500+?)
- **Calling context:** (trigger? Flow? scheduled job? LWC invocable?)

## Pre-Flight Checks

- [ ] `CustomNotificationType` with the chosen DeveloperName exists in all target orgs.
- [ ] Recipients are verified as User/Group/Queue Ids only.
- [ ] The target record is accessible to every recipient (sharing model check).
- [ ] Body fits the mobile push truncation budget (~190 chars).

## Approach

- [ ] Synchronous send (fine for non-trigger contexts with fewer than ~10 recipients)
- [ ] Queueable wrapper (required for trigger-originated sends)
- [ ] Batched Queueable (for >500 recipient broadcasts)

## Code Sketch

```apex
public class {{NotifierQueueable}} implements Queueable {
    private static final String TYPE_DEV_NAME = '{{DevName}}';
    private final List<Id> recordIds;

    public {{NotifierQueueable}}(List<Id> recordIds) { this.recordIds = recordIds; }

    public void execute(QueueableContext ctx) {
        Id typeId = [SELECT Id FROM CustomNotificationType
                     WHERE DeveloperName = :TYPE_DEV_NAME LIMIT 1].Id;
        for (Id rid : recordIds) {
            try {
                Messaging.CustomNotification n = new Messaging.CustomNotification();
                n.setNotificationTypeId(typeId);
                n.setTargetId(rid);
                n.setTitle('{{title}}');
                n.setBody('{{body}}');
                n.send(new Set<String>{ /* recipients */ });
            } catch (Exception e) {
                System.debug(LoggingLevel.WARN, e.getMessage());
            }
        }
    }
}
```

## Checklist

- [ ] Notification Type resolved by DeveloperName, not hardcoded Id.
- [ ] Queueable wrapper if fired from a trigger.
- [ ] `setTargetId` called with the record to open.
- [ ] Recipients validated as User/Group Ids.
- [ ] Body truncated for mobile push.
- [ ] Try/catch around `send()` with logging but not rethrow.
- [ ] Audit log row written if compliance demands provable delivery intent.
- [ ] Tests assert `send()` did not throw; recipients were computed correctly.

## Notes

Deviations from the standard pattern, with justification.
