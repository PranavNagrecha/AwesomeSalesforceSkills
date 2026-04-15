---
name: real-time-vs-batch-integration
description: "When to use this skill: choosing between real-time (synchronous callouts, Platform Events, CDC, Pub/Sub API) and batch (Bulk API 2.0, scheduled ETL) integration patterns. Trigger keywords: should I use real-time or batch, how to sync high-volume data, when to use Platform Events vs Bulk API, integration latency vs volume tradeoff. NOT for Batch Apex internals (use batch-apex-patterns), NOT for MuleSoft middleware design (use middleware-integration-patterns), NOT for CDC field tracking configuration."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Reliability
triggers:
  - "should I use real-time or batch integration for syncing orders between Salesforce and ERP"
  - "our nightly data load is taking too long and we want to switch to event-driven sync"
  - "how do I decide whether to use Platform Events or Bulk API for customer data synchronization"
  - "trigger-based Apex callout is timing out under high load, what is the right alternative"
  - "we need near-real-time sync but have over ten thousand records per hour"
tags:
  - integration
  - real-time
  - batch
  - platform-events
  - bulk-api
  - cdc
  - pub-sub-api
  - integration-patterns
  - data-sync
inputs:
  - "Expected record volume per hour or per day for the integration"
  - "Acceptable latency from source change to destination visibility (seconds, minutes, hours)"
  - "Whether the integration must be transactional (rollback on failure) or can be eventually consistent"
  - "Direction of data flow (Salesforce-to-external, external-to-Salesforce, or bidirectional)"
  - "Whether the external system exposes a webhook/event stream or only a polling endpoint"
outputs:
  - "Pattern recommendation (synchronous callout, Platform Events, CDC/Pub/Sub, Bulk API 2.0, or hybrid) with rationale"
  - "Decision table mapping volume + latency to the correct Salesforce integration mechanism"
  - "Risk list for the chosen pattern including governor limits and operational constraints"
  - "Recommended workflow steps for implementing the chosen pattern"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Real-Time vs Batch Integration

This skill activates when a practitioner must choose between real-time and batch integration approaches in Salesforce. It provides a decision framework grounded in the Salesforce Integration Patterns guide, covering synchronous callouts, Platform Events, Change Data Capture, Pub/Sub API, and Bulk API 2.0, and produces a defensible pattern recommendation with limits and tradeoffs.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Volume**: how many records change per hour at peak? Anything above roughly 2,000 records per transaction window is outside Apex callout capacity and requires an async or bulk mechanism.
- **Latency tolerance**: does the business need sub-second acknowledgement, near-real-time (seconds to minutes), or is a nightly window acceptable?
- **Transactionality requirement**: synchronous callouts participate in the Salesforce DML transaction and can be rolled back; CDC events and Platform Events are fire-and-forget once published — they cannot be recalled.
- **Most common wrong assumption**: practitioners frequently treat Platform Events and synchronous Apex callouts as equivalent "real-time" options. They are not — callouts are synchronous and bound by a 120-second timeout and 100 callouts/transaction limit; Platform Events are asynchronous with up to 72-hour replay but no rollback guarantee.

---

## Core Concepts

### Synchronous Callout (Remote Process Invocation — Request and Reply)

An Apex HTTP or SOAP callout fires inline within a DML transaction. The calling transaction blocks until the external system responds or the 120-second timeout elapses. Governor limits: 100 callouts per transaction, 120-second timeout per callout, and callouts cannot be made from triggers that already have DML pending (the "callout after DML" restriction). This pattern is correct when: volume is low (single record or small sets), the caller needs an immediate response to make a commit/rollback decision, and the external system can respond within the timeout.

### Asynchronous Event-Driven (Platform Events and CDC/Pub/Sub API)

Platform Events are schema-defined Salesforce objects published via `EventBus.publish()` or DML insert. Subscribers receive events asynchronously via Apex triggers, CometD streaming, or Pub/Sub API gRPC. Key behavioral facts:

