---
name: change-data-capture-integration
description: "Use this skill when setting up CDC to stream Salesforce record changes to external systems via CometD or Pub/Sub API. Covers change event channels, entity selection, event structure, replay ID management, gap events, and subscriber management. NOT for Apex CDC trigger subscribers (see apex/platform-events-apex). NOT for publishing custom business events (use integration/platform-events-integration)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
triggers:
  - how do I stream Salesforce record changes to an external system
  - set up CDC for external subscriber with replay ID
  - configure change data capture entity selection and channel subscription
  - Pub/Sub API change event subscription setup
  - external system not receiving CDC events after reconnect
tags:
  - change-data-capture
  - CDC
  - CometD
  - pub-sub-api
  - replay-id
  - external-subscription
  - event-streaming
  - middleware
inputs:
  - Target entity list (standard and custom objects to track)
  - External subscriber technology (MuleSoft, Kafka connector, custom CometD/gRPC client)
  - Replay strategy requirement (tip-only vs durable vs custom replay ID)
  - Edition and add-on license availability
outputs:
  - Entity selection configuration guidance
  - Channel subscription URL or Pub/Sub API topic path
  - Replay ID storage and recovery strategy
  - Gap event handling design
  - Subscriber management checklist
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Change Data Capture Integration

Use this skill when an external system needs to receive near-real-time Salesforce record changes without polling. CDC publishes structured change events to a durable event bus that external subscribers consume via Pub/Sub API (gRPC) or the CometD Streaming API. This skill covers the full lifecycle: entity selection, channel topology, event structure, replay, gap handling, and subscriber operations.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which objects need CDC?** Confirm whether they are standard objects (count toward the 5-entity default limit), custom objects, or both.
- **What subscriber technology is in use?** Pub/Sub API (gRPC) is the modern preferred path; CometD is the legacy path still supported for existing middleware.
- **What Edition is the org on?** Default event delivery allocations differ: 50,000/day (Performance/Unlimited), 25,000/day (Enterprise), 10,000/day (Developer Edition). The add-on removes entity limits and shifts delivery to a monthly 3M/month model.
- **Replay requirement:** Does the subscriber need durable replay (full 72-hour window) or tip-only? Is storing and recovering the replay ID in external state required?
- **Is Apex the subscriber?** If yes, stop — use `apex/platform-events-apex` instead. This skill covers external (non-Apex) subscribers only.

---

## Core Concepts

### Change Event Structure

Every CDC message wraps a `ChangeEventHeader` object alongside the record fields. Key header fields:

| Field | Type | Description |
|---|---|---|
| `entityName` | string | API name of the changed object (e.g., `Account`) |
| `changeType` | enum | `CREATE`, `UPDATE`, `DELETE`, `UNDELETE`, or `GAP_*` prefixed variants |
| `changedFields` | string[] | Fields changed in an UPDATE (Pub/Sub API only; not in CometD) |
| `nulledFields` | string[] | Fields explicitly set to null in an UPDATE (Pub/Sub API only) |
| `diffFields` | string[] | Fields that changed due to formula or roll-up recalculation (Pub/Sub API only) |
| `recordIds` | string[] | Record IDs affected; multiple IDs appear when gap events are merged |
| `transactionKey` | string | Unique transaction identifier; use to deduplicate or correlate events |
| `sequenceNumber` | int | Order of change within a transaction |
| `commitTimestamp` | long | Epoch milliseconds when the change committed |

`changedFields`, `nulledFields`, and `diffFields` are **not available in CometD clients** — they require Pub/Sub API or Apex triggers. This is a critical architectural difference.

### Enabling CDC and Entity Selection

CDC is enabled per object in **Setup > Integrations > Change Data Capture**. This page controls entity selections for the default `ChangeEvents` standard channel only. Custom channels are managed separately via `PlatformEventChannel` and `PlatformEventChannelMember` metadata types.

Default entity selection limit is **5 objects (standard + custom combined)** across all channels and all editions. If the same entity is selected in multiple channels, it counts once. Exceeding 5 requires purchasing the Change Data Capture add-on.

