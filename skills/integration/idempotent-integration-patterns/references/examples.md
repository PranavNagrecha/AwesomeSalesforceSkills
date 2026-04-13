# Examples — Idempotent Integration Patterns

## Example 1: External ID Upsert for Inbound Order Synchronization

**Context:** An ERP system pushes order records into Salesforce every 15 minutes via a scheduled job. Network timeouts and transient errors cause the ERP to retry failed batches. Without idempotency, each retry creates a duplicate Order record in Salesforce.

**Problem:** The ERP integration uses `POST /services/data/v59.0/sobjects/Order__c/` on each call. When the ERP retries after a timeout, Salesforce receives the payload a second time and inserts a new Order record rather than updating the one from the first (successful but unreceived) call. The operations team now has duplicate Orders that must be manually de-duplicated.

**Solution:**

Step 1 — Add the External ID field to Order__c via metadata:

```xml
<!-- Order__c.object-meta.xml snippet -->
<fields>
    <fullName>ERP_Order_Id__c</fullName>
    <externalId>true</externalId>
    <unique>true</unique>
    <type>Text</type>
    <length>50</length>
    <label>ERP Order ID</label>
</fields>
```

Step 2 — ERP switches from POST (insert) to PATCH against the External ID endpoint:

```
PATCH /services/data/v59.0/sobjects/Order__c/ERP_Order_Id__c/ORD-20240315-9001
Content-Type: application/json
Authorization: Bearer {access_token}

{
  "Name": "Order 9001",
  "Status__c": "Processing",
  "Amount__c": 1500.00,
  "ERP_Order_Id__c": "ORD-20240315-9001"
}
```

Step 3 — ERP retry logic sends the identical PATCH on failure. Salesforce finds the matching External ID value and updates the existing record. No duplicate is created.

Step 4 — If the ERP erroneously sends two records with the same ERP Order ID (a data quality problem), Salesforce returns `HTTP 300 MULTIPLE_CHOICES` rather than silently creating a third record. The ERP error handler logs this for human review.

**Why it works:** The upsert endpoint performs a deterministic three-way branch — 0 matches insert, 1 match update, 2+ matches error — entirely based on the External ID value. The outcome of sending the same payload twice is identical to sending it once. The External ID field's `unique=true` constraint prevents the 2+ match case from occurring under normal conditions.

---

## Example 2: Platform Event Subscriber with ReplayId Checkpoint

**Context:** A Salesforce org publishes `Payment_Processed__e` Platform Events when payments are confirmed. A subscriber Apex trigger receives these events and creates `Cash_Receipt__c` records. The subscriber has experienced downtime due to a deployment. During the outage, several Payment events were published and retained on the bus. On restart, the subscriber must process those missed events exactly once — not skip them, not re-process events it already handled before the outage.

**Problem:** On restart, the subscriber re-subscribes from ReplayId `-2` (tip of the queue), which skips all events published during the downtime. Cash receipts are never created for payments processed during the outage. Alternatively, if the team tries to fix this by subscribing from `-1` (all retained events), the subscriber re-processes every event from the last 3 days and creates duplicate Cash Receipt records.

**Solution:**

Step 1 — Ensure the Platform Event uses "Publish After Commit":

```
Setup → Platform Events → Payment_Processed__e → Edit
Publish Behavior: Publish After Commit   ← change from default "Publish Immediately"
```

Step 2 — Create a checkpoint object to persist the last processed ReplayId:

```xml
<!-- Event_Replay_Checkpoint__c.object-meta.xml snippet -->
<fields>
    <fullName>Channel_Name__c</fullName>
    <type>Text</type>
    <length>255</length>
    <unique>true</unique>
    <externalId>true</externalId>
</fields>
<fields>
    <fullName>Last_Replay_Id__c</fullName>
    <type>Text</type>
    <length>50</length>
</fields>
```

Step 3 — Subscriber Apex trigger with idempotent processing and checkpoint write:

