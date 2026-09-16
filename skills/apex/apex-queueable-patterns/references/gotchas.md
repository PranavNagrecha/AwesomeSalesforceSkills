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

## The Duplicate Signature Is Released At Dequeue, Not At Completion

**What happens:** A team adds `AsyncOptions.DuplicateSignature` expecting "only one instance of this job runs at a time." What they get is "only one instance sits *in the queue* at a time." The signature is removed when the job starts processing, not when it finishes: per the Apex Developer Guide, "if other jobs with the same signature are already running when the new job is enqueued, then the enqueue operation for the new job succeeds." The removal is deliberate — it guarantees at least one job instance per signature runs. Two concurrent executions of the same logical work therefore remain possible, along with the row-lock contention the team hoped to remove.

The suppressed enqueue is not silent. `System.enqueueJob(job, options)` throws `DuplicateMessageException`:

```text
Attempt to enqueue job with duplicate queueable signature
```

Thrown, not returned — so an uncaught one inside a trigger surfaces to the user as failed DML, not a benign no-op.

**When it occurs:** A long-running recalculation enqueued from a record-triggered path while a prior instance is mid-execution; or any code that treats `DuplicateMessageException` as an error rather than the success path.

**How to avoid:** Catch `DuplicateMessageException` and treat it as "work already queued — nothing to do." For true single-execution semantics the signature is not enough: pair it with a status field or a `FOR UPDATE`-guarded control record flipped at the start of `execute()`. Build signatures from stable business keys via `new System.QueueableDuplicateSignature.Builder().addId(...).addString(...).build()` (the Reference Guide sample uses `new`, `apexrefguide` L227456-227461; the Developer Guide sample omits it, `apexdev` L16243-16248 — prefer the `new` form). The builder is size-bounded: `getSize()`, `getRemainingSize()` and `getMaxSize()` report the signature in bytes (`apexdev` L16228-16232), so a signature built from a long concatenated string can run out of room — including a timestamp or a `Trigger.new` size defeats the mechanism, because every transaction then produces a different signature.

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

**When it occurs:** Apex unit tests run async jobs synchronously within `Test.stopTest()` — *"The system executes all asynchronous processes started in a test method synchronously after the Test.stopTest statement."* (`apexdev` L16123-16126).

UNVERIFIED (2026-09-05): that the single-child enqueue limit goes *unenforced* in that synchronous mode is not stated in either extracted guide. What they state is narrower and points the other way — *"You can test chained queueable jobs by using appropriate stack depths, but be aware of applicable Apex governor limits."* (`apexdev` L16166-16167). Treat the passing test as no evidence either way rather than as proof the rule is enforced.

**How to avoid:** Do not treat a passing unit test as proof that the chaining logic respects the single-child rule. Manually review `execute()` bodies and count `System.enqueueJob()` calls. Use the static checker in this skill to flag files with multiple enqueue calls inside a `void execute(QueueableContext` block.

---

## The Synchronous Enqueue Ceiling Is 50, Not 1 — So The Per-Record Loop Survives Testing

**What happens:** A trigger handler calls `System.enqueueJob` once per qualifying
record. The developer tests with a handful of records; nothing fails. The first
Data Loader batch of 200 blows up mid-save.

The limit that is nearly always quoted — one job per transaction — is the
*asynchronous* one. The guide is explicit: *"You can add up to 50 jobs to the
queue with System.enqueueJob in a single transaction. In asynchronous
transactions (for example, from a batch Apex job), you can add only one job to
the queue"* (`apexdev` L16179-16181). The limits table reads the same: 50
synchronous, 1 asynchronous (`apexdev` L19573).

**When it occurs:** Any per-record enqueue reached from a synchronous entry
point — a trigger, an `@AuraEnabled` method, an Apex REST resource. It fails on
the 51st qualifying record, not the second, so a manual test with 10 records and
a unit test with 5 both pass.

**How to avoid:** Collect Ids across the whole `Trigger.new`, enqueue once, and
read `Limits.getQueueableJobs()` against `Limits.getLimitQueueableJobs()`
(`apexdev` L16181; `apexrefguide` L220873-220895) if a code path can legitimately
enqueue more than one job. The checker in this skill flags `System.enqueueJob`
inside a `for` loop as an ERROR for exactly this reason.

