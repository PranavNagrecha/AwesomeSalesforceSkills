# Well-Architected Notes — SOQL Relationship Queries

## Relevant Pillars

- **Performance Efficiency** — Relationship queries are the primary mechanism for eliminating N+1 SOQL patterns. A parent-to-child subquery replaces a per-row child query inside a loop, reducing query count from O(n) to O(1). Child-to-parent dot notation similarly avoids a separate parent lookup. However, relationship queries that return large row totals (outer rows + inner rows > 50,000) will hit governor limits just as flat queries do; careful limit and chunk planning is required at scale.
- **Reliability** — Failing to null-guard `getSObjects()` results causes `NullPointerException` errors in production triggers and batch jobs. The reliability pillar demands defensive coding for all platform APIs that return null rather than empty collections. Handling the TYPEOF ELSE branch and checking `getSObjectType()` before casting prevents `ClassCastException` errors that surface as unhandled exceptions.
- **Security** — Relationship queries inherit the field-level security and sharing enforcement of the running user context. Use `WITH USER_MODE` or `WITH SECURITY_ENFORCED` to enforce FLS and CRUD on both the outer object and the inner subquery fields when queries run in system context. Cross-object field access via dot notation is subject to the same FLS rules as direct field access.
- **Operational Excellence** — Relationship query structure (subquery count, traversal depth) should be reviewed during code review and tested against governor limits in dedicated bulk test scenarios. Documenting the child relationship name used in both SOQL and `getSObjects()` calls is important for maintainability, especially for custom object relationships where the name can be changed in Setup.

## Architectural Tradeoffs

**Single relationship query vs multiple flat queries:** A single query with subqueries minimizes SOQL count (critical for triggers processing large batches) but risks hitting the 50,000 total row limit faster than multiple targeted flat queries with specific WHERE filters. Choose based on expected data volume per parent record.

**TYPEOF vs post-query split:** `TYPEOF` in SOQL is expressive and type-safe at query time but is a developer preview feature with deployment risk. The alternative — querying only the polymorphic ID field and then issuing type-specific lookups — uses additional SOQL but is fully GA. For production-critical code, prefer the post-query split pattern unless `TYPEOF` is confirmed GA in the target org.

**Subquery with LIMIT vs full child set:** Adding `LIMIT 200` to a subquery guards against large child sets but silently truncates data. If all child records must be processed, use a separate child query with a parent ID filter and process in batch.

## Anti-Patterns

1. **N+1 SOQL in Triggers** — Issuing a child SOQL query inside a `for` loop over trigger records is the most commonly cited Apex performance anti-pattern. For every 200-record batch in a trigger, this can exhaust the 100-query limit before processing completes. Use parent-to-child subqueries to bundle child fetches into the initial query.

2. **Unchecked getSObjects() Iteration** — Calling `getSObjects()` without a null guard and iterating the result directly is a reliability anti-pattern. It passes unit tests that always provide child data but silently explodes in production when a parent record exists without children. Every `getSObjects()` call site must have an explicit null check.

3. **Mixing Subqueries into Bulk API Paths** — Including parent-to-child subqueries in SOQL that may be executed through the Bulk API (e.g., external ETL tools, some batch configurations) causes runtime failures that are difficult to diagnose because the same query works in interactive Apex. Separate Bulk API query paths must use flat queries only.

## Official Sources Used

- SOQL and SOSL Reference — Using Relationship Queries: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_relationships_query_using.htm
- SOQL and SOSL Reference — Understanding Relationship Query Limitations: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_relationships.htm
- Apex Developer Guide — Polymorphic Relationships: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_polymorphic_relationships.htm
- Apex Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
