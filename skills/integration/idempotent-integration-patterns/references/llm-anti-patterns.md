# LLM Anti-Patterns — Idempotent Integration Patterns

Common mistakes AI coding assistants make when generating or advising on Idempotent Integration Patterns.
These patterns help the consuming agent self-check its own output.

### Anti-Pattern 1: Idempotency Key Regenerated on Every Retry

**What LLMs do:** Generate a new UUID or random token inside the callout execution method body on every invocation, then pass it as the `X-Idempotency-Key` header:

```apex
// WRONG — LLM-generated pattern
public void execute(QueueableContext ctx) {
    String key = EncodingUtil.convertToHex(Crypto.generateAesKey(128)); // new key each run
    HttpRequest req = new HttpRequest();
    req.setHeader('X-Idempotency-Key', key);
    req.setBody(JSON.serialize(payload));
    new Http().send(req);
}
```

**Why:** LLMs are trained on documentation examples that show how to construct an idempotency key for illustration purposes, not how to persist and reuse it across retries. The training data conflates "generating" a key with "using" a key.

**Correct approach:** Generate the key once at enqueue time, persist it to the driving record, and read it in the execution method:

```apex
// CORRECT — key generated once when work item is created
public static void enqueue(Id orderId) {
    Order__c o = [SELECT Id FROM Order__c WHERE Id = :orderId];
    o.Callout_Idempotency_Key__c =
        EncodingUtil.convertToHex(Crypto.generateAesKey(128));
    update o;
    System.enqueueJob(new PaymentCalloutQueueable(orderId));
}

public void execute(QueueableContext ctx) {
    Order__c o = [
        SELECT Callout_Idempotency_Key__c FROM Order__c WHERE Id = :this.orderId
    ];
    HttpRequest req = new HttpRequest();
    req.setHeader('X-Idempotency-Key', o.Callout_Idempotency_Key__c);
    req.setBody(JSON.serialize(buildPayload(o)));
    new Http().send(req);
}
```

**Detection:** Look for any call to `Crypto.generateAesKey()`, `UUID.randomUUID()`, `Math.random()`, or `System.now().getTime()` inside an `execute()` method body or inside a method that is called on every attempt. If the key-generation code is not in an enqueue or initialization path followed by a DML write, flag it.

---

### Anti-Pattern 2: Platform Event Published with "Publish Immediately" Assumed Safe

**What LLMs do:** Generate `EventBus.publish()` calls inside Apex methods that also contain DML, and document the pattern as "transactionally safe" without mentioning the Publish Behavior setting. LLMs often include a note about "events fire before commit" without connecting this to the actionable fix.

```apex
// WRONG — LLM assumes this is safe in a transactional context
trigger OrderTrigger on Order__c (after insert) {
    List<Payment_Confirmed__e> events = new List<Payment_Confirmed__e>();
    for (Order__c o : Trigger.new) {
        events.add(new Payment_Confirmed__e(Order_Id__c = o.Id));
    }
    EventBus.publish(events); // fires immediately, not after commit
}
```

**Why:** LLMs are trained on Salesforce documentation examples that use the default "Publish Immediately" setting for brevity. The documentation notes the behavior but many training examples do not model the configuration step needed to change it.

**Correct approach:** Explicitly verify and document the Platform Event's Publish Behavior setting. For any event published inside a transaction that performs DML, the setting must be "Publish After Commit":

```
Setup → Platform Events → Payment_Confirmed__e → Edit
Publish Behavior: Publish After Commit
```

The Apex code itself does not change — `EventBus.publish()` is the same call. The configuration change is at the event definition level, not in the code.

**Detection:** Look for `EventBus.publish()` calls in Apex triggers or methods that also contain DML (`insert`, `update`, `upsert`, `delete`). If the review does not include a note verifying the Platform Event's "Publish Behavior" is "Publish After Commit," flag it.

---

### Anti-Pattern 3: Using POST (Insert) Instead of PATCH (Upsert) for Inbound Sync

**What LLMs do:** Generate REST integration code that queries for an existing record and then branches: insert if not found, update if found. This is presented as "idempotent" because it avoids double inserts — but it is not safe under concurrent retries.

```python
# WRONG — LLM-generated Python middleware
existing = sf.query(f"SELECT Id FROM Order__c WHERE ERP_Order_Id__c = '{erp_id}'")
if existing['totalSize'] == 0:
    sf.Order__c.create({'ERP_Order_Id__c': erp_id, 'Status__c': 'New'})
else:
    sf.Order__c.update(existing['records'][0]['Id'], {'Status__c': 'New'})
```

**Why:** LLMs model CRUD patterns from general programming training data where query-then-branch is a common idiom. The Salesforce External ID upsert endpoint collapses this to one atomic operation, but LLMs do not consistently prefer it because the REST upsert endpoint is less prominent in training data than basic CRUD examples.

**Correct approach:** Use the External ID upsert endpoint directly — one call, one atomic operation:

