# Gotchas — Recursive Trigger Prevention

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Line citations of the form `apexdev L<n>` refer to the Apex Developer Guide, Version 67.0, Summer '26
(<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf>).

## Static Boolean Guards Hide Skipped Work

**What happens:** The loop stops recursing, but some legitimate records never receive required processing.

**When it occurs:** One flag controls the whole transaction.

**How to avoid:** Use record-aware guards or delta checks instead of a single global Boolean.

---

## A `hasRun` Flag Is Consumed By The First Batch Of 200

**What happens:** A 400-row load processes rows 1–200 and silently drops rows 201–400. The load reports
complete success — no error, no rejected row, just missing downstream work.

**When it occurs:** Any DML over 200 records. "DML operations that include over 200 records are
processed in batches, and the trigger is invoked for each batch. `Trigger.size` includes only the number
of records in the current batch, not the total number of records in the DML operation"
(`apexdev` L15029–15033). The guard is a static, and "the value of a static variable persists within the
context of a single transaction… if an Apex DML request causes a trigger to fire multiple times, the
static variables persist across these trigger invocations" (`apexdev` L3738–3740). Batch one sets the
flag; batch two reads it as already set.

**How to avoid:** Key the guard by record Id, so the size of the guard grows with the work rather than
being exhausted by it. Prove it with a 400-record test — `references/code-examples.md`,
`guardSurvivesTwoHundredRecordChunking`.

---

## A Static Declared Inside The `.trigger` File Is Not The Same Variable Next Context

**What happens:** A guard set in `before insert` reads as `false` in `after insert` of the same save.
The handler runs twice, and the developer concludes the guard "doesn't work" and makes it broader.

**When it occurs:** The static is declared in the trigger body rather than in a class. "A static
variable defined in a trigger doesn't retain its value between different trigger contexts within the
same transaction, such as between before insert and after insert invocations. Instead, define the static
variables in a class so that the trigger can access these class member variables"
(`apexdev` L3761–3763).

**How to avoid:** Guards live in a class — `RecursionGuard`, or the handler's own static. The trigger
file holds one dispatch line and nothing else.

---

## Partial-Success DML Refires Triggers With The Statics Still Dirty

**What happens:** `Database.update(records, false)` succeeds on the retry, but the retried subset gets no
processing at all, because the guard from attempt one is still populated.

**When it occurs:** Any `allOrNone = false` DML, and any bulk call arriving through the API with default
settings. The runtime "makes a second attempt that includes only those records that didn't generate
errors", up to a third attempt (`apexdev` L9070–9076), and "Apex triggers are fired for the first save
attempt, and if errors are encountered… triggers are refired on this subset of records"
(`apexdev` L9079–9080). Governor limits are reset between those attempts; static variables are not —
"Because these trigger invocations are part of the same transaction, static class variables that are
accessed by the trigger aren't reset" (`apexdev` L15499–15501).

**How to avoid:** A fingerprint-keyed guard re-serves the retried rows because their values are
unchanged and they were never marked. A `hasRun` Boolean does not. If a guard must be reset between
attempts, reset it from the code that owns the DML, not from a `finally` inside the handler.

---

## A Rollback Does Not Roll Back The Guard

**What happens:** A savepoint rollback undoes the records but leaves the guard marked. The retry runs
against a clean database with a dirty guard, and processes nothing.

**When it occurs:** Any `Database.rollback(Savepoint)` in the same transaction as a guarded trigger.
"Static variables aren't reverted during a rollback. If you try to run the trigger again, the static
variables retain the values from the first run" (`apexdev` L8692–8693). Related trap in the same list:
"References to savepoints can't cross-trigger invocations… If you declare a savepoint as a static
variable then try to use it across trigger contexts, you receive a run-time error" (`apexdev` L8689–8691).

**How to avoid:** Treat guard state as belonging to the transaction, not to the data. Code that rolls
back must explicitly clear the guard for the affected Ids before retrying.

---

## The Workflow Field Update Re-Fire Is Exactly One Extra Pass — And `Trigger.old` Lies On It

**What happens:** The handler runs a third time on what looks like an unchanged record, and the delta
check compares against values nobody ever saved.

**When it occurs:** A workflow rule with a field update fires on the save. Step 11 of the order of
execution updates the record again, re-runs system validations, and "executes before update triggers and
after update triggers, regardless of the record operation (insert or update), one more time (and only
one more time)" (`apexdev` L15455–15460). On that pass, "`Trigger.old` doesn't hold the newly updated
field by the workflow after the update. Instead, `Trigger.old` holds the object before the initial
record update was made" — the guide's own example: a field goes 1 → 10 (user) → 11 (workflow), and
`Trigger.old` reads 1, not 10 (`apexdev` L15494–15498).

**How to avoid:** Do not try to suppress this pass; it is bounded at one and it usually carries values
you want. Guard on a fingerprint of the fields you read, so an identical echo is dropped and a real
change is served. `apex/order-of-execution-deep-dive` and `flow/flow-record-save-order-interaction` own
the full step list.

---

## A Recursive Save Skips Steps 9 Through 17

**What happens:** Work chained from inside a trigger's own DML never gets its assignment rule,
auto-response, escalation, or roll-up summary. The team adds a second trigger to compensate, and now has
a recursion problem *and* an ordering problem.

