---
name: batch-data-cleanup-patterns
description: "Use when scheduling automated deletion of temporary records, enforcing data retention policies, running nightly cleanup jobs, reclaiming org storage, managing recycle bin, or performing async bulk deletion of aged records. Trigger keywords: batch delete, retention policy, purge records, cleanup job, recycle bin, emptyRecycleBin, hard delete, nightly purge, storage optimization. NOT for data archival to external storage (use data-archival-strategies)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Scalability
triggers:
  - "delete old records automatically on a schedule every night"
  - "clean up temporary records created by automation or integrations"
  - "enforce data retention policy by purging records older than a set number of years"
  - "reclaim org storage by removing soft-deleted records from the recycle bin"
  - "run a nightly job to permanently remove debug or staging records"
tags:
  - batch-apex
  - deletion
  - retention-policy
  - recycle-bin
  - storage-optimization
  - scheduler
  - hard-delete
  - data-cleanup
inputs:
  - "Object API name and retention period (e.g., purge records older than 30 days)"
  - "Whether permanent deletion (hard delete / emptyRecycleBin) is required"
  - "Expected record volume — determines batch size and chunking strategy"
  - "Cascade deletion risk: master-detail child objects that auto-delete with parent"
outputs:
  - "Batch Apex class implementing Database.Batchable<SObject> with retention filter"
  - "Schedulable wrapper class with System.schedule() cron expression"
  - "Optional emptyRecycleBin() call in finish() for immediate storage reclaim"
  - "Error log or custom object record capturing partial-delete failures"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Batch Data Cleanup Patterns

This skill activates when a practitioner needs to automatically delete records on a scheduled cadence — for retention policy enforcement, temporary record purging, storage optimization, or recycle bin management — without moving data to an external system. Use `data-archival-strategies` instead when records must be preserved in Big Objects or exported to external storage before deletion.

---

## Before Starting

Gather this context before working on anything in this domain:

- **What object and what filter?** Confirm the sObject API name, the field used for age filtering (`CreatedDate`, `LastModifiedDate`, or a custom retention date field), and the retention threshold (e.g., 30 days, 7 years).
- **Is permanent deletion required?** Standard `delete` sends records to the Recycle Bin (15-day hold, still counts against data storage). If storage reclaim is urgent, use `Database.emptyRecycleBin()` in the batch `finish()` method or use a HARD_DELETE Bulk API job.
- **Cascade risk.** Any master-detail relationship means deleting the parent also deletes all child records. Count affected child volumes before scheduling. A deletion of 1,000 parent records may cascade to hundreds of thousands of children.
- **Governor limits in play.** Each Batch Apex `execute()` chunk is a separate transaction. The DML row limit is 10,000 per transaction. The total rows processed per batch job is capped at 50 million for the query. Bulk API HARD_DELETE counts against the org's daily API call limits.

---

## Core Concepts

### Batch Apex for Bulk Deletion

`Database.Batchable<SObject>` is the standard pattern for scheduled bulk deletion. The `start()` method returns a `Database.QueryLocator` (up to 50 million rows per job) filtered by the retention criterion. The `execute()` method receives chunks (typically 200 records) and calls `delete` or `Database.delete(records, false)` for partial-failure tolerance. The `finish()` method is the correct place to log results, send notifications, or call `Database.emptyRecycleBin()`.

Use `Database.delete(records, false)` (allOrNone = false) rather than bare `delete` so that a single bad record does not roll back the entire chunk. Capture `Database.DeleteResult[]` and log failures to a custom object or Platform Event for audit.

### Schedulable Interface and Cron Expressions

Schedule a batch by implementing `Schedulable` and calling `Database.executeBatch()` inside `execute(SchedulableContext ctx)`. Register the schedule via `System.schedule('Job Name', cronExpression, new MyScheduler())`. Salesforce cron expressions are six-part (seconds minutes hours day-of-month month day-of-week) with an optional seventh year part. A nightly job at 2:00 AM every day uses `'0 0 2 * * ?'`. Maximum 100 scheduled Apex jobs allowed per org; cleanup jobs should be consolidated or use a single dispatcher pattern.

