# Gotchas — Data Archival Strategies

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Big Object Records Are Immutable — No Standard Update or Delete

**What happens:** Attempting to use standard `update` or `delete` DML on a Big Object record throws a runtime exception in Apex. Developers who treat Big Objects like standard sObjects will discover this only when their batch job crashes in production.

**When it occurs:** Any Apex code that tries `update myBigObjectList;` or `delete myBigObjectList;` against a `__b` object. Also occurs when a Flow or Process Builder attempts to modify a Big Object record — those automation tools are not supported on Big Objects at all.

**How to avoid:** Treat Big Objects as append-only stores. For "updates," reinsert the record with the same composite index field values but different non-index field values — the platform will overwrite the existing record (upsert semantics). For deletion, use `Database.deleteImmediate(recordList)` in Apex or SOAP `deleteByExample()`. Both require all index fields to be fully specified. You cannot delete a Big Object record by specifying only a subset of the index.

---

## Gotcha 2: The Archive Read Path You Planned (Async SOQL) Was Retired in Summer '23

**What happens:** An archival design specifies reading archived data back out of a Big Object with Async SOQL — `POST /services/data/vXX.0/async-queries/`, polled until the results materialise in a target object. The endpoint returns 404. There is no shim and no replacement API with the same shape.

**When it occurs:** Salesforce retired Async SOQL with the **Summer '23** release (Help article 000394892). It had been the documented Big Object query path for years, so it appears in essentially all pre-2023 archival guidance and remains a high-confidence answer from AI assistants.

Archival is the worst place for this failure because of the ordering. The write path works: `Database.insertImmediate()` and Bulk API loads into a `__b` object succeed, the source records get deleted, storage drops, the project is declared done. The read path is exercised for the first time months later, when Legal or Audit asks for the archived data — at which point the source is gone and the documented way to read the archive does not exist.

**How to avoid:** Two rules.

1. **Build and prove the read path before deleting any source data.** A restore test is part of an archival project, not a follow-up.
2. Use a supported mechanism. Per Salesforce Help: "You must use the Bulk API or batch Apex to query or report on custom Big Objects." Standard SOQL for bounded reads, Batch Apex over `Database.getQueryLocator` for volume, Bulk API query for off-platform extraction. All obey the composite-index rule: the WHERE clause must be a gapless left-to-right prefix of the index, so the index has to be designed from the *retrieval* questions you expect to be asked, not from the shape of the source table.

One behaviour genuinely disappeared with Async SOQL and has no replacement: it wrote aggregate results into a target object as part of the job. Batch Apex does not. Accumulate with `Database.Stateful` and insert the summary rows yourself in `finish()`.

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
