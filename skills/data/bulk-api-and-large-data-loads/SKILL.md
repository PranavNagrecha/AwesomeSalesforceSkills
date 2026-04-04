---
name: bulk-api-and-large-data-loads
description: "Use when choosing between Bulk API 2.0 and REST/SOAP API for large-volume data operations, sizing batch jobs, monitoring bulk job status, and handling failed records in bulk pipelines. Triggers: bulk api, large data load, batch insert, bulk job, serial vs parallel mode. NOT for Data Loader UI steps (use data-import-and-management) or real-time single-record integrations (use apex/callouts-and-http-integrations)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "How do I load a million records into Salesforce efficiently?"
  - "My bulk job is failing with lock contention — should I switch to serial mode?"
  - "How do I retrieve failed records from a Bulk API 2.0 job after it completes?"
tags:
  - bulk-api
  - large-data-volumes
  - data-loading
  - async
  - batch
inputs:
  - Data volume estimate (record count and size)
  - Object type being loaded
  - Required processing mode (serial or parallel)
  - Error handling requirements
outputs:
  - API selection recommendation (Bulk API 2.0 vs REST)
  - Batch size and concurrency guidance
  - Job monitoring checklist
  - Failed record handling strategy
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Bulk API and Large Data Loads

This skill activates when a practitioner needs to move more than a few thousand records into or out of Salesforce programmatically, choose between Bulk API 2.0 and synchronous REST/SOAP, configure serial vs. parallel processing, or recover from failed bulk jobs. It does not cover Data Loader UI workflows or real-time single-record callouts.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Record volume and object type.** The threshold for Bulk API 2.0 is >2,000 records per operation. Below that, use bulkified REST (Composite) or SOAP. Confirm the object — some objects with complex sharing models or heavy triggers benefit from serial mode regardless of volume.
- **Most common wrong assumption.** Practitioners assume parallel mode is always safe and that a Bulk API 2.0 job either succeeds or fails atomically. Neither is true. Parallel mode causes lock contention on objects with complex triggers or sharing recalculation. And a job in `JobComplete` state may still contain failed and unprocessed records — the job itself succeeded but individual records did not.
- **Key limits in play.** Bulk API 2.0 automatically creates one internal batch per 10,000 records, up to a daily cap of 150,000,000 records per org. Each upload request must not exceed 150 MB (after base64 encoding). A batch that cannot process within 5 minutes is retried up to 20 times before the job moves to `Failed`. There is no SLA on Bulk API 2.0 processing time since it is fully asynchronous.

---

## Core Concepts

### Bulk API 2.0 vs. REST/SOAP

Any data operation involving more than 2,000 records is a good candidate for Bulk API 2.0. Operations under 2,000 records should use bulkified synchronous calls (REST Composite or SOAP). Bulk API 2.0 is the recommended choice over legacy Bulk API (v1) because it has a simpler workflow, automatic batching, a single results endpoint, and automatic PK chunking for query jobs.

Bulk API 2.0 supports two job types:

- **Ingest jobs** — insert, update, upsert, delete, hardDelete operations using CSV data.
- **Query jobs** — asynchronous SOQL queries that return large result sets, with automatic PK chunking.

Bulk API 2.0 uses standard OAuth 2.0 bearer token authentication, the same as all other Salesforce REST APIs.

### Job Lifecycle (Ingest)

Every Bulk API 2.0 ingest job moves through these states:

1. **Open** — Job created, accepting data uploads.
2. **UploadComplete** — Caller signals upload is done; Salesforce begins processing. This PATCH is mandatory — omitting it means the job never starts.
3. **InProgress** — Salesforce auto-batches records (one batch per 10,000 records) and processes them.
4. **JobComplete** — All batches processed. Individual records may still have failed.
5. **Failed** — Salesforce could not process the job (e.g., repeated batch timeouts after 20 retries).
6. **Aborted** — Job canceled by the creator or a user with Manage Data Integrations permission.

Once a job reaches `JobComplete` or `Failed`, the caller must retrieve results from three endpoints:
- `GET .../successfulResults/` — records that were processed successfully.
- `GET .../failedResults/` — records that failed with error messages.
- `GET .../unprocessedRecords/` — records that were never attempted (only present for `Failed` or `Aborted` jobs).

### Serial vs. Parallel Mode

Bulk API 2.0 processes jobs in parallel mode by default, creating internal batches that run concurrently. This is faster but can cause record lock contention when:
- The object has complex Apex triggers that update shared parent records.
- Sharing recalculation is triggered by ownership changes.
- Records in different batches reference the same parent (causing parent-level locks).

Serial mode (legacy Bulk API v1 concept; in Bulk API 2.0 the equivalent is one upload chunk at a time with careful batching) processes batches one at a time, minimizing lock contention at the cost of slower throughput. For objects prone to locking, group child records by parent ID within the same batch and consider using serial mode in Bulk API (v1) if lock errors persist.

The official guidance: avoid serial mode unless parallel mode results in lock timeouts and you cannot reorganize batches to avoid the locks.

### Failed Record Handling

Bulk API 2.0 does not roll back successfully processed records when other records in the same job fail. Each record is processed independently. After a job completes:

1. Retrieve `failedResults` — each row contains `sf__Error` describing the failure reason.
2. Retrieve `unprocessedRecords` — records that were never attempted (batch-level failure, not record-level).
3. Fix the root cause (validation rule violation, missing required field, duplicate, etc.).
4. Submit a new job with only the failed and unprocessed records.

Do not delete your local source CSV until all three result endpoints confirm complete coverage.

