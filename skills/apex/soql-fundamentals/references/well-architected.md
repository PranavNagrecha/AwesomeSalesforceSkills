# Well-Architected Notes — SOQL Fundamentals

## Relevant Pillars

- **Security** — Every SOQL query in Apex runs in system mode by default, bypassing FLS and object-level security. Queries must explicitly enforce sharing and field permissions using `WITH USER_MODE` (preferred, fewer limitations) or `WITH SECURITY_ENFORCED`. Failing to enforce access in user-facing code is a common vulnerability.

- **Reliability** — Queries without ORDER BY produce non-deterministic results that are consistent in sandbox but fail silently in production. OFFSET limitations (max 2,000 rows) and the 100 SOQL queries-per-transaction limit are reliability boundaries that must be designed for, not discovered in production.

- **Scalability** — SOQL has hard governor limits: 100 queries per synchronous transaction, 50,000 rows per transaction, and a 100,000-character query length limit. Queries that work at 10,000 records fail at 1,000,000. Aggregate functions, selective WHERE clauses, and relationship queries built correctly scale without code changes; ad-hoc loops-in-loops do not.

- **Operational Excellence** — SOQL written in triggers must be bulkified: a single SOQL inside a for-loop is one of the most commonly cited performance anti-patterns in Salesforce Apex. Storing SOQL queries outside of for-loops, using collections, and leveraging Maps for lookups are fundamental operational practices.

## Architectural Tradeoffs

**Child-to-parent vs. two queries:** A child-to-parent traversal (dot notation) retrieves parent data in one query but flattens the result. If you need the parent object along with multiple related children, a parent-to-child subquery keeps results structured but has a 20-subquery limit per SELECT statement. Choose based on whether you need the data flat (child-to-parent) or hierarchical (parent-to-child).

**OFFSET pagination vs. queryMore():** OFFSET is simple to implement but caps at 2,000 rows and has no server-side cursor — the underlying data can change between page requests. `queryMore()` / `nextRecordsUrl` uses a server-side cursor that is stable for up to 15 minutes. For production UIs with large data sets, cursor-based approaches are more reliable.

**Aggregate in SOQL vs. aggregate in Apex:** Aggregating on the server (GROUP BY + aggregate function) uses zero Apex heap and CPU for the aggregation step. Aggregating in Apex code consumes heap proportional to the number of records loaded. At scale, server-side aggregation is always preferred for reporting use cases.

## Anti-Patterns

1. **SOQL inside a for-loop** — Placing a SOQL query inside an iteration loop multiplies the query count by the number of iterations, quickly exhausting the 100-query limit in synchronous Apex. Replace with a single query before the loop, loading results into a Map keyed by ID for efficient lookup inside the loop.

2. **SELECT * simulation via dynamic field enumeration** — Dynamically building a field list from `Schema.getGlobalDescribe()` to retrieve all fields bypasses FLS, risks `QUERY_TOO_COMPLICATED` on large objects, and introduces SOQL injection risk if any user data is concatenated. Use `FIELDS(STANDARD)` / `FIELDS(CUSTOM)` with LIMIT, or enumerate specific needed fields.

3. **Unbounded queries in triggers** — Trigger code that queries related records without a selective WHERE clause or LIMIT can return 50,000 rows per transaction, blocking other DML and consuming the entire row budget. Always add WHERE conditions and LIMIT to trigger-context queries; use Batch Apex for bulk data operations.

## Official Sources Used

- SOQL and SOSL Reference (Version 66.0, Spring '26) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm
  - Used for: SELECT syntax, all clause definitions, relationship query rules, aggregate function behavior, LIMIT/OFFSET limits, FIELDS() keyword behavior, date literal reference
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
  - Used for: inline SOQL syntax in Apex, Database.query() dynamic SOQL, FOR UPDATE locking, governor limits, WITH USER_MODE vs WITH SECURITY_ENFORCED guidance
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
  - Used for: framing scalability and security pillars
