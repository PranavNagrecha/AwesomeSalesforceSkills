---
name: streaming-api-and-pushtopic
description: "Use when setting up real-time data streaming from Salesforce to external systems using the Streaming API (PushTopic, Generic Streaming), CometD client configuration, replay, and channel management. NOT for Platform Events (use platform-events-apex or platform-events-integration)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how to push Salesforce record changes to an external system in real time using PushTopic"
  - "external client is not receiving Salesforce streaming API events after a connection drop"
  - "how to configure CometD client to subscribe to a Salesforce channel with replay"
  - "setting up generic streaming API channel for custom payloads"
  - "missed events after reconnect on Streaming API subscription"
tags:
  - streaming-api
  - pushtopic
  - cometd
  - generic-streaming
  - replay
  - real-time-integration
inputs:
  - "Salesforce object and SOQL filter condition for the PushTopic (or channel name for Generic Streaming)"
  - "Authentication method used by the external CometD client (OAuth user-agent, username-password, JWT)"
  - "Replay ID requirement: -1 (all retained), -2 (new only), or a specific stored replay ID"
  - "Expected concurrent subscriber count per channel"
  - "API version to use (minimum 24.0 for PushTopic, 36.0 for Generic Streaming replay)"
outputs:
  - "PushTopic record definition with correct SOQL query and notification type flags"
  - "CometD handshake and subscription code sketch (Java EMP Connector or JavaScript bayeux)"
  - "Replay strategy recommendation with durable subscription configuration"
  - "Channel limit assessment and concurrency guidance"
  - "Troubleshooting checklist for missed events, connection drops, and authentication errors"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Streaming API and PushTopic

This skill activates when an external system needs to receive Salesforce record change notifications or arbitrary event payloads in real time, using the Streaming API over a CometD (Bayeux) connection. It covers PushTopic creation and SOQL constraints, Generic Streaming channels, replay ID handling for durable subscriptions, client configuration, and troubleshooting dropped connections or missed events.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Salesforce API version in use**: PushTopic requires API v24.0+. Generic Streaming channel replay requires v36.0+. The CometD client version must match or exceed the API version declared in the `/cometd/<version>` endpoint URL.
- **Authentication method**: The external client must authenticate first via OAuth (or username-password flow in sandboxes) and obtain a session token before connecting to CometD. Named Credentials cannot be used directly for inbound CometD; the client owns the session.
- **Concurrent client limits**: Each Streaming API channel supports a maximum of 1,000 concurrent clients per org (across all channels), and a maximum of 100 simultaneous clients per individual channel. Exceeding this causes `402::Unknown client` or handshake rejection.
- **PushTopic SOQL restrictions**: Not all SOQL is valid. Aggregate functions (COUNT, SUM, etc.), relationship traversal in the SELECT clause (e.g., `Account.Name` from Opportunity), LIMIT, OFFSET, and semi-joins are all prohibited. Only fields on the root object can appear in SELECT.
- **Event retention**: Streaming API retains events for 24 hours. If a subscriber is offline longer than that, events are permanently lost. For guaranteed delivery, consider Platform Events with a 72-hour window instead.

---

## Core Concepts

### PushTopic

A PushTopic is a Salesforce record (`PushTopic` sObject) that defines a SOQL query against a standard or custom object. Salesforce evaluates each DML operation against the query and fires a streaming notification if the record matches. The notification payload includes changed field values defined in the SELECT clause.

Key fields on the PushTopic record:

| Field | Meaning |
|---|---|
| `Name` | Channel name suffix. The full channel path is `/topic/<Name>`. |
| `Query` | The SOQL that defines what records trigger events. Must pass SOQL streaming restrictions. |
| `ApiVersion` | API version to use. Must be 24.0 or higher. |
| `NotifyForOperationCreate` | Fire when a record matching the query is created. |
| `NotifyForOperationUpdate` | Fire when a matching record is updated. |
| `NotifyForOperationDelete` | Fire when a matching record is deleted. |
| `NotifyForOperationUndelete` | Fire when a matching record is undeleted. |
| `NotifyForFields` | Which fields to include in the payload: `All`, `Referenced`, `Select`, or `Where`. |

`NotifyForFields = Referenced` is the safe default: it fires when any field used in the SOQL SELECT or WHERE changes. `All` fires on any field change, increasing noise. `Select` fires only when SELECT-listed fields change.

### Generic Streaming API

