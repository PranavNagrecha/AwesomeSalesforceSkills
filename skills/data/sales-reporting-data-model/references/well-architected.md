# Well-Architected Notes — Sales Reporting Data Model

## Relevant Pillars

- **Performance** — Reporting Snapshots decouple data-intensive pipeline analysis from live Opportunity queries, preventing report timeout on large datasets. Historical Trend Reporting uses an internal data store that does not hit standard query limits. CRTs with "without" joins that span large object volumes can be slow; index filter fields and use date-scoped filters to maintain acceptable run times.

- **Reliability** — Reporting Snapshot runs depend on: (1) the source report being below the 2,000-row cap, (2) the Running User being active, and (3) the schedule executing on time. Any of these failure modes silently corrupts the historical archive. Operational monitoring of snapshot run history is a reliability requirement, not optional.

- **Scalability** — Reporting Snapshot target objects grow unboundedly. A daily snapshot of 1,500 records creates over half a million records per year. Storage limits, report performance on large target objects, and data retention policies must be planned at design time. HTR has a hard 8-field cap and 3-month retention — it does not scale to long-term history or high-cardinality field tracking. CRT multi-object chains of 4 objects with no indexed join fields degrade as object volumes grow.

- **Operational Excellence** — Each reporting mechanism requires ongoing operational care: monitoring Snapshot run success, maintaining HTR field priority as business requirements evolve, and keeping CRT deployed status current. Undocumented reporting architectures accumulate invisible debt — retention policies, Running User dependencies, and field-cap trade-offs must be documented for future admins.

- **Security** — Reporting Snapshot Running Users must have access to all data in scope — which can mean bypassing normal row-level sharing if the user is an admin or has "View All Data." The target custom object then needs its own OWD and sharing rules to control who can see the accumulated pipeline history. Avoid granting wide data access in the Running User account without a documented approval.

## Architectural Tradeoffs

**HTR vs. Reporting Snapshots:** HTR is lower-maintenance and zero storage cost, but is bounded by 3-month retention, 8 tracked fields, and no API access. Reporting Snapshots require ongoing operational management (monitoring, storage growth, Running User hygiene) but scale to multi-year history and arbitrary field breadth. For most production orgs, both are used in tandem: HTR for near-term operational trending, Snapshots for long-term archival.

**Reporting Snapshots vs. CRM Analytics / Data Cloud:** Reporting Snapshots are native, declarative, and require no additional licenses. CRM Analytics and Data Cloud offer richer time-series modeling, larger data volumes, and real-time ingestion but require separate licensing and more implementation investment. For orgs already licensed for CRM Analytics, the native Snapshot approach may be redundant.

**CRTs vs. Standard Report Types:** Native CRTs are part of the platform and do not require package management. They are the right tool for multi-object joins and gap analysis. Standard report types should be used wherever they cover the requirement — CRTs add maintenance overhead (deployment status, field layout curation) that is only justified when standard types cannot meet the need.

## Anti-Patterns

1. **Using Text field type for monetary values in Snapshot target objects** — Monetary values stored as Text cannot be aggregated (SUM, AVG) in reports, sort lexicographically instead of numerically, and break multi-currency comparisons. All monetary Snapshot fields must be Currency type. This is a design-time error that requires data migration to fix after records have accumulated.

2. **Running a Reporting Snapshot with an employee user as the Running User** — When the employee leaves, the snapshot silently fails. All Reporting Snapshot Running Users should be a dedicated integration user or service account not tied to any individual employee's employment status.

3. **Activating HTR late in the org lifecycle and expecting historical data** — HTR data collection starts at activation. Enabling it after a business problem is discovered means the historical window for investigation pre-dates activation and is simply unavailable. The correct pattern is to activate HTR at org go-live or at the start of the Sales Cloud rollout.

## Official Sources Used

- Report on Historical Data with Reporting Snapshots — https://help.salesforce.com/s/articleView?id=sf.data_about_analytic_snap.htm&type=5
- Historical Trending — https://help.salesforce.com/s/articleView?id=sf.reports_historical_trending_overview.htm&type=5
- Opportunities with Historical Trending Report — https://help.salesforce.com/s/articleView?id=sf.reports_historical_trending_create.htm&type=5
- Custom Report Types — https://help.salesforce.com/s/articleView?id=sf.reports_report_type_setup.htm&type=5
- Salesforce Well-Architected — https://architect.salesforce.com/well-architected/overview
- Salesforce Object Reference (OpportunityHistory) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunityhistory.htm
