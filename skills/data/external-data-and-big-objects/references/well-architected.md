# Well-Architected Notes — External Data and Big Objects

## Relevant Pillars

- **Performance** — Composite index design is the primary performance lever for Big Objects, and it is close to irreversible: the index defines which queries are *possible*, not merely which are fast. A filter that is not a gapless left-to-right prefix of the index is not a slow query, it is an invalid one, and the remedy is a new Big Object rather than a tuned query. External Object query patterns must be designed to avoid per-record callout patterns (loops) that exhaust callout limits and create latency spikes.
- **Scalability** — Big Objects are the recommended mechanism for Salesforce data that grows without bound (audit logs, IoT telemetry, event streams). They are designed to scale into the billions of records without affecting standard org query performance, unlike standard custom objects which share the main data storage tier.
- **Reliability** — `Database.insertImmediate()` failures are silent by default. A production system that does not instrument and alert on Big Object insert failures will silently lose records at scale. Note also the asymmetry that makes Big Object projects fail late: the write path works long before anyone exercises the read path, so a broken read design (most often one built on the retired Async SOQL API) is discovered only when the first compliance query is due, against a populated tier.
- **Operational Excellence** — Big Object reads at volume run as Batch Apex, so they inherit Apex batch operations: monitor `AsyncApexJob` for failed and stuck jobs, and design retry with the same discipline as any other batch. External Object connectivity should be monitored via Salesforce Connect request logs in Setup.

## Architectural Tradeoffs

**Big Object vs External Object**

| Dimension | Big Object | External Object |
|---|---|---|
| Data location | Stored in Salesforce | Stays in external system |
| Query mechanism | Standard SOQL, Batch Apex, or Bulk API query | Synchronous SOQL (real-time callout) |
| Query limits | No per-query API calls to external | Consumes Salesforce callout limits |
| Latency | Results available after async job | Live at query time (subject to callout timeout) |
| DML support | Insert/upsert only, no triggers | Read-only or write-through (adapter-dependent) |
| Use case fit | Audit history, IoT telemetry, event logs | Live ERP lookups, small reference data |
| Analytics support | Aggregation is the caller's job in Batch Apex | Limited; callout-per-query makes bulk analytics impractical |

The primary decision axis is: **does the data need to live in Salesforce, or does it need to stay external?** If it must stay external, External Objects are the correct mechanism. If it can be ingested into Salesforce and the volume is too large for standard objects, Big Objects are the correct tier.

**Big Object vs Standard Object for High-Volume Data**

Standard objects are inappropriate for datasets expected to grow beyond ~10 million records. They share the org's main data storage tier, so large standard object tables degrade SOQL query performance for the entire org, not just queries targeting those tables. Big Objects exist precisely to isolate high-volume storage from the standard query path.

## Anti-Patterns

1. **Designing the read path around Async SOQL** — Retired in Summer '23; the `async-queries` endpoint is gone. It remains the most likely wrong answer in this domain because it was correct and heavily documented for six years, so it is what both practitioners and models reach for. Teams discover it after ingestion is live and the tier is populated. Read via standard SOQL, Batch Apex, or Bulk API query, and note that the aggregate-into-a-target-object behaviour has no replacement — you write those records yourself in `finish()`.

2. **Using an External Object for bulk data access** — External Objects are designed for single-record or small-set lookups where the external system can respond within the callout timeout window. Using an External Object as a replacement for bulk data ingestion — e.g., querying thousands of External Object records in a batch process — will exhaust callout limits, trigger timeouts, and produce inconsistent results. Bulk access to external data requires either a data copy pipeline into Salesforce (Big Object or standard object) or an external analytics platform.

3. **Treating Big Object records as mutable** — Big Objects do not support update DML. Teams that design data models expecting to correct or update records will discover this constraint only at the implementation phase. Architectural decisions about Big Object schemas should be made with the knowledge that records are effectively append-only, and any correction strategy must be planned upfront (overwrite via upsert-by-index, or tombstone-and-reinsert patterns).

## Official Sources Used

- Big Objects Implementation Guide — https://developer.salesforce.com/docs/atlas.en-us.bigobjects.meta/bigobjects/big_object.htm
- Object Reference: Concepts (External Objects) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Salesforce Help 000394892: Big Objects Async SOQL Retirement — Async SOQL retired with Summer '23; "You must use the Bulk API or batch Apex to query or report on custom Big Objects" — https://help.salesforce.com/s/articleView?id=000394892&language=en_US&type=1
- SOQL and SOSL Reference: SOQL Object Limits and Limitations (big objects) — "A SOQL query can only filter on the fields defined in the big object's index, in the order that they are defined, without gaps"; last filtered index field allows =, <, >, <=, >=, IN; !=, LIKE, NOT IN, EXCLUDES, INCLUDES unsupported — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_limits.htm
- Salesforce Connect Overview — https://help.salesforce.com/s/articleView?id=sf.platform_connect_about.htm&type=5
- Large Data Volumes Best Practices — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_introduction.htm
