# Gotchas — limits-and-scalability-planning

## Gotcha 1: CPU Limit Includes Formula Fields, Validation Rules, and Workflow — Not Just Apex Code

The 10,000ms synchronous CPU limit measures all Apex execution time in the transaction, including time spent evaluating formula fields, validation rules, and Apex called from workflow field updates. This is not a limit on the time your Apex code runs in isolation — it is the cumulative CPU time charged to the transaction by the Salesforce platform.

Practical consequences:
- An object with 20 complex formula fields (especially cross-object formulas that traverse relationships) adds CPU time on every record save, even if no custom Apex is triggered.
- Validation rules that use `VLOOKUP()` or `PRIORVALUE()` functions consume CPU on evaluation.
- A trigger that calls a helper class that calls another utility that calls another method — each frame in the call stack consumes CPU. Deep call chains on large record sets compound quickly.
- Managed package triggers also consume CPU in the same governor bucket. An installed package that places an after-insert trigger on Account competes with your own triggers for the same 10,000ms budget.

The debug log `CUMULATIVE_LIMIT_USAGE` entry at the end of a transaction shows the true CPU consumed. Do not estimate based on Apex code alone — always profile in a representative data environment.

---

## Gotcha 2: SOQL Limit of 100 Is Shared With Managed Packages — They Are Not Separate

The 100 SOQL queries per transaction limit is a single shared pool across all Apex code running in the default namespace, including Apex from installed managed packages. There is no separate "managed package SOQL budget."

This is a common source of mysterious `Too many SOQL queries: 101` errors where the code looks like it only executes 60 queries. The remaining 40+ queries came from managed package triggers, formula evaluations via VLOOKUP, or Apex actions fired by declarative automation in the same transaction.

How to identify:
- Enable debug logs with the `DB` category at FINE or FINEST level. Each `SOQL_EXECUTE_BEGIN` entry shows the query and its originating namespace (e.g., `[namespace]` prefix for managed package code).
- Look for `LIMIT_USAGE_FOR_NS (namespace)` entries to see per-namespace limit consumption for managed packages that declare their own namespace. However, some managed packages run in the default namespace and their queries appear unnamespaced.

Mitigation:
- Reserve SOQL headroom in your own code. If the org has installed packages known to issue 20–30 queries per transaction, design your custom Apex to stay within 50–60 queries per transaction rather than 80–90.
- Audit new managed package installations by reviewing their governor limit footprint in a sandbox before deploying to production.

---

## Gotcha 3: Future Methods Do NOT Get Higher SOQL Limits — The CPU and Heap Expansion Is All They Get

A common misconception is that `@future` methods have "relaxed" governor limits across the board. They do not. Future methods receive the same SOQL query limit (100), DML statement limit (150), and DML row limit (10,000) as synchronous code. The only limits that are higher for future (and other async Apex) are CPU time (60,000ms vs. 10,000ms) and heap size (12MB vs. 6MB).

This matters when developers move SOQL-heavy logic to `@future` expecting the extra headroom to solve a `Too many SOQL queries` error. It will not. If the synchronous transaction hit 101 SOQL queries, moving the same code to `@future` will also hit 101 SOQL queries — just with more CPU budget available before the failure.

The only async pattern that genuinely resets the SOQL limit per chunk is Batch Apex, because each `execute()` call is a fresh transaction with a fresh governor limit budget. For SOQL-heavy operations, Batch Apex is the correct escalation path, not `@future`.

---

## Gotcha 4: DML Statement Count and DML Row Count Are Two Separate Limits

The DML governor has two independent ceilings:
- **DML statements:** 150 per transaction (each `insert`, `update`, `delete`, `upsert`, `merge`, `undelete` call is one statement regardless of record count).
- **DML rows:** 10,000 per transaction (the total number of records across all DML statements).

Both limits can be independently violated. A loop that inserts a single record 151 times hits the DML statement limit even though only 151 rows were processed. A single bulk insert of 10,001 records hits the DML row limit in one statement.

Mixed-object DML (inserting Accounts, then Contacts, then Opportunities in the same transaction) is a common pattern that creeps toward the statement limit. Each `Database.insert(accountList)` is one statement, `Database.insert(contactList)` is a second, `Database.upsert(opportunityList, ...)` is a third — these accumulate across all Apex code paths in the transaction, including helper methods and trigger handlers called from unrelated code paths.

---

## Gotcha 5: Batch Apex "50 Million Records per 24 Hours" Is a Rolling Window, Not a Daily Reset

The Batch Apex record processing limit of 50 million records resets on a rolling 24-hour basis, not at midnight or at the start of each calendar day. This means:

- A batch job that processes 30 million records starting at 11 PM will consume 30 million of the rolling 24-hour budget. Another batch job starting at 1 AM (2 hours later) still has 30 million records against the limit because the window extends to 11 PM the following night.
- Organizations that run batch jobs in overlapping night windows (e.g., different business units each scheduling their own nightly sync) can inadvertently combine to exceed the 50-million limit even though no single job is that large.

Monitor cumulative batch consumption using the Apex Jobs page in Setup or through the `AsyncApexJob` object query. Schedule batch jobs with explicit start time sequencing rather than "start after midnight" assumptions.

---

## Gotcha 6: Heap Size Limit Applies to Peak Usage, Not Average — String Concatenation in Loops Is a Silent Heap Killer

The 6MB synchronous and 12MB async heap limits apply to the peak live object graph at any single point in the transaction, not the average. If your code builds a large string by concatenating in a loop and the string reaches 6MB in the middle of the transaction, the transaction fails even if you immediately discard the string afterward.

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

1. **Deleted fields are not immediately freed.** When you delete a custom field, Salesforce retains it in a "soft delete" state for 15 days. During that window, the field still counts against the 500 limit. To reclaim the slot immediately, navigate to Setup > Deleted Fields and hard-delete the field. In orgs where active development has involved heavy field iteration, the soft-deleted pool can account for 30–50 phantom fields.

2. **Formula fields count even if they produce no stored data.** Every formula field on an object consumes one slot from the 500-field pool, even though formula fields are computed on read and store no data. An object with 200 formula fields and 300 regular fields is at capacity even though the stored data footprint is only 300 fields wide.
