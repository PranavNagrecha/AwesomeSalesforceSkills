# LLM Anti-Patterns — Real-Time vs Batch Integration

Common mistakes AI coding assistants make when generating or advising on real-time vs batch integration in Salesforce. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Apex Callouts With Platform Events as Equivalent "Real-Time" Solutions

**What the LLM generates:** An LLM recommends "use Platform Events or Apex callouts — both are real-time" without distinguishing that callouts are synchronous and transaction-blocking while Platform Events are asynchronous and fire-and-forget. It then suggests either interchangeably depending on which was mentioned first in the conversation.

**Why it happens:** Both are described in integration docs as "real-time" or "event-driven" mechanisms. LLMs conflate latency characteristics and transactionality — they see both as "fast" and do not model the fundamental synchronous/asynchronous distinction at the transaction level.

**Correct pattern:**

```
Synchronous callout: fires inline, blocks the Salesforce transaction, rollback propagates to the call,
  120s timeout, 100/transaction limit. Use when: caller needs the response to commit/reject.

Platform Event: fires after publish(), does not block transaction, cannot be rolled back once on bus,
  72-hr replay, async subscriber. Use when: decoupling is required, rollback is not needed.

These are NOT interchangeable. Choose based on transactionality requirement first, then latency.
```

**Detection hint:** Look for phrases like "you can use either callouts or Platform Events for real-time" or recommendations that use both in the same sentence without distinguishing synchronous vs asynchronous semantics.

---

## Anti-Pattern 2: Recommending Synchronous Callouts for High-Volume Record Operations

**What the LLM generates:** A trigger is written that calls `@future(callout=true)` or an inline HTTP callout for every inserted or updated record, with a comment like "this ensures real-time sync with the external system". No volume check is performed.

**Why it happens:** LLMs are trained on many single-record trigger examples and generalize them to all use cases. The governor limit of 100 callouts/transaction is not intuitively obvious, and the training examples rarely show bulk operations that would expose the failure.

**Correct pattern:**

```apex
// WRONG: one callout per record — fails at bulk load
trigger OrderTrigger on Order (after insert) {
    for (Order o : Trigger.new) {
        ExternalService.syncOrder(o.Id); // @future callout
    }
}

// CORRECT: publish Platform Event per record, subscriber handles at its own rate
trigger OrderTrigger on Order (after insert) {
    List<Order_Sync_Event__e> events = new List<Order_Sync_Event__e>();
    for (Order o : Trigger.new) {
        events.add(new Order_Sync_Event__e(Order_Id__c = o.Id));
    }
    EventBus.publish(events);
}
```

**Detection hint:** Any trigger that calls a `@future` or callout method inside a `for (SObject s : Trigger.new)` loop. Also look for absence of bulk volume analysis in the recommendation.

---

## Anti-Pattern 3: Assuming Platform Events Provide Transactional Rollback

**What the LLM generates:** Advice like "publish a Platform Event in your trigger — if it fails, Salesforce will roll back the event along with the transaction." This is wrong for the default `PUBLISH_IMMEDIATELY` behavior.

**Why it happens:** LLMs reason by analogy with DML — DML rolls back on exception, therefore anything done inside the same transaction also rolls back. The Platform Event `publishBehavior` distinction is a Salesforce-specific nuance not present in general programming knowledge.

**Correct pattern:**

```
Default Platform Event publishBehavior = PUBLISH_IMMEDIATELY:
  - Event is on the bus as soon as EventBus.publish() returns success
  - If the enclosing transaction later rolls back, the event is NOT retracted
  - Subscribers receive the event even if the source record was never committed

To tie event publishing to transaction commit:
  - Set publishBehavior = PHASE_AFTER_COMMIT on the Platform Event object definition
  - Or publish the event from a separate Queueable that only runs after the originating transaction confirms success
```

