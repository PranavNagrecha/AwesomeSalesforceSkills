---
name: analytics-external-data
description: "Use when bringing non-Salesforce data into CRM Analytics via the External Data API, Data Connectors, or Live Datasets. Trigger keywords: InsightsExternalData, External Data API, live dataset, remote connection, Snowflake connector, BigQuery connector, Tableau Bridge, external CSV upload, analytics connector. NOT for standard data import into Salesforce objects. NOT for Salesforce object sync via dataflow local connectors. NOT for standard ETL into Sales or Service Cloud."
category: data
salesforce-version: "Spring '26+"
well-architected-pillars:
  - Performance
  - Reliability
  - Security
tags:
  - crm-analytics
  - external-data
  - InsightsExternalData
  - live-dataset
  - data-connector
  - snowflake
  - bigquery
  - redshift
inputs:
  - External data source type (CSV file, Snowflake, BigQuery, Redshift, or other JDBC-compatible warehouse)
  - Whether data must be materialized in CRM Analytics or can be queried live at runtime
  - Volume of data (row count, file size) to determine chunking strategy
  - Refresh frequency requirements (real-time, hourly, daily)
  - Authentication credentials and network access details for external warehouse
outputs:
  - Configured InsightsExternalData upload job with metadata JSON schema and chunked data rows
  - Data Connector and Remote Connection configured in Data Manager for scheduled refresh
  - Live Dataset linked to Remote Connection for read-through query
  - Decision recommendation on materialized vs. live dataset approach with tradeoff rationale
triggers:
  - "How do I upload CSV data from an external system into CRM Analytics programmatically?"
  - "Connecting Snowflake to CRM Analytics for live queries or scheduled dataset refresh"
  - "Analytics External Data API InsightsExternalData InsightsExternalDataPart upload"
  - "How do I create a Live Dataset in CRM Analytics pointing to BigQuery or Redshift?"
  - "What is the difference between a Data Connector and a Live Dataset in CRM Analytics?"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Analytics External Data

Use this skill when you need to bring data from outside Salesforce into CRM Analytics — whether via programmatic CSV upload using the External Data API, prebuilt Data Connectors to cloud warehouses, or Live Datasets for read-through queries against external systems. This skill covers three distinct paths and the architectural tradeoffs between them.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm which external data path applies: External Data API (programmatic CSV upload), Data Connector (scheduled materialized sync), or Live Dataset (read-through at query time).
- Determine whether data must be materialized inside CRM Analytics or whether querying the external system at runtime is acceptable. This is the single most consequential decision — it controls performance, freshness, and cost.
- Check CRM Analytics limits: dataset row limits (250 million rows per dataset), External Data API file size limits (per-chunk 10 MB, total 40 GB per job), and Live Dataset query timeout constraints driven by the external system.

---

## Core Concepts

CRM Analytics supports three fundamentally different mechanisms for ingesting or accessing external data. Conflating them causes architectural mistakes that are expensive to reverse.

### Path 1: Analytics External Data API (InsightsExternalData SObject)

The External Data API lets you programmatically upload CSV data into CRM Analytics to create or replace materialized datasets. It uses the `InsightsExternalData` and `InsightsExternalDataPart` SObjects exposed via the standard REST or SOAP API.

The upload sequence is strict and non-negotiable:

1. Create an `InsightsExternalData` record with a `MetadataJson` field containing a JSON schema that defines the dataset structure — field names, types (Text, Numeric, Date, etc.), and dataset name.
2. Upload data rows as `InsightsExternalDataPart` records, each containing a chunk of gzip-compressed CSV. Chunks must not exceed 10 MB each.
3. Set `Action` on the `InsightsExternalData` record to `Process` to trigger ingestion.

The metadata JSON schema step is mandatory. If you skip it or upload rows before the schema record exists, the job fails. The resulting dataset is a standard materialized CRM Analytics dataset — it is refreshed only when you re-run the upload job.

**When to use:** Integration pipelines (MuleSoft, Apex, external ETL tools) that need to push data into CRM Analytics on a schedule or event-driven basis. Suitable for data that does not reside in a supported Data Connector warehouse.

### Path 2: Data Connectors (Materialized, Scheduled Refresh)

Data Connectors provide prebuilt connections to external cloud warehouses: Snowflake, Google BigQuery, Amazon Redshift, and others. They are configured through CRM Analytics Data Manager using a Remote Connection object.

