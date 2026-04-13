---
name: idempotent-integration-patterns
description: "Use this skill to design or review Salesforce integrations that must be safe to retry — covering External ID upsert semantics, Platform Event replay with ReplayId, Publish After Commit configuration, and idempotency key management. NOT for duplicate management rules or Duplicate Management configuration."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
triggers:
  - "how do I make my integration safe to retry without creating duplicate records"
  - "Platform Events are being redelivered and I am getting duplicate processing"
  - "my external system retries failed API calls and I am seeing duplicate data in Salesforce"
  - "what is the correct way to use External ID fields for upsert operations"
  - "idempotency key strategy for callouts from Salesforce to an external system"
tags:
  - idempotency
  - external-id
  - upsert
  - platform-events
  - retry-safe
inputs:
  - "Integration direction: inbound (external system → Salesforce), outbound (Salesforce → external), or both"
  - "Transport mechanism: REST API, Platform Events, Outbound Messages, or custom callout"
  - "Whether the external system sends a stable unique identifier per business event"
  - "Current retry or error-handling strategy in place"
outputs:
  - "Idempotency design recommendation covering key generation, storage, and lookup strategy"
  - "External ID field configuration guidance for upsert-safe inbound integrations"
  - "Platform Event subscriber pattern with ReplayId tracking and Publish After Commit configuration"
  - "Outbound callout pattern with persisted idempotency key (pre-enqueue generation)"
  - "Review checklist confirming retry-safe behavior"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Idempotent Integration Patterns

This skill activates when a practitioner needs to ensure that integration messages can be delivered or retried more than once without producing duplicate records, duplicate side effects, or data inconsistency in Salesforce. It covers both inbound (external system writes to Salesforce) and outbound (Salesforce calls an external system) directions.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the external system supplies a stable unique identifier per business event (order ID, payment reference, event GUID). Without a stable key, idempotency cannot be guaranteed at the platform level.
- Identify the transport: REST upsert via External ID, Platform Events with ReplayId, Outbound Messages with a stable message ID, or a custom HTTP callout using X-Idempotency-Key headers.
- Check the Platform Event's "Publish Behavior" setting in the event definition. The default is "Publish Immediately," which fires before DML is committed and breaks at-least-once subscriber guarantees. It must be "Publish After Commit" for subscriber idempotency to hold.
- Clarify governor limit exposure: External ID upsert via the Bulk API or REST Collections API behaves differently from single-record upsert under high volume. Understand whether the caller is sending one record at a time or batches.

---

## Core Concepts

### Concept 1: External ID Upsert Semantics

The Salesforce REST API and Bulk API support upsert via a designated External ID field. The platform applies a deterministic three-way branch per incoming record:

- **0 matches** — the record is inserted as a new record.
- **1 match** — the matching record is updated in place.
- **2+ matches** — the operation returns an error for that row (`MULTIPLE_CHOICES`).

Because the outcome is determined entirely by whether the External ID value already exists, resending the same payload produces the same outcome: an insert the first time, an update on every subsequent retry. This makes External ID upsert the primary idempotency mechanism for inbound integrations.

An External ID field must be marked `externalId=true` in the object metadata. It should also be marked `unique=true` to prevent the 2+ match error. The field type must be Text, Number, or Email. Auto-number fields cannot serve as External IDs in the upsert API path.

Platform governor limits: the REST upsert endpoint (`/services/data/vXX.0/sobjects/{Object}/{ExternalIdField}/{Value}`) handles one record per call. Use the Collections endpoint (`/composite/sobjects/{Object}/{ExternalIdField}`) for batches of up to 200 records. Bulk API v2 handles millions of records with asynchronous job semantics.

### Concept 2: Platform Events, ReplayId, and Publish After Commit

Platform Events carry a `ReplayId` — an opaque monotonically increasing cursor assigned by the event bus at publication time. Subscribers can resume from a specific `ReplayId` to replay missed events within the 3-day retention window (72 hours). This enables at-least-once delivery: if a subscriber fails mid-processing, it can re-subscribe from the last successfully processed `ReplayId`.

For the replay to be useful the subscriber must store the last processed `ReplayId` in a durable location (a custom object, Platform Cache with fallback, or an external store) before acknowledging completion of processing.

The Apex trigger on a Platform Event fires inside a separate transaction from the publishing transaction. If the subscriber writes DML, that DML is in its own transaction. The subscriber should treat each event delivery as potentially a re-delivery and guard accordingly — usually by checking whether the record identified by an External ID or a unique field already reflects the event's intent.

### Concept 3: Publish After Commit vs Publish Immediately

Every Platform Event definition has a "Publish Behavior" property:

