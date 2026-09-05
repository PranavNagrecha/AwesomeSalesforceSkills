---
name: apex-batch-chaining
description: "Use this skill when you need to run one Batch Apex job immediately after another completes — chaining via finish(), managing Flex Queue capacity, or choosing between batch-to-batch chaining and a Queueable bridge. NOT for single-job batch design or scope sizing — use apex/batch-apex-patterns. NOT for choosing Batch vs Queueable — use apex/async-apex."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "chain batch jobs apex finish"
  - "run batch after batch completes"
  - "flex queue capacity check before executeBatch"
  - "database executeBatch from finish method"
  - "schedule next batch after current batch finishes"
  - "queueable alternative to batch chaining"
  - "chain a queueable after a batch job finishes"
  - "batch chain stopped halfway no error anywhere"
  - "restart a broken batch chain from where it failed"
  - "add a kill switch to a running batch pipeline"
  - "stop a batch job from re-enqueueing itself forever"
  - "capture which records failed in a batch job"
  - "trace which batch job started which downstream job"
  - "test that finish enqueues the next batch without running it"
  - "flex queue full LimitException from executeBatch"
  - "pass state from one batch job to the next"
tags:
  - batch-apex
  - batch-chaining
  - flex-queue
  - async
inputs:
  - "The batch class(es) to be chained in sequence"
  - "Any state that must be passed between chained jobs (record IDs, counters, error lists)"
  - "Expected volume of jobs to be enqueued — needed to assess Flex Queue risk"
outputs:
  - "Apex finish() implementation with FlexQueue capacity guard"
  - "Optional Queueable bridge for unlimited-depth or conditional chaining"
  - "Review checklist for test-class coverage and governor limit exposure"
  - "ChainOrchestrator class with a Custom Metadata kill-switch and a test seam"
  - "BatchApexErrorEvent subscriber trigger for mid-chain failure capture"
  - "AsyncApexJob verification queries and a scheduled watchdog query"
dependencies:
  - batch-apex-patterns
  - apex-queueable-patterns
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Apex Batch Chaining

This skill activates when a practitioner needs to trigger one or more Batch Apex jobs in a controlled sequence — using `finish()` callbacks, Flex Queue guards, or a Queueable bridge — and must avoid silent job-queue saturation or loss of intermediate state.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm you actually need chaining: if you only have one large job, use `batch-apex-patterns` instead.
- Know how much of each ceiling the org is already using. They are two separate limits, not one: *"Up to 5 batch jobs can be queued or active concurrently"* and *"Up to 100 Holding batch jobs can be held in the Apex flex queue"* (`apexdev` L17686–17687). The flex queue is additional capacity — *"only five active Batch Apex jobs are allowed at one time in your org. Jobs beyond this limit are placed in the Flex Queue, which is limited to 100 additional jobs"* (L15939–15940).
- Identify whether intermediate state must pass between jobs. `Database.Stateful` keeps state inside a single job; you need a different mechanism (Custom Settings, Custom Metadata, a temporary SObject, or a constructor parameter) to pass state between chained jobs.
- Confirm the API version on the **batch class** is 26.0 or later — *"Starting with API version 26.0, you can start another batch job from an existing batch job to chain jobs together"* (`apexdev` L17811); for 25.0 and earlier *"you can't call Database.executeBatch or System.scheduleBatch from any batch Apex method"* (L17836–17837). The version that governs is the running batch class's, not a helper's (L17838–17841). At API 52.0+ a flex-queue lock failure throws `System.AsyncException`; at 51.0 and earlier it returns the empty Id `000000000000000` (`apexrefguide` L207068–207070).
- Decide, now, how the chain will be stopped. Two mechanisms, both needed: a kill-switch a human flips without a deploy, and `System.abortJob` for a job already in flight (`apexdev` L17230).

---

## Questions to Ask Before Configuring

