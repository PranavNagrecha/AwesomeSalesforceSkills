---
name: platform-events-integration
description: "Use when publishing Platform Events from external systems via REST API, subscribing to Platform Events from outside Salesforce via CometD or Pub/Sub API, designing replay ID strategy for durable external consumers, or handling high-volume event delivery guarantees. Trigger keywords: 'external publish platform event', 'CometD subscribe', 'Pub/Sub API', 'replay ID external', 'durable subscription', 'RetainUntilDate'. NOT for Apex-only event publishing or triggering (use platform-events-apex). NOT for Change Data Capture external subscription (use change-data-capture-integration)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
tags:
  - platform-events
  - cometd
  - pub-sub-api
  - replay-id
  - external-integration
  - high-volume-events
triggers:
  - "how do I publish a platform event from an external system or middleware"
  - "external subscriber not receiving platform events after reconnect, missed events"
  - "setting up CometD or Pub/Sub API to subscribe to Salesforce platform events from Java or Node"
  - "what replay ID should I use for a new external platform event subscriber"
  - "high-volume platform event vs standard platform event for integration throughput"
  - "dead letter or event backlog when external subscriber falls behind"
inputs:
  - "event name and whether it is standard or high-volume (HighVolumeEventBus)"
  - "direction: external publisher pushing into Salesforce, external subscriber reading from Salesforce, or both"
  - "consumer technology: Java, Node, Python, MuleSoft, or other middleware using CometD or gRPC Pub/Sub API"
  - "expected message volume and required replay window (up to 72 hours)"
  - "idempotency requirements on the subscriber side"
outputs:
  - "REST publish endpoint pattern and auth setup recommendation"
  - "CometD or Pub/Sub API subscription pattern with replay ID configuration"
  - "high-volume vs standard event guidance based on volume and behavior requirements"
  - "idempotency and dead-letter design recommendation"
  - "review checklist for external event integration reliability"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Platform Events Integration

Use this skill when the integration boundary crosses outside Salesforce: an external system publishes Platform Events into Salesforce via REST, or a middleware consumer subscribes to events using CometD or the newer Pub/Sub API. The skill covers the full external connection lifecycle — auth, replay ID strategy, high-volume vs standard limits, delivery guarantees, and what to do when subscribers fall behind.

---

## Before Starting

