# Examples — Async Apex

## Example 1: Queueable For Post-Save Callout

**Context:** An `Order__c` trigger needs to notify an external OMS after the records are committed. The payload is small enough for one background job per transaction.

**Problem:** Calling the external API directly from the trigger risks transaction failures, uncommitted-work errors, and poor monitoring.

**Solution:**

```apex
public class OrderDispatchQueueable implements Queueable, Database.AllowsCallouts {
    private final Set<Id> orderIds;

    public OrderDispatchQueueable(Set<Id> orderIds) {
        this.orderIds = orderIds;
    }

    public void execute(QueueableContext context) {
        List<Order__c> orders = [
            SELECT Id, External_Key__c, Status__c
            FROM Order__c
            WHERE Id IN :orderIds
        ];

        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:OMS_NC/orders/sync');
        request.setMethod('POST');
        request.setTimeout(10000);
        request.setBody(JSON.serialize(orders));

        HttpResponse response = new Http().send(request);
        if (response.getStatusCode() >= 300) {
            throw new CalloutException('OMS sync failed: ' + response.getBody());
        }
    }
}

trigger OrderTrigger on Order__c (after insert, after update) {
    Set<Id> changedOrderIds = new Set<Id>();
    for (Order__c record : Trigger.new) {
        changedOrderIds.add(record.Id);
    }
    System.enqueueJob(new OrderDispatchQueueable(changedOrderIds));
}
```

**Why it works:** The transaction commits first, then the Queueable performs the callout with its own async monitoring record and callout support.

---

## Example 2: Scheduled Batch For Nightly Cleanup

**Context:** Stale `Lead` records must be closed every night, and the volume can exceed what one transaction should handle.

**Problem:** A scheduled class that queries and updates everything inline risks CPU, SOQL row, and DML row failures.

**Solution:**

```apex
public class StaleLeadBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext context) {
        return Database.getQueryLocator([
            SELECT Id, Status
            FROM Lead
            WHERE Status = 'Open'
            AND LastActivityDate < :Date.today().addDays(-90)
        ]);
    }

    public void execute(Database.BatchableContext context, List<Lead> scope) {
        for (Lead leadRecord : scope) {
            leadRecord.Status = 'Closed - Inactive';
        }
        Database.update(scope, false);
    }

    public void finish(Database.BatchableContext context) {
        System.debug('Completed batch job ' + context.getJobId());
    }
}

global class StaleLeadScheduler implements Schedulable {
    global void execute(SchedulableContext context) {
        Database.executeBatch(new StaleLeadBatch(), 200);
    }
}
```

**Why it works:** The scheduler only starts the work. Batch handles chunking, fresh limits, and a controllable scope size.

---

## Anti-Pattern: Async Fan-Out Inside A Loop

**What practitioners do:** They call `System.enqueueJob()` once for each record in `Trigger.new`.

```apex
for (Order__c record : Trigger.new) {
    System.enqueueJob(new OrderDispatchQueueable(new Set<Id>{record.Id}));
}
```

**What goes wrong:** Job counts explode, monitoring becomes noisy, and the design is harder to retry or reason about. In chained Queueables, this can also violate child-job limits.

**Correct approach:** Aggregate IDs and enqueue a single job per transaction, or deliberately chunk into a controlled series of jobs.
