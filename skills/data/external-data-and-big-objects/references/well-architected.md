# Well-Architected Notes — External Data and Big Objects

## Relevant Pillars

- **Performance** — Composite index design is the primary performance lever for Big Objects. A poorly designed index means every Async SOQL job performs a full-tier scan, which causes long job runtimes and delays in result availability. External Object query patterns must be designed to avoid per-record callout patterns (loops) that exhaust callout limits and create latency spikes.
- **Scalability** — Big Objects are the recommended mechanism for Salesforce data that grows without bound (audit logs, IoT telemetry, event streams). They are designed to scale into the billions of records without affecting standard org query performance, unlike standard custom objects which share the main data storage tier.
- **Reliability** — `Database.insertImmediate()` failures are silent by default. A production system that does not instrument and alert on Big Object insert failures will silently lose records at scale. Async SOQL jobs must also be monitored; a job stuck in `Running` or `Failed` state will never write results to the target object.
- **Operational Excellence** — Async SOQL jobs must be polled for completion; there is no push notification mechanism. Operational runbooks must include procedures for detecting, retrying, and debugging failed Async SOQL jobs. External Object connectivity should be monitored via Salesforce Connect request logs in Setup.

## Architectural Tradeoffs

**Big Object vs External Object**

| Dimension | Big Object | External Object |
|---|---|---|
| Data location | Stored in Salesforce | Stays in external system |
| Query mechanism | Async SOQL (batch, non-real-time) | Synchronous SOQL (real-time callout) |
| Query limits | No per-query API calls to external | Consumes Salesforce callout limits |
| Latency | Results available after async job | Live at query time (subject to callout timeout) |
| DML support | Insert/upsert only, no triggers | Read-only or write-through (adapter-dependent) |
| Use case fit | Audit history, IoT telemetry, event logs | Live ERP lookups, small reference data |
| Analytics support | Async SOQL aggregations | Limited; callout-per-query makes bulk analytics impractical |

The primary decision axis is: **does the data need to live in Salesforce, or does it need to stay external?** If it must stay external, External Objects are the correct mechanism. If it can be ingested into Salesforce and the volume is too large for standard objects, Big Objects are the correct tier.

**Big Object vs Standard Object for High-Volume Data**

Standard objects are inappropriate for datasets expected to grow beyond ~10 million records. They share the org's main data storage tier, so large standard object tables degrade SOQL query performance for the entire org, not just queries targeting those tables. Big Objects exist precisely to isolate high-volume storage from the standard query path.

## Anti-Patterns

1. **Querying a Big Object with synchronous SOQL in production** — Standard SOQL against a Big Object appears to work in sandboxes with small data volumes but silently returns zero results or partial data at scale. All production Big Object queries must go through the Async SOQL REST API. Teams that use synchronous SOQL in production build reporting pipelines that appear to function in QA but fail silently after go-live.

2. **Using an External Object for bulk data access** — External Objects are designed for single-record or small-set lookups where the external system can respond within the callout timeout window. Using an External Object as a replacement for bulk data ingestion — e.g., querying thousands of External Object records in a batch process — will exhaust callout limits, trigger timeouts, and produce inconsistent results. Bulk access to external data requires either a data copy pipeline into Salesforce (Big Object or standard object) or an external analytics platform.

3. **Treating Big Object records as mutable** — Big Objects do not support update DML. Teams that design data models expecting to correct or update records will discover this constraint only at the implementation phase. Architectural decisions about Big Object schemas should be made with the knowledge that records are effectively append-only, and any correction strategy must be planned upfront (overwrite via upsert-by-index, or tombstone-and-reinsert patterns).

## Official Sources Used

- Big Objects Implementation Guide — https://developer.salesforce.com/docs/atlas.en-us.bigobjects.meta/bigobjects/big_object.htm
- Object Reference: Concepts (External Objects) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Async SOQL Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.bigobjects.meta/bigobjects/async_query_overview.htm
- Salesforce Connect Overview — https://help.salesforce.com/s/articleView?id=sf.platform_connect_about.htm&type=5
- Large Data Volumes Best Practices — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_introduction.htm
