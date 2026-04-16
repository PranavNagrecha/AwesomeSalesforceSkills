---
name: bulk-api-2-patterns
description: "Use when designing or hardening external-to-Salesforce integrations that orchestrate Bulk API 2.0 ingest or query jobs: OAuth-backed job lifecycle, mandatory UploadComplete, polling JobComplete/Failed, CSV upload sizing, locator pagination for query results, partial-failure retry, and ordered multi-job loads (parent before child). Trigger keywords: bulk ingest job stuck in Open, retry only failed bulk rows, poll Bulk API 2 job status, Sforce-Locator pagination, multipart bulk ingest vs CSV upload. NOT for Bulk API 1.0 SOAP jobs (use data/bulk-api-patterns v1 sections), NOT for choosing batch vs real-time architecture alone (use integration/real-time-vs-batch-integration), NOT for low-level REST field/csv mechanics without integration context (use data/bulk-api-patterns)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
  - Security
triggers:
  - "our ETL connector creates a Bulk API 2 ingest job but records never process and the job stays Open forever"
  - "how should middleware poll Bulk API 2.0 job status and download failed rows without reprocessing successes"
  - "we run a parent Account upsert job and a child Contact job and need a reliable order of completion for Salesforce"
  - "Bulk API 2.0 query job returns CSV pages how do we follow Sforce-Locator until the last page"
  - "after a partial bulk failure what is the correct idempotent retry pattern using external id upsert"
tags:
  - integration
  - bulk-api-2
  - bulk-ingest
  - bulk-query
  - async-jobs
  - csv-upload
  - oauth
  - job-orchestration
inputs:
  - "Operation (insert, update, upsert, delete, hardDelete, or query) and target object API name"
  - "Whether the client uses single-part CSV uploads or multipart create-and-upload"
  - "Peak daily record volume versus org Bulk API 2.0 daily processing limits"
  - "Whether dependent objects require strictly ordered jobs (parent then child)"
  - "How the integration stores job IDs and checkpoints for restart after outage"
outputs:
  - "End-to-end job orchestration sequence with explicit state transitions and polling gates"
  - "Retry and partial-failure handling that respects non-rollback of successful batches"
  - "Query-result pagination rules using only the Sforce-Locator header value"
  - "Operational checklist for monitoring, logging, and alerting on job states"
dependencies:
  - data/bulk-api-patterns
  - integration/real-time-vs-batch-integration
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Bulk API 2.0 Patterns (Integration)

This skill activates when an integration engineer, ETL author, or middleware developer must make a **long-running Bulk API 2.0 pipeline reliable**: not merely issue REST calls, but coordinate job creation, data upload, the mandatory close signal, asynchronous processing, result retrieval, and safe retries. Bulk API 2.0 is asynchronous; successful internal batches are not rolled back when other batches fail, so integration design must treat outcomes as **per-record and per-batch**, not as a single atomic transaction. That asymmetry drives most production incidents when teams assume “the job failed so nothing landed,” or when they omit the step that transitions a job from **Open** to processing.

The platform exposes ingest jobs under `.../jobs/ingest/` and query jobs under `.../jobs/query/`. For ingest, after CSV data is uploaded with `PUT` against the job’s data URL, you **must** send `PATCH` on the job resource with `{"state":"UploadComplete"}` so Salesforce can start processing. Skipping that request leaves the job waiting indefinitely—there is no background timeout that substitutes for an explicit client signal. Multipart job creation is an exception: when job metadata and CSV are posted together as `multipart/form-data`, Salesforce completes the upload phase for you and you do not manually set `UploadComplete`. Choose multipart only when payload size fits the documented multipart limits; larger loads should use the standard create → upload → `UploadComplete` sequence.

Operational limits matter at integration design time. Salesforce creates internal batches of up to 10,000 records and caps total processed volume per org per rolling window (see *Bulk API 2.0 Limits* in the official guide). Each upload `PUT` must keep payload under the per-request size cap described in the guide (including base64-related guidance where applicable). Exceeding limits produces failed batches or throttling; the connector should surface `numberRecordsFailed`, `numberRecordsProcessed`, and error result files rather than silently restarting whole files.