Custom channels are created with Metadata API (`PlatformEventChannel` type) or Tooling API and support up to 100 custom channels. Selections made in `PlatformEventChannelMember` for custom channels are NOT reflected in the Setup UI — query Tooling API to audit selections.

### Change Event Channels

Two channel types exist:

- **Default standard channel** — `/data/ChangeEvents` — delivers events for all entities selected via Setup UI. All subscribers on this channel see events for all selected objects.
- **Standard per-entity channels** — `/data/AccountChangeEvent`, `/data/Contact__ChangeEvent` — pre-built channels delivering events for one standard or custom object respectively. Custom objects use `<ObjectName>__ChangeEvent`.
- **Custom channels** — `/data/<ChannelName>__chn` — subscriber-isolated channels; each subscriber receives events only for entities assigned to that channel. Use custom channels when different downstream systems need different entity subsets, or when event enrichment (additional fields beyond changed fields) is required.

Custom channels support event enrichment: you can add fields to the change event payload that were not part of the originating DML change, allowing downstream systems to avoid follow-up queries.

### External Subscription Protocols

**Pub/Sub API (gRPC) — preferred for new integrations:**
- Subscribe by topic name, e.g., `/data/AccountChangeEvent`
- Supports `FetchRequest` with replay ID for durable subscription
- Returns `changedFields`, `nulledFields`, `diffFields` in the header — richer than CometD
- Available from API version 54.0+

**CometD (Streaming API) — legacy, still supported:**
- Subscribe via long-polling HTTP handshake on `/cometd/<version>`
- Use the EMP Connector (open-source Java library from Salesforce) or MuleSoft CDC connector
- Replay controlled via `{"replay": <replayId>}` in the subscription request
- Does NOT surface `changedFields`, `nulledFields`, or `diffFields` in the message body

### Replay IDs and Durable Subscription

Change events are retained for **72 hours** (3 days). Subscribers can replay events within this window using replay IDs:

| Replay ID Value | Meaning |
|---|---|
| `-1` | Tip — receive only events published after subscribing (no history) |
| `-2` | All retained — replay all events stored in the current 72-hour window |
| `<specific ID>` | Resume from a specific position; subscriber must persist this value after each batch |

Durable subscription requires the subscriber to persist the last successfully processed replay ID to external state (database, cache, or file). On reconnect, pass the stored replay ID to resume without gaps.

**Replay ID storage responsibility lies entirely with the subscriber.** Salesforce does not maintain per-subscriber cursors — if a subscriber reconnects without a stored replay ID, it can only start at tip (`-1`) or replay all retained events (`-2`).

### Gap Events

When Salesforce cannot generate a full change event (e.g., event exceeds the 1 MB maximum size, a bulk database operation bypasses the application server, or an internal error occurs), it sends a **gap event** instead.

Gap events have `changeType` values prefixed with `GAP_`: `GAP_CREATE`, `GAP_UPDATE`, `GAP_DELETE`, `GAP_UNDELETE`, `GAP_OVERFLOW`. They include the `recordIds` header field but contain **no changed field data**.

Gap event handling strategy:
1. Detect gap events by checking `changeType` for the `GAP_` prefix.
2. Mark affected records as dirty in the external system.
3. Issue a REST API query for the current record state using the `recordIds` from the gap event header.
4. Reconcile using `commitTimestamp` to ensure you are not overwriting a newer non-gap change event.

---

## Common Patterns

### Pattern 1: Single External Subscriber — Default Channel with Durable Replay

**When to use:** One middleware system (e.g., MuleSoft, Boomi) needs all CDC changes for a small set of objects.

**How it works:**
1. Enable the target objects in Setup > Integrations > Change Data Capture (max 5 entities without add-on).
2. Subscribe to `/data/ChangeEvents` or the per-entity channel `/data/AccountChangeEvent`.
3. Use replay ID `-2` on first connection to catch up, then switch to persisting the last processed replay ID.
4. Store the replay ID after each successful batch commit to external state.
5. On gap event, fetch current record via REST API using the record ID in the header.

