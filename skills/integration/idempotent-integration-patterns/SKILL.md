---
name: idempotent-integration-patterns
description: "Use when designing retry-safe integrations with Salesforce — including external ID upsert strategies, idempotency key management for inbound calls, Platform Event replay safety, and Outbound Message retry handling. NOT for Salesforce duplicate management rules."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
triggers:
  - "How do I prevent duplicate records when an integration retries a failed API call?"
  - "What is the correct way to use External IDs for idempotent upsert operations in Salesforce?"
  - "Platform Events are being replayed — how do I make my subscriber idempotent?"
  - "How do I prevent duplicate processing when an Outbound Message is delivered multiple times?"
  - "Integration is creating duplicate records on retry — what pattern should I use?"
tags:
  - idempotent
  - external-id
  - upsert
  - platform-events
  - retry
  - idempotent-integration-patterns
  - integration-patterns
inputs:
  - "Integration direction: inbound (external → Salesforce) or outbound (Salesforce → external)"
  - "Current deduplication or idempotency mechanism in place"
  - "Whether Platform Events, Outbound Messages, or REST API are involved"
  - "External system's ability to generate stable idempotency keys"
outputs:
  - "External ID upsert configuration for inbound idempotent record writes"
  - "Idempotency key strategy for inbound API calls"
  - "Platform Event Publish After Commit configuration for safe event publishing"
  - "Subscriber-side duplicate detection pattern for replayed events"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Idempotent Integration Patterns

This skill activates when a practitioner needs to design or fix retry-safe integrations with Salesforce — ensuring that replayed API calls, retried Platform Events, and repeated Outbound Message deliveries do not produce duplicate records or duplicate side effects. It covers both inbound (external systems writing to Salesforce) and outbound (Salesforce notifying external systems) idempotency patterns.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Idempotency and deduplication are different problems**: Duplicate management rules in Salesforce prevent duplicate records based on matching rules at insertion time. Idempotent integration patterns prevent duplicate DML operations from retried API calls regardless of existing duplicate management rules. Both may be needed together.
- **Most critical idempotency mistake**: Generating a new idempotency key on each retry attempt. This defeats the entire purpose of idempotency — the key must be computed once before the first attempt and reused for all retries of the same operation.
- **Platform Event publishing timing**: The default "Publish Immediately" Platform Event setting can publish an event before a DML transaction commits. If the transaction rolls back, the event has already been published and subscribers process it for a record that never existed. Use "Publish After Commit" for any event that must be correlated with committed DML.

---

## Core Concepts

### External ID Upsert — Primary Inbound Idempotency Mechanism

The Salesforce REST and SOAP APIs support upsert operations via External ID fields. An External ID is a custom field marked as "External ID" on a Salesforce object. The upsert operation behavior:

- **0 matching records**: Inserts a new record.
- **1 matching record**: Updates the existing record.
- **2+ matching records**: Returns an error per row.

This is inherently idempotent: replaying the same upsert with the same External ID and payload always produces the same result — either the record already exists (update) or it was successfully created on a prior attempt (update is a no-op for unchanged fields). There is no risk of creating a duplicate record from a retried call.

External ID upsert via REST API:
```
PATCH /services/data/v63.0/sobjects/Account/ExternalId__c/<externalIdValue>
```

External ID upsert via Bulk API 2.0 (for > 2,000 records):
- Use the Upsert operation with the External ID field specified as the `externalIdFieldName`.

### Idempotency Keys for Inbound API Calls Without External IDs

When an inbound integration cannot use External ID upsert (e.g., the external system generates UUIDs only, or the data requires Apex-level deduplication), use an idempotency key pattern:

1. The external system generates a stable idempotency key (UUID or hash) once before the first call attempt. This key is sent as a custom HTTP header (`X-Idempotency-Key`) or as a field in the payload.
2. Salesforce stores the key (e.g., in a custom `IdempotencyLog__c` object) on the first successful processing.
3. On retry, Salesforce checks the key against the log. If found, it returns the prior result without re-processing.

Critical rule: **The idempotency key must be generated once before the first attempt and reused for all retries.** Generating a new key on each retry means each attempt appears unique — the entire idempotency benefit is lost.