Generic Streaming is used when the event payload is arbitrary (not tied to a Salesforce object). A `StreamingChannel` record is created with a channel name in the form `/u/<ChannelName>`. External or Apex code publishes payloads using the `PushTopic` REST endpoint or via `Streaming.PushTopic` (deprecated). The recommended publisher is the Streaming Channel Push REST endpoint:

```
POST /services/data/v60.0/sobjects/StreamingChannel/<channelId>/push
Body: { "pushEvents": [{ "payload": "my payload", "userIds": [] }] }
```

An empty `userIds` array broadcasts to all subscribers. A non-empty array restricts delivery to those user IDs.

### CometD and the Handshake-Subscribe Flow

The Salesforce Streaming API implements the Bayeux protocol via CometD. The client must complete this sequence:

1. **POST** to `/cometd/<version>` with `handshake` message — obtains `clientId`.
2. **POST** with `connect` message — establishes the long-poll connection.
3. **POST** with `subscribe` message to `/topic/<PushTopicName>` or `/u/<ChannelName>`.
4. Re-issue `connect` immediately after each server response (long-poll loop).

The Salesforce-provided **EMP Connector** (Java, open source on GitHub) wraps this lifecycle and handles reconnection, replay, and subscription automatically. For JavaScript, the official `cometd` npm package or the Lightning `empApi` LWC wire adapter are the recommended clients.

### Replay ID and Durable Subscriptions

Every streaming event carries a monotonically increasing `replayId`. A client can pass a `replayId` value in the subscription `ext` object to replay events stored within the retention window:

```json
{
  "channel": "/topic/MyTopic",
  "ext": { "replay": { "/topic/MyTopic": -1 } }
}
```

Replay values:

| Value | Behavior |
|---|---|
| `-2` (default) | Receive only new events from this point forward. |
| `-1` | Replay all retained events (up to 24 hours). |
| `<replayId>` | Replay all events after (not including) that ID. |

Clients must persist the last-seen `replayId` to durable storage before processing each event. On reconnect they pass the stored ID. Storing the ID after processing risks duplicate processing if the process crashes between the two steps — weigh idempotency requirements.

---

## Common Patterns

### Mode 1: Creating a PushTopic and Subscribing via CometD

**When to use:** An external service needs to be notified whenever a Salesforce Opportunity is updated (e.g., Stage or Amount changes).

**How it works:**

1. Create the PushTopic via Apex or REST (one-time setup):

```apex
PushTopic pt = new PushTopic();
pt.Name = 'OpportunityUpdates';
pt.Query = 'SELECT Id, Name, StageName, Amount FROM Opportunity WHERE StageName != \'Closed Lost\'';
pt.ApiVersion = 60.0;
pt.NotifyForOperationCreate = true;
pt.NotifyForOperationUpdate = true;
pt.NotifyForOperationDelete = false;
pt.NotifyForOperationUndelete = false;
pt.NotifyForFields = 'Referenced';
insert pt;
```

2. External client authenticates via OAuth 2.0 and obtains `access_token` and `instance_url`.
3. Client connects to `<instance_url>/cometd/60.0` and performs handshake.
4. Client subscribes to `/topic/OpportunityUpdates` with a replay extension set to the last stored `replayId` (or `-2` on first run).
5. Client processes each incoming message and persists the `replayId` before acknowledging.

**Why not polling:** REST polling on Opportunity every N seconds burns API request quota and has latency proportional to the polling interval. Streaming delivers sub-second notifications with a persistent connection.

### Mode 2: Generic Streaming for Custom Payloads

**When to use:** A middleware system needs to push arbitrary JSON payloads to subscribed Salesforce users or external listeners — for example, triggering a UI refresh on a custom Lightning page.

**How it works:**

1. Create a `StreamingChannel` record:

```apex
StreamingChannel sc = new StreamingChannel();
sc.Name = '/u/WorkflowUpdates';
insert sc;
```

2. Grant permission: Users must have the "Streaming API" permission (included in most standard profiles).
3. Publisher pushes events via the Streaming Channel Push REST endpoint:

```
POST /services/data/v60.0/sobjects/StreamingChannel/<id>/push
Content-Type: application/json
{ "pushEvents": [{ "payload": "{\"status\":\"ready\"}", "userIds": [] }] }
```

4. Subscribers follow the same CometD handshake-subscribe flow, subscribing to `/u/WorkflowUpdates`.

### Mode 3: Troubleshooting Connection Drops and Missed Events

**When to use:** The external client was offline or disconnected and suspects events were missed.

**How it works:**