---

## Common Patterns

### Pattern 1: Standard Bulk Ingest Pipeline

**When to use:** Any insert, update, upsert, or delete of >2,000 records from an external system or migration pipeline.

**How it works:**
1. Authenticate with OAuth 2.0 to get a bearer token.
2. `POST /services/data/vXX.X/jobs/ingest/` with `{"object": "Account", "operation": "insert", "contentType": "CSV"}` — note the `id` in the response.
3. `PUT /services/data/vXX.X/jobs/ingest/{jobId}/batches` with CSV body (up to 100 MB raw / 150 MB base64). Repeat for large datasets.
4. `PATCH /services/data/vXX.X/jobs/ingest/{jobId}` with `{"state": "UploadComplete"}` — this starts processing.
5. Poll `GET /services/data/vXX.X/jobs/ingest/{jobId}` until `state` is `JobComplete` or `Failed`.
6. Retrieve `successfulResults`, `failedResults`, and `unprocessedRecords`.
7. Resubmit a new job for any records in failed or unprocessed.

**Why not synchronous REST:** Synchronous REST calls are subject to governor limits per transaction and cannot handle millions of records in a single call. Bulk API 2.0 processes records asynchronously in the background without tying up a transaction thread.

### Pattern 2: Bulk Query for Large Extracts

**When to use:** Extracting more than 1 million records, or any query that would time out via synchronous SOQL.

**How it works:**
1. `POST /services/data/vXX.X/jobs/query` with `{"operation": "query", "query": "SELECT Id, Name FROM Account"}`.
2. Poll the job status until `JobComplete`.
3. `GET .../results` with pagination using the `Sforce-Locator` response header to iterate through result pages.

Bulk API 2.0 query jobs automatically apply PK chunking to split large queries into manageable segments.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| <2,000 records | Bulkified REST Composite or SOAP | Synchronous; simpler error handling; avoids async overhead |
| 2,000–10M records, standard object | Bulk API 2.0, parallel mode | Automatic batching; faster throughput |
| Object with heavy triggers or sharing recalc | Bulk API 2.0, consider legacy Bulk API serial mode | Lock contention risk; serial reduces concurrent batch collisions |
| Nightly delta feed, known low failure rate | Bulk API 2.0 parallel, retry loop for failures | Balance throughput with automated error recovery |
| Large extract (>1M records) | Bulk API 2.0 query job | Auto PK chunking; paginated results from single endpoint |
| Permanent deletion bypassing Recycle Bin | Bulk API 2.0 with `hardDelete` operation | `delete` soft-deletes; `hardDelete` removes from Recycle Bin immediately |
| Initial data migration with sharing rules | Defer sharing calculation, then Bulk API 2.0 | Reduces sharing recalculation overhead during load |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Volume confirmed — >2,000 records justifies Bulk API 2.0; <2,000 should use REST Composite
- [ ] Operation type confirmed — insert, update, upsert, delete, or hardDelete
- [ ] Parallel vs. serial mode decision documented and rationale recorded
- [ ] Upload chunk size confirmed — raw CSV ≤100 MB per PUT request (150 MB after base64)
- [ ] `UploadComplete` PATCH is included in the implementation (job never starts without it)
- [ ] Poll loop implemented with exponential backoff, terminates on `JobComplete` or `Failed`
- [ ] All three result endpoints are retrieved: `successfulResults`, `failedResults`, `unprocessedRecords`
- [ ] Failed and unprocessed records are resubmitted in a new job (not the same job)
- [ ] Source CSV retained locally until all records confirmed processed
- [ ] Validation rules and triggers verified — bulk jobs do not bypass them

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Parallel mode lock contention on trigger-heavy objects** — Parallel batches running concurrently can simultaneously try to update the same parent record or trigger shared resource updates, causing `UNABLE_TO_LOCK_ROW` errors. This surfaces in `failedResults` and silently leaves records unprocessed. Use serial mode (Bulk API v1) or group records by parent ID to minimize collisions.

2. **Unprocessed records are not in failedResults** — Practitioners check `failedResults` and assume any record not there was successful. Unprocessed records from a batch-level failure appear only in `unprocessedRecords`. If you do not call that endpoint, you silently lose records. Always call all three result endpoints after every job.

3. **UploadComplete is mandatory — omitting it means nothing happens** — A job created with `state: Open` will never start processing until the caller sends `PATCH {"state": "UploadComplete"}`. There is no timeout that auto-starts the job. Forgetting this PATCH is a common silent failure in new implementations.

4. **Job state machine gotcha: JobComplete does not mean all records succeeded** — `JobComplete` means Salesforce finished processing attempts. Records inside the job may still have failed with validation errors, duplicate errors, or permission errors. Treating `JobComplete` as "everything worked" without checking `failedResults` is a data integrity risk.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| API selection recommendation | Bulk API 2.0 vs. REST Composite, with record count and object type rationale |
| Concurrency mode decision | Parallel vs. serial with documented justification based on trigger complexity |
| Job monitoring checklist | Step-by-step poll pattern with all three result endpoint retrievals |
| Failed record retry strategy | Pattern for extracting, remediating, and resubmitting failed and unprocessed records |

---

## Related Skills

- data-import-and-management — for Data Loader UI steps, declarative import tools, and non-programmatic data operations
- apex/callouts-and-http-integrations — for real-time single-record or low-volume REST integrations that should not use Bulk API
- data-model-design-patterns — for object design choices that affect bulk load performance (e.g., avoiding lock-prone parent structures)
