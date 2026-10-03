# Gotchas: ETL vs API Data Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each one names the official source it rests on.

## Gotcha 1: Bulk API 2.0 calls still count toward the daily API allocation

**What happens:** A team moves a REST pipeline to Bulk API 2.0 expecting a separate call budget, then keeps polling job status every few seconds from several jobs. The org still runs out of API requests.

**When it occurs:** When the 150,000,000-record daily ingest ceiling is mistaken for a separate call allocation.

**How to avoid:** Count job create, upload, close, poll, and result calls against the org's API request allocation. Poll with backoff. Bulk saves calls because one upload carries up to 150 MB, not because its calls are free.

**Source:** Salesforce Developer Limits and Allocations Quick Reference (262), "API Request Limits and Allocations": APIs that count include REST, SOAP, Bulk API, and Bulk API 2.0.

---

## Gotcha 2: Row-by-row REST writes for volume

**What happens:** A pipeline calls `POST /sobjects/Account` once per record. A nightly delta of a few hundred thousand rows burns a matching number of API requests.

**When it occurs:** When an ETL connector or custom script defaults to single-record REST.

**How to avoid:** Under 2,000 records per operation, use Composite or sObject Collections (up to 200 records per call, counted as one call). Above 2,000, use Bulk API 2.0.

**Source:** Bulk API 2.0 and Bulk API Developer Guide (262), introduction; REST API Developer Guide (262), "sObject Collections."

---

## Gotcha 3: Crossing the daily record limit stops the job mid-file

**What happens:** The job fails, and records after the limit are not processed. Records before it are already committed.

**When it occurs:** When several ingest jobs in one rolling 24-hour window together pass 150,000,000 records, or 15,000 batches shared with Bulk API (1.0).

**How to avoid:** Budget daily volume across every job and tool that writes to the org. Make jobs restartable from the control table, and read `unprocessedrecords` after any failed job.

**Source:** Bulk API 2.0 Developer Guide (262), "Understanding Bulk API 2.0 Ingest"; Limits Quick Reference (262), "Bulk API and Bulk API 2.0 Limits and Allocations."

---

## Gotcha 4: A slow batch fails the whole ingest job

**What happens:** A batch that cannot be processed within 5 minutes is retried. After 20 retries, the entire job moves to Failed and the remaining data is not processed.

**When it occurs:** When triggers, flows, or sharing recalculation on the target object make each 10,000-record batch slow.

**How to avoid:** Reduce automation cost on the target object during the window, keep uploads small, and split very heavy objects into more jobs.

**Source:** Bulk API 2.0 Developer Guide (262), "Understanding Bulk API 2.0 Ingest"; Limits Quick Reference (262), ingest "Maximum time before a batch is retried."

---

## Gotcha 5: There is no serial mode, so child loads lock on parents

**What happens:** Contacts for the same Account land in different parallel batches. Some rows fail with lock errors.

**When it occurs:** When the extract is not sorted by parent key.

**How to avoid:** Sort and group child rows by parent ID at the source. Integration Patterns says failure to group usually loads the first child and fails the following children for that parent.

**Source:** Bulk API 2.0 Developer Guide (262), Create a Job response, `concurrencyMode`: "Currently only parallel mode is supported"; Integration Patterns and Practices (262), "Batch Data Synchronization."

---

## Gotcha 6: Results come back in a different order and expire

**What happens:** A job that maps failures back to source rows by line number marks the wrong rows as failed. A job that reads results days later finds them gone.

**When it occurs:** When the ETL tool reconciles by position, or retries are run by a weekly process.

**How to avoid:** Reconcile `failedResults` and `successfulResults` by external ID or `sf__Id`. Read results within 7 days of job completion.

**Source:** Bulk API 2.0 Developer Guide (262), "Get Job Failed Record Results" usage notes; Limits Quick Reference (262), "Results lifespan."

---

## Gotcha 7: JSON is not an option for Bulk API 2.0

**What happens:** A pipeline built to emit JSON for the bulk load, or to read JSON query results, is rejected or needs a rewrite.

**When it occurs:** When the design assumes Bulk API 2.0 accepts the same formats as Bulk API (1.0).

**How to avoid:** Produce CSV for ingest and parse CSV for query results. `columnDelimiter` and `lineEnding` are the only format controls.

**Source:** Bulk API 2.0 Developer Guide (262), Create a Job and Create a Query Job request bodies: `contentType` "Only CSV is supported."

---

## Gotcha 8: Expecting seconds from a batch pattern

**What happens:** An ETL tool scheduled every five minutes still leaves users looking at stale data, and the load competes with users during business hours.

**When it occurs:** When a latency requirement measured per record is met with a shorter batch interval.

**How to avoid:** Use Remote Call-In, Platform Events, or Change Data Capture for per-record latency. Keep batch loads inside a designated window.

**Source:** Integration Patterns and Practices (262), "Batch Data Synchronization," Timeliness sidebar: timeliness "isn't of significant importance in this pattern," and batch loads during business hours can cause contention.

---

## Gotcha 9: Conflating one-time migration with an ongoing pipeline

**What happens:** Tools picked for a one-time move (Data Loader, Data Import Wizard) end up running a nightly sync with no control table, retry logic, or lineage.

**When it occurs:** When a migration project becomes the steady-state integration by default.

**How to avoid:** Classify the work first. An ongoing pipeline needs a control table, restart values, and error tables, as Integration Patterns describes.

**Source:** Integration Patterns and Practices (262), "Batch Data Synchronization," the seven-step ETL program and the error handling table.