Data Connectors work by pulling data from the external warehouse on a scheduled refresh cycle and materializing it as a standard CRM Analytics dataset. After ingestion, queries run against the materialized dataset inside CRM Analytics — not against the warehouse. This means:

- Query performance is predictable and fast (data is local to CRM Analytics).
- Data freshness is bounded by the refresh schedule, not real-time.
- Storage is consumed inside CRM Analytics for the materialized copy.

A Remote Connection is a configuration object in Data Manager. It stores credentials and connection details. It does not upload data by itself. You must create a Data Connector recipe or dataflow that references the Remote Connection to actually pull and materialize data.

**When to use:** When the external warehouse supports a prebuilt connector, data volume fits within refresh windows, and users need fast dashboard query performance rather than real-time freshness.

### Path 3: Live Datasets (Read-Through, Not Materialized)

Live Datasets are a read-through query mechanism. When a CRM Analytics dashboard queries a Live Dataset, the query is translated and executed against the external system at runtime. No data is materialized inside CRM Analytics.

Key behavioral differences from materialized datasets:

- Data is always current — there is no refresh lag.
- Query performance is entirely dependent on the external system's response time and concurrency limits.
- CRM Analytics applies its query translation layer (SAQL to external query dialect), which may not support all SAQL constructs.
- Live Datasets cannot be joined with materialized datasets in the same SAQL query without federation workarounds.

Live Datasets require a Remote Connection. However, having a Remote Connection does not automatically create a Live Dataset — they are separate configuration steps.

**When to use:** When data freshness is critical and the external system can reliably serve low-latency queries at dashboard load time. Avoid when external system SLAs are inconsistent or data volumes make per-query execution expensive.

### Tableau Bridge

For on-premises or network-restricted data sources, Tableau Bridge acts as a relay between CRM Analytics and data behind a firewall. Bridge is installed on-premises and manages the secure tunnel. This is the recommended path when the external data source is not cloud-accessible.

### Streaming Data

For event-driven or near-real-time streaming data, CRM Analytics supports ingestion via the External Data API in micro-batches. True streaming (sub-minute latency) is not natively supported in CRM Analytics — use Salesforce Data Streams or a streaming pipeline that batches into the External Data API.

---

## Common Patterns

### Pattern 1: Programmatic CSV Upload via External Data API

**When to use:** An integration layer (Apex scheduled job, MuleSoft flow, Python ETL script) needs to push data from a system not supported by prebuilt connectors into CRM Analytics.

**How it works:**
1. Construct the metadata JSON schema defining field names and types.
2. POST to `/services/data/vXX.X/sobjects/InsightsExternalData` to create the header record with `MetadataJson` set.
3. Compress CSV data rows into 10 MB gzip chunks.
4. POST each chunk to `/services/data/vXX.X/sobjects/InsightsExternalDataPart` referencing the parent `InsightsExternalData` ID.
5. PATCH the `InsightsExternalData` record setting `Action` to `Process`.
6. Poll the `Status` field until it reaches `Completed` or `Failed`.

**Why not the alternative:** Standard Data Loader and Bulk API target Salesforce objects (Accounts, Contacts, custom objects) — they cannot write into CRM Analytics datasets.

### Pattern 2: Snowflake Live Dataset for Real-Time Querying

**When to use:** Finance or operations team needs a CRM Analytics dashboard that always reflects current Snowflake data — refresh lag is unacceptable.

**How it works:**
1. Create a Remote Connection in Data Manager pointing to the Snowflake account with OAuth or username-password credentials.
2. Create a Live Dataset referencing a specific Snowflake table or view via the Remote Connection.
3. Build SAQL queries against the Live Dataset — queries execute against Snowflake at dashboard load time.
4. Monitor Snowflake query logs to validate latency and concurrency impact.

