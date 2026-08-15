# Examples — Custom Notification Type Design

Worked designs for Custom Notification Types, with the metadata that has to ship
alongside them and the Apex that enforces the design decisions. Every platform
construct below is quoted from the Metadata API Developer Guide, the Apex
Reference Guide, or the Actions Developer Guide (Summer '26, API 67.0). The
*send* itself — the loop, the batching, the 500-value cap — is
`admin/custom-notification-types`; this file covers the design around it.

---

## Example 1: A case-escalation notification, end to end

**Context:** Support wants the on-call agent notified when a case crosses its
escalation threshold, on desktop and on the phone, deep-linked to the case.

**Problem:** The first build "worked" in the sandbox on a laptop and delivered
nothing to any phone in production. Nothing in the Apex changed between them.

### The type definition

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/notificationtypes/Case_Escalation.notiftype-meta.xml
     Metadata API suffix is .notiftype, directory notificationtypes,
     available in API version 46.0 and later. -->
<CustomNotificationType xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Max 80 characters. This is the handle Apex and Flow resolve by. -->
    <customNotifTypeName>Case_Escalation</customNotifTypeName>

    <!-- Max 255 characters. The Metadata API Developer Guide says this
         "is displayed with the notification type name" — so wherever the name
         shows up, this shows up with it. Write it as prose a human reads while
         working out what the notification is for, not as a changelog entry. -->
    <description>Fires when a case you own or cover is 30 minutes from breaching its SLA. Turn this off only if someone else is covering your queue.</description>

    <masterLabel>Case Escalation</masterLabel>

    <desktop>true</desktop>
    <mobile>true</mobile>

    <!-- The Metadata API Developer Guide describes this field as
         "Reserved for future use." Leave it alone. Slack notifications are a
         SEPARATE notification type — see Example 5. -->
</CustomNotificationType>
```

### The delivery settings that have to ship with it

This is the file whose absence produced the "works on desktop, silent on mobile"
split. `NotificationTypeConfig` is a different metadata type in a different
directory with a different suffix, and nothing about deploying the type pulls it
along.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Metadata API suffix .config, directory notificationTypeConfig,
     available in API version 48.0 and later. -->
<NotificationTypeConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <notificationTypeSettings>
        <!-- "Required. Specifies a notification type's API name" -->
        <notificationType>Case_Escalation</notificationType>

        <notificationChannels>
            <desktopEnabled>true</desktopEnabled>
            <mobileEnabled>true</mobileEnabled>
            <slackEnabled>false</slackEnabled>
        </notificationChannels>

        <!-- THIS is the gate that swallows mobile push. appSettings is
             per-connected-app: "An array of settings for the connected apps
             supported for a notification type". A notification type with
             mobileEnabled=true and no enabled connected app delivers to no
             device at all.

             Read the exact connectedAppName values out of the target org
             (Setup -> Apps -> Connected Apps -> Manage) rather than guessing —
             the set differs between orgs depending on which mobile apps,
             Field Service apps, and Mobile SDK apps are installed. -->
        <appSettings>
            <connectedAppName><!-- e.g. the org's Salesforce mobile app --></connectedAppName>
            <enabled>true</enabled>
        </appSettings>
    </notificationTypeSettings>
</NotificationTypeConfig>
```

**Why it works:** the two files are treated as one deployable unit. Deploying
only the first produces a type that is *defined* everywhere and *delivered*
nowhere, and because `send()` still returns without throwing, no error surfaces
anywhere in the org.

### Resolving the audience — wrong and right

**Wrong.** Enumerate the users:

```apex
// Resolves the on-call agents at design time and freezes them into the code.
Set<String> recipients = new Set<String>{
    '005...AAA', '005...BBB', '005...CCC'
};
```

Every rotation change is now a deployment. Nobody remembers, and the notification
quietly starts paging people who left the team.

**Right.** Pass the queue ID and let the platform fan out:

```apex
public with sharing class EscalationAudience {

    /**
     * Returns the ID set to hand to Messaging.CustomNotification.send().
     *
     * recipientIds accepts more than user IDs. The Actions Developer Guide
     * documents the accepted kinds for the Flow action, and the same
     * resolution applies to the Apex send:
     *
     *   UserId        -> that user, if active
     *   GroupId       -> all active group members
     *   QueueId       -> all active queue members
     *   AccountId     -> all active Account Team members
     *                    (requires account teams enabled)
     *   OpportunityId -> all active Opportunity Team members
     *                    (requires team selling enabled)
     *
     * "Values can be combined in a list up to 500 values." That 500 counts the
     * IDs you pass, NOT the humans reached. One queue ID may be 300 people.
     */
    public static Set<String> forCase(Case c) {
        Set<String> ids = new Set<String>();

        // The owner may be a user or a queue; the ID kind tells you which, and
        // both are valid recipients, so no branch is needed.
        if (c.OwnerId != null) {
            ids.add(c.OwnerId);
        }

        // Plus the standing on-call group. Membership is administered in Setup,
        // where the support manager can change it without a release.
        Group onCall = [
            SELECT Id
            FROM Group
            WHERE DeveloperName = 'Support_On_Call'
              AND Type = 'Regular'
            WITH USER_MODE
            LIMIT 1
        ];
        ids.add(onCall.Id);

        return ids;
    }
}
```

Two IDs cover an arbitrarily large, self-maintaining audience.

### Looking up the notification type

The Apex Reference Guide's own sample queries the type by `DeveloperName`:

```apex
CustomNotificationType notificationType =
    [SELECT Id, DeveloperName
     FROM CustomNotificationType
     WHERE DeveloperName='Custom_Notification'
     WITH USER_MODE
     LIMIT 1];
```

Two design consequences of that one statement:

1. **It costs a SOQL query per call.** Under a bulk trigger that is a query per
   batch at best and a query per record at worst. Cache it — the ID is stable for
   the life of the type.

2. **`WITH USER_MODE` means a permission problem looks like a data problem.** If
   the running user cannot read `CustomNotificationType`, the query returns zero
   rows and the assignment throws `System.QueryException: List has no rows for
   assignment to SObject` — which reads as "the notification type doesn't exist"
   and sends people to Setup to recreate a type that is already there.

A cached, honest version:

```apex
public with sharing class NotificationTypes {

    private static final Map<String, Id> CACHE = new Map<String, Id>();

    public class MissingNotificationTypeException extends Exception {}

    /** Resolves a notification type ID by API name, once per transaction. */
    public static Id idFor(String developerName) {
        if (CACHE.containsKey(developerName)) {
            return CACHE.get(developerName);
        }

        List<CustomNotificationType> found = [
            SELECT Id, DeveloperName
            FROM CustomNotificationType
            WHERE DeveloperName = :developerName
            WITH USER_MODE
            LIMIT 1
        ];

        if (found.isEmpty()) {
            // Say which of the two causes it is, because they have different
            // fixes and the query cannot tell them apart.
            throw new MissingNotificationTypeException(
                'No readable CustomNotificationType named "' + developerName +
                '". Either the type is not deployed to this org, or the running ' +
                'user lacks read access to CustomNotificationType.'
            );
        }

        CACHE.put(developerName, found[0].Id);
        return found[0].Id;
    }
}
```

---

## Example 2: Making the throttle a property of the record

**Context:** A status field on a work order is edited several times in a single
session by the same dispatcher. Each edit fires the notification.

**Problem:** The obvious fix — a static `Boolean alreadySent` in the trigger
handler — only suppresses repeats *inside one transaction*. Six separate saves
over four minutes are six separate transactions, and the static resets each time.

**Design:** put the suppression state on the record, where it survives
transactions, is visible to admins, is queryable when someone asks why, and is
shared by every sender regardless of whether it is Flow or Apex.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/objects/WorkOrder/fields/Last_Escalation_Notice__c.field-meta.xml -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Last_Escalation_Notice__c</fullName>
    <label>Last Escalation Notice</label>
    <type>DateTime</type>
    <!-- Read-only to everyone: it is machine state, not a user field.
         Grant edit through the automation's permission set only. -->
    <trackHistory>false</trackHistory>
</CustomField>
```

```apex
public with sharing class EscalationNotifier {

    /**
     * Minimum interval between two notifications about the same record.
     * Held in custom metadata so a support manager can widen the window during
     * an incident without a deployment.
     */
    private static Integer suppressionMinutes() {
        Notification_Registry__mdt cfg =
            Notification_Registry__mdt.getInstance('Case_Escalation');
        return cfg == null || cfg.Suppression_Minutes__c == null
            ? 60
            : Integer.valueOf(cfg.Suppression_Minutes__c);
    }

    /**
     * Splits a batch into the records that may notify now and those that are
     * inside the suppression window. Bulk-safe: no SOQL or DML in a loop.
     */
    public static List<WorkOrder> notifiable(List<WorkOrder> candidates) {
        DateTime cutoff = DateTime.now().addMinutes(-suppressionMinutes());
        List<WorkOrder> allowed = new List<WorkOrder>();

        for (WorkOrder wo : candidates) {
            if (wo.Last_Escalation_Notice__c == null
                    || wo.Last_Escalation_Notice__c < cutoff) {
                allowed.add(wo);
            }
        }
        return allowed;
    }

    /**
     * Stamps the records that were notified. Runs AFTER the send, so a failed
     * send does not consume the window and silently swallow the next attempt.
     */
    public static void stampNotified(List<WorkOrder> sent) {
        List<WorkOrder> updates = new List<WorkOrder>();
        DateTime now = DateTime.now();
        for (WorkOrder wo : sent) {
            updates.add(new WorkOrder(
                Id = wo.Id,
                Last_Escalation_Notice__c = now
            ));
        }
        if (!updates.isEmpty()) {
            // User mode is the default for database operations in API 67.0;
            // this automation's permission set grants edit on the field.
            update updates;
        }
    }
}
```

**Why it works:**

- Suppression survives across transactions, users, and senders.
- Ordering matters and is deliberate: **send, then stamp**. Stamping first is the
  intuitive order and it means a send that throws still burns the hour, so the
  event that most needed the notification is the one that never gets it.
- The window is configuration, not code, so widening it during an incident is a
  Setup change.

**What this does not do:** it does not de-duplicate *concurrent* saves. Two
simultaneous transactions can both read a null stamp and both send. If a strict
once-only guarantee is required, that needs a different mechanism — a unique
external ID on a delivery-log record, or `FOR UPDATE` on the subject row — and
the honest design answer is usually that one duplicate notification is cheaper
than the locking.

---

## Example 3: Digest instead of per-event

**Context:** "Notify reps when a lead is assigned to them." Fifty leads land in a
morning routing run.

**Wrong:** fifty notifications, delivered in about four seconds, to one person.

**Right:** one notification, deep-linked to the list of what changed.

```apex
public with sharing class LeadAssignmentDigest implements Schedulable {

    public void execute(SchedulableContext ctx) {
        // One query, grouped by owner. Aggregate keeps heap flat regardless of
        // how many leads routed overnight.
        AggregateResult[] rows = [
            SELECT OwnerId owner, COUNT(Id) total
            FROM Lead
            WHERE IsConverted = FALSE
              AND CreatedDate = LAST_N_DAYS:1
              AND Owner.Type = 'User'
            WITH USER_MODE
            GROUP BY OwnerId
        ];

        Id typeId = NotificationTypes.idFor('Lead_Assignment_Digest');

        for (AggregateResult row : rows) {
            String ownerId = String.valueOf(row.get('owner'));
            Integer total  = Integer.valueOf(row.get('total'));

            Messaging.CustomNotification n = new Messaging.CustomNotification();
            n.setNotificationTypeId(typeId);
            n.setTitle(total + ' new leads assigned to you');

            // Max 750 characters for the body. Merge fields resolve at RUNTIME,
            // so a body that fits in the sandbox can overflow in production
            // against a long account name. Truncate deliberately.
            n.setBody(clip(
                'You were assigned ' + total + ' leads overnight. ' +
                'Open the New Leads list view to work them.', 750));

            // Non-record destination, so targetPageRef rather than targetId.
            // Exactly one of the two is required.
            n.setTargetPageRef(JSON.serialize(new Map<String, Object>{
                'type' => 'standard__objectPage',
                'attributes' => new Map<String, Object>{
                    'objectApiName' => 'Lead',
                    'actionName'    => 'list'
                },
                'state' => new Map<String, Object>{
                    'filterName' => 'New_This_Week'
                }
            }));

            n.send(new Set<String>{ ownerId });
        }
    }

    private static String clip(String s, Integer max) {
        return s != null && s.length() > max ? s.substring(0, max - 1) + '…' : s;
    }
}
```

**Why it works:** fifty interruptions become one, and the one that survives is
more useful than any of the fifty was. The digest is also the only shape that
degrades gracefully — a routing run that assigns 500 leads produces the same one
notification.

**Trade-off to state out loud:** the digest is not real-time. If a lead needs
working within minutes, this design is wrong and a per-event notification with a
tight throttle is right. Pick on the basis of the recipient's actual response
time, not on which is easier to build.

---

## Example 4: The registry, as deployable metadata

A wiki page listing notification types is out of date the week after it is
written. Custom metadata is not, because it deploys with the change that creates
the type and can be asserted on in a test.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/customMetadata/Notification_Registry.Case_Escalation.md-meta.xml -->
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Case Escalation</label>
    <values><field>Notification_Type_API_Name__c</field><value xsi:type="xsd:string"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">Case_Escalation</value></values>
    <values><field>Owner_Team__c</field><value xsi:type="xsd:string"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">Support Ops</value></values>
    <values><field>Recipient_Action__c</field><value xsi:type="xsd:string"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">On-call agent reassigns or escalates the case before SLA breach.</value></values>
    <values><field>Suppression_Minutes__c</field><value xsi:type="xsd:double"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">60</value></values>
    <values><field>Review_Date__c</field><value xsi:type="xsd:date"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">2026-11-01</value></values>
</CustomMetadata>
```

And the test that makes the registry load-bearing rather than decorative:

```apex
@IsTest
private class NotificationRegistryTest {

    /**
     * Every notification type deployed to the org must have a registry row.
     * Without this assertion the registry is documentation; with it, shipping an
     * unregistered notification type fails the build.
     */
    @IsTest
    static void everyNotificationTypeIsRegistered() {
        Set<String> registered = new Set<String>();
        for (Notification_Registry__mdt r : Notification_Registry__mdt.getAll().values()) {
            registered.add(r.Notification_Type_API_Name__c);
        }

        List<String> unregistered = new List<String>();
        for (CustomNotificationType t : [
                SELECT DeveloperName FROM CustomNotificationType]) {
            if (!registered.contains(t.DeveloperName)) {
                unregistered.add(t.DeveloperName);
            }
        }

        Assert.isTrue(
            unregistered.isEmpty(),
            'Notification types with no registry entry — add one naming the ' +
            'owner, the recipient action, and a review date: ' + unregistered
        );
    }

    /** A registry row with no stated recipient action is a notification with no purpose. */
    @IsTest
    static void everyRegistryRowStatesARecipientAction() {
        for (Notification_Registry__mdt r : Notification_Registry__mdt.getAll().values()) {
            Assert.isFalse(
                String.isBlank(r.Recipient_Action__c),
                r.Notification_Type_API_Name__c +
                ' has no Recipient_Action__c. If nobody acts on it, it is a report.'
            );
        }
    }
}
```

`Notification_Registry__mdt.getAll()` reads custom metadata without consuming a
SOQL query, so the registry can also be consulted at send time — as
`EscalationNotifier` does for its suppression window — at no governor cost.

---

## Example 5: Slack is a different type, not a fourth checkbox

**What people try:**

```xml
<CustomNotificationType xmlns="http://soap.sforce.com/2006/04/metadata">
    <customNotifTypeName>Deal_Won</customNotifTypeName>
    <masterLabel>Deal Won</masterLabel>
    <desktop>true</desktop>
    <mobile>false</mobile>
    <slack>true</slack>   <!-- does not do what it looks like it does -->
</CustomNotificationType>
```

The Metadata API Developer Guide describes `slack` on `CustomNotificationType`
as **"Reserved for future use."**

**What is actually true, in two parts, because they are easy to conflate:**

1. Slack *is* a real delivery channel at the org-settings layer.
   `NotificationTypeConfig` → `notificationChannels` carries a documented
   `slackEnabled` boolean alongside `desktopEnabled` and `mobileEnabled`.

2. A Slack notification is created as its **own notification type** through
   Notification Builder's Slack path, where it is bound to a Slack app and a
   Slack message configuration, and it is sent by a Send Notification action.

So the design shape is two types, not one type with three channels:

```text
Deal_Won_Desktop   -> CustomNotificationType, desktop=true, mobile=false
                      audience: the opportunity owner
                      deep link: the opportunity record (targetId)

Deal_Won_Slack     -> Slack notification type created in Notification Builder
                      audience: the #wins channel
                      message: a short congratulation and a link
```

This is better design than a single type would have been anyway. The desktop
notification is for the person who has to do the next thing; the Slack post is
for an audience that is *celebrating*, not acting. They deserve different
copy, different frequency rules, and different owners.

---

## Anti-Pattern: the field-change notification

**What gets built:**

```text
Record-Triggered Flow on Account, "A record is created or updated",
no entry criteria, Action: Send Custom Notification, recipient: Owner.
```

**What goes wrong:** every integration write, every mass update, every dedup
merge, and every batch job touching Account produces a notification. In one
observed org this produced roughly forty bell notifications a day per rep for
system-driven field writes, and within two weeks the reps had switched the
channel off — which also switched off the three notifications that mattered.

**Correct approach:** notify on a *transition*, not on a save, and require the
transition to be one the recipient can respond to.

```text
Entry criteria — "Only when a record is updated to meet the condition
requirements", formula:

  AND(
    ISCHANGED({!$Record.OwnerId}),
    NOT(ISBLANK({!$Record.OwnerId})),
    {!$User.Id} <> {!$Record.OwnerId}
  )
```

`ISCHANGED` restricts the flow to the transition rather than the save. The last
clause is the one that gets left out, and it is why the person who reassigned the
account gets a notification telling them the account was reassigned.

**Detection:** a record-triggered flow whose entry criteria contain no
`ISCHANGED` and no prior-value comparison, with a notification action in the
body. That combination is almost always the field-change notification wearing a
different name.
