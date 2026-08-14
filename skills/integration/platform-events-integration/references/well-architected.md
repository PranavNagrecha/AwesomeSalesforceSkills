# Well-Architected Notes — Platform Events Integration

## Relevant Pillars

- **Reliability** — At-least-once delivery combined with durable replay ID management is the primary reliability mechanism for external subscribers. An integration that does not persist replay state is unreliable by design: any restart drops events published during the outage. Dead-letter patterns address the gap when subscribers fall behind the retention window.

- **Scalability** — The 250,000/hour figure is the **org-wide publishing allocation** for high-volume platform events on Enterprise, Performance, and Unlimited (50,000 on Developer), extendable only by purchasing add-on capacity in +25,000/hour increments. No event type escapes it, so a capacity plan must size against it directly rather than assuming a tier upgrade buys headroom. The Pub/Sub API credit model provides natural backpressure, allowing subscribers to scale consumption to their processing capacity without overwhelming downstream systems.

- **Security** — External publish and subscribe connections must use OAuth 2.0 Connected App flows. JWT Bearer is the correct choice for server-to-server integrations; it avoids credential storage in the external system and supports IP restriction at the Connected App level. Event payloads should not carry PII or sensitive data beyond what the consumer genuinely needs — apply data minimization at the event schema design stage.

- **Operational Excellence** — Subscriber lag and publisher failure rates are the two essential operational metrics. Without visibility into these, a silent disconnect (CometD heartbeat failure) or a publish error (HTTP 429 or 503 from REST endpoint) goes undetected. Event Log Files in Salesforce and middleware-side metrics form the observability baseline.

- **Performance** — Pub/Sub API over gRPC delivers significantly higher throughput than CometD for high-volume subscribers. The REST publish endpoint is synchronous and subject to API rate limits; extremely high-frequency publishers should evaluate whether an intermediate queue (e.g., MuleSoft Anypoint, AWS EventBridge) absorbs spikes before publishing to Salesforce.

## Architectural Tradeoffs

**CometD vs Pub/Sub API:** CometD is more broadly supported in existing enterprise middleware and requires no gRPC stack. Pub/Sub API is faster, schema-native via Avro, and better suited to high-throughput scenarios. CometD also carries more connection-liveness burden on the client: from Streaming API v64.0 the server can initiate a disconnect (auto-scaling, more often on Hyperforce), so the client owes a `/meta/disconnect` listener and a reconnect on top of the long-poll loop, whereas a dropped gRPC stream surfaces as an error the Pub/Sub client already handles. New integrations built after Summer '22 should default to Pub/Sub API unless the middleware stack does not support gRPC.

**Standard-Volume vs High-Volume Platform Event — no longer a live tradeoff:** You can no longer define a new standard-volume custom platform event; new platform events are high volume by default. Standard-volume events are a legacy population that Salesforce retires in **Summer '27**, so the only architectural decision left is migration sequencing for orgs that still have them. Two dates get confused here and both matter for planning: the retirement target *moved* — the Summer '25 (API 64.0) edition of the allocations page projected retirement in Summer '25, the current edition says Summer '27 — so an org that read the older doc may have budgeted a migration that is now two years early, and one that read a summary of it may believe its existing standard-volume events already stopped firing. They did not. The tiers differ in allocation (100,000 vs 250,000 publishes/hour on EE/Perf/Unlimited) and retention (24 vs 72 hours) — neither of which is configurable on either tier.

**REST Publish vs Apex Trigger Publish:** External systems publishing via REST have full control over event timing and payload construction but must manage OAuth tokens. Apex Trigger publishing tightly couples event emission to DML, which can be desirable (event is only published on successful record save) or undesirable (event payload is constrained by the triggering record's state).

**Durable vs Ephemeral Subscribers:** Durable subscribers persist replay ID state and tolerate outages up to the retention window. Ephemeral subscribers (replay `-1`) are simpler but drop events during any disconnection. Use durable subscriptions for all production integrations; document the explicit decision and impact if ephemeral is chosen.

## Anti-Patterns

1. **No replay ID persistence** — Subscribing with a hardcoded `-1` in a production integration treats every restart as "start from now," silently dropping events published during outages. At scale or with infrequent consumers (nightly batch jobs), this is a data loss guarantee, not a design choice.

2. **Treating retention as configurable** — Designing a replay window longer than 72 hours and expecting a per-event retention setting (commonly imagined as `RetainUntilDate`) to deliver it. No such field exists on any Platform Event, and publishing an unrecognized key succeeds without error, so the design validates in test and loses events in production. Longer windows require a durable ledger written alongside the publish.

3. **No idempotency on subscribers** — Designing a subscriber that assumes exactly-once delivery leads to duplicate transactions, double-sent notifications, or overcounted metrics when events are replayed. At-least-once is the platform's contract; the subscriber's contract must accommodate it.

4. **Embedding sensitive data in event payloads without need-to-know review** — Platform Event payloads are accessible to any subscriber connected to the channel with valid credentials. Including SSNs, full credit card numbers, or protected health information without a data classification review violates least-privilege access and creates compliance exposure.

## Official Sources Used

- Platform Events Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Platform Event Allocations — confirms verbatim "You can no longer define new standard-volume custom platform events. New platform events are high volume by default. Standard-volume custom platform events will be retired in Summer '27."; also the 250,000/hour (EE/Perf/Unlimited) and 50,000/hour (Developer) high-volume publish allocations, the 100,000/hour standard-volume allocation, and that the add-on "increases the hourly event publishing allocation by 25,000 events per hour" (a separate line raises the 24-hour *delivery* allocation by 100,000 — do not merge the two). Page header reads Summer '26 (API version 67.0). (verified 2026-08-13) — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
- Standard-Volume Platform Events Retirement — Salesforce Help retirement notice. The retirement release is cited from the Platform Event Allocations page above; this Help page is a client-rendered SPA and could not be re-verified. — https://help.salesforce.com/s/articleView?id=002280033&language=en_US&type=1
- Streaming API Client Connection — confirms "In Streaming API version 64.0 and later, the server can sometimes send a disconnect message to the client. The disconnects, which happen more frequently when using a Hyperforce instance, are due to infrastructure auto-scaling", and the required remedy "the client must add a listener for the /meta/disconnect channel and reconnect after receiving a disconnect message". Also the 40-second subscription expiry and the 110-second CometD reconnect window. (verified 2026-08-13) — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/using_streaming_api_client_connection.htm
- Streaming API Message Durability (replayId `-1` = default, new events only; `-2` = all retained events) — https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/using_streaming_api_durability.htm
- Pub/Sub API Developer Guide — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/pub-sub-api-intro.html
- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
