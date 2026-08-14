# LLM Anti-Patterns — Platform Events Integration

Common mistakes AI coding assistants make when generating or advising on Salesforce Platform Events for external integration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using CometD When Pub/Sub API Is Available

**What the LLM generates:** "Subscribe to Platform Events from your external application using the CometD Bayeux protocol" without mentioning that the Pub/Sub API (gRPC-based) is the modern replacement with better performance, bidirectional streaming, and event replay support.

**Why it happens:** CometD was the original external subscription mechanism and dominates training data. Pub/Sub API was introduced in Winter '22 and has less coverage.

**Correct pattern:**

```text
External subscription options:

Pub/Sub API (RECOMMENDED for new development):
- gRPC-based, bidirectional streaming
- Supports publish and subscribe from external systems
- Managed event replay with ReplayId
- Better throughput and lower latency than CometD
- Endpoint: api.pubsub.salesforce.com:7443

CometD / Streaming API (LEGACY):
- HTTP long-polling or WebSocket
- Subscribe only (cannot publish via CometD)
- Limited replay support (-1 = new events only; -2 = all retained events)
- Endpoint: /cometd/XX.0
- v64.0+: the SERVER can initiate a disconnect (infrastructure auto-scaling,
  more frequent on Hyperforce). The client must add a listener for the
  /meta/disconnect channel and reconnect after receiving one, resuming from
  the stored replayId. The long-poll loop alone does not cover this, and the
  reference client libraries do not do it for you.

Use Pub/Sub API for all new external Platform Event consumers.
CometD is acceptable for existing implementations or simple use cases.
```

**Detection hint:** Flag new integration designs that use CometD for Platform Event subscription without mentioning Pub/Sub API as the preferred alternative.

---

## Anti-Pattern 2: Not Handling Replay ID Gaps for Durable Subscribers

**What the LLM generates:** "Store the last ReplayId and use it to resume subscription" without handling the scenario where the stored ReplayId has expired (events are retained for 72 hours for high-volume events — every event definable today — and 24 hours for legacy standard-volume events).

**Why it happens:** Replay ID persistence is a standard pattern, but the edge case where the stored ID is older than the retention window (causing the subscription to fail) is not commonly covered.

**Correct pattern:**

```text
Replay ID strategy for durable external subscribers:

1. Store the latest ReplayId after processing each event
2. On reconnect, provide the stored ReplayId
3. Handle ReplayId expiration:
   - If the stored ReplayId is older than 72 hours, it has expired
   - The subscription will fail or miss events
   - Fall back to ReplayPreset.EARLIEST to get all retained events
     (CometD equivalent: replayId -2)
   - Or ReplayPreset.LATEST if old events are not needed (CometD: replayId -1)
   - ReplayPreset is a Pub/Sub API enum (LATEST / EARLIEST / CUSTOM); the
     numbers above are the CometD replay IDs, not values of the enum

4. Implement dead letter handling:
   - If the subscriber cannot process an event, store it for retry
   - Do not block the subscription for one failed event

Pub/Sub API replay:
  Subscribe with ManagedSubscription for automatic replay management
  OR use ReplayPreset.CUSTOM with a specific ReplayId
```

**Detection hint:** Flag external subscribers that store ReplayId without a fallback for expired IDs. Look for missing error handling when the stored ReplayId is older than the retention period.

---

## Anti-Pattern 3: Publishing Events via REST API Without Checking Daily Limits

**What the LLM generates:** "POST to /services/data/vXX.0/sobjects/My_Event__e/ to publish events from your external system" without noting the daily and hourly allocation limits for Platform Event publishing.

**Why it happens:** The REST API endpoint for publishing events is straightforward. LLMs focus on the API call mechanics without covering the allocation model.

**Correct pattern:**

