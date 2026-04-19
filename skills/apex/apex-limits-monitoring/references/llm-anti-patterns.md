# LLM Anti-Patterns — Apex Limits Monitoring

Common mistakes AI coding assistants make when generating or advising on Apex governor limit defensive coding. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Trying to Catch `System.LimitException`

**What the LLM generates:**

```apex
try {
    List<Account> results = [SELECT Id FROM Account WHERE ...];
    update results;
} catch (System.LimitException le) {
    System.debug('Limit hit: ' + le.getMessage());
    // graceful degradation logic
}
```

**Why it happens:** LLMs are trained on Java and general exception-handling idioms where catching runtime exceptions is a common defensive pattern. They apply this pattern to Apex without recognizing that `System.LimitException` is a special uncatchable exception.

**Correct pattern:**

```apex
// Guard BEFORE the query — prevention, not recovery
if ((Limits.getLimitQueries() - Limits.getQueries()) < 10) {
    System.debug(LoggingLevel.WARN, 'Insufficient SOQL headroom. Skipping query.');
    return new List<Account>();
}
List<Account> results = [SELECT Id FROM Account WHERE ...];
```

**Detection hint:** Search for `catch.*LimitException` in generated code. Any such block is wrong.

---

## Anti-Pattern 2: Using `getLimitX()` Without `getX()` — Checking the Ceiling Instead of Current Usage

**What the LLM generates:**

```apex
// WRONG — this checks the ceiling, not remaining headroom
if (Limits.getLimitQueries() < 10) {
    // this condition is always false (ceiling is 100 or 200, never < 10)
    return;
}
```

**Why it happens:** LLMs sometimes confuse the purpose of the two Limits methods. They know `getLimitX()` is "the important number" and omit `getX()` entirely, producing a check that is semantically meaningless (the ceiling never changes within a transaction).

**Correct pattern:**

```apex
// Check remaining headroom: ceiling minus consumed
Integer soqlRemaining = Limits.getLimitQueries() - Limits.getQueries();
if (soqlRemaining < 10) {
    return;
}
```

**Detection hint:** A guard clause that calls only `getLimitX()` without a paired `getX()` subtraction is always wrong for a headroom check.

---

## Anti-Pattern 3: Assuming Synchronous and Asynchronous Limits Are the Same

**What the LLM generates:**

```apex
// Hardcoded to sync ceiling — wrong in async (Batch, Queueable, Future, Scheduled)
private static final Integer MAX_SOQL = 100;

if (Limits.getQueries() >= MAX_SOQL - 10) {
    return;
}
```

**Why it happens:** LLMs are more commonly trained on synchronous Apex examples and hardcode the synchronous ceilings (100 SOQL, 10,000 ms CPU, 6 MB heap). When the same code runs in an async context, the hardcoded ceiling (100 SOQL) is more conservative than the actual ceiling (200 SOQL), wasting 50% of available headroom.

**Correct pattern:**

```apex
// Use getLimitQueries() — returns the correct ceiling for the current context
// (100 in sync, 200 in async — no hardcoding needed)
Integer soqlRemaining = Limits.getLimitQueries() - Limits.getQueries();
if (soqlRemaining < 10) {
    return;
}
```

**Detection hint:** Any hardcoded integer constant compared against `Limits.getQueries()`, `Limits.getDMLStatements()`, `Limits.getCpuTime()`, or `Limits.getHeapSize()` should be replaced with the equivalent `getLimitX()` call.

---

## Anti-Pattern 4: Confusing CPU Time with Wall-Clock Time

**What the LLM generates:**

```apex
// MISLEADING comment — getCpuTime() does NOT measure total elapsed time
if (Limits.getCpuTime() > 9000) {
    System.debug('Transaction has been running for nearly 9 seconds');
    return;
}
```

**Why it happens:** LLMs conflate `Limits.getCpuTime()` with a wall-clock timer. In reality, CPU time excludes all callout I/O wait time. A transaction making 50 HTTP callouts that each take 500 ms will show very low CPU time while consuming 25 seconds of wall-clock time.

**Correct pattern:**

```apex
// CPU time check — valid for Apex execution time, NOT total elapsed time
if (Limits.getCpuTime() > (Integer)(Limits.getLimitCpuTime() * 0.90)) {
    System.debug(LoggingLevel.WARN, 'Approaching CPU time limit. Stopping early.');
    return;
}
// For callout-heavy code, ALSO check:
if (Limits.getCallouts() >= Limits.getLimitCallouts() - 5) {
    System.debug(LoggingLevel.WARN, 'Approaching callout limit.');
    return;
}
```

**Detection hint:** Comments describing `getCpuTime()` as "elapsed time" or "wall clock" are wrong. CPU time excludes callout I/O.

---

## Anti-Pattern 5: Not Checking Limits Before a Loop with Variable Iteration Count

**What the LLM generates:**

```apex
// WRONG — check is outside the loop; consumption inside the loop is unbounded
if ((Limits.getLimitQueries() - Limits.getQueries()) < 10) {
    return;
}
for (Id recordId : recordIds) {  // recordIds could be 1 or 1000
    Account acc = [SELECT Id FROM Account WHERE Id = :recordId]; // 1 SOQL per iteration
    process(acc);
}
```

**Why it happens:** LLMs often add a single guard at the method entry point, treating it as a binary check. They do not account for SOQL or DML inside the loop body that multiplies consumption by the iteration count.

**Correct pattern:**

```apex
for (Id recordId : recordIds) {
    // Guard inside the loop — check before EACH expensive operation
    if ((Limits.getLimitQueries() - Limits.getQueries()) < 5) {
        System.debug(LoggingLevel.WARN, 'SOQL headroom exhausted mid-loop. Stopping.');
        break;
    }
    Account acc = [SELECT Id FROM Account WHERE Id = :recordId];
    process(acc);
}
```

**Detection hint:** A SOQL query or DML statement inside a loop body with no `Limits.getX()` guard immediately before it is a limit risk. Alternatively, if a single guard appears only at method entry but the method body contains a loop with SOQL/DML, it is insufficient.

---

## Anti-Pattern 6: Ignoring Aggregate Query Limit When Using `COUNT()` or `GROUP BY`

**What the LLM generates:**

```apex
// Guards only standard SOQL queries — misses aggregate query consumption
if ((Limits.getLimitQueries() - Limits.getQueries()) < 10) {
    return;
}
AggregateResult[] results = [
    SELECT AccountId, COUNT(Id) total FROM Contact GROUP BY AccountId
];
```

**Why it happens:** LLMs know about the standard SOQL query limit but are often unaware that aggregate queries (`COUNT()`, `SUM()`, `GROUP BY`) are tracked against a separate limit (`Limits.getAggregateQueries()` / `Limits.getLimitAggregateQueries()` = 300).

**Correct pattern:**

```apex
// Guard standard SOQL AND aggregate SOQL separately
if ((Limits.getLimitQueries() - Limits.getQueries()) < 10) {
    return;
}
if ((Limits.getLimitAggregateQueries() - Limits.getAggregateQueries()) < 5) {
    return;
}
AggregateResult[] results = [
    SELECT AccountId, COUNT(Id) total FROM Contact GROUP BY AccountId
];
```

**Detection hint:** Code that issues aggregate SOQL (queries containing `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `GROUP BY`) but only guards `Limits.getQueries()` is missing the aggregate query guard.
