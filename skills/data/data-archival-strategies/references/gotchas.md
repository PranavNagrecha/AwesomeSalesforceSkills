# Gotchas — Data Archival Strategies

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Big Object Rows Cannot Be Changed With Standard DML

**What happens:** Code that treats a `__b` object like an sObject (`update archiveRows;`, `delete archiveRows;`, a flow on the big object) fails. Big objects are a non-transactional, horizontally scalable store; triggers, flows, and processes aren't supported on them.

**When it occurs:** Archive jobs ported from a custom-object prototype, or "fix-up" scripts written after a bad load.

**How to avoid:** Write with `Database.insertImmediate()`; to change a row, reinsert it with the same index values (the reinsert overwrites). Delete with `Database.deleteImmediate()` or SOAP `deleteByExample()`, specifying every index field; partial indexes, non-indexed fields, and wildcards aren't allowed, and the limit is 50,000 records per call. After deleting everything for capacity reasons, the guide says to insert one or two blank records and wait 24 hours for the new capacity to be recognized.

---

## Gotcha 2: The Read Path Is the Part Nobody Tests Until It Is Too Late

**What happens:** Records are written to the archive, the source is deleted, storage drops, and the project closes. Months later an auditor asks for the data and the planned retrieval does not work: the query does not match the index, or the chosen API cannot read big objects.

**When it occurs:** The Big Objects guide lists SOQL, Bulk API, Chatter, and SOAP APIs as the only APIs supported for big objects, and says the REST API, for example, isn't supported. Designs built on another mechanism (a REST integration, a report, or older Async SOQL guidance) fail on first use. Queries must also follow the index: in the guide's delete example, fields "must be listed in the order they appear in the index, without any gaps."

**How to avoid:** Make the restore test a deliverable. Run the real retrieval (SOQL on an index prefix, and a Bulk API 2.0 query job for volume, which the guide says supports big objects) against archived rows before any production delete, and have the data owner sign off on the results.

---

## Gotcha 3: Emptying the Recycle Bin Helps Queries, Not Storage

**What happens:** A team responds to a storage alert by emptying the Recycle Bin and sees no change, or budgets storage savings from "clearing the bin."

**When it occurs:** The LDV guide says items in the Recycle Bin don't count against an org's storage usage and there is no limit on how many it can hold. It also says soft-deleted data "still affects database performance" because deleted records have to be excluded from every query; one of its case studies kept the Recycle Bin empty to speed up a report.

**How to avoid:** Count storage savings only from records removed from live objects. Empty the Recycle Bin (or use Bulk API hard delete for large deletes, which the LDV guide recommends for a million or more records) when the goal is query performance. `Database.emptyRecycleBin()` accepts 10,000 records per call and counts against the DML statement limit.

---

## Gotcha 4: Deleting a Record Deletes Its Field History Too

**What happens:** An archive job copies parent fields to a big object and deletes the source. Later, the compliance team asks for the field-change history of those records, and it is gone.

**When it occurs:** The Security guide: "If you delete a record in your production data, the delete cascades to the related history tracking records," while Field Audit Trail copies already in `FieldHistoryArchive` are not deleted. Without Field Audit Trail, field history is only kept up to 18 months (24 months via the API) in any case. Field history does not count against data storage, so it is never a storage reason to delay deletion.

**How to avoid:** Decide before deletion whether history must survive. If so, turn on Field Audit Trail and deploy a `HistoryRetentionPolicy` so history is copied into `FieldHistoryArchive` first, or export the `<Object>History` rows into the archive.

---

## Gotcha 5: `insertImmediate` Reports Failures Instead of Throwing

**What happens:** An archive batch calls `Database.insertImmediate(rows)`, sees no exception, deletes the source rows, and some rows never reached the archive.

**When it occurs:** The Big Objects guide: "If a record insert fails, the Database.insertImmediate() method doesn't throw an exception. Instead, it returns a SaveResult object." It also says partial batch failures are expected in this distributed store and advises: "Don't try to figure out which records succeeded and which failed. Retry the entire batch."

**How to avoid:** Inspect every `SaveResult`. If any failed, retry the whole batch (writes are idempotent), and delete the source only after a fully successful write.

---

## Gotcha 6: Big Object Writes Are Callouts, So Order Matters in a Transaction

**What happens:** An execute method deletes or updates source records first and then writes the archive, and the write fails.

**When it occurs:** The Big Objects guide says DML operations on big objects "are considered callouts, so Apex execution governors and limits for callouts apply," and the Apex Developer Guide says callouts aren't allowed after DML operations in the same transaction by default. The guide also recommends asynchronous Apex for big object writes from a trigger, process, or flow on an sObject. Big object DML does not count toward the DML statement limit.

**How to avoid:** In each `execute`, write to the big object first, then do sObject DML. Run archive writes from Batch or Queueable Apex, never from a trigger.

---

## Gotcha 7: A Big Object Index Is Permanent and Tightly Constrained

**What happens:** A deployed archive turns out to need a different query key, or a deployment fails on index rules.

**When it occurs:** "After you've deployed a big object, you can't edit or delete the index. To change the index, start over with a new big object." Index fields must be marked required; LongTextArea and URL fields can't be in the index; the text fields in an index can total at most 100 characters (Email fields count as 80, Phone as 40) unless Support raises it.

**How to avoid:** Design the index from the read questions, put the most selective leading field first, and validate the definition (the skill's checker enforces these rules) before the first deployment.

---

## Gotcha 8: Custom Big Objects Store Encrypted Source Data as Clear Text

**What happens:** Fields encrypted with Shield Platform Encryption on the source object are archived unencrypted.

**When it occurs:** The Big Objects guide: "Big objects don't support encryption. If you archive encrypted data from a standard or custom object, it's stored as clear text on the big object." Field history archived through Field Audit Trail is handled by the Shield field history archive instead, but the Security guide notes that history already archived before Platform Encryption was turned on stays unencrypted until Salesforce re-archives it.

**How to avoid:** List encrypted fields before designing the archive, and get explicit sign-off before writing any of them to a custom big object, or leave them out.

---

## Gotcha 9: Whitespace and Nulls Behave Unexpectedly in Big Object Writes

**What happens:** A row written with a trailing space in an index field can never be matched or deleted; a reinsert intended to clear a value leaves the old value in place.

**When it occurs:** SOQL trims leading and trailing white space from WHERE values on index fields, so stored values with white space are never matched, and the Index metadata notes such rows can't be deleted. Setting a value to NULL on an upsert into a custom big object does not update a field that already has a value.

**How to avoid:** Call `.trim()` on every index value before `insertImmediate`. Treat archived values as write-once; if a value must be cleared, the guide's remedy is to delete and recreate the field.

---

## Gotcha 10: Apex Tests Write Real Big Object Data

**What happens:** Running the archive job's tests leaves rows in the production big object, or tests fail with mixed DML.

**When it occurs:** The Big Objects guide: tests may do DML on big objects, but "real data is manipulated without any automatic rollback or cleanup," and tests that mix big object and sObject DML in one transaction aren't allowed and fail.

**How to avoid:** Mock the write layer with the Apex Stub API, so tests exercise the batch logic without calling `insertImmediate` for real.
