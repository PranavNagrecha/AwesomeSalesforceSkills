# Gotchas: Governor Limits

Non-obvious governor-limit behaviors that cause real production failures. Line numbers ("L") refer to the pdftotext extraction of the Apex Developer Guide, release 262; the full quoted table is in `limits-table.md`.

## Gotcha 1: Limits are per transaction, not per method or per class

**What happens:** A trigger handler uses 40 queries and a service it calls uses 70; together they pass 100 and the transaction fails.

**When it occurs:** Whenever triggers, services, utilities, flows, and package code run in one transaction.

**How to avoid:** Budget the whole transaction. Count every automation layer, and query once per object per transaction.

```apex
// These two calls share the same 100-query synchronous budget.
AccountService.doSomething();     // uses 40 SOQL
ContactService.doSomethingElse(); // uses 70 SOQL; the 101st query throws
```

**Source:** Apex Developer Guide (262), Per-Transaction Apex Limits: "These limits count for each Apex transaction" (L19530); SOQL 100 synchronous, 200 asynchronous (L19544).

---

## Gotcha 2: Platform event and CDC triggers get 2,000 records per batch

**What happens:** A subscriber trigger that runs one query per record works for small tests and fails under real event volume.

**When it occurs:** In triggers on platform events and Change Data Capture events, where the batch size is 2,000 instead of 200.

**How to avoid:** Write event triggers for 2,000 records per execution and test with that volume.

**Source:** Apex Developer Guide (262), Static Apex Limits: "Apex trigger batch size 200" (L19852) and footnote: "The Apex trigger batch size for platform events and Change Data Capture events is 2,000" (L19862).

---

## Gotcha 3: Async raises some limits but not query rows or DML rows

**What happens:** Code moved to a Queueable or future method to escape limits fails on the same 50,000-row or 10,000-DML-row ceiling.

**When it occurs:** When "it's async" is treated as "it's unlimited."

**How to avoid:** Use Batch Apex (or cursors with chained Queueables) for row volumes above those limits. Async raises SOQL count (200), heap (12 MB), and CPU (60,000 ms), not rows.

**Source:** Apex Developer Guide (262), Per-Transaction Apex Limits: query rows 50,000 sync and async (L19546); DML rows 10,000 sync and async (L19556); heap 6 MB and 12 MB (L19577); CPU 10,000 and 60,000 ms (L19579).

---

## Gotcha 4: getQueryLocator rows are capped at 10,000 outside Batch start

**What happens:** Code that uses `Database.getQueryLocator` in an ordinary transaction to "get 50 million rows" stops at 10,000.

**When it occurs:** When the Batch-only 50 million figure is applied to any `QueryLocator`.

**How to avoid:** Return the `QueryLocator` from a Batch `start` method for large volumes; elsewhere treat it as a 10,000-row source. A direct `[SELECT]` stops at 50,000 rows even with a SOQL for loop.

**Source:** Apex Developer Guide (262): "Total number of records retrieved by Database.getQueryLocator 10,000" (L19548); "Maximum number of records returned for a Batch Apex query in Database.QueryLocator 50 million" (L19856).

---

## Gotcha 5: Scheduled Apex is async but runs with synchronous limits

**What happens:** A scheduler that processes data inline fails at 100 queries or 10,000 ms of CPU.

**When it occurs:** When `Schedulable.execute` does the work instead of dispatching it.

**How to avoid:** Have the scheduler enqueue a Queueable or start a Batch and return. The org can have at most 100 scheduled Apex jobs at once (5 in Developer Edition), so use one dispatcher instead of many schedules.

**Source:** Apex Developer Guide (262): "Although scheduled Apex is an asynchronous feature, synchronous limits apply to scheduled Apex jobs" (L19536); "Maximum number of Apex classes scheduled concurrently 100. In Developer Edition orgs, the limit is 5" (L19776).

---

## Gotcha 6: Async contexts allow one enqueue and no future calls

**What happens:** A Queueable that enqueues two jobs, or a Batch `execute` that calls a future method, throws a limit exception.

**When it occurs:** When fan-out logic written for a trigger is reused inside async code.

**How to avoid:** Chain one child job per Queueable execution, and from Batch enqueue at most one Queueable per `execute` instead of calling future methods. Future calls from a Queueable are allowed (50).

**Source:** Apex Developer Guide (262): System.enqueueJob 50 synchronous, 1 asynchronous (L19573); future methods 50 synchronous, "0 in batch and future contexts; 50 in queueable context" (L19568 to L19571).

---

## Gotcha 7: Recursive DML stops at a stack depth of 16

**What happens:** A trigger that updates records which re-fire the same trigger throws `Maximum trigger depth exceeded` long before the SOQL or DML counts run out.

**When it occurs:** On recursive save paths without a guard.

**How to avoid:** Track processed record IDs in a static `Set<Id>` and skip records already handled.

**Source:** Apex Developer Guide (262): "Total stack depth for any Apex invocation that recursively fires triggers due to insert, update, or delete statements 16" (L19559), and footnote 3 on why trigger recursion is restricted more tightly (L19638 to L19648).

