---
name: data-cloud-ingestion-api
description: "Use when implementing or troubleshooting the Salesforce Data Cloud Ingestion API — covers streaming ingestion (near-real-time micro-batches), bulk ingestion (CSV-based full-replace jobs), schema management in OpenAPI 3.0.x YAML, Connected App setup with cdp_ingest_api scope, and error handling for both modes. NOT for standard Salesforce Bulk API, CRM Analytics data import, or Data Cloud data streams from CRM objects."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "How do I push external event data into Data Cloud using the Ingestion API?"
  - "Data Cloud Ingestion API schema changes — can I remove a field after deployment?"
  - "Streaming vs bulk ingestion for Data Cloud — which should I use?"
  - "Data Cloud Ingestion API Connected App setup and cdp_ingest_api OAuth scope"
  - "Bulk ingestion CSV file format requirements and size limits for Data Cloud"
tags:
  - data-cloud
  - ingestion-api
  - streaming-ingestion
  - bulk-ingestion
  - schema-management
  - Connected-App
inputs:
  - "Data source type: streaming events (real-time) vs. bulk snapshots (batch files)"
  - "Data schema: field names, data types, required DateTime field for engagement objects"
  - "Connected App credentials for OAuth 2.0 authentication"
outputs:
  - "OAuth 2.0 Connected App configuration with correct cdp_ingest_api scope"
  - "Ingestion API schema (OpenAPI 3.0.x YAML) for the source data"
  - "Streaming vs. bulk ingestion integration design with error handling"
  - "Schema governance policy: additive-only changes after deployment"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Data Cloud Ingestion API

This skill activates when a practitioner needs to implement or troubleshoot the Salesforce Data Cloud Ingestion API — the REST API for pushing external data into Data Cloud from outside the Salesforce ecosystem. It covers both interaction patterns (streaming micro-batches and bulk CSV jobs), the irreversible nature of schema deployments, the Connected App setup requirements, and error handling for both modes.

---

## Before Starting

Gather this context before working on anything in this domain:

- The Ingestion API has two distinct modes: **Streaming** (fire-and-forget micro-batches, processed approximately every 3 minutes) and **Bulk** (CSV-only, full-replace semantics, no partial updates).
- Bulk limits: 150 MB maximum per file, 100 files maximum per job, UTF-8 encoding, comma-delimited (RFC 4180).
- Schema changes are largely **irreversible after deployment**: you cannot remove a field, change a data type, or delete an object once deployed. Only additive changes (new fields) are supported.
- A Connected App with the `cdp_ingest_api` OAuth scope is required before the Ingestion API source can be registered in Data Cloud Setup.
- Engagement-category objects require a DateTime field in the schema — omitting it fails schema validation at registration time.

---

## Core Concepts

### Streaming vs. Bulk Ingestion

**Streaming Ingestion:**
- Endpoint: `POST /services/data/v{version}/ssot/ingest/connectors/{connectorId}/streaming/{objectName}`
- Returns 202 Accepted immediately; records are processed asynchronously approximately every 3 minutes
- Synchronous validation endpoint for development: `POST .../streaming/{objectName}/validate` — validates payload structure without writing data
- Supports upsert semantics (patch/partial update)
- Best for: real-time event data (clickstream, IoT, webhooks) where near-real-time latency is acceptable

**Bulk Ingestion:**
- Endpoint: `POST /services/data/v{version}/ssot/ingest/connectors/{connectorId}/jobs`
- CSV-only format: UTF-8, comma-delimited per RFC 4180
- Maximum 150 MB per file, 100 files per job
- Full-replace semantics: replaces all data for the specified object — no incremental or patch mode
- Best for: nightly or periodic full data snapshots from external data warehouses

### Schema Management (OpenAPI 3.0.x YAML)

Ingestion API schemas are defined in OpenAPI 3.0.x YAML and uploaded to Data Cloud at registration time. Critical constraints:

- **Additive-only after deployment**: you can add fields to an existing object, but cannot remove fields, change data types, rename fields, or delete objects
- **Engagement-category objects require a DateTime field**: must include a field with `type: string, format: date-time`
- **Schema changes are irreversible**: design the schema thoroughly before initial deployment

### Authentication: Connected App with cdp_ingest_api Scope

Ingestion API calls require OAuth 2.0 via a Connected App configured with `cdp_ingest_api` OAuth scope:
1. Create a Connected App in Setup > App Manager
2. Add OAuth scope: `cdp_ingest_api` (Data Cloud Ingest API)
3. Configure JWT Bearer Token or Client Credentials flow for server-to-server auth
4. Register the data source in Data Cloud Setup > Data Stream > Ingestion API using the Connected App

