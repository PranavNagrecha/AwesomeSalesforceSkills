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
- Limited replay support (-1 for all retained, -2 for new only)
- Endpoint: /cometd/XX.0

Use Pub/Sub API for all new external Platform Event consumers.
CometD is acceptable for existing implementations or simple use cases.
```

**Detection hint:** Flag new integration designs that use CometD for Platform Event subscription without mentioning Pub/Sub API as the preferred alternative.

---

## Anti-Pattern 2: Not Handling Replay ID Gaps for Durable Subscribers

**What the LLM generates:** "Store the last ReplayId and use it to resume subscription" without handling the scenario where the stored ReplayId has expired (events are retained for 72 hours for standard events, 72 hours for high-volume events).

**Why it happens:** Replay ID persistence is a standard pattern, but the edge case where the stored ID is older than the retention window (causing the subscription to fail) is not commonly covered.

**Correct pattern:**

```text
Replay ID strategy for durable external subscribers:

1. Store the latest ReplayId after processing each event
2. On reconnect, provide the stored ReplayId
3. Handle ReplayId expiration:
   - If the stored ReplayId is older than 72 hours, it has expired
   - The subscription will fail or miss events
   - Fall back to ReplayPreset.EARLIEST (-1) to get all retained events
   - Or use ReplayPreset.LATEST (-2) if processing old events is not needed

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
- Higher throughput (millions per day)
- Requires separate licensing or entitlement
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

Standard Platform Events:
- At-least-once delivery (duplicates are possible)
- Events are ordered by publish timestamp
- Events retained for 72 hours (for replay)

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
