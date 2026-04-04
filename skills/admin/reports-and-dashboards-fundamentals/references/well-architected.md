# Well-Architected Notes — Reports and Dashboards Fundamentals

## Relevant Pillars

### Security

Reports and dashboards are a primary path through which users access aggregated data. The "running user" configuration on a dashboard is a security control, not just a UX setting. A static dashboard running as a user with View All Data exposes every record in the org to anyone who can view that dashboard — including portal users and community users if the dashboard is shared incorrectly. Key security principles:

- Default to "Run as logged-in user" (dynamic dashboard) to ensure record-level security is enforced per viewer.
- Audit static dashboard running users: any running user with elevated sharing access creates an implicit data elevation path.
- Report subscriptions send the running user's data to all recipients — treat subscription delivery as a broadcast of the owner's data, not personalized data.
- Folder permissions are the access control layer for reports and dashboards. A report in a public folder is visible to all users who have access to that folder. Review folder sharing before deploying sensitive reports.

### Operational Excellence

Reports and dashboards degrade without governance. An org accumulates private reports, stale dashboards, and broken subscriptions over time:

- Reports in private folders are invisible to the team and are effectively lost when the creator leaves.
- Dashboard last-refresh timestamps older than 30 days indicate abandoned dashboards consuming storage.
- Hard-coded date filters become stale silently — no error, just wrong data.
- Broken subscriptions continue to attempt delivery and generate bounce errors.

Operational excellence requires a regular (quarterly) report and dashboard audit: identify stale, private, and orphaned assets and clean them up.

### User Experience

A dashboard with the wrong component type for its data degrades decision quality. Core UX principles:

- Use Metric components for single KPIs stakeholders check at a glance.
- Use Bar/Column charts for comparisons across a limited set of categories (< 10 categories).
- Use Line charts for trends over time.
- Use Gauge components when a target is known and progress matters (e.g., quota attainment).
- Do not overload a dashboard with more than 8–10 components — cognitive overload reduces dashboard adoption.
- Dynamic dashboards improve relevance but require that users understand they are seeing their own data, not org-wide data.

### Performance

- Reports on objects with millions of records can be slow or timeout if filters are too broad. Always apply at least one selective filter (date range, owner, record type) to limit the scan.
- Cross-filters add join operations to the query — use them sparingly.
- Joined reports execute multiple queries — each block is a separate report execution. Joining 5 blocks on a large org can be slow.
- Dashboard refresh is bounded by the slowest source report. A dashboard with one slow report delays all component updates.

### Reliability

- Relative date filters are more reliable than absolute date filters — they do not require manual updates and do not silently become stale.
- CRT field layouts should be kept lean — the fewer fields in the layout, the less risk of breaking field references when objects are modified.
- Summary formulas that reference PREVGROUPVAL or PARENTGROUPVAL break silently if the grouping level they reference is removed from the report. Test formulas after any structural report change.

---

## Architectural Tradeoffs

**Dynamic vs Static Dashboard**: Dynamic dashboards enforce record-level security per viewer but cannot be scheduled or subscribed to. Static dashboards can be scheduled but introduce data-elevation risk if the running user has broad access. The correct choice depends on whether viewers should see personalized or shared data, and whether scheduled delivery is required.

**Summary Report vs Matrix Report**: Summary reports are simpler to build and maintain. Matrix reports support crosstab analysis but are harder to interpret with many grouping levels. Prefer Summary unless a true two-axis comparison (rows AND columns grouped) is the core business need.

**Standard Report Type vs Custom Report Type**: Standard report types require no maintenance and work immediately. Custom report types require admin creation, a deployment window, and ongoing field-layout maintenance. Use standard types unless they genuinely cannot support the required objects or join semantics.

**Report Subscription vs Dashboard**: Subscriptions deliver results by email on a schedule. Dashboards require the user to log in. Subscriptions are better for stakeholders who do not log in regularly; dashboards are better for daily active users. Do not duplicate delivery — if a dashboard is already available, a subscription emailing the same data creates redundancy and maintenance overhead.

---

## Anti-Patterns

1. **Static Dashboard as a Security Shortcut** — Running a dashboard as a high-privilege user (e.g., "System Admin" or a user with View All Data) because it is easier than setting up proper sharing. Every dashboard viewer sees admin-level data. This violates the principle of least privilege and is a significant data exposure risk. Use dynamic dashboards or build the correct sharing model instead.

2. **Report-as-Export Without Governance** — Creating tabular reports with no groupings, no description, and no folder assignment purely to export data. These accumulate in private folders, are duplicated repeatedly, and become unmaintainable. Establish a "Data Exports" shared folder with clear naming conventions and a review cycle.

3. **Custom Report Type for Every Edge Case** — Creating a new CRT every time a standard type seems insufficient, without first checking if a cross-filter, bucket field, or formula column on the standard type can solve the problem. CRTs multiply maintenance overhead. Exhaust standard-type options first.

---

## Official Sources Used

- Salesforce Help: Reports and Dashboards Overview — https://help.salesforce.com/s/articleView?id=sf.reports_dashboards.htm
- Salesforce Help: Get Started with Reports — https://help.salesforce.com/s/articleView?id=sf.reports_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help: Dynamic Dashboards — https://help.salesforce.com/s/articleView?id=sf.analytics_dashboards_dynamic.htm
- Salesforce Help: Custom Report Types — https://help.salesforce.com/s/articleView?id=sf.reports_defining_report_types.htm
- Salesforce Help: Joined Reports — https://help.salesforce.com/s/articleView?id=sf.reports_joined.htm
- Salesforce Help: Bucket Fields in Reports — https://help.salesforce.com/s/articleView?id=sf.reports_bucketing_about.htm
- Salesforce Help: Report Subscriptions — https://help.salesforce.com/s/articleView?id=sf.reports_subscribe_overview.htm
