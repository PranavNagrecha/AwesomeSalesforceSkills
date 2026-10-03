# Governor Limits: Examples

## Example 1: Refactoring SOQL-in-Loop in a Trigger Handler

### Before

```apex
public void onAfterInsert(List<Opportunity> newRecords) {
    for (Opportunity opp : newRecords) {
        // ❌ 1 SOQL per record; 200 opportunities = 200 SOQL
        Account acc = [SELECT Id, Name FROM Account WHERE Id = :opp.AccountId];
        acc.Last_Won_Date__c = (opp.StageName == 'Closed Won') ? opp.CloseDate : acc.Last_Won_Date__c;
        update acc; // ❌ 1 DML per record
    }
}
```

### After

```apex
public void onAfterInsert(List<Opportunity> newRecords) {
    // 1. Collect IDs
    Set<Id> accountIds = new Set<Id>();
    for (Opportunity opp : newRecords) {
        if (opp.StageName == 'Closed Won') {
            accountIds.add(opp.AccountId);
        }
    }
    if (accountIds.isEmpty()) return;

    // 2. Query once
    Map<Id, Account> accountMap = new Map<Id, Account>(
        [SELECT Id, Last_Won_Date__c FROM Account WHERE Id IN :accountIds]
    );

    // 3. Process in memory
    for (Opportunity opp : newRecords) {
        if (opp.StageName == 'Closed Won' && accountMap.containsKey(opp.AccountId)) {
            Account acc = accountMap.get(opp.AccountId);
            if (acc.Last_Won_Date__c == null || opp.CloseDate > acc.Last_Won_Date__c) {
                acc.Last_Won_Date__c = opp.CloseDate;
            }
        }
    }

    // 4. DML once
    update accountMap.values();
}
```

Result: 2 statements (1 SOQL + 1 DML) regardless of number of Opportunities.

---

## Example 2: Queueable for Post-DML Callout

### Trigger Handler (after DML complete)

```apex
public void onAfterInsert(List<Contact> newRecords) {
    // Don't make callout here; DML has occurred in this transaction
    Set<Id> ids = new Map<Id, Contact>(newRecords).keySet();
    System.enqueueJob(new ContactSyncQueueable(ids));
}
```

### Queueable Implementation

```apex
public class ContactSyncQueueable implements Queueable, Database.AllowsCallouts {

    private Set<Id> contactIds;

    public ContactSyncQueueable(Set<Id> contactIds) {
        this.contactIds = contactIds;
    }

    public void execute(QueueableContext ctx) {
        List<Contact> contacts = [
            SELECT Id, FirstName, LastName, Email
            FROM Contact
            WHERE Id IN :contactIds
        ];

        // Async limits: 200 SOQL, 60,000 ms CPU, 12 MB heap; still 100 callouts per transaction.
        List<Error_Log__c> logs = new List<Error_Log__c>();
        for (Contact c : contacts) {
            try {
                ExternalCRMClient.syncContact(c);
            } catch (Exception e) {
                // Collect, don't insert inside the loop.
                logs.add(new Error_Log__c(Contact__c = c.Id, Error_Message__c = e.getMessage()));
            }
        }
        insert logs; // one DML statement for all failures
    }
}
```

If more than 100 contacts can arrive, chunk the IDs and chain one Queueable per chunk, because the callout limit is 100 per transaction (limits table L19563).

---

## Example 3: Batch Apex for Nightly Cleanup

```apex
public class StaleLeadCleanupBatch implements Database.Batchable<SObject>, Database.Stateful {

    // Database.Stateful allows instance vars to persist across execute() calls
    private Integer totalProcessed = 0;
    private Integer totalErrors = 0;

    public Database.QueryLocator start(Database.BatchableContext ctx) {
        // A Batch QueryLocator returns up to 50 million rows (limits table L19856)
        return Database.getQueryLocator(
            'SELECT Id, Status, LastActivityDate FROM Lead ' +
            'WHERE Status != \'Closed\' AND LastActivityDate < LAST_N_YEARS:1'
        );
    }

    public void execute(Database.BatchableContext ctx, List<SObject> scope) {
        // Limits reset for each execute() (limits table L19530 to L19531)
        List<Lead> leads = (List<Lead>) scope;
        List<Lead> toUpdate = new List<Lead>();

        for (Lead l : leads) {
            l.Status = 'Closed - No Response';
            toUpdate.add(l);
        }

        Database.SaveResult[] results = Database.update(toUpdate, false); // allOrNone = false
        totalProcessed += results.size();
        for (Database.SaveResult sr : results) {
            if (!sr.isSuccess()) totalErrors++;
        }
    }

    public void finish(Database.BatchableContext ctx) {
        // Send completion email
        Messaging.SingleEmailMessage email = new Messaging.SingleEmailMessage();
        email.setToAddresses(new List<String>{'ops-team@company.com'});
        email.setSubject('Stale Lead Cleanup Complete');
        email.setPlainTextBody(
            'Processed: ' + totalProcessed + '\nErrors: ' + totalErrors
        );
        Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{email});
    }
}

// Schedule it:
// Database.executeBatch(new StaleLeadCleanupBatch(), 200);
```

