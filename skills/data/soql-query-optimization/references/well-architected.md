# Well-Architected Notes — SOQL Query Optimization

## Relevant Pillars

- **Reliability** — Query timeouts directly interrupt business processes. A batch job that times out mid-run leaves data in a partially processed state, requiring manual intervention and data reconciliation. Making queries selective is a prerequisite for reliable automation at scale.
- **Scalability** — A query that performs acceptably at 100,000 records may fail at 1,000,000. Index strategy decisions made at object creation time are far cheaper than retrofit requests when the object has already grown to millions of records. Queries must be designed to remain selective as data volumes grow.
- **Performance** — Selective queries return results faster for users in list views, reports, and flows. Non-selective queries degrade user experience progressively as data grows, and the degradation is non-linear — performance can collapse suddenly once a threshold is crossed.
- **Operational Excellence** — Teams that rely on Query Plan tool reviews as part of their development workflow catch non-selective patterns before they reach production. Proactive index planning, documented in architecture decision records, avoids emergency Salesforce Support cases during production incidents.

## Architectural Tradeoffs

**Custom indexes vs. query restructuring:** Requesting a custom index on an existing non-indexed field is faster to implement but creates a dependency on Salesforce Support response time and adds maintenance overhead. Restructuring the query to use an existing standard indexed field is more self-contained but may require data model changes (adding a lookup field, restructuring relationships) if no suitable indexed field exists.

**Skinny tables vs. composite indexes:** Skinny tables eliminate the join between standard and custom field tables, which benefits many read patterns at once on an object. Composite indexes optimize specific query patterns. Skinny tables are appropriate when many different queries against the same object are slow; composite indexes are appropriate when a specific query pattern (one filter field, one sort field) is the bottleneck.

**Stored formula equivalents vs. real-time formulas:** Converting a non-deterministic formula field to a stored field (updated by automation) makes it indexable but introduces a refresh lag. For reports and batch processing where nightly freshness is acceptable, this is a clean trade. For user-facing real-time displays, the formula field may still be necessary for display while the stored field is used for filtering.

**OR decomposition vs. OR query:** Decomposing an OR query into two Apex queries increases SOQL query count against governor limits. On objects where each sub-query is fast (both indexed and selective), this trade is almost always worth it. On objects where even the sub-queries are non-selective, decomposition does not help.

## Anti-Patterns

1. **Treating LIMIT as a performance fix** — Adding LIMIT to a non-selective query does not prevent a full-table scan. The database must still scan all records to find qualifying rows before applying the limit. LIMIT is a result-set restriction, not a query access strategy control.
2. **Building OR conditions across non-indexed fields** — A query that ORs two non-indexed custom fields always results in a full-table scan regardless of the individual selectivity of each filter. The optimizer cannot use partial index coverage for OR conditions.
3. **Using formula fields as primary WHERE clause filters on large objects** — Non-deterministic formula fields cannot receive indexes. Any WHERE clause filter on a non-deterministic formula field will always be a full-table scan. This is a permanent structural constraint, not a configuration gap that can be resolved with an index request.

## Official Sources Used

- Salesforce Large Data Volumes Best Practices — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_query_optimizer.htm
- SOQL and SOSL Reference — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm
- Salesforce Help: Custom Indexes — https://help.salesforce.com/s/articleView?id=sf.custom_indexes.htm
- Salesforce Large Data Volumes Best Practices: Indexes — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_infrastructure_indexes.htm
- Salesforce Large Data Volumes Best Practices: Skinny Tables — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_infrastructure_skinny_tables.htm
