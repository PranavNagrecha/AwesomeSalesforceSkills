---
name: data-cloud-integration-strategy
description: "Use this skill when designing or troubleshooting the data pipeline strategy for connecting source systems to Data Cloud — including ingestion API pattern selection (streaming vs. batch), connector type decisions, DSO-to-DLO-to-DMO pipeline lag, and lakehouse federation patterns. Triggers on: Data Cloud ingestion API setup, streaming vs batch connector decision, Data Cloud connector types, MuleSoft Direct for Data Cloud, data pipeline lag for segmentation. NOT for standard Salesforce integration patterns (use integration-patterns skill), not for querying Data Cloud once data is ingested (use data-cloud-query-api), not for configuring standard admin connectors through the UI only."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Scalability
tags:
  - data-cloud
  - ingestion-api
  - streaming-ingestion
  - bulk-ingestion
  - connectors
  - pipeline
  - lakehouse
  - mulesoft-direct
  - dso
  - dlo
  - dmo
inputs:
  - "Source system type (CRM, cloud storage, custom application, unstructured content)"
  - "Data volume (daily row count, payload size per event)"
  - "Latency requirements (near-real-time vs. batch)"
  - "Data Cloud org with Ingestion API connected app configured"
outputs:
  - "Connector type recommendation and rationale"
  - "Ingestion API pattern selection (streaming vs. bulk) with limits"
  - "DSO-to-DLO-to-DMO pipeline lag estimate"
  - "Schema design for OpenAPI 3.0.x Ingestion API connector"
triggers:
  - "Data Cloud ingestion API streaming vs batch decision"
  - "how to connect external data to Data Cloud"
  - "Data Cloud connector type selection"
  - "MuleSoft Direct for Data Cloud setup"
  - "Data Cloud pipeline lag causing segmentation delays"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Data Cloud Integration Strategy

This skill activates when a practitioner is designing or troubleshooting how source systems connect to Data Cloud. It covers ingestion API pattern selection (streaming vs. bulk), connector type decisions, multi-hop pipeline lag (DSO → DLO → DMO), schema constraints, and lakehouse federation options. It does NOT cover post-ingestion querying (use data-cloud-query-api) or standard Salesforce-to-Salesforce integration.

---

## Before Starting

Gather this context before working on anything in this domain:

- Data Cloud Ingestion API has two mutually exclusive patterns on a single connector: **streaming** (fire-and-forget micro-batches, ~3 minutes async, hard 200 KB per request limit) and **bulk** (CSV files, 150 MB max per file, 100 files max per job). One connector cannot mix both patterns.
- Streaming ingestion is NOT real-time. The ~3 minute processing interval is async and carries no sub-3-minute SLA. Practitioners who assume sub-minute latency will be surprised.
- Every connector writes to a Data Stream Object (DSO), which flows DSO → DLO (Data Lake Object) → DMO (Data Model Object). This multi-hop pipeline introduces lag before data is available for segmentation or activation.

---

## Core Concepts

### Connector Types

Data Cloud supports four categories of connectors:

| Connector Type | Use Case | Examples |
|---|---|---|
| Built-in (CRM Connector) | Salesforce CRM objects (near-real-time via Change Data Capture) | Salesforce org objects |
| Cloud Storage | Files from S3, GCS, Azure Data Lake | CSV/Parquet files on schedule |
| Ingestion API | Custom source systems via REST API | App databases, custom events |
| MuleSoft Direct | Unstructured sources, SharePoint, Confluence | Content repositories, legacy systems |

MuleSoft Direct requires separate MuleSoft licensing. It is the only connector type that handles unstructured content ingestion.

### Streaming vs. Bulk Ingestion API

**Streaming Ingestion:**
- Fire-and-forget micro-batches processed approximately every 3 minutes
- Hard limit: 200 KB per request
- No sub-3-minute latency guarantee — async processing
- Suitable for event-driven or high-frequency low-payload data
- A synchronous validation endpoint exists for dev-mode schema pre-flight

**Bulk Ingestion:**
- CSV files only (UTF-8, comma-delimited, RFC 4180 compliant)
- Up to 150 MB per file, maximum 100 files per job
- Full-replace semantics — partial updates (patch) are NOT supported
- Suitable for daily/nightly loads of large datasets

A single Ingestion API connector cannot use both modes — choose at connector creation time.

### DSO → DLO → DMO Pipeline Lag

Every connector writes data into a Data Stream Object (DSO). The platform then processes DSO records into a Data Lake Object (DLO) and subsequently maps to a Data Model Object (DMO) for segmentation and identity resolution. This multi-hop pipeline introduces cumulative lag. Data is typically not available for segmentation within minutes of ingestion — practitioners must account for this lag in SLA commitments.

Identity resolution (Unified Profile creation) runs as frequently as every 15 minutes but is independent of connector ingestion lag.

### Schema Constraints for Ingestion API

Ingestion API schemas are defined in OpenAPI 3.0.x YAML format. After a schema is deployed, changes are largely irreversible: fields cannot be removed, field types cannot be changed, and objects cannot be deleted. Engagement-category DSOs require a `DateTime` field as mandatory. Plan schema carefully before deploying to production.

### Lakehouse Federation

Data Cloud supports zero-copy federation to external lakehouse platforms (Snowflake, Databricks, BigQuery, Redshift) via Data Federation. This allows querying external data in Data Cloud without physical ingestion. Batch ingestion caps at 100M rows or 50 GB per object — for datasets above this threshold, federation is the recommended approach.

---

