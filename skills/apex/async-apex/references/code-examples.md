# Code Examples: Async Apex

Deployable Apex, tests, metadata, and manifest for the async patterns in `SKILL.md`. Narrative examples are in `examples.md`.

## Example 1: Queueable for a post-save callout, with a test

**Context:** An `Order__c` trigger must notify an external order system after records are committed. A trigger chunk can hold up to 200 records.

**Problem:** Calling the API from the trigger is not allowed before commit and hides failures. Enqueuing one job per record can pass the 50-enqueue synchronous limit and wastes daily async executions.

### Worker

`force-app/main/default/classes/OrderDispatchQueueable.cls`

```apex
public with sharing class OrderDispatchQueueable implements Queueable, Database.AllowsCallouts {

    public class OmsSyncException extends Exception {}

    private final Set<Id> orderIds;

    public OrderDispatchQueueable(Set<Id> orderIds) {
        this.orderIds = orderIds;
    }

    public void execute(QueueableContext context) {
        // Re-query: the job runs later, so read current values.
        List<Order__c> orders = [
            SELECT Id, External_Key__c, Status__c
            FROM Order__c
            WHERE Id IN :orderIds
            WITH USER_MODE
        ];
        if (orders.isEmpty()) {
            return;
        }
        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:OMS_NC/orders/sync');
        request.setMethod('POST');
        request.setHeader('Content-Type', 'application/json');
        request.setTimeout(10000);
        request.setBody(JSON.serialize(orders));

        HttpResponse response = new Http().send(request);
        if (response.getStatusCode() >= 300) {
            // Surface the failure on the AsyncApexJob record; a Finalizer can pick it up for retry.
            throw new OmsSyncException('OMS sync failed with status ' + response.getStatusCode());
        }
    }
}
```

### Trigger

`force-app/main/default/triggers/OrderTrigger.trigger`

```apex
trigger OrderTrigger on Order__c (after insert, after update) {
    Set<Id> changedOrderIds = new Set<Id>();
    for (Order__c record : Trigger.new) {
        Order__c previous = Trigger.isUpdate ? Trigger.oldMap.get(record.Id) : null;
        if (previous == null || previous.Status__c != record.Status__c) {
            changedOrderIds.add(record.Id);
        }
    }
    if (!changedOrderIds.isEmpty()) {
        System.enqueueJob(new OrderDispatchQueueable(changedOrderIds)); // one job per chunk
    }
}
```

### Test

`force-app/main/default/classes/OrderDispatchQueueableTest.cls`

```apex
@IsTest
private class OrderDispatchQueueableTest {

    @IsTest
    static void enqueuesOneJobAndCallsOut() {
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator().withResponse(200, '{"ok":true}'));
        List<Order__c> orders = new List<Order__c>();
        for (Integer i = 0; i < 200; i++) {
            orders.add(new Order__c(External_Key__c = 'EXT-' + i, Status__c = 'Submitted'));
        }
        Test.startTest();
        insert orders;
        System.assertEquals(1, Limits.getQueueableJobs(), 'one job for the whole chunk');
        Test.stopTest(); // the queued job runs here

        System.assertEquals(1, [SELECT COUNT() FROM AsyncApexJob WHERE JobType = 'Queueable' AND Status = 'Completed']);
    }

    @IsTest
    static void failedCalloutMarksJobFailed() {
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator().withResponse(503, ''));
        Order__c o = new Order__c(External_Key__c = 'EXT-X', Status__c = 'Submitted');
        insert o;
        Test.startTest();
        System.enqueueJob(new OrderDispatchQueueable(new Set<Id>{ o.Id }));
        try {
            Test.stopTest();
        } catch (OrderDispatchQueueable.OmsSyncException e) {
            System.assert(e.getMessage().contains('503'), 'status is reported');
        }
    }
}
```

`MockHttpResponseGenerator` is the shared mock at `templates/apex/tests/MockHttpResponseGenerator.cls`; deploy it with the test. UNVERIFIED (2026-10-03): whether an exception thrown inside a Queueable surfaces at `Test.stopTest()` in every API version; the second test tolerates both behaviors. `Order__c` needs `External_Key__c` and `Status__c`, and the `OMS_NC` Named Credential must exist.

