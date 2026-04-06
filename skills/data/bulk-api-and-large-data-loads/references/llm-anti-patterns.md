# LLM Anti-Patterns — Bulk API and Large Data Loads

Common mistakes AI coding assistants make when generating or advising on Salesforce Bulk API and large data loading operations.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Defaulting to Parallel Mode Without Assessing Lock Contention Risk

**What the LLM generates:** "Use Bulk API 2.0 in parallel mode for maximum throughput" without mentioning that parallel processing can cause UNABLE_TO_LOCK_ROW errors when multiple batches update records that share parent records, lookup relationships, or are subject to sharing recalculation.

**Why it happens:** Parallel mode is the default and is faster, so training data presents it as the standard recommendation. The lock contention scenario that requires serial mode is a production-specific issue underrepresented in tutorials.

**Correct pattern:**

```text
Mode selection for Bulk API 2.0:

Use Parallel (default) when:
- Records are independent (no shared parent records)
- No triggers that update related records across batches
- Insert-only operations with no lookup relationships being updated

Use Serial when:
- Updating child records that share common parent records (Account -> Contacts)
- Triggers or Flows on the object update related records
- Previous parallel loads failed with UNABLE_TO_LOCK_ROW errors
- Loading to objects with complex sharing rules

For Bulk API 2.0, sort your CSV by parent ID to reduce lock contention
even in parallel mode.
```

**Detection hint:** Flag Bulk API recommendations that do not mention serial mode or lock contention. Look for "parallel" recommendations on objects with master-detail or lookup relationships to high-volume parents.

---

## Anti-Pattern 2: Recommending Bulk API for Small Record Sets

**What the LLM generates:** "Use Bulk API 2.0 to insert 50 records" when the REST API with SObject Collections or Composite resources would be more efficient for small volumes, avoiding the async job overhead.

**Why it happens:** LLMs associate "data loading" with "Bulk API" regardless of volume. The crossover point where Bulk API becomes more efficient than REST composite requests (~2,000-10,000 records) is rarely stated in training data.

**Correct pattern:**

```text
API selection by volume:
- 1-200 records: REST SObject Collections (up to 200 records per call)
- 200-2,000 records: REST SObject Collections in multiple calls
- 2,000-10,000+ records: Bulk API 2.0 becomes worthwhile
- 10,000+ records: Bulk API 2.0 is the clear choice

Bulk API overhead includes job creation, CSV upload, polling, and result
download — a minimum ~30s processing time even for small datasets.
```

**Detection hint:** Flag Bulk API recommendations where the stated record count is under 2,000 without justification for choosing async processing over synchronous REST.

---

## Anti-Pattern 3: Ignoring Failed Record Handling in Bulk Job Results

**What the LLM generates:** "Create the bulk job, upload the CSV, and close the job — the records will be inserted" without showing how to retrieve and handle failed records from the `failedResults` endpoint.

**Why it happens:** Success-path tutorials dominate training data. The multi-step error handling flow (poll status, download failed results, parse per-record errors, retry) is often omitted in examples.

**Correct pattern:**

```text
Complete Bulk API 2.0 error handling:

1. Poll: GET /services/data/vXX.0/jobs/ingest/{jobId}
   Wait for state = "JobComplete" or "Failed"

2. Success: GET /services/data/vXX.0/jobs/ingest/{jobId}/successfulResults/

3. Failures: GET /services/data/vXX.0/jobs/ingest/{jobId}/failedResults/
   Each row includes sf__Error column with the error message

4. Unprocessed: GET /services/data/vXX.0/jobs/ingest/{jobId}/unprocessedrecords/

5. Retry failed records after correcting data issues
6. Log all outcomes for reconciliation
```

**Detection hint:** Flag Bulk API examples that show job creation and CSV upload but do not include `failedResults` or `unprocessedrecords` endpoints.

---

## Anti-Pattern 4: Not Disabling Triggers and Flows During Large Data Loads

**What the LLM generates:** "Load your 2 million records using Bulk API" without discussing whether triggers, Flows, validation rules, and sharing rules should be temporarily disabled or bypassed during the load to prevent governor limit failures and improve throughput.

**Why it happens:** Bypassing automation during data loads is an operational practice that does not appear in API documentation. LLMs focus on the API mechanics without addressing the org-side preparation.

**Correct pattern:**

```text
Pre-load preparation for large data volumes:

1. Identify active triggers and record-triggered Flows on the target object
2. Consider bypass mechanisms:
   - Custom Metadata or Custom Setting flag checked by triggers/Flows
   - Temporarily deactivate non-essential Flows (with change management)
   - Use the "Disable Parallel Apex Testing" feature for batch loads
3. Disable non-essential validation rules or add bypass criteria
4. Defer sharing rule recalculation (Setup > Sharing Settings > Defer)
5. Schedule load during off-peak hours to avoid contention with users

Re-enable all automation and verify data integrity after the load completes.
```

**Detection hint:** Flag large data load recommendations (>100K records) that do not mention trigger/Flow bypass, validation rule handling, or sharing deferral.

---

## Anti-Pattern 5: Confusing Bulk API 2.0 Daily Limits with Per-Job Limits

**What the LLM generates:** "You can process up to 10,000 records per Bulk API 2.0 job" or "There is no limit on how many bulk jobs you can run" — confusing per-job, per-upload, and daily rolling limits.

**Why it happens:** Bulk API has limits at multiple levels (file size per upload, records per 24-hour period, batches per 24-hour period). Training data cites different limits in different contexts, and LLMs mix them up.

**Correct pattern:**

```text
Bulk API 2.0 limits (verify current values in Salesforce docs):

Per upload: 150 MB maximum file size
Per job: no explicit record count limit (governed by file size and time)
Rolling 24-hour: 150 million records processed
Rolling 24-hour: 15,000 batches (platform-created, not user-controlled in v2)
Concurrent jobs: varies by org (typically 100 open jobs)
Daily API requests: Bulk API jobs count separately from REST API daily limit

Multiple CSV uploads can be added to the same job before closing it.
```

**Detection hint:** Flag any claim of a per-job record count limit for Bulk API 2.0 (this is a v1 concept). Check for missing references to the 150 million record rolling 24-hour limit.
