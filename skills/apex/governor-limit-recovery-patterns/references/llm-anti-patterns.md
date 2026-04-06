# LLM Anti-Patterns — Governor Limit Recovery Patterns

Common mistakes AI coding assistants make when generating or advising on Governor Limit Recovery Patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Wrapping Code in try/catch to Handle LimitException

**What the LLM generates:** A try/catch block with `catch(System.LimitException e)` or `catch(Exception e)` around a loop, with recovery logic in the catch body (e.g., logging and returning partial results).

**Why it happens:** LLMs are trained on Java/C#/Python patterns where all exceptions are catchable. The Java `RuntimeException` hierarchy trains the model to assume all runtime exceptions can be caught. The model does not internalize that Apex has a special uncatchable exception class.

**Correct pattern:**

```apex
// WRONG — LimitException is never catchable; catch block never runs
try {
    for (SObject rec : records) {
        doExpensiveWork(rec);
    }
} catch (System.LimitException e) {
    System.debug('caught limit exception'); // NEVER REACHED
}

// CORRECT — check headroom before the operation
for (SObject rec : records) {
    if (Limits.getLimitQueries() - Limits.getQueries() < 3) {
        deferredIds.add(rec.Id);
        break;
    }
    doExpensiveWork(rec);
}
```

**Detection hint:** Look for `catch.*LimitException` or `catch.*Exception.*limit` patterns in the generated code. Any catch block intended to handle limit errors is wrong.

---

## Anti-Pattern 2: Assuming Database.rollback() Clears the sObject Id Field

**What the LLM generates:** Code that calls `Database.rollback(sp)` and then checks `if (record.Id != null)` or uses `record.Id` to re-insert or publish a platform event, assuming the Id was cleared by the rollback.

**Why it happens:** The model conflates "rollback reverts the database insert" with "rollback resets the in-memory object state." This conflation is intuitive but wrong — Apex does not reset sObject field values as part of rollback.

**Correct pattern:**

```apex
// WRONG — Id is still set after rollback; this check is always true
Database.rollback(sp);
if (record.Id != null) {
    // Incorrectly treats rolled-back record as persisted
    publishEvent(record.Id);
}

// CORRECT — explicitly null the Id after rollback
Database.rollback(sp);
record.Id = null; // must be done manually
if (record.Id != null) {
    publishEvent(record.Id); // now correctly skipped
}
```

**Detection hint:** Search for `Database.rollback` followed within 10 lines by `record.Id` or `.Id` access without an explicit `= null` assignment between them.

---

## Anti-Pattern 3: Assuming Static Variables Reset on Rollback

**What the LLM generates:** Code that uses static sets or maps as recursion guards or processed-ID caches, performs a `Database.rollback()`, and continues processing — without resetting the static state. The assumption is that rollback "resets everything."

**Why it happens:** LLMs model rollback as a broad reset operation. Static variables in Java/C# are scoped differently and the concept of "transaction-bounded" static state does not map cleanly from other languages.

**Correct pattern:**

```apex
// WRONG — processedIds still contains IDs from before the rollback
private static Set<Id> processedIds = new Set<Id>();

Savepoint sp = Database.setSavepoint();
for (Account acc : accounts) {
    processedIds.add(acc.Id);
    insert acc;
}
if (limitHit) {
    Database.rollback(sp);
    // processedIds is NOT cleared — stale IDs will cause records to be skipped
}

// CORRECT — explicitly reset static state alongside the rollback
Database.rollback(sp);
processedIds.clear(); // explicitly reset after rollback
```

**Detection hint:** Search for `Database.rollback` near static variable accesses (e.g., `static.*Set`, `static.*Map`, `static.*List`) without a `.clear()` or reassignment call in the same code block.

---

## Anti-Pattern 4: Parsing BatchApexErrorEvent.JobScope Without Checking DoesExceedJobScopeMaxLength

**What the LLM generates:** A `BatchApexErrorEvent` trigger that directly calls `evt.JobScope.split(',')` without first checking `evt.DoesExceedJobScopeMaxLength`, then iterates the resulting list treating all entries as valid Ids.

