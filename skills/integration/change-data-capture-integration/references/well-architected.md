# Well-Architected Notes — Change Data Capture Integration

## Relevant Pillars

- **Reliability** — CDC is an event-driven integration whose reliability depends entirely on the subscriber correctly handling replay, reconnection, and gap events. A subscriber that loses its replay ID or ignores gap events will silently accumulate data drift. Reliability engineering for CDC means treating the subscriber like a stateful system with explicit durability requirements, not a simple webhook listener.

- **Integration** — CDC is one of three primary Salesforce integration patterns (alongside Platform Events and outbound messaging). Selecting CDC over alternatives is an architectural decision that should be made with full awareness of what CDC does and does not deliver: field-level deltas, delete/undelete signals, 72-hour retention, and the entity selection limit.

- **Scalability** — The event delivery allocation (shared across all CometD and Pub/Sub API clients) is a hard constraint. Integration designs that fan out to multiple direct Salesforce subscribers without accounting for this limit will hit the allocation ceiling. Scaling CDC to multiple consumers requires a bridging pattern (single authoritative subscriber → Kafka/middleware) or custom channels with server-side filtering.

- **Operational Excellence** — Subscribers that do not monitor delivery allocation usage, do not alert on subscriber disconnection, and do not test gap event recovery will fail silently in production. Observable CDC integrations instrument replay ID persistence, gap event frequency, and daily allocation consumption.

---

## Architectural Tradeoffs

| Tradeoff | CDC Advantage | CDC Constraint |
|---|---|---|
| vs. polling REST API | Explicit deltas, delete/undelete signals, no missed changes within retention | Requires persistent subscriber; 72-hour retention cap; entity selection limit |
| vs. Platform Events | Automatic event generation for every DML; no Apex publisher needed | Cannot publish custom business events; no control over payload schema |
| vs. Outbound Messaging | Richer event (multiple fields, changeType, changed fields); handles deletes | Outbound messaging is synchronous and simpler to implement for single-record workflows |
| Pub/Sub API vs CometD | `changedFields` delta available; gRPC more efficient at scale | CometD has wider existing middleware connector support |
| Default channel vs custom channel | Simpler setup | All subscribers share all entities; no server-side filtering; no event enrichment |

---

## Anti-Patterns

1. **Skipping replay ID persistence** — Treating CDC subscription as stateless (reconnecting with `-1` tip every time) means changes during outages are permanently lost. Every CDC subscriber must treat replay ID storage as a first-class reliability requirement equivalent to a database transaction log pointer.

2. **Using CDC as a fan-out bus by multiplying direct subscribers** — Adding a new CometD or Pub/Sub API subscriber for each consuming system multiplies event delivery allocation consumption proportionally. At scale, this exhausts the org's daily limit. Use a single bridge subscriber publishing to Kafka or enterprise middleware, letting those systems handle fan-out.

3. **Not implementing gap event recovery** — Gap events are not errors to be swallowed — they are Salesforce's signal that field-level data was lost in transit. Ignoring them produces silent divergence between Salesforce and the external system. Every CDC integration must have a documented and tested gap recovery path using REST API re-fetch.

---

## Official Sources Used

- Change Data Capture Developer Guide — CDC event structure, channel types, replay ID, gap events, entity selection, allocations
  URL: https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Pub/Sub API Developer Guide — gRPC subscription, FetchRequest, changedFields availability
  URL: https://developer.salesforce.com/docs/platform/pub-sub-api/guide/pub-sub-api-intro.html
- Integration Patterns — architecture pattern selection: CDC vs Platform Events vs outbound messaging
  URL: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — Reliability, Integration, and Scalability pillar framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