```apex
trigger PaymentProcessedSubscriber on Payment_Processed__e (after insert) {
    List<Cash_Receipt__c> receiptsToUpsert = new List<Cash_Receipt__c>();

    for (Payment_Processed__e event : Trigger.new) {
        // Build the Cash Receipt using the payment's stable ID as External ID
        // so that re-delivery of the same event upserts rather than inserts.
        Cash_Receipt__c receipt = new Cash_Receipt__c(
            Payment_External_Id__c = event.Payment_Id__c,  // External ID field
            Amount__c              = event.Amount__c,
            Payment_Date__c        = event.Payment_Date__c
        );
        receiptsToUpsert.add(receipt);
    }

    // Use upsert with the External ID field — safe to run on re-delivery
    Schema.SObjectField extIdField =
        Cash_Receipt__c.Payment_External_Id__c.getDescribe().getSObjectField();
    Database.upsert(receiptsToUpsert, extIdField, false);

    // Write checkpoint AFTER successful processing
    String lastReplayId = String.valueOf(
        Trigger.new[Trigger.new.size() - 1].ReplayId
    );
    Event_Replay_Checkpoint__c checkpoint = new Event_Replay_Checkpoint__c(
        Channel_Name__c  = 'Payment_Processed__e',
        Last_Replay_Id__c = lastReplayId
    );
    upsert checkpoint Event_Replay_Checkpoint__c.Channel_Name__c;
}
```

Step 4 — On subscriber restart, the CometD client reads the stored `Last_Replay_Id__c` and subscribes from that position, replaying only events published after the last successfully processed one.

**Why it works:** Two complementary idempotency guards work together. The Platform Event's "Publish After Commit" setting ensures no phantom events are delivered. The `Database.upsert()` with the External ID field in the subscriber ensures that if the same event is delivered twice (at-least-once delivery), the second delivery updates the existing Cash Receipt rather than creating a duplicate. The checkpoint written after processing ensures that the subscriber resumes from precisely the right position, not from an arbitrary fixed point.

---

## Anti-Pattern: Idempotency Key Generated at Callout Time

**What practitioners do:** Generate a UUID inside the callout method body on every execution:

```apex
// WRONG: key is regenerated on each execution attempt
public void execute(QueueableContext ctx) {
    String idempotencyKey = UUID.randomUUID().toString(); // new key every time
    HttpRequest req = new HttpRequest();
    req.setHeader('X-Idempotency-Key', idempotencyKey);
    req.setBody(buildPayload(this.orderId));
    new Http().send(req);
}
```

**What goes wrong:** Each execution attempt — including every retry — sends a different `X-Idempotency-Key`. The external payment processor treats each attempt as a distinct new charge because it has never seen that key before. The result is multiple charges for the same order, or multiple shipments, or multiple ERP entries. The logs show one Salesforce Queueable job; the external system shows three charges.

**Correct approach:** Generate the key exactly once when the work item is first enqueued, persist it to the triggering record, and read it on every attempt:

```apex
// CORRECT: key generated once at enqueue time, stored in Order__c.Callout_Idempotency_Key__c
public void execute(QueueableContext ctx) {
    Order__c order = [
        SELECT Id, Callout_Idempotency_Key__c
        FROM Order__c
        WHERE Id = :this.orderId
        LIMIT 1
    ];
    // Key already exists from when the job was enqueued
    HttpRequest req = new HttpRequest();
    req.setHeader('X-Idempotency-Key', order.Callout_Idempotency_Key__c);
    req.setBody(buildPayload(order));
    new Http().send(req);
}

// Enqueue method — called once when the order transitions to "Ready to Charge"
public static void enqueue(Id orderId) {
    Order__c order = [SELECT Id FROM Order__c WHERE Id = :orderId];
    order.Callout_Idempotency_Key__c = generateStableKey(orderId);
    update order;
    System.enqueueJob(new PaymentCalloutQueueable(orderId));
}
```