```text
Platform Event publishing limits (external via REST API):

Standard Platform Events:
- Hourly allocation: varies by edition (check /services/data/vXX.0/limits/)
  Enterprise Edition: ~100,000 per hour (varies)
- Each REST POST to publish one event = 1 API call + 1 event allocation
- Batch publish via Composite API: up to 10 events per composite subrequest

High-Volume Platform Events:
- Hourly publishing allocation: 250,000/hour on Enterprise, Performance and
  Unlimited; 50,000/hour on Developer
- NO separate license is required — new platform events are high volume by
  default. The Platform Event Add-On License buys MORE allocation
  (+25,000 published/hour; separately +100,000 delivered per 24 hours),
  not access to the tier.
- Published via REST API or Pub/Sub API

Monitor usage:
  GET /services/data/vXX.0/limits/
  Look for: DailyStandardVolumePlatformEvents and HourlyPublishedPlatformEvents

Optimize:
- Batch multiple records into a single event payload if possible
- Use Pub/Sub API for high-throughput publishing (more efficient than REST)
```

**Detection hint:** Flag external Platform Event publishing designs that do not reference hourly or daily allocation limits. Check for missing `/limits/` monitoring.

---

## Anti-Pattern 4: Confusing Platform Events with Change Data Capture for External Sync

**What the LLM generates:** "Publish a Platform Event whenever an Account is updated to notify the external system" using a trigger-based approach, when Change Data Capture (CDC) already provides automatic event publishing for record changes.

**Why it happens:** LLMs default to custom solutions (trigger + Platform Event) when a native solution (CDC) exists. CDC is a separate feature that automatically generates events on record changes without custom code.

**Correct pattern:**

```text
Platform Events vs Change Data Capture for external sync:

Change Data Capture (CDC):
- Automatic events on record create/update/delete/undelete
- No trigger or code required — enable per object in Setup
- Event includes changed fields only (delta payload)
- Subscribe via Pub/Sub API or CometD on /data/ channel
- Best for: syncing record changes to external systems

Custom Platform Events:
- Custom-defined event schema
- Published explicitly via Apex, Flow, or REST API
- Best for: business events, workflow triggers, custom payloads
- Required when: you need custom data in the event beyond field changes

Do NOT build a trigger that publishes a Platform Event for every record
change when CDC already does this natively.
```

**Detection hint:** Flag trigger-based Platform Event publishing that mirrors record change notifications. Check whether CDC is enabled for the object before recommending custom event publishing.

---

## Anti-Pattern 5: Not Configuring Event Delivery in the Correct Order

**What the LLM generates:** External subscriber code that processes events without considering that Platform Events are delivered in publish order but may be delivered more than once (at-least-once delivery guarantee).

**Why it happens:** Training data often presents event processing as exactly-once. Salesforce Platform Events provide at-least-once delivery, meaning consumers must handle duplicate events.

**Correct pattern:**

```text
Platform Event delivery guarantees:

Standard-Volume Platform Events (legacy, pre-Spring '19):
- At-least-once delivery (duplicates are possible)
- Events are ordered by publish timestamp
- Events retained for 24 hours (for replay)

High-Volume Platform Events:
- At-least-once delivery
- Partition-level ordering (not global ordering)
- Events retained for 72 hours

Consumer design requirements:
1. Idempotent processing: handle the same event being delivered twice
2. Use EventUuid or a business key for deduplication
3. Do not rely on global ordering across partitions (HVPE)
4. Implement checkpoint/commit: update stored ReplayId AFTER
   successful processing, not before
5. Handle gaps: if events are missed, use earliest replay to catch up
```

**Detection hint:** Flag external subscriber implementations that do not handle duplicate events or implement idempotent processing. Look for missing deduplication logic.

---

## Anti-Pattern 6: Inventing a Per-Event Retention Field (`RetainUntilDate`)

**What the LLM generates:** Apex or REST that sets a retention field on a Platform Event to extend the replay window — most often `entry.RetainUntilDate = DateTime.now().addDays(8);` or a `"RetainUntilDate"` key in a REST publish body — accompanied by advice to "use a High-Volume event, which supports configurable retention."

