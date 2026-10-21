# Well-Architected Notes — Report Performance Tuning

## Relevant Pillars

- **Performance** — This is the primary pillar. Report performance is determined by filter selectivity and indexes ("SOQL queries, reports, and list views ... all depend on selectivity and indexes", ldv 264 L225-226), object volume, report type join complexity, and execution context. The Reports and Dashboards REST API returns only the first 2,000 report rows, sync or async (REST API 262, Requirements and Limitations); large result sets belong in a Bulk API 2.0 query (api_asynch 264 L136-137).

- **Operational Excellence** — Reports and dashboards are operational monitoring tools. When they time out or return stale data, org operators lose visibility into business state. Documenting required filters in report descriptions (`Report.description`, api_meta 264 L106706), scheduling refreshes during off-peak windows, and building Bulk API extraction pipelines for large datasets keep the reporting layer reliable.

- **Reliability** — A report that silently stops at 2,000 API rows creates a false sense of completeness. UNVERIFIED (2026-10-21): that dashboard components that time out show "data unavailable" and that failed subscriptions deliver no email — Help-only. Building reports that consistently complete within timeout thresholds — through filter enforcement and component count management — is a reliability requirement.

- **Security** — A `SpecifiedUser` dashboard shows "All users ... data at the access level of one specific running user ... regardless of their own security settings" (api_meta 264 L50170-50174), so it can grant every viewer that user's data slice. UNVERIFIED (2026-10-21): the run-as behaviour of report subscriptions. Performance tuning must not introduce sharing model bypasses as a side effect (e.g., removing an owner scope to improve speed).

- **Scalability** — Reports designed without volume awareness become a scalability liability. Scalable report design mandates selective, indexed filters from day one, CRT complexity minimization (ldv 264 L794-796), and a non-report extraction path for any dataset that will grow past 2,000 rows.

## Architectural Tradeoffs

**Filter coverage vs. user flexibility:** Mandatory selective filters (especially date ranges) reduce query scope but also reduce what users can see in a single report run. Resolution: provide multiple saved reports with different pre-set date ranges (current quarter, last 90 days, this fiscal year) rather than a single open-ended report.

**Bulk API extraction vs. interactive report:** A Bulk API 2.0 query returns complete datasets but requires engineering effort; reports are self-service but return at most 2,000 rows through the API. Async report runs help with the 2-minute API timeout and keep results for 24 hours (REST API 262, Run Reports Synchronously or Asynchronously) — they do not raise the row cap. Resolution: use Bulk API pipelines when the row requirement exceeds 2,000 or the data feeds an integration.

**CRT flexibility vs. query complexity:** Custom report types join up to four objects (api_meta 264 L108487); each additional object and each outer join increases query complexity, and an outer join forbids inner joins later in the chain (L108487-108489). Resolution: use CRTs only when standard types cannot serve the use case, and use inner joins wherever outer join behavior is not required.

**Dashboard component richness vs. refresh performance:** More components per dashboard provide richer at-a-glance information but add report runs on every refresh. UNVERIFIED (2026-10-21): the 20-component guidance and the one-query-per-component model — Help-only. The REST API caps dashboard refreshes at 200 per hour (REST API 262, Requirements and Limitations).

## Anti-Patterns

1. **Filter-free reports on large objects** — Building a report on a high-volume object (Opportunity, Case, Activity) with no selective, indexed filter makes the optimizer perform a full scan (ldv 264 L305-307). Resolution: treat selective filters as mandatory structural constraints, not optional parameters.

2. **Using a report — UI export or Analytics API — to extract large datasets** — The API returns only the first 2,000 report rows, sync or async (REST API 262, Requirements and Limitations); UI export truncation is UNVERIFIED (Help-only). Any downstream process built on a report extract may be working with incomplete data. Resolution: use a Bulk API 2.0 query for any extraction requirement that may exceed 2,000 rows.

3. **Oversized CRTs retained for historical compatibility** — Custom report types are often built with maximum object coverage "just in case." The LDV guide says to minimize the objects and relationships a report queries (ldv 264 L794-796). Resolution: periodically audit CRT object usage against active reports and trim unused objects from the relationship chain.

## Official Sources Used

- Large Data Volumes Best Practices — selectivity and indexes for reports (ldv 264 L225-226), index thresholds (L463, L468), fields indexed by default (L308-309), full scan without an index (L305-307), Reporting best practices (L787-811), multi-join report case (L1240-1260).
- Reports and Dashboards REST API Developer Guide 262 — Requirements and Limitations ("The API returns up to the first 2,000 report rows", 1,200 async and 500 sync runs per hour, 100 columns, 200 dashboard refreshes per hour, 5 report subscriptions per user); Run Reports Synchronously or Asynchronously (2-minute timeout does not apply to async, 24-hour results); Report Error Codes (100-column message); Instances List (`New`/`Running`/`Success`/`Error`) — https://developer.salesforce.com/docs/atlas.en-us.api_analytics.meta/api_analytics/sforce_analytics_rest_api_limits_limitations.htm
- Metadata API Developer Guide — Report fields `crossFilters`, `description`, `scope`, `timeFrameFilter` and `ReportFilter.booleanFilter` (api_meta 264 L106680, L106706, L106812-106829, L107292-107296, L107791-107801); Dashboard `dashboardType` (L50170-50190); ReportType `ObjectRelationship` join limits and `outerJoin` (L108487-108495) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_report.htm
- Apex Developer Guide — Reports and Dashboards API via Apex, Requirements and Limitations: 100 columns, 500 sync / 1,200 async runs per hour, 24-hour async results, "The API returns up to the first 2,000 report rows", 20 custom field filters, 200 dashboard refreshes per hour (apexdev 264 L33669-33694); sync rows count toward the 50,000 SOQL rows limit (L33700-33702); same record count as the UI (L33714-33715).
- Object Reference — `CronJobDetail.JobType` `3` = Dashboard Refresh (obj 264 L86824, L86850); `CronTrigger.CronJobDetailId` (L86903).
- Bulk API 2.0 Developer Guide — bulk queries (api_asynch 264 L136-137), query job resources (L1055-1126).
- Salesforce Help (not corpus) — Improve Report Performance; Reports and Dashboards Limits and Allocations; Cross Filter Considerations; Dynamic Dashboards — https://help.salesforce.com/s/articleView?id=sf.reports_improve_performance.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