Ask these before writing the first `finish()`. Each maps to a gotcha this package documents; an agent that skips them ships a chain that deploys, passes its tests, and stops halfway in production with every job showing `Completed`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "When link N fails, must link N+1 still run, must the chain stop, or must it resume from where it stopped?" | These are three different designs: proceed-anyway, gate on `AsyncApexJob.NumberOfErrors`, or re-drive from a staging object. Chain-stops-quietly is the default and almost never what anyone wanted (gotcha 10) | The gate condition in every `finish()`, and whether a `BatchApexErrorEvent` subscriber is in scope |
| "Who stops this at 2am, and with what — a deploy, a click, or an abort?" | The metadata kill-switch stops the chain at the next hand-off; only `System.abortJob` stops a job already running (`apexdev` L17230). A chain with neither is unstoppable without a deployment | The `Chain_Step__mdt` record set, and the runbook line naming which lever fits which symptom |
| "What has to travel between links, and how big does it get?" | `Database.Stateful` is per-job, not per-chain (gotcha 6) — and a Stateful collection that grows per scope is re-serialized before every remaining chunk (gotcha 5) | Constructor parameters for scalars, a named staging sObject for anything record-level |
| "How many total async executions will one full run of this chain cost?" | Roughly Σ(rows ÷ scope + 2) per link against a cap shared by all async Apex, and the check is pre-emptive: *"The batch won't start unless there is sufficient capacity for the entire job available"* (`apexdev` L17694–17697) | A number to compare against the org's 250,000-or-licences×200 headroom before the design is committed |
| "Does any link need to fan out to more than one downstream job?" | It cannot. An async transaction may enqueue exactly one job (`apexdev` L16175–16177), and the same rule binds Finalizers and Queueable children | A coordinator link, or a Platform Event with independent subscribers, decided before the code is written |
| "Is any link's failure transient, and how many retries do we actually want?" | The platform permits five consecutive Finalizer re-enqueues (`apexdev` L16292–16295). Taking all five on a deterministic failure burns five async executions and still fails | An exception-type allowlist and a retry ceiling below the platform's, plus the `AsyncOptions.DuplicateSignature` that stops a double-retry |
| "How will anyone prove tomorrow that all three links ran?" | No platform field records chain lineage — `AsyncApexJob.ParentJobId` is internal `BatchApexWorker` linkage (gotcha 9) | A correlation Id carried through the constructors, and the `AsyncApexJob` query the on-call runbook will actually paste |

What a proper configuration adds over just calling `executeBatch` from `finish()`: the chain has one place that decides to advance, so the kill-switch, the capacity check and the error gate exist once rather than N times; a broken link leaves a durable record instead of a `Completed` job and a stale table; and the test suite asserts the hand-off deterministically rather than depending on how many levels `Test.stopTest()` happens to drive.

---

## Core Concepts

### finish() as the Chain Trigger

Every Batch Apex class implements three interface methods: `start()`, `execute()`, and `finish()`. The `finish(Database.BatchableContext bc)` method is called exactly once after all `execute()` scope chunks complete. Calling `Database.executeBatch(new NextBatch())` inside `finish()` is the standard, platform-supported mechanism for chaining. The returned `Id` is the `AsyncApexJob` Id of the newly enqueued job — capture it if you need to monitor downstream status.

Chaining from `finish()` is synchronous from the perspective of your code but fully asynchronous from the platform's perspective. The new job enters the **Flex Queue** and waits for an execution slot.

### The Flex Queue and the 5-Concurrent-Job Ceiling

Two ceilings, counted separately. Up to **5** batch jobs queued or active concurrently, and up to **100 Holding** jobs in the Apex flex queue behind them (`apexdev` L17686–17687) — the flex queue is *"limited to 100 additional jobs"* (L15939–15940), so the practical in-flight ceiling is 105.