- **Publish Immediately** (default) — the event is enqueued on the bus at the moment `EventBus.publish()` is called, before the surrounding transaction commits or rolls back. If the publisher transaction rolls back, the event has already been published and subscribers will process it for a record that does not yet exist (or no longer exists). This breaks idempotency because a subscriber may create or mutate data based on a phantom event.
- **Publish After Commit** — the event is only enqueued if the surrounding transaction commits successfully. If the transaction rolls back, no event is published. This is the correct setting for transactional outbox patterns and for maintaining causal consistency between the published data and the event payload.

Change "Publish Behavior" in Setup → Platform Events → [Event Name] → Edit. This change is not available via API metadata deployment in all org types; verify in the target environment.

### Concept 4: Idempotency Key Management for Outbound Callouts

When Salesforce initiates an outbound HTTP callout that may be retried (e.g., from a Queueable or a flow with retry logic), the request must carry an idempotency key that:

1. Is generated exactly once, before the first attempt.
2. Is persisted alongside the work item (in a custom object or a Platform Event payload field) before the first callout is made.
3. Is reused verbatim on every retry of the same logical operation.

The key must NOT be regenerated on each attempt. Common key strategies: a deterministic hash of the stable business inputs (`orderId + eventType + timestamp`), or a UUID generated and stored when the work item is enqueued.

---

## Common Patterns

### Pattern 1: External ID Upsert for Inbound Data Synchronization

**When to use:** An external system pushes records into Salesforce on a schedule or event, and the integration must be retry-safe because the external system may resend on failure.

**How it works:**

1. Define a Text External ID field on the Salesforce object (e.g., `ERP_Order_Id__c`, `externalId=true`, `unique=true`).
2. The external system sends a `PATCH` to `/services/data/vXX.0/sobjects/Order__c/ERP_Order_Id__c/{erpId}` with the full record payload.
3. Salesforce inserts on first call, updates on retry — no duplicate record is created.
4. The external system does not need to track whether it already sent the record; it simply sends and retries on network failure.

**Why not the alternative:** Using `POST` (insert) requires the external system to first query whether the record exists and branch on the result. This is a two-step, non-atomic operation — a race condition window exists between the query and the insert. External ID upsert collapses this to a single atomic operation.

### Pattern 2: Platform Event Subscriber with ReplayId Tracking

**When to use:** An Apex Trigger or Flow subscribes to a Platform Event channel and must process each business event exactly once, even if the subscriber process is interrupted and restarted.

**How it works:**

1. Set the Platform Event's Publish Behavior to "Publish After Commit."
2. In the subscriber Apex trigger, after successfully processing the event payload (writing DML or calling an external service), persist the `ReplayId` to a custom object (e.g., `Event_Replay_Checkpoint__c` with a Text field for the channel name and a Text field for the last ReplayId).
3. On subscriber restart or re-subscription, pass the stored `ReplayId` as the subscription starting point so the CometD client replays only events not yet processed.
4. Guard against re-delivery by checking a unique field on the target record before writing DML — the External ID upsert pattern from Pattern 1 serves as the subscriber's duplicate guard.

**Why not the alternative:** Subscribing from `-1` (all retained events) on restart re-processes the full 3-day backlog. Subscribing from `-2` (tip) skips events that arrived while the subscriber was down. Neither is correct for at-least-once-processed semantics.

### Pattern 3: Persisted Idempotency Key for Outbound Callouts

**When to use:** A Queueable or scheduled Apex job makes a callout to an external payment processor, shipping provider, or ERP that supports idempotency keys on their API.

**How it works:**

1. When the work item is first enqueued, generate a UUID and store it in a custom field on the triggering record (e.g., `Callout_Idempotency_Key__c`).
2. On each execution attempt, read the stored key — do not generate a new one.
3. Pass the key in the `X-Idempotency-Key` (or equivalent) request header.
4. The external system deduplicates based on the key and returns the same response for any retry.
5. On success, clear or archive the key. On terminal failure, flag the record for human review.

