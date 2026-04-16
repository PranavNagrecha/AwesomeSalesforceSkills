---
name: pub-sub-api-patterns
description: "Use this skill when building or debugging gRPC-based Pub/Sub API integrations for subscribing to or publishing Salesforce Platform Events, Change Data Capture events, or custom channels — including auth flow, flow control, event replay, Managed Subscriptions, and language client setup. Triggers on: Pub/Sub API gRPC subscription, subscribe to platform events via gRPC, event replay with Pub/Sub API, managed event subscription Salesforce, FetchRequest flow control. NOT for legacy PushTopic API (deprecated), not for legacy Streaming API via CometD or EMP Connector (use those for legacy integrations only), not for Flow-based platform event triggers (use flow/flow-trigger-patterns skill)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
tags:
  - pub-sub-api
  - grpc
  - platform-events
  - cdc
  - change-data-capture
  - event-replay
  - managed-subscriptions
  - streaming
  - subscriptions
inputs:
  - "Salesforce org with Pub/Sub API access enabled"
  - "OAuth access token and instance URL and tenant ID"
  - "Topic name (e.g., /event/MyPlatformEvent__e or /data/ChangeEvents)"
  - "Replay ID strategy (Earliest, Latest, or specific replay ID for resume)"
outputs:
  - "gRPC Subscribe or ManagedSubscribe stream consuming Salesforce events"
  - "Publish or PublishStream gRPC call publishing events to Salesforce"
  - "Managed Subscription configuration for server-side replay tracking"
  - "Auth token refresh strategy for long-running subscriptions"
triggers:
  - "subscribe to Salesforce Platform Events via gRPC"
  - "Pub/Sub API authentication tenantid header"
  - "event replay Pub/Sub API replay ID"
  - "Managed Subscription vs Subscribe Pub/Sub API"
  - "FetchRequest num_requested limit Pub/Sub API"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Pub/Sub API Patterns

This skill activates when a developer needs to integrate with Salesforce's gRPC-based Pub/Sub API for subscribing to or publishing Platform Events, Change Data Capture (CDC) events, or custom event channels. It covers authentication, flow control, event replay, Managed Subscriptions, and language client patterns. It does NOT cover legacy PushTopic, legacy Streaming API (CometD/EMP Connector), or Flow-based event triggering.

---

## Before Starting

Gather this context before working on anything in this domain:

- Pub/Sub API uses gRPC/HTTP2, not REST. Language clients must use the proto definition from the Salesforce Pub/Sub API GitHub repo. CometD or EMP Connector cannot be used with this API.
- Authentication requires three headers: `accesstoken`, `instanceurl`, and `tenantid`. The `tenantid` is the org's 18-character organization ID.
- The default session timeout is 2 hours. This does NOT drop active Subscribe streams, but DOES close idle PublishStream connections. Long-running subscriber clients must handle token refresh.

---

## Core Concepts

### gRPC RPC Methods

Pub/Sub API exposes these gRPC methods:

| Method | Description |
|---|---|
| `Subscribe` | Client-driven subscription — client sends FetchRequests to control event delivery rate |
| `ManagedSubscribe` | Server-side replay tracking — client subscribes by subscription name, server tracks replay ID |
| `Publish` | Unary publish of a single batch of events |
| `PublishStream` | Bidirectional streaming publish for high-throughput scenarios |

### Authentication Headers

All gRPC calls require three metadata headers:

```
accesstoken: <Salesforce OAuth access token>
instanceurl: <Salesforce org URL>
tenantid: <18-character Organization ID>
```

Access tokens are standard Salesforce OAuth tokens — no Data Cloud token exchange required (unlike Data Cloud Query API). JWT Bearer, Client Credentials, or User-Agent flows all work.

### Flow Control via FetchRequest

`Subscribe` uses client-driven flow control. The client sends a `FetchRequest` specifying the number of events it can process (`numRequested`). The server delivers at most `numRequested` events per request. After processing, the client sends another `FetchRequest` for the next batch. Maximum 100 events per FetchRequest.

This is a **per-request batch size**, not a rate limit or row count ceiling. Practitioners who interpret it as a "100 event limit" will break their pagination logic.

### Event Replay

Events are retained on the event bus for **3 days**. Replay options:

- **Earliest** — replay from the oldest retained event
- **Latest** — start from events published after subscription begins (no replay)
- **Custom replay ID** — resume from a specific event position (use the `replayId` field from prior events)

For consumer resilience, clients should persist the last successfully processed `replayId` to an external store and pass it on reconnect.

### Managed Subscriptions

