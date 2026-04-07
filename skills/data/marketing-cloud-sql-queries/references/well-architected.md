# Well-Architected Notes — Marketing Cloud SQL Queries

## Relevant Pillars

- **Performance** — The 30-minute hard timeout and full-table scan behavior make query performance the highest-risk failure mode. Every query must be designed around indexed column filters and bounded date ranges. Performance is not optional — an unoptimized query does not degrade gracefully; it fails completely and leaves the target DE in an unknown state.
- **Reliability** — The silent zero-row wipe risk (Overwrite action + empty result set) is a reliability threat. Well-architected automations default to **Update** action on production DEs, test in Query Studio before scheduling, and monitor Automation Studio activity history for unexpected empty-result runs.
- **Operational Excellence** — Query Activities embedded in Automation Studio are production data pipelines. They must be documented with their date range assumptions, target DE action setting, expected row counts, and retention window constraints. Undocumented automations become unmaintainable and create data quality incidents when inherited.
- **Security** — System data views expose send, open, and click event data for all subscribers in the business unit. Access to Query Activity authoring in Automation Studio should be restricted to roles that are authorized to access subscriber-level engagement data. Marketing Cloud role-based access controls govern who can create or edit Query Activities.
- **Scalability** — The 18-million-row-per-run limit and the 30-minute timeout define the upper bound of a single Query Activity. Designs that approach these limits must be decomposed into multiple Query Activities with intermediate staging DEs, or the query scope must be partitioned (e.g., by date range or subscriber segment).

## Architectural Tradeoffs

**Overwrite vs. Update action:** Overwrite provides clean-slate semantics and simpler downstream logic (no concern about stale rows), but introduces the silent-wipe risk on zero-result runs. Update is safer for production DEs but requires a Primary Key field on the target DE and careful handling of rows that should be deleted (they persist unless explicitly removed by a separate Delete Activity). Choose Overwrite only for staging DEs that are fully rebuilt each cycle; use Update for any DE where data continuity matters.

**Single large query vs. multiple scoped queries:** A single query covering a long date range is simpler to maintain but approaches the timeout limit as data volume grows. Decomposing into multiple queries (e.g., one per week, combined via an intermediate DE) increases operational complexity but provides headroom for growth and allows partial results to be retained if one activity fails.

**System data views vs. pre-extracted tracking DEs:** Querying system data views directly is always fresh (up to ~6 months) but is constrained by retention and timeout limits. Maintaining a continuously updated custom tracking DE (populated by daily Query Activities) allows historical queries beyond 6 months and supports more complex joins without performance risk. The tradeoff is operational overhead to maintain the extraction pipeline.

## Anti-Patterns

1. **Unbounded system data view queries** — Querying _Sent, _Open, or _Click without a date range filter causes a full-table scan that grows without bound as the account accumulates history. This is the single most common cause of query timeouts. Every system data view query must include `WHERE EventDate >= DATEADD(DAY, -N, GETDATE())` with N no larger than 180.

2. **Using Overwrite action on shared or master DEs** — Setting the Query Activity action to Overwrite on a DE that is also written by other automations, imports, or journey activities creates a race condition. Whichever process runs last wins, and a zero-row Overwrite silently destroys all other processes' contributions. Master profile DEs and suppression lists must never use Overwrite.

3. **Generating SQL with standard SQL dialect assumptions** — Using MySQL or PostgreSQL syntax (e.g., `NOW()`, `LIMIT`, `DATE_FORMAT()`, CTEs, window functions) in a Marketing Cloud Query Activity produces runtime errors. The T-SQL-like dialect of Marketing Cloud SQL is narrow — only the constructs explicitly documented in the SF Help SQL Reference are available.

## Official Sources Used

- SQL Query Activity — Build a Query Activity: https://help.salesforce.com/s/articleView?id=sf.mc_as_using_query_activity.htm&type=5
- Marketing Cloud SQL Reference: https://help.salesforce.com/s/articleView?id=sf.mc_as_sql_reference.htm&type=5
- Optimizing Query Activity Performance: https://help.salesforce.com/s/articleView?id=sf.mc_as_query_activity_best_practices.htm&type=5
- System Data Views Overview: https://help.salesforce.com/s/articleView?id=sf.mc_as_system_data_views.htm&type=5
- Automation Studio Activities — Query: https://help.salesforce.com/s/articleView?id=sf.mc_as_query_activity_available_data.htm&type=5
