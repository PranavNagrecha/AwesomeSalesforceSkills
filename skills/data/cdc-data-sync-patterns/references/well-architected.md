# Well-Architected Notes — CDC Data Sync Patterns

## Relevant Pillars

- **Reliability** — CDC replication reliability depends entirely on the subscriber correctly handling replay, gap events, and recovery scenarios. A subscriber that loses its `replayId` or ignores gap events introduces silent data drift that can be very difficult to detect and reconcile after the fact. Three days of retention is the boundary you can rely on: an outage longer than that requires a full re-sync. Reliability design includes durable replay ID storage (or `ManagedSubscribe`), gap and overflow paths, transaction-level commits, and an automatic re-sync trigger based on the last processed `commitTimestamp`.

- **Scalability** — CDC event volume scales with Salesforce transaction volume. High-velocity orgs (large batch loads, high-frequency automation) can generate thousands of events per second on busy channels. The replication pipeline must be designed to process events faster than they are produced, buffer during spikes, and handle back-pressure gracefully. Ordering and deduplication logic using `transactionKey` + `sequenceNumber` must scale horizontally if the pipeline is partitioned.

- **Performance** — Gap reconciliation calls are synchronous and add latency. Batch the record IDs from several gap events into one query where possible, and run reconciliation off the main event loop so the stream keeps moving while dirty records wait.

- **Operational Excellence** — The replication lifecycle (day-0 load, incremental CDC, gap recovery, post-outage re-sync) must be observable and automatable. Instrument every stage: number of events processed, last persisted `replayId`, time since last successful commit, gap event rate, and re-sync trigger events. Alerting on a subscriber that has not committed a new replay ID within a configurable threshold catches silent failures well before the 3-day retention runs out.

## Architectural Tradeoffs

**CDC streaming vs. scheduled batch polling:** CDC provides near-real-time delta capture with explicit `changeType`, `changedFields`, and record IDs. Batch polling via REST or Bulk API is simpler to implement but cannot detect deletes or undeletes without additional bookkeeping, and misses field-level change information. The tradeoff is operational complexity (CDC replication lifecycle management) vs. data fidelity (polling misses deletes and field-level deltas).

**ReplayId durability vs. processing simplicity:** Persisting the `replayId` after every batch adds a write operation to the hot path of the pipeline. Skipping it simplifies the hot path but makes recovery expensive (full re-sync or a replay of everything retained). The correct tradeoff for most production pipelines is to persist the `replayId` transactionally alongside the event data write — both succeed or both fail together.

**Gap event fallback cost vs. consistency:** Issuing a REST API query for every gap event adds latency and REST API request consumption. The alternative — ignoring gap events or processing them as empty updates — produces data drift that is difficult to detect and expensive to remediate. For correctness, the fallback is mandatory; optimize it by batching multiple record IDs into a single query when multiple gap events arrive in close succession.

## Anti-Patterns

1. **Treating the replay ID as ephemeral** — Keeping it only in memory means every restart either replays everything retained (`EARLIEST`) or accepts a gap (`LATEST`). The Streaming API guide warns that replaying everything when many events are stored can slow performance.

2. **Ignoring gap events** — Processing all CDC events through a single code path without checking for the `GAP_` prefix. Gap events carry no field data; processing them as normal change events silently writes corrupt data to the external datastore. This is the most dangerous anti-pattern because it produces no error, only wrong data.

3. **Using arrival time for event ordering** — Applying events in the order the subscriber receives them, one by one. The CDC guide's approach is to buffer by `transactionKey`, order by `sequenceNumber` within the transaction, and commit the transaction as a unit.

## Official Sources Used

Read for this revision (2026-10-19):

- Change Data Capture Developer Guide (API 67.0, fetched from https://developer.salesforce.com/docs/get_document_content/change_data_capture/<page>.htm/en-us/262.0; pages cdc_other_events_gap, cdc_other_events_overflow, cdc_replication_steps, cdc_event_fields_header): gap event causes (1 MB, field type conversions, internal errors, database-level changes) and the four GAP_ types; GAP_OVERFLOW after 100,000 changes, one per entity, dummy record ID, field changes counted individually; transaction-based replication with a buffer keyed by transactionKey and the /data/ChangeEvents channel; sequence-number gaps when objects aren't enabled; mark-dirty gap handling with commitTimestamp and LastModifiedDate; overflow re-sync and delete reconciliation; header field meanings and merged recordIds.
- Pub/Sub API Subscribe RPC reference (fetched from https://developer.salesforce.com/docs/platform/pub-sub-api/references/methods/subscribe-rpc.html): 3-day retention; LATEST, EARLIEST, CUSTOM presets; EARLIEST after more than 3 days disconnected; replay IDs stored as bytes; keepalive FetchResponse carries the latest replay_id; ManagedSubscribe (Beta) commits the replay ID on the server.
- Streaming API Developer Guide (`api_streaming.txt`): 72-hour retention for high-volume and change events, later purging, no guarantee beyond 72 hours (L324-334); replay IDs opaque and not contiguous (L352-357); -1, -2, and replay ID options with the -2 performance warning (L448-520); CDC retention 3 days (L613).
- Metadata API Developer Guide (`api_meta.txt`): PlatformEventChannelMember, eventChannel, selectedEntity, enrichedFields, filterExpression (API 56.0+), file suffix and folder (L96019-96118).

Listed in the original version and not re-read:

- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm (used for day-0 and re-sync loads; see data/bulk-api-patterns)
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