### Platform Event "Publish After Commit"

Platform Events have two publishing timing options:

- **Publish Immediately** (default): The event is published as soon as the `EventBus.publish()` call executes, even if the enclosing DML transaction has not yet committed. If the transaction rolls back (e.g., due to a trigger exception after the publish call), the event has already been delivered to subscribers for a record that no longer exists.

- **Publish After Commit**: The event is only published to subscribers after the enclosing DML transaction has fully committed. If the transaction rolls back, the event is discarded — no subscribers receive it. This is the safe setting for any Platform Event that must be correlated with committed DML.

Set at publish time in Apex:
```apex
// Publish Immediately (default — risky for transactional events)
EventBus.publish(new MyEvent__e(Data__c = 'value'));

// Publish After Commit (safe for transactional events)
EventBus.publishImmediate(new MyEvent__e(Data__c = 'value'), 
    new EventBus.PublishSettings(EventBus.PublishSettings.PublishBehavior.AFTER_COMMIT));
// OR set on the event object before publish:
```

### Platform Event ReplayId for Subscriber-Side Idempotency

Platform Events retain events for 3 days. CometD subscribers can replay events from a specific `replayId` by providing it on reconnection. For subscriber-side idempotency:

1. The subscriber persists the last successfully processed `replayId` externally.
2. On reconnection after a failure, the subscriber provides the persisted `replayId` to receive only events it has not yet processed.
3. The subscriber must still handle duplicates because "at-least-once" delivery means an event may be received more than once even with `replayId` management.

### Outbound Message At-Least-Once Delivery

Outbound Messages use at-least-once delivery — the same message may be delivered multiple times. External systems receiving Outbound Messages must implement idempotency at their end:

1. Use the `<sObject><Id>...</Id></sObject>` in the SOAP payload as the natural idempotency key per record.
2. Store processed record IDs with a timestamp in the external system.
3. On receipt of a duplicate delivery (same record ID within a short window), return the SOAP acknowledgment immediately without re-processing.

---

## Common Patterns

### Idempotent Inbound Record Sync with External ID Upsert

**When to use:** An external system needs to sync records into Salesforce reliably, even when network failures cause retries.

**How it works:**
1. External system assigns a stable external identifier to each record (e.g., ERP order number `ORD-2025-0012345`).
2. A custom field `ERP_Order_Number__c` is created on the Salesforce Order object and marked as External ID and Unique.
3. Each sync operation uses a REST API upsert:
```
PATCH /services/data/v63.0/sobjects/Order/ERP_Order_Number__c/ORD-2025-0012345
Content-Type: application/json
{ "Status": "Fulfilled", "ShipDate": "2025-08-01" }
```
4. On retry (same external ID), the operation updates the existing record rather than creating a duplicate.
5. For bulk syncs (2,000+ records), use Bulk API 2.0 Upsert with `ERP_Order_Number__c` as the `externalIdFieldName`.

### Idempotent Platform Event Subscriber

**When to use:** A CometD or Apex trigger subscriber processes Platform Events but must not process the same event twice.

