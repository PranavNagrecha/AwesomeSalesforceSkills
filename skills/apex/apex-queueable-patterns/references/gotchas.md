# Gotchas — Apex Queueable Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `MaximumQueueableStackDepth` Must Be Re-Set On Every Enqueue Call In The Chain

**What happens:** A developer sets `AsyncOptions.MaximumQueueableStackDepth = 5` on the first `enqueueJob()` call and assumes the limit propagates to all subsequent chained jobs automatically. It does not. If the child job calls `System.enqueueJob()` without its own `AsyncOptions` instance, the depth guard is not applied and the chain can exceed the intended limit.

**When it occurs:** Multi-step Queueable chains where the first job sets `AsyncOptions` but passes the constructor — not the options — to child jobs, which then re-enqueue without options.

**How to avoid:** Make `AsyncOptions` configuration part of the enqueue call at every level of the chain. A static helper method or a shared constant that constructs the `AsyncOptions` object is the cleanest way to enforce this consistently across all chain links. Verify with `System.AsyncInfo.getCurrentQueueableStackDepth()` inside each `execute()` and log or alert if depth unexpectedly reaches the cap.

---

## Finalizer Failure Does Not Roll Back The Parent's Committed Work

**What happens:** The parent Queueable completes and commits its DML. The Finalizer runs in a separate transaction and itself throws an exception. The parent's committed records remain committed — there is no rollback. The Finalizer's own transaction is rolled back, so any DML the Finalizer attempted (failure records, notifications) is also lost.

**When it occurs:** Finalizer code performs expensive SOQL inside a loop, exceeds its own DML limits, or tries to handle exceptions from the parent without guarding against its own governor limit issues.

**How to avoid:** Treat the Finalizer as a lightweight coordinator, not a heavy processor. Keep it under the same discipline applied to any Apex transaction: no SOQL in loops, no unbounded collections, DML statements counted carefully. If the Finalizer itself needs to do significant work, it should enqueue another Queueable to do it rather than executing inline. Monitor Finalizer failures through `AsyncApexJob` where the `JobType` is `Queueable` and the `Status` is `Failed`.

---

## Static Variables Do Not Survive Between Chained Queueable Transactions

**What happens:** A developer uses a static variable to accumulate state across chained Queueable jobs — for example, a static `List<String>` to collect log entries. The list is populated in job 1 but is empty (re-initialized to its declaration default) when job 2 starts.

**When it occurs:** Teams familiar with `Database.Stateful` in Batch Apex expect Queueable to offer similar in-memory continuity. It does not. Each chained Queueable runs in a completely fresh Apex transaction; all static and instance state from the previous transaction is gone.

**How to avoid:** Pass all required state through constructor parameters of the next Queueable job. Use serializable types: primitives, Lists, Sets, Maps of primitives, and lightweight inner classes. For larger accumulated state (error lists, processed IDs), write to a custom object or use a Platform Event in the parent job before chaining, then read from storage in the next job. Never rely on static variables to bridge async transactions.

---

## `Database.AllowsCallouts` Omission Fails At Runtime, Not Compile Time

**What happens:** A Queueable class makes an `Http.send()` call but does not declare `implements Database.AllowsCallouts`. The class compiles and deploys cleanly. At runtime the job throws `System.CalloutException: Callout not allowed from this future method`. The error message references "future method" even though the job is Queueable, which causes confusion when reading debug logs.

**When it occurs:** Developers port logic from an existing callout class into a Queueable without checking the interface declaration, or a code review misses the missing interface on a PR that only touches the method body.

**How to avoid:** The `implements` line on any Queueable that makes callouts must read `implements Queueable, Database.AllowsCallouts`. Add a static analysis check (see `scripts/check_apex_queueable_patterns.py` in this skill) that flags Queueable classes containing `Http` or `WebServiceCallout` references without the `AllowsCallouts` interface declaration.

---

## Tests Execute Queueables Synchronously And Do Not Enforce The Single-Child Limit

**What happens:** A unit test for a Queueable that chains two children passes cleanly in sandbox. The same code fails with `System.LimitException: Too many queueable jobs added to the queue: 2` in production.

**When it occurs:** Apex unit tests run async jobs synchronously within `Test.stopTest()`. In this synchronous execution mode the single-child enqueue limit is not enforced. Tests that enqueue multiple children from one `execute()` call pass without error. Production enforces the limit.

**How to avoid:** Do not treat a passing unit test as proof that the chaining logic respects the single-child rule. Manually review `execute()` bodies and count `System.enqueueJob()` calls. Use the static checker in this skill to flag files with multiple enqueue calls inside a `void execute(QueueableContext` block.
