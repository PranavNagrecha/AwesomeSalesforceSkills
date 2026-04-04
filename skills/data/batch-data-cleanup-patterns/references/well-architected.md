# Well-Architected Notes — Batch Data Cleanup Patterns

## Relevant Pillars

- **Operational Excellence** — Scheduled batch cleanup is an operational responsibility. Jobs must be monitored, alerting must be wired into the `finish()` method, and failures must be logged to a queryable record (custom object or Platform Event). An unmonitored cleanup job that silently skips records is worse than no job at all.
- **Scalability** — Cleanup patterns must handle growing data volumes gracefully. `Database.Batchable` resets governor limits per chunk, allowing deletion at scale that a single scheduled class cannot achieve. Batch size must be tuned based on cascade child volume.
- **Reliability** — Using `Database.delete(scope, false)` (allOrNone=false) ensures that a single corrupt record does not abort an entire batch chunk. Partial-failure logging provides the audit trail needed to reprocess failed records.
- **Security** — The user or integration credential running the batch must have the "Delete" permission on the target object and, if using hard delete, the "Bulk API Hard Delete" system permission. Batch Apex runs in the context of the user who submitted it via `Database.executeBatch()`.

## Architectural Tradeoffs

**Soft delete vs. hard delete:** Soft delete (standard `delete` + `emptyRecycleBin()`) is recoverable within the `emptyRecycleBin` window if called incorrectly. Hard delete via Bulk API is permanent and unrecoverable — appropriate for compliance scenarios but requires extra permission and adds operational risk if the retention filter has a bug.

**Per-chunk emptyRecycleBin vs. in finish():** Calling `emptyRecycleBin()` in each `execute()` chunk avoids accumulating large ID lists in memory (heap limit risk for millions of records), but adds a callout-equivalent operation per chunk. Calling it in `finish()` is simpler but requires `Database.Stateful` to track IDs, and the list can become very large for multi-million-record jobs. For jobs over 500,000 records, prefer per-chunk emptying.

**Batch Apex vs. Bulk API HARD_DELETE:** Batch Apex offers full Apex control (conditional logic, error handling, notifications) but is slower than Bulk API (200 records per chunk vs. millions per API job). Use Batch Apex for moderate volumes and complex logic; use Bulk API HARD_DELETE for large-volume compliance runs where simplicity and speed matter more than Apex expressiveness.

## Anti-Patterns

1. **Deleting records inside a trigger** — Triggers run synchronously within the caller's governor limits. Bulk deletion inside a trigger exhausts DML row limits and causes the originating save to fail. Use Batch Apex scheduled via a Schedulable class.
2. **Relying on automatic 15-day Recycle Bin purge for storage relief** — Automatic purge is not immediate and does not satisfy storage budget requirements or compliance mandates for permanent deletion. Always explicitly empty the Recycle Bin or use hard delete.
3. **Setting batch size at 200 without checking cascade child volume** — A single cascade explosion can silently fail entire batch chunks if child count pushes DML rows over 10,000 per transaction. Always profile cascade depth before finalizing batch size.

## Official Sources Used

- Apex Developer Guide — Batch Apex (`Database.Batchable`), `Database.delete()` allOrNone behavior, `Database.emptyRecycleBin()`, Schedulable interface, `System.schedule()` cron syntax
  URL: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — `Database.emptyRecycleBin()` method signature, `Database.DeleteResult` class, governor limits for DML operations
  URL: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Bulk API 2.0 Developer Guide — HARD_DELETE operation, ingest job lifecycle, permissions required for hard delete
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Salesforce Well-Architected Overview — Operational Excellence pillar framing, reliability and scalability guidance
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