**How it works:**
1. Every Platform Event includes a stable message identifier in a custom field (e.g., `CorrelationId__c`) generated by the publisher once.
2. The subscriber maintains a processing log (a Salesforce custom object or external store) keyed by `CorrelationId__c`.
3. On receipt of an event: check the log for the `CorrelationId__c`. If found, skip processing and acknowledge. If not found, process and record in the log.
4. Use "Publish After Commit" at the publisher to ensure the event correlates with committed data.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Inbound: prevent duplicate records on retry | External ID upsert (PATCH with external ID) | 0-match inserts, 1-match updates, 2-match errors — inherently replay-safe |
| Inbound: no External ID field available | Idempotency key in payload + deduplication log | Must generate key once before first attempt, reuse for all retries |
| Platform Event: prevent processing rollback orphans | Publish After Commit | Default Publish Immediately publishes before transaction commits |
| Platform Event: replay subscriber after failure | Persist replayId + idempotent subscriber logic | 3-day retention; replay from last processed replayId |
| Outbound Message: prevent duplicate processing | Store processed record IDs in external system | Outbound Messages use at-least-once delivery |
| Generating idempotency key on each retry | Stop — compute once, reuse | New key per retry means each attempt appears unique — idempotency is broken |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify integration direction and mechanism** — Determine whether the idempotency gap is on inbound calls (external → Salesforce), outbound notifications (Salesforce → external), or both. Identify whether Platform Events, Outbound Messages, or REST/SOAP API calls are involved.
2. **For inbound idempotency — establish External ID upsert** — Create or identify an External ID field on the target object. Ensure the field is marked Unique. Validate the external system sends a stable, pre-generated external ID with every record. Switch the API call from POST (insert) to PATCH with the External ID path parameter.
3. **For inbound idempotency without External ID — implement idempotency key log** — Create an `IntegrationIdempotencyLog__c` object (or equivalent) to store processed keys. Implement a pre-processing check in Apex or middleware: if the key is in the log, return the prior result; otherwise process and log the key.
4. **For Platform Event publishing — configure Publish After Commit** — Review all `EventBus.publish()` calls that publish events correlated with DML operations. Change to Publish After Commit for any event where the subscriber must only receive events for committed records.
5. **For Platform Event subscribers — implement subscriber-side deduplication** — Add a `CorrelationId__c` or similar stable field to the Platform Event definition. Implement a processing log in the subscriber. Check the log before processing each event.
6. **For outbound idempotency — implement deduplication in the external system** — Use the Salesforce record ID in the Outbound Message SOAP payload as the natural idempotency key. Store processed record IDs with timestamps in the external system and skip re-processing within a defined window.
7. **Test retry scenarios** — Explicitly test the idempotency implementation by simulating retries: send the same API call or event twice and verify no duplicate records or side effects are produced.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Inbound: External ID field created, marked as Unique, and used in PATCH upsert calls
- [ ] Inbound: External system generates idempotency key ONCE per operation (not per retry)
- [ ] Platform Events: Publish After Commit configured for events correlated with DML
- [ ] Platform Events: Subscriber implements deduplication on CorrelationId or equivalent stable field
- [ ] Outbound Messages: External system deduplicates on Salesforce record ID
- [ ] Retry scenario tested: same API call or event sent twice → no duplicate records or effects
- [ ] Idempotency log maintenance plan documented (purge old entries to avoid unbounded growth)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Generating a new idempotency key on each retry defeats idempotency** — The single most common idempotency design error. The idempotency key must be computed once before the first attempt (e.g., as a hash of the operation payload or a UUID generated at enqueue time) and reused for all retries of the same operation. A key generated at execution time means every retry is treated as a new unique operation — the idempotency log never matches and duplicates are created on every retry.
2. **Platform Event Publish Immediately can publish for rolled-back transactions** — The default "Publish Immediately" setting publishes events to subscribers before the enclosing DML transaction commits. If the transaction subsequently rolls back (due to a trigger error, a validation failure, or a governor limit breach after the publish call), the event has already been delivered. Subscribers receive an event referencing a record that was never committed. Use "Publish After Commit" for any event that must correlate with committed data.
3. **External ID upsert with 2+ matching records throws an error, not a silently ignored update** — If the External ID field is not marked as Unique, and two records share the same external ID value, the upsert operation returns an error for that row rather than updating one of them. This can cause entire bulk operations to fail if the External ID field is not unique. Always mark External ID fields as Unique.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| External ID field design | Custom field configuration for Unique External ID on target object |
| Upsert API call pattern | REST PATCH or Bulk API 2.0 upsert call with External ID path |
| Idempotency key strategy | Pre-generation requirement, storage pattern, check-before-process logic |
| Publish After Commit configuration | Apex EventBus.publish() update for safe Platform Event publishing |
| Subscriber deduplication pattern | CorrelationId check and processing log design |

---

## Related Skills

- retry-and-backoff-patterns — Retry behavior on the calling side (this skill covers the server-side idempotency receiver)
- event-driven-architecture — Platform Event architecture decisions that affect subscriber idempotency design
- outbound-message-setup — Outbound Message delivery behavior this skill's deduplication patterns address
