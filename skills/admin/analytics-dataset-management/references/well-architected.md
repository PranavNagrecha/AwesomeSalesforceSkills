# Well-Architected Notes — Analytics Dataset Management

## Relevant Pillars

- **Reliability** — Dataset pipelines must run predictably on schedule. Failures should surface as alerts, not silent data staleness. Quota management and failure notifications are core reliability requirements.
- **Performance** — Large append-mode datasets degrade query performance. Trimming datasets to a relevant time window and combining multi-object flows into single dataflows reduces both storage consumption and query scan cost.
- **Operational Excellence** — Dataflow ownership, failure alerting, schedule documentation, and row-count monitoring are the operational scaffolding that keeps a CRM Analytics deployment sustainable. Without them, pipeline problems surface only when a stakeholder notices stale data.
- **Security** — Dataset-level security (security predicates and app sharing) is a separate concern from the source Salesforce object permissions. Well-Architected framing requires that row-level access is explicitly designed at the dataset layer, not assumed to inherit from org sharing.
- **Scalability** — The 60-run/day quota and the 500M-row org ceiling are hard scalability limits. Architecture decisions made early (append vs. full-replace, one flow per object vs. combined flows, frequency of refresh) determine whether the deployment scales gracefully or hits a wall.

## Architectural Tradeoffs

**Freshness vs. quota consumption:** Higher refresh frequency improves data currency but consumes more of the 60-run quota. For most operational dashboards, a nightly refresh is sufficient. Reserve frequent (hourly or sub-hourly) refresh cadences for dashboards that support intraday decisions where data age genuinely affects the decision.

**Append vs. full-replace:** Append mode is cheaper per run because only new rows are written. Full-replace re-ingests all rows on every run, which consumes more processing time and is slower for large datasets. However, full-replace with a date-range filter is the only reliable mechanism to keep row count controlled over time. For datasets expected to grow beyond 50M rows per year, design for full-replace with a rolling window from the start; retrofitting a trim mechanism after the dataset is live is disruptive.

**Single combined dataflow vs. modular flows:** A single dataflow containing all related objects is simpler to monitor and costs one quota slot. However, a single large dataflow is harder to debug when one object's data changes unexpectedly, because all objects must re-run together. A reasonable middle ground is to group objects by domain (sales objects together, service objects together) into 2–3 combined flows rather than one monolith or ten single-object flows.

## Anti-Patterns

1. **Unbounded append-mode datasets** — Loading records in append mode without any trim or filter strategy creates a dataset that grows without limit. Once the 500M org ceiling is hit, all dataset writes in the org fail, not just the oversized dataset. Design for row-count management before the first production run, not after the failure.

2. **Assuming date column type from source object type** — CRM Analytics does not automatically inherit the Salesforce field type. Practitioners who assume that a Salesforce Date field will arrive as a Date column in the dataset will build dashboards that silently return no data for date-based charts and filters. Explicit schema declarations are mandatory, not optional.

3. **One dataflow per object with high-frequency schedules** — Scheduling individual single-object dataflows at hourly or sub-hourly intervals to "maximize freshness" rapidly saturates the 60-run quota. This leaves no room for managed-package flows, recipe jobs, or the ad-hoc manual runs needed during troubleshooting.

## Official Sources Used

- CRM Analytics REST API Developer Guide (Spring '26) — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm
- Dataset Capacity and Limits — https://help.salesforce.com/s/articleView?id=sf.bi_limits.htm
- Transformations for CRM Analytics Dataflows — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_dataflow_transformations.htm
- Date Functions in SAQL Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_saql.meta/bi_dev_guide_saql/bi_saql_date_functions.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