**Why not just polling:** Polling via REST API misses field-level delta information and cannot detect deletes or undeletes. CDC provides explicit `changeType` and the exact set of changed fields.

### Pattern 2: Multiple Subscribers with Isolated Custom Channels

**When to use:** Two or more downstream systems need CDC but for different entity subsets, or with different event enrichment needs.

**How it works:**
1. Create a custom `PlatformEventChannel` per subscriber group via Metadata API.
2. Add `PlatformEventChannelMember` records for the relevant entities per channel.
3. Configure event enrichment on channel members where subscribers need additional fields beyond the changed ones.
4. Each subscriber connects to its specific channel path, e.g., `/data/ERP_Sync__chn`.
5. Each subscriber manages its own replay ID independently.

**Why not the default channel:** The default channel broadcasts all selected entities to all subscribers. Custom channels isolate event scope and reduce delivery allocation consumption by filtering server-side before delivery.

### Pattern 3: CDC → Kafka Bridge for Fan-Out

**When to use:** Multiple downstream consumers exist and Kafka is the enterprise event backbone.

**How it works:**
1. One dedicated integration layer (MuleSoft CDC connector, custom Pub/Sub API gRPC client, or Kafka Connect Salesforce connector) subscribes to Salesforce CDC via Pub/Sub API.
2. That layer publishes to Kafka topics mapped per entity (`account-changes`, `opportunity-changes`).
3. Kafka consumers subscribe independently; the CDC-to-Kafka bridge manages Salesforce replay ID in its own persistent store.
4. Kafka provides its own offset management and fan-out — Salesforce event delivery allocation is consumed only by the single bridge subscriber.

**Why not multiple Salesforce subscribers:** Each additional CometD or Pub/Sub API subscriber counts independently against the org's event delivery allocation. Centralizing to one bridge protects the allocation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One integration system needs all CDC changes | Default `/data/ChangeEvents` channel, CometD or Pub/Sub API | Simple; no custom channel overhead |
| Multiple systems need different entities | Custom channels per subscriber | Server-side filtering; preserves delivery allocation |
| Need `changedFields` delta in external system | Pub/Sub API (gRPC) | CometD does not surface `changedFields` |
| Existing MuleSoft or Boomi middleware | CometD via EMP Connector or platform connector | Established connector support; migration to Pub/Sub API optional |
| Tracking > 5 entity types | Purchase CDC add-on or evaluate if all entities truly need CDC | Default limit is 5; add-on removes the cap |
| Subscriber was offline > 72 hours | Full re-sync via Bulk API 2.0 then re-subscribe at tip | Events beyond retention window are permanently purged |
| Need enriched fields in event payload | Custom channel with event enrichment on PlatformEventChannelMember | Avoids follow-up REST queries per event |
| Kafka is the enterprise bus | Single Pub/Sub API bridge to Kafka | Preserves delivery allocation; Kafka provides fan-out |

---

## Recommended Workflow

1. **Confirm scope and limits** — Count the entities needed. Verify org Edition and whether the CDC add-on is licensed. Confirm subscriber technology (Pub/Sub API or CometD).
2. **Enable entities and configure channels** — For up to 5 entities, enable via Setup > Change Data Capture. For custom channels or more entities (with add-on), create `PlatformEventChannel` and `PlatformEventChannelMember` via Metadata API deployment.
3. **Design replay ID strategy** — Decide where the subscriber persists the last replay ID (external DB, Redis, config file). Decide initial replay behavior: `-2` for full catch-up or `-1` for tip-only.
4. **Implement subscriber** — For Pub/Sub API: implement a gRPC `Subscribe` call with `FetchRequest` carrying the stored replay ID. For CometD: configure the EMP Connector or middleware connector with the channel path and replay extension.
5. **Implement gap event handling** — Add conditional logic that detects `GAP_` prefixed `changeType` values, marks records dirty, and fetches current state from REST API using `recordIds`.
6. **Test replay and reconnection** — Validate reconnect behavior by stopping the subscriber, waiting, and replaying using the stored replay ID. Confirm the subscriber resumes from the correct position.
7. **Monitor delivery allocation usage** — Check Setup > Event Monitoring or REST API to track daily delivery usage against the org's allocation. Alert before the limit is reached.

