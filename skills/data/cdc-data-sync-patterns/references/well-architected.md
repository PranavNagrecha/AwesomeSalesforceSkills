# Well-Architected Notes — CDC Data Sync Patterns

## Relevant Pillars

- **Reliability** — CDC replication reliability depends entirely on the subscriber correctly handling replay, gap events, and recovery scenarios. A subscriber that loses its `replayId` or ignores gap events introduces silent data drift that can be very difficult to detect and reconcile after the fact. The 72-hour retention window is the hard reliability boundary: any outage exceeding it requires a full re-sync, which is operationally expensive. Reliability design must include explicit retry logic, durable `replayId` persistence, gap event fallback, and an automated trigger for Bulk API re-sync when the retention window is exceeded.

- **Scalability** — CDC event volume scales with Salesforce transaction volume. High-velocity orgs (large batch loads, high-frequency automation) can generate thousands of events per second on busy channels. The replication pipeline must be designed to process events faster than they are produced, buffer during spikes, and handle back-pressure gracefully. Ordering and deduplication logic using `transactionKey` + `sequenceNumber` must scale horizontally if the pipeline is partitioned.

- **Performance** — Gap event fallback queries via REST API are synchronous and add latency to the replication pipeline. In orgs with frequent bulk operations, gap events can be common. Design the fallback path to batch multiple gap event record IDs into a single SOQL query where possible, rather than issuing one query per gap event. Also, avoid using SOQL `LIMIT 1` patterns that retrieve only partial state after a gap event.

- **Operational Excellence** — The replication lifecycle (day-0 load, incremental CDC, gap recovery, post-outage re-sync) must be observable and automatable. Instrument every stage: number of events processed, last persisted `replayId`, time since last successful commit, gap event rate, and re-sync trigger events. Alerting on a subscriber that has not committed a new `replayId` within a configurable threshold catches silent failures before the 72-hour window expires.

## Architectural Tradeoffs

**CDC streaming vs. scheduled batch polling:** CDC provides near-real-time delta capture with explicit `changeType`, `changedFields`, and record IDs. Batch polling via REST or Bulk API is simpler to implement but cannot detect deletes or undeletes without additional bookkeeping, and misses field-level change information. The tradeoff is operational complexity (CDC replication lifecycle management) vs. data fidelity (polling misses deletes and field-level deltas).

**ReplayId durability vs. processing simplicity:** Persisting the `replayId` after every batch adds a write operation to the hot path of the pipeline. Skipping it simplifies the hot path but makes recovery expensive (full re-sync or full 72-hour replay). The correct tradeoff for most production pipelines is to persist the `replayId` transactionally alongside the event data write — both succeed or both fail together.

**Gap event fallback cost vs. consistency:** Issuing a REST API query for every gap event adds latency and REST API request consumption. The alternative — ignoring gap events or processing them as empty updates — produces data drift that is difficult to detect and expensive to remediate. For correctness, the fallback is mandatory; optimize it by batching multiple record IDs into a single query when multiple gap events arrive in close succession.

## Anti-Patterns

1. **Treating replayId as ephemeral** — Storing the `replayId` only in memory or not storing it at all. This means every subscriber restart loses its position and must replay the full 72-hour window or accept a data gap. In high-velocity orgs, full 72-hour replay can take hours and creates enormous downstream processing load.

2. **Ignoring gap events** — Processing all CDC events through a single code path without checking for the `GAP_` prefix. Gap events carry no field data; processing them as normal change events silently writes corrupt data to the external datastore. This is the most dangerous anti-pattern because it produces no error, only wrong data.

3. **Using wall-clock time for event ordering** — Relying on the time the subscriber receives the event (network arrival time) or even the `commitTimestamp` alone for intra-transaction ordering. Multiple events within the same transaction share the same `commitTimestamp`. Correct ordering within a transaction requires `sequenceNumber` within the same `transactionKey`.

## Official Sources Used

- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Pub/Sub API Developer Guide — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/pub-sub-api-intro.html
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