---

## `@IsTest(IsParallel=true)` Bans `System.enqueueJob` Outright

**What happens:** Someone annotates a test class `@IsTest(IsParallel=true)` to
speed up the suite. Every Queueable test in it fails, and the failure names the
enqueue rather than the annotation.

The restriction is absolute, not a limit: *"Tests can not call the
System.schedule() and System.enqueueJob() methods."* (`apexdev` L5965, under
`@IsTest(IsParallel=true) Annotation`). There is no parallel-safe way to enqueue.

**When it occurs:** During a test-runtime optimisation pass, or when a class is
copied from a codebase that annotates every test class for parallelism by
convention.

**How to avoid:** Keep `IsParallel=true` off any test class that enqueues. If the
suite needs the parallelism, split the Queueable assertions into their own class
without the annotation. Leave a comment on the class saying why — the next person
to run a suite-wide annotation sweep needs it.

---

## A Queueable Never Enters The Flex Queue, So Half The Standard Monitoring Query Is Dead

**What happens:** A monitoring query written for Batch Apex is reused for
Queueable jobs. It filters or reports on `Status = 'Holding'`, or gates a runbook
step on `JobItemsProcessed`. Both return nothing useful, forever.

Two separate facts collide. `Holding` is footnoted in the object reference as
*"This status applies to batch jobs in the Apex flex queue"*
(`object_reference` L42423-42429), and the flex queue accepts batch jobs only
(`apexdev` L17234-17240) — a Queueable is never held. And the batch counters are
hard-wired to zero: *"Similar to future jobs, queueable jobs do not process
batches, and so the number of processed batches and the number of total batches
are always zero."* (`apexdev` L16012-16013).

**When it occurs:** Any org that standardised its async monitoring on Batch Apex
first, which is most of them.

**How to avoid:** For `JobType = 'Queueable'` the meaningful columns are `Status`
(`Queued`, `Processing`, `Completed`, `Failed`, `Aborted`), `NumberOfErrors` and
`ExtendedStatus` (`object_reference` L42305-42311, L42419-42427). Progress inside
a chain has to be recorded by the code — a counter on a control record or an
`Application_Log__c` row per link. See `references/code-examples.md` § 7.

---

## `transient` Fields Arrive `null`, And Nothing Warns You

**What happens:** A member variable is marked `transient` — often copied from a
Visualforce controller, sometimes added deliberately to keep the serialized job
small. The job compiles, deploys, and runs with that field `null`.

*"Variables that are declared transient are ignored by serialization and
deserialization and the value is set to null in Queueable Apex."*
(`apexdev` L15975-15976). The same is true of a Finalizer field
(`apexdev` L16360-16361).

**When it occurs:** Porting controller code into a job; or a well-meant attempt
to shrink serialized state, where the correct move is to pass Ids and re-query.

**How to avoid:** No `transient` on any Queueable or Finalizer member. To shrink
state, narrow what is carried: a `Set<Id>` and a re-query beats a `List<SObject>`
with every field populated, and it also removes the deserialization break that
follows a field-set change between deployments.

---

## Enqueuing Async Apex Needs "View Setup and Configuration" Outside System Mode

**What happens:** A Queueable enqueued from an `@AuraEnabled` method or an
Experience Cloud context fails for some users and works for admins. Nothing in
the class differs between them.

The permission is documented on the object, not on the interface: *"If Apex is
not running in system mode, users must have the View Setup and Configuration
permission to access this object and to enqueue asynchronous Apex jobs."*
(`object_reference` L42269-42271, AsyncApexJob, Special Access Rules).

**When it occurs:** `with sharing` / user-mode code paths reached by
minimum-access personas, community users, or integration users provisioned with a
lean permission set. It never reproduces for the developer.

**How to avoid:** Treat View Setup and Configuration as a dependency of the
feature and put it on the permission set that grants the feature, or move the
enqueue into a system-mode entry point. Include the enqueue in the persona test
matrix rather than testing it only as an admin.

---

## Before API 67.0, A Queueable With No Sharing Declaration Ran `without sharing`

**What happens:** A Queueable class declared as plain `public class MyJob` reads
and writes records the running user cannot see. Recompiling it later at a newer
API version quietly changes that.