---

## Review Checklist

- [ ] All target entities are enabled and the 5-entity limit (or add-on) is accounted for.
- [ ] Channel topology is confirmed: default channel vs per-entity channel vs custom channel.
- [ ] Subscriber uses Pub/Sub API (preferred) or has a documented reason for CometD.
- [ ] Replay ID is persisted to durable external state after each processed batch.
- [ ] Gap event handling is implemented and tested with a `GAP_CREATE` or `GAP_UPDATE` scenario.
- [ ] Initial replay strategy is documented (`-1` tip or `-2` full catch-up).
- [ ] Event delivery allocation usage is monitored with alerting before the daily cap.
- [ ] Subscriber reconnect behavior under the 72-hour window is tested.
- [ ] If multiple subscribers exist, evaluate custom channels to prevent shared delivery allocation exhaustion.

---

## Salesforce-Specific Gotchas

1. **`changedFields` is absent in CometD** — The `changedFields`, `nulledFields`, and `diffFields` header fields are only available via Pub/Sub API or Apex triggers. CometD delivers the full updated field set in the message body, not just deltas. Systems that build diff logic based on CometD payloads must compare against stored state, not rely on the header.

2. **Gap events contain no changed field data** — When a gap event fires, the subscriber only receives the `recordIds` and the gap `changeType`. There are no field values in the event body. Subscribers that ignore gap event detection and try to process them as normal change events will silently skip updates and accumulate data drift. Always check the `changeType` for the `GAP_` prefix before processing field values.

3. **Entity selections in custom channels are invisible in Setup UI** — The Change Data Capture Setup page only reflects selections on the default `ChangeEvents` channel. Entities in custom channels do not appear there. Practitioners who audit CDC coverage via Setup will undercount actual event volume. Use `SELECT QualifiedApiName FROM PlatformEventChannelMember` in Tooling API to get the full picture.

4. **Event delivery allocation is per-subscriber, cumulative** — Each subscribed CometD or Pub/Sub API client independently consumes from the org's daily delivery allocation. Two subscribers receiving the same 20,000-event stream consume 40,000 of the allocation. High fan-out subscriptions exhaust the default allocation quickly. Use custom channels with server-side filtering or a single bridge to Kafka/middleware to control consumption.

5. **72-hour retention is hard** — Events purged after the retention window cannot be replayed at any price. A subscriber that goes offline for more than 72 hours will have a gap that cannot be closed by replaying CDC events. Recovery requires a full Bulk API re-sync of the affected objects followed by re-subscribing at tip.

6. **Formula fields and roll-ups do not generate CDC events** — CDC captures explicit DML changes to stored field values. Formula field recalculations and roll-up summary field updates triggered by child record changes do not generate change events for the parent record. Systems that track formula field state via CDC will silently miss recalculations.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Entity selection list | Objects enabled for CDC and the channel they are on |
| Channel subscription path | CometD or Pub/Sub API topic path per subscriber |
| Replay ID storage design | Where and how the subscriber persists the last replay ID |
| Gap event handling logic | Code or flow logic for detecting and recovering from gap events |
| Delivery allocation monitoring plan | Setup dashboard or REST API query for daily usage tracking |

---

## Related Skills

- `apex/platform-events-apex` — Use when Apex triggers are the CDC subscriber, or when the integration publishes/consumes custom Platform Events.
- `integration/platform-events-integration` — Use for custom business events (not row-change CDC). Covers Pub/Sub API and CometD for Platform Events.
- `architect/platform-selection-guidance` — Use when deciding between CDC, Platform Events, and outbound messaging for an integration pattern.
- `data/external-data-and-big-objects` — Use when data volume considerations affect CDC strategy or when Bulk API is needed for re-sync after gap events.