**Why it happens:** The surrounding reasoning is correct and that is what makes this durable. The model correctly knows retention is 72 hours, correctly knows that is too short for a weekly reconciliation, and correctly knows high-volume events differ from standard-volume ones. It then closes the gap with the mechanism that would exist if the platform were designed the obvious way — a settable expiry — and names it in Salesforce's own house style (`RetainUntilDate` looks exactly like a real platform field). Adjacent products reinforce it: SQS, EventBridge, and Kafka all expose per-message or per-topic retention, so a retention knob is the strong prior for anything called an event bus.

**Correct version:** No Platform Event has a retention field. Retention is a fixed platform property — **72 hours** for high-volume events (which is every event definable since Spring '19) and **24 hours** for legacy standard-volume events — and no API accepts an override. For a replay window beyond 72 hours the supported design is a durable ledger: the publisher writes a copy of each payload to a Big Object or external queue in the same unit of work as `EventBus.publish`, keyed by a correlation ID, and a subscriber returning from a long outage backfills from that store before resuming live at its persisted `replayId`.

**Why it is dangerous rather than merely wrong:** Publishing an unrecognized field does not fail. `EventBus.publish` returns success, the REST call returns 201, integration tests pass, and the defect surfaces only when a subscriber that has been down for four days replays and receives three days of events. The subscriber sees a valid, shorter stream — there is no error, no gap marker, and no signal anywhere in the system that data is missing.

**Detection hint:** `grep -rniE 'retainuntil|retentiondate|expiresat' --include='*.cls' --include='*.json' --include='*.md' .` — on an `__e` object or a platform-event publish payload, any hit is either a no-op or a misleadingly-named custom field. Structurally: any design document that answers "what if the subscriber is down longer than 72 hours?" with a *setting* rather than with a *second durable write* has this bug. The skill's checker script (`scripts/check_platform_events_integration.py`, Check 2) flags these field names on `__e` metadata automatically.

---

## Anti-Pattern 7: Treating 250,000/hour as a Standard-Tier Ceiling That High-Volume Escapes

**What the LLM generates:** A comparison table with rows like `| Max events per hour | Standard: 250,000 | High-Volume: Unlimited |`, and routing advice of the form "switch to a High-Volume Platform Event once you exceed 250k/hour."

**Why it happens:** Classic relabelling — the number is real but attached to the wrong dimension. 250,000/hour is the **org-wide publishing allocation for high-volume events** on Enterprise, Performance, and Unlimited. The model, holding a genuine Salesforce figure and a genuine two-tier distinction, assumes the figure is what separates the tiers. "High-volume" as a name actively invites the reading that it is the unbounded option.

**Correct version:** The hourly publishing allocation is per org, not per tier: **250,000/hour** for high-volume events on Enterprise, Performance, and Unlimited; **50,000/hour** on Developer; add-on capacity is sold in **+25,000/hour** increments. Standard-volume (legacy) events have their own, *lower*, allocation of 100,000/hour on EE/Perf/Unlimited — so the tiers do differ, but in the opposite direction from the fabricated table, and neither tier is unlimited. Separately, event *delivery* to CometD/empApi subscribers is metered on a 24-hour basis and is a different allocation; do not merge the two into one row.

**Compounding error:** the tier choice is not live work. Salesforce: "You can no longer define new standard-volume custom platform events. New platform events are high volume by default. Standard-volume custom platform events will be retired in **Summer '27**." Advice framed as "pick standard or high-volume" is answering a question that no longer exists; the real question for an org holding legacy events is migration sequencing. Note the symmetric failure, produced by models trained on the Spring '25 / Summer '25 doc editions, which projected retirement in **Summer '25**: asserting that standard-volume events *have already been retired* and that the org's existing ones have stopped firing. The date moved out by two years. Both errors are wrong in opposite directions, and both are checkable against one sentence on the allocations page.

**Detection hint:** `grep -rn 'Unlimited (platform capacity)\|High-Volume.*[Uu]nlimited' <files>` — no platform event publishes without an allocation, so "unlimited" in a platform-event limits table is always wrong. More generally, flag any hourly platform-event figure written without an edition qualifier: the allocation differs across editions, so a correct citation cannot be a bare number.