```python
# CORRECT — single atomic upsert via External ID
sf.Order__c.upsert(
    'ERP_Order_Id__c',
    erp_id,
    {'Status__c': 'New', 'ERP_Order_Id__c': erp_id}
)
# Equivalent REST call:
# PATCH /services/data/v59.0/sobjects/Order__c/ERP_Order_Id__c/{erp_id}
```

**Detection:** Look for a SOQL query (`SELECT Id FROM ... WHERE ExternalIdField__c = ...`) immediately followed by a conditional `insert`/`create` and `update`. This pattern should be replaced with an External ID upsert.

---

### Anti-Pattern 4: ReplayId Checkpoint Written Before Processing

**What LLMs do:** Generate Platform Event subscriber code that stores the ReplayId at the start of the trigger body to "mark the event as seen" and prevent re-processing. When processing fails after the checkpoint write, the failed event is permanently skipped.

```apex
// WRONG — checkpoint written before processing
trigger PaymentEventSubscriber on Payment_Confirmed__e (after insert) {
    for (Payment_Confirmed__e event : Trigger.new) {
        // Store checkpoint first to prevent re-processing
        saveCheckpoint(event.ReplayId);  // WRONG ORDERING
        processPaymentEvent(event);      // if this fails, event is lost
    }
}
```

**Why:** LLMs associate "idempotency" with "mark as seen before processing" patterns drawn from message queue documentation (e.g., Kafka consumer offset commit). In Kafka, committing the offset before processing is a valid at-most-once strategy. For Salesforce Platform Events with at-least-once delivery semantics and subscriber-side idempotency guards, the correct strategy is at-least-once-processed, which requires writing the checkpoint after successful processing.

**Correct approach:** Write the ReplayId checkpoint only after all processing has committed:

```apex
// CORRECT — checkpoint written after processing completes
trigger PaymentEventSubscriber on Payment_Confirmed__e (after insert) {
    for (Payment_Confirmed__e event : Trigger.new) {
        processPaymentEvent(event);   // idempotent: uses External ID upsert internally
    }
    // Checkpoint written after all events in the batch are processed
    String lastReplayId = String.valueOf(
        Trigger.new[Trigger.new.size() - 1].ReplayId
    );
    saveCheckpoint('Payment_Confirmed__e', lastReplayId);
}
```

**Detection:** Look for checkpoint-write calls (DML on a checkpoint/cursor object) that appear before the primary processing DML or callout within the same trigger or method. The checkpoint write should be the last operation in the trigger body.

---

### Anti-Pattern 5: External ID Field Created Without Unique Constraint

**What LLMs do:** Generate metadata for an External ID field that sets `externalId=true` but omits `unique=true`. The generated field definition looks correct for enabling the upsert endpoint but silently allows duplicate External ID values to accumulate, eventually causing `MULTIPLE_CHOICES` errors on upsert retries.

```xml
<!-- WRONG — missing unique constraint -->
<fields>
    <fullName>ERP_Order_Id__c</fullName>
    <externalId>true</externalId>
    <!-- unique: not specified — defaults to false -->
    <type>Text</type>
    <length>50</length>
</fields>
```

**Why:** LLMs learn from documentation examples that emphasize `externalId=true` as the key property for enabling the upsert API path. The `unique=true` constraint is documented separately as a best practice, not as a required companion property, so LLMs treat it as optional. In practice, an External ID field without a unique constraint is broken for retry-safe upsert patterns because duplicate values cause the 300 error.

**Correct approach:** Always include both properties:

```xml
<!-- CORRECT — unique constraint required for safe upsert -->
<fields>
    <fullName>ERP_Order_Id__c</fullName>
    <externalId>true</externalId>
    <unique>true</unique>
    <type>Text</type>
    <length>50</length>
    <label>ERP Order ID</label>
</fields>
```

**Detection:** Scan any generated External ID field metadata (`.object-meta.xml` or Setup UI instructions) for `<externalId>true</externalId>` without an accompanying `<unique>true</unique>`. Any External ID field definition missing the unique constraint should be flagged.

---

### Anti-Pattern 6: Treating Duplicate Management Rules as an Idempotency Mechanism

**What LLMs do:** Recommend enabling Salesforce Duplicate Management (Matching Rules + Duplicate Rules) as the solution to prevent duplicate records created by integration retries. This is presented as an alternative to External ID upsert, often because the LLM conflates "preventing duplicates" with "idempotent integration."

**Why:** Duplicate Management and idempotency both prevent duplicate records, so LLMs associate them. However, Duplicate Management operates at the UI and API layer with fuzzy matching logic; it is not a retry-safe mechanism. A duplicate rule can block a legitimate retry of a failed insert, or pass a retry that creates a near-duplicate if the field values differ slightly between attempts.

**Correct approach:** Use External ID upsert for integration idempotency. Duplicate Management is for preventing user-entered duplicates based on fuzzy matching (name, email, phone similarity). These are separate concerns with separate tools:

```
Integration idempotency  →  External ID upsert (deterministic, atomic)
User duplicate prevention →  Matching Rules + Duplicate Rules (fuzzy, advisory)
```

**Detection:** Look for recommendations to create Matching Rules or Duplicate Rules as the solution to integration retry safety. This is a scope mismatch — flag it and redirect to the External ID upsert pattern.
