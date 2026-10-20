# Gotchas — limits-and-scalability-planning

## Gotcha 1: CPU Limit Includes Formula Fields, Validation Rules, and Workflow — Not Just Apex Code

The 10,000ms synchronous CPU limit (Apex Developer Guide 264 L19782) measures all Apex execution time in the transaction, including time spent evaluating formula fields, validation rules, and Apex called from workflow field updates. This is not a limit on the time your Apex code runs in isolation — it is the cumulative CPU time charged to the transaction by the Salesforce platform.

Practical consequences:
- An object with 20 complex formula fields (especially cross-object formulas that traverse relationships) adds CPU time on every record save, even if no custom Apex is triggered.
- Validation rules that use `VLOOKUP()` or `PRIORVALUE()` functions consume CPU on evaluation.
- A trigger that calls a helper class that calls another utility that calls another method — each frame in the call stack consumes CPU. Deep call chains on large record sets compound quickly.
- Managed package triggers also consume CPU in the same governor bucket: CPU time includes "package code and workflows" (264 L19858), and CPU is one of the limits that certified packages do not get separately (L19922). An installed package that places an after-insert trigger on Account competes with your own triggers for the same 10,000ms budget.

The debug log `CUMULATIVE_LIMIT_USAGE` entry at the end of a transaction shows the true CPU consumed. Do not estimate based on Apex code alone — always profile in a representative data environment.

---

## Gotcha 2: Only Non-Certified Package Code Shares Your 100 SOQL Queries — Certified Managed Packages Get Their Own

Which package code competes with yours for the 100 synchronous SOQL queries depends on whether the package is a certified managed package. The Apex Developer Guide (264 L19873–19880): "Certified managed packages—managed packages that have passed the security review for AppExchange—get their own set of limits for most per-transaction limits", and "the certified managed package gets its own 100-SOQL-query limit for synchronous Apex, in addition to the org's native code limit of 100 SOQL queries." Across all certified namespaces a transaction may run up to 11 times the per-namespace limit — 1,100 SOQL queries (L19883–19886).

Two things still come out of your own budget:
- **Non-certified packages.** "Namespaces in non-certified packages don't have their own separate governor limits. The resources that they use continue to count against the same governor limits used by the org's custom code" (L19891–19892; also L19926–19927). An unmanaged or non-certified package that issues 40 queries in your trigger path leaves you 60.
- **Heap, CPU and transaction time.** These are counted once for the whole transaction even with certified packages (L19920–19924), so a certified package that burns CPU still shrinks your 10,000ms (see Gotcha 1).

This is a common source of mysterious `Too many SOQL queries: 101` errors where your code looks like it only executes 60 queries: the other 40 came from a non-certified package, or from declarative automation and Apex actions in the same transaction.

How to identify:
- Enable debug logs with the `DB` category at FINE or FINEST level. Each `SOQL_EXECUTE_BEGIN` entry shows the query and its originating namespace.
- Look for `LIMIT_USAGE_FOR_NS (namespace)` entries to see per-namespace consumption, then check each namespace against the certified/non-certified list from your package inventory — the log does not tell you which kind it is.

Mitigation:
- Inventory installed packages and record which are certified (own limits) and which are not (shared limits); size your SOQL headroom only against the non-certified ones.
- Audit new package installations for their governor limit footprint in a sandbox before deploying to production.

---

## Gotcha 3: Future Methods Get Higher SOQL, CPU and Heap Limits — But Not Higher DML Limits

A common misconception is that `@future` methods have "relaxed" governor limits across the board. They do not. Future methods receive the same DML statement limit (150) and DML row limit (10,000) as synchronous code. The limits that are higher for future (and other async Apex) are SOQL queries (200 vs. 100), CPU time (60,000ms vs. 10,000ms) and heap size (25MB vs. 10MB from the Winter '27 release; 12MB vs. 6MB through Summer '26) — Apex Developer Guide 264 L19747, L19780.

This matters when developers move SOQL-heavy logic to `@future` expecting the extra headroom to solve a `Too many SOQL queries` error. It will not. If the synchronous transaction hit 101 SOQL queries because the query sits in a loop, moving the same code to `@future` only moves the failure to the 201st query.

Scheduled Apex is the exception inside "async": it is an asynchronous feature, but synchronous limits apply to it (Apex Developer Guide 264 L19739), so a `Schedulable` gets 100 SOQL, 10,000ms CPU and the 10MB heap, not the async column.

The only async pattern that genuinely resets the SOQL limit per chunk is Batch Apex, because each `execute()` call is a fresh transaction with a fresh governor limit budget. For SOQL-heavy operations, Batch Apex is the correct escalation path, not `@future`.

---

## Gotcha 4: DML Statement Count and DML Row Count Are Two Separate Limits

The DML governor has two independent ceilings:
- **DML statements:** 150 per transaction (Apex Developer Guide 264 L19757; each `insert`, `update`, `delete`, `upsert`, `merge`, `undelete` call is one statement regardless of record count).
- **DML rows:** 10,000 per transaction (264 L19759; the total number of records across all DML statements).

Both limits can be independently violated. A loop that inserts a single record 151 times hits the DML statement limit even though only 151 rows were processed. A single bulk insert of 10,001 records hits the DML row limit in one statement.

Mixed-object DML (inserting Accounts, then Contacts, then Opportunities in the same transaction) is a common pattern that creeps toward the statement limit. Each `Database.insert(accountList)` is one statement, `Database.insert(contactList)` is a second, `Database.upsert(opportunityList, ...)` is a third — these accumulate across all Apex code paths in the transaction, including helper methods and trigger handlers called from unrelated code paths.