**Why it happens:** The model generates the happy-path parsing without knowing the truncation behavior of the `JobScope` field. The documentation for `DoesExceedJobScopeMaxLength` is a detail the model often misses or ignores when generating boilerplate event handlers.

**Correct pattern:**

```apex
// WRONG — JobScope may be truncated; last entry may be a partial Id
for (String id : evt.JobScope.split(',')) {
    Id recId = (Id) id; // throws StringException if id is malformed
}

// CORRECT — check truncation flag first
if (evt.DoesExceedJobScopeMaxLength) {
    // Fall back to SOQL-based recovery using AsyncApexJobId + status field
    List<MyObject__c> failed = [
        SELECT Id FROM MyObject__c
        WHERE BatchJobId__c = :evt.AsyncApexJobId
          AND Status__c = 'InProgress'
    ];
    // process failed
} else {
    for (String rawId : evt.JobScope.split(',')) {
        Id recId = (Id) rawId.trim();
        // process recId
    }
}
```

**Detection hint:** Look for `evt.JobScope.split` or `JobScope.split` in event trigger handlers without a preceding `DoesExceedJobScopeMaxLength` check in the same conditional scope.

---

## Anti-Pattern 5: Placing the Limits Check Only at Method Entry, Not Inside the Loop

**What the LLM generates:** A single `Limits.*` check at the top of the method before the processing loop, concluding that if headroom is sufficient at entry, the whole loop is safe.

**Why it happens:** The model treats headroom as a threshold to clear once rather than a budget that decrements on each iteration. This reflects a Java/Python mental model where resource checks are done at the gate, not per-iteration.

**Correct pattern:**

```apex
// WRONG — headroom is checked once; mid-loop consumption is not tracked
if (Limits.getLimitQueries() - Limits.getQueries() > 10) {
    for (SObject rec : records) {
        // 200 records × 1 query each = 200 queries; LimitException at record 91
        Account a = [SELECT Id FROM Account WHERE Id = :rec.get('AccountId') LIMIT 1];
    }
}

// CORRECT — headroom checked per iteration
for (SObject rec : records) {
    if (Limits.getLimitQueries() - Limits.getQueries() < 3) {
        deferredIds.add((Id) rec.get('Id'));
        break;
    }
    Account a = [SELECT Id FROM Account WHERE Id = :rec.get('AccountId') LIMIT 1];
}
```

**Detection hint:** Look for a single `Limits.*` check before a `for` loop where the loop body contains SOQL, DML, or callout operations. The check should be inside the loop, not only before it.

---

## Anti-Pattern 6: Using More Than 5 Savepoints Per Transaction

**What the LLM generates:** Nested service methods that each independently call `Database.setSavepoint()` for local recovery, resulting in multiple savepoints across a single transaction call stack — often exceeding the 5-savepoint limit.

**Why it happens:** The model generates defensive savepoint patterns per method without tracking cross-method savepoint consumption. Each method looks correct in isolation; the problem only appears when they are called together.

**Correct pattern:**

```apex
// WRONG — three savepoints in one call stack; may exceed limit of 5
public void processOrder(Order__c order) {
    Savepoint sp1 = Database.setSavepoint(); // savepoint 1
    insert order;

    LineItemService.insert(order.Id);      // internally sets savepoint 2
    PaymentService.charge(order.Id);       // internally sets savepoint 3
}

// CORRECT — savepoint ownership at the transaction boundary layer
public void processOrder(Order__c order) {
    Savepoint sp = Database.setSavepoint(); // single savepoint at orchestration layer
    try {
        insert order;
        LineItemService.insertWithoutSavepoint(order.Id);  // no internal savepoint
        PaymentService.chargeWithoutSavepoint(order.Id);   // no internal savepoint
    } catch (Exception e) {
        Database.rollback(sp);
        throw e;
    }
}
```

**Detection hint:** Count `Database.setSavepoint()` calls in the transitive call graph of any method. If more than 5 are reachable in a single execution path, refactor savepoint ownership to the outermost orchestration layer.