- Events are durable in the event bus for up to **72 hours** (standard volume) or **3 days** (high-volume); subscribers can replay from any point in that window using a replay ID.
- Publishing succeeds even if no subscriber is listening — the event is not lost.
- Events are **not rolled back** when the publishing transaction rolls back (as of Spring '25, standard Platform Events do fire even on transaction rollback by default unless the `publishBehavior` is set to `PHASE_AFTER_COMMIT`).
- CDC events (Change Data Capture) are automatically generated by the platform for tracked objects; they carry field-level change data and the replay window is 3 days.
- Pub/Sub API provides a gRPC-based subscriber interface suitable for high-throughput external consumers.

### Bulk API 2.0 (Batch Data Load)

Bulk API 2.0 is the correct mechanism for loading or extracting large volumes of records — Salesforce recommends it for datasets above 2,000 records. Jobs are asynchronous and processed in the background. Key behavioral facts:

- No cross-batch atomicity: a job that processes 500,000 records in multiple batches will commit successful batches even if later batches fail. There is no "all-or-nothing" job-level rollback.
- Bulk API 2.0 jobs must be processed outside peak business hours when possible to avoid resource contention; Salesforce guidance recommends scheduling large loads during off-peak windows.
- The API uses CSV ingest format; each job has a hard limit of 150 million records per rolling 24-hour period.
- PK chunking (available in legacy Bulk API, not natively in Bulk API 2.0 jobs) is required for very large queries; use query jobs or SOQL with cursor-based pagination instead.

### Hybrid Approach

Many production integrations combine patterns: a Platform Event or CDC subscriber receives a change notification in near-real-time but delegates heavy record processing to a queued Bulk API job or a scheduled batch. This decouples the event detection latency from the volume constraint.

---

## Common Patterns

### Pattern 1: Trigger-Based Sync for Low-Volume Transactional Records

**When to use:** Individual record creates/updates that require immediate confirmation from an external system (e.g., creating a payment authorization, validating an address, checking inventory for a single order line).

**How it works:**
1. An Apex trigger or process fires on record insert/update.
2. A `@future(callout=true)` method or a queueable with callout support issues an HTTP request to the external endpoint.
3. The response updates a status field on the Salesforce record in a follow-on DML.
4. Retry logic is handled by re-queuing or using a Platform Event to signal failure.

**Why not Platform Events here:** The caller needs a synchronous confirmation to decide whether to commit or surface an error to the user. Platform Events do not provide a reply.

**Limits to enforce:** Verify fewer than 100 callouts will fire per transaction. Use `@future` or Queueable to avoid the "callout after DML" error. Set a Named Credential — never hardcode endpoint URLs or credentials.

### Pattern 2: Event-Driven Near-Real-Time Sync via Platform Events

**When to use:** Volume is moderate (hundreds to low thousands of events per hour), latency must be under a few minutes, and the business does not require transactional rollback on the receiving side (e.g., broadcasting order status changes to a fulfillment system).

**How it works:**
1. A trigger or Flow publishes a Platform Event on record change.
2. An external subscriber (MuleSoft, custom app, AWS Lambda) listens on CometD or Pub/Sub API gRPC.
3. The subscriber processes and writes to the target system.
4. Replay IDs allow the subscriber to recover from downtime without data loss within the 72-hour window.

**Why not synchronous callouts:** External system downtime or latency spikes would block the Salesforce transaction and risk timeout errors at scale.

### Pattern 3: Bulk API 2.0 Scheduled Batch Sync

**When to use:** Volume exceeds 2,000 records per sync cycle, latency tolerance is hours (e.g., nightly ERP sync, daily customer master reconciliation), and eventual consistency is acceptable.

**How it works:**
1. External ETL tool or scheduled job queries Salesforce (SOQL query job via Bulk API 2.0) or receives a data extract.
2. Target system data is transformed and staged.
3. A Bulk API 2.0 ingest job upserts records using an external ID field.
4. Job status is polled; failed records are captured in the results CSV and re-queued for the next cycle.
5. Schedule jobs during off-peak hours to avoid resource contention with interactive users.

**Why not Platform Events for this volume:** At sustained thousands-per-second rates, Platform Events have throughput limits (standard: 250,000 events/day for most editions) and the event bus is not a reliable high-volume ETL channel.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| <100 records, immediate response needed, user-facing | Synchronous callout (Apex HTTP/SOAP) | Caller needs reply to commit or surface error; volume is within callout limits |
| Hundreds to low-thousands of events/hour, latency < 5 min, no rollback needed | Platform Events + external subscriber | Async, durable 72-hr replay, decouples systems |
| External system needs to react to Salesforce record changes automatically | Change Data Capture + Pub/Sub API | Platform-generated, field-level diff, 3-day replay, no custom publish code |
| >2,000 records per cycle, hours latency acceptable | Bulk API 2.0 scheduled job | Purpose-built for volume; callouts and Platform Events cannot handle this throughput reliably |
| High event volume + need for immediate detection but deferred processing | Hybrid: CDC/Platform Event triggers a queued batch | Decouples detection latency from processing volume |
| Bidirectional sync with conflict resolution | Middleware (MuleSoft) + Bulk API 2.0 or Platform Events | Salesforce-native patterns lack built-in conflict resolution; middleware handles transformation |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Establish volume and latency requirements**: ask the stakeholder for peak records-per-hour and the maximum acceptable delay from source change to destination visibility. These two axes determine the viable pattern set before any implementation begins.
2. **Confirm transactionality needs**: determine whether the integration must roll back Salesforce data if the external system rejects the payload. If yes, only a synchronous callout participates in the transaction; all async patterns are eventually consistent.
3. **Apply the decision table**: map volume + latency + transactionality to the correct Salesforce mechanism. Flag if volume exceeds callout limits (100/transaction) or Platform Event daily allocations (250,000 standard).
4. **Check governor limits for the chosen pattern**: for callouts verify the 120s timeout and 100/transaction limit; for Platform Events confirm daily event allocation; for Bulk API 2.0 confirm the 150M records/24hr limit and plan the off-peak schedule.
5. **Design the error and retry path**: synchronous callouts need try/catch + status field; Platform Event subscribers need a dead-letter queue or replay-ID restart strategy; Bulk API 2.0 jobs need results-CSV processing to re-queue failed rows.
6. **Validate with a load estimate**: calculate peak event or record rate against the chosen mechanism's limits; if headroom is under 30%, escalate to the next tier or add a hybrid buffer.
7. **Document the chosen pattern and rationale** in the integration design using the template in `templates/real-time-vs-batch-integration-template.md`, including replay window, retry approach, and failure notification path.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Volume and latency requirements are documented with numbers, not just words like "real-time"
- [ ] Chosen pattern is within governor limits at projected peak load (callout limits, event allocations, Bulk API daily cap)
- [ ] Transactionality decision is explicit: rollback-capable (synchronous) or eventually consistent (async)
- [ ] Error handling and retry path is defined for each integration leg
- [ ] Named Credentials are used for all outbound callouts (no hardcoded endpoints or credentials)
- [ ] Bulk API 2.0 jobs are scheduled outside peak business hours
- [ ] Platform Event or CDC replay window is sufficient for expected subscriber downtime scenarios

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Apex callout 120-second timeout is absolute** — there is no way to extend it. If the external system is slow or the payload is large, a synchronous callout will time out even at low volume. The fix is to move to a Queueable or @future callout that fires outside the user transaction, decoupling user-facing latency from external system performance.
2. **"Callout after DML" restriction** — if a trigger performs DML before the callout code runs, the callout is blocked with `System.CalloutException: You have uncommitted work pending`. This forces callouts to @future or Queueable, which means they cannot roll back the DML they follow.
3. **Platform Events do not roll back on transaction rollback by default** — as of Spring '25, `publishBehavior` defaults to `PUBLISH_IMMEDIATELY` for standard Platform Events; events already written to the bus are not retracted if the publishing transaction fails. Use `PHASE_AFTER_COMMIT` publish behavior when the event should only fire on successful commit.
4. **CDC 72-hour / 3-day replay window is a hard ceiling** — if a subscriber is down for longer than the replay window, events are gone. Design monitoring to alert if a subscriber has not polled within 48 hours so the window does not silently expire.
5. **Bulk API 2.0 has no cross-batch atomicity** — a job processing 500,000 records in multiple internal batches will commit each batch independently. If batch 3 of 10 fails, batches 1–2 are already committed and cannot be rolled back. Design idempotent upserts using external IDs so retries are safe.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration pattern recommendation | Written rationale mapping volume/latency/transactionality to the chosen Salesforce mechanism |
| Decision table | Populated version of the decision table in this skill with project-specific values |
| Governor limit validation | Calculations showing chosen pattern is within limits at projected peak |
| Error handling design | Retry approach, dead-letter strategy, and monitoring thresholds per integration leg |

---

## Related Skills

- integration/middleware-integration-patterns — use alongside when MuleSoft or an iPaaS layer is involved in the integration topology
- integration/api-led-connectivity-architecture — use when the integration is part of a broader API-led connectivity design
- integration/error-handling-in-integrations — use for designing retry, dead-letter, and alerting patterns for whichever mechanism is chosen
- apex/batch-apex-patterns — use when the batch processing logic itself is implemented in Apex Batch rather than Bulk API 2.0