### Recycle Bin and Storage Impact

Standard `delete` DML moves records to the Recycle Bin, where they remain for up to 15 days before automatic purging. Critically, records in the Recycle Bin **count against data storage** until they are purged. For large cleanup jobs this means storage is not reclaimed immediately. Two options for instant reclaim:

1. **`Database.emptyRecycleBin(List<SObject>)`** — call in the batch `finish()` method, passing the IDs of deleted records. This permanently removes them.
2. **Bulk API HARD_DELETE** — set the operation to `hardDelete` in a Bulk API job. Records bypass the Recycle Bin entirely. Requires the "Hard Delete" system permission.

### Retention Policy Filtering with SOQL Date Literals

Filter records by age using SOQL date literals. `CreatedDate < LAST_N_DAYS:30` selects records created more than 30 days ago. `CreatedDate < LAST_N_YEARS:7` selects records older than 7 years. For custom retention fields, use `Retention_Date__c < TODAY`. Always add a selective index-friendly filter (e.g., on `CreatedDate` or a custom indexed field) to avoid full-table scans on large objects. Use `LIMIT` in test queries but not in the `QueryLocator` — the batch framework handles chunking.

---

## Common Patterns

### Pattern 1: Nightly Scheduled Batch with Soft Delete and Recycle Bin Empty

**When to use:** Regular purge of temporary records (debug logs, staging records, integration scratch objects) where permanent deletion is needed but the volume is moderate (under 5 million rows per run).

**How it works:**
1. Implement `Database.Batchable<SObject>` — `start()` queries records past retention threshold.
2. `execute()` calls `Database.delete(scope, false)` and logs failures.
3. `finish()` calls `Database.emptyRecycleBin()` with the deleted IDs to immediately reclaim storage.
4. A `Schedulable` wrapper registers the batch via `System.schedule()` with a nightly cron.

**Why not the alternative:** Running deletion in a single scheduled class (without Batch Apex) fails above ~10,000 records per night due to DML and CPU governor limits. Flow-based deletion has even lower throughput and no retry mechanism.

### Pattern 2: Bulk API Hard Delete for High-Volume Retention Jobs

**When to use:** Monthly or quarterly retention runs deleting millions of records where Batch Apex throughput is insufficient or where avoiding Recycle Bin pollution is critical (e.g., compliance-driven purge).

**How it works:**
1. Create a Bulk API 2.0 ingest job with `operation: hardDelete` and `object: YourObject__c`.
2. Upload a CSV of record IDs to delete — sourced from a prior SOQL query or export.
3. Close the job and poll for completion. Records are permanently deleted without entering the Recycle Bin.
4. Requires the "Bulk API Hard Delete" permission assigned to the integration user.