A full flex queue is **not silent**: *"If the Apex flex queue has the maximum number of 100 jobs, Database.executeBatch throws a LimitException and doesn't add the job to the queue"* (`apexdev` L17238–17239). What makes it *look* silent is the second-order effect — an unhandled exception in `finish()` *"prevents the next job from being enqueued and breaks the sequence"* (L17823–17825) while the throwing job still reports `Completed`. So the fix is a try/catch around every hand-off, not just a pre-flight count.

There is no read API for the queue. `System.FlexQueue` exposes exactly four methods — `moveAfterJob`, `moveBeforeJob`, `moveJobToEnd`, `moveJobToFront` (`apexrefguide` L215739–215762) — all of them reordering. Depth is read with SOQL on `AsyncApexJob`, grouped by `Status` so each count meets its own ceiling.

```apex
// Reorder, don't poll: push a starved chain link to the front of the holding queue
Boolean moved = System.FlexQueue.moveJobToFront(highPriorityJobId);
```

### Queueable as an Unlimited-Depth Alternative

A Queueable class can enqueue a new Queueable from inside its own `execute()` method — this is the standard recursive Queueable pattern. Exactly **one** child per parent: *"Only one child job can exist for each parent queueable job. Starting multiple child jobs from the same queueable job isn't supported"* (`apexdev` L16187–16189). Total depth is unbounded in production — *"Because no limit is enforced on the depth of chained jobs, you can chain one job to another"* — but capped in the orgs you develop in: *"For Developer Edition and Trial organizations, the maximum stack depth for chained jobs is 5, which means that you can chain jobs four times"* (L16182–16186). A runaway chain therefore stops itself in your sandbox and does not stop itself in production. Set the bound explicitly with `AsyncOptions.MaximumQueueableStackDepth` and read it back with `AsyncInfo.getCurrentQueueableStackDepth()` (L16044–16062).

Queueable chains are preferred when:
- The number of chain steps is not known at design time.
- You need to pass complex typed state between steps (Queueable constructors accept any serializable type).
- Each step must conditionally decide whether to enqueue the next step.

Queueable chains have their own governor context per `execute()` invocation, just like batch. The trade-off is that Queueable does not chunk records the way Batch does — if a step processes large data sets you still need a batch class for that step, with a Queueable acting only as the coordinator.

### Test Limitations

Three bounds, all grounded, make an end-to-end chain test impossible regardless of how many levels the platform drives:

- *"When testing your batch Apex, you can test only one execution of the execute method"* (`apexdev` L17739–17740) — set `scope` to the seeded record count or the test covers one chunk of many.
- *"In a running test, you can submit a maximum of 5 batch jobs"* (L17683).
- *"Asynchronous calls, such as @future or executeBatch, called in a startTest, stopTest block, don't count against your limits"* (L17614–17615) — so a test can never reproduce a flex-queue or 24-hour-cap failure.

UNVERIFIED (2026-09-05): the commonly-cited rule that `Test.stopTest()` drives exactly **one** level of a chain is not stated in the extracted guides. They say only that *"The system executes all asynchronous processes started in a test method synchronously after the Test.stopTest statement"* (L16123–16125, L17604–17607), which is silent about a job started by another job's `finish()`; for Queueables the guide points the other way — *"You can test chained queueable jobs by using appropriate stack depths"* (L16166).

Design around the uncertainty instead of betting on it. Route every hand-off through one orchestrator that records the request and skips the start under `Test.isRunningTest()`, then assert on the recorded request. That assertion holds whatever the platform does. See `references/code-examples.md` § 7.

---

## Common Patterns

### Pattern 1: Two-Step Chain with Flex Queue Guard

**When to use:** You have exactly two batch jobs that must run in sequence and you want the simplest possible implementation.

**How it works:**

