# Well-Architected Notes — Real-Time vs Batch Integration

## Relevant Pillars

- **Performance** — The primary pillar. Pattern selection directly determines whether the integration operates within governor limits at expected peak volume. A synchronous callout chosen for a high-volume use case will hit the 100/transaction limit and time out; a Bulk API 2.0 job scheduled during business hours will degrade due to resource contention. Every pattern recommendation must include a peak-load calculation.
- **Scalability** — Real-time patterns (synchronous callouts) do not scale horizontally — the 100/transaction and 120s timeout are hard walls. Async event-driven patterns (Platform Events, CDC) scale within daily allocation limits. Bulk API 2.0 is the purpose-built scalable path for record volume. Architectural decisions made early lock in the scalability ceiling for the integration.
- **Reliability** — Each pattern has a different failure mode: synchronous callouts fail fast and visibly; Platform Events can publish phantom events on transaction rollback; Bulk API 2.0 partial commits are silent. Reliability design must address the specific failure mode of the chosen pattern, not generic retry logic.
- **Operational Excellence** — Monitoring requirements differ by pattern. Synchronous callouts need timeout alerting; Platform Event subscribers need replay-window health checks; Bulk API 2.0 jobs need results-CSV processing and re-queue automation. These must be built before go-live, not retrofitted.
- **Security** — All outbound callouts must use Named Credentials. Bulk API 2.0 authentication uses OAuth 2.0 with least-privilege connected app scope. CDC and Pub/Sub API consumers must be granted only the event channel permissions they need, not full org access. Field-level security applies to CDC — only fields visible to the integration user appear in change events.

## Architectural Tradeoffs

**Latency vs Volume — the primary axis:** Synchronous callouts provide the lowest latency (subsecond when the external system responds quickly) but hard-cap at 100 records/transaction. Platform Events provide near-real-time async delivery but have daily allocation limits (250,000 standard events/day on most editions). Bulk API 2.0 handles unlimited volume but introduces hours of latency. These three operating points cannot be collapsed — a design that needs both sub-minute latency and millions of records per day requires a hybrid architecture.

**Transactionality vs Decoupling — the secondary axis:** Synchronous callouts allow the Salesforce transaction to roll back based on the external system's response. This provides strong consistency but tightly couples the Salesforce commit to external system availability. Every second of external system downtime becomes a Salesforce transaction failure visible to users. Async patterns (Platform Events, CDC, Bulk API) decouple availability but accept eventual consistency. This tradeoff must be resolved by the business, not assumed by the architect.

**Replay and Recovery:** Platform Events (72-hour replay) and CDC (3-day replay) provide built-in recovery for subscriber downtime within the window. Synchronous callouts have no replay — a failed callout requires application-level retry logic. Bulk API 2.0 jobs require explicit failed-results processing. The replay window must be longer than the longest expected subscriber outage; if it is not, a full reconciliation mechanism must exist.

## Anti-Patterns

1. **One callout per record in a trigger** — Placing `@future(callout=true)` inside a trigger that fires for every record insert/update creates a design that works in development (where data loads are small) and fails silently in production (where bulk operations exceed the 100/transaction callout limit or overwhelm the external API). The correct pattern is to aggregate change signals into Platform Events or to collect IDs for a single batch callout.

2. **Treating Platform Events as a high-volume ETL channel** — Platform Events are designed for event notification, not bulk data movement. Using them to transfer full record payloads at rates of tens of thousands per hour burns the daily event allocation, produces large event payloads that are hard to debug, and loses data if subscribers exceed the replay window. Use Bulk API 2.0 for data volume above 2,000 records per cycle.

3. **Assuming Bulk API 2.0 jobs are atomic** — Building integration logic that depends on a bulk job either fully succeeding or fully failing leads to data consistency bugs in production. Every Bulk API 2.0 job must be treated as partially committable, and the failed-results CSV must be processed and re-queued as a first-class part of the integration design, not an afterthought.

## Related Skills

Run `python3 scripts/skill_graph.py integration/real-time-vs-batch-integration` for the full graph. Key related skills:

- `integration/error-handling-in-integrations` — retry, dead-letter, and circuit-breaker patterns applicable to any chosen mechanism
- `integration/middleware-integration-patterns` — when a MuleSoft or iPaaS layer mediates between Salesforce and external systems
- `integration/api-led-connectivity-architecture` — broader API topology design that this pattern selection feeds into

## Official Sources Used

- Salesforce Integration Patterns (Architect Guide) — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Asynchronous Processing Decision Guide — https://architect.salesforce.com/docs/architect/fundamentals/guide/async-processing-decision.html
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Platform Events Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Pub/Sub API Developer Guide — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/pub-sub-api-intro.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Apex Governor Limits (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
