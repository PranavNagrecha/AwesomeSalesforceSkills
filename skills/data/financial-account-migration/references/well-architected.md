# Well-Architected Notes — Financial Account Migration

## Relevant Pillars

- **Reliability** — The six-step insert order and RBL disablement pattern are reliability controls. Skipping either produces partial loads, lock errors, or stale rollups that can persist indefinitely, making the migrated org unreliable for advisors. Running `RollupRecalculationBatchable` post-load ensures the org reaches a consistent, known-good state before go-live.

- **Performance Efficiency** — Bulk API 2.0 with parallelized batches is the correct mechanism for large-volume FSC data loads. However, FSC's synchronous trigger architecture imposes a hard constraint: parallel workers loading holdings against shared parent accounts will contend without RBL disablement. The performance pattern is: disable triggers for bulk → load at full Bulk API throughput → recalculate in a single controlled pass.

- **Operational Excellence** — Migration jobs should be re-runnable. Using external ID fields with `UPSERT` operations (rather than `INSERT`) means that a failed or partial load can be re-submitted without duplicate record creation. All pre-load and post-load steps (RBL toggle, recalculation batch) should be scripted, not manual.

- **Security** — The RBL disablement targets only the ETL integration user's custom setting instance, not the org-wide setting, to avoid disabling rollup aggregation for live advisor users during a migration window that spans business hours.

## Architectural Tradeoffs

**Throughput vs. trigger safety:** Bulk API 2.0 achieves maximum load throughput (up to 150 million rows per 24 hours per org). FSC's synchronous RBL triggers are incompatible with that throughput for FinancialHolding and FinancialAccountTransaction. The tradeoff is: disable triggers for load speed, accept that rollup values will be stale during the load window, and repair them with a post-load batch. This is the correct tradeoff for any load above a few thousand rows.

**Balance history completeness vs. migration complexity:** Migrating full balance history into Core FSC (one `FinancialAccountBalance` row per snapshot per account) can multiply the row count by the number of historical periods. For an org with 100,000 accounts and 24 months of history, this means 2.4 million additional rows. The architectural decision is whether the analytics value of full history justifies the added load time and storage. For initial go-live, a common approach is to load the most recent 12 months of history and archive older data in an external system.

**Re-runnability vs. insert performance:** UPSERT operations via external ID are slightly slower than INSERT but are architecturally required for production migrations. Network interruptions, batch failures, and partial loads are expected at scale. A migration that cannot be re-run safely without producing duplicates is an operational risk.

## Anti-Patterns

1. **Loading all six object layers in a single Data Loader job** — Parent records that do not yet exist at load time cause foreign-key failures for child rows in the same batch. The six layers must be discrete, sequential jobs with count validation between each step.

2. **Disabling RBL at the org level instead of the user level** — Setting `FinServ__EnableRollupSummary__c = false` at the org level (via the default custom setting record, not a user-specific instance) disables rollup aggregation for all users, including live advisors. This causes real-time balance displays to stop updating for active users during the load window. Always scope the disablement to the ETL user's custom setting instance.

3. **Skipping `RollupRecalculationBatchable` after re-enabling RBL** — Once RBL is re-enabled, only new DML operations trigger incremental rollup updates. Records loaded while RBL was disabled retain stale (zero or pre-load) rollup values indefinitely. The recalculation batch is mandatory, not optional.

## Official Sources Used

- FSC Developer Guide Spring '26 — https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_dev.meta/financial_services_cloud_dev/
- FinancialAccountTransaction Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_financialaccounttransaction.htm
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Salesforce Well-Architected: Reliable Pillar — https://architect.salesforce.com/well-architected/reliable
- Salesforce Well-Architected: Performance Efficiency Pillar — https://architect.salesforce.com/well-architected/performant
