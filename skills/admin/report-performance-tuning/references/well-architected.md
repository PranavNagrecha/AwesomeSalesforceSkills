# Well-Architected Notes — Report Performance Tuning

## Relevant Pillars

- **Performance** — This is the primary pillar. Report performance is determined by filter selectivity, object volume, report type join complexity, and execution context (interactive vs. async). Failing to apply selective filters on large objects is the single most common cause of report timeouts. The Analytics API async pattern is the platform-aligned approach for processing large result sets without degrading the interactive experience for other users.

- **Operational Excellence** — Reports and dashboards are operational monitoring tools. When they time out or return stale data, org operators lose visibility into business state. Documenting required filters in report descriptions, scheduling refreshes during off-peak windows, and building async extraction pipelines for large datasets are all operational discipline practices that keep the reporting layer reliable.

- **Reliability** — Dashboard components that time out silently show "data unavailable" rather than an error, creating a false sense of completeness. Subscriptions that fail due to timeout deliver no email, and the subscriber may not know the failure occurred. Building reports that consistently complete within timeout thresholds — through filter enforcement and component count management — is a reliability requirement, not a nice-to-have.

- **Security** — Report subscriptions and "run as specified user" dashboards expose data at the sharing level of the running user, not the viewer. Using "run as specified user" on a dashboard effectively grants every viewer access to that user's data slice. This is a security concern when that user has broader access than the viewer should have. Performance tuning must not introduce sharing model bypasses as a side effect (e.g., removing an Owner = Current User filter to improve speed).

- **Scalability** — Reports designed without volume awareness become a scalability liability. An approach that works at 100K records may fail at 5M records as the org grows. Scalable report design mandates selective filters from day one, CRT complexity minimization, and async processing paths for any report that will grow with data volume.

## Architectural Tradeoffs

**Filter coverage vs. user flexibility:** Mandatory selective filters (especially date ranges) reduce query scope but also reduce what users can see in a single report run. The tradeoff is between performance and breadth of insight. Resolution: provide multiple saved reports with different pre-set date ranges (current quarter, last 90 days, this fiscal year) rather than a single open-ended report. This preserves usability while keeping each query selective.

**Async API vs. interactive report:** Async API execution returns complete datasets but requires engineering effort to build, schedule, and maintain the polling/parsing pipeline. Interactive reports are self-service but are capped at 2,000 rows and subject to timeouts. The tradeoff is engineering cost vs. self-service accessibility. Resolution: use async pipelines only when the row count requirement genuinely exceeds 2,000 or when the report is part of a data integration workflow, not for standard business user access.

**CRT flexibility vs. query complexity:** Custom report types allow spanning multiple objects with configurable join behavior, enabling reporting on relationships that standard types do not expose. Each additional object and each outer join increases query complexity. The tradeoff is reporting capability vs. query performance. Resolution: use CRTs only when standard types genuinely cannot serve the use case, and audit CRT join types to use inner joins wherever the outer join behavior is not required.

**Dashboard component richness vs. refresh performance:** More components per dashboard provide richer at-a-glance information but multiply the number of report queries on every refresh cycle. A 30-component dashboard runs 30 separate report queries on refresh. The tradeoff is information density vs. refresh speed and system load. Resolution: limit dashboards to 20 or fewer components and split by audience or function when richer coverage is needed.

## Anti-Patterns

1. **Filter-free reports on large objects** — Building a report on a high-volume object (Opportunity, Case, Activity) with no date range, owner, or record type filter causes a full table scan on every execution. As org data grows, this report degrades and eventually times out. The anti-pattern is often introduced because it "worked fine" when the org was small. Resolution: treat selective filters as mandatory structural constraints, not optional parameters.

2. **Using UI export to extract large datasets** — Exporting reports via the Lightning Report UI to get "all the data" silently truncates at 2,000 rows. Any downstream process (spreadsheet analysis, BI feed, compliance export) built on this export is working with incomplete data without any indication of truncation. Resolution: use the Analytics API async endpoint for any extraction requirement that may exceed 2,000 rows.

3. **Oversized CRTs retained for historical compatibility** — Custom report types are often built with maximum object coverage "just in case." Over time, reports built on these CRTs only use fields from 2 of the 4 objects, but the CRT is never simplified because it is unclear what depends on it. The dead join overhead accumulates as data grows. Resolution: periodically audit CRT object usage against active reports and trim unused objects from the relationship chain.

## Official Sources Used

- Salesforce Help: Improve Report Performance — https://help.salesforce.com/s/articleView?id=sf.reports_improve_performance.htm
- Salesforce Analytics API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_analytics.meta/api_analytics/sforce_analytics_rest_api_intro.htm
- Salesforce Help: Reports and Dashboards Overview — https://help.salesforce.com/s/articleView?id=sf.reports_overview.htm
- Salesforce Help: Custom Report Types — https://help.salesforce.com/s/articleView?id=sf.reports_custom_report_types_overview.htm
- Salesforce Help: Dynamic Dashboards — https://help.salesforce.com/s/articleView?id=sf.dashboards_dynamic_about.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
