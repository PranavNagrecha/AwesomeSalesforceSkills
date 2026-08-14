# Well-Architected Notes — Data Cloud Query API

## Relevant Pillars

- **Security** — Data Cloud tokens carry org-wide data access scopes. Token storage, rotation, and scope minimization are critical. The connected app's OAuth scopes must include `cdp_api` and should be restricted to the minimum required DMOs.
- **Performance** — Query V2 is synchronous but not unbounded. Large queries should use pagination tuned to avoid cursor expiry. Query API V3 (ADAPTIVE or ASYNC) or the Query Connect API should be preferred for bulk exports to avoid the 1-hour time window; neither carries V2's inter-batch cursor expiry.
- **Scalability** — Query API is suited for targeted reads and integrations but is not a bulk analytics engine. High-frequency querying should be cached or offloaded to CRM Analytics Direct Data connections.
- **Reliability** — Cursor expiry after 3-minute inter-batch gaps is a reliability risk for slow consumers. Pipelines must account for cursor failure and implement retry with fresh query submission.
- **Operational Excellence** — Monitor token expiry independently from standard Salesforce session lifetimes. Log `dcInstanceUrl` per environment — it can change during Data Cloud region migrations.

## Architectural Tradeoffs

**Query V2 vs. Query Connect:** Query V2 is simpler to implement (synchronous, standard REST) but imposes a 1-hour fetch window and per-batch row limits. Query Connect is more complex (async polling model) but supports unlimited rows and 24-hour result availability. Choose based on result set size and downstream consumer latency.

**Query API V3 vs. V1/V2:** V3 buys standardized SQLSTATE errors, status/metadata/cancel endpoints, and chunk-based retrieval without the V2 cursor's 3-minute expiry. It costs a rewrite of both the retrieval loop and the error parser, since it has no synchronous mode and renames unaliased columns. With no published V1/V2 retirement date, the honest posture is: new integrations start on V3, existing V2 integrations migrate when they need what V3 adds, not on a deadline that does not exist.

**`sfsqlquery` vs. `ConnectApi.CdpQuery` in Apex:** `sfsqlquery` is the recommended surface for new development and removes two categories of bespoke code — chained-Queueable pagination (`SqlQueueable`) and untestable Data 360 calls (`SqlTester`). The constraint is the class's `.cls-meta.xml` `apiVersion`: below 67.0, `ConnectApi.CdpQuery` is the only option, so raising `apiVersion` is a prerequisite of the migration rather than a follow-up to it.

**Query API vs. Direct Data (CRM Analytics):** For analytics and dashboarding, CRM Analytics Direct Data connections query DMOs natively without requiring custom token flows. Reserve Query API for programmatic integrations and ETL pipelines.

**Calculated Insights vs. Raw DMO SQL:** Calculated Insights encapsulate complex aggregations and are precalculated — they are faster to query but lag real-time by a batch cycle. Raw DMO SQL reflects the latest unified state but may be slower for aggregations.

## Anti-Patterns

1. **Reusing Standard Salesforce OAuth Tokens for Data Cloud API** — Standard tokens from `/services/oauth2/token` are not valid for Data Cloud Query API. Always exchange at `/services/a360/token`. Skipping this step causes all Data Cloud API calls to fail with 401 and wastes debugging time.

2. **Synchronous Pagination Without Consumer Decoupling** — Processing each page synchronously before fetching the next page risks cursor expiry if processing takes more than 3 minutes per batch. Decouple fetching from processing by buffering pages.

3. **Querying Unpublished Calculated Insights** — Querying a CI that is not yet published or whose last run failed returns empty results silently. Applications built on this pattern appear to work in development (where CIs are published) and break in production (where CI publication is delayed after deployment).

## Official Sources Used

