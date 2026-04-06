# Well-Architected Notes — Data Reconciliation Patterns

## Relevant Pillars

- **Reliability** — Data reconciliation is fundamentally a reliability concern. Integrations that lack reconciliation checks are fragile: silent failures accumulate until business processes break. The layered count-field-record reconciliation ladder provides an early warning system that keeps data contracts reliable across system boundaries.
- **Operational Excellence** — Automated reconciliation checks, structured discrepancy logging, and idempotent upsert patterns reduce manual investigation time and enable integrations to self-heal (re-queue failed rows, replay CDC gaps) without operator intervention.
- **Security** — External ID fields used as upsert keys must be protected from casual updates. Grant field-level security on External ID fields only to integration users, not to end users, to prevent accidental overwrites of the join key. Count reconciliation queries should run via a dedicated integration user with View All Data rather than a user subject to sharing rules.
- **Performance** — Bulk API 2.0 is the correct API for reconciliation at scale. REST single-record upserts are subject to per-transaction API call limits and do not scale beyond a few hundred records. Field-level hash comparison should be scoped to the delta period, not run as a full-table scan.

## Architectural Tradeoffs

**CDC vs. Polling:** CDC provides near-real-time delta detection with minimal query overhead but has a 72-hour retention window and does not support all objects. Polling via `SystemModstamp` or `LastModifiedDate` is universally applicable but introduces latency equal to the polling interval and produces false positives from formula recalculations. Use CDC where supported; fall back to polling with a supplemental tombstone strategy for objects not on the CDC support list.

**External ID Uniqueness vs. Flexibility:** Enforcing Unique on an External ID field prevents duplicates and enables reliable upsert but adds an indexed column that slightly increases DML overhead on that object. For high-volume objects (millions of records), evaluate whether the index cost is acceptable or whether a surrogate matching strategy (e.g., a pre-query lookup before upsert) is preferable.

**Full Reconciliation vs. Incremental:** Full reconciliation (compare every record) is accurate but expensive. Incremental reconciliation (compare only the delta since last run) is fast but can miss drift that occurred before the last-run timestamp or outside the delta window. Schedule a full reconciliation periodically (weekly or monthly) to reset the baseline, and rely on incremental reconciliation for daily operation.

## Anti-Patterns

1. **Treating JobComplete as full success** — Checking only the Bulk API 2.0 job state string without fetching `failedResults` means partial failures silently accumulate. Always check `numberRecordsFailed` and retrieve the `failedResults` CSV after every job.

2. **Delta loads without tombstone logic** — Using `LastModifiedDate > :lastRun` as the sole change detection mechanism misses hard-deleted records entirely. Integrations built on this pattern drift silently until count-level reconciliation surfaces the discrepancy. Pair every delta load strategy with a tombstone or CDC DELETE event handler.

3. **Non-unique External ID fields used as upsert keys** — Skipping the Unique constraint on an External ID field allows duplicate values to accumulate. The first upsert operation that encounters duplicates produces `MULTIPLE_CHOICES` errors, and the root cause is hard to diagnose if the field was not intended to be non-unique. Enforce uniqueness at field definition time.

## Official Sources Used

- Bulk API 2.0 Developer Guide (Upsert) — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Data Integration Decision Guide — https://architect.salesforce.com/decision-guides/data-integration
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