---

## Gotcha 8: SOSL has its own count and a 2,000-row cap per search

**What happens:** Fuzzy matching with `FIND` in a loop fails at 21 searches, and a broad search returns only 2,000 rows.

**When it occurs:** When SOSL replaces SOQL inside per-record logic.

**How to avoid:** Run one search for the whole batch and narrow it with `RETURNING` filters.

**Source:** Apex Developer Guide (262): SOSL queries 20 (L19550); records retrieved by a single SOSL query 2,000 (L19552).

---

## Gotcha 9: Cursor fetches still spend SOQL queries and rows

**What happens:** A cursor-based job fails on the SOQL limit even though it uses one cursor.

**When it occurs:** When each `Cursor.fetch` call is treated as free. Each fetch counts as a query, fetched rows count as query rows, and only 100 fetches are allowed per transaction. Across the org, cursor rows are capped at 100 million per 24 hours.

**How to avoid:** Fetch in chunks sized to stay under 50,000 rows per transaction, chain Queueables for more, and budget daily cursor rows across all jobs.

**Source:** Apex Developer Guide (262), "Apex Cursors": "Calling the Cursor.fetch() method counts against the SOQL query limit, and the rows fetched count against the SOQL query row limit. You can make a maximum of 100 Cursor.fetch() calls per transaction"; limits L19601, L19603, L19753, L19763.

---

## Gotcha 10: Callouts after uncommitted DML fail

**What happens:** "You have uncommitted work pending. Please commit or rollback before calling out."

**When it occurs:** When a transaction inserts or updates records, or calls a future method or starts a batch, and then makes a callout.

**How to avoid:** Move the callout to a Queueable with `Database.AllowsCallouts`, or make the callout before any DML.

**Source:** Apex Developer Guide (262), savepoint and callout example asserting the "You have uncommitted work pending" message (L8769) and "Asynchronous Apex and Mock Callouts": "Similar to DML, asynchronous Apex operations result in pending uncommitted work that prevents callouts from being performed later in the same transaction" (L35183).

---

## Gotcha 11: CPU time counts more than your own code

**What happens:** A transaction fails on CPU even though the Apex itself looks light.

**When it occurs:** When managed package code and workflow-type processes run in the same transaction; their CPU counts against the same 10,000 ms. Time spent in the database and waiting on callouts doesn't count.

**How to avoid:** Profile the whole transaction in a debug log, and reduce nested loops and string building in your own code first.

**Source:** Apex Developer Guide (262), Per-Transaction Apex Limits footnote 5 (L19652 to L19657). UNVERIFIED (2026-10-03): that flows invoked from Apex share the caller's SOQL and DML counts; the 262 guide states CPU sharing for "package code and workflows" but does not spell out flow query counts.

---

## Gotcha 12: Test.startTest() gives a fresh set of limits, and async runs at stopTest()

**What happens:** Setup DML eats the limit budget so the code under test fails, or assertions run before async work.

**When it occurs:** When tests create large data sets without a `Test.startTest()` boundary, or assert before `Test.stopTest()`.

**How to avoid:** Create data, call `Test.startTest()`, run the code, call `Test.stopTest()`, then assert. Limits also apply to each test method separately.

```apex
Test.startTest();
System.enqueueJob(new MyQueueable(records));
Test.stopTest(); // queued work runs here
System.assertEquals('Expected', [SELECT Status__c FROM MyObject__c WHERE Id = :recordId].Status__c);
```

**Source:** Apex Reference Guide (262), `Test.startTest()`: "Any code that executes after the call to startTest and before stopTest is assigned a new set of governor limits"; Apex Developer Guide (262), "Limits apply individually to each testMethod" (L19660) and "Testing Future Methods."

---

## Gotcha 13: Batch resets limits for each execute, not for the job

**What happens:** One heavy scope fails while the rest of the job succeeds.

**When it occurs:** When a scope's records trigger expensive automation, or a scope size is too large for the per-execute budget.

**How to avoid:** Size scopes to the most expensive record path and keep `start` simple. UNVERIFIED (2026-10-03): the limit context of `start` and `finish`; the guide states that limits reset "for each execution of a batch of records in the execute method" and that start, execute, and finish can each make up to 100 callouts.

**Source:** Apex Developer Guide (262), Per-Transaction Apex Limits (L19530 to L19531) and "Batch Apex Governor Limits."

---

## Gotcha 14: Certified packages get their own limits, inside cumulative totals

**What happens:** An ISV package that is fine in a test org fails in a busy subscriber org, or a subscriber expects package code to use its own heap and CPU.

**When it occurs:** When several certified namespaces run in one transaction.

**How to avoid:** Design packages against the per-namespace limits and remember heap, CPU, execution time, and unique namespaces are shared across the transaction. Cumulative totals include 1,100 SOQL queries and 1,650 DML statements.

**Source:** Apex Developer Guide (262), Per-Transaction Certified Managed Package Limits (L19667 to L19721).
