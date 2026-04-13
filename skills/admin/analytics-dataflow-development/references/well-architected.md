# Well-Architected Notes — Analytics Dataflow Development

## Relevant Pillars

- **Performance** — Dataflow node ordering directly determines runtime. Placing Filter and SliceDataset nodes early (before Augment) reduces row count and schema width at the most compute-intensive join step. Monolithic dataflows with 20+ nodes should be split into chained pipelines using Edgemart to reduce per-run scope and improve failure isolation.
- **Reliability** — A single failing node aborts the entire run and leaves the registered dataset in its prior state. Pipelines must be structured so that failures are immediately detectable (via alerting on run status) and recoverable (via clean re-run after fixing the failing node). Critical datasets should have documented recovery playbooks.
- **Operational Excellence** — Scheduling must account for the 60-run rolling 24-hour org limit. Dataflow JSON should be source-controlled (`.wdf` files committed to version control) so changes are auditable. Node names should be descriptive to make Job Progress Details readable during incident response.
- **Security** — sfdcDigest respects Salesforce field-level security for the running user's credential but does not apply sharing rules by default. Row-level security for CRM Analytics datasets is enforced via security predicates on the registered dataset, not within the dataflow itself. Dataflows that extract sensitive fields should be reviewed to confirm the registered dataset has appropriate security predicates.
- **Scalability** — The 250-million-row-per-dataset cap and the 60-run-per-24-hour org limit are hard ceilings. Dataflow designs should include row-volume projections and growth plans. Designs approaching these limits should proactively split datasets or consolidate shared-source dataflows before limits are hit in production.

## Architectural Tradeoffs

**Dataflows vs. Recipes:** Dataflows offer full JSON control and support complex SAQL expressions (computeRelative, computeExpression) that are not available in Recipes. However, Recipes are the strategic direction for new development — they provide a visual UI, incremental load support, and multi-join-type options that dataflows lack. New pipelines should use Recipes unless there is a specific technical requirement that only dataflows satisfy.

**Monolithic vs. chained dataflows:** A single large dataflow is easier to schedule (one trigger, one run) but is harder to debug (any of 30 nodes could fail), harder to optimize (the entire graph runs even if only one section changes), and risks consuming a disproportionate share of the 60-run quota per day. Chained dataflows using Edgemart are more resilient — failures are isolated to one stage, and only the affected stage needs to re-run — but require dependency scheduling and intermediate dataset management.

**Full-refresh vs. incremental:** sfdcRegister always does a full replace. For high-volume historical datasets (tens of millions of rows), rebuilding the full dataset on every run is expensive and slow. The incremental pattern (Edgemart existing dataset + sfdcDigest new records + Append + sfdcRegister) keeps runtime manageable but requires careful deduplication logic. Recipes with incremental output are the cleaner solution for this pattern.

## Anti-Patterns

1. **Augment before Filter** — Running an Augment join on the full extracted row set before applying a Filter node multiplies compute cost unnecessarily. Always filter to the minimum required row set before any join operation. This is the single most common performance anti-pattern in CRM Analytics dataflows.

2. **Monolithic 30-node dataflows with no intermediate checkpoints** — Large single dataflows make debugging slow (must re-run the entire pipeline to test a fix to any node), are harder to maintain (no logical boundaries between pipeline stages), and are more likely to approach run-time limits. Split at natural domain boundaries using Edgemart as the connector.

3. **Undocumented sfdcRegister aliases** — Changing an alias without updating all downstream consumers creates silent data staleness. Treating aliases as mutable and undocumented leads to incidents where dashboards silently serve stale data after a rename. Aliases should be treated as stable identifiers and documented alongside any dashboards or SAQL lenses that depend on them.

## Official Sources Used

- Transformations for CRM Analytics Dataflows — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_transformations.htm
- CRM Analytics Limits — https://help.salesforce.com/s/articleView?id=sf.bi_admin_limits.htm
- Analytics SAQL Developer Guide: Speed Up Queries with Dataflow Transformations — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_saql.meta/bi_dev_guide_saql/bi_saql_speed_up_queries_with_dataflow_transformations.htm
- CRM Analytics REST API Developer Guide (Spring '26) — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