## Common Patterns

### Pattern 1: Streaming Ingestion for Application Event Data

**When to use:** Source system generates frequent, small payloads (e.g., behavioral events, clickstream, IoT sensor readings) and near-real-time availability (within minutes) is acceptable.

**How it works:**

1. Create an Ingestion API connector in Data Cloud Setup, select Streaming mode.
2. Define the OpenAPI 3.0.x schema for the event payload — include DateTime field for engagement-category objects.
3. Obtain Data Cloud-specific OAuth token for the connected app.
4. POST events to the streaming endpoint (200 KB max per request).
5. Events batch approximately every 3 minutes into DSO, then flow to DLO and DMO.

**Why not use bulk:** Bulk is file-based (CSV), batched, and designed for high-volume periodic loads. Streaming suits event-driven, low-payload, frequent patterns.

### Pattern 2: Bulk Ingestion for Nightly Data Warehouse Sync

**When to use:** A large relational dataset (e.g., order history, historical customer records) needs to be loaded from an external data warehouse on a nightly schedule.

**How it works:**

1. Export source data as UTF-8 CSV (max 150 MB per file, 100 files per job).
2. Create an Ingestion API connector in Bulk mode.
3. POST the CSV files to the bulk upload endpoint in a single job.
4. Monitor job status until processing completes.
5. Data flows DSO → DLO → DMO with multi-hop pipeline lag.

**Why not use streaming:** Large files cannot be streamed due to the 200 KB per-request limit. Bulk handles full dataset replacement efficiently.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| High-frequency low-payload events from custom app | Streaming Ingestion API | Fire-and-forget micro-batches, event-driven |
| Nightly full-dataset load from data warehouse | Bulk Ingestion API (CSV) | Handles large files, 150 MB/file max |
| Salesforce CRM object sync | CRM Connector (built-in) | Native, near-real-time via CDC, no custom code |
| SharePoint or Confluence content | MuleSoft Direct | Only connector type for unstructured sources |
| Dataset > 50 GB or 100M rows | Data Federation (zero-copy) | Exceeds physical ingestion limits |
| Partial record updates (patch semantics) | Cannot use Ingestion API — redesign | Bulk is full-replace only; no patch support |

---

## Recommended Workflow

1. Identify the source system type, data volume, and latency requirements before selecting a connector type.
2. For custom sources, decide streaming vs. bulk based on payload size and frequency — a single connector cannot mix both.
3. Design the OpenAPI 3.0.x schema carefully before deploying — field removal and type changes are not supported post-deployment.
4. For engagement-category DSOs, include a mandatory DateTime field in the schema.
5. Implement OAuth token flow for the Ingestion API connected app; use the streaming validation endpoint for schema pre-flight during development.
6. Account for the DSO → DLO → DMO multi-hop lag when communicating data availability SLAs to stakeholders.
7. For large datasets (>50 GB), evaluate Data Federation instead of physical ingestion.

---

## Review Checklist

- [ ] Connector type matches source system (CRM, cloud storage, Ingestion API, MuleSoft Direct)
- [ ] Streaming vs. bulk decision documented with rationale
- [ ] Schema designed and reviewed before deployment — irreversible after deploy
- [ ] 200 KB streaming limit and 150 MB / 100-file bulk limits verified against volume
- [ ] DateTime field included for engagement-category DSOs
- [ ] Multi-hop pipeline lag (DSO → DLO → DMO) communicated to stakeholders
- [ ] For datasets > 50 GB: Data Federation considered as alternative
- [ ] MuleSoft Direct licensing confirmed if selected

---

## Salesforce-Specific Gotchas

1. **Streaming Is Not Real-Time** — The Ingestion API streaming mode processes batches approximately every 3 minutes asynchronously. There is no sub-minute SLA. Any integration that depends on sub-minute latency in Data Cloud will not be met by the Ingestion API.

2. **Single Connector Cannot Mix Streaming and Bulk** — A connector is created in either streaming or bulk mode. Switching modes requires creating a new connector, and changing schema after the fact is largely impossible (no field removal, no type change). Choose mode and schema carefully at inception.

3. **Bulk Ingestion Is Full-Replace Only** — Bulk ingestion does not support partial updates (PATCH semantics). Every bulk job replaces the full dataset for the objects in scope. Partial-update use cases must use streaming ingestion or a different approach.

4. **Multi-Hop Lag Before Segmentation** — Data ingested via Ingestion API is NOT immediately available for segmentation or activation. It must traverse DSO → DLO → DMO first. Identity resolution adds a further processing step. Plans that assume immediate availability will fail.

5. **Irreversible Schema After Deployment** — Ingestion API schemas are defined in OpenAPI 3.0.x YAML. Once deployed, you cannot remove a field, change its type, or delete an object. Retiring a schema requires creating a new connector with a new schema and migrating historical data.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Connector type selection | Documented decision: CRM/cloud storage/Ingestion API/MuleSoft Direct with rationale |
| Ingestion API schema | OpenAPI 3.0.x YAML for custom source DSO |
| Pipeline lag estimate | DSO → DLO → DMO latency projection for stakeholder SLA communication |
| Ingestion client code | OAuth token flow + streaming/bulk POST implementation |

---

## Related Skills

- data-cloud-query-api — for querying DMO data once ingestion is complete
- data-cloud-activation-development — for event-driven actions on ingested DMO data
- rest-api-patterns — for standard Salesforce REST/SOQL integration patterns
- mulesoft-anypoint-architecture — for MuleSoft Direct integration architecture
