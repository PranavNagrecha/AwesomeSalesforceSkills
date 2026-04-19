# Gotchas — Apex Limits Monitoring

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `System.LimitException` Is Uncatchable and Untestable via Try/Catch

**What happens:** When any governor limit is exceeded, Salesforce throws `System.LimitException`. Unlike `DmlException` or `QueryException`, this exception cannot be caught with a `try/catch` block. The transaction terminates immediately and all work is rolled back before any handler can execute. Code like `catch (System.LimitException e)` compiles without error but the catch block is never reached during a real breach.

**When it occurs:** Any time code exceeds a governor ceiling — 100 SOQL queries in synchronous Apex, 150 DML statements, 10,000 ms CPU, 6 MB heap. The exception fires at the moment of breach, not at the end of the transaction.

**How to avoid:** Write guard clauses using `Limits.getLimitX() - Limits.getX()` before the expensive operation. Prevention is the only option. There is no "handle the limit breach" pattern.

---

## Gotcha 2: Heap Check Must Account for the Full Object Graph, Not Just the Collection Size

**What happens:** `Limits.getHeapSize()` returns bytes consumed by all objects in the current heap — including every field value on every nested SObject, every string, and every collection element. A `List<Account>` with 5,000 records, each with ten populated text fields, can easily consume 3–4 MB of the 6 MB synchronous heap. Checking heap size only at the top of a method understates consumption if large collections are populated inside the method body.

**When it occurs:** Service methods that query large SObject lists with `SELECT *`-style field lists, or that build intermediate collections inside loops. The heap grows with each record added to memory; it does not shrink until references go out of scope (and even then, GC timing is not guaranteed).

**How to avoid:** Check `Limits.getHeapSize()` periodically inside data-intensive loops, not just at method entry. Use selective `SELECT` field lists — retrieve only the fields needed for processing. Null out large collections (`myList = null`) when they are no longer needed to make them eligible for garbage collection.

---

## Gotcha 3: DML Statements vs DML Rows Are Separate Limits

**What happens:** Salesforce enforces two independent DML limits: statement count (`Limits.getDMLStatements()` / `Limits.getLimitDMLStatements()` = 150) and row count (`Limits.getDMLRows()` / `Limits.getLimitDMLRows()` = 10,000). Bulkifying DML (using `update myList` instead of `update record` inside a loop) reduces statement count but not row count. Code that bulkifies DML correctly can still hit the row limit if it updates tens of thousands of records across multiple DML calls.

**When it occurs:** ETL-style batch execute methods, trigger handlers that cascade updates to related records, or bulk data migration code paths.

**How to avoid:** Guard both limits independently. Before a bulk DML call, check both `getDMLStatements()` and `getDMLRows()` (accounting for the size of the list you are about to commit). If DML rows are the constraint, split the update into multiple Batch Apex executions rather than a single bulk DML.

---

## Gotcha 4: CPU Time Excludes Callout Wait Time — `getCpuTime()` Reads Low on Callout-Heavy Code

**What happens:** `Limits.getCpuTime()` measures Apex execution time but excludes time spent waiting for external callout responses (HTTP, web service). A method that makes 50 callouts may show only 200 ms of CPU time while consuming 45 seconds of wall-clock time. Developers monitoring only `getCpuTime()` underestimate actual transaction duration for callout-heavy integrations.

**When it occurs:** Integration code that calls external REST APIs inside loops, or any code path that uses `Http.send()` within iteration.

**How to avoid:** Monitor `Limits.getCallouts()` alongside `Limits.getCpuTime()` for callout-heavy code. The callout limit is 100 per transaction (`Limits.getLimitCallouts()` = 100). Also note that callouts are not allowed after DML in the same transaction (platform restriction unrelated to limits); plan the DML/callout ordering carefully.

---

## Gotcha 5: Aggregate Queries Count Against a Separate Limit — Not the Standard SOQL Query Limit

**What happens:** SOQL queries that include aggregate functions (`COUNT()`, `SUM()`, `AVG()`, `GROUP BY`) are tracked separately by `Limits.getAggregateQueries()` / `Limits.getLimitAggregateQueries()` (ceiling: 300 per transaction). They do not count against the standard query limit tracked by `Limits.getQueries()`. Code that guards only `Limits.getQueries()` and issues many aggregate queries can still exhaust `Limits.getLimitAggregateQueries()`.

**When it occurs:** Report-style Apex, validation logic that uses aggregate queries to count related records, or data quality checks that summarize large datasets.

**How to avoid:** If a class issues both standard and aggregate SOQL, guard both limits. Add a check for `Limits.getLimitAggregateQueries() - Limits.getAggregateQueries()` before aggregate queries in the same way guard clauses are added for standard SOQL.