---

## Example 4: Monitoring Limits During Development

```apex
public class LimitMonitor {

    public static void checkpoint(String label) {
        System.debug('=== LIMIT CHECK: ' + label + ' ===');
        System.debug('SOQL: ' + Limits.getQueries() + '/' + Limits.getLimitQueries());
        System.debug('DML Statements: ' + Limits.getDmlStatements() + '/' + Limits.getLimitDmlStatements());
        System.debug('DML Rows: ' + Limits.getDmlRows() + '/' + Limits.getLimitDmlRows());
        System.debug('CPU (ms): ' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime());
        System.debug('Heap (bytes): ' + Limits.getHeapSize() + '/' + Limits.getLimitHeapSize());
    }
}

// Usage in service class during development:
LimitMonitor.checkpoint('before bulk query');
List<Account> accounts = [SELECT Id FROM Account WHERE ...];
LimitMonitor.checkpoint('after bulk query, before processing');
// ... processing
LimitMonitor.checkpoint('after processing, before DML');
update accountsToUpdate;
LimitMonitor.checkpoint('after DML');
```

---

## Example 5: Platform event trigger sized for 2,000 events, with a test

**Context:** An ERP publishes `Order_Status__e` events (text fields `Order_Key__c` and `Status__c`). A trigger must update the matching `Order__c` records (`External_Key__c` is an External ID). Platform event triggers receive up to 2,000 events per batch (limits table L19862; Platform Events Developer Guide 262).

`force-app/main/default/triggers/OrderStatusEventTrigger.trigger`

```apex
trigger OrderStatusEventTrigger on Order_Status__e (after insert) {
    OrderStatusEventHandler.apply(Trigger.new);
}
```

`force-app/main/default/classes/OrderStatusEventHandler.cls`

```apex
public with sharing class OrderStatusEventHandler {

    public static void apply(List<Order_Status__e> events) {
        // 1. Collect keys; the last event per key wins.
        Map<String, String> statusByKey = new Map<String, String>();
        for (Order_Status__e e : events) {
            if (String.isNotBlank(e.Order_Key__c)) {
                statusByKey.put(e.Order_Key__c, e.Status__c);
            }
        }
        if (statusByKey.isEmpty()) {
            return;
        }
        // 2. One query for up to 2,000 keys (well under 50,000 rows).
        List<Order__c> toUpdate = new List<Order__c>();
        for (Order__c o : [
            SELECT Id, External_Key__c, Status__c
            FROM Order__c
            WHERE External_Key__c IN :statusByKey.keySet()
            WITH USER_MODE
        ]) {
            String status = statusByKey.get(o.External_Key__c);
            if (o.Status__c != status) {
                o.Status__c = status;
                toUpdate.add(o);
            }
        }
        // 3. One DML statement; partial success so one bad row doesn't fail the batch.
        Database.update(toUpdate, false);
    }
}
```

`force-app/main/default/classes/OrderStatusEventHandlerTest.cls`

```apex
@IsTest
private class OrderStatusEventHandlerTest {

    @IsTest
    static void handlesTwoThousandEventsInOneBatch() {
        List<Order__c> orders = new List<Order__c>();
        for (Integer i = 0; i < 2000; i++) {
            orders.add(new Order__c(External_Key__c = 'ERP-' + i, Status__c = 'Submitted'));
        }
        insert orders;

        List<Order_Status__e> events = new List<Order_Status__e>();
        for (Integer i = 0; i < 2000; i++) {
            events.add(new Order_Status__e(Order_Key__c = 'ERP-' + i, Status__c = 'Shipped'));
        }
        Test.startTest(); // fresh set of governor limits for the code under test
        EventBus.publish(events);
        Test.getEventBus().deliver();
        Test.stopTest();

        System.assertEquals(2000, [SELECT COUNT() FROM Order__c WHERE Status__c = 'Shipped']);
    }
}
```

Each class needs a `-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

package.xml:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>OrderStatusEventHandler</members>
        <members>OrderStatusEventHandlerTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>OrderStatusEventTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>Order_Status__e</members>
        <members>Order__c</members>
        <name>CustomObject</name>
    </types>
    <version>67.0</version>
</Package>
```

**Why it works:** One query and one DML statement serve a full 2,000-event batch, and the test proves it at that size. `Test.getEventBus().deliver()` delivers the published events inside the test (Platform Events Developer Guide 262). UNVERIFIED (2026-10-03): whether inserting 2,000 `Order__c` rows plus delivery fits your org's automation within one test method's limits; reduce automation in the test or split setup into `@TestSetup` if it does not.
