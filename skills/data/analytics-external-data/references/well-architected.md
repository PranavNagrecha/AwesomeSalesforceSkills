# Well-Architected Notes — Analytics External Data

## Relevant Pillars

- **Performance** — The materialized vs. live dataset decision is primarily a performance decision. Materialized datasets (via Data Connectors or External Data API uploads) deliver consistent query performance because CRM Analytics serves queries from its own storage. Live Datasets delegate query execution to the external system — any latency or concurrency issue in that system directly degrades dashboard performance. Choose the path that meets the dashboard SLA under realistic concurrent load.
- **Reliability** — External Data API integration jobs must include status polling and failure alerting. A job that reaches `Failed` status silently leaves the dataset stale. Live Datasets introduce a runtime dependency on an external system — if that system is unavailable, dashboards fail. Materialized datasets decouple dashboard availability from external system availability.
- **Security** — Remote Connection credentials (Snowflake OAuth tokens, BigQuery service account keys) must be rotated regularly and stored using CRM Analytics Named Credentials where supported. External Data API calls must use authenticated session IDs — never hardcode credentials in integration scripts. Review field-level access for sensitive columns in external datasets (e.g., salary, PII) and apply CRM Analytics dataset sharing rules and row-level security predicates.
- **Scalability** — External Data API supports datasets up to 40 GB per job (chunked). Data Connector recipe refresh windows must complete within the CRM Analytics processing timeout. For datasets approaching tens of millions of rows, validate that refresh completes within the scheduled window with room to spare. Live Datasets do not scale with CRM Analytics dataset limits — they scale with the external warehouse's capacity.
- **Operational Excellence** — Data Manager job notifications, External Data API status monitoring, and Recipe failure alerts are non-negotiable for production deployments. Version-control the metadata JSON schema for External Data API jobs — schema changes require intentional dataset version management to avoid breaking dependent dashboards.

## Architectural Tradeoffs

**Materialized (Data Connector / External Data API) vs. Live Dataset:**

| Factor | Materialized | Live Dataset |
|---|---|---|
| Query performance | Fast and consistent | Depends on external system |
| Data freshness | Bounded by refresh schedule | Always current |
| External system dependency | Only during refresh | On every query |
| CRM Analytics storage cost | Consumes dataset storage | None (no local copy) |
| Dashboard availability | Independent of external system | Coupled to external system |
| Incremental load support | Yes (with watermark) | N/A (always queries live) |

**External Data API vs. Data Connector:**

Use the External Data API when the source system has no prebuilt connector or when the integration layer is a custom pipeline (Apex, Python, MuleSoft custom connector). Use Data Connectors for supported warehouses (Snowflake, BigQuery, Redshift) where the prebuilt connector reduces maintenance overhead.

## Anti-Patterns

1. **Live Dataset as a drop-in replacement for a slow-refreshing Data Connector** — Teams switch to Live Datasets when Data Connector refresh windows are too slow, expecting equivalent behavior with better freshness. Live Datasets introduce a runtime dependency that did not exist before. Under concurrent dashboard load, this degrades reliability and shifts the performance bottleneck to the external warehouse. The correct fix for slow refresh is incremental load configuration on the Data Connector recipe, not Live Datasets.

2. **No failure alerting on External Data API jobs** — Integration pipelines push data via the External Data API and consider the job done after setting `Action = Process`. If the job fails (schema mismatch, corrupt chunk, API timeout), the failure is silent — the dataset remains at its previous state. Downstream dashboards show stale data without any visible error. Always poll the `Status` field and surface `Failed` states to an alerting channel.

3. **Using Remote Connections without downstream data artifacts** — Creating a Remote Connection in Data Manager and treating it as evidence that data is flowing. The connection configuration is inert until a Recipe, Dataflow, or Live Dataset references it. This produces an org where Remote Connections exist but no data is actually ingested.

## Official Sources Used

- Analytics External Data API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_ext_data.meta/bi_dev_guide_ext_data/bi_ext_data_overview.htm
- CRM Analytics REST API Developer Guide (Spring '26) — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm
- Connect and Sync Your Data to CRM Analytics — https://help.salesforce.com/s/articleView?id=sf.bi_integrate_connectors_parent.htm&type=5
- CRM Analytics Limits and Considerations — https://help.salesforce.com/s/articleView?id=sf.bi_limits.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
