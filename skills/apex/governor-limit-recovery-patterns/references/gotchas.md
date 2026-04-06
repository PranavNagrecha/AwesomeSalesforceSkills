# Gotchas — Governor Limit Recovery Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LimitException Cannot Be Caught — Not Even with catch(Exception e)

**What happens:** When any governor limit is exceeded, the Apex runtime throws `System.LimitException`. Unlike `DmlException`, `CalloutException`, or even `NullPointerException`, this exception type bypasses all catch blocks. The transaction terminates, the full stack unwinds, and a complete rollback occurs. No catch handler fires.

**When it occurs:** Triggered by any limit breach: 101st synchronous SOQL query, 151st DML statement, CPU time over 10 000 ms, heap over 6 MB, etc. Developers discover this behavior when a catch block they expected to fire silently never executes.

**How to avoid:** Never design limit-breach recovery around try/catch. Design recovery to fire before the limit is reached using `Limits.*` comparisons. Threshold: if remaining headroom is less than your per-iteration cost plus a buffer, exit the loop or defer work.

---

## Gotcha 2: sObject Id Is Not Cleared After Database.rollback()

**What happens:** After `Database.rollback(sp)`, the in-memory sObject variable that was inserted retains its `Id` field value. The Id was assigned by the pre-rollback DML and is now referencing a record that no longer exists in the database. Any code that checks `record.Id != null` will incorrectly treat this as a successfully persisted record.

**When it occurs:** Any time code checks Id presence as a "was this committed?" indicator after a rollback. Common in service layers that inspect Id to decide whether to update vs. insert, or in event-driven code that reads the Id to publish a platform event.

**How to avoid:** Explicitly null the Id field immediately after `Database.rollback(sp)`: `record.Id = null;`. Document this requirement with a comment near the rollback call so future maintainers understand why the explicit null assignment is necessary.

---

## Gotcha 3: Static Variables Are Not Reset on Rollback

**What happens:** `Database.rollback(sp)` reverts DML state and resets the `Limits.*` counters for DML and queries, but it does NOT reset static variables. Any `static Map`, `static Set`, `static Integer`, or other static state that was modified between the savepoint and the rollback call retains its post-savepoint values.

**When it occurs:** Trigger handler frameworks that use static sets to track processed record IDs (recursion prevention), static caches populated during the same transaction, or static counters tracking batch progress. After rollback the static state is stale, causing records to be silently skipped on re-processing or double-counted.

**How to avoid:** After calling `Database.rollback(sp)`, explicitly reset any static variables that were mutated after the savepoint. Use a dedicated cleanup method in the class that manages static state, and call it in the same code block as the rollback call.

---

## Gotcha 4: setSavepoint() Itself Consumes a DML Statement

**What happens:** Each call to `Database.setSavepoint()` counts as one DML statement toward the 150-statement synchronous limit (or 150 async limit). Developers who add savepoints to "protect" DML-heavy code inadvertently make the DML budget situation worse.

**When it occurs:** In any transaction where DML is already near the ceiling. Adding 2-3 savepoints in nested service calls can push a transaction from safe to failing, particularly in trigger contexts where multiple handlers are chained.

**How to avoid:** Use at most one or two savepoints per logical transaction unit. Do not nest savepoints in every helper method. Check `Limits.getDMLStatements()` before calling `setSavepoint()` just as you would before any DML, and treat the savepoint call as a DML statement in your budget calculation.

---

## Gotcha 5: BatchApexErrorEvent JobScope Truncation Is Silent

**What happens:** `BatchApexErrorEvent.JobScope` is a String field containing a comma-separated list of record IDs from the failed scope. When the scope is large enough that the full ID list exceeds the field's character limit, the platform sets `DoesExceedJobScopeMaxLength = true` and truncates `JobScope` mid-string. A handler that splits on comma without checking the flag receives an incomplete list with a potentially malformed final entry.

**When it occurs:** Large batch scopes (e.g., 2000-record scopes with 18-character Ids) or scopes where each ID is repeated in a custom format. The truncation point is not predictable and may cut an ID in half.

**How to avoid:** Always check `DoesExceedJobScopeMaxLength` before parsing `JobScope`. When it is `true`, fall back to a SOQL query using the `AsyncApexJobId` and a status field rather than attempting to parse the truncated string.

---

## Gotcha 6: Limits Class Returns Zero During Test Execution Unless @isTest Context Includes Real Operations

**What happens:** In test classes, `Limits.getQueries()` and related methods return 0 until real SOQL, DML, or CPU-consuming operations are actually executed within the test context. Mocked or no-op tests that bypass database interaction will show 0 usage regardless of what the production code path would consume, making headroom tests appear to pass trivially.

**When it occurs:** Unit tests that use `Test.setMock()` for callouts, or tests with entirely mocked service layers, may not exercise the Limits checkpoints at all because no real DML or SOQL is issued.

**How to avoid:** Write integration-style tests that insert real test data and execute the full code path to validate that Limits checkpoints fire under real consumption. Parameterize the checkpoint threshold in a constant so you can lower it in tests to simulate near-limit conditions without requiring 100+ records.