1. Check the last persisted `replayId` in client-side storage.
2. On reconnect, set the replay extension to that `replayId`. The server replays all events with a higher ID within the 24-hour retention window.
3. If no `replayId` was persisted, set replay to `-1` to receive all retained events (risk: replay storm if the backlog is large).
4. Verify the client is re-issuing `connect` immediately after every server response. A gap in the long-poll loop causes the server to expire the client session (`402::Unknown client`), requiring a full re-handshake.
5. Check for rate limit errors: `401::Authentication required` after a session token expires. The client must re-authenticate and reconnect, not just re-subscribe.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Record change notifications to an external system | PushTopic Streaming API | Direct object-change binding with SOQL filter; no Apex code needed for basic cases |
| Arbitrary payload broadcasting to subscribers | Generic Streaming (`StreamingChannel`) | Decoupled from sObject schema; publisher controls payload shape |
| Guaranteed delivery with >24 hour retention | Platform Events (use `platform-events-integration` skill) | Platform Events retain events 72 hours and support higher throughput allocations |
| Real-time UI updates inside Salesforce Lightning | LWC `empApi` wire adapter with Platform Events or PushTopic | Native Lightning integration without external CometD client |
| High-volume (>200k events/day) or append-only audit | Pub/Sub API (gRPC) or Platform Events | Streaming API PushTopic throughput is limited by org streaming allocations |
| Replay older than 24 hours | Not possible with Streaming API — switch to Platform Events | Streaming API event retention window is fixed at 24 hours |

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

Run through these before marking work in this area complete:

- [ ] PushTopic SOQL does not use aggregate functions, LIMIT, OFFSET, relationship fields in SELECT, or semi-joins.
- [ ] `ApiVersion` on the PushTopic is 24.0 or higher; CometD URL version matches.
- [ ] `NotifyForFields` is set deliberately (`Referenced` for most cases; `All` only if justified).
- [ ] CometD client persists `replayId` to durable storage before processing each event.
- [ ] Client re-issues `connect` immediately after each server response (long-poll loop is unbroken).
- [ ] Concurrent subscriber count per channel has been estimated and is below 100 per channel / 1,000 org-wide.
- [ ] Authentication token refresh is handled — CometD sessions expire when the session token expires.
- [ ] For Generic Streaming, the `StreamingChannel` record exists and users have the Streaming API permission.
- [ ] Event retention requirement has been confirmed to be within 24 hours; if not, Platform Events is the right choice.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **PushTopic SOQL bans aggregate functions and relationship traversal** — `SELECT COUNT(Id), Account.Name FROM Opportunity` is invalid for two separate reasons: COUNT() is an aggregate and `Account.Name` is a parent relationship field. Only root-object fields in the SELECT list are allowed. The insert of the PushTopic will fail with a SOQL validation error if violations exist.
2. **24-hour event retention — not 72** — Unlike Platform Events, Streaming API retains events for only 24 hours. If a subscriber is offline for more than 24 hours, those events are gone. This is a frequent surprise for teams that assume Streaming API and Platform Events behave identically.
3. **CometD client session expiry after Salesforce session timeout** — The CometD connection is bound to the OAuth session. When the session token expires (default 2 hours for connected apps without `refreshTokenIssuanceTime`), the server returns `401::Authentication required`. The client must re-authenticate (get a fresh token) and then perform a full CometD handshake before re-subscribing. Simply re-subscribing on the old `clientId` will fail.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| PushTopic record definition | Apex snippet or REST payload for creating the PushTopic with correct SOQL and flags |
| CometD subscription code sketch | Handshake-subscribe loop in Java (EMP Connector) or JavaScript (cometd npm) |
| Replay configuration | Subscription `ext` block with the right `replayId` value and persistence strategy |
| Channel limit assessment | Estimate of concurrent clients vs. per-channel and org-wide limits |
| Troubleshooting checklist | Ordered diagnostic steps for missed events, dropped connections, and auth failures |

---

## Related Skills

- `platform-events-apex` — Use when you need Apex-triggered event publishing, higher throughput, or 72-hour retention instead of 24-hour Streaming API retention.
- `platform-events-integration` — Use when an external system publishes or subscribes to Platform Events via CometD or Pub/Sub API with guaranteed delivery semantics.
- `named-credentials-setup` — Use when the external CometD client needs to make additional Salesforce REST callouts (separate from the streaming connection itself) and needs secure credential storage.
- `oauth-flows-and-connected-apps` — Use when configuring the OAuth Connected App that issues the access token the CometD client uses for authentication.
