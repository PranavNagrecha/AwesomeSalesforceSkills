# Gotchas — Batch Apex Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `Database.Stateful` Persists State, Not Good Judgment

**What happens:** Teams keep large collections or payloads in instance variables across scopes.

**When it occurs:** Stateful is used for convenience instead of lightweight counters or IDs.

**How to avoid:** Persist only the minimum necessary cross-scope state.

---

## Scope Size Is A Performance Lever, Not A Default To Ignore

**What happens:** A job uses an inherited batch size even though the work has heavy callouts or expensive CPU logic.

**When it occurs:** Scope size is never revisited after the initial implementation.

**How to avoid:** Tune scope based on payload size, lock contention, and external system tolerance.

---

## `finish()` Is Often The Only Safe Completion Boundary

**What happens:** Teams assume that once `executeBatch()` returns a job ID, the workflow is effectively done.

**When it occurs:** Follow-up actions are triggered too early.

**How to avoid:** Put completion notifications and downstream dispatch in `finish()` where appropriate.

---

## Batch Tests Need `Test.stopTest()`

**What happens:** Assertions run before batch work has executed.

**When it occurs:** Tests enqueue the batch but do not force completion.

**How to avoid:** Execute the batch between `Test.startTest()` and `Test.stopTest()`.
