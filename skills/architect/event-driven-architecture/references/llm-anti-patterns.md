# LLM Anti-Patterns — Event-Driven Architecture

Common mistakes AI coding assistants make when generating or advising on event-driven architecture decisions for Salesforce. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Platform Events Replay With Event Sourcing

**What the LLM generates:** "Use Platform Events with replay enabled to implement event sourcing for your Salesforce loan application. Subscribers can replay from `replayId: -2` to reconstruct the full event history."

**Why it happens:** LLMs are trained on EDA literature where event sourcing and event streaming are described together. Apache Kafka and similar systems do support indefinite retention. The LLM generalizes this to Platform Events without knowing the 72-hour ceiling.

**Correct pattern:**

```text
Platform Events replay window: 72 hours (maximum 3 days with extended retention).
This is a delivery guarantee for consumer restart — not a durable event log.
For event sourcing state reconstruction beyond 72 hours, use:
- Data Cloud (streaming ingestion via Pub/Sub API, configurable retention)
- Apache Kafka (configurable unlimited retention)
- Custom Event_Log__c object (append-only, SOQL-queryable, subject to storage limits)
Platform Events deliver to the durable store; they do not replace it.
```

**Detection hint:** Watch for "Platform Events replay" and "event sourcing" in the same recommendation without mention of an external durable store or retention limits.

---

## Anti-Pattern 2: Recommending Choreography for Use Cases Requiring Transactional Integrity

**What the LLM generates:** "Use choreography with Platform Events for your loan disbursement workflow. Each system listens for events and processes independently — this is the modern, decoupled approach."

**Why it happens:** Choreography is frequently promoted in EDA literature as the "modern" alternative to orchestration. LLMs absorb this framing and apply it without evaluating whether eventual consistency is acceptable for the specific use case.

**Correct pattern:**

```text
Choreography commits to eventual consistency. There is no central coordinator to
detect partial completion or trigger compensating transactions.

For financial transactions, fund disbursements, or any workflow where all steps
must complete or all must roll back:
→ Use orchestration (Flow Orchestration or Apex Queueable orchestrator)
→ The orchestrator retains transactional state and can compensate on failure

Only choose choreography when the business explicitly accepts that steps may
complete at different times and partial completion is a tolerable outcome.
```

**Detection hint:** Watch for "choreography" recommended for workflows involving money movement, inventory deduction, or compliance-gated approvals without an explicit statement that eventual consistency is acceptable.

---

## Anti-Pattern 3: Prescribing EDA for Simple Request-Reply Scenarios

**What the LLM generates:** "Publish a Platform Event when the opportunity closes, subscribe to it in a Flow that calls an external API, then publish a result event back to update the record. This gives you a decoupled, event-driven integration."

**Why it happens:** LLMs optimize for pattern-completeness and often recommend event-driven patterns as a default because they are associated with scalability and resilience in training data, regardless of whether the use case justifies the complexity.

**Correct pattern:**

```text
EDA is appropriate when:
- Multiple consumers must react to the same event (fan-out)
- Producer throughput must be decoupled from consumer capacity (load leveling)
- Consumers must be independently deployable and scalable

For single-producer, single-consumer, synchronous-response scenarios:
→ Use a direct Apex @future callout or Queueable callout
→ Simpler call stack, easier error handling, lower latency, no event bus overhead

Adding an async event round-trip to a request-reply use case adds latency
and complexity without any architectural benefit.
```

**Detection hint:** Watch for Platform Event publish + Platform Event result pattern for integrations that have one caller and one responder.

---

## Anti-Pattern 4: Designing Event Schema Without a Versioning Strategy

**What the LLM generates:** An event schema with business fields but no version indicator:

```json
{
  "orderId": "a1B000000xyz",
  "customerId": "0013000000abc",
  "totalAmount": 299.99,
  "status": "PLACED"
}
```

**Why it happens:** LLMs generate minimal schemas that satisfy the immediate requirement. Schema versioning is an operational concern that requires foresight about future changes — LLMs under-weight future-proofing in favor of immediate correctness.

