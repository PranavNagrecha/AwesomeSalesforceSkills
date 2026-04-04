# Gotchas — Data Archival Strategies

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Big Object Records Are Immutable — No Standard Update or Delete

**What happens:** Attempting to use standard `update` or `delete` DML on a Big Object record throws a runtime exception in Apex. Developers who treat Big Objects like standard sObjects will discover this only when their batch job crashes in production.

**When it occurs:** Any Apex code that tries `update myBigObjectList;` or `delete myBigObjectList;` against a `__b` object. Also occurs when a Flow or Process Builder attempts to modify a Big Object record — those automation tools are not supported on Big Objects at all.

**How to avoid:** Treat Big Objects as append-only stores. For "updates," reinsert the record with the same composite index field values but different non-index field values — the platform will overwrite the existing record (upsert semantics). For deletion, use `Database.deleteImmediate(recordList)` in Apex or SOAP `deleteByExample()`. Both require all index fields to be fully specified. You cannot delete a Big Object record by specifying only a subset of the index.

---

## Gotcha 2: Async SOQL Is Not Transactional and Runs Slowly — Do Not Chain with Real-Time Processes

**What happens:** Async SOQL jobs are submitted asynchronously and results are materialized into a target object (standard or Big Object) after an unpredictable delay. There is no callback mechanism and no transactional guarantee. Jobs queued back-to-back may execute out of order. Practitioners who submit an Async SOQL job and then immediately try to query the target object for the results will find an empty or partial result set.

**When it occurs:** Any architecture that assumes Async SOQL results are available synchronously — e.g., triggering a downstream process immediately after submitting an Async SOQL job, or using Async SOQL for real-time customer-facing data needs.

**How to avoid:** Reserve Async SOQL for batch analytics and reporting use cases where eventual consistency is acceptable. Use Batch Apex with SOQL in the `start()` method for archival jobs that need predictable execution timing and sequencing. Monitor Async SOQL job status via the Bulk API query jobs endpoint before depending on results.

---

## Gotcha 3: Recycle Bin Records Degrade Query Performance — Full Recycle Bin Can Cause Slow Queries on Large Tables

**What happens:** Soft-deleted records participate in the query optimizer's selectivity calculations even though they are excluded from standard SOQL results. On a large object (e.g., 5 million active records + 2 million soft-deleted records in the Recycle Bin), the optimizer sees 7 million rows when computing selectivity thresholds. This inflated count can cause the optimizer to incorrectly determine that an index is not selective enough to use, leading to a full table scan and severely degraded query performance on list views and reports.

**When it occurs:** After bulk soft-deletes (especially during data cleanup or migration testing). An org that routinely soft-deletes large volumes and relies on the 15-day auto-purge will experience periodic performance degradation correlated with those delete operations.

**How to avoid:** Empty the Recycle Bin promptly after bulk deletes using `Database.emptyRecycleBin()` in Apex or the Setup > Recycle Bin UI. For large-volume archival jobs, use Bulk API 2.0 hard delete or call `Database.emptyRecycleBin()` at the end of each batch execute block. Monitor Setup > Recycle Bin volume as part of routine storage health checks.

---

## Gotcha 4: Field History on Archived Records Is NOT Archived Automatically

**What happens:** When parent records are archived (either moved to a Big Object or hard-deleted), the associated History object rows — e.g., `AccountHistory`, `CaseHistory`, `OpportunityFieldHistory` — are not automatically removed or archived. They remain in the History object table and continue to count against data storage. The History object can silently become one of the largest storage consumers in the org, especially on objects with many tracked fields or high field-change velocity.

**When it occurs:** Any time records are deleted (hard or soft) without first addressing the associated history rows. Also occurs when Field History Tracking is left enabled on high-churn fields (e.g., Status, Stage) over many years.

**How to avoid:** Before archiving parent records, query the History object for the rows associated with the records to be archived and handle them separately. If history retention is required, evaluate Salesforce Shield's Field Audit Trail to archive history into `FieldHistoryArchive` before deleting parents. If history is not required, delete history rows before deleting parent records. Proactively disable Field History Tracking on fields where history is not needed to stop future accumulation.
