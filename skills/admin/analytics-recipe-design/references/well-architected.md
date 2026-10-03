# Well-Architected Notes — Analytics Recipe Design

## Relevant Pillars

- **Performance** — In `Full` run mode a recipe reprocesses its whole input on every run, so run time grows with input size. Filter nodes placed early in the graph reduce the row count before expensive Join and Aggregate operations. Lookup joins are cheaper to reason about than MultiValueLookup joins, which can dramatically expand row count. Over-wide Output schemas (many unnecessary columns) increase storage and query time for downstream lenses.

- **Reliability** — Join type misconfigurations (Inner instead of Lookup) cause silent data loss that is not caught by recipe run success status. Row count verification after every recipe run is the primary reliability control. Schedules live on the separate Schedule resource (`/wave/asset/<recipeId>/schedule`), are not part of `WaveRecipe` metadata, and must be recreated in every org the recipe is deployed to.

- **Security** — Row-level security (RLS) for the output dataset is a security predicate on the dataset. The recipe's Output node can set it only when the dataset is first created; after that, edit the dataset. A recipe that produces a dataset without a security predicate will expose all rows to all users with dataset access. Recipe design should include explicit documentation of the intended security predicate, even if the predicate is applied separately after the recipe run.

- **Operational Excellence** — Recipes replace legacy dataflows for new development (UNVERIFIED (2026-10-03): the "as of Spring '25" date is not stated in the guides read). Recipe node graphs should be named descriptively (not left as "Node 1", "Join 2") so that the design intent is auditable without running the recipe. Recipe descriptions should document the join type rationale for every Join node.

## Architectural Tradeoffs

**Lookup vs LeftOuter join:** Both preserve all left-side rows. Lookup is semantically tighter — it is designed for the "enrich, don't filter" use case and is the recommended join type when adding reference data to a fact dataset. LeftOuter is appropriate when the right-side dataset also needs to contribute rows to the output schema in a way that LeftOuter more explicitly communicates (e.g., joining two fact datasets where the left dataset is the primary fact). When in doubt, Lookup communicates intent more clearly.

**Bucket node vs SAQL binning at query time:** Bucket nodes persist the classification logic in the dataset schema, making it available to all downstream lenses without query-layer duplication. SAQL binning at query time offers more flexibility (the bin ranges can vary per lens) but creates maintenance risk when the segment definition changes — every lens must be updated individually. For canonical business segments (Revenue Tier, Account Size) that should be consistent across all dashboards, a Bucket node in the recipe is the architecturally correct choice.

**Recipe scheduling frequency vs dataset freshness requirements:** Dataflow and recipe runs longer than 2 minutes count against a shared limit of 60 runs in a rolling 24-hour period, and at the limit no dataflow, recipe, or data sync can run. High-frequency schedules on long recipes exhaust that budget for every other job. Balance freshness requirements against quota impact. For near-real-time freshness requirements that cannot be met within quota, evaluate whether a direct object connection or a dataflow (for specific legacy use cases) is more appropriate.

**Full reprocessing vs incremental:** A `Full` run reprocesses the whole input. Check whether the native `Incremental` run mode applies before building a manual pattern. For datasets under ~1M rows, this is typically within acceptable run time bounds. For larger datasets, the filter-append incremental approximation pattern (see gotchas.md) adds architectural complexity and must be documented explicitly — the pattern is not self-documenting in the recipe canvas.

## Anti-Patterns

1. **Default Inner join on all Join nodes** — Accepting the default join type without reviewing whether all left-side rows must be preserved. Results in silent data loss that is only detectable by comparing row counts. Every Join node must have an explicitly reviewed and documented join type.

2. **Embedding scheduling intent in the recipe JSON** — Attempting to configure a recurring refresh by adding a schedule property to the recipe body or deployment package. Recipe schedules are managed only through the Schedule resource (`PUT /wave/asset/<recipeId>/schedule`); the recipe's `scheduleAttributes` field is read-back only. This anti-pattern results in recipes that never refresh automatically, with no error to indicate why.

3. **Building wide output datasets without a column pruning step** — Including all input columns in the Output node when only a subset is needed by downstream lenses. Wide datasets increase storage consumption, slow query execution in SAQL lenses, and expose fields that may not be covered by the dataset's security predicate. Add a column selection step (available on most node types' output column configuration) to retain only required fields.

## Official Sources Used

Read for the 2026-10-03 pass (all fetched with plain `curl`; line numbers cite the `pdftotext -layout` extraction):

- Data Prep Recipe REST API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_recipes_api.pdf (recipe definition and node map L420-616, Schedule a Recipe and Run a Recipe L588-616, Join Parameters Input join types L2770-2795, formula expression types L2740-2752, L4317-4362, `runMode` values L2953-2956, L3660-3663)
- CRM Analytics REST API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_rest.pdf (Schedule Dataflows, Recipes, and Data Syncs with request bodies L1480-1570, Schedule resource methods and versions L6266-6300, `/wave/dataflowjobs` start and stop L1425-1460)
- CRM Analytics REST API Recipe Resources page (JSON endpoint): https://developer.salesforce.com/docs/get_document_content/bi_dev_guide_rest/bi_resources_recipes_overview.htm/en-us/262.0 (points recipe reference content to the Data Prep Recipe REST API guide)
- Analytics Platform Setup Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_admin_guide_setup.pdf (Integration User and Security User behavior L87-106, Edit Dataset Recipes permission L207, Recipe and Dataflow Limits L1148-1191)
- Analytics Security Implementation Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_admin_guide_security.pdf (predicate changes after dataset creation, `$User` session note, Output node Security Predicate L274-300)
- Metadata API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (WaveRecipe fields, deletion, and wildcard note L138986-139058; WaveApplication and FolderShare L138608-138650, L74693-74740)

Listed by the original author and not re-read in this pass (help.salesforce.com and architect.salesforce.com do not serve article content to plain HTTP clients):

- Transformations for Data Prep Recipes (Salesforce Help): https://help.salesforce.com/s/articleView?id=sf.bi_integrate_recipes_transformations.htm
- Nodes for Data Prep Recipes (Salesforce Help): https://help.salesforce.com/s/articleView?id=sf.bi_integrate_recipes_nodes.htm
- Join Operations: Analytics (Salesforce Help): https://help.salesforce.com/s/articleView?id=sf.bi_integrate_recipes_node_join.htm
- CRM Analytics REST API Developer Guide (atlas HTML): https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