*"In API version 67.0 and later, classes without an explicit sharing declaration
run in with sharing mode."* At API 66.0 and earlier the mode was inferred, and
for a class that is an entry point with no calling class — which is exactly what a
Queueable is in its own transaction — *"Otherwise, the class runs in without
sharing mode."* (`apexdev` L4961-4967).

**When it occurs:** On an old class the day someone bumps its `apiVersion`, or on
a new class in a codebase where the sharing declaration is inconsistent. The
symptom is a job that used to return everything now returning less.

**How to avoid:** Declare it. `with sharing`, `without sharing` or
`inherited sharing` on every Queueable and every Finalizer, chosen deliberately,
and paired with `WITH USER_MODE` or `as user` on the DML where user-mode
enforcement is the intent (`apexdev` L15986, L16007-16009).

---

## The Delay Parameter Is Ignored In Tests, And The Two Delay Sources Do Not Compose

**What happens:** A back-off is implemented with
`AsyncOptions.MinimumQueueableDelayInMinutes` and a test is written to prove the
ordering. The test proves nothing: *"The delay is ignored during Apex testing."*
(`apexdev` L16018; `apexrefguide` L238954-238975).

The second half bites in production. An explicit delay does not add to the
org-wide floor, it replaces it — *"Using the System.enqueueJob(queueable, delay)
method ignores any org-wide enqueue delay setting."* (`apexdev` L16036). So
passing `0` runs as fast as the platform allows even in an org whose
`ApexSettings.DefaultQueueableDelay` is 600 seconds (`api_meta` L110718-110724),
and the guide warns that with chained jobs a zero delay can *"rapidly reach the
daily async Apex limit"* (`apexdev` L16021-16023).

**When it occurs:** Rate-limit back-off against an external API; polling loops;
any org where an admin set a global delay as a throttle and code later bypasses
it by passing an explicit one.

**How to avoid:** Assert on the value passed to the enqueue helper, not on
observed timing. Read the effective floor at runtime with
`System.AsyncInfo.getMinimumQueueableDelayInMinutes()` (`apexrefguide`
L201128-201139) and pass `Math.max(requested, effectiveFloor)` rather than a bare
constant, so an admin throttle is respected instead of overridden.

---

## A Callout After DML In The Same `execute()` Throws, Even With `AllowsCallouts`

**What happens:** A Queueable implements `Database.AllowsCallouts`, updates
records, then posts the result to an external system. The callout fails with
uncommitted-work pending, and the marker interface is blamed.

The interface grants permission to call out; it does not change transaction
ordering. *"You can not make a callout when there are pending operations in the
same transaction. Things that result in pending operations are DML statements,
asynchronous Apex (such as future methods and batch Apex jobs), scheduled Apex, or
sending email. You can make callouts before performing these types of
operations."* (`apexdev` L35860-35862). The runtime message is
`UnexpectedException: A callout was unsuccessful because of pending uncommitted
work related to a process, flow, or Apex operation.` (`apexdev` L26230-26232).

**When it occurs:** Fetch-then-save jobs refactored into save-then-notify jobs;
or a chained job where an earlier step in the same `execute()` acquired a lock.

**How to avoid:** Order every `execute()` as callouts first, DML second. When
both directions are genuinely needed, split them: the callout job chains a child
that does the DML, or the DML job attaches a Finalizer that makes the callout —
*"Callouts are allowed in finalizer implementations."* (`apexdev` L16356) and the
Finalizer runs in its own transaction (`apexdev` L16296-16297). See
`apex/callout-and-dml-transaction-boundaries` for the full ordering treatment.

---

## Checker Ignores Comments And String Literals

**What happens:** The skill checker flags a keyword that appears only in a comment or a string literal (for example a note that `WITH SECURITY_ENFORCED` is not used, or an assertion message that mentions `EventBus.publish`).

**When it occurs:** Before the checker blanked `//` line comments, `/* … */` block comments, and `'…'` string literals to spaces (same length, newlines preserved) for code-pattern rules.

**How to avoid:** Trust the checker on executable code only. Mentions inside comments and string literals are ignored for pattern matches; rules that intentionally read comments (for example a `// reason:` search) still read the original text.