For **query** jobs, results arrive as paginated CSV. The only supported way to walk pages is to read the `Sforce-Locator` response header from each `GET .../results` call, pass that opaque token as the `locator` query parameter on the next call, and stop when the header’s value is the literal string `null`. Guessing locator values or omitting pagination strands part of the extract off-platform.

Use **`data/bulk-api-patterns`** when the primary need is call-level request/response examples, CSV grammar, or v1 vs v2 comparisons. Use **`integration/real-time-vs-batch-integration`** when the open question is whether bulk is appropriate versus events or synchronous callouts. This integration skill focuses on **connector behavior**: idempotency keys (typically upsert external IDs), sequencing multi-job loads, backoff on `InProgress`, and parsing `successfulResults`, `failedResults`, and `unprocessedRecords` to build the next upload file.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Auth and instance URL**: OAuth access token, API version segment (for example `v66.0`), and the correct My Domain base URL for all subsequent job URLs returned by `contentUrl`.
- **Upload path**: single-part CSV `PUT` sequence versus multipart `POST` create—multipart skips manual `UploadComplete` by design.
- **Failure semantics**: whether downstream systems can tolerate partial success; if not, compensating transactions must live **outside** Salesforce because bulk commits are not all-or-nothing.
- **Most common wrong assumption**: that creating a job and streaming CSV is enough for processing to start. Without `UploadComplete` (non-multipart), nothing enters `InProgress`.
- **Limits in play**: daily processed-record ceiling, per-upload payload size, and query page sizing via `maxRecords` where supported—always cross-check the current *Limits and Allocations* topic for the API version in use.

---

## Core Concepts

### Ingest job state machine (integration view)

From an integrator’s perspective, ingest jobs move through **Open → UploadComplete → InProgress → JobComplete | Failed | Aborted**. **Open** means additional `PUT` uploads may still be sent to `contentUrl`. **UploadComplete** means the client has declared that uploads are finished; Salesforce will not accept more data for that job. **InProgress** covers automatic batching and record operation execution. **JobComplete** means processing finished, not that every row succeeded—inspect counts and download result CSVs. **Failed** indicates the job could not be completed after repeated internal attempts (distinct from per-row validation errors surfaced while the job still completes). **Aborted** is operator-driven cancellation when permitted.

### Partial success and retry scope

When some rows fail validation or hit row-level errors, Salesforce can still reach **JobComplete** with a non-zero `numberRecordsFailed`. Successful rows remain committed. Integration-layer retries must therefore **rebuild a new job** (or a new CSV) containing only unresolved rows plus any net-new inserts, typically guided by `failedResults` and `unprocessedRecords`. Re-sending an entire million-row file after ten failures is wasteful and risks duplicate operations unless the operation is upsert keyed by a natural or external identifier.

### Query extracts and locators

Large SOQL extracts must be consumed through repeated `GET .../jobs/query/{id}/results` calls. Each response includes the next locator in `Sforce-Locator`. Continue until that header equals `null` (the string shown in official examples). Never synthesize locator tokens; only reuse the value returned by Salesforce.

---

## Common Patterns

### Pattern 1: Hardened single-job ingest (create → upload → UploadComplete → poll → results)

**When to use:** Middleware owns a CSV file larger than multipart convenience thresholds or generated in stages.

**How it works:** `POST /jobs/ingest/` with `object`, `operation`, `contentType: CSV`, and delimiter/line-ending metadata matching the file. Upload bytes with `PUT` to `contentUrl`. Send `PATCH` with `UploadComplete`. Poll `GET` on the job until terminal state. Download `successfulResults`, `failedResults`, and `unprocessedRecords` as separate resources to decide the next action.

**Why not the alternative:** Polling only HTTP `202` from an upload `PUT` is insufficient—upload responses do not substitute for job state polling, and omitting `PATCH` leaves the job permanently **Open**.

### Pattern 2: Ordered parent/child bulk loads

**When to use:** Child rows reference parents that must exist before the child ingest job runs.

**How it works:** Run and **fully complete** the parent ingest job—including result validation—before creating the child job. Encode the dependency in orchestration metadata (workflow engine, queue, or state table) so a retried parent does not launch duplicate children.

