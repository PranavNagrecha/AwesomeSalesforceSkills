# Gotchas — Callout and DML Transaction Boundaries

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: DML From a Different Class or Package Still Blocks Your Callout

**What happens:** Your class has no DML before the callout, but the callout still throws `System.CalloutException: You have uncommitted work pending`. A managed package, trigger handler, or utility class earlier in the same transaction performed DML that you did not write.

**When it occurs:** Any time your code runs in a transaction that includes trigger handlers, before/after flows, or managed package subscribers that touch DML before your callout executes.

**How to avoid:** Always trace the full transaction path, not just your own class. If DML from external code is unavoidable, move the callout to a Queueable. Use debug logs filtered to `DML_BEGIN` and `CALLOUT_REQUEST` to confirm ordering.

---

## Gotcha 2: Savepoints Do Not Clear Uncommitted Work for Callout Purposes

**What happens:** A developer creates a savepoint, performs DML, rolls back to the savepoint, and then attempts a callout — expecting the rollback to clear the "uncommitted work" flag. The callout still throws the exception.

**When it occurs:** Any time `Database.setSavepoint()` and `Database.rollback()` are used before a callout in the same transaction.

**How to avoid:** Savepoints do not reset the callout restriction. The platform tracks that DML was attempted in the transaction regardless of rollback. The only way to get a clean callout context is a separate transaction (Queueable or @future).

---

## Gotcha 3: Batch Apex execute() Resets Per Chunk But AllowsCallouts Must Be Declared

**What happens:** A Batch class attempts callouts in `execute()` but throws an error because the class does not implement `Database.AllowsCallouts`, even though each `execute()` invocation is its own transaction.

**When it occurs:** Implementing `Database.Batchable` without also implementing `Database.AllowsCallouts` on the same class.

**How to avoid:** Add `Database.AllowsCallouts` to the class declaration. Within each `execute()`, perform callouts before DML. Each chunk gets its own transaction, so the ordering resets per chunk.

---

## Gotcha 4: Platform Events and EventBus.publish() Count as DML

**What happens:** Publishing a platform event via `EventBus.publish()` counts as a DML operation. A subsequent callout in the same transaction throws the uncommitted-work-pending error.

**When it occurs:** Any time `EventBus.publish()` is called before a callout in the same execution context.

**How to avoid:** Publish platform events after all callouts, or move the callout to a separate async boundary. If you must publish first (for example, to log an event), defer the callout to a Queueable.

---

## Gotcha 5: Test.startTest/stopTest Forces Queueable Execution But Does Not Merge Transactions

**What happens:** In test classes, `Test.stopTest()` forces synchronous execution of enqueued Queueables. Developers sometimes expect the Queueable to share the test transaction and are confused when the Queueable runs in its own context (which is the correct and desired behavior for callout separation).

**When it occurs:** When writing test methods for the Queueable callout pattern.

**How to avoid:** Use `Test.setMock(HttpCalloutMock.class, mock)` before `Test.startTest()`. Assert callout results after `Test.stopTest()`. Remember that the Queueable runs in its own governor context, which is why the pattern works in production.
