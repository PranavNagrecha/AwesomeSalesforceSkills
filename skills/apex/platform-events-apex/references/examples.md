# Examples — Platform Events Apex

## Example 1: Bulk Publish From A Service Class

**Context:** An order-processing service must broadcast `Order_Status_Changed__e` events whenever orders move to `Approved`.

**Problem:** Publishing one event at a time inline and ignoring results makes failures invisible.

**Solution:**

```apex
public with sharing class OrderEventPublisher {
    public static void publishApproved(List<Order__c> approvedOrders) {
        List<Order_Status_Changed__e> eventsToPublish = new List<Order_Status_Changed__e>();
        for (Order__c orderRecord : approvedOrders) {
            eventsToPublish.add(new Order_Status_Changed__e(
                Order_Id__c = orderRecord.Id,
                External_Key__c = orderRecord.External_Key__c,
                Status__c = 'Approved'
            ));
        }

        List<Database.SaveResult> results = EventBus.publish(eventsToPublish);
        for (Integer i = 0; i < results.size(); i++) {
            if (!results[i].isSuccess()) {
                for (Database.Error err : results[i].getErrors()) {
                    System.debug(LoggingLevel.ERROR,
                        'Platform Event publish failed for order ' +
                        approvedOrders[i].Id + ': ' + err.getMessage());
                }
            }
        }
    }
}
```

**Why it works:** Events are bulk-published and publication failures are not silently ignored.

---

## Example 2: Thin Platform Event Trigger Delegating To Queueable

**Context:** A published integration event should trigger a downstream callout without bloating the subscriber trigger.

**Problem:** Heavy logic in the event trigger becomes hard to test and harder to retry.

**Solution:**

```apex
trigger InvoiceSyncEventTrigger on Invoice_Sync_Requested__e (after insert) {
    Set<String> invoiceKeys = new Set<String>();
    for (Invoice_Sync_Requested__e eventRecord : Trigger.New) {
        invoiceKeys.add(eventRecord.Invoice_Key__c);
    }
    System.enqueueJob(new InvoiceSyncQueueable(invoiceKeys));
}
```

**Why it works:** The event trigger remains an adapter. Retry and error-handling complexity moves to a dedicated async worker.

---

## Anti-Pattern: Using Platform Events As A Row-Change Mirror For Everything

**What practitioners do:** They create a custom platform event for every object mutation even when CDC already models the need.

**What goes wrong:** Payload duplication grows, ownership becomes unclear, and consumers cannot tell whether the event represents a business action or just DML noise.

**Correct approach:** Use CDC when row changes are the product. Use Platform Events when the message is a business-defined signal.

---

## Example 3: Proving A Subscriber Is Actually Alive Before You Trust It

**Context:** An `Order_Approved__e` subscriber has been deployed for a month. Downstream reports a gap. The trigger code looks fine and its test class is green.

**Problem:** A green test proves the handler works when an event is handed to it. It proves nothing about whether the subscription is still receiving events. A subscriber that exceeded its `RetryableException` budget sits in `Status = Error` — *"disconnected and stopped receiving published events"* — and when it is later fixed it *"resumes automatically from the tip, starting from new events"* (`object_reference` L131382–131390), so the backlog is gone and no test ever fails.

**Solution:** Make the subscription's runtime state a first-class monitored artifact, not something you look at during an incident.

```sql
-- Run this on a schedule, not just when someone complains.
-- EventBusSubscriber is read-only and internal-users-only (object_reference L131272-131283).
SELECT Topic,
       Name,                -- the trigger name
       Type,                -- 'ApexTrigger'; blank for a flow Pause element
       Status,              -- Running | Error | Suspended | Repartitioning
       Retries,             -- climbing = RetryableException is firing
       LastError,           -- the message from the last EventBus.RetryableException
       LastProcessed,       -- replaces Position as of API 66.0
       LastPublished,       -- replaces Tip as of API 66.0
       IsPartitioned
FROM EventBusSubscriber
WHERE Topic IN ('Order_Approved__e', 'Invoice_Sync_Requested__e')
ORDER BY Topic
```

Read the result like this:

| Observation | What it means | Action |
|---|---|---|
| `Status = Running`, `Retries = 0` | healthy | none |
| `Status = Running`, `Retries` climbing | a failure is being classified as transient when it may not be | inspect `LastError`; check the retry cap is below nine |
| `Status = Error` | the retry budget was exceeded; events are being dropped on the floor | fix and re-save the trigger, then reconcile the gap from your own publisher log — the subscription resumes from the tip, not from the gap |
| `Status = Suspended` | an admin or an internal error disconnected it | resume from the subscription detail page on the platform event |
| `LastPublished = -1` | expected on a `HighVolume` event — *"For high-volume platform events and change events, the value for Tip isn't available and is always -1"* (`object_reference` L131338–131340) | do not compute lag from these columns; use your own `Correlation_Id__c` timestamps |

**Why it works:** The two failure modes that actually lose events in production — a subscription in `Error` and a subscription silently retrying — are both invisible from Apex and both visible in one SOQL query. Alerting on it turns a month-long gap into a same-day one.
