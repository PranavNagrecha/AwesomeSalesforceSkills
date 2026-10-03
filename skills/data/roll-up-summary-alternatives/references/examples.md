# Examples: Roll Up Summary Alternatives

The native roll-up summary field metadata is in `metadata-examples.md`. This file holds the lookup rollup built in Apex.

## Example 1: Lookup rollup with Apex, plus a repair job

**Context:** `Service_Ticket__c` looks up to Account through `Account__c`. Account needs `Open_Ticket_Count__c`, the number of tickets where `Is_Closed__c` is false. Tickets are inserted in bulk, reparented, deleted, and undeleted, and Accounts get merged.

### Fields

`force-app/main/default/objects/Account/fields/Open_Ticket_Count__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Open_Ticket_Count__c</fullName>
    <defaultValue>0</defaultValue>
    <label>Open Ticket Count</label>
    <precision>9</precision>
    <required>false</required>
    <scale>0</scale>
    <type>Number</type>
</CustomField>
```

`force-app/main/default/objects/Service_Ticket__c/fields/Account__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Account__c</fullName>
    <deleteConstraint>SetNull</deleteConstraint>
    <label>Account</label>
    <referenceTo>Account</referenceTo>
    <relationshipLabel>Service Tickets</relationshipLabel>
    <relationshipName>Service_Tickets</relationshipName>
    <required>false</required>
    <type>Lookup</type>
</CustomField>
```

`Service_Ticket__c` also needs a checkbox `Is_Closed__c`.

### Trigger

`force-app/main/default/triggers/ServiceTicketRollup.trigger`

```apex
trigger ServiceTicketRollup on Service_Ticket__c (after insert, after update, after delete, after undelete) {
    TicketRollupService.collectAndRecalculate(
        Trigger.isDelete ? null : Trigger.new,
        Trigger.isInsert || Trigger.isUndelete ? null : Trigger.oldMap
    );
}
```

### Service

`force-app/main/default/classes/TicketRollupService.cls`

```apex
public without sharing class TicketRollupService {
    // without sharing: the total must count every ticket, not only those the editing user can see.

    public static void collectAndRecalculate(List<Service_Ticket__c> newRows, Map<Id, Service_Ticket__c> oldMap) {
        Set<Id> accountIds = new Set<Id>();
        if (newRows != null) {
            for (Service_Ticket__c t : newRows) {
                if (t.Account__c != null) {
                    accountIds.add(t.Account__c);
                }
            }
        }
        if (oldMap != null) {
            for (Service_Ticket__c t : oldMap.values()) {
                if (t.Account__c != null) {
                    accountIds.add(t.Account__c); // old parent on reparent or delete
                }
            }
        }
        recalculate(accountIds);
    }

    public static void recalculate(Set<Id> accountIds) {
        if (accountIds == null || accountIds.isEmpty()) {
            return;
        }
        Map<Id, Integer> counts = new Map<Id, Integer>();
        for (Id accountId : accountIds) {
            counts.put(accountId, 0);
        }
        // One aggregate per transaction. COUNT with GROUP BY uses one query row per group.
        for (AggregateResult ar : [
            SELECT Account__c accountId, COUNT(Id) openCount
            FROM Service_Ticket__c
            WHERE Account__c IN :accountIds AND Is_Closed__c = false
            GROUP BY Account__c
        ]) {
            counts.put((Id) ar.get('accountId'), (Integer) ar.get('openCount'));
        }
        List<Account> changed = new List<Account>();
        for (Account a : [SELECT Id, Open_Ticket_Count__c FROM Account WHERE Id IN :accountIds]) {
            Integer fresh = counts.get(a.Id);
            if (a.Open_Ticket_Count__c == null || a.Open_Ticket_Count__c.intValue() != fresh) {
                changed.add(new Account(Id = a.Id, Open_Ticket_Count__c = fresh));
            }
        }
        // Writing only changed parents keeps parent locks and parent save procedures to a minimum.
        update changed;
    }
}
```

### Repair batch for merges, cascaded deletes, and undeletes

`force-app/main/default/classes/TicketRollupRepairBatch.cls`

