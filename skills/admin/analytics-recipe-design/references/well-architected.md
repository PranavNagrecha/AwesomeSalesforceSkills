# Well-Architected Notes — Analytics Recipe Design

## Relevant Pillars

- **Performance** — Recipe run time scales linearly with input dataset size because every run reprocesses the full input. Filter nodes placed early in the graph reduce the row count before expensive Join and Aggregate operations. Lookup joins are cheaper to reason about than MultiValueLookup joins, which can dramatically expand row count. Over-wide Output schemas (many unnecessary columns) increase storage and query time for downstream lenses.

- **Reliability** — Join type misconfigurations (Inner instead of Lookup) cause silent data loss that is not caught by recipe run success status. Row count verification after every recipe run is the primary reliability control. Schedule configurations exist as a separate resource and must be re-verified after recipe updates, since a recipe re-save does not reset its schedule.

- **Security** — Row-level security (RLS) for the output dataset is defined by a security predicate on the dataset, not by the recipe itself. A recipe that produces a dataset without a security predicate will expose all rows to all users with dataset access. Recipe design should include explicit documentation of the intended security predicate, even if the predicate is applied separately after the recipe run.

- **Operational Excellence** — Recipes replace legacy dataflows for new development as of Spring '25. Recipe node graphs should be named descriptively (not left as "Node 1", "Join 2") so that the design intent is auditable without running the recipe. Recipe descriptions should document the join type rationale for every Join node.

## Architectural Tradeoffs

**Lookup vs LeftOuter join:** Both preserve all left-side rows. Lookup is semantically tighter — it is designed for the "enrich, don't filter" use case and is the recommended join type when adding reference data to a fact dataset. LeftOuter is appropriate when the right-side dataset also needs to contribute rows to the output schema in a way that LeftOuter more explicitly communicates (e.g., joining two fact datasets where the left dataset is the primary fact). When in doubt, Lookup communicates intent more clearly.

**Bucket node vs SAQL binning at query time:** Bucket nodes persist the classification logic in the dataset schema, making it available to all downstream lenses without query-layer duplication. SAQL binning at query time offers more flexibility (the bin ranges can vary per lens) but creates maintenance risk when the segment definition changes — every lens must be updated individually. For canonical business segments (Revenue Tier, Account Size) that should be consistent across all dashboards, a Bucket node in the recipe is the architecturally correct choice.

**Recipe scheduling frequency vs dataset freshness requirements:** Recipes are quota-consuming — each run counts against the org's recipe processing quota. High-frequency schedules (hourly) on large datasets can exhaust the quota and cause downstream scheduled jobs to queue or fail. Balance freshness requirements against quota impact. For near-real-time freshness requirements that cannot be met within quota, evaluate whether a direct object connection or a dataflow (for specific legacy use cases) is more appropriate.

**Full reprocessing vs approximate incremental pattern:** Recipes reprocess full input on every run. For datasets under ~1M rows, this is typically within acceptable run time bounds. For larger datasets, the filter-append incremental approximation pattern (see gotchas.md) adds architectural complexity and must be documented explicitly — the pattern is not self-documenting in the recipe canvas.

## Anti-Patterns

1. **Default Inner join on all Join nodes** — Accepting the default join type without reviewing whether all left-side rows must be preserved. Results in silent data loss that is only detectable by comparing row counts. Every Join node must have an explicitly reviewed and documented join type.

2. **Embedding scheduling intent in the recipe JSON** — Attempting to configure a recurring refresh by adding a schedule property to the recipe body or deployment package. Recipe schedules are an independent resource (`/wave/recipes/{id}/schedules`) and are not part of the recipe definition. This anti-pattern results in recipes that never refresh automatically, with no error to indicate why.

3. **Building wide output datasets without a column pruning step** — Including all input columns in the Output node when only a subset is needed by downstream lenses. Wide datasets increase storage consumption, slow query execution in SAQL lenses, and expose fields that may not be covered by the dataset's security predicate. Add a column selection step (available on most node types' output column configuration) to retain only required fields.

## Official Sources Used

- Transformations for Data Prep Recipes (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_recipes_transformations.htm
- Nodes for Data Prep Recipes (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_recipes_nodes.htm
- Join Operations — Analytics (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_recipes_node_join.htm
- CRM Analytics REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
