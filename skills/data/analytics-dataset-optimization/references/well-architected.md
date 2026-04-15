# Well-Architected Notes — Analytics Dataset Optimization

## Relevant Pillars

- **Performance** — The primary pillar for this skill. Field pruning directly reduces the memory and I/O cost of every SAQL query. Date granularity choices determine whether timeseries expressions are native operations (Date type) or require per-row function evaluation (Text with runtime conversion). Pre-computed epoch fields eliminate repeated `date_to_epoch()` calls. Dataset splitting is the only available mechanism to reduce per-query scan scope in a platform with no native partition pruning.

- **Scalability** — Dataset optimization is a prerequisite for sustainable scale. A wide, unpartitioned dataset that performs acceptably at 2 million rows will degrade visibly at 20 million rows. Field pruning and dataset splitting must be designed before scale is reached, not after. The 60-run rolling window is a fixed ceiling — orgs that don't optimize their refresh schedules will hit it and have no recourse except consolidation.

- **Operational Excellence** — Refresh schedule design and run-budget management are ongoing operational responsibilities. Splitting datasets by year requires operational procedures for creating new datasets, updating dashboards, and retiring old datasets at year boundaries. Undocumented dataset splits create confusion when dashboards are updated by team members who are unaware of the multi-dataset architecture.

- **Reliability** — Poorly designed refresh schedules produce stale data without visible error signals. When the 60-run window is exhausted, later-in-the-day jobs are silently skipped and dashboards display yesterday's data. The reliability risk is that no alert is raised by default — only a dataset freshness monitor reveals the problem.

## Architectural Tradeoffs

**Field count vs. development convenience:** Pulling all fields from a Salesforce object (`*` equivalent) is faster to set up and accommodates future dashboard needs without a dataflow change. The cost is proportionally slower sync times and query performance. The tradeoff tips toward selective field inclusion at scale (millions of rows) and toward wider inclusion in early development or low-volume datasets.

**Dataset splitting vs. unified dataset:** A unified dataset is simpler to maintain and query (no multi-dataset SAQL needed). Dataset splitting reduces query scan scope but introduces operational complexity: new datasets must be created at year or period boundaries, dashboards must be updated, and SAQL for cross-period views must use unions or summary aggregations. The tradeoff tips toward splitting when row counts are above 10–20 million and dominant queries filter to a single period.

**Epoch pre-computation vs. runtime date math:** Computing durations at ELT time reduces per-query compute but adds fields to the dataset schema (widening it slightly). For simple datasets with few concurrent users, the runtime cost of `date_to_epoch()` is negligible. The tradeoff tips toward pre-computation when the dataset has millions of rows and concurrent user count is significant (dozens or more simultaneously active dashboard sessions).

**Refresh frequency vs. run budget:** High-frequency refreshes keep data fresh but consume run-budget slots faster, potentially crowding out other datasets. The right balance is to identify the minimum refresh cadence each business use case actually requires — live operational dashboards may need hourly or more frequent refreshes, while weekly reporting datasets can refresh nightly or weekly without business impact.

## Anti-Patterns

1. **Pulling all object fields into every dataset** — Dataflow and Recipe configurations that include all fields from a Salesforce object because it is convenient produce unnecessarily wide datasets. At production scale, this is the single most common source of CRM Analytics performance problems. The correct approach is to audit dashboard SAQL bindings and produce a field whitelist before writing the dataflow or Recipe configuration.

2. **Treating "dataset partition by year" as equivalent to database partitioning** — CRM Analytics has no native partition index. Queries do not skip rows based on a partition key. Any design that relies on platform-level partition pruning will behave incorrectly — every query will scan the full dataset regardless of filter values. The architectural response is to create separate named datasets per period, not to expect the platform to prune based on a date column.

3. **Scheduling all datasets to refresh at maximum frequency** — Every run slot is drawn from the shared 60-run rolling window. Refreshing historical datasets (whose data does not change) at the same frequency as current-period datasets is wasteful and can exhaust the run budget, causing the most important current-period refreshes to be skipped. Tier refresh frequency by business need: high-frequency only for datasets that drive live operational use cases.

## Official Sources Used

- CRM Analytics Limits and Considerations — https://help.salesforce.com/s/articleView?id=sf.bi_admin_limits.htm&type=5
  Used for: dataset field-count limits, per-org row ceilings, 60-run rolling window behavior, and dataset size constraints.

- CRM Analytics REST API Developer Guide (Spring '26) — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm
  Used for: dataset metadata endpoints, schema inspection via API, SAQL query structure for date expressions and timeseries, and epoch companion field behavior.

- Connect and Sync Your Data to CRM Analytics — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_connectors_intro.htm&type=5
  Used for: dataflow sfdcDigest node field selection behavior, schema transformation nodes, and date type declaration syntax.

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
  Used for: Performance, Scalability, and Operational Excellence pillar framing for tradeoff guidance.