```apex
public class StepOneBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([SELECT Id FROM Account WHERE ...]);
    }

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        // process scope
    }

    public void finish(Database.BatchableContext bc) {
        // Early warning: Holding is measured against 100 (apexdev L17687)
        Integer holding = [
            SELECT COUNT() FROM AsyncApexJob
            WHERE JobType = 'BatchApex' AND Status = 'Holding'
        ];
        if (holding >= 95) {
            ApplicationLogger.error('StepOneBatch',
                'Flex queue Holding at ' + holding + '/100. StepTwoBatch not started.');
            ApplicationLogger.flush();
            return;
        }
        // The count narrows the window; the try/catch is what actually protects
        // the chain, because a full queue THROWS (apexdev L17238-17239) and an
        // unhandled throw in finish() breaks the sequence (L17823-17825).
        try {
            Id next = Database.executeBatch(new StepTwoBatch(), 200);
            ApplicationLogger.info('StepOneBatch', 'StepTwoBatch started as ' + next);
        } catch (Exception e) {
            ApplicationLogger.error('StepOneBatch', e);
        } finally {
            ApplicationLogger.flush();
        }
    }
}
```

**Why the count is not enough on its own:** the queue *"sometimes exceeds the maximum limit, resulting from parallel requests to enqueue batch Apex jobs"* (`apexdev` L17251–17253), so another transaction can fill it between the count and the call. The count buys the on-call team warning; the try/catch is what keeps the failure from disappearing into a `Completed` job.

### Pattern 2: Queueable Coordinator for Multi-Step Chains

**When to use:** Three or more steps, or when each step must decide conditionally whether to proceed.

**How it works:**

```apex
public class BatchChainCoordinator implements Queueable {
    private Integer step;
    private Id contextId; // pass state between steps

    public BatchChainCoordinator(Integer step, Id contextId) {
        this.step = step;
        this.contextId = contextId;
    }

    public void execute(QueueableContext ctx) {
        if (step == 1) {
            Database.executeBatch(new StepOneBatch(contextId), 200);
        } else if (step == 2) {
            Database.executeBatch(new StepTwoBatch(contextId), 200);
        } else if (step == 3) {
            Database.executeBatch(new StepThreeBatch(contextId), 200);
        }
        // Queueable does NOT chain itself here — the batch finish() calls:
        // System.enqueueJob(new BatchChainCoordinator(step + 1, contextId));
    }
}
```

Each batch's `finish()` method calls:

```apex
public void finish(Database.BatchableContext bc) {
    System.enqueueJob(new BatchChainCoordinator(2, this.contextId));
}
```

**Why this works better than pure batch-to-batch chaining:** The coordinator owns all routing logic in one place. Adding a step means editing one class, not modifying every batch's `finish()`. Conditional skipping (e.g., skip step 3 if no records were processed) is easy to add.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Two sequential batch jobs, simple state passing via constructor | Direct `finish()` chain with Flex Queue guard | Simplest; no extra class needed |
| Three or more sequential batch jobs | Queueable coordinator + batch `finish()` → `enqueueJob()` | Centralizes routing; avoids modifying every finish() when chain grows |
| Chain steps unknown at design time (dynamic depth) | Queueable chain — each step decides whether to enqueue next | Only Queueable supports fully open-ended depth without design-time limit |
| Need to pass complex typed objects between steps | Queueable constructor parameters | Batch constructor accepts typed args but Queueable makes this the primary state-passing mechanism |
| Next link may find no work (poll-until-done, off-peak) | `System.scheduleBatch(job, name, minutesFromNow)` from `finish()` | The guide's own recommendation — the delay *"optimizes the usage of available batch jobs and the flex queue by preventing jobs that don't have any work from repeatedly starting"* (`apexdev` L17831–17835). Minimum 1 minute; costs a scheduled-Apex slot until the job queues |
| A link must fan out to two or more downstream jobs | One coordinator link, or a Platform Event with independent subscribers | An async transaction may enqueue exactly one job (`apexdev` L16175–16177) — fan-out from `finish()` is not possible |
| Record-level failure detail must survive the chain | `Database.RaisesPlatformEvents` + a `BatchApexErrorEvent` trigger | The only signal for uncatchable failures: *"Events are also fired for … uncatchable Apex exceptions such as LimitExceptions"* (`apexdev` L17845–17847) |
| Chain must survive test coverage requirements with full path coverage | Orchestrator with a `Test.isRunningTest()` seam, one test per link | A test may submit 5 batch jobs and exercise one `execute()` (`apexdev` L17683, L17739–17740); asserting on a recorded hand-off request is deterministic, asserting on a downstream job's data effects is not |