- Is the external system acting as a publisher (pushing events into Salesforce), a subscriber (reading events from Salesforce), or both?
- What event API will the subscriber use: the legacy Streaming API over CometD, or the newer Pub/Sub API over gRPC?
- What is the expected event volume per hour? This determines whether you need a High-Volume Platform Event or a standard one.
- Does the subscriber need to recover after downtime? If yes, a durable subscription with explicit replay ID management is mandatory.
- What is the event retention requirement? High-volume platform events are stored for **72 hours**; standard-volume (legacy, pre-Spring '19) events for **24 hours**. Neither window is extensible — there is no retention field to set. If you need a longer replay window, you must design an out-of-band durable ledger.

---

## Core Concepts

### Publishing From External Systems via REST

External systems publish Platform Events by POSTing to the Platform Event sObject REST endpoint:

```
POST /services/data/vXX.0/sobjects/OrderShipped__e/
Authorization: Bearer <access_token>
Content-Type: application/json

{ "OrderId__c": "801xx000001234", "ShippedDate__c": "2025-10-01T00:00:00Z" }
```

The response contains a `replayId` for the published event. Authentication uses standard OAuth 2.0 connected app flows — JWT bearer for server-to-server or User-Agent/Web Server for interactive flows. The REST endpoint imposes the same API governor limits as standard sObject REST calls.

### Subscribing From External Systems: CometD vs Pub/Sub API

Two external subscription protocols exist:

**CometD (Streaming API):** Bayeux-protocol long-polling over HTTPS. Mature, supported in many enterprise middleware stacks. Requires managing handshake, re-subscribe after network disconnect, and replay extension (`/meta/subscribe` with `replay` extension field). CometD subscribers must reconnect after 40 seconds of inactivity; failure to reconnect within the replay window causes event loss.

**Pub/Sub API:** gRPC-based binary API introduced in Summer '22. Supports higher throughput, server-side schema fetch via Apache Avro, and bidirectional streaming. Preferred for new integrations where the middleware stack supports gRPC. Salesforce publishes client libraries for Java, Python, and Node. Auth is the same OAuth 2.0 flow used by REST.

The Pub/Sub API endpoint is separate from the standard instance URL: `api.pubsub.salesforce.com:7443`.

### Replay ID: At-Least-Once Delivery and Durable Subscriptions

Platform Events deliver at-least-once. Every event has a `replayId`. External consumers must store the last successfully processed `replayId` durably (database, distributed cache) so they can resume from exactly where they left off after a disconnect or restart.

Three special replay ID values:
- `-1` — subscribe from the latest event (miss all events published before subscription)
- `-2` — subscribe from the earliest retained event (replay from the start of the retention window: 72 hours for high-volume events, 24 hours for standard-volume)
- Specific `replayId` — replay from a known position (requires that the event is still within the retention window)

If a consumer starts fresh with `-1` and fails during processing, events emitted during the outage are lost unless the consumer switches to `-2` or a stored position on restart. Design consumers to store replay position before acknowledging processing completion.

### High-Volume Platform Events vs Standard Platform Events

**This is not a live design choice for new work.** After Spring '19 you cannot define a new standard-volume platform event — every event you create in Setup is high-volume. Standard-volume events are a legacy population, and Salesforce is retiring publish and subscribe for them in **Winter '27**. If an org still has standard-volume events, the task is migration, not selection.

| Feature | Standard-Volume (legacy) | High-Volume (all new events) |
|---|---|---|
| Can be newly defined | No — not since Spring '19 | Yes (the only option) |
| Publish allocation per hour (org-wide) | 100,000 (EE / Perf / Unlimited); 1,000 (Dev, Prof w/ API add-on) | 250,000 (EE / Perf / Unlimited); 50,000 (Developer) |
| Event retention window | 24 hours | 72 hours |
| Retention configurable | No | No — 72 hours is fixed |
| Apex subscriber trigger | Supported | Supported |
| External CometD/Pub/Sub | Supported | Supported |
| Lifecycle | Retiring in Winter '27 | Current |

Two things this table exists to stop you assuming:

1. **The 250,000/hour figure is an org-wide publishing allocation, not a tier feature.** It is the ceiling for high-volume events on Enterprise, Performance, and Unlimited. It is not "unlimited above 250k" — moving to a high-volume event does not buy additional hourly headroom beyond that allocation. Capacity plans must size against 250,000/hour and buy the add-on (+25,000/hour) if they need more.
2. **Retention is fixed at 72 hours and cannot be extended by any field or setting.** For replay windows longer than 72 hours, the publisher must write a copy of each event to a durable store (Big Object, external queue) and the subscriber backfills from that store. See Pattern 3.

---

## Common Patterns

### Pattern 1 — External Publisher via REST with Idempotent Payload

**When to use:** An external order management or ERP system pushes domain events into Salesforce. The publisher controls event creation and timing.

**How it works:**
1. Configure a Connected App with OAuth 2.0 JWT Bearer flow for the external system.
2. Obtain an access token with the `api` scope (or the event-specific scope).
3. POST to `/services/data/vXX.0/sobjects/YourEvent__e/` with the event payload.
4. Include a stable idempotency key field on the event (e.g., `CorrelationId__c` as a Text field). Apex or Flow subscribers can deduplicate on this key.
5. Check the HTTP response for `success: true` and log the returned `replayId` if audit tracing is needed.

**Why not the alternative:** Polling a Salesforce query endpoint instead of publishing events couples the integration to Salesforce record shape and misses the decoupled event model.

### Pattern 2 — Durable External Subscriber via Pub/Sub API

**When to use:** A middleware platform must process Salesforce-published events reliably, including recovery after planned maintenance windows or unplanned outages.

**How it works:**
1. On first start, subscribe with `-2` (earliest) to catch any events already in the retention window, or with a stored `replayId` if one exists.
2. Fetch events in batches using the `FetchRequest` RPC. Pub/Sub API uses a request-credits model: send a `FetchRequest` with a `num_requested` count; the server streams responses until the credit is exhausted.
3. After processing each batch, persist the highest `replayId` to durable storage before acknowledging or processing the next batch.
4. On reconnect, always pass the last stored `replayId`. Never hardcode `-1` except for throw-away consumers.
5. Before replaying from an older stored `replayId`, use Pub/Sub API's `GetTopic` / `GetSchema` RPCs to confirm the schema version — a replayed event carries the schema ID that was current when it was published, which may predate the subscriber's cached schema.

**Why not the alternative:** CometD requires more client-side reconnect logic and is slower for high-throughput scenarios; Pub/Sub API handles backpressure natively through the credit model.

### Pattern 3 — Dead-Letter Handling When Subscribers Fall Behind

**When to use:** A subscriber has been offline longer than the retention window (72 hours for high-volume events, 24 for standard-volume). Because the window is fixed and cannot be extended, this pattern is mandatory — not optional — for any subscriber whose worst-case outage exceeds three days.

**How it works:**
1. Accept that events outside the retention window are permanently lost via normal replay.
2. Implement a compensating mechanism: the publisher writes the same payload to a durable store (e.g., a Salesforce Platform Cache partition, a BigObject, or an external message queue) when publishing the event.
3. On subscriber restart after a long outage, the subscriber reads from the durable store to backfill, then resumes live event subscription.
4. Alternatively, design the subscriber to tolerate gaps by requesting a full-state sync from Salesforce (REST or Bulk API query) before resuming event consumption.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| External system publishes business events into Salesforce | REST POST to `/sobjects/EventName__e/` with JWT auth | Standard REST endpoint, no special client library needed |
| New middleware subscriber, gRPC stack available | Pub/Sub API | Higher throughput, Avro schema fetch, better backpressure |
| Legacy middleware already using Bayeux/CometD | Streaming API CometD | Less migration effort; still fully supported |
| Sustained publish rate approaching 250k/hour | Buy the event add-on (+25,000/hour) and/or batch domain changes into fewer, coarser events | 250,000/hour is a hard org-wide allocation on EE/Perf/Unlimited; no event tier exceeds it |
| Org still has pre-Spring '19 standard-volume events | Migrate them to high-volume events now | Publish and subscribe for standard-volume events are retired in Winter '27 |
| Subscriber must recover after multi-day outage | Publisher writes a durable copy (Big Object / external queue) + subscriber backfills from it | The 72-hour window is fixed and cannot be extended by any setting; backfill is the only path |
| Subscriber processing is not idempotent | Add correlation ID field + consumer-side dedup table | At-least-once delivery means duplicates will arrive |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] External publisher authenticates with OAuth 2.0 connected app — no hard-coded credentials.
- [ ] Subscriber persists last processed `replayId` durably before marking batch complete.
- [ ] First-start replay strategy is documented: `-2` (earliest), stored ID, or intentional `-1` (no history).
- [ ] Peak publish rate is sized against the org-wide hourly allocation (250,000/hour on EE/Perf/Unlimited, 50,000 on Developer), with add-on capacity budgeted if the design approaches it.
- [ ] Idempotency: event payload includes a stable correlation or deduplication key.
- [ ] Dead-letter strategy defined for subscribers that may be offline beyond the retention window.
- [ ] Any requirement for a replay window longer than 72 hours is satisfied by a durable ledger, NOT by a retention setting — no such setting exists.
- [ ] No pre-Spring '19 standard-volume platform events remain in the integration path (Winter '27 retirement).
- [ ] Monitoring: publisher failures and subscriber lag are observable (event log files, middleware metrics).

