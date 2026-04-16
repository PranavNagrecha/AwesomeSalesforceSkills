# Well-Architected Notes — Data Cloud Integration Strategy

## Relevant Pillars

- **Performance** — Streaming ingestion carries a ~3-minute async batch interval. Multi-hop pipeline (DSO → DLO → DMO) adds additional lag. Architecture must account for 20-45 minute end-to-end latency for segment availability, not 3-minute latency.
- **Reliability** — Bulk ingestion is full-replace — a failed job leaves the dataset in the last successfully uploaded state. Schema irreversibility requires upfront design investment.
- **Scalability** — Batch ingestion caps at 100M rows or 50 GB per object. Datasets exceeding these limits require Data Federation (zero-copy) rather than physical ingestion.
- **Operational Excellence** — Schema deployments are irreversible. Connector configuration changes mid-stream require new connector creation. Operational runbooks must document rollback-impossible schema changes.

## Architectural Tradeoffs

**Streaming vs. Bulk:** Streaming suits high-frequency low-payload event data (behavioral events, IoT readings). Bulk suits high-volume periodic full-dataset loads (historical records, nightly data warehouse sync). Choosing the wrong mode for the data pattern causes either data loss (bulk for events) or schema exhaustion (streaming for bulk volumes).

**Ingestion API vs. MuleSoft Direct:** MuleSoft Direct handles unstructured content and complex transformation logic natively, but requires MuleSoft licensing. For structured relational data, Ingestion API is simpler and license-free. Choose based on source system type and licensing.

**Physical Ingestion vs. Data Federation:** For datasets above 50 GB or 100M rows, zero-copy federation to Snowflake, Databricks, BigQuery, or Redshift avoids physical ingestion limits. Federation trades query latency for storage cost — federated queries are slower than in-platform queries against ingested data.

## Anti-Patterns

1. **Streaming Ingestion for Sub-Minute Latency Requirements** — No Ingestion API connector delivers sub-minute data availability in Data Cloud. Using Streaming Ingestion for real-time use cases creates unmet SLA commitments. Architect separately for real-time and batch use cases.

2. **Delta-Only Bulk Ingestion Jobs** — Sending only changed records in a bulk job deletes all records not included in the batch. Full-replace semantics must be planned upfront. Delta ingestion must use streaming mode.

3. **Schema-Before-Architecture** — Deploying Ingestion API schemas before the full data model is designed creates permanent technical debt. Schema changes post-deployment are not supported. Invest in data modeling before creating connectors.

## Official Sources Used

- Data 360 Integration Guide — Ingestion API — https://developer.salesforce.com/docs/data/data-cloud-int/guide/c360-a-ingestion-api
- Data Cloud Connectors and Integrations — https://help.salesforce.com/s/articleView?id=c360_a_sources_targets.htm
- Data Cloud Architecture Strategy — https://architect.salesforce.com/docs/architect/fundamentals/guide/data-cloud-architecture-strategy
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
