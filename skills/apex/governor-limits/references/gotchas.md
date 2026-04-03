# Governor Limits — Gotchas

## 1. Limits Are Per Transaction, Not Per Record or Per Method

A transaction is the entire Apex execution context — one trigger fire, one `@AuraEnabled` call, one `execute()` in a Queueable. If your trigger calls a service class which calls a utility class, they all share the same 100 SOQL queries.

```apex
// These two methods share the same 100-query budget
AccountService.doSomething();   // uses 40 SOQL
ContactService.doSomethingElse(); // uses 70 SOQL → BOOM
```

---

## 2. `@future` Parameters Must Be Primitives or Collections of Primitives

```apex
// ❌ Compile error — SObject not allowed
@future
public static void process(List<Account> accounts) { }

// ✅ Pass IDs and re-query inside the future method
@future
public static void process(Set<Id> accountIds) {
    List<Account> accounts = [SELECT Id FROM Account WHERE Id IN :accountIds];
}
```

---

## 3. `@future` Cannot Be Called From a Batch `execute()` Method

If you try to call a `@future` from inside Batch's `execute()`, you get a runtime error. Use chained Queueables or a child Batch instead.

---

## 4. You Cannot Enqueue More Than 1 Child Queueable Job Per Execution

```apex
public void execute(QueueableContext ctx) {
    System.enqueueJob(new JobA()); // ✅ Fine
    System.enqueueJob(new JobB()); // ❌ Only one child allowed — throws LimitException
}
```

If you need fan-out from a Queueable, use Platform Events or redesign the processing to be iterative (process chunk, chain one next job).

---

## 5. Each `execute()` Chunk in Batch Gets Fresh Limits — But `start()` and `finish()` Do Not

`start()` shares a transaction with framework overhead. If your `start()` method runs complex SOQL or transforms, it can hit limits. Keep `start()` minimal — use a simple `Database.getQueryLocator()`.

---

## 6. `Database.getQueryLocator()` Can Return Up to 50 Million Rows; `[SELECT]` Returns Only 50,000

For large-scale processing always use `Database.getQueryLocator()` in `start()`. Direct SOQL (even with LIMIT) fails once you exceed 50,000 records.

---

## 7. Heap Limit Is Easy to Hit With Large String Operations

JSON serialization, long string concatenation, and large `Map` objects consume heap. Classic trap: deserializing a large API response inside a loop.

```apex
// ❌ Heap problem — parsing a large payload per record
for (String payload : payloads) {
    Map<String, Object> parsed = (Map<String, Object>) JSON.deserializeUntyped(payload);
    // ... process
}

// ✅ Process one at a time in a Queueable, setting payload = null after use
```

---

## 8. Flow Invoked From Apex Shares the Calling Transaction's Governor Limits

Calling `Flow.Interview.createInterview()` or a Process Builder from Apex does not give the Flow its own governor limit context. The Flow's queries and DML statements count against the calling Apex transaction's budget.

---

## 9. Scheduled Apex Has a Global Limit of 100 Scheduled Jobs

Across the org. If you have many scheduled Apex classes running at the same time, new ones fail to schedule. Use a single master scheduler that dispatches to batch classes.

---

## 10. `Test.startTest()` / `Test.stopTest()` Resets Governor Limits AND Forces Async Execution

Governors reset at `startTest()`. Async jobs (`@future`, `Queueable`, `Batch`) don't run until `stopTest()` is called. Always call `stopTest()` before asserting on async results — not doing so is a common source of "test passes locally, fails in deployment" bugs.

```apex
Test.startTest();
System.enqueueJob(new MyQueueable(records));
Test.stopTest(); // ← async actually runs here

// Assert after stopTest
System.assertEquals('Expected', [SELECT Status__c FROM MyObject__c WHERE Id = :id].Status__c);
```
