# Well-Architected Notes — SOQL Query Optimization

## Relevant Pillars

- **Reliability** — Query timeouts directly interrupt business processes. A batch job that times out mid-run leaves data in a partially processed state, requiring manual intervention and data reconciliation. Making queries selective is a prerequisite for reliable automation at scale.
- **Scalability** — A query that performs acceptably at 100,000 records may fail at 1,000,000. Index strategy decisions made at object creation time are far cheaper than retrofit requests when the object has already grown to millions of records. Queries must be designed to remain selective as data volumes grow.
- **Performance** — Selective queries return results faster for users in list views, reports, and flows. Non-selective queries degrade user experience progressively as data grows, and the degradation is non-linear — performance can collapse suddenly once a threshold is crossed.
- **Operational Excellence** — Teams that rely on Query Plan tool reviews as part of their development workflow catch non-selective patterns before they reach production. Proactive index planning, documented in architecture decision records, avoids emergency Salesforce Support cases during production incidents.

## Architectural Tradeoffs

**Custom indexes vs. query restructuring:** Requesting a custom index on an existing non-indexed field is faster to implement but creates a dependency on Salesforce Support response time and adds maintenance overhead. Restructuring the query to use an existing standard indexed field is more self-contained but may require data model changes (adding a lookup field, restructuring relationships) if no suitable indexed field exists.

**Skinny tables vs. two-column indexes:** Skinny tables eliminate the join between standard and custom field tables, which benefits many read patterns at once on an object. Composite indexes optimize specific query patterns. Skinny tables are appropriate when many different queries against the same object are slow; composite indexes are appropriate when a specific query pattern (one filter field, one sort field) is the bottleneck.

**Stored formula equivalents vs. real-time formulas:** Converting a non-deterministic formula field to a stored field (updated by automation) makes it indexable but introduces a refresh lag. For reports and batch processing where nightly freshness is acceptable, this is a clean trade. For user-facing real-time displays, the formula field may still be necessary for display while the stored field is used for filtering.

**OR decomposition vs. OR query:** Decomposing an OR query into two Apex queries increases SOQL query count against governor limits. On objects where each sub-query is fast (both indexed and selective), this trade is almost always worth it. On objects where even the sub-queries are non-selective, decomposition does not help.

## Anti-Patterns

1. **Treating LIMIT as the first performance fix** — LIMIT on its own does not give the optimizer an index to drive from. The LDV guide lists it as the last step after tuning filters, and the one documented exception is ORDER BY on an indexed field with a LIMIT under 100,000 for Last_N_Days queries (see Gotcha 3).
2. **Building OR conditions across non-indexed fields** — A query that ORs two non-indexed custom fields always results in a full-table scan regardless of the individual selectivity of each filter. The optimizer cannot use partial index coverage for OR conditions.
3. **Using formula fields as primary WHERE clause filters on large objects** — Non-deterministic formula fields cannot receive indexes. Any WHERE clause filter on a non-deterministic formula field will always be a full-table scan. This is a permanent structural constraint, not a configuration gap that can be resolved with an index request.

## Official Sources Used

Read for this revision (2026-10-19), Summer '26 (API 67.0) PDFs in the local corpus:

- Best Practices for Deployments with Large Data Volumes (`salesforce_large_data_volumes_bp.txt`): standard and custom index thresholds with the 2M/5M/500K worked examples (L463-471); only the failing index is excluded (L472); AND 20%, OR 10%, all OR fields indexed, LIKE sampling of 100,000 rows (L476-481); the AND twice-threshold and intersection test and the OR tip (L279-293); default indexed fields and unindexable field types (L308, L399-409); custom index by Support or by deploying a custom index XML file via the Metadata API (L395); External ID field types (L418-424); null rows excluded from index tables and the rebuild requirement (L436-438); non-deterministic formula cases (L485-505); cross-object notation (L515); two-column indexes (L524-538); custom indexes copied to all sandboxes (L398) and skinny tables copied to Full sandboxes only (L381-385); skinny-table objects, contents, omission of soft-deleted rows, and the "magic wand" warning (L329-351); nightly statistics (L315-319); soft-deleted rows still affect queries, 15-day retention, hard delete (L735-742, L1021); OR decomposition, negative filters, IN lists, NA placeholder (L949-980); LIMIT starting at 100,000 as a last resort (L1011); ORDER BY ... LIMIT 99999 sort-optimization case (L1220-1237); Recycle Bin kept empty in the report case (L1258).
- Apex Developer Guide (`salesforce_apex_developer_guide.txt`): selective-query criteria and the trigger emphasis (L9625-9632); default indexes including External ID and Unique, auto-indexing, unindexable types, TEXT() on picklist, and the cases where a custom index isn't used (L9641-9663); record counts include soft-deleted rows, and the `Name != ''` example (L9666-9693); ALL ROWS (L9959-9961).
- REST API Developer Guide (`api_rest.txt`): Query Performance Feedback (Beta) `explain` parameter, API 30.0+, plans sorted most to least optimal, `leadingOperationType` values, and `relativeCost` above 1.0 meaning not selective (L17784-17867); worked response (L3810-3866).
- Metadata API Developer Guide (`api_meta.txt`): CustomIndex type, `.indx-meta` suffix, API 50.0+, Support contact required, `allowNullValues` and `booleanIndexedValue` fields (L41099-41138).
- SOQL and SOSL Reference, FIND {SearchQuery} wildcards (fetched from https://developer.salesforce.com/docs/get_document_content/soql_sosl/sforce_api_calls_sosl_find.htm/en-us/262.0): asterisks match at the middle or end of a search term.
- Object Reference (`object_reference.txt`): UserPreference value 99 "Enable Query Plan" (L301033).
- Salesforce Developer Limits and Allocations Quick Reference (`salesforce_app_limits_cheatsheet.txt`): total heap size 6 MB synchronous, 12 MB asynchronous (L89).

Listed in the original version and not re-read (help.salesforce.com cannot be fetched):

- Salesforce Help: Custom Indexes — https://help.salesforce.com/s/articleView?id=sf.custom_indexes.htm
- Salesforce Help: Non-Selective Query Error "System.QueryException" — https://help.salesforce.com/s/articleView?id=000386468&type=1
- Salesforce Help: Developer Console Query Plan Tool FAQ — https://help.salesforce.com/s/articleView?id=000386864&type=1
- SOQL and SOSL Reference — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm
