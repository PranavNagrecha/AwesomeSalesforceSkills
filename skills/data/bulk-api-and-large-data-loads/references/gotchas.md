# Gotchas — Bulk API and Large Data Loads

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Parallel Mode Lock Contention on Objects with Heavy Triggers

**What happens:** Bulk API 2.0 parallel mode automatically splits uploaded data into internal batches of 10,000 records and processes them concurrently. If multiple batches simultaneously modify records that share a parent — or if Apex triggers in those batches attempt to update a shared resource (e.g., a rollup field on a parent object, a custom setting, or a shared custom object record) — Salesforce throws `UNABLE_TO_LOCK_ROW` errors. Affected records end up in `failedResults` with that error code. If the batch itself times out after repeated lock failures, those records land in `unprocessedRecords` instead.

**When it occurs:** Loading records on objects with:
- Apex triggers that update parent records (e.g., updating a parent Account from a child Contact trigger).
- Ownership changes that trigger private sharing recalculation.
- Any trigger that updates a single shared record (e.g., a custom counter or aggregate record).
- Creating users or records with private sharing models.

**How to avoid:**
- Sort your CSV by parent ID before uploading so records sharing a parent land in the same internal batch.
- Use the Defer Sharing Calculation feature (Setup > Defer Sharing Calculation) to suspend sharing recalculation during the load.
- For severe cases, switch to legacy Bulk API (v1) with `concurrencyMode: Serial`, which processes one batch at a time and minimizes concurrent lock competition. This is slower but avoids lock errors entirely on problematic objects.
- As a last resort, disable the problematic triggers during the load window using a Custom Metadata Type or Custom Setting flag, then re-enable and run a Batch Apex post-processing job.

---

## Gotcha 2: Unprocessed Records Are NOT in failedResults — You Must Check a Separate Endpoint

**What happens:** When a Bulk API 2.0 batch fails to process within 5 minutes, Salesforce retries it up to 20 times. If it still cannot be processed, the batch — and all records in it — is abandoned. These records are NOT written to `failedResults`. They appear only in `unprocessedRecords`. If your integration only checks `failedResults`, these records are silently lost.

**When it occurs:**
- Any time a batch exceeds the 5-minute processing timeout (common on objects with slow triggers or during org-wide peak load).
- When the entire job is `Aborted` by a user or system.
- When the job reaches `Failed` state due to repeated batch timeouts.

**How to avoid:** After every job reaches a terminal state (`JobComplete`, `Failed`, or `Aborted`), always call all three result endpoints:
1. `GET .../successfulResults/` — processed successfully.
2. `GET .../failedResults/` — attempted but failed at the record level.
3. `GET .../unprocessedRecords/` — never attempted.

Treat `count(successful) + count(failed) + count(unprocessed) == total records uploaded` as your integrity check. If the sum does not match, something has been missed.

---

## Gotcha 3: Validation Rules and Apex Triggers Fire on Bulk API 2.0 Jobs — No Bypass Exists

**What happens:** Practitioners sometimes expect that "bulk" implies a bypass of business logic. It does not. Every record processed by a Bulk API 2.0 job goes through the full Salesforce record-save lifecycle: validation rules, workflow rules (where still active), process builder, Apex triggers, and duplicate rules. A validation rule that fails for even one record will land that record in `failedResults` with the validation rule error message.

**When it occurs:** Any bulk load against an object that has active validation rules, Apex triggers, or duplicate management rules. This is especially common during migrations where source data does not conform to rules added after the original system was built.

**How to avoid:**
- Audit validation rules on the target object before the load. Identify any rules that the source data cannot satisfy and either fix the data or temporarily deactivate the rule (with change management approval) for the load window.
- Run a small pilot batch of 100–500 records first and inspect `failedResults` before committing to the full load.
- If triggers must be bypassed, implement a bypass flag (Custom Metadata or Custom Setting) in each trigger — never disable triggers via the Setup UI in production without a formal change process.

---

## Gotcha 4: The UploadComplete PATCH Is Mandatory — Omitting It Means the Job Never Starts

**What happens:** Creating a job with a `POST` to `/jobs/ingest/` puts it in `Open` state. Salesforce does not start processing until the caller sends a `PATCH` with `{"state": "UploadComplete"}`. There is no automatic timeout that transitions the job. A job stuck in `Open` state will remain there indefinitely, consuming an open job slot, until it is aborted or the `UploadComplete` PATCH is sent.

**When it occurs:** In new integrations where the developer reads only the "create job" and "upload data" steps and misses the "Upload Complete" step in the workflow. Also occurs when an integration fails after uploading data but before sending the PATCH — the job gets orphaned.

**How to avoid:**
- Always structure the ingest pipeline as: Create → Upload → UploadComplete → Poll → Retrieve Results. Treat the `UploadComplete` PATCH as a required step in the pipeline, not an optional notification.
- Implement monitoring for jobs stuck in `Open` state for more than a few minutes — this indicates a broken pipeline.
- Use the multipart job creation request for small datasets (≤100,000 characters), which transitions the job to `UploadComplete` automatically in a single call.
