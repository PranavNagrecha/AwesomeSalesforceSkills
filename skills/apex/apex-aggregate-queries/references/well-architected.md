# Well-Architected Notes — Apex Aggregate Queries

## Relevant Pillars

- **Performance Efficiency** — Aggregate queries are the primary pillar. Offloading COUNT/SUM/GROUP BY to the Salesforce database tier eliminates the need to load individual SObject records into heap, reducing CPU time, heap usage, and SOQL row consumption. Choosing the right aggregate pattern (flat GROUP BY vs ROLLUP vs date-function grouping) directly determines whether the solution stays within governor limits at scale.
- **Reliability** — Incorrect row-cap assumptions (2,000 vs 50,000) cause runtime `LimitException` in production. Brittle alias access (`expr0`) breaks silently when query column order changes. Reliable aggregate Apex requires defensive coding: explicit aliases, null guards on ROLLUP subtotals, and cardinality pre-estimation.
- **Operational Excellence** — Readable, well-aliased aggregate queries are significantly easier to maintain and debug than equivalent in-memory Apex aggregation. Teams that standardize on DB-tier aggregation reduce the surface area for regression during schema changes.

## Architectural Tradeoffs

**Aggregate SOQL vs in-memory Apex summation:** Aggregate SOQL wins on performance and governor limit efficiency when the number of result groups is under ~1,500 (leaving headroom below the 2,000-row cap). In-memory Apex summation becomes necessary only when the grouping cardinality is too high for aggregate SOQL — in that case Batch Apex with range-partitioned aggregate queries is the recommended pattern.

**GROUP BY ROLLUP/CUBE vs post-processing subtotals:** ROLLUP/CUBE shifts subtotal computation to the DB tier and keeps Apex logic simple. The tradeoff is reduced control over the 2,000-row cap, since subtotal rows count. For large multi-dimension reports, computing subtotals in Apex from a plain GROUP BY may be safer than risking a ROLLUP-inflated LimitException.

**Static aggregate SOQL vs dynamic aggregate SOQL:** Static inline aggregate SOQL benefits from compile-time field validation. Dynamic aggregate SOQL (`Database.query(soqlString)`) is needed only when the GROUP BY field must be determined at runtime (e.g. user-configurable grouping). Dynamic queries bypass compile-time checks — validate field API names against Schema.getGlobalDescribe() before constructing the string.

## Anti-Patterns

1. **Fetching flat records and summing in Apex loops** — Loading thousands of Opportunity records into a List just to `for` loop and sum `Amount` burns SOQL rows, heap, and CPU when an aggregate query would do the same work entirely at the database tier. This pattern breaks at scale and is a direct violation of the Performance Efficiency pillar.

2. **Using WHERE to filter on aggregate output** — `WHERE SUM(Amount) > 100000` is a parse error. Practitioners who do not know HAVING sometimes add a post-loop Apex filter instead, loading all aggregated rows and discarding most of them — wasting the 2,000-row budget on rows that are immediately thrown away. Use `HAVING` to filter aggregate values before rows are returned.

3. **Assuming the flat-SOQL 50,000-row limit applies** — Designing aggregate queries that can produce up to 10,000 grouped rows because "SOQL allows 50,000" leads to runtime failures. The aggregate row cap is 2,000 — always treat this as a hard design constraint, not an edge case.

## Official Sources Used

- SOQL and SOSL Reference — Aggregate Functions: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_agg_functions.htm
- Apex Developer Guide — Working with SOQL Aggregate Functions: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_agg_fns.htm
- SOQL and SOSL Reference — GROUP BY Considerations: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_group_by_considerations.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
