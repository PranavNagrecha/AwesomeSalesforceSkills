# Well-Architected Notes — Platform Events Integration

## Relevant Pillars

- **Reliability** — At-least-once delivery combined with durable replay ID management is the primary reliability mechanism for external subscribers. An integration that does not persist replay state is unreliable by design: any restart drops events published during the outage. Dead-letter patterns address the gap when subscribers fall behind the retention window.

- **Scalability** — High-Volume Platform Events remove the 250k/hour publish cap. The Pub/Sub API credit model provides natural backpressure, allowing subscribers to scale consumption to their processing capacity without overwhelming downstream systems. Choosing the wrong event tier (standard vs high-volume) is an architectural scaling constraint that is costly to change post-launch.

- **Security** — External publish and subscribe connections must use OAuth 2.0 Connected App flows. JWT Bearer is the correct choice for server-to-server integrations; it avoids credential storage in the external system and supports IP restriction at the Connected App level. Event payloads should not carry PII or sensitive data beyond what the consumer genuinely needs — apply data minimization at the event schema design stage.

- **Operational Excellence** — Subscriber lag and publisher failure rates are the two essential operational metrics. Without visibility into these, a silent disconnect (CometD heartbeat failure) or a publish error (HTTP 429 or 503 from REST endpoint) goes undetected. Event Log Files in Salesforce and middleware-side metrics form the observability baseline.

- **Performance** — Pub/Sub API over gRPC delivers significantly higher throughput than CometD for high-volume subscribers. The REST publish endpoint is synchronous and subject to API rate limits; extremely high-frequency publishers should evaluate whether an intermediate queue (e.g., MuleSoft Anypoint, AWS EventBridge) absorbs spikes before publishing to Salesforce.

## Architectural Tradeoffs

**CometD vs Pub/Sub API:** CometD is more broadly supported in existing enterprise middleware and requires no gRPC stack. Pub/Sub API is faster, schema-native via Avro, and better suited to high-throughput scenarios. New integrations built after Summer '22 should default to Pub/Sub API unless the middleware stack does not support gRPC.

**Standard vs High-Volume Platform Event:** Standard events are simpler to set up and sufficient for < 250k events/hour with a 72-hour replay window. High-Volume events carry more configuration overhead but are the only option for extended retention via `RetainUntilDate`. Choosing standard and later needing high-volume is a breaking migration.

**REST Publish vs Apex Trigger Publish:** External systems publishing via REST have full control over event timing and payload construction but must manage OAuth tokens. Apex Trigger publishing tightly couples event emission to DML, which can be desirable (event is only published on successful record save) or undesirable (event payload is constrained by the triggering record's state).

**Durable vs Ephemeral Subscribers:** Durable subscribers persist replay ID state and tolerate outages up to the retention window. Ephemeral subscribers (replay `-1`) are simpler but drop events during any disconnection. Use durable subscriptions for all production integrations; document the explicit decision and impact if ephemeral is chosen.

## Anti-Patterns

1. **No replay ID persistence** — Subscribing with a hardcoded `-1` in a production integration treats every restart as "start from now," silently dropping events published during outages. At scale or with infrequent consumers (nightly batch jobs), this is a data loss guarantee, not a design choice.

2. **Using standard Platform Events when High-Volume limits apply** — Teams that hit 250k/hour caps or need extended retention encounter silent throttling or data loss instead of a clean scalability boundary. Selecting the event tier is an architectural decision that should happen before go-live, not in incident response.

3. **No idempotency on subscribers** — Designing a subscriber that assumes exactly-once delivery leads to duplicate transactions, double-sent notifications, or overcounted metrics when events are replayed. At-least-once is the platform's contract; the subscriber's contract must accommodate it.

4. **Embedding sensitive data in event payloads without need-to-know review** — Platform Event payloads are accessible to any subscriber connected to the channel with valid credentials. Including SSNs, full credit card numbers, or protected health information without a data classification review violates least-privilege access and creates compliance exposure.

## Official Sources Used

- Platform Events Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Pub/Sub API Developer Guide — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/pub-sub-api-intro.html
- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