**Why not the alternative:** Scheduling a Data Connector refresh every 15 minutes introduces lag and consumes CRM Analytics dataset storage. For sub-hour freshness requirements with manageable query volumes, Live Datasets avoid the overhead.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Data is in a system with no prebuilt connector (proprietary API, legacy DB) | External Data API (InsightsExternalData) | Only path for arbitrary CSV push into CRM Analytics |
| Data is in Snowflake/BigQuery/Redshift and freshness can be hourly or daily | Data Connector with scheduled refresh | Fast dashboard queries; predictable performance; no runtime warehouse cost per query |
| Data must always reflect current state; source is Snowflake or BigQuery | Live Dataset | No materialization lag; queries hit source at runtime |
| Data is behind corporate firewall or on-premises | Tableau Bridge + connector | Secure relay without opening firewall to internet |
| Volume is huge (hundreds of millions of rows) and query speed matters | Data Connector (materialized) | Live Dataset performance degrades at high volume; materialization is faster for analytics workloads |
| Near-real-time streaming events (sub-minute) | External Data API micro-batch or upstream streaming platform | CRM Analytics has no native streaming ingest; use micro-batch patterns |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the data path** — Confirm whether the requirement calls for External Data API (CSV push), Data Connector (materialized sync), or Live Dataset (read-through). Ask about freshness requirements, source system type, and whether data must be stored inside CRM Analytics.
2. **For External Data API:** Construct the metadata JSON schema first, referencing the field types supported by CRM Analytics (Text, Numeric, Date, Dimension). Do not upload data rows until the `InsightsExternalData` header record is created and confirmed.
3. **For Data Connectors:** Create the Remote Connection in Data Manager, test connectivity, then build a Recipe or Dataflow that references the connection. Set a refresh schedule aligned with business freshness needs.
4. **For Live Datasets:** Create the Remote Connection, then create the Live Dataset pointing at the target table or view. Build a test SAQL query to validate latency before wiring into dashboards.
5. **Validate data fidelity** — After any ingestion, run a row-count and spot-check query against both the source and the CRM Analytics dataset to confirm completeness.
6. **Monitor and alert** — Set up Data Manager job failure notifications. For External Data API jobs, build status polling into the integration layer to catch `Failed` states before they cause silent data gaps.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Correct data path selected (External Data API vs. Data Connector vs. Live Dataset) based on freshness and source system constraints
- [ ] For External Data API: metadata JSON schema created before data row upload; all fields typed correctly
- [ ] For Data Connectors: Remote Connection tested; refresh schedule configured; materialized dataset row count validated
- [ ] For Live Datasets: query latency tested under realistic concurrency; Snowflake/BigQuery query costs assessed
- [ ] Data Manager job failure notifications configured
- [ ] No use of Data Loader or Bulk API targeting CRM Analytics datasets (wrong tool)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **InsightsExternalData metadata must precede data rows** — Creating `InsightsExternalDataPart` records before the parent `InsightsExternalData` header record has a valid `MetadataJson` will cause the entire job to fail with a schema validation error. Always create and confirm the header first.
2. **Live Datasets do not cache or materialize** — Every dashboard load triggers a live query against the external system. If the external system is slow, unavailable, or rate-limited, the dashboard fails or times out. This surprises teams who assume CRM Analytics buffers the data.
3. **Remote Connection ≠ data upload** — A Remote Connection is a credential/configuration object. Creating one does not move or stage any data. Data movement requires a separate Recipe, Dataflow, or Live Dataset that references the connection.
4. **Data Connector refresh does not guarantee incremental load** — By default, many Data Connector recipes perform full refresh. Implementing incremental loads requires custom SAQL filter logic in the Recipe input node, anchored on a watermark field (e.g., `LastModifiedDate`).
5. **External Data API chunk limit is 10 MB compressed** — Files larger than 10 MB must be split into multiple `InsightsExternalDataPart` records. Sending a single part larger than 10 MB causes a hard API error.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| InsightsExternalData upload job | REST API sequence (header + parts + process action) for programmatic CSV ingestion into a CRM Analytics dataset |
| Metadata JSON schema | Field type definitions required as `MetadataJson` on the `InsightsExternalData` record before data rows are uploaded |
| Remote Connection configuration | Data Manager connection record storing credentials for Snowflake, BigQuery, or Redshift |
| Data Connector Recipe | CRM Analytics Recipe node sequence that reads from the Remote Connection and writes to a materialized dataset |
| Live Dataset definition | Configuration linking a Remote Connection to a specific external table or view for read-through querying |
| Decision rationale | Written recommendation covering materialized vs. live tradeoff with justification based on freshness, volume, and source system |

---

## Related Skills

- analytics-data-architecture — for end-to-end CRM Analytics pipeline design, incremental load strategy, and dataset schema planning
- analytics-dataflow-development — for building and tuning Dataflows that consume externally ingested datasets
- analytics-recipe-design — for Recipe-based ingestion from Data Connectors into materialized datasets
- middleware-integration-patterns — for selecting MuleSoft or other middleware as the layer that drives External Data API uploads
