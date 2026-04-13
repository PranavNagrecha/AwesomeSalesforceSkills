---
name: cdc-data-sync-patterns
description: "Use this skill when designing or troubleshooting the replication lifecycle for CDC-based data synchronization: day-0 full load, incremental delta processing, replay ID management, gap event fallback, and ordering/deduplication using transactionKey and sequenceNumber. NOT for CDC admin setup (entity selection, channel configuration, edition limits — see integration/change-data-capture-integration). NOT for Apex CDC trigger subscribers."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - change-data-capture
  - CDC
  - replication
  - replay-id
  - gap-events
  - bulk-api
  - data-sync
  - incremental-load
  - transactionKey
  - sequenceNumber
triggers:
  - How do I implement incremental CDC replication without data drift
  - CDC subscriber went offline for 3 days — how to re-sync
  - Handling GAP_CREATE events in my CDC pipeline
inputs:
  - Target objects being replicated and their approximate record volume
  - External datastore type (data warehouse, database, data lake)
  - Acceptable replication lag (near-real-time vs batch tolerance)
  - "Current subscriber state: new deployment vs reconnect vs post-outage recovery"
  - Time the subscriber was offline (if recovering from an outage)
outputs:
  - Day-0 load strategy (Bulk API query job design)
  - Incremental CDC replication design with replay ID persistence plan
  - Gap event fallback query logic
  - Ordering and deduplication design using transactionKey and sequenceNumber
  - Offline recovery decision tree (replay vs full re-sync)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# CDC Data Sync Patterns

Use this skill when designing or debugging the data replication lifecycle for CDC-based synchronization pipelines. It covers the full replication lifecycle: initial day-0 full load via Bulk API, incremental delta processing via CDC events, durable replay ID management, gap event fallback queries, and correct event ordering using `transactionKey` and `sequenceNumber`. This skill is distinct from `integration/change-data-capture-integration`, which covers CDC admin setup and channel configuration.

## Trigger Scenarios

- How do I implement incremental CDC replication without data drift
- CDC subscriber went offline for 3 days — how to re-sync
- Handling GAP_CREATE events in my CDC pipeline
- What replayId value should I use when starting a new CDC replication job
- How to deduplicate CDC events when two transactions update the same record
- My CDC pipeline missed events during a restart — how do I recover without data loss

---

## Before Starting

Gather this context before working on anything in this domain:

- **Is the subscriber new or reconnecting?** New subscribers need a day-0 full load before switching to CDC. Reconnecting subscribers need to check whether their stored `replayId` is still within the 72-hour retention window.
- **How long was the subscriber offline?** If offline for more than 72 hours, replay is impossible — a full Bulk API re-sync is required. This is the single most important constraint in CDC replication design.
- **Where is the replay ID persisted?** Salesforce maintains no per-subscriber cursor. If the subscriber loses its `replayId`, the entire replay window may be unrecoverable. External durable storage (database, cache) is mandatory.
- **Are GAP events expected?** Bulk DML operations, large record sizes exceeding 1 MB, and internal Salesforce errors all generate gap events. Any CDC replication pipeline must handle them or risk silent data drift.

---

## Core Concepts

### CDC Event Retention and the 72-Hour Window

Salesforce retains Change Data Capture events for **72 hours** (3 days). Events outside this window are permanently purged and cannot be replayed at any price. The retention window is the central constraint around which all recovery strategies must be designed.

A subscriber that reconnects within 72 hours of going offline can replay missed events using its stored `replayId`. A subscriber that was offline for more than 72 hours has no CDC-based recovery path and must perform a full Bulk API re-sync of the affected objects before resuming CDC.

### ReplayId Values and Durable Subscription

The `replayId` controls where in the event stream a subscriber begins receiving events:

| ReplayId Value | Meaning |
|---|---|
| `-1` | Tip — receive only events published after subscribing (no catch-up) |
| `-2` | Full catch-up — replay all events retained in the 72-hour window |
| `<specific ID>` | Resume from a specific position; subscriber must persist this after each successful batch |

Choosing the right value depends on subscriber state:
- **New deployment (after day-0 load is complete):** Use `-1` to receive only new events going forward. The day-0 load already captured existing state.
- **Reconnect within 72 hours:** Use the last persisted `replayId` to resume without gaps.
- **Reconnect after 72+ hours:** Do not use `-2`. Events before the retention window are gone. Perform a full Bulk API re-sync, then subscribe at `-1`.

**Critical:** Salesforce maintains no per-subscriber cursor. The subscriber is solely responsible for persisting the `replayId` after each successfully processed event batch. Failure to persist it means the subscriber cannot resume from where it left off.

### Gap Events: Fallback is Mandatory

When Salesforce cannot generate a complete change event — because the record change was too large (>1 MB), originated from a bulk operation that bypassed the application server, or an internal error occurred — it emits a **gap event** instead.

