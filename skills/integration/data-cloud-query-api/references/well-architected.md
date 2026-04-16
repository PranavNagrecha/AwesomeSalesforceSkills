# Well-Architected Notes — Data Cloud Query API

## Relevant Pillars

- **Security** — Data Cloud tokens carry org-wide data access scopes. Token storage, rotation, and scope minimization are critical. The connected app's OAuth scopes must include `cdp_api` and should be restricted to the minimum required DMOs.
- **Performance** — Query V2 is synchronous but not unbounded. Large queries should use pagination tuned to avoid cursor expiry. Query Connect API should be preferred for bulk exports to avoid 1-hour time window constraints.
- **Scalability** — Query API is suited for targeted reads and integrations but is not a bulk analytics engine. High-frequency querying should be cached or offloaded to CRM Analytics Direct Data connections.
- **Reliability** — Cursor expiry after 3-minute inter-batch gaps is a reliability risk for slow consumers. Pipelines must account for cursor failure and implement retry with fresh query submission.
- **Operational Excellence** — Monitor token expiry independently from standard Salesforce session lifetimes. Log `dcInstanceUrl` per environment — it can change during Data Cloud region migrations.

## Architectural Tradeoffs

**Query V2 vs. Query Connect:** Query V2 is simpler to implement (synchronous, standard REST) but imposes a 1-hour fetch window and per-batch row limits. Query Connect is more complex (async polling model) but supports unlimited rows and 24-hour result availability. Choose based on result set size and downstream consumer latency.

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
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