**Why it works:** The enqueue happens once per trigger chunk, well under the 50-enqueue synchronous limit (Apex Developer Guide 262, L19573). The job re-queries current data, calls out under `Database.AllowsCallouts`, and leaves a failed `AsyncApexJob` behind when the remote system rejects it.

---

## Example 2: Scheduler that dispatches a batch, with a test

**Context:** Stale `Lead` records must be closed every night, and the volume can exceed one transaction.

`force-app/main/default/classes/StaleLeadBatch.cls`

```apex
public with sharing class StaleLeadBatch implements Database.Batchable<SObject>, Database.Stateful {
    private Integer failed = 0;

    public Database.QueryLocator start(Database.BatchableContext context) {
        return Database.getQueryLocator([
            SELECT Id, Status
            FROM Lead
            WHERE Status = 'Open - Not Contacted'
            AND LastActivityDate < LAST_N_DAYS:90
        ]);
    }

    public void execute(Database.BatchableContext context, List<Lead> scope) {
        for (Lead leadRecord : scope) {
            leadRecord.Status = 'Closed - Not Converted';
        }
        for (Database.SaveResult result : Database.update(scope, false)) {
            if (!result.isSuccess()) {
                failed++;
            }
        }
    }

    public void finish(Database.BatchableContext context) {
        System.debug(LoggingLevel.INFO, 'StaleLeadBatch ' + context.getJobId() + ' failed rows: ' + failed);
    }
}
```

`force-app/main/default/classes/StaleLeadScheduler.cls`

```apex
public with sharing class StaleLeadScheduler implements Schedulable {
    public void execute(SchedulableContext context) {
        // Synchronous limits apply to scheduled Apex, so dispatch and return.
        Database.executeBatch(new StaleLeadBatch(), 200);
    }
}
```

`force-app/main/default/classes/StaleLeadBatchTest.cls`

```apex
@IsTest
private class StaleLeadBatchTest {

    @IsTest
    static void closesOpenLeadsInOneScope() {
        List<Lead> leads = new List<Lead>();
        for (Integer i = 0; i < 50; i++) {
            leads.add(new Lead(LastName = 'Stale ' + i, Company = 'Acme', Status = 'Open - Not Contacted'));
        }
        insert leads;
        // LastActivityDate cannot be set directly; this test checks the batch runs and leaves fresh leads alone.
        Test.startTest();
        Id jobId = Database.executeBatch(new StaleLeadBatch(), 200);
        Test.stopTest();
        System.assertEquals('Completed', [SELECT Status FROM AsyncApexJob WHERE Id = :jobId].Status);
        System.assertEquals(50, [SELECT COUNT() FROM Lead WHERE Status = 'Open - Not Contacted'], 'leads with no old activity stay open');
    }

    @IsTest
    static void schedulerDispatchesTheBatch() {
        Test.startTest();
        String cronId = System.schedule('Stale lead test', '0 0 2 * * ?', new StaleLeadScheduler());
        Test.stopTest();
        System.assertEquals(1, [SELECT COUNT() FROM CronTrigger WHERE Id = :cronId]);
    }
}
```

The `Status` values assume the default lead status picklist; change them to your org's values.

### Metadata and manifest

Each class needs a `-meta.xml`, for example `force-app/main/default/classes/StaleLeadBatch.cls-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>OrderDispatchQueueable</members>
        <members>OrderDispatchQueueableTest</members>
        <members>MockHttpResponseGenerator</members>
        <members>StaleLeadBatch</members>
        <members>StaleLeadScheduler</members>
        <members>StaleLeadBatchTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>OrderTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <version>67.0</version>
</Package>
```

After deployment, schedule the job once: `System.schedule('Stale lead nightly', '0 0 2 * * ?', new StaleLeadScheduler());`. Before redeploying `StaleLeadScheduler`, delete the scheduled job; deploying a class with pending scheduled jobs fails.

**Why it works:** The scheduler only dispatches, because synchronous limits apply to scheduled Apex (L19536). The batch gets fresh limits per scope, uses partial-success DML, and keeps a failure count across scopes with `Database.Stateful` (instance variables only).
