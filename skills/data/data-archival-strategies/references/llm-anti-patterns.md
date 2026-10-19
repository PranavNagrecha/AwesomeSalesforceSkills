# LLM Anti-Patterns — Data Archival Strategies

Common mistakes AI coding assistants make when generating or advising on Salesforce data archival strategies.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating a Big Object as a General-Purpose Archive Table

**What the LLM generates:** "Archive old records to a big object and query them as needed," with ad hoc filters, a REST integration to read them, and a standard report for auditors.

**Why it happens:** Models map a big object to "a large table" from relational databases and carry over relational query and UI expectations.

**Correct pattern:**

```text
Big objects (Big Objects Implementation Guide):
- APIs: SOQL, Bulk API / Bulk API 2.0, Chatter, SOAP only. REST API isn't supported.
- Queries and deletes follow the index: index fields in order, without gaps.
- No triggers, flows, processes; object and field permissions only, no sharing rules.
- Custom Lightning / Visualforce components instead of standard list views and detail pages.
- Index fixed after deployment.
Design the index from the questions auditors will ask. If the questions are unknown
or ad hoc, a big object is the wrong target.
```

**Detection hint:** A big object recommendation with no index design, any REST endpoint used to read a `__b` object, or a filter on a non-index field.

---

## Anti-Pattern 2: Claiming `insertImmediate` Is Fire-and-Forget

**What the LLM generates:** "`Database.insertImmediate()` returns void and fails silently; check the debug log," or code that ignores the return value and deletes the source immediately.

**Why it happens:** Models conflate "doesn't throw" with "doesn't report."

**Correct pattern:**

```apex
List<Database.SaveResult> results = Database.insertImmediate(rows);
Boolean allOk = true;
for (Database.SaveResult r : results) {
    if (!r.isSuccess()) {
        allOk = false;
    }
}
if (!allOk) {
    // Retry the entire batch (writes are idempotent); do not delete the source.
    System.enqueueJob(new ArchiveRetryJob(rows));
    return;
}
```

The guide: failures return a `SaveResult` with `getErrors()`; no exception is thrown; retry the whole batch.

**Detection hint:** `insertImmediate` whose result is not assigned, or a source delete in the same block with no success check.

---

## Anti-Pattern 3: Promising Storage Savings From the Recycle Bin

**What the LLM generates:** "Deleted records keep consuming storage in the Recycle Bin for 15 days, so empty it to reclaim space," sometimes with an invented Recycle Bin capacity ("25 times your storage" or "25,000 records").

**Why it happens:** It matches how many databases behave, and Storage Usage often does not move right after a mass delete.

**Correct pattern:** The LDV guide says Recycle Bin items don't count against storage usage and that there is no limit on the number of deleted items it can hold. Emptying it helps query performance, because soft-deleted rows still have to be excluded from queries. Budget storage savings from records removed from live objects.

**Detection hint:** Any sentence pairing "empty the Recycle Bin" with "reclaim storage," or any numeric Recycle Bin capacity.

---

## Anti-Pattern 4: Recommending External Storage Without Reporting and Lookup Answers

**What the LLM generates:** "Archive records to S3 or Heroku Postgres to reduce storage," with no word on reports, lookups from active records, or how users find the data.

**Why it happens:** External storage is well documented outside Salesforce; the in-org consequences are not.

**Correct pattern:**

```text
Before choosing an external archive, answer:
1. Reporting: does anyone report on archived records? If yes, keep a summary
   record in Salesforce or choose a soft archive.
2. Lookups: do active records point at the records being archived?
3. Access: will users reach the data through an external object, a link,
   or an integration?
4. Retention: does a regulation require the data to stay in Salesforce?
```

**Detection hint:** An external archive recommendation without an answer for reporting, lookups, and user access.

---

## Anti-Pattern 5: Getting Field History Retention Wrong

**What the LLM generates:** "Field Audit Trail keeps history for 10 years," "history rows of deleted records stay until the 18-month truncation," or "field history is a hidden storage consumer."

**Why it happens:** Older material and paraphrases have drifted from the current Security guide.

**Correct pattern:**

```text
Security guide, Field History Tracking and Field Audit Trail:
- Without Field Audit Trail: kept up to 18 months, 24 months via the API; 20 tracked fields per object.
- With Field Audit Trail: archived into FieldHistoryArchive and kept until you delete it;
  200 tracked fields per object; policy = HistoryRetentionPolicy via Metadata API;
  default archive after 18 months (production) / 1 month (sandboxes).
- Field history and Field Audit Trail data don't count against data storage.
- Deleting a record cascades to its history rows (not to FieldHistoryArchive copies).
- Field history can be deleted manually at any time.
```

**Detection hint:** A fixed year count for Field Audit Trail, a claim that history survives deletion of its parent, or field history listed as a data-storage consumer.

---

## Anti-Pattern 6: Quoting Storage Allocations From Memory

**What the LLM generates:** A storage paragraph full of per-edition and per-licence numbers used to size the archival business case.

**Why it happens:** Allocation tables are widely paraphrased, and every number in them attaches to a specific edition, licence, and storage type that is easy to mix up.

**Correct pattern:** Take used and allowed figures from the org's Setup > Storage Usage page and record them in the template; leave allocation tables to `data/data-storage-management`. Size the saving from the record counts of the objects being archived, not from Recycle Bin or field history contents, which don't count against data storage.

**Detection hint:** An allocation figure in an archival plan with no Storage Usage screenshot or export behind it.
