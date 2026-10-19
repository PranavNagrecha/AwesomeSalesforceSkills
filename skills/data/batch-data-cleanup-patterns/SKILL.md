---
name: batch-data-cleanup-patterns
description: "Use when scheduling automated deletion of temporary records, enforcing data retention policies, running nightly cleanup jobs, reclaiming org storage, managing recycle bin, or performing async bulk deletion of aged records. Trigger keywords: batch delete, retention policy, purge records, cleanup job, recycle bin, emptyRecycleBin, hard delete, nightly purge, storage optimization. NOT for archiving records to Big Objects or external storage instead of deleting them — use data/data-archival-strategies. NOT for deleting unused fields, flows and other metadata — use admin/org-cleanup-and-technical-debt."
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
  - "permanently delete records older than seven years so they cannot be restored"
  - "schedule a batch purge without blocking deployments of the cleanup class"
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
  - "Optional per-chunk emptyRecycleBin() call in execute() so deleted rows cannot be restored (Recycle Bin rows do not count against storage)"
  - "Error log or custom object record capturing partial-delete failures"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# Batch Data Cleanup Patterns

This skill activates when records must be deleted on a schedule — retention enforcement, purging temporary or staging records, or permanent removal for compliance — without keeping a copy elsewhere. Use `data/data-archival-strategies` when records must be preserved in a big object or external store first.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Object, filter, and cutoff.** The sObject, the age field (`CreatedDate`, `LastModifiedDate`, or a retention date field), and whether the cutoff is rolling ("older than 2,555 days") or calendar-aligned ("before 1 January seven years ago").
- **Why the records are being deleted.** Query performance, a policy that requires permanent deletion, or storage. Recycle Bin rows don't count against storage, but they are restorable for 15 days and still weigh on queries.
- **What else goes with them.** Master-detail children are deleted with their parent, and so is each record's field history.
- **Volume per run.** Drives batch size, whether `emptyRecycleBin` fits (10,000 records per call), and whether Bulk API 2.0 hard delete is the better tool.
- **Who runs it.** Hard delete through the Bulk API needs the "Bulk API Hard Delete" permission, which is off by default.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Must deleted records be unrecoverable, or is a 15-day restore window acceptable?" | A plain delete leaves records restorable in the Recycle Bin for 15 days (Gotcha 1) | A per-chunk `emptyRecycleBin` or a Bulk API 2.0 `hardDelete` job, only when policy needs it |
| "Is the cutoff exactly N days back, or by calendar year?" | `LAST_N_YEARS:n` is calendar-year based, so it does not mean "older than n×365 days" (Gotcha 4) | A bound `Date` cutoff computed in Apex, or a documented calendar rule |
| "Which master-detail children and field history go with these records, and does anyone need them?" | Deleting a parent deletes its detail records and its field history (Gotcha 2) | A child count and an export or archive decision before the first run |
| "How many records will one run delete?" | `emptyRecycleBin` accepts 10,000 records per call and counts as a DML statement (Gotcha 3) | Per-chunk purging and a batch size that fits |
| "Will anyone deploy changes to the cleanup class while it is scheduled?" | By default you can't deploy an Apex class that has active jobs (Gotcha 5) | A runbook step to pause the job, or the deployment setting turned on deliberately |
| "Could this job be launched from a trigger or by several schedules at once?" | Only five batch jobs run at a time and the flex queue holds 100 (Gotcha 6) | One dispatcher schedule instead of per-record launches |
| "Does the cleanup release include destructive metadata changes?" | A roll-up summary field deleted through Metadata API is purged with no Recycle Bin, and `purgeOnDelete` doesn't work in production (Gotcha 7) | A one-way-door step in the runbook with exported values |

A proper cleanup design adds a cutoff that means what the policy says, failure logging per record, and a restore decision made up front; a quick delete job leaves recoverable data the policy said was gone, or deletes children nobody counted.

---

## Core Concepts

### Batch Apex for deletion

`start()` returns a `Database.QueryLocator` (up to 50 million records), `execute()` receives chunks (200 by default; a QueryLocator scope above 2,000 is chunked to 2,000), and each `execute()` is its own transaction with its own limits, including 10,000 DML rows. Use `Database.delete(scope, false)` so one failing record does not roll back the chunk, and record every failed `DeleteResult`.

### Recycle Bin, purge, and hard delete

| Mechanism | Restorable afterwards? | Notes |
|---|---|---|
| `delete` / `Database.delete` | Yes, for 15 days | Rows still have to be excluded from queries; they don't count against storage |
| `Database.emptyRecycleBin(ids)` | No | 10,000 records per call; counts as a DML statement; don't include cascade-deleted child Ids |
| Bulk API 2.0 `hardDelete` | No | Records skip the Recycle Bin; needs "Bulk API Hard Delete"; recommended by the LDV guide for deletes of a million or more |

### Scheduling

A `Schedulable` class calls `Database.executeBatch`; `System.schedule(name, cron, instance)` registers it. Cron syntax is `Seconds Minutes Hours Day_of_month Month Day_of_week Optional_year` in the scheduling user's time zone, so `'0 0 2 * * ?'` is 2:00 AM daily. An org can have 100 scheduled Apex jobs at one time.

### Deploying the class

Every class ships with a `.cls-meta.xml`. Because a scheduled cleanup keeps a job active against the class, plan deployments around it.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- classes/RetentionPurgeBatch.cls-meta.xml -->
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## Common Patterns

### Pattern 1: Nightly purge with per-chunk Recycle Bin purge

