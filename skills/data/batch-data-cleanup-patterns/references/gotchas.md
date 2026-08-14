# Gotchas — Batch Data Cleanup Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Recycle Bin Counts Against Data Storage — Standard Delete Does Not Free Space

**What happens:** When records are deleted using standard Apex `delete` or Data Loader delete, they move to the Recycle Bin rather than being permanently removed. Records in the Recycle Bin continue to count against the org's data storage allocation for up to 15 days until automatic purge. A nightly batch that deletes 500,000 records per run can cause storage to appear unchanged (or even grow) in the days immediately after the job.

**When it occurs:** Any batch cleanup job that uses bare `delete` DML or `Database.delete()` without a subsequent `Database.emptyRecycleBin()` call. Especially visible in orgs with tight storage budgets or compliance requirements for permanent deletion.

**How to avoid:** Call `Database.emptyRecycleBin(List<SObject>)` in the batch `finish()` method (or per chunk in `execute()` for very large jobs). Alternatively, use Bulk API 2.0 with `operation: hardDelete` — this bypasses the Recycle Bin entirely. The "Hard Delete" system permission must be assigned to the running user or integration credential.

---

## Gotcha 2: Cascade Deletion in Master-Detail Relationships Deletes More Records Than Expected

**What happens:** Deleting a master record in a master-detail relationship automatically and permanently deletes all detail records — even if the detail object was not part of the cleanup scope. For example, deleting an Account that has master-detail children (custom invoices, order line items) deletes all those children in the same transaction. This can multiply the actual row count deleted by an order of magnitude and trigger DML limit exceptions or unintended data loss.

**When it occurs:** Batch cleanup jobs targeting parent objects (Account, Opportunity, a custom master object) when detail records exist in related objects. Most dangerous when the detail object is not well-known or when the relationship was added after the cleanup pattern was originally designed.

**How to avoid:** Before writing any delete code, run a query to count child records: `SELECT COUNT() FROM Detail_Object__c WHERE Master__c IN :parentIds`. If child counts are high, reduce batch size to stay within per-transaction DML row limits (10,000 rows), or delete child records explicitly in a separate batch before the parent batch runs. Document cascade relationships in the cleanup runbook.

---

## Gotcha 3: `@isTest(SeeAllData=true)` in Deletion Tests Corrupts Shared Test Data

**What happens:** If a batch Apex test class uses `@isTest(SeeAllData=true)` and runs deletion logic, it can delete real existing records from the org's test or sandbox environment. This is because `SeeAllData=true` exposes all records visible to the test user. A deletion batch that matches on `CreatedDate < LAST_N_DAYS:30` will delete any matching records in the org — not just test-inserted data.

**When it occurs:** Developers use `SeeAllData=true` to avoid inserting test data, particularly when the cleaned-up object is complex to set up in isolation.

**How to avoid:** Always use `@isTest(SeeAllData=false)` (the default) and `@TestSetup` to explicitly insert test records. Create records both inside and outside the retention threshold to verify that the batch deletes only the correct subset. Never use `SeeAllData=true` in any test class that exercises deletion or update DML.

---

## Gotcha 4: `Database.executeBatch()` Cannot Be Called from a Trigger with Pending DML

**What happens:** Calling `Database.executeBatch()` inside an Apex trigger (or any context with uncommitted work in the current transaction) throws a runtime exception: "System.AsyncException: Database.executeBatch cannot be called from a batch start, batch execute, or future method." A related variant is "You have uncommitted work pending" when trying to launch a batch from within a trigger that has already performed DML.

**When it occurs:** Developers try to trigger a cleanup batch from within a record save flow — for example, launching a purge batch every time a record is updated. Also triggered when calling `executeBatch` inside another batch's `execute()` method (chaining must happen in `finish()` only).

**How to avoid:** Never call `Database.executeBatch()` from a trigger's DML context. Use a Schedulable class registered via `System.schedule()` for time-based cleanup. If the cleanup must be event-driven, publish a Platform Event from the trigger and handle batch dispatch in an asynchronous subscriber.

---

## Gotcha 5: Batch Size Too Large Causes DML Row Limit Exceptions When Cascade Children Are Numerous

**What happens:** The default batch size of 200 is too large when each parent record has many master-detail children. If deleting 200 parent records cascades to 10,000+ child records in the same transaction, the 10,000 DML row limit is breached and the chunk fails entirely — but only that chunk, not the whole job (since `allOrNone=false`). This can result in silently skipped records if errors are not logged.

**When it occurs:** Cleanup jobs on objects with heavy master-detail children (e.g., deleting Orders that have 100+ Order Products each), particularly when the cleanup was designed without checking cascade volumes.

**How to avoid:** Query the average child count before setting the batch size: if each parent has an average of N children, set batch size to `floor(10000 / N)` rounded down to a safe number. Common safe sizes: 50 (when cascading 100+ children), 100 (20–50 children), 200 (few or no children). Always log `DeleteResult` failures so silently skipped records are visible.

---

## Gotcha 6: Deleting a Roll-Up Summary Field via Metadata API Bypasses the Recycle Bin Unconditionally

**What happens:** Cleanup work often ships as a `destructiveChanges.xml` deployment alongside the record purge — dropping the staging fields and roll-ups the retired data fed. A custom field deleted that way normally lands in the Recycle Bin and can be restored; you opt out of that by setting the `purgeOnDelete` deployment option to true. Roll-up summary fields are the exception: per the Metadata API Developer Guide, a roll-up summary field deleted through the Metadata API is not saved in the Recycle Bin and is purged even when `purgeOnDelete` is left false. There is no undelete, and the aggregate values stored on the parent records go with it.

**When it occurs:** Any destructive deployment containing a `CustomField` member that happens to be a roll-up summary — including the routine "delete it and re-create it with a corrected filter" refactor, which reads as reversible but is not.

**How to avoid:** Treat roll-up summary deletion as a one-way door in the cleanup runbook, separate from the reversible destructive changes. Export the current values (`SELECT Id, Rollup__c FROM Object__c`) first if any report, formula, or integration reads them, and remember that a re-created roll-up recalculates only from surviving detail records — child rows the purge already removed are never reflected again. Where only the filter criteria need to change, edit the roll-up in place instead of dropping and re-adding it.

---

## Gotcha 7: Intake Purge Must Hard-Delete, and Metrics Must Not Live on the Purged Row

**What happens:** Salesforce is a pass-through: after TTL the application is deleted, but `delete` leaves 15 days in the Recycle Bin. Compliance still has recoverable PII. Funnel counts lived on the Application (or in an LTA JSON on it) — they die with the row. Back-office cannot look up "what did this person file?" in Salesforce; the document store is the record.

**When it occurs:** Experience Cloud guest or logged-in intake where Salesforce is not the system of record.

**How to avoid:** Call `Database.emptyRecycleBin` in batch `execute()` (per chunk), not only in `finish()` after a huge scope has sat in the bin. Emit **non-PII** section-lifecycle events (id, section, timestamp) so measurement survives. Do not purge until the evidence artifact (PDF object id in the document store, not the blob in Salesforce) is confirmed. Null PII fields on absolute session TTL even before the delete job runs.
