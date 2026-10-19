# Worked Example — One-Off Hard Delete of 1.2 Million Staging Rows, Then a Nightly Job

**Situation:** `Staging_Order__c` holds 1.2 million rows from a retired integration. Policy: rows older than 90 days must be unrecoverable. After the backlog is gone, a nightly job keeps it clean (about 8,000 new rows a day).

## Part 1: The backlog, with Bulk API 2.0 `hardDelete`

The LDV guide recommends the Bulk API hard delete option for deletes of one million or more records, and hard-deleted records skip the Recycle Bin. The running user needs the "Bulk API Hard Delete" permission, which is off by default.

1. Extract Ids with a Bulk API 2.0 query job, using a bound cutoff:

```json
{
  "operation": "query",
  "query": "SELECT Id FROM Staging_Order__c WHERE CreatedDate < 2026-07-21T00:00:00Z"
}
```

2. Create the ingest job:

```json
{
  "object": "Staging_Order__c",
  "operation": "hardDelete",
  "contentType": "CSV",
  "lineEnding": "LF"
}
```

3. `PUT` the CSV (a single `Id` column) to the job's `batches` resource, then `PATCH` the job with `{"state": "UploadComplete"}`.
4. Poll the job until `JobComplete` or `Failed`, then download `failedResults/` and `unprocessedRecords/`.
5. Reconcile: query count before minus rows in `successfulResults/` must equal the count after. Investigate every failed row before re-running only those Ids.

## Part 2: The nightly job

| Decision | Value | Why |
|---|---|---|
| Cutoff | `Date.today().addDays(-90)`, bound | Rolling policy; `LAST_N_DAYS` starts at midnight and is easy to misread |
| Batch size | 200 | No master-detail children on `Staging_Order__c` (checked) |
| Purge | `emptyRecycleBin` per chunk | Policy says unrecoverable; 200 Ids per call is far under the 10,000 limit |
| Schedule | `'0 0 2 * * ?'` | 2:00 AM in the scheduling user's time zone |
| Failure record | Count in `Database.Stateful`, detail rows in `Cleanup_Error_Log__c` | Audit trail for the policy owner |

Release runbook entry, because a class with an active scheduled job can't be deployed by default:

```text
Before deploying RetentionPurgeBatch or its scheduler:
  1. Setup > Scheduled Jobs: delete "Nightly Staging Purge" (note the cron).
  2. Deploy.
  3. Re-run: System.schedule('Nightly Staging Purge', '0 0 2 * * ?', new StagingPurgeScheduler());
  4. Confirm the job is listed again with the next run time.
```

## Part 3: Test plan

| Test | Setup | Assertion |
|---|---|---|
| Deletes only expired rows | Insert 10 rows; `Test.setCreatedDate` on 5 to 95 days ago | 5 remain after `Test.stopTest()` |
| Partial failure is counted | Make one expired row undeletable in the test (for example, reference it from a record that blocks deletion) | Failure count is 1 and the error row is logged |
| Scheduler registers | `System.schedule` inside `Test.startTest()` | A `CronTrigger` row exists for the job name |

A batch test runs only one `execute`, so keep test rows at or under the scope passed to `executeBatch`.