---

## Recommended Workflow

1. **Confirm chaining, and confirm the shape.** Read `standards/decision-trees/async-selection.md` — Q7 ("Does downstream work need to resume even if the main job fails?" → Finalizer) and Q8 (scope size, "max 2,000 when start() returns a QueryLocator"). A single large dataset is `apex/batch-apex-patterns`, not this skill. Answer the seven **Questions to Ask** above and record the answers; the enqueue budget (one job per async transaction) and the retry ceiling are design constraints, not implementation details.

2. **Budget the chain before writing it.** Estimate Σ(rows ÷ scope + 2) executions per link against the org's 24-hour async headroom. The check is pre-emptive and all-or-nothing — *"The batch won't start unless there is sufficient capacity for the entire job available"* (`apexdev` L17694–17697). Run the flex-queue and headroom queries in `references/code-examples.md` § 11 against the target org.

3. **Build the orchestrator first, then the links.** Copy `references/code-examples.md` §§ 2–5: `ChainOrchestrator` (kill-switch read, upstream-error gate, scope clamp, `Test.isRunningTest()` seam), then each Batchable and the terminal Queueable + Finalizer. Log through `templates/apex/ApplicationLogger.cls`; never re-implement a logger. Every `finish()` calls the orchestrator and nothing else.

4. **Wire failure capture.** Declare `Database.RaisesPlatformEvents` on every Batchable link and deploy the `BatchApexErrorEvent` trigger from § 6 — it is the only channel that reports uncatchable failures. Subscriber design beyond this chain's needs belongs to `apex/platform-events-apex`.

5. **Write the tests against the seam, not the chain.** Use `ChainOrchestratorTest` (§ 7) as the shape: assert the recorded `ChainRequest` names the next link, assert no downstream `AsyncApexJob` row exists, and set `scope` to the seeded record count so the single testable `execute()` covers all of it. Seed with `templates/apex/tests/TestDataFactory.cls`; follow the ≥200-record shape in `templates/apex/tests/BulkTestPattern.cls`.

6. **Run the checker over the source tree** before deploying:
   `python3 skills/apex/apex-batch-chaining/scripts/check_apex_batch_chaining.py --manifest-dir force-app --strict`
   C001 (executeBatch in `execute()`), C006 (async outside `startTest`) and C010 (illegal scope literal) are ERRORs; C002, C004, C007, C008 and C009 are WARNs that `--strict` promotes; C003 and C005 are advisories a human adjudicates.

7. **Deploy switched off, then flip the switch.** Follow the deploy order in § 10 — `Chain_Step__mdt` records land with `Enabled__c = false`, so go-live is a metadata edit and rollback is the same edit reversed. Then run the review checklist below and paste § 11's verification query into the runbook.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every hand-off in `finish()` is inside a try/catch — `finish()` cannot throw, or the chain ends while the job reports `Completed`
- [ ] Capacity is read as two counts (Holding vs. queued/active), each against its own ceiling, with `JobType` filtered so `BatchApexWorker` rows do not inflate it
- [ ] Exactly one `System.enqueueJob` on any path through a `finish()`, a Finalizer, or a Queueable `execute()`
- [ ] State passed between chained jobs uses constructor parameters or a staging sObject — never `Database.Stateful`, and no `Stateful` collection that grows per scope
- [ ] Every link reads a kill-switch before advancing, and the runbook names `System.abortJob` for a job already running
- [ ] There is a terminal condition — step counter, zero-row query, or the kill-switch — so the chain cannot recurse indefinitely
- [ ] Every Batchable link declares `Database.RaisesPlatformEvents`, and a `BatchApexErrorEvent` subscriber persists the failure
- [ ] The Finalizer's retry ceiling is set by you and is below the platform's five, and is gated on an exception-type allowlist
- [ ] Tests assert on the recorded hand-off request, not on a downstream job's data effects; `scope` equals the seeded record count
- [ ] `check_apex_batch_chaining.py --strict` is clean, or each remaining finding is adjudicated in writing
- [ ] A correlation Id (constructor parameter or `ApplicationLogger.Request_Id__c`) makes the chain reconstructable — `ParentJobId` will not do it

