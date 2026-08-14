# Gotchas — Platform Events Integration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Event Retention Is Fixed — No Field or Setting Extends It

**What happens:** Teams design an integration that needs a replay window longer than 72 hours — for example, a weekend batch job that must replay Friday through Sunday events. They look for a per-event retention field to set at publish time, find advice describing one (`RetainUntilDate` is the name that circulates most), write it into the payload, and ship. Salesforce ignores the unknown field, events expire on the platform schedule, and the Sunday job replays only the last three days. The gap is silent: the subscriber receives a valid, shorter stream and has no signal that anything is missing.

**When it occurs:** Any integration whose worst-case replay need exceeds the platform window. Retention is a fixed platform property, not a publishable attribute: **72 hours for high-volume platform events, 24 hours for legacy standard-volume events.** No API — Apex `EventBus.publish`, REST, or Pub/Sub — accepts a retention override. There is no `RetainUntilDate` field on any Platform Event object.

**How to avoid:** Treat 72 hours as a hard ceiling and design past it explicitly. The supported pattern is a durable ledger: the publisher writes a copy of each event payload (Big Object, external queue, or custom object with an archival policy) in the same unit of work as the publish, and a subscriber returning from a long outage backfills from that ledger before resuming live subscription at its stored `replayId`. Second, since Spring '19 every newly defined event is high-volume, so "make it high-volume to get more retention" is not an available move — new events already are. Detection: grep the integration for a retention field name on an `__e` object; if one is present, it is doing nothing.

---

## Gotcha 2: CometD Connections Expire Silently Without Heartbeat

**What happens:** A middleware CometD subscriber connects successfully and starts receiving events. After a period of inactivity (no new events published on the channel), the server closes the connection after 40 seconds. The client does not receive an error — the subscription simply stops delivering events. The integration appears healthy from the publisher side but the subscriber is effectively dead.

**When it occurs:** Any CometD subscriber implementation that does not continuously send `/meta/connect` long-poll requests. This is common in home-grown or naively implemented CometD clients that treat the initial handshake as sufficient to keep the channel alive.

**How to avoid:** CometD clients must implement the full Bayeux long-poll loop: after a `/meta/connect` response arrives (with or without event data), immediately send another `/meta/connect`. Use the CometD reference client libraries (Java `org.cometd.client`, JavaScript `cometd`) rather than raw HTTP clients — they implement the heartbeat loop correctly, though not the server-initiated disconnect handling that Streaming API v64.0+ additionally requires (see Gotcha 6). Add a subscriber health check that alerts if no events are received within N minutes during a period when events are expected, to detect silent disconnections.

---

## Gotcha 3: At-Least-Once Delivery Guarantees Duplicates — Not Just Retries

**What happens:** Platform Events deliver at-least-once. Under normal conditions the event arrives once. Under retry conditions — network disconnection during ack, subscriber reconnect, or event replay from a stored ID that covers already-processed events — the same event is delivered again. Subscribers that treat delivery as exactly-once write duplicate records or trigger duplicate downstream operations.

**When it occurs:** Any subscriber that does not implement idempotent processing. Most commonly seen when processing financial transactions, creating records in an external system, or sending notifications where duplicates cause user harm.

**How to avoid:** Include a correlation or idempotency key field on every Platform Event definition (e.g., `CorrelationId__c` as a unique Text field). Subscribers check whether they have already processed the correlation ID before acting on the event payload. Store processed IDs in a keyed lookup table — Salesforce custom objects, an external database table, or a distributed cache — and expire entries after a window longer than the event retention period.

---

## Gotcha 4: Pub/Sub API Credit Model Stalls Subscribers Under Load

**What happens:** A Pub/Sub API subscriber sends an initial `FetchRequest` with `num_requested: 100`. It processes the first 100 events but does not issue a new `FetchRequest` with credits. The gRPC stream stays open but no further events are delivered. The subscriber appears to have "stopped receiving events" even though it is connected and events continue to be published.

**When it occurs:** Middleware or custom Pub/Sub API client code that treats the subscription as a push stream. The Pub/Sub API is a pull-with-credits model, not a true push model. Clients must explicitly request more events by sending new `FetchRequest` messages after processing each batch.

**How to avoid:** Implement a continuous request loop: after processing a batch, immediately issue a new `FetchRequest` for the next batch. The Salesforce-provided reference clients (Java, Python, Node) handle this internally. If building a custom client, model the credit loop explicitly and test it with artificially high message rates to confirm throughput does not degrade.

---

## Gotcha 5: Replay ID Storage Timing Determines Whether You Lose or Duplicate Events

**What happens:** A subscriber stores the `replayId` before processing the event payload. If the subscriber crashes mid-processing, on restart it resumes from the next event, silently skipping the event that was being processed. Conversely, if the subscriber stores the `replayId` after processing but the store itself fails, the same event is reprocessed on the next restart.

**When it occurs:** Any durable subscriber that does not carefully sequence replay ID persistence relative to processing acknowledgment. Both orderings have failure modes.

**How to avoid:** At-least-once is safer than at-most-once for most integration scenarios. Always store the `replayId` after successful processing rather than before. Accept that under failure conditions the same event may be reprocessed, and enforce idempotency (see Gotcha 3) to make reprocessing harmless. Document which failure mode the integration is designed to tolerate and test the reconnect scenario explicitly.

---

## Gotcha 6: The Server Can Disconnect You — CometD v64.0+ Needs a `/meta/disconnect` Listener

**What happens:** A CometD subscriber that correctly runs the Bayeux long-poll loop still stops delivering events after some hours. Nothing in the client looks wrong: the last `/meta/connect` returned normally, the process is alive, the channel is still "subscribed", and the publisher keeps publishing. What the client received and silently dropped was a message on `/meta/disconnect` it never registered a listener for. The usual misdiagnosis is replay ID handling or an exhausted event delivery allocation; both are innocent.

**When it occurs:** Streaming API **version 64.0 and later** — the version in the client's endpoint path (`/cometd/64.0`), not the org's release. Salesforce documents the behavior only for v64.0 and later, so a client still pinned to `/cometd/58.0` on the same Summer '26 org is outside the documented scope — but register the listener anyway; it costs nothing at any version, and the docs do not promise older endpoints are exempt. Salesforce: "In Streaming API version 64.0 and later, the server can sometimes send a disconnect message to the client. The disconnects, which happen more frequently when using a Hyperforce instance, are due to infrastructure auto-scaling." Pre-2025 guidance treated disconnects as client-initiated only, so most existing subscriber code wires up `/meta/handshake`, `/meta/connect` and `/meta/subscribe` and nothing else.

**How to avoid:** Salesforce is explicit about the remedy: "To reconnect, the client must add a listener for the `/meta/disconnect` channel and reconnect after receiving a disconnect message." Register that listener, and have it re-handshake, re-subscribe, and resume from the **stored `replayId`** — not `-1` — so events published during the gap are replayed rather than skipped (Gotcha 5). Do not assume the CometD library covers this: the reference clients implement the long-poll loop, not a reconnect-after-server-disconnect policy. Detection: `grep -rn 'meta/disconnect' <subscriber source>` — against a v64.0+ endpoint, zero hits is the bug. Pub/Sub API subscribers are not exposed to this; a terminated gRPC stream surfaces as an error the client already has to handle, which is one more reason to prefer it for new work.