**Why not the alternative:** Batch Apex calling `Database.emptyRecycleBin()` still creates transient Recycle Bin entries that briefly inflate storage metrics. Hard delete via Bulk API is the cleanest path for compliance scenarios.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Nightly purge under 5M records, Apex team | Batch Apex + `emptyRecycleBin()` in `finish()` | Full control, partial-failure handling, audit logging |
| Monthly compliance purge of millions of records | Bulk API 2.0 HARD_DELETE job | Highest throughput, bypasses Recycle Bin entirely |
| Ad-hoc one-time cleanup of a small object | Data Loader delete + Manual Recycle Bin empty | Simplest; no code required |
| Cascading parent-child deletion at scale | Batch Apex deleting parent records only | Master-detail auto-cascade handles children; reduces DML calls |
| Retention enforcement with custom date field | Batch Apex with `Retention_Date__c < TODAY` filter | Explicit date field is indexable and auditable |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify scope.** Confirm the sObject, retention period, expected record volume, and whether permanent deletion is required. Run a `SELECT COUNT()` with the retention filter before writing any delete code.
2. **Check cascade risk.** For each object being deleted, list its master-detail child relationships. Query child counts to confirm the cascade volume is acceptable. Adjust batch size down if children are numerous.
3. **Implement the Batch Apex class.** Write `Database.Batchable<SObject>` with a `QueryLocator` using the retention SOQL filter. Use `Database.delete(scope, false)` in `execute()`. Capture `DeleteResult[]` and log failures. In `finish()`, call `Database.emptyRecycleBin()` if immediate storage reclaim is required.
4. **Implement the Schedulable wrapper.** Write a `Schedulable` class that calls `Database.executeBatch()` with the appropriate batch size. Register via `System.schedule()` in Anonymous Apex or a deployment script. Confirm the scheduled job appears in Setup > Scheduled Jobs.
5. **Write tests with `@TestSetup`.** Insert test records explicitly — never use `SeeAllData=true` for deletion tests. Verify that records past the threshold are deleted and records within the threshold survive. Assert `Database.DeleteResult` success flags. Test the scheduler class separately.
6. **Validate storage impact.** After the first production run, check Setup > Company Information > Data Storage Used and confirm the recycle bin is emptied as expected.
7. **Monitor and alert.** Use the `finish()` method to send an email or create a Platform Event with job summary (records deleted, failures). Set up a Scheduled Job failure alert in Setup > Monitoring.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Retention SOQL filter uses an indexed field (`CreatedDate` or custom indexed field) to avoid full-table scan
- [ ] `Database.delete(scope, false)` used (not bare `delete`) so a single failure does not roll back the chunk
- [ ] `DeleteResult[]` failures are logged to a custom object or Platform Event for audit
- [ ] `Database.emptyRecycleBin()` or HARD_DELETE strategy is in place if storage reclaim is required
- [ ] Cascade deletion volume has been estimated for all master-detail children
- [ ] Batch Apex test uses `@TestSetup` (never `SeeAllData=true`) with explicit insert of test data
- [ ] Scheduled job is registered and visible in Setup > Scheduled Jobs
- [ ] Job completion notification is wired into `finish()` method

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Recycle Bin counts against storage until emptied** — Standard `delete` does not immediately free storage. Records occupy data storage for up to 15 days until automatic purge. On large cleanup runs this can temporarily inflate storage usage and trigger storage limit alerts. Always call `Database.emptyRecycleBin()` in `finish()` or use HARD_DELETE.
2. **Cascade deletion multiplies record counts unexpectedly** — Deleting a master record in a master-detail relationship automatically deletes all detail records. Deleting 10,000 parent Accounts may cascade to 200,000 Contact and Opportunity child records. This can consume DML row limits, trigger storage spikes, and cause unintended data loss. Always run a child count query before the first production run.
3. **`SeeAllData=true` in deletion tests corrupts shared test data** — If a batch test uses `@isTest(SeeAllData=true)` and deletes records, it may delete real org data in the test sandbox if test isolation is not enforced. Always use `@TestSetup` with explicit record inserts and `@isTest(SeeAllData=false)` (the default).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Batch Apex class | `Database.Batchable<SObject>` implementation with retention filter, partial-delete handling, and optional `emptyRecycleBin()` call |
| Schedulable wrapper class | `Schedulable` implementation that dispatches the batch with correct batch size |
| Error log records | Custom object or Platform Event records capturing failed `DeleteResult` rows for audit |
| Batch cleanup template | `templates/batch-data-cleanup-patterns-template.md` — copy-paste starting point |

---

## Related Skills

- `data/data-archival-strategies` — Use when records must be preserved in Big Objects or exported to external storage before deletion
- `apex/batch-apex-patterns` — General Batch Apex patterns including stateful aggregation, chaining, and error handling
- `apex/apex-scheduled-jobs` — Scheduling Apex jobs, cron syntax, managing scheduled job limits
- `data/data-quality-and-governance` — Data retention governance, GDPR right-to-erasure, anonymization vs deletion decisions
