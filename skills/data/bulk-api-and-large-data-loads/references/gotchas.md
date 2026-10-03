# Gotchas: Bulk API and Large Data Loads

Non-obvious behaviours that lose records, stall jobs, or burn the org's daily allocation. Each gotcha names its source. "Bulk Guide" means the Bulk API 2.0 and Bulk API Developer Guide, Version 67.0 (api_asynch.pdf). "Limits Reference" means the Salesforce Developer Limits and Allocations Quick Reference, Summer '26. "LDV Guide" means Best Practices for Deployments with Large Data Volumes.

## Gotcha 1: Parallel Lock Contention, and Bulk API 2.0 Has No Serial Mode

**What happens:** Bulk API 2.0 splits the upload into internal batches of 10,000 records and processes them in parallel. When batches update records that share a parent, or triggers update one shared record, rows fail with lock errors (`UNABLE_TO_LOCK_ROW`, or the batch-level `TooManyLockFailure`). Teams then look for a serial switch in Bulk API 2.0 and find none: `concurrencyMode` is "For future use... Currently only parallel mode is supported."

**When it occurs:** Child loads whose parents receive roll-up or trigger updates, AccountTeamMember-style records that lock their account, and the operations the guide names as lock-prone: creating users, updating ownership for records with private sharing, updating user roles, and updating territory hierarchies.

**How to avoid:**
- Sort the CSV by parent ID so records that lock the same parent land in the same batch.
- Defer sharing calculation for initial loads (LDV Guide, "Defer Sharing Calculation"), then resume it in a maintenance window.
- Rewrite complex trigger logic as batch Apex that runs after the load, as the guide recommends.
- If locks persist, move only that load to a Bulk API 1.0 job created with `concurrencyMode` Serial (see `references/rest-examples.md`). Serial is slower and the guide says to use it only when you "can't reorganize your batches to avoid locks."

**Source:** Bulk Guide, Create a Job response body (concurrencyMode); Bulk API Plan Bulk Data Loads (Use Parallel Concurrency Mode Whenever Possible; Organize Batches to Minimize Lock Contention; Be Aware of Operations that Increase Lock Contention; Minimize Number of Triggers); Errors (TooManyLockFailure). LDV Guide, Defer Sharing Calculation.

---

## Gotcha 2: Unprocessed Records Are Not in failedResults

**What happens:** A batch that cannot finish within 5 minutes fails and is retried up to 20 times. After 20 retries "the entire ingest job is moved to the Failed state and remaining job data isn't processed." Those rows never appear in `failedResults`. "Unprocessed rows are not the same as failed rows. Failed rows are processed but encounter an error during processing."

**When it occurs:** Slow triggers or flows, heavy lock contention, aborted jobs, and jobs that cross the 150,000,000-record daily limit mid-run.

**How to avoid:** After every terminal state, call `successfulResults`, `failedResults`, and `unprocessedrecords`, and check that the three counts add up to the uploaded row count. Create a new job for the failed and unprocessed rows after fixing the cause. "Don't delete your local CSV data until you've confirmed that all records were successfully processed by Salesforce."

**Source:** Bulk Guide, Understanding Bulk API 2.0 Ingest; Get Job Unprocessed Record Results; Upload Job Data usage notes; Troubleshooting Ingest Timeouts.

---

## Gotcha 3: Validation Rules, Triggers, and Flows Still Run

**What happens:** A load that expected to skip business logic lands thousands of rows in `failedResults` with validation messages, or times out because triggers fire in 200-record chunks across every batch.

**When it occurs:** Every Bulk API load. Batches are processed in chunks of 200 records (API 21.0 and later), and each chunk runs the save lifecycle. Bulk processing has its own CPU limit of 60,000 ms on the Salesforce servers.

**How to avoid:** Audit validation rules, triggers, and flows on the target object before the load. Run a pilot of a few hundred rows in a sandbox first ("Processing times can be different in a production organization"). If automation must be bypassed, use a bypass flag the automation checks, and remove it after the load under change control. UNVERIFIED (2026-10-03): workflow rules and Process Builder behaviour during Bulk API loads was not re-read in a fetched source; the guide only says "Workflow actions increase processing time."

**Source:** Limits Reference, Bulk API and Bulk API 2.0 Limits (Batch processing time, chunk size 200). Bulk Guide, Limits (Maximum CPU Time Limit 60,000 ms); General Guidelines for Data Loads (test in sandbox; Minimize Number of Workflow Actions; Minimize Number of Triggers).

---

