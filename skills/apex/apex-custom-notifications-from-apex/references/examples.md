# Examples — Apex Custom Notifications From Apex

## Example 1: Notify Case Owner On Escalation From A Trigger

**Context:** A Case trigger updates `Status` to "Escalated". The current owner should get a bell notification linked to the Case.

**Problem:** Practitioners call `cn.send(...)` synchronously from the trigger. A transient platform error on the notification send aborts the DML — the user sees "An unexpected error occurred" when trying to save the Case, even though the escalation logic itself was fine.

**Solution:**

```apex
public with sharing class CaseTriggerHandler {
    public static void afterUpdate(List<Case> newList, Map<Id, Case> oldMap) {
        List<Id> escalated = new List<Id>();
        for (Case c : newList) {
            Case prior = oldMap.get(c.Id);
            if (c.Status == 'Escalated' && prior.Status != 'Escalated') {
                escalated.add(c.Id);
            }
        }
        if (!escalated.isEmpty()) {
            System.enqueueJob(new CaseEscalationNotifier(escalated));
        }
    }
}

public class CaseEscalationNotifier implements Queueable {
    private static final String TYPE_DEV_NAME = 'Case_Escalation';
    private final List<Id> caseIds;
    public CaseEscalationNotifier(List<Id> caseIds) { this.caseIds = caseIds; }

    public void execute(QueueableContext ctx) {
        Id typeId = [SELECT Id FROM CustomNotificationType
                     WHERE DeveloperName = :TYPE_DEV_NAME LIMIT 1].Id;
        for (Case c : [SELECT Id, OwnerId, CaseNumber FROM Case WHERE Id IN :caseIds]) {
            try {
                Messaging.CustomNotification n = new Messaging.CustomNotification();
                n.setNotificationTypeId(typeId);
                n.setTargetId(c.Id);
                n.setTitle('Case ' + c.CaseNumber + ' escalated');
                n.setBody('This case is now Priority 1 and needs immediate attention.');
                n.send(new Set<String>{ c.OwnerId });
            } catch (Exception e) {
                System.debug(LoggingLevel.WARN,
                    'Notification failed for ' + c.Id + ': ' + e.getMessage());
            }
        }
    }
}
```

**Why it works:** The trigger enqueues; the Queueable does the SOQL and send. A failure in `send()` is logged but does not affect the DML transaction that triggered it.

---

## Example 2: Notify A Queue's Members

**Context:** A new high-value Opportunity arrives and the "Inside Sales" queue should be pinged.

**Problem:** Developers iterate the queue's members with a SOQL on `GroupMember`, getting User Ids, then paginate the send — duplicative work.

**Solution:**

```apex
public with sharing class HighValueOppNotifier {
    public static void pingInsideSales(Opportunity opp) {
        Group q = [SELECT Id FROM Group WHERE Type = 'Queue' AND DeveloperName = 'Inside_Sales' LIMIT 1];
        Id typeId = [SELECT Id FROM CustomNotificationType
                     WHERE DeveloperName = 'High_Value_Opp' LIMIT 1].Id;

        Messaging.CustomNotification n = new Messaging.CustomNotification();
        n.setNotificationTypeId(typeId);
        n.setTargetId(opp.Id);
        n.setTitle('High-value opp: ' + opp.Name);
        n.setBody('Amount: ' + opp.Amount);
        n.send(new Set<String>{ q.Id });
    }
}
```

**Why it works:** Passing the Group/Queue Id to `send()` delegates member expansion to Salesforce. One call reaches every queue member, respecting the 500-recipient cap automatically.

---

## Example 3: Truncating Body For Mobile Push

**Context:** A long-form opportunity summary gets used as the notification body. Mobile users see a truncated mess.

**Problem:** Practitioners pass the full rich text; iOS and Android truncate around 200 chars.

**Solution:**

```apex
public static String shortBody(String full) {
    if (full == null) return '';
    String plain = full.stripHtmlTags().replaceAll('\\s+', ' ').trim();
    return plain.length() > 190 ? plain.substring(0, 187) + '...' : plain;
}
```

**Why it works:** Strip HTML, normalize whitespace, and cap at 190 characters with an ellipsis. The in-app bell will still have the target record to drill into.

---

## Anti-Pattern: Hardcoding The Notification Type Id

**What practitioners do:**

```apex
n.setNotificationTypeId('0MLxx0000004DfK');
```

**What goes wrong:** Custom Notification Type Ids differ between production, full sandbox, and developer sandbox. On sandbox refresh the Id changes and the notification fails with `INVALID_NOTIFICATION_TYPE_ID`.

**Correct approach:** Always `SELECT Id FROM CustomNotificationType WHERE DeveloperName = ...`. DeveloperName is stable across orgs.

---

## Anti-Pattern: Ignoring Recipient Id Validation

**What practitioners do:**

```apex
n.send(new Set<String>{ someContact.Id });
```

**What goes wrong:** `INVALID_RECIPIENT_IDS` is thrown. Contacts, Accounts, and custom objects are not valid recipients — only Users, Groups, and Queues (which are a Group subtype).

**Correct approach:** If the recipient is conceptually a Contact, resolve to their User Id via `Contact.AccountContactRelation` → `User` or a lookup. Never pass non-user Ids.