---

## Salesforce-Specific Gotchas

The full set with line cites is in `references/gotchas.md` (12 gotchas). The three that break chains most often:

1. **A full flex queue throws — it does not queue silently.** `Database.executeBatch` throws a `LimitException` at 100 Holding jobs (`apexdev` L17238–17239). Because the throw lands in `finish()`, the sequence breaks while the job reports `Completed` — which is why it is so often misread as silent.
2. **`System.FlexQueue.getJobIds()` does not exist.** The class has four methods, all reordering (`apexrefguide` L215739–215762). Read depth with SOQL.
3. **`AsyncApexJob.ParentJobId` is not the chain link.** It records internal `BatchApexWorker` lineage, not "the job that started me" (Object Reference, `AsyncApexJob`). Nothing on the platform records chain lineage — carry your own correlation Id.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `ChainOrchestrator.cls` | The one class that decides to advance: kill-switch read, upstream-error gate, scope clamp, `Test.isRunningTest()` seam |
| Batchable links (`.cls` + `-meta.xml`) | `Database.Batchable` + `Database.Stateful` (counters only) + `Database.RaisesPlatformEvents`, each `finish()` delegating to the orchestrator |
| Terminal Queueable + Finalizer | `Queueable, Database.AllowsCallouts, Finalizer` with a bounded retry, `AsyncOptions` stack depth and `DuplicateSignature` |
| `Chain_Step__mdt` type + records | The kill-switch and per-link scope size; deployed with `Enabled__c = false` |
| `MarkChainFailure.trigger` | `BatchApexErrorEvent` subscriber that marks the failed scope and logs which link died |
| Test class | One test per link, asserting the recorded hand-off request and the absence of a downstream job row |
| `package.xml` + deploy order | Six ordered steps, ending in the metadata edit that switches the chain on |
| Verification SOQL | Ordered `AsyncApexJob` read, split capacity counts, and the watchdog query the guide prescribes |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are writing the classes — the full three-link pipeline, `Chain_Step__mdt`, the `BatchApexErrorEvent` trigger, the test class, `-meta.xml`, `package.xml`, deploy order and verification SOQL |
| `references/gotchas.md` | A chain stopped halfway, a guard did not compile, or a monitoring query returned nonsense — 12 grounded platform behaviours |
| `references/examples.md` | You want the narrative walk-through of the two-step and coordinator scenarios, plus the diagnostic sequence for a chain that reported success |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated chaining code, or self-checking your own output — 8 patterns with detection hints |
| `references/well-architected.md` | You are justifying the orchestrator over N scattered `finish()` methods, or need the source list with the claim each supports |

---

## Related Skills

- `apex/batch-apex-patterns` — scope sizing, `Database.Stateful`, `QueryLocator` vs `Iterable`, and single-job batch design; read this first before chaining
- `apex/apex-queueable-patterns` — Queueable interface, `System.enqueueJob`, and child-job limits; used when building the Queueable coordinator
- `apex/apex-transaction-finalizers` — owns Finalizer design, retry ceilings and `FinalizerContext`; this skill only uses a Finalizer as the last link
- `apex/async-apex` — high-level comparison of all async mechanisms; useful for initial technology selection
- `apex/platform-events-apex` — owns `__e` subscriber design; read it before extending the `BatchApexErrorEvent` trigger beyond this chain
- `apex/debug-and-logging` — owns the logging framework this package logs through