**Detection hint:** Look for code that publishes Platform Events inside a try/catch expecting the catch to "cancel" the event, or architecture diagrams showing Platform Events as a rollback-safe mechanism.

---

## Anti-Pattern 4: Using Platform Events as a Bulk ETL Transport for High-Volume Loads

**What the LLM generates:** A design where a migration script or nightly sync publishes one Platform Event per changed record, relying on Apex subscribers to process them asynchronously — presented as a scalable alternative to REST API individual calls.

**Why it happens:** Platform Events are described as scalable and async, so LLMs generalize them to high-volume data movement. The daily event allocation limits and the architectural mismatch between event notification and bulk data transfer are not captured in typical training examples.

**Correct pattern:**

```
Platform Event daily allocations (typical):
  - Developer/Professional: 250,000 events/day
  - Enterprise: 250,000 events/day (can purchase add-ons)
  High-volume events: separate product with different limits

For 150,000 records/day: a single nightly Bulk API 2.0 job consumes 1 API call to create,
1 to upload, 1 to close, and polling calls — total under 20 API calls.
Platform Events for the same volume would consume 150,000 of the 250,000 daily event allocation,
leaving 100,000 for all other event-driven processes in the org.

Use Platform Events for: notifications, workflow triggers, cross-system event fanout.
Use Bulk API 2.0 for: moving large datasets, reconciliation, migration.
```

**Detection hint:** Any design showing one Platform Event per record for volumes over 1,000 records/cycle. Look for absence of daily event allocation math in the recommendation.

---

## Anti-Pattern 5: Treating Bulk API 2.0 Jobs as Atomic Transactions

**What the LLM generates:** Integration logic that checks whether a bulk job "succeeded" or "failed" as a binary outcome and either commits all changes or rolls back — assuming a Bulk API 2.0 job is atomic like a database transaction.

**Why it happens:** LLMs are trained on database and REST API patterns where transactions are often atomic. The Bulk API's parallel batch processing model with independent batch commits is a Salesforce-specific behavior that contradicts this mental model.

**Correct pattern:**

```
WRONG assumption:
  if job.state == "JobComplete": all_records_committed = True
  if job.state == "Failed": no_records_committed = True

CORRECT model:
  job.state == "JobComplete" means: processing finished, some records may have succeeded and
  some may have failed. Always retrieve and process /failedResults/ regardless of job state.

  job.state == "Failed" means: the job itself failed to process (authentication error, schema error)
  — but any batches already committed before the failure are permanent.

Idempotent upsert (externalIdFieldName) is mandatory so that retrying failed rows is safe.
```

**Detection hint:** Code or documentation that checks `job.state == "JobComplete"` without subsequently fetching and processing the `/failedResults/` endpoint. Also look for insert (not upsert) operations without external IDs on retry logic.

---

## Anti-Pattern 6: Ignoring the CDC/Platform Event Replay Window in High-Availability Design

**What the LLM generates:** Architecture diagrams or designs that show CDC or Platform Event subscribers as reliable event consumers without any mention of the replay window limit or a reconciliation fallback, implying "CDC means you never miss a change."

**Why it happens:** The replay capability is highlighted as a reliability feature in documentation, but the finite window (72 hours / 3 days) is a footnote that LLMs tend to omit when presenting the feature positively.

**Correct pattern:**

```
CDC replay window = 3 days (72 hours for standard Platform Events).
After this window, events are gone — no error, no notification, silent gap.

Required complementary design:
  1. Monitor: alert if subscriber has not polled within 48 hours.
  2. Reconcile: if window expires, run a Bulk API 2.0 query job to compare source vs target
     and produce a correction file before resuming CDC-based sync.
  3. Document: the replay window is a hard SLA constraint; it must appear in the integration
     design document, not just in the operations runbook.
```

**Detection hint:** CDC/Platform Event architecture that mentions "replay capability" without specifying the window duration or a reconciliation fallback for outages exceeding the window.