```apex
public with sharing class RetentionPurgeBatch implements Database.Batchable<SObject>, Database.Stateful {
    private final Date cutoff;
    private Integer deleted = 0;
    private Integer failed = 0;

    public RetentionPurgeBatch(Integer retentionDays) {
        this.cutoff = Date.today().addDays(-retentionDays);
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            [SELECT Id FROM Integration_Log__c WHERE CreatedDate < :cutoff]
        );
    }

    public void execute(Database.BatchableContext bc, List<Integration_Log__c> scope) {
        List<Database.DeleteResult> results = Database.delete(scope, false);
        List<Id> purge = new List<Id>();
        for (Integer i = 0; i < results.size(); i++) {
            if (results[i].isSuccess()) {
                purge.add(scope[i].Id);
                deleted++;
            } else {
                failed++;
            }
        }
        if (!purge.isEmpty()) {
            Database.emptyRecycleBin(purge);
        }
    }

    public void finish(Database.BatchableContext bc) {
        System.debug(LoggingLevel.INFO, 'Retention purge: deleted=' + deleted + ' failed=' + failed);
    }
}
```

The scope stays within the 10,000-record `emptyRecycleBin` limit because it is purged chunk by chunk; collecting every Id for `finish()` would not.

### Pattern 2: Bulk API 2.0 hard delete for large one-off purges

Create an ingest job with `"operation": "hardDelete"`, upload a CSV with an `Id` column, close the job (`UploadComplete`), then read `failedResults/`. The running user needs "Bulk API Hard Delete". See `data/bulk-api-patterns` for the job lifecycle.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| Recurring purge, records must be unrecoverable | Batch Apex with per-chunk `emptyRecycleBin` | Purges within the 10,000-per-call limit, logs each failure |
| One-off purge of a million or more records | Bulk API 2.0 `hardDelete` | LDV guide recommendation; skips the Recycle Bin |
| Recurring purge, restore window acceptable | Batch Apex with `Database.delete(scope, false)` only | Simplest; rows are purged automatically after 15 days |
| Parent records with master-detail children | Count children first; lower the batch size or purge children in their own job | Children are deleted with the parent |
| Calendar-year retention policy | `LAST_N_YEARS:n` with the rule written down | Literal is calendar-aligned |
| Rolling retention policy | Bound `Date` cutoff computed in Apex | Exact and testable |

---

## Recommended Workflow

1. Fill `templates/batch-data-cleanup-patterns-template.md`: object, cutoff rule (rolling or calendar), restore requirement, expected volume, and master-detail children with counts.
2. Run `SELECT COUNT()` with the exact cutoff filter and a child-count query in a full-copy sandbox; record both.
3. Build the batch from Pattern 1 (or a Bulk API 2.0 `hardDelete` job from Pattern 2; `references/worked-example.md` walks through both), plus a `Schedulable` wrapper and `.cls-meta.xml` files.
4. Run `python3 skills/data/batch-data-cleanup-patterns/scripts/check_batch_data_cleanup_patterns.py --manifest-dir force-app/main/default` and fix every ERROR.
5. Write tests that insert records on both sides of the cutoff, run the batch between `Test.startTest()` and `Test.stopTest()` with a scope that covers all test rows, and assert survivors and deletions.
6. Schedule with `System.schedule`, confirm the job under Setup > Scheduled Jobs, and add the "pause before deploy" step to the release runbook.

---

## Review Checklist

- [ ] The cutoff is a bound `Date` (rolling) or a documented calendar rule, not an assumed `LAST_N_YEARS` meaning
- [ ] `Database.delete(scope, false)` with every failure counted or logged
- [ ] `emptyRecycleBin` is called per chunk, never with more than 10,000 Ids
- [ ] Master-detail children and field history were counted and signed off
- [ ] Tests insert their own data on both sides of the cutoff; no `SeeAllData=true`
- [ ] The release runbook pauses the scheduled job before deploying the class
- [ ] The checker reports no ERROR lines

---

## Salesforce-Specific Gotchas

Full write-ups are in `references/gotchas.md`:

| # | Gotcha |
|---|---|
| 1 | Deleted is not gone: Recycle Bin rows are restorable for 15 days |
| 2 | Deleting a parent deletes its detail records and its field history |
| 3 | `emptyRecycleBin` takes 10,000 records per call |
| 4 | `LAST_N_YEARS` is calendar-aligned |
| 5 | Scheduled jobs block deployments of the class |
| 6 | Batch launches from triggers hit the concurrency limits |
| 7 | Roll-up summary fields deleted through Metadata API are purged at once |
| 8 | Intake purges must hard-delete, and metrics must not live on the purged row |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Batch Apex class | Retention filter, partial-failure handling, per-chunk purge |
| Schedulable wrapper | Dispatches the batch with an explicit scope |
| `.cls-meta.xml` files | Deployable class metadata |
| Failure log | Counts or records for failed deletes |
| Filled template | `templates/batch-data-cleanup-patterns-template.md` |

---

## Related Skills

- `data/data-archival-strategies` — preserve records in a big object or external store before deleting
- `data/bulk-api-patterns` — Bulk API 2.0 job lifecycle for `hardDelete`
- `apex/batch-apex-patterns` — stateful batches, chaining, and error handling in general
- `apex/apex-scheduled-jobs` — cron syntax and managing scheduled jobs
- `data/data-quality-and-governance` — retention governance and erasure decisions
- `admin/org-cleanup-and-technical-debt` — deleting unused fields and other metadata
