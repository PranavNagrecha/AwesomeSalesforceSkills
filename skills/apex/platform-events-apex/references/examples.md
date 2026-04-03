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
