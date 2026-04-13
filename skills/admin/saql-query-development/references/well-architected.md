# Well-Architected Notes — SAQL Query Development

## Relevant Pillars

- **Performance** — SAQL query structure directly determines query execution time. Broad `load` statements without `filter` push the full dataset through every downstream operator. Moving filters as early as possible in the pipeline (immediately after `load`) reduces the number of rows processed by `group`, `cogroup`, and windowing steps. `cogroup` on high-cardinality keys can be expensive; pre-filtering each stream before the `cogroup` statement reduces the join set size. Windowing functions scan the full partition for each row — unbounded partitions over large datasets compound cost.
- **Reliability** — Queries that depend on dataset developer names in REST API calls fail silently when the dataset is renamed or versioned. Using `datasetId` and `datasetVersionId` makes REST API integrations resilient to naming changes. Piggyback query logic that ignores the `query` attribute `filter` field creates invisible reliability gaps: dashboard filters appear to apply but do not, producing silent data errors that users may not detect.
- **Operational Excellence** — SAQL pipeline queries are more maintainable than deeply nested single-statement queries because each step has a named stream that can be inspected independently in the SAQL editor. Keeping each transformation in a discrete, named step (load → filter → group → foreach → order → limit) makes it easier to isolate and debug a failing stage. Consistent naming conventions for stream variables (`q`, `orders`, `accts`) improve readability across team members.

## Architectural Tradeoffs

**Aggregation vs Windowing:** Plain `group ... foreach` aggregation is simpler and faster for dashboard KPIs where the exact row count is not important. Windowing functions preserve row count and enable per-row ranking and running totals, but require two `foreach` steps (one for aggregation, one for windowing) and scan the full partition for each computed row. Use windowing only when the use case genuinely requires per-row computed values rather than group-level summaries.

**cogroup vs separate dataset loads:** Joining two datasets with `cogroup` adds query complexity and join processing overhead. When the enrichment data (e.g., account name) is small and static, embedding it in the primary dataset at dataflow/recipe time avoids runtime `cogroup` cost entirely. Reserve `cogroup` for cases where the join data is dynamic or cannot be denormalized at prep time.

**rollup vs separate summary queries:** The `rollup` modifier generates all subtotal levels in one query pass, which is more efficient than running separate queries for detail rows, region subtotals, and grand totals. The tradeoff is query complexity — the consumer must use `grouping()` flag fields to distinguish subtotal rows from detail rows, adding conditional logic to every widget that uses the result.

## Anti-Patterns

1. **Writing SQL/SOQL syntax in SAQL contexts** — Any `SELECT ... FROM ... WHERE ... GROUP BY` construct in a SAQL editor, dashboard step, or REST API payload fails at parse time. There is no partial execution. All SAQL queries must use the pipeline assignment syntax (`q = load ...; q = filter q by ...; q = group q by ...; q = foreach q generate ...`). This is the most common single cause of SAQL query failures.

2. **Referencing dataset developer names in REST API payloads** — The `/wave/query` endpoint requires `datasetId` and `datasetVersionId`. Integrations that pass only the developer name or omit the version ID fail at runtime. Always resolve the ID pair programmatically before constructing the API payload.

3. **Applying dashboard filters to piggyback query steps via the query attribute** — When `pigql` is set on a dashboard step, the `filter`, `limit`, and `order` on the `query` attribute are silently ignored. Any filter binding or dynamic widget interaction that targets the `query` attribute on a piggyback step produces no effect — the dashboard appears interactive but the data does not change. All filtering logic must live inside the `pigql` SAQL string.

## Official Sources Used

- SAQL Developer Guide — Statements overview: https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_saql.meta/bi_dev_guide_saql/bi_saql_statements.htm
- SAQL Developer Guide — Windowing Functions: https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_saql.meta/bi_dev_guide_saql/bi_saql_functions_windowing.htm
- SAQL Developer Guide — cogroup statement: https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_saql.meta/bi_dev_guide_saql/bi_saql_cogroup.htm
- SAQL Developer Guide — Aggregate Functions: https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_saql.meta/bi_dev_guide_saql/bi_saql_functions_aggregate.htm
- SAQL Developer Guide — rollup and grouping(): https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_saql.meta/bi_dev_guide_saql/bi_saql_group_rollup.htm
- CRM Analytics REST API Developer Guide — SAQL Query endpoint: https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_reference_query.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