Managed Subscriptions (Summer '24 Open Beta, verify GA status) offload replay ID tracking to the server. A `ManagedEventSubscription` metadata record stores the consumer's last acknowledged replay position. Org limit: 200 managed subscriptions.

On reconnect, the client subscribes using the subscription name — no replay ID management needed in client code. Useful for stateless consumer deployments.

### Publishing Events

`Publish` sends events in a single batch:
- Max 1 MB per individual event
- Recommended 3 MB per batch / hard limit 4 MB per batch
- Max 200 events per publish request

`PublishStream` is bidirectional streaming for sustained high-throughput publishing.

---

## Common Patterns

### Pattern 1: Subscribe to a Platform Event Topic

**When to use:** An external system needs to consume Salesforce Platform Events published by org processes.

**How it works (Python/grpc example):**

```python
import grpc
from pubsub_api_pb2 import FetchRequest, ReplayPreset
from pubsub_api_pb2_grpc import PubSubStub

# Build auth metadata
metadata = [
    ("accesstoken", access_token),
    ("instanceurl", instance_url),
    ("tenantid", org_id),
]

channel = grpc.secure_channel("api.pubsub.salesforce.com:7443", grpc.ssl_channel_credentials())
stub = PubSubStub(channel)

def fetch_requests():
    yield FetchRequest(
        topic_name="/event/MyPlatformEvent__e",
        replay_preset=ReplayPreset.LATEST,
        num_requested=100
    )
    # After processing events, yield another FetchRequest
    while True:
        # Process events, then request more
        yield FetchRequest(num_requested=100)

for event_batch in stub.Subscribe(fetch_requests(), metadata=metadata):
    for event in event_batch.events:
        # Process event, persist replayId
        process(event)
```

**Why not use CometD:** CometD/EMP Connector is the legacy path. Pub/Sub API gRPC is the current recommended path for new integrations, offering better throughput, flow control, and language client support.

### Pattern 2: Managed Subscription for Stateless Consumer

**When to use:** Deployed in containerized/serverless environment where local replay ID storage is impractical.

**How it works:**

1. Create a `ManagedEventSubscription` metadata record (via Metadata API or Setup) with a unique subscription name and target topic.
2. In client code, use `ManagedSubscribe` RPC with the subscription name instead of `Subscribe`.
3. Server tracks replay position per subscription name — no client-side replay ID management needed.
4. On restart, reconnect using the same subscription name and the server resumes from last acknowledged position.

**Why not use standard Subscribe:** For stateless deployments, local replay ID storage is a reliability liability. Managed Subscriptions eliminate this complexity.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New external subscriber for Platform Events | Subscribe with FetchRequest flow control | Current recommended path |
| Stateless/containerized consumer | ManagedSubscribe | Server-side replay tracking, no local state |
| High-throughput event publishing | PublishStream | Bidirectional streaming for sustained publish rate |
| Resume from known replay position | Custom replay ID in Subscribe | Specify exact replayId from persisted consumer state |
| Legacy CometD integration maintenance | Keep using CometD | Only migrate to gRPC for new integrations |
| Consumer needs events older than 3 days | Not possible | Event bus retains only 3 days |

---

## Recommended Workflow

1. Obtain the Pub/Sub API proto file from the Salesforce Pub/Sub API GitHub repository and generate language client stubs.
2. Set up OAuth token flow and capture `accesstoken`, `instanceurl`, and 18-character org ID for `tenantid`.
3. Implement token refresh logic — 2-hour session timeout does not drop Subscribe streams but will eventually expire. Implement pre-emptive token refresh.
4. For `Subscribe`: implement a FetchRequest generator that sends flow-controlled requests and persists `replayId` after each successfully processed batch.
5. For `ManagedSubscribe`: create the ManagedEventSubscription metadata record and subscribe by name.
6. For publishing: batch events up to 200 per request and max 4 MB per batch. Use `Publish` for sporadic publishing, `PublishStream` for sustained high throughput.
7. Test replay by stopping the consumer, publishing test events, then reconnecting with the last persisted replay ID.

---

## Review Checklist

- [ ] gRPC proto generated from official Salesforce Pub/Sub API repository
- [ ] Auth headers include `accesstoken`, `instanceurl`, and `tenantid` (18-char org ID)
- [ ] FetchRequest numRequested is ≤ 100 per request
- [ ] ReplayId persisted after each successfully processed batch
- [ ] Token refresh implemented for long-running subscriber
- [ ] Publish batches ≤ 200 events and ≤ 4 MB per batch
- [ ] Managed Subscription limit (200 per org) checked if using ManagedSubscribe
- [ ] Consumer handles 3-day event retention window in SLA design

---

## Salesforce-Specific Gotchas

1. **100 Events Per FetchRequest Is Not a Rate Limit** — The 100-event cap on a single FetchRequest is a per-request batch size for flow control. It is NOT a rate limit or throughput ceiling. Multiple FetchRequests can retrieve the full event stream. Miscommunicating this leads to incorrect capacity planning.

2. **tenantid Must Be 18-Character Org ID** — Using the 15-character org ID causes authentication failures. The `tenantid` header requires the 18-character format. Retrieve it from `SELECT Id FROM Organization` SOQL and ensure it's 18 chars.

3. **2-Hour Session Does Not Drop Active Streams** — The default 2-hour OAuth session timeout will eventually expire, but active `Subscribe` streams remain open until the session is explicitly invalidated or the connection drops. Implement pre-emptive token refresh before expiry rather than relying on error-driven refresh.

4. **Managed Subscriptions Org Limit Is 200** — There is a hard limit of 200 `ManagedEventSubscription` records per org. For large-scale deployments with many independent consumers, this limit requires architectural planning — not all consumers can use Managed Subscriptions.

5. **CometD Recommendation Is Now Legacy** — LLMs trained on older Salesforce documentation recommend CometD/EMP Connector as the primary streaming integration pattern. As of Summer '22, Pub/Sub API gRPC is the recommended path for new integrations. CometD remains supported for existing integrations but should not be used for new development.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| gRPC subscriber client | Language-specific subscriber using Subscribe or ManagedSubscribe RPC |
| Event publisher client | Publish or PublishStream implementation with batch size compliance |
| Managed Subscription config | ManagedEventSubscription metadata record definition |
| Replay ID persistence strategy | External store design for consumer-side replay position tracking |

---

## Related Skills

- change-data-capture-integration — for CDC-specific event structure and field-level change tracking
- platform-events-integration — for platform event design and Flow-based event handling
- real-time-vs-batch-integration — for deciding whether streaming events are the right integration pattern
