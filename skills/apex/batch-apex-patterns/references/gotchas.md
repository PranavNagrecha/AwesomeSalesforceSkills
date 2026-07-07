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

---

## The 50-Million QueryLocator Cap Silently Bounds Your Design

**What happens:** A design assumes a `Database.QueryLocator` will address the entire object, but the addressable set is larger than the 50-million-record ceiling a QueryLocator can return.

**When it occurs:** Truly large-data-volume objects are processed with a QueryLocator instead of a custom `Iterable` in `start()`.

**How to avoid:** Past 50 million records, return an `Iterable` from `start()` — it is not subject to the QueryLocator cap, but the iterable must then be produced within normal per-transaction SOQL limits.

---

## Only Five Batch Jobs Run At Once — The Rest Queue

**What happens:** A fan-out design fires many `Database.executeBatch()` calls expecting them to run in parallel, but the org only allows 5 batch jobs queued or active at a time.

**When it occurs:** Multiple batches are launched together (e.g., one per region or per object) without accounting for concurrency.

**How to avoid:** Serialize the work (chain the next batch from `finish()`) or schedule submissions. Beyond the 5-slot cap, jobs hold in the Apex flex queue, which tops out at 100 holding jobs.

---

## Tiny Scope Sizes Can Exhaust The 24-Hour Execution Ceiling

**What happens:** An aggressively small scope on a huge dataset multiplies `execute()` invocations and pushes against the 250,000-executions-per-24-hours (or user-licenses × 200) ceiling.

**When it occurs:** Scope size is minimized for per-scope safety without considering total execution count across the dataset.

**How to avoid:** Choose scope size against both per-scope throughput and the 24-hour execution ceiling; each scope is one method execution counted toward that limit.