**When it occurs:** Any DML issued from inside a trigger. "During a recursive save, Salesforce skips
steps 9 (assignment rules) through 17 (roll-up summary field in the grandparent record)"
(`apexdev` L15414–15415).

**How to avoid:** Do not build a chain that depends on those steps running on the nested save. If the
requirement genuinely needs an assignment rule to run, the record has to be saved by a non-recursive
operation — usually asynchronously, after commit.

---

## The Ceiling Is A Stack Depth Of 16, And It Arrives As An Uncatchable Failure

**What happens:** The user clicks Save and gets a limit exception rather than a friendly message. The
loop does not degrade gracefully; it hits a wall — a `LimitException` is one of the "uncatchable Apex
exceptions… caused by reaching governor limits" (`apexdev` L17856), so no `try/catch` in the handler
can turn it into a warning.

**When it occurs:** "Total stack depth for any Apex invocation that recursively fires triggers due to
insert, update, or delete statements" is 16, synchronous and asynchronous alike (`apexdev` L19559). The
guide is explicit about why that number is so much lower than other limits: "recursive Apex that fires a
trigger spawns the trigger in a new Apex invocation. The new invocation is separate from the invocation
of the code that caused it to fire. Spawning a new invocation of Apex is a more expensive operation than
a recursive call in a single invocation. Therefore, there are tighter restrictions on the stack depth"
(`apexdev` L19638–19648).

**How to avoid:** Never rely on 16 as the guard. It is the crash barrier. `TriggerHandler`'s own
`MAX_DEPTH` of 10 throws a readable `TriggerHandlerException` before the platform does — keep it, and
put the real fix in the per-record guard.

---

## Bulk API Resets Governor Limits Between Chunks But Not The Statics

**What happens:** A guard that infers "am I re-entering?" from `Limits.getDmlStatements()` or
`Limits.getQueries()` reads zero on every chunk of a Bulk API load and concludes it is a fresh
transaction each time — while the actual guard statics carry over.

**When it occurs:** Any Bulk API job. "If a Bulk API request causes a trigger to fire multiple times for
chunks of 200 records, governor limits are reset between these trigger invocations for the same HTTP
request. Static variables aren't reset within the multiple trigger invocations for the same Bulk API
request" (`apexdev` L3789–3792, restated at L14904–14907 and in the Version 21.0 versioned-behaviour note
at L44982–44986).

**How to avoid:** Never derive re-entry state from limit counters. The two reset on different schedules,
and the mismatch only shows up under Bulk API — which is to say, in production data loads and not in any
test.

---

## `TriggerHandler.skipOnce()` Really Does Mean Once — Not Once Per Record

**What happens:** A handler calls `TriggerHandler.skipOnce('ChildTriggerHandler')` before updating 500
children, expecting the child trigger to stay quiet. The first batch of 200 is skipped and the remaining
300 run.

**When it occurs:** `templates/apex/TriggerHandler.cls` implements the skip as
`skipOnceHandlers.remove(handlerName)` — a `Set.remove()` that returns `true` exactly once and empties
the entry. Because a DML over 200 rows invokes the trigger once per batch (`apexdev` L15029–15033), the
second invocation finds the set empty.

**How to avoid:** Use `skipOnce` only for a DML you can prove is at most 200 rows. For anything larger,
mark the child Ids in the record-keyed guard before the DML, or switch the handler off through
`TriggerControl` for the duration.

---

## Two Triggers On The Same Event Have No Guaranteed Order

**What happens:** The guard set by trigger A may or may not be visible to trigger B, and which one runs
first can change between deployments. The recursion bug is intermittent and unreproducible.

**When it occurs:** More than one trigger on an object for the same event. "If more than one trigger is
defined on an object for the same event, the order of trigger execution isn't guaranteed"
(`apexdev` L15502–15504).

**How to avoid:** One trigger per object, dispatching to one handler. The checker in
`scripts/check_recursive_trigger_prevention.py` WARNs when it finds a second `.trigger` file on the same
sObject. Consolidation itself belongs to `apex/trigger-framework`.

---

## Not All Re-Entry Is Accidental

**What happens:** A guard prevents a second pass that was actually part of the intended design.

**When it occurs:** Teams assume every repeated execution is a bug.

**How to avoid:** Identify which re-entry paths are legitimate before installing the guard.

---

## The Trigger Might Not Be The Only Source

**What happens:** Teams blame the trigger while surrounding automation or related-object updates are causing the extra pass.

**When it occurs:** The order of execution is not traced fully.

**How to avoid:** Map the full automation chain before deciding where the guard belongs. A record-triggered
flow is a live participant: "When a process or flow executes a DML operation, the affected record goes
through the save procedure" (`apexdev` L15468), and its run order relative to other flows on the object is
set by the `triggerOrder` field, an int from 1 to 2,000 (`api_meta` L68438–68441).

---

## Guard Placement Matters

**What happens:** A guard exists, but it runs after the self-DML path has already been queued.

**When it occurs:** The guard is added late in the method rather than before the recursive branch.

**How to avoid:** Place the guard directly ahead of the self-triggering operation.