---

## Common Patterns

### Pattern 1: Streaming Ingestion for Real-Time Events

**When to use:** External system generates events (web clickstream, mobile app events, IoT) that must appear in Data Cloud within minutes.

**How it works:**
1. Configure Connected App with `cdp_ingest_api` scope
2. Define OpenAPI 3.0.x schema for the event object
3. Register Ingestion API connector in Data Cloud Setup
4. External system calls streaming endpoint with JSON payload
5. Data Cloud processes micro-batch within approximately 3 minutes
6. Use validate endpoint during development to test payload format without writing data

### Pattern 2: Bulk Ingestion for Nightly Snapshot

**When to use:** External data warehouse exports a full snapshot nightly. The snapshot replaces the previous Data Cloud record set for that object.

**How it works:**
1. Export data to CSV (UTF-8, comma-delimited, ≤150 MB per file)
2. Create bulk job via `POST .../jobs`
3. Upload CSV files (≤100 files per job)
4. Close job to trigger processing
5. Poll job status endpoint until complete
6. Validate via Data Cloud Query API to confirm record count

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Real-time events | Streaming Ingestion | Processed every ~3 minutes; fire-and-forget |
| Nightly full snapshot | Bulk Ingestion (CSV, 150 MB/file max) | Full-replace semantics; handles large volumes |
| Partial record update | Streaming with upsert semantics | Bulk is full-replace only |
| Schema testing in development | Streaming validate endpoint | Validates structure without writing data |
| Schema field removal needed | Architecture review — create new object version | Field removal is not supported post-deployment |

---

## Recommended Workflow

1. **Design schema before deployment** — Define all fields, types, and object categories in OpenAPI 3.0.x YAML. Confirm engagement-category objects include a DateTime field. Review schema with all stakeholders before deployment — post-deployment changes are additive-only.
2. **Configure Connected App** — Create a Connected App with `cdp_ingest_api` scope. Test OAuth token acquisition before schema registration.
3. **Register Ingestion API connector in Data Cloud Setup** — Navigate to Data Cloud Setup > Data Streams > New > Ingestion API. Select the Connected App and upload the schema.
4. **Select ingestion mode** — For real-time events: streaming endpoint. For nightly snapshots: bulk job pattern.
5. **Implement error handling** — Streaming: monitor Data Cloud error logs for processing failures. Bulk: poll job status until complete; errors appear in job status response.
6. **Use streaming validate endpoint during development** — Test payload format without writing data to Data Cloud.
7. **Validate records landed** — After streaming or bulk job, query Data Cloud Query API with ANSI SQL to confirm record counts.

---

## Review Checklist

- [ ] OpenAPI 3.0.x schema designed and reviewed before deployment
- [ ] Engagement-category objects include a required DateTime field
- [ ] Schema is designed as additive-only — no planned field removals post-deployment
- [ ] Connected App configured with `cdp_ingest_api` OAuth scope
- [ ] Streaming vs. bulk selection documented with rationale
- [ ] Bulk files: ≤150 MB per file, ≤100 files per job, UTF-8, comma-delimited
- [ ] Streaming validate endpoint used during development
- [ ] Post-ingestion validation via Data Cloud Query API confirms record counts

---

## Salesforce-Specific Gotchas

1. **Schema changes are largely irreversible after deployment** — After a schema is deployed, you cannot remove fields, change data types, or delete objects. Adding fields is the only supported change. An incorrectly designed schema requires creating a new object or living with the bad field indefinitely.
2. **Bulk ingestion uses full-replace semantics** — A bulk job replaces the entire dataset for the object. Running a partial file deletes all records not in that file. Bulk is for full snapshots, not incremental updates.
3. **Engagement-category objects require a DateTime field** — Schemas for Engagement-type objects must include a field with `type: string, format: date-time`. Omitting it fails schema validation at registration time.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| OpenAPI 3.0.x schema YAML | Complete schema file for all ingested objects |
| Connected App configuration | OAuth scope requirements and authentication flow documentation |
| Ingestion mode design | Streaming vs. bulk decision with implementation specification |
| Error handling runbook | Streaming error log monitoring and bulk job status polling |

---

## Related Skills

- `data/data-cloud-data-model-objects` — For DMO design that receives ingested data
- `admin/data-cloud-provisioning` — For Data Cloud org provisioning and Connected App setup
- `integration/api-led-connectivity` — For MuleSoft integration patterns feeding the Ingestion API
