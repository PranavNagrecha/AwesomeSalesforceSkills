# Examples — Custom Notification Types

Two worked scenarios and one anti-pattern showing how Custom
Notifications get fired from declarative and code contexts, and
why email alerts cannot substitute for them when the business need
is a real-time bell or push.

---

## Example 1: Flow "Send Custom Notification" with dynamic recipients (user vs group vs queue)

**Context:** Service Cloud team wants an in-app alert when a Case's
priority is escalated to "High." The alert routes to one of three
recipient kinds depending on case ownership: if the owner is a
User, notify that user; if the owner is a Queue, notify the queue;
and any time the priority becomes High, also notify the on-call
support manager group. The notification must reach desktop bell
and mobile push so on-call engineers see it after hours.

**Problem:** Practitioners hard-wire a single User Id into the
Recipient Ids parameter (e.g., the case owner) and discover that
Queue-owned cases produce zero notifications because the Send
Custom Notification action treats the Queue Id as an invalid
recipient unless explicitly added to a collection. Worse, hardcoding
the `Custom Notification Type Id` (an `0ML...` Id) breaks on sandbox
refresh because the Id is org-specific.

**Solution:** Resolve the Notification Type Id at runtime with Get
Records, build a Text collection of recipient Ids in an Assignment,
add the on-call group Id from a Custom Label or Custom Metadata
Type, and pass the collection to the Send Custom Notification core
action.

```
Flow: Case_Priority_High_Notification
  Type: Record-Triggered Flow
  Object: Case
  Trigger: A record is updated
  Condition Requirements:
    - ISCHANGED({!$Record.Priority})
    - {!$Record.Priority} = "High"
  Optimize for: Actions and Related Records (after-save)

Get Records: Get_Notification_Type
  Object: CustomNotificationType
  Filter: DeveloperName = "Case_Priority_High"
  Store: First record only → notifType

Get Records: Get_OnCall_Group
  Object: Group
  Filter: DeveloperName = "Support_OnCall_Managers"
    AND Type = "Regular"
  Store: First record only → onCallGroup

Assignment: Build_Recipients
  recipientIds Add → {!$Record.OwnerId}        // User OR Queue Id
  recipientIds Add → {!onCallGroup.Id}         // Public Group Id

Action: Send Custom Notification
  Custom Notification Type Id: {!notifType.Id}
  Notification Title:          "Case escalated: {!$Record.CaseNumber}"
  Notification Body:           "Priority is now High. Subject: {!$Record.Subject}"
  Recipient Ids:               {!recipientIds}        // Text collection
  Target Id:                   {!$Record.Id}          // 15- or 18-char record Id
```

**Why it works:** The `OwnerId` field on Case holds either a User Id
(prefix `005`) or a Queue Id (prefix `00G`); the Send Custom
Notification action's Recipient Ids parameter accepts both, plus
Public Group Ids (also `00G`), so a single collection handles all
three recipient kinds without branching. Resolving the Notification
Type Id via Get Records against `CustomNotificationType` (an
sObject available since API 47.0) makes the flow portable across
orgs — only the DeveloperName needs to match. The `Target Id`
parameter creates the deep-link: tapping the notification on mobile
opens the Case record in the Salesforce app; clicking the desktop
bell entry navigates to the record page.

---

## Example 2: Apex `Messaging.CustomNotification` with explicit type Id lookup and bulk targeting

**Context:** Sales Ops wants every Account Owner whose territory
just got rebalanced to receive a push notification listing how many
Accounts moved in or out. Quarterly rebalancing affects 2,500
Account Owners across the org. The job runs in a Batch Apex class
overnight. Notifications must reach mobile push (so reps see them
on the next morning login) and desktop bell.

**Problem:** A naive batch implementation calls `n.send(allOwnerIds)`
where `allOwnerIds` holds 2,500 Ids. The send call exceeds the
500-recipient limit per `send()` and throws
`Messaging.CustomNotificationException`. Even worse, when the
notification type Id is hardcoded (e.g., copied from a sandbox),
the batch fails in production with `INVALID_NOTIFICATION_TYPE_ID`
because the Id differs per org.

**Solution:** Cache the type Id via a one-time SOQL against
`CustomNotificationType.DeveloperName`, chunk the recipient set into
batches of 500, and send one notification per chunk inside the
batch's `execute()` method.