- Data 360 Query Guide — https://developer.salesforce.com/docs/data/data-cloud-query-guide/guide/query-guide-get-started
- Data Cloud Query V2 API Reference — https://developer.salesforce.com/docs/data/data-cloud-query-guide/references/c360a-api-query-v2
- API Limits for Profile, Query, and Calculated Insights — https://developer.salesforce.com/docs/atlas.en-us.c360a_api.meta/c360a_api/c360a_api_limits.htm
- Data 360 Connect API Overview — https://developer.salesforce.com/docs/data/connectapi/overview
- Data 360 Connect API Get Started (Data Cloud → Data 360 rebrand) — https://developer.salesforce.com/docs/data/connectapi/guide/get-started.html
- Boost Data Cloud Integrations with the New Query Connect API (blog) — https://developer.salesforce.com/blogs/2025/08/boost-data-cloud-integrations-with-the-new-query-connect-api
- Migrate to Query API V3 (Data 360 Query Guide) — https://developer.salesforce.com/docs/data/data-cloud-query-guide/references/data-cloud-query-api-reference/query-api-migration.html — confirms "Query API V3 doesn't support synchronous execution", the `nextBatchId` → `queryId` + `chunks`/`rows` move, the `_col0`/`_col1` → `1`/`2` rename for unaliased expressions, the SQLSTATE error model, the three V3-only endpoints, and "Use quoted aliases to guarantee specific casing." Its V1/V2 → V3 table is a **replacement mapping you apply when rewriting a client**, not a statement that the old paths are aliased to V3 at runtime. It publishes no retirement date, and carries no release stamp. (verified 2026-08-14)
- Query Data using Query API (Data 360 REST API Reference) — https://developer.salesforce.com/docs/data/data-cloud-query-guide/references/data-cloud-query-api-reference/c360a-api-queryservices-overview.html — confirms the full V3 endpoint set and that the Connect REST API `ssot/query-sql` surface is documented alongside it rather than replaced by it. Note that this page documents only V3 and the Connect REST paths — V1/V2 have been moved off it. (verified 2026-08-14)
- Legacy Query Services API (Data 360 REST API Reference) — https://developer.salesforce.com/docs/data/data-cloud-query-guide/references/data-cloud-query-api-reference/c360a-api-queryservices-legacy.html — this is where V1/V2 are now documented. Confirms "This page describes the legacy versions of the Data 360 Query API", still lists `POST /api/v1/query`, `POST /api/v2/query` and `GET /api/v2/query/{nextBatchId}`, recommends moving ("For the best query experience, use query services through the Data 360 Connect REST API"), and gives **no deprecation or end-of-life date**. This page — not the migration page — is what supports "leave a working V2 integration alone". (verified 2026-08-14)
- Query Data 360 Data with Apex (Data 360 Query Guide) — https://developer.salesforce.com/docs/data/data-cloud-query-guide/guide/dc-apex-query.html — confirms "For backward compatibility, the ConnectApi.CdpQuery class remains available as a low-level interface that directly mirrors the Connect REST API" and "We recommend using the sfsqlquery namespace for all new development", plus the `SqlStatement.create(...).withWorkloadName(...).execute()` example. (verified 2026-08-13)
- sfsqlquery Namespace (Apex Reference Guide, Summer '26 / API version 67.0) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_namespace_sfsqlquery.htm — confirms the release stamp and exactly six classes: QueryHandle, Row, SqlQueueable, SqlRowIterator, SqlStatement, SqlTester. (verified 2026-08-13)
- sfsqlquery.SqlQueueable Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_sfsqlquery_SqlQueueable.htm — confirms it is an abstract base class for chained Queueable execution with `processDataChunk()` and `chainNextJob(sfsqlquery.QueryHandle)`. (verified 2026-08-13)
- sfsqlquery.SqlTester Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_sfsqlquery_SqlTester.htm — confirms Data 360 SQL response mocking in Apex tests via `clearMocks`, `setMockMetadata`, `setMockRows`, `enqueueMockRows`. (verified 2026-08-13)
- ConnectApi.CdpQuery Static Methods — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ConnectAPI_CdpQuery_static_methods.htm — confirms the exact legacy spellings `queryANSISql`, `queryAnsiSqlV2`, `nextBatchAnsiSqlV2`. (verified 2026-08-13)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
