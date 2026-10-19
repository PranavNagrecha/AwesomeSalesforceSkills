# Well-Architected Notes — Batch Data Cleanup Patterns

## Relevant Pillars

- **Operational Excellence** — Scheduled batch cleanup is an operational responsibility. Jobs must be monitored, alerting must be wired into the `finish()` method, and failures must be logged to a queryable record (custom object or Platform Event). An unmonitored cleanup job that silently skips records is worse than no job at all.
- **Scalability** — Cleanup patterns must handle growing data volumes gracefully. `Database.Batchable` resets governor limits per chunk, allowing deletion at scale that a single scheduled class cannot achieve. Batch size must be tuned based on cascade child volume.
- **Reliability** — Using `Database.delete(scope, false)` (allOrNone=false) ensures that a single corrupt record does not abort an entire batch chunk. Partial-failure logging provides the audit trail needed to reprocess failed records.
- **Security** — The user or integration credential running the batch must have the "Delete" permission on the target object and, if using hard delete, the "Bulk API Hard Delete" system permission. Batch Apex runs in the context of the user who submitted it via `Database.executeBatch()`.

## Architectural Tradeoffs

**Soft delete vs. permanent delete:** A plain delete leaves records restorable for 15 days, which is a safety net if the retention filter has a bug. `emptyRecycleBin()` and Bulk API hard delete remove that net. Choose permanent deletion only when policy requires it, and test the filter on both sides of the cutoff first.

**Per-chunk emptyRecycleBin vs. in finish():** `emptyRecycleBin()` accepts at most 10,000 records per call and counts as a DML statement. Calling it per chunk keeps every call small; collecting Ids for `finish()` fails once a run deletes more than 10,000 records and grows heap the whole time.

**Batch Apex vs. Bulk API `hardDelete`:** Batch Apex offers full Apex control (conditional logic, error handling, notifications) but is slower than Bulk API (200 records per chunk vs. millions per API job). Use Batch Apex for moderate volumes and complex logic; use a Bulk API `hardDelete` job for large-volume compliance runs where simplicity and speed matter more than Apex expressiveness.

## Anti-Patterns

1. **Deleting records inside a trigger** — Triggers run synchronously within the caller's governor limits. Bulk deletion inside a trigger exhausts DML row limits and causes the originating save to fail. Use Batch Apex scheduled via a Schedulable class.
2. **Relying on the automatic 15-day purge for a permanent-deletion mandate** — Records stay restorable until the purge, which has no guaranteed time. Recycle Bin rows don't count against storage, so the purge is about recoverability and query performance, not storage.
3. **Setting batch size at 200 without checking cascade child volume** — Deleting a parent deletes its master-detail children. Measure the DML rows one heavy parent costs in a sandbox before finalizing the batch size, so chunks stay under the 10,000-row transaction limit.

## Official Sources Used

Read for this revision (2026-10-19):

- Best Practices for Deployments with Large Data Volumes (`salesforce_large_data_volumes_bp.txt`): soft deletion still affects performance; Recycle Bin items don't count against storage; no item limit; 15-day retention and no guaranteed purge time; Bulk API hard delete recommended (L733-742); hard delete for one million or more records (L1019-1023).
- Apex Reference Guide (`salesforce_apex_reference_guide.txt`): `Database.emptyRecycleBin` is permanent, takes 10,000 records, cascade Ids must be excluded (account example), and counts against DML statements (L206900-206935); `Test.setCreatedDate` (L240831-240836).
- Apex Developer Guide (`salesforce_apex_developer_guide.txt`): test DML rolled back (L1008-1010); cron syntax and user time zone (L16812-16820); 100 scheduled Apex jobs (L16947); five queued or active batch jobs (L17012) and flex queue of 100 (L17235); invoking batch from a trigger with extreme caution (L17731-17733); one execute per batch test (L17734-17737); 50 million QueryLocator rows (L17701); default scope 200 and QueryLocator chunks up to 2,000 (L17309-17311, L17792).
- Salesforce Developer Limits and Allocations Quick Reference (`salesforce_app_limits_cheatsheet.txt`): 10,000 DML rows per transaction (L66).
- Bulk API 2.0 and Bulk API Developer Guide (`api_asynch.txt`): `hardDelete` skips the Recycle Bin; "Bulk API Hard Delete" permission off by default (L1640-1647); ingest workflow, batches upload, UploadComplete, and results resources (L161, L605-647, L698-734).
- Metadata API Developer Guide (`api_meta.txt`): no deploy of a class with active jobs by default (L22218-22221); ApexClass `.cls-meta.xml` and `status` (L22231, L22271); `purgeOnDelete` only in Developer Edition and sandboxes, roll-up summary fields purged on Metadata API delete (L4234-4246, L4638-4640).
- Salesforce Security Guide (`salesforce_security_impl_guide.txt`): deleting a record cascades to its field history (L4895-4896).
- SOQL and SOSL Reference, "Date Formats and Date Literals" (fetched from https://developer.salesforce.com/docs/get_document_content/soql_sosl/sforce_api_calls_soql_select_dateformats.htm/en-us/262.0): `LAST_N_DAYS:n` starts at midnight n days ago and includes today; `LAST_N_YEARS:n` is calendar-year based and ends December 31 of last year.