**Why not the alternative:** Generating a new UUID on each attempt (a common LLM-produced pattern) means each retry is a new request to the external system, not a replay. The external system processes each retry as a distinct operation, creating duplicate charges, shipments, or orders.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| External system pushes records into Salesforce and may retry on failure | External ID upsert via REST or Bulk API | Single atomic operation; replay-safe by design; no external state needed |
| Platform Event subscriber must resume after downtime without re-processing | ReplayId checkpoint + Publish After Commit | Prevents phantom events and allows resume from last processed position |
| Salesforce makes outbound callout to a service that supports idempotency keys | Generate key once at enqueue, persist to record, reuse on retry | External system deduplicates; Salesforce retries are safe |
| External system has no stable unique identifier | Design rejected — negotiate a stable ID or generate a deterministic surrogate from composite fields | Without a stable key, platform-level idempotency cannot be guaranteed |
| High-volume inbound sync (millions of records) | Bulk API v2 upsert with External ID | Async job semantics handle volume; upsert remains idempotent |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the transport and direction.** Determine whether the integration is inbound (external → Salesforce), outbound (Salesforce → external), or bidirectional. Confirm what transport mechanism is in use (REST, Bulk, Platform Events, Outbound Messages, callout). Each requires a different idempotency mechanism.
2. **Verify External ID field availability.** For inbound patterns, confirm the target sObject has an External ID field marked `externalId=true` and `unique=true`. If not, add one before proceeding. Validate that the field type is Text, Number, or Email.
3. **Check Platform Event Publish Behavior.** For event-driven patterns, navigate to Setup → Platform Events → [Event] → Edit and confirm "Publish Behavior" is set to "Publish After Commit." If it is "Publish Immediately," change it and document the impact on existing subscribers.
4. **Design the idempotency key strategy for outbound callouts.** Identify where the key is generated (at enqueue time), where it is persisted (custom field on the work record), and how it is passed to the external system (HTTP header or request body field). Confirm the external system's idempotency key semantics (TTL, scope, response behavior).
5. **Implement or review the subscriber duplicate guard.** For Platform Event subscribers, confirm that the processing logic is idempotent itself — either by using External ID upsert for any DML it performs, or by checking for existence before insert. Verify that the ReplayId checkpoint is written in the same logical unit of work as the processing.
6. **Test retry scenarios explicitly.** Simulate retry by sending the same payload twice (inbound) or by failing and retrying the Queueable (outbound). Verify that the second execution produces no additional records or side effects. Check error logs for `DUPLICATE_VALUE` or `MULTIPLE_CHOICES` errors that indicate a broken idempotency setup.
7. **Review the checklist below and confirm all items pass before marking the integration complete.**

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] External ID field is present, marked `externalId=true`, and marked `unique=true` on all target sObjects used in upsert operations
- [ ] Platform Event "Publish Behavior" is set to "Publish After Commit" for all events used in transactional patterns
- [ ] Idempotency keys for outbound callouts are generated once at enqueue time and persisted to a durable store before the first attempt
- [ ] Platform Event subscriber stores ReplayId checkpoint after successful processing, not before
- [ ] Subscriber processing logic is itself idempotent (uses upsert or existence check before DML)
- [ ] Retry scenario has been tested end-to-end: same payload sent twice produces one record, not two
- [ ] Error handling for `MULTIPLE_CHOICES` (duplicate External ID values) is in place and alerts on-call

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Publish Immediately fires before commit** — The default "Publish Immediately" Platform Event setting enqueues the event on the bus at the moment `EventBus.publish()` is called, even if the surrounding transaction later rolls back. Subscribers receive an event for a record that was never actually committed. This causes phantom processing: the subscriber may insert or update records that reference a nonexistent parent, or trigger external callouts for operations that were rolled back. Always set "Publish After Commit" for transactional outbox patterns.
2. **Idempotency key regenerated on retry** — Code that generates a UUID or hash inside the callout method body (rather than reading a pre-stored key from the record) produces a different idempotency key on every execution attempt. The external system sees each attempt as a distinct new request and processes all of them, resulting in duplicate charges, duplicate shipments, or duplicate records. Generate the key exactly once before the first enqueue and store it durably.
3. **External ID upsert returns MULTIPLE_CHOICES when the field is not unique** — If the External ID field is created without `unique=true`, the platform allows multiple records to have the same External ID value. A subsequent upsert against that value returns a `300 MULTIPLE_CHOICES` error rather than updating either record. The integration appears to succeed (no insert exception) until a retry reveals the ambiguity. Always mark External ID fields unique.
4. **ReplayId stored before processing, not after** — Storing the checkpoint ReplayId at the start of event processing (before DML or callout) means that if the processing fails partway through, the checkpoint advances past the failed event. On restart, the event is skipped and never re-processed, violating at-least-once semantics. Write the checkpoint only after all processing for that event batch is complete and committed.
5. **Bulk API v2 upsert and External ID case sensitivity** — The REST single-record upsert endpoint performs a case-insensitive match on Text External ID values. The Bulk API v2 upsert performs a case-sensitive match. If the external system sends `"ORD-001"` and the stored value is `"ord-001"`, the Bulk API treats this as no match and inserts a second record. Normalize the case of External ID values at the point of ingestion.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Idempotency design document | Records the key generation strategy, storage location, transport header, and retry behavior for each integration direction |
| External ID field specification | Field API name, type, `externalId=true`, `unique=true`, and the upsert endpoint path |
| Platform Event configuration note | Publish Behavior setting, ReplayId checkpoint object name and fields, subscriber restart procedure |
| Outbound callout pattern snippet | Queueable Apex skeleton showing key retrieval from record, header assignment, and retry guard |

---

## Related Skills

- retry-and-backoff-patterns — use alongside this skill to configure retry intervals and maximum attempt counts; idempotency is a prerequisite for safe retry
- external-id-strategy — use when designing the External ID field schema for a new object; this skill consumes that output
- platform-events-architecture — use for broader event bus design decisions; this skill focuses on the idempotency subset
