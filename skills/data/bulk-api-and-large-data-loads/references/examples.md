# Examples — Bulk API and Large Data Loads

## Example 1: Million-Record Account Migration with Serial Mode

**Context:** A financial services customer is migrating 1.2 million Account records from a legacy CRM into Salesforce. The Account object has three Apex triggers that recalculate a custom rollup field on a parent Region object, and the org uses private sharing with complex sharing rules that trigger recalculation on ownership changes.

**Problem:** An initial test run using parallel mode (the default) produced thousands of `UNABLE_TO_LOCK_ROW` errors in `failedResults` because concurrent batches were simultaneously trying to update the same parent Region records. Records that failed were not in `failedResults` consistently — some appeared in `unprocessedRecords` because their batches timed out after 5 minutes and exhausted the 20-retry limit.

**Solution:**

```text
Step 1 — Pre-load preparation
- Sort the Account CSV by Region__c (parent ID) before upload.
  This ensures records sharing a parent land in the same batch,
  reducing inter-batch lock collisions even in parallel mode.
- Confirm CSV is UTF-8, line endings are LF, size <100 MB per chunk.

Step 2 — Defer sharing calculation (Setup > Defer Sharing Calculation)
- Suspend sharing rule calculation before the load.
- This prevents ownership-change sharing recalculation from running
  for every inserted record during the load window.

Step 3 — Create and submit the ingest job
POST /services/data/v66.0/jobs/ingest/
Body:
{
  "object": "Account",
  "operation": "insert",
  "contentType": "CSV"
}

Step 4 — Upload data in chunks
PUT /services/data/v66.0/jobs/ingest/{jobId}/batches
(Repeat for each CSV chunk, staying under 100 MB raw per request)

Step 5 — Signal upload complete (MANDATORY)
PATCH /services/data/v66.0/jobs/ingest/{jobId}
Body: {"state": "UploadComplete"}

Step 6 — Poll until terminal state
GET /services/data/v66.0/jobs/ingest/{jobId}
Poll every 30 seconds. Stop when state is JobComplete or Failed.

Step 7 — Retrieve ALL three result endpoints
GET .../successfulResults/       → confirm inserted record IDs
GET .../failedResults/           → rows with sf__Error column
GET .../unprocessedRecords/      → records never attempted

Step 8 — Retry
Create a NEW job with the union of failedResults and unprocessedRecords rows.
Fix the root cause for each sf__Error category before resubmitting.

Step 9 — Resume sharing calculation after load is confirmed complete.
```

**Why it works:** Sorting by parent ID groups related records into the same internal batch, reducing lock collisions. Deferring sharing calculation eliminates the biggest source of contention during initial loads. Retrieving all three result endpoints ensures no records are silently lost.

---

## Example 2: Nightly Integration Feed — 50K Records with Parallel Mode and Automated Retry

**Context:** An e-commerce integration pushes 40,000–60,000 Order records into Salesforce every night. The Order object has no complex triggers, and the org uses public read/write on Order. Speed matters because the load window is 2 hours.

**Problem:** The integration team was using REST API Composite batches of 200 records each, which required 250–300 HTTP calls per night and frequently hit the REST API call limit during peak loads. They also had no retry logic — any batch that failed was silently dropped.

**Solution:**

```python
# Pseudocode — illustrates the pattern, not a production implementation

def run_nightly_order_load(records_csv_path):
    token = get_oauth_token()

    # Create job
    job = create_ingest_job(token, object="Order__c", operation="upsert",
                            external_id_field="Integration_Id__c")
    job_id = job["id"]

    # Upload CSV (assuming <100 MB)
    upload_job_data(token, job_id, records_csv_path)

    # Signal complete
    set_upload_complete(token, job_id)

    # Poll with exponential backoff
    state = poll_until_terminal(token, job_id, poll_interval_seconds=15)

    # Retrieve all results
    successful = get_successful_results(token, job_id)
    failed = get_failed_results(token, job_id)
    unprocessed = get_unprocessed_records(token, job_id)

    log_summary(len(successful), len(failed), len(unprocessed))

    # Automated retry for failed + unprocessed
    retry_records = failed + unprocessed
    if retry_records:
        retry_csv = build_retry_csv(retry_records)
        run_retry_job(token, retry_csv, attempt=2)

    # Alert if retry still has failures
    assert_zero_failures_after_retry()
```

**Why it works:** Bulk API 2.0 replaces 250+ synchronous REST calls with a single job, well within API limits. Upsert with an external ID field handles both new and existing records in one operation. The automated retry loop with separate handling for `failedResults` vs. `unprocessedRecords` ensures complete record coverage. Parallel mode is safe here because the Order object has no lock-prone trigger logic.

---

## Anti-Pattern: Treating JobComplete as Full Success

**What practitioners do:** After polling until `state == JobComplete`, they log "load succeeded" and move on without retrieving `failedResults` or `unprocessedRecords`.

**What goes wrong:** `JobComplete` means Salesforce finished processing attempts — not that all records were written. Validation rule failures, duplicate errors, and permission errors all land in `failedResults`. Records in batches that hit the 5-minute timeout appear in `unprocessedRecords`. Both are silently lost if the caller does not retrieve these endpoints. In high-volume migrations, this can mean thousands of records missing from Salesforce with no error ever surfaced to the integration team.

**Correct approach:** Always retrieve all three result endpoints after every job: `successfulResults`, `failedResults`, and `unprocessedRecords`. Archive the failed and unprocessed CSVs. Create a new job to resubmit them after fixing the root cause.