---

## Gotcha 5: Batch Apex Has No "50 Million Records per 24 Hours" Cap — 50 Million Is a Per-Job QueryLocator Ceiling, and the 24-Hour Cap Counts Executions

Two different numbers get merged into a phantom "50 million records per 24 hours" rule:

- **50 million is per job, not per day.** "A maximum of 50 million records can be returned in the Database.QueryLocator object. If more than 50 million records are returned, the batch job is immediately terminated and marked as Failed" (Apex Developer Guide 264 L17902–17903; table row L20059). A 60-million-row object cannot be swept by one QueryLocator job at all, however quiet the day.
- **The 24-hour rolling cap counts method executions.** The org gets 250,000 asynchronous Apex method executions per 24 hours, or user licenses × 200, whichever is greater (L19936–19940), shared by Batch, Queueable, scheduled and future; for Batch Apex every `start`, `execute` and `finish` call is one execution (L20001–20002). The window is rolling (L17895), not a midnight reset.

What happens: a 10-million-record job at scope 200 needs 50,000 `execute` calls plus `start` and `finish` — 50,002 executions. Batch Apex checks capacity before it starts: "if the batch requires 10,000 executions and the remaining asynchronous limit is 9,500 executions, an AsyncApexExecutions Limit exceeded exception is thrown" and the job does not run (L17895–17899).

When it occurs: overlapping night windows where several teams' batch, Queueable and scheduled jobs draw from the same execution budget, or a small scope (50) that quadruples the execution count of the same record volume.

How to avoid: size each job as executions (records ÷ scope + 2), sum all async work in the window, and read the remaining budget from `DailyAsyncApexExecutions` in the REST limits resource before submitting (REST API Developer Guide 264 L7986). Split any object over 50 million rows across multiple jobs with disjoint filters.

---

## Gotcha 6: Heap Size Limit Applies to Peak Usage, Not Average — String Concatenation in Loops Is a Silent Heap Killer

The heap limits (10MB synchronous and 25MB async from the Winter '27 release, Apex Developer Guide 264 L19780; 6MB / 12MB through Summer '26) apply to the peak live object graph at any single point in the transaction, not the average. If your code builds a large string by concatenating in a loop and the string reaches the ceiling in the middle of the transaction, the transaction fails even if you immediately discard the string afterward.

During Winter '27 only, a nonproduction org can keep the lower Summer '26 heap through `ApexSettings.enableEnforceSummer26ApexHeapLimit` (Metadata API 264 L113855–113862; from Spring '27 the higher heap is enforced everywhere), so a sandbox load test can report 6MB / 12MB headroom while production has 10MB / 25MB. Read `Limits.getLimitHeapSize()` in the test run rather than assuming either pair.

The most common violation pattern:

```apex
String output = '';
for (Account a : accountList) {
    output += a.Name + ',' + a.Id + '\n'; // each iteration adds to heap
}
```

At 50,000 accounts with a 50-character average name, this string grows to roughly 3.5MB before the loop ends. If other objects are also in memory, the combined heap exceeds the limit.

Use `List<String>` with `String.join()` instead of concatenation, or process and emit in chunks rather than building a full in-memory string.

---

## Gotcha 7: The 500 Custom Fields per Object Limit Is a Shared Pool Across All Field Types, Including Formula Fields You Think You Deleted

The 500 custom field limit per object counts every custom field regardless of type — text, number, formula, checkbox, lookup, long text area, and others. This is well-known, but two nuances catch architects off guard:

1. **Deleted fields are not immediately freed, and they also hold their field-type allocation.** UNVERIFIED (2026-10-20): every quotation, count (500/800, 40, 25, 15 days, 75%) and Setup path in this point comes from Salesforce Help field-deletion topics that are not in the Winter '27 corpus; the "30–50 phantom fields" figure is an illustration, not a measured value. Deleting a custom field is a soft delete: "Deleted custom fields and their data are stored until your org permanently deletes them or 15 days have elapsed, whichever happens first." Until then "the field counts against the maximum number of custom fields allowed in your org until the hard-delete process permanently deletes it" — 500 in Enterprise Edition, 800 in Unlimited/Performance. The nuance architects miss is that the deleted field keeps its *typed* slot as well: "a deleted custom roll-up summary field counts against the maximum number of roll-up summary fields for your Salesforce edition." A deleted lookup or master-detail still occupies one of the 40 relationship fields; a deleted roll-up still occupies one of the 25 roll-up summary fields. In orgs where active development has involved heavy field iteration, the soft-deleted pool can account for 30–50 phantom fields.

   The failure looks like a bug rather than a limit — creating or editing a field errors with "Unable to access page" or "No clean data columns available for custom fields" while the object's visible field count is comfortably under the cap.

   Reclaiming the slot is not instant, so "delete the unused fields" is a multi-day remediation, not a same-afternoon fix. On the object's Deleted Fields page, **Erase** only moves the field into the *ready for hard delete* state; Salesforce then runs a background job ("Cleanup of custom field data when a custom field definition is hard deleted", visible under Setup > Background Jobs). The **Purge** button, which initiates that hard delete immediately, appears only once the org reaches 75% of its custom field allocation for the object, and only in Salesforce Classic on Enterprise, Performance, and Unlimited Editions. Permanently deleting fields requires **Customize Application**; the Purge path additionally requires **View All Data**.

2. **Formula fields count even if they produce no stored data.** Every formula field on an object consumes one slot from the 500-field pool, even though formula fields are computed on read and store no data. An object with 200 formula fields and 300 regular fields is at capacity even though the stored data footprint is only 300 fields wide.
