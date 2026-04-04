# Gotchas — Platform Events Integration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: RetainUntilDate Is Only Available on High-Volume Platform Events

**What happens:** Teams design an integration that needs event replay windows longer than 72 hours — for example, a weekend batch job that must replay Friday through Sunday events. They add `RetainUntilDate` to a standard Platform Event definition expecting it to extend retention. The field is silently ignored or unavailable, and events expire after 72 hours regardless.

**When it occurs:** Any integration that relies on replay windows beyond 72 hours using a standard (non-high-volume) Platform Event. The field `RetainUntilDate` only appears and functions on High-Volume Platform Events (`HighVolumeEventBus` channel).

**How to avoid:** Check the event's channel type before designing the retention strategy. If the replay window exceeds 72 hours, the event must be High-Volume from the start. Migrating from standard to High-Volume later requires creating a new event object, which is a breaking change for all existing publishers and subscribers.

---

## Gotcha 2: CometD Connections Expire Silently Without Heartbeat

**What happens:** A middleware CometD subscriber connects successfully and starts receiving events. After a period of inactivity (no new events published on the channel), the server closes the connection after 40 seconds. The client does not receive an error — the subscription simply stops delivering events. The integration appears healthy from the publisher side but the subscriber is effectively dead.

**When it occurs:** Any CometD subscriber implementation that does not continuously send `/meta/connect` long-poll requests. This is common in home-grown or naively implemented CometD clients that treat the initial handshake as sufficient to keep the channel alive.

**How to avoid:** CometD clients must implement the full Bayeux long-poll loop: after a `/meta/connect` response arrives (with or without event data), immediately send another `/meta/connect`. Use the CometD reference client libraries (Java `org.cometd.client`, JavaScript `cometd`) rather than raw HTTP clients — they implement the heartbeat loop correctly. Add a subscriber health check that alerts if no events are received within N minutes during a period when events are expected, to detect silent disconnections.

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
