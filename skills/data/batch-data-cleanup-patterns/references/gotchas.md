# Gotchas — Batch Data Cleanup Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deleted Is Not Gone — Recycle Bin Rows Are Restorable for 15 Days

**What happens:** A retention job "deletes" records that policy says must be unrecoverable, and they can still be restored for 15 days. Separately, teams expect the purge to change Storage Usage and are confused when emptying the bin does not.

**When it occurs:** Any job using `delete` or `Database.delete` alone. The LDV guide says deleted items stay in the Recycle Bin for 15 days, after which they are scheduled for hard deletion at no guaranteed time; Recycle Bin items don't count against storage usage; and soft-deleted data still affects database performance because it must be excluded from queries.

**How to avoid:** When policy requires permanent deletion, call `Database.emptyRecycleBin` per chunk or use a Bulk API 2.0 `hardDelete` job, whose records "aren't stored in the Recycle Bin." Count storage savings from the delete itself, not from the purge.

---

## Gotcha 2: Deleting a Parent Deletes Its Detail Records and Its Field History

**What happens:** A job targeting one object removes far more data than planned: master-detail children, and the field history of every deleted record.

**When it occurs:** The Apex Reference Guide's `emptyRecycleBin` notes give the cascade example: when an account is deleted, related contacts, opportunities, contracts, and so on are deleted too. The Security guide says a delete "cascades to the related history tracking records." Whether the cascaded rows count toward the transaction's 10,000 DML-row limit is not stated in the guides used here; measure it in a sandbox with `Limits.getDmlRows()` after deleting one parent with a known child count before choosing a batch size.

**How to avoid:** Count children per parent before the first run, export or archive what must survive, and lower the batch size (or purge children in their own job first) for heavy parents.

---

## Gotcha 3: `emptyRecycleBin` Takes 10,000 Records per Call

**What happens:** A batch collects every deleted Id in a `Database.Stateful` list and calls `emptyRecycleBin` once in `finish()`. With more than 10,000 Ids the call fails, and the whole night's deletes stay restorable.

**When it occurs:** The Apex Reference Guide: "Only 10,000 records can be specified for deletion." Each call also counts against the DML statement limit, and its records count toward rows processed. Including the Ids of cascade-deleted children causes an error; only the top-level Ids belong in the list.

**How to avoid:** Purge inside `execute()`, once per chunk, with only the Ids that `Database.delete` reported as successful.

---

## Gotcha 4: `LAST_N_YEARS` Is Calendar-Aligned

**What happens:** `WHERE CreatedDate < LAST_N_YEARS:7` is written as "older than seven years," but it keeps up to almost a year of extra data, and the boundary jumps on 1 January.

**When it occurs:** The SOQL reference defines `LAST_N_YEARS:n` as starting on January 1 and ending on December 31 of the year before the current year, so `<` compares against a January 1 boundary rather than today minus seven years. `LAST_N_DAYS:n` starts at 12:00 AM n days before today and includes today, so `< LAST_N_DAYS:30` excludes everything from that midnight onward. UNVERIFIED (2026-10-19): both literal definitions come from the SOQL and SOSL Reference date-literals page, which is not in the local PDF corpus; the bound-Date fix below does not depend on them.

**How to avoid:** For rolling retention, compute the cutoff in Apex (`Date.today().addYears(-7)` or `addDays(-n)`) and bind it. Use the literals only when the policy really is calendar-based, and write that rule into the runbook.

---

## Gotcha 5: Scheduled Jobs Block Deployments of the Class

**What happens:** A fix to the cleanup class fails to deploy because the class has an active scheduled job.

**When it occurs:** The Metadata API guide: "By default, you can't deploy updates to an Apex class if there are one or more active jobs for that class." The options are to cancel the jobs and reschedule after deployment, or to enable deployments with Apex jobs in Deployment Settings.

**How to avoid:** Put "abort the scheduled job, deploy, reschedule" in the release runbook, or make an explicit decision to allow deployments with active jobs.

---

## Gotcha 6: Batch Launches From Triggers Hit the Concurrency Limits

**What happens:** A trigger launches a cleanup batch on every save; a bulk update fires it many times, and jobs pile up or fail to enqueue.

**When it occurs:** The Apex guide allows invoking batch jobs from triggers but warns to use extreme caution and to guarantee the trigger can't add more batch jobs than the limit, especially for API bulk updates, import wizards, and mass changes. Only five batch jobs can be queued or active at once, and the flex queue holds up to 100 in Holding status. Separately, an org can have 100 scheduled Apex jobs at one time.

**How to avoid:** Run cleanup from one scheduled dispatcher. If an event must request cleanup, record the request and let the scheduled job pick it up.

---

## Gotcha 7: Roll-Up Summary Fields Deleted Through Metadata API Are Purged at Once

**What happens:** A cleanup release drops staging fields with `destructiveChanges.xml`. A roll-up summary field among them is gone for good, with its values.

**When it occurs:** The Metadata API guide: "When you delete a roll-up summary field using Metadata API, the field isn't saved in the Recycle Bin. The field is purged even if you don't set the purgeOnDelete deployment option to true." The `purgeOnDelete` option itself only works in Developer Edition and sandbox orgs, not in production.

**How to avoid:** Treat roll-up summary deletion as irreversible: export the values first, and edit a roll-up in place rather than dropping and recreating it when only its filter changes. A recreated roll-up only recalculates from detail records that still exist.

---

## Gotcha 8: Intake Purges Must Hard-Delete, and Metrics Must Not Live on the Purged Row

**What happens:** Salesforce is a pass-through for an intake form. After the time-to-live the application is deleted, but it sits in the Recycle Bin for 15 days, so personal data is still recoverable. Funnel counts stored on the application die with the row.

**When it occurs:** Experience Cloud guest or logged-in intake where Salesforce is not the system of record.

**How to avoid:** Purge per chunk in `execute()`. Emit non-personal lifecycle events (record id, section, timestamp) so measurement survives the delete. Confirm the evidence artifact exists in the document store before purging, and clear personal fields when the session expires, even before the delete job runs.
