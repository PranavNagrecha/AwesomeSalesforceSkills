# Well-Architected Notes — Marketing Cloud Data Views

## Relevant Pillars

- **Performance** — System data views are the highest-risk area for query timeout failures in Marketing Cloud. The 30-minute Query Activity hard limit applies to all data view queries. Queries that do not include a date-scoped WHERE clause on an indexed field (EventDate, JobID, SubscriberKey) run as full-table scans across up to 6 months of engagement data. On accounts with large send volumes, unscoped queries routinely hit the timeout. The WAF Performance pillar requires that data access patterns are designed around platform constraints — here, that means mandatory date scoping, composite join keys, and deduplication logic baked into every data view query.

- **Reliability** — Data view queries that succeed with zero rows and no error — because the requested date range has aged out — create a silent reliability failure. Downstream automation that depends on the populated target DE (suppression lists, sendable audiences, reporting DEs) will proceed with stale or empty data. Reliable architectures account for the ~6-month retention window by implementing incremental staging jobs that continuously persist engagement data to custom DEs, ensuring the queryable dataset does not depend on aging system view data.

- **Operational Excellence** — System data views are the only platform-native source of engagement event data in Marketing Cloud. Operational health depends on consistently scheduled Query Activities that keep custom DEs current. Monitoring must check both query success status and target DE row counts — a query can succeed (exit code 0) while writing zero rows due to empty results from aged-out data. Automation Studio activity history and email alerting on automation failure are minimum operational controls.

- **Security** — System data views contain PII (subscriber email addresses, click event metadata, status). All output DEs that store data view results must follow the same PII governance as the source views: restricted sharing, appropriate retention policies, and data classification labels. Access to Query Activities in Automation Studio should be role-controlled. Data views themselves cannot have row-level security applied — the only control is who can create and run Query Activities.

- **Scalability** — The ~6-month rolling window is a fixed platform constraint that does not scale with account size. High-volume senders generate more rows in system data views, making date-unscoped queries more likely to timeout. Scalable architectures incrementally stage engagement data to custom DEs on a short cadence (daily or weekly) rather than relying on wide-window queries against system views at the point of need.

## Architectural Tradeoffs

**Real-time vs. Batch Access:** System data views provide no real-time access path. All data retrieval is batch, scheduled, and asynchronous via Automation Studio. Architectures that need near-real-time engagement data (e.g., triggered sends based on recent opens) must use Marketing Cloud's Journey Builder behavioral triggers or transactional event APIs rather than polling data views.

**Retention Window vs. Historical Analysis:** The ~6-month rolling window means long-term engagement analytics must be built on a custom Data Extension layer that is continuously populated. Teams that need 12-month or multi-year views must invest in incremental staging infrastructure from day one. Retrofitting this after the retention window has passed means the historical data is permanently lost.

**Composite Key Correctness vs. Query Simplicity:** Cross-view joins require `JobID + SubscriberKey` as composite key. Simpler single-key joins (EmailAddress or SubscriberKey alone) produce incorrect results with no query-level error. The architectural principle here is that correctness cannot be compromised for simplicity — the composite key pattern must be enforced as a team standard, ideally through code review or query templates.

## Anti-Patterns

1. **API Polling for Engagement Data** — Routing REST or SOAP API calls toward system data view data is architecturally broken: it is not possible. Architectures that rely on the Tracking Events REST API as a substitute for data views receive event data from a different store with different schema, different retention, and no SQL aggregation. The correct pattern is to stage data view results into custom DEs via scheduled Query Activities, then expose those DEs through the Data Extension REST API.

2. **Wide-Window Queries Without Incremental Staging** — Running a single Query Activity with a 180-day (maximum window) date range is the anti-pattern for any production use case. It is unreliable (close to the timeout boundary for large accounts), operationally fragile (any single query failure means no data), and architecturally brittle (the window cannot be extended beyond 6 months). The correct pattern is a narrow-window incremental query (e.g., 7 days) that appends to a persistent staging DE with Query Activity action set to Update.

3. **Storing Only SubscriberKey Without JobID in Engagement Staging DEs** — A staging DE that records engagement events without preserving `JobID` cannot be correctly joined back to `_Job` for enrichment, nor to other event views for multi-event correlation. Any custom DE that stages system data view records must include `JobID` as a field from the start, or the join patterns described in this skill become impossible to reconstruct.

## Official Sources Used

- Data Views Overview — https://help.salesforce.com/s/articleView?id=sf.mc_as_data_views.htm
- Sent Data View — https://help.salesforce.com/s/articleView?id=sf.mc_as_data_view_sent.htm
- Query Activity — https://help.salesforce.com/s/articleView?id=sf.mc_as_query_activity.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