Gap event `changeType` values: `GAP_CREATE`, `GAP_UPDATE`, `GAP_DELETE`, `GAP_UNDELETE`, `GAP_OVERFLOW`.

Gap events include the `ChangeEventHeader` with `recordIds` but **contain no field data** in the event body. A subscriber that processes a gap event as if it were a normal change event will see empty or null field values and silently write corrupted data to the external datastore.

Correct gap event handling:
1. Check `changeType` for the `GAP_` prefix before processing any event.
2. If a gap event is detected, extract the `recordIds` from `ChangeEventHeader`.
3. Issue a REST API SOQL query for the current full record state using those IDs.
4. Apply the queried record state to the external datastore.
5. Use `commitTimestamp` to guard against overwriting a newer non-gap event that has already been applied.

### Event Ordering: transactionKey and sequenceNumber

CDC events within a single transaction are delivered with the same `transactionKey` and incrementing `sequenceNumber` values. Across transactions, events are ordered by `commitTimestamp`.

Two scenarios where ordering matters:
- **Multiple changes to the same record in one transaction:** Use `sequenceNumber` to apply them in the correct order.
- **Events from concurrent transactions updating the same record:** Use `commitTimestamp` and `transactionKey` to detect and deduplicate out-of-order delivery. Do not use wall-clock time at the subscriber — use the commit timestamp from the event header.

Using event arrival time or subscriber processing time for ordering instead of `transactionKey` + `sequenceNumber` + `commitTimestamp` is a common source of data corruption in CDC replication pipelines.

---

## Common Patterns

### Pattern 1: Day-0 Full Load then Switch to CDC

**When to use:** Bootstrapping a new CDC replication pipeline for objects that already have existing records. CDC only publishes events for changes that occur after the subscription is set up — it does not backfill existing records.

**How it works:**
1. Record the current `replayId` at the tip of the event stream before running the Bulk API load (use Pub/Sub API `GetTopic` to retrieve the latest `replayId`).
2. Run a Bulk API 2.0 query job to extract all existing records from the target object.
3. Load those records into the external datastore.
4. Subscribe to the CDC topic using the `replayId` recorded in step 1. This ensures no events published during the Bulk API load are missed.
5. Process incoming CDC events to apply incremental deltas.

**Why not CDC alone from the start:** CDC does not replay events older than 72 hours and has no mechanism to publish events for records that existed before the subscription started.

### Pattern 2: Reconnect Within 72 Hours Using Persisted ReplayId

**When to use:** A subscriber restarts or reconnects after a brief outage (less than 72 hours) and needs to catch up without data loss.

**How it works:**
1. On shutdown, ensure the last successfully processed `replayId` is written to durable external storage (database row, Redis key, etc.).
2. On reconnect, read the stored `replayId` from external storage.
3. Subscribe to the CDC topic using that specific `replayId`.
4. Process all events from that position forward before switching back to normal streaming.

**Why not `-2` on reconnect:** Using `-2` replays the full 72-hour window, which can produce millions of events for active orgs. Using the stored specific `replayId` resumes from exactly where processing stopped.

### Pattern 3: Post-72-Hour Outage Recovery via Full Bulk API Re-sync

**When to use:** A subscriber has been offline for more than 72 hours (e.g., infrastructure failure, planned maintenance that ran long). The stored `replayId` now points to events that are outside the retention window and cannot be replayed.

**How it works:**
1. Detect that the stored `replayId` is stale (the Pub/Sub API returns an error indicating the replay ID is outside the retention window).
2. Perform a full Bulk API 2.0 query job on each affected object to extract current record state.
3. Upsert those records into the external datastore (using an external ID or record ID as the upsert key).
4. Subscribe to the CDC topic at `-1` (tip) to resume receiving new changes going forward.
5. Store the new `replayId` from the first event received to re-establish a durable position.

**Why not partial replay:** There is no partial replay for events beyond the retention window. The only authoritative source of current record state after 72+ hours offline is a fresh Bulk API extract.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Brand-new CDC pipeline, existing records | Day-0 Bulk API load, then subscribe at recorded tip replayId | CDC does not backfill pre-existing records |
| Subscriber reconnects < 72 hours after outage | Resume with persisted replayId | Efficient; replays only missed events |
| Subscriber reconnects > 72 hours after outage | Full Bulk API re-sync, then subscribe at -1 | Retention window expired; replay impossible |
| First-ever connection, no historical data needed | Subscribe at -1 (tip) | No catch-up required |
| First-ever connection, want all retained events | Subscribe at -2 | Gets up to 72 hours of history |
| changeType has GAP_ prefix | Extract recordIds from header, query REST API | Gap events have no field data |
| Multiple events for same record in one transaction | Order by sequenceNumber within same transactionKey | Correct application order |
| Deduplicating events across retries or reconnects | Use transactionKey + sequenceNumber as idempotency key | Unique per change within a transaction |

---