**Correct pattern:**

```json
{
  "schemaVersion": "1.0",
  "eventId": "evt-uuid-here",
  "eventType": "OrderPlaced",
  "occurredAt": "2026-04-13T10:00:00Z",
  "orderId": "a1B000000xyz",
  "customerId": "0013000000abc",
  "totalAmount": 299.99,
  "status": "PLACED"
}
```

Every event payload must include: `schemaVersion` (enables consumers to route to the correct parser), `eventId` (idempotency key), `eventType` (human-readable business event name), `occurredAt` (timestamp for ordering and audit). Consumers must ignore unknown fields (forward compatibility). Breaking schema changes require a new `schemaVersion` or a new event type — never an in-place field rename or removal.

**Detection hint:** Watch for event schema proposals without a version field, without an idempotency key, or with operation-named event types (RecordUpdated) rather than business-event names (OrderPlaced).

---

## Anti-Pattern 5: Missing Idempotency Design — Assuming Exactly-Once Delivery

**What the LLM generates:** Consumer logic that creates a record directly upon event receipt, with no deduplication check:

```apex
trigger OrderPlacedSubscriber on Order_Placed__e (after insert) {
    for (Order_Placed__e event : Trigger.new) {
        Order__c order = new Order__c(
            External_Order_Id__c = event.Order_Id__c,
            Status__c = 'New'
        );
        insert order;
    }
}
```

**Why it happens:** LLMs model the happy path. At-least-once delivery is a property of distributed systems that is under-represented in code examples in training data, which typically show the single-event, single-consumer path.

**Correct pattern:**

```apex
trigger OrderPlacedSubscriber on Order_Placed__e (after insert) {
    Set<String> externalIds = new Set<String>();
    for (Order_Placed__e event : Trigger.new) {
        externalIds.add(event.Order_Id__c);
    }
    // Check for already-processed events
    Map<String, Order__c> existing = new Map<String, Order__c>();
    for (Order__c o : [SELECT Id, External_Order_Id__c FROM Order__c
                        WHERE External_Order_Id__c IN :externalIds]) {
        existing.put(o.External_Order_Id__c, o);
    }
    List<Order__c> toInsert = new List<Order__c>();
    for (Order_Placed__e event : Trigger.new) {
        if (!existing.containsKey(event.Order_Id__c)) {
            toInsert.add(new Order__c(
                External_Order_Id__c = event.Order_Id__c,
                Status__c = 'New'
            ));
        }
    }
    if (!toInsert.isEmpty()) insert toInsert;
}
```

Alternatively, use UPSERT with an External ID field — this is the simplest idempotency implementation for Salesforce consumers.

**Detection hint:** Watch for consumer trigger or Flow logic that creates records on event receipt without an idempotency check (EXISTS query, UPSERT, or processed-event log lookup).

---

## Anti-Pattern 6: Recommending Platform Events as an Event Store for Recovery Scenarios

**What the LLM generates:** "If your downstream system goes offline, it can reconnect and replay all missed events using `replayId: -2` to start from the beginning of the event stream."

**Why it happens:** The `-2` replayId (replay all retained events) is prominently documented in the Platform Events Developer Guide and is correctly used for consumer restart scenarios. LLMs over-generalize this to mean the bus is an event store with indefinite retention.

**Correct pattern:**

```text
replayId: -2 replays events within the retention window only (up to 72 hours / 3 days).
Events older than the retention window are permanently gone from the bus.

For disaster recovery scenarios where a consumer could be offline for longer:
→ The durable store (Event_Log__c, Data Cloud, Kafka) is the recovery source
→ Platform Events deliver to the durable store in near-real time
→ Recovery replays from the durable store, not from the bus

Do not present Platform Events replay as a disaster recovery mechanism for
outages longer than the retention window.
```

**Detection hint:** Watch for recommendations that a consumer can "catch up on all missed events" via replay without specifying the 72-hour ceiling or confirming the outage duration is within the window.
