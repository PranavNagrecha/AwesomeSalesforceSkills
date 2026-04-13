# Examples — Event-Driven Architecture

## Example 1: Choosing Choreography for a Retail Order Lifecycle

**Scenario:** A retailer running Salesforce Commerce Cloud (B2C) and Salesforce Sales Cloud needs to notify three downstream systems when an order is placed: a fulfillment warehouse (SAP), a customer communication platform (Marketing Cloud), and a finance ledger (NetSuite). Each system operates independently and failures in one should not block others.

**Problem:** The team initially designed a synchronous Apex trigger that called all three external APIs in sequence during the Order record save. When SAP had a 30-second timeout, the entire transaction failed and the order record was not saved. Marketing Cloud and NetSuite were never notified.

**Solution:**

The architecture was redesigned as a choreography pattern using Platform Events as the Salesforce-native transport:

1. An Apex after-insert trigger publishes an `Order_Placed__e` Platform Event with schema version, order ID, idempotency key (order external ID), and a timestamp. The trigger does not call any external system.
2. A MuleSoft Anypoint subscription receives `Order_Placed__e` events via the Pub/Sub API and fans the event out to SAP, Marketing Cloud, and NetSuite over separate queued channels.
3. Each downstream system processes the event independently. SAP failure does not block Marketing Cloud delivery.
4. Each consumer writes a processed-event log keyed on the idempotency key to prevent duplicate processing on redelivery.

```text
Architecture Decision Record — Order Lifecycle EDA

Pattern:       Pub/Sub (Salesforce) → Fanout (MuleSoft) → Queuing (per system)
Consistency:   Eventual — fulfillment, notification, and finance may complete at different times
Idempotency:   Consumers deduplicate on Order_External_ID__c
Compensation:  Each system handles its own failure independently; no global rollback
Replay:        Platform Events replay window (72 hours) used for consumer restart only,
               not for state reconstruction
```

**Why it works:** Choreography decouples the Salesforce order transaction from downstream system availability. Each consumer's failure is isolated. The idempotency key ensures that a consumer restart does not create duplicate records. The explicit consistency model (eventual) was accepted by the business because a 5-minute delay in NetSuite posting is tolerable.

---

## Example 2: Rejecting Event Sourcing Without an External Durable Store

**Scenario:** A financial services firm wants to implement event sourcing for their loan application workflow on Salesforce. The requirement is that the full audit history of every state transition (Applied, Underwriting, Approved, Funded, Closed) must be reconstructable from the event log at any future point.

**Problem:** The architecture team initially proposed using Platform Events as the event log. The Loan_State_Changed__e event would be published on every transition and consumers would replay the event stream to reconstruct current state.

**Solution:**

The proposal was rejected at architecture review for the following reasons:

- Platform Events have a maximum replay window of 72 hours (3 days maximum with extended retention). A loan application active for 90 days cannot have its state reconstructed from the Platform Events bus.
- Platform Events do not provide query access to historical events — only replay from a checkpoint. SOQL cannot query `Loan_State_Changed__e` history.
- Regulatory audit requirements mandate 7-year event retention.

The approved architecture uses Platform Events as the **transport** only:

```text
Architecture Decision Record — Loan Event Sourcing

Pattern:          Event sourcing with external durable store
Transport:        Loan_State_Changed__e Platform Event (72-hour delivery bus)
Durable Store:    Custom Loan_Event_Log__c object (append-only, never updated)
Retention:        Event_Log__c records retained per data retention policy (7 years)
State Rebuild:    SOQL on Event_Log__c ordered by Event_Sequence__c
Schema Version:   Version__c field on each event record
Idempotency:      External_Event_ID__c unique index on Event_Log__c
```

Each Platform Event subscriber writes the event payload as an immutable `Loan_Event_Log__c` record. State is reconstructed by querying and replaying `Loan_Event_Log__c` records in sequence order, not from the Platform Events bus.

**Why it works:** The durable store (Event_Log__c) survives beyond the 72-hour Platform Events window. The bus handles delivery; the object handles retention and queryability. This separation is the correct architectural pattern when event sourcing is genuinely required in Salesforce.

---

## Anti-Pattern: Using EDA to Replace a Simple Request-Reply Integration

**What practitioners do:** A team needs Salesforce to fetch an account credit score from an external credit bureau API when an opportunity reaches Closed Won stage. They design a Platform Event trigger, a subscriber that calls the external API, and a second Platform Event to write the result back to the record.

**What goes wrong:** The round-trip adds 5–30 seconds of latency through two asynchronous hops. The UI must poll for the result or use Streaming API to detect the update. Error handling now spans two async transactions, making debugging harder. The business requirement was simply "show the credit score on the record when the opportunity closes."

**Correct approach:** A synchronous Apex callout in an `@future` method or a Queueable job is sufficient. The event-driven round-trip adds async complexity, debugging overhead, and latency for a use case that has a single producer, a single consumer, and no fan-out requirement. EDA is the wrong architectural style here. Use request-reply.