## Recommended Workflow

1. **Determine subscriber state** — Is this a new deployment, a reconnect after a short outage, or a reconnect after a long outage (>72 hours)? The answer determines whether to run a Bulk API load, resume from a stored `replayId`, or trigger a full re-sync.
2. **Run day-0 load if required** — For new pipelines: record the current tip `replayId`, execute a Bulk API 2.0 query job, load results to the external datastore, then subscribe at the recorded `replayId` to catch any events published during the load.
3. **Implement replay ID persistence** — After each successfully processed batch of events, write the last `replayId` to durable external storage. Never rely on in-memory state alone. Include a write-confirm step before acknowledging event processing.
4. **Implement gap event detection and fallback** — Before processing any event fields, check `changeType` for the `GAP_` prefix. On detection: extract `recordIds` from `ChangeEventHeader`, query REST API for current field values, apply those values using `commitTimestamp` as a guard against stale overwrites.
5. **Implement ordering and deduplication** — Within a transaction (`transactionKey`), apply events in ascending `sequenceNumber` order. Across transactions, use `commitTimestamp` for sequencing. Use `transactionKey` + `sequenceNumber` as an idempotency key to safely handle event redelivery.
6. **Test recovery scenarios** — Explicitly test: subscriber restart within 72 hours (should resume from stored replayId), subscriber restart after simulated 72-hour gap (should trigger Bulk API re-sync), and gap event injection (should trigger REST fallback query).

---

## Review Checklist

- [ ] Day-0 full load via Bulk API is implemented for new pipelines (CDC does not backfill pre-existing records).
- [ ] Tip `replayId` is recorded before the Bulk API load starts to avoid missing events published during the load.
- [ ] `replayId` is persisted to durable external storage after every successfully processed event batch.
- [ ] Reconnection logic reads the stored `replayId` and passes it to the subscription call on restart.
- [ ] `>72-hour outage` scenario triggers a full Bulk API re-sync rather than attempting to replay expired events.
- [ ] All events are checked for `GAP_` prefix in `changeType` before any field processing occurs.
- [ ] Gap event handling issues a REST API query using `recordIds` from `ChangeEventHeader`.
- [ ] Events within a transaction are applied in `sequenceNumber` order.
- [ ] `transactionKey` + `sequenceNumber` is used as an idempotency key to handle event redelivery.

---

## Salesforce-Specific Gotchas

1. **72-hour retention is absolute and non-negotiable** — Events purged after the retention window are permanently gone. There is no support case, add-on, or org setting that can extend the window or recover purged events. Design recovery procedures to assume this constraint.

2. **Gap events carry no field data — only recordIds** — A `GAP_UPDATE` event has the same `changeType` field as any other change event, but the event body contains no field values. Subscribers that do not check for the `GAP_` prefix before processing field data will write empty or null values to the external datastore silently.

3. **Salesforce has no per-subscriber cursor** — Salesforce does not track where any individual subscriber is in the event stream. The subscriber must persist the `replayId` externally. Losing the `replayId` means the subscriber can only start at tip (`-1`) or replay the full retained window (`-2`) — both of which may cause data gaps or excessive event volume.

4. **transactionKey + sequenceNumber, not timestamp, for ordering** — `commitTimestamp` is accurate at the transaction level but multiple events within a single transaction share the same timestamp. Using timestamp alone to order intra-transaction events produces non-deterministic results. Always use `sequenceNumber` within a shared `transactionKey`.

5. **Stale replayId gives an error, not silent behavior** — If the subscriber provides a `replayId` that is outside the retention window, the Pub/Sub API returns an error rather than silently falling back to tip. Reconnection logic must handle this error explicitly and trigger the Bulk API re-sync path.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Day-0 load design | Bulk API 2.0 query job configuration and timing relative to first CDC subscription |
| ReplayId persistence design | Storage location, write timing, and recovery read procedure |
| Gap event handling logic | Detection check and REST API fallback query design for GAP_* events |
| Ordering/deduplication design | transactionKey + sequenceNumber usage for correct event application order |
| Recovery decision tree | Flowchart: reconnect < 72h → resume; reconnect > 72h → full re-sync |

---

## Related Skills

- `integration/change-data-capture-integration` — Use for CDC admin setup: entity selection, channel configuration, edition limits, event delivery allocation, and subscriber technology (Pub/Sub API vs CometD). This is the admin counterpart to this replication-lifecycle skill.
- `apex/change-data-capture-apex` — Use when the CDC subscriber is an Apex trigger rather than an external system.
- `data/data-reconciliation-patterns` — Use when designing scheduled reconciliation as a complement to or safety net for CDC-based replication.
- `integration/bulk-api-data-operations` — Use for Bulk API 2.0 job design when running the day-0 full load or post-outage re-sync.

## Official Sources Used

- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Pub/Sub API Developer Guide — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/pub-sub-api-intro.html
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