---

## Salesforce-Specific Gotchas

1. **There is no retention-extension field on any Platform Event** — not `RetainUntilDate`, not anything else. Retention is a fixed platform property: 72 hours for high-volume events, 24 hours for legacy standard-volume events. Any design that assumes a publisher can push the expiry out will lose every event past the window, silently, with the subscriber seeing only a gap. Longer windows require a durable ledger written alongside the publish.
2. **CometD connections silently expire after 40 seconds of inactivity** — clients must send `/meta/connect` heartbeats continuously or the server closes the channel without error, leading to missed events that appear as gaps in the subscriber.
3. **Pub/Sub API uses a credit-based flow model** — if a client sends a `FetchRequest` and does not issue new credits after consuming the batch, the stream stalls. Middleware that expects a push model without managing credits will stop receiving events under load.
4. **At-least-once delivery means duplicates are guaranteed in retry scenarios** — every external subscriber must be idempotent; not designing for duplicates is the most common production reliability bug.
5. **Replay IDs are not sequential integers across all events** — they are opaque per-channel values. Do not subtract or compare replay IDs numerically to detect gaps; use the CometD or Pub/Sub API ordering guarantees instead.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| REST publish pattern | Endpoint URL, auth setup, and payload structure for external publishers |
| Subscriber design recommendation | CometD vs Pub/Sub API choice, replay ID storage design, and backpressure handling |
| Event tier recommendation | Standard vs High-Volume guidance based on throughput and retention requirements |
| Idempotency and dead-letter design | Correlation key field design and compensating backfill strategy |

---

## Related Skills

- `apex/platform-events-apex` — Use when Apex is the publisher or subscriber. Covers `EventBus.publish`, Apex trigger subscribers, and publish result handling.
- `integration/change-data-capture-integration` — Use when external systems must consume record-change events from Salesforce rather than custom domain events.
- `integration/streaming-api-and-pushtopic` — Use when the integration uses legacy PushTopic queries over CometD instead of Platform Events.
- `architect/platform-selection-guidance` — Use when the decision between Platform Events, CDC, and Outbound Messaging is still open.
