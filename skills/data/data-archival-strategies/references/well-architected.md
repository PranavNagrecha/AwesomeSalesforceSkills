# Well-Architected Notes — Data Archival Strategies

## Relevant Pillars

- **Reliability** — Storage exhaustion blocks all new record inserts org-wide, making storage management a direct reliability concern. A well-designed archival strategy prevents storage-induced outages by keeping data storage below alert thresholds, ensuring the org continues to function as record volumes grow. Recycle bin hygiene and proactive archival are reliability practices, not just housekeeping.
- **Scalability** — Archival is the primary mechanism for designing against long-term data growth. Objects that grow unboundedly become query bottlenecks: the query optimizer struggles to use indexes on tables with tens of millions of rows, and reports slow down. A scalable data architecture uses archival to keep active-record counts within performant bounds, offloading aging data to Big Objects or external storage that scale independently.
- **Performance** — While not a named pillar in isolation, query performance is directly affected by record counts, recycle bin volume, and field history accumulation. Archival strategy decisions have measurable performance consequences.

## Architectural Tradeoffs

**Big Object vs External Storage**

Big Objects keep archived data on-platform and queryable via SOQL (with index constraints), but they consume Salesforce infrastructure. External storage (S3, Heroku PostgreSQL, Data Cloud) removes data from Salesforce entirely, minimizing on-platform storage costs, but requires custom integration to surface data back to Salesforce users when needed. The tradeoff is: on-platform queryability vs cost-optimized cold storage.

Choose Big Objects when:
- Audit or compliance teams need to run Salesforce-native queries against archived data
- The query pattern is known and fits the composite index design
- Staying fully within the Salesforce trust boundary is a requirement

Choose external storage when:
- Archived data is accessed rarely (cold archive)
- Cost-per-GB is a driving concern
- Data volume exceeds practical Big Object limits or management overhead

**Soft-Delete Pattern vs True Archival**

The IsArchived__c soft-delete pattern preserves full reporting capability at zero implementation cost but does not reclaim any storage. True archival (to Big Object or external) reclaims storage but may break existing reports and integrations that assume all records are in the standard object. The tradeoff is: reporting compatibility vs storage reclamation.

**Field History Retention**

Disabling Field History Tracking on high-churn fields is the most effective way to control History object growth. However, once tracking is disabled, that history is gone — there is no retroactive capture. The decision to disable tracking should be made with input from compliance, audit, and data governance stakeholders.

## Anti-Patterns

1. **Archiving without hard delete** — Moving records to a Big Object or external store and then soft-deleting the source records leaves recycle bin residue that degrades query performance for 15 days. Always pair archival writes with a hard delete (`Database.emptyRecycleBin()` or Bulk API hard delete) to fully reclaim storage and eliminate selectivity impact.

2. **Using Big Objects as a general-purpose record store** — Big Objects are optimized for high-volume, append-only archival with fixed query patterns. Using them to store data that needs arbitrary filtering, updates, or complex reporting creates significant query limitations and Apex complexity. Only move data to Big Objects when the query pattern is known and maps to an indexable composite key.

3. **Leaving Field History Tracking enabled on high-churn fields indefinitely** — On objects like Case or Opportunity with frequent status changes, field history rows accumulate at a multiple of the parent record volume. Without active management, History objects can silently grow to be larger than the parent object they track, consuming disproportionate storage and eventually requiring emergency cleanup.

## Official Sources Used

- Big Objects Implementation Guide — https://developer.salesforce.com/docs/atlas.en-us.bigobjects.meta/bigobjects/big_object_overview.htm
- Salesforce Large Data Volumes Best Practices — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/
- Field History Tracking — https://help.salesforce.com/s/articleView?id=sf.field_history.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