**Why not the alternative:** Submitting both jobs concurrently produces intermittent `FIELD_INTEGRITY_EXCEPTION` and foreign-key failures that disappear under light load but fail in production peaks.

### Pattern 3: Query job pagination worker

**When to use:** Downstream warehouse needs the entire query result set without loading everything into one HTTP response.

**How it works:** Create the query job, poll until results are ready, then loop `GET` results passing each returned `Sforce-Locator` until the header reads `null`. Persist the last successful locator with checkpoints to support restart.

**Why not the alternative:** Increasing `maxRecords` does not remove the need for locators on large extracts; skipping pages silently loses data.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Small payload, single HTTP round-trip acceptable | Multipart `POST` create with embedded CSV | Platform auto-finishes upload phase; no manual `UploadComplete` |
| Large CSV generated on disk or stream | Standard create + chunked `PUT` + `PATCH UploadComplete` | Meets size limits and explicit close semantics |
| Some rows failed with `JobComplete` | New job with failed-row CSV + upsert external id | Avoids duplicating successes; aligns with non-rollback semantics |
| Extract > one HTTP response | Locator-driven pagination | Only supported navigation through paged CSV results |
| Nightly volume near org daily cap | Spread jobs, monitor `numberRecordsProcessed`, alert before hard stop | Prevents silent truncation when daily allocation is exhausted |

---

## Recommended Workflow

1. Confirm API version, OAuth token lifetime, and object/operation support (including `hardDelete` permission implications) before generating CSV.
2. Choose multipart versus staged `PUT`; if staged, verify declared `lineEnding` and `columnDelimiter` match the physical file.
3. Create the job, upload all parts within per-request size limits, then send `PATCH {"state":"UploadComplete"}` unless multipart already completed the upload phase.
4. Poll job `GET` on a backoff schedule while state is `UploadComplete` or `InProgress`; treat `Failed` and `Aborted` as terminal error paths with logging.
5. On `JobComplete`, download the three result resources, persist raw CSV artifacts for audit, and compute counts versus the source system.
6. For query jobs, walk `Sforce-Locator` until `null`, writing each page to object storage before advancing.
7. Open a follow-up job only for remaining failed/unprocessed rows, preserving idempotency via upsert keys or deterministic deletes.

---

## Review Checklist

- [ ] Non-multipart ingest includes explicit `UploadComplete` after final `PUT`.
- [ ] Polling distinguishes `InProgress`, `JobComplete`, `Failed`, and `Aborted` with separate handling.
- [ ] Partial failures produce a scoped retry file—not a blind full-file replay unless idempotent upsert covers it.
- [ ] Query extracts implement locator pagination without invented tokens.
- [ ] Parent/child loads are sequenced with a hard gate on parent `JobComplete` plus reconciliation.
- [ ] Monitoring includes Salesforce job ID, state transitions, and row counters in external logs.

---

## Salesforce-Specific Gotchas

1. **Silent “never starts” jobs** — Forgetting `UploadComplete` after uploads leaves jobs in **Open** with no processing. Impact: SLAs miss indefinitely until someone aborts the job.
2. **Misread JobComplete** — Operators treat `JobComplete` as “all rows inserted.” Impact: downstream systems advance checkpoints while data is still missing; always reconcile counts.
3. **Locator misuse** — Fabricating or reusing stale locators corrupts extracts. Impact: duplicate or skipped rows in the warehouse; only trust headers from the immediately prior response.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Job orchestration runbook | Step table listing HTTP methods, states, and polling intervals tied to observability IDs |
| Retry CSV specification | Column list and external-id strategy for the second-pass Bulk job |
| Pagination audit log | Sequence of locators and byte counts per page for query extracts |

---

## Related Skills

- `data/bulk-api-patterns` — Detailed REST examples, CSV rules, multipart structure, and Bulk API v1 comparison tables.
- `integration/real-time-vs-batch-integration` — Architecture-level choice between bulk batch paths and event/callout patterns.
- `data/bulk-api-and-large-data-loads` — Strategic sizing, concurrency discussions, and LDV-oriented load planning.