## Gotcha 4: The UploadComplete PATCH Is Mandatory, and Open Jobs Do Not Wait Forever

**What happens:** A job created with `POST /jobs/ingest` sits in `Open` and never processes because the caller never sent `{"state":"UploadComplete"}`. Correction (2026-10-03): an earlier version said the job waits indefinitely. The Limits Reference sets the "Maximum time that a job can remain open" at 24 hours for ingest jobs, and non-terminal jobs older than seven days are periodically cleaned up.

**When it occurs:** New integrations that skip the step, and pipelines that crash after the upload but before the PATCH.

**How to avoid:** Treat Create, Upload, UploadComplete, Poll, and Results as one unit. Alert on any job still `Open` after a few minutes. For small payloads (100,000 characters or less), use the multipart create request: "After you create a multipart job, the upload is completed for you automatically."

**Source:** Bulk Guide, Create a Job (state values; Usage Notes on multipart requests); Step 4: Bulk Insert with a Multipart Request. Limits Reference, General Limits (Maximum time that a job can remain open; Batch and job lifespan).

---

## Gotcha 5: The Default Line Ending Is LF

**What happens:** A CSV exported on Windows loads with the default settings and rows fail, or the last column of every row carries a stray carriage return into Salesforce.

**When it occurs:** "The default line ending, if not specified, is LF." Windows and many spreadsheet tools write CRLF, and "the text editor used to create the CSV file" can override the operating system default.

**How to avoid:** Set `"lineEnding": "CRLF"` on job creation when the file uses CRLF, or normalize the file to LF before upload. Set `columnDelimiter` (COMMA, SEMICOLON, TAB, PIPE, CARET, BACKQUOTE) when the source is not comma-separated. Save files as UTF-8.

**Source:** Bulk Guide, Prepare CSV Files; Create a Job request body (lineEnding, columnDelimiter).

---

## Gotcha 6: 150 MB Is a Per-Job Cap After Base64, Not a Raw File Size

**What happens:** A 140 MB CSV upload is rejected, or a pipeline tries to push several large PUTs into one job.

**When it occurs:** "Files are converted to base64 when received by Salesforce. This conversion can increase the data size by approximately 50%." The Quick Start states "You can upload up to 150 MB per job (after base64 encoding)," and the Limits Reference lists "150 MB per job" for Bulk API 2.0.

**How to avoid:** Keep raw CSV at or under 100 MB per job and split larger sets across several jobs. Each job still produces batches against the daily allocation, so plan the job count with Gotcha 7 in mind.

**Source:** Bulk Guide, Prepare CSV Files; Upload Job Data usage notes; Quick Start Step 3. Limits Reference, Limits Specific to Ingest Jobs (Maximum file size).

---

## Gotcha 7: The 15,000-Batch Allocation Is Shared Across Both Bulk APIs

**What happens:** A migration weekend submits many small jobs, and on Monday the nightly feeds from other integrations fail or queue because the org has used its batch allocation.

**When it occurs:** "You can submit up to 15,000 batches per rolling 24-hour period. This allocation is shared between Bulk API and Bulk API 2.0." In Bulk API 2.0 "only ingest jobs consume batches. Query jobs don't." Separately, if "more than 2,000 unprocessed requests from a single organization are in the queue," further requests are delayed.

**How to avoid:** Budget batches per integration per day, prefer fewer large jobs over many small ones, and avoid submitting hundreds of jobs at once. Check the org's remaining allocation through the REST `/limits` resource before a large run.

**Source:** Limits Reference, Batch Allocations. Bulk Guide, Limits ("available to clients via the REST API /limits endpoint"); Minimize Number of Batches in the Asynchronous Queue.

---

## Gotcha 8: hardDelete Skips the Recycle Bin and Needs a Permission That Is Off by Default

**What happens:** A cleanup job using `hardDelete` fails with an insufficient-access error, or, worse, succeeds and the records cannot be restored from the Recycle Bin.

**When it occurs:** "When the hardDelete value is specified, the deleted records aren't stored in the Recycle Bin. Instead, they become immediately eligible for deletion. The permission for this operation, 'Bulk API Hard Delete,' is disabled by default and must be enabled by an administrator. A Salesforce user license is required for hard delete."

**How to avoid:** Grant Bulk API Hard Delete to one integration user through a permission set, require an approval step before any hardDelete job, and keep the extract of deleted IDs. The LDV Guide recommends hard delete for large deletions, so plan it rather than avoid it.

**Source:** Bulk Guide, Create a Job request body (operation values and hardDelete note). LDV Guide, Deleting Data.