```apex
public class TerritoryRealignmentNotifier
        implements Database.Batchable<SObject>, Database.Stateful {

    private static final String TYPE_DEV_NAME = 'Territory_Realigned';
    private static final Integer SEND_CHUNK = 500;
    private Id cachedTypeId;

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, OwnerId, Name FROM Account WHERE Territory_Changed__c = TRUE'
        );
    }

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        if (cachedTypeId == null) {
            cachedTypeId = [SELECT Id FROM CustomNotificationType
                            WHERE DeveloperName = :TYPE_DEV_NAME LIMIT 1].Id;
        }

        // Group AccountIds per OwnerId so the body can include a count.
        Map<Id, List<Id>> accountsByOwner = new Map<Id, List<Id>>();
        for (Account a : scope) {
            if (!accountsByOwner.containsKey(a.OwnerId)) {
                accountsByOwner.put(a.OwnerId, new List<Id>());
            }
            accountsByOwner.get(a.OwnerId).add(a.Id);
        }

        // Chunk recipients into 500-per-send batches.
        List<Id> ownerIds = new List<Id>(accountsByOwner.keySet());
        for (Integer i = 0; i < ownerIds.size(); i += SEND_CHUNK) {
            Integer end = Math.min(i + SEND_CHUNK, ownerIds.size());
            Set<String> chunk = new Set<String>();
            for (Id ownerId : ownerIds.subList(i, end)) {
                chunk.add(String.valueOf(ownerId));
            }

            Messaging.CustomNotification n = new Messaging.CustomNotification();
            n.setNotificationTypeId(cachedTypeId);
            n.setTitle('Territory realigned');
            n.setBody('Your Account portfolio was updated overnight.');
            n.setTargetPageRef('{"type":"standard__navItemPage","attributes":{"apiName":"Account"}}');
            try {
                n.send(chunk);
            } catch (Exception e) {
                System.debug(LoggingLevel.ERROR, 'Notify failed: ' + e.getMessage());
            }
        }
    }

    public void finish(Database.BatchableContext bc) { }
}
```

**Why it works:** Caching the type Id on the Batchable instance
(via `Database.Stateful`) means one SOQL per chunk-of-chunks, not
one per `execute()`. Chunking at 500 respects the recipient cap
without relying on Apex to throw — the wrapper guarantees the cap
is honored before `send()` is invoked. Using `setTargetPageRef`
with a `pageReference` JSON string lets the notification deep-link
to the Account list view instead of a single record; the
`setTargetId` route is for record-specific notifications, but a
realignment summary doesn't have one canonical record. Wrapping
`send()` in try/catch with explicit logging surfaces the silent
failure modes (e.g., a recipient Id that became inactive between
the query and the send) without aborting the batch.

---

## Anti-Pattern: Using Email Alerts for transactional notifications instead of Custom Notifications

**What practitioners do:**

```
Process Builder / Workflow / Flow path

Trigger: Case priority escalated to "High"
Action: Email Alert
  Template: Case_Escalation_Email
  Recipients: Case Owner, Case Owner's Manager
  From: org-wide email address
```

The team picks Email Alert because (a) it's the most familiar
notification mechanism on Salesforce, (b) it has a clear audit
trail (the sent email is logged in Activity History), and (c) it
works for every recipient regardless of whether they have the
Salesforce mobile app installed.

**What goes wrong:** Email Alerts do not deliver to the in-app bell
icon, the desktop notification toast, or the Salesforce mobile
push channel. A field rep using the Salesforce mobile app sees no
indication that the case has escalated — they have to open their
email inbox and notice the new mail. In an on-call scenario where
the rep is in another customer's office and only checks email
between meetings, the escalation sits unread for hours. Worse, the
team's email provider (Outlook, Gmail) routinely classifies
automated Salesforce notifications as low-priority or filters them
to a "Salesforce" folder the rep checks once a day. The "real-time
escalation alert" is in practice a 4-hour-delayed escalation alert.

Email Alerts also can't deep-link to a Salesforce record on a
mobile device — the email body holds a URL, but tapping it opens
the browser, prompts for login, and lands on a page that may not
render well on mobile. A Custom Notification with `Target Id` set
opens the Case record directly in the Salesforce mobile app, where
the rep is already authenticated.

**Correct approach:** Use Custom Notifications for any event that
needs to interrupt the recipient's current activity — escalations,
approval requests, SLA-at-risk warnings, real-time alerts. Custom
Notifications light up the bell (desktop), the toast (browser tab),
and the mobile push channel (iOS/Android) in one declarative
action. Keep email for audit-trail messages (invoices, receipts,
confirmations) where persistence and reply-ability matter more
than immediacy. The two channels are complementary, not redundant:
a typical "Case escalated" workflow fires both a Custom Notification
(for the immediate attention) and an Email Alert (for the audit
trail and for stakeholders who don't have a Salesforce license).

When the email-alert pattern is already in production, replace it
incrementally: add a parallel Send Custom Notification action,
monitor delivery via a Platform Event marker, and once confirmed
working, downgrade the email to a daily-digest format instead of
per-event.