```apex
public without sharing class TicketRollupRepairBatch implements Database.Batchable<SObject>, Schedulable {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([SELECT Id FROM Account]);
    }
    public void execute(Database.BatchableContext bc, List<Account> scope) {
        TicketRollupService.recalculate(new Map<Id, Account>(scope).keySet());
    }
    public void finish(Database.BatchableContext bc) {
    }
    public void execute(SchedulableContext sc) {
        Database.executeBatch(new TicketRollupRepairBatch(), 200);
    }
}
```

### Test class

`force-app/main/default/classes/TicketRollupServiceTest.cls`

```apex
@IsTest
private class TicketRollupServiceTest {

    @TestSetup
    static void setup() {
        insert new List<Account>{ new Account(Name = 'Rollup A'), new Account(Name = 'Rollup B') };
    }

    static Map<String, Account> accounts() {
        Map<String, Account> byName = new Map<String, Account>();
        for (Account a : [SELECT Id, Name, Open_Ticket_Count__c FROM Account WHERE Name LIKE 'Rollup %']) {
            byName.put(a.Name, a);
        }
        return byName;
    }

    @IsTest
    static void bulkInsertReparentDeleteUndelete() {
        Map<String, Account> acc = accounts();
        List<Service_Ticket__c> tickets = new List<Service_Ticket__c>();
        for (Integer i = 0; i < 200; i++) {
            tickets.add(new Service_Ticket__c(Account__c = acc.get('Rollup A').Id, Is_Closed__c = false));
        }
        Test.startTest();
        insert tickets;
        System.assertEquals(200, accounts().get('Rollup A').Open_Ticket_Count__c, 'bulk insert counted');

        for (Integer i = 0; i < 50; i++) {
            tickets[i].Account__c = acc.get('Rollup B').Id;
        }
        update tickets;
        System.assertEquals(150, accounts().get('Rollup A').Open_Ticket_Count__c, 'old parent decremented');
        System.assertEquals(50, accounts().get('Rollup B').Open_Ticket_Count__c, 'new parent incremented');

        List<Service_Ticket__c> toDelete = new List<Service_Ticket__c>{ tickets[0], tickets[1] };
        delete toDelete;
        System.assertEquals(48, accounts().get('Rollup B').Open_Ticket_Count__c, 'delete decremented');

        undelete toDelete;
        System.assertEquals(50, accounts().get('Rollup B').Open_Ticket_Count__c, 'undelete restored');
        Test.stopTest();
    }

    @IsTest
    static void repairBatchFixesDrift() {
        Map<String, Account> acc = accounts();
        insert new Service_Ticket__c(Account__c = acc.get('Rollup A').Id, Is_Closed__c = false);
        update new Account(Id = acc.get('Rollup A').Id, Open_Ticket_Count__c = 99); // simulate drift
        Test.startTest();
        Database.executeBatch(new TicketRollupRepairBatch(), 200);
        Test.stopTest();
        System.assertEquals(1, accounts().get('Rollup A').Open_Ticket_Count__c, 'repair recomputed from source');
    }
}
```

Schedule the repair nightly once deployed, for example `System.schedule('Ticket rollup repair', '0 0 2 * * ?', new TicketRollupRepairBatch());`.

package.xml members: `ServiceTicketRollup` (ApexTrigger); `TicketRollupService`, `TicketRollupRepairBatch`, `TicketRollupServiceTest` (ApexClass); `Account.Open_Ticket_Count__c`, `Service_Ticket__c.Account__c`, `Service_Ticket__c.Is_Closed__c` (CustomField); `Service_Ticket__c` (CustomObject).

**Why it works:** The trigger covers insert, update with reparent, delete, and undelete. The repair batch covers what the Apex Developer Guide says triggers never see: merge reparenting, cascaded deletes, and child undeletes under a restored parent. COUNT with GROUP BY costs one query row per Account, not one per ticket.

---

## Anti-Pattern: Aggregate query per child record

**What practitioners do:** Recalculate the parent total inside a loop for each changed child.

**What goes wrong:** SOQL count, query rows, and parent locks all grow with the batch.

**Correct approach:** Collect affected parents, aggregate once, write only changed parents.
