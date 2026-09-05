# Well-Architected Notes — Apex Batch Chaining

## Relevant Pillars

- **Reliability** — The chain's weakest link is `finish()`, not `execute()`. An
  unhandled exception there *"prevents the next job from being enqueued and
  breaks the sequence"* while the job itself still reports `Completed`. A
  reliable chain wraps every hand-off in try/catch, declares
  `Database.RaisesPlatformEvents` so uncatchable failures surface as
  `BatchApexErrorEvent`, and runs the guide's own scheduled watchdog to restart
  an interrupted sequence.
- **Performance Efficiency** — Scope size decides how long each link holds one of
  the five concurrent slots. The platform caps scope at 2,000 for a
  `QueryLocator` start and recommends factors of 2000. A chain of many
  small-scope jobs is not just slow; each `start`/`execute`/`finish` counts
  against the shared 24-hour async cap, so over-chunking a chain can make the
  whole org's async budget the binding constraint.
- **Operational Excellence** — There is no platform field linking link A to link
  B, so a chain is only observable if it makes itself observable: a correlation
  Id carried through constructors, `AsyncApexJob` Ids logged at each hand-off,
  and a kill-switch a human can flip without a deployment.

## Architectural Tradeoffs

**Simplicity vs. Maintainability:**
A direct `finish()` chain (Job A calls `Database.executeBatch(new JobB())`) is
the simplest possible implementation and has no extra classes. The cost is that
routing, the capacity guard, the kill-switch read and the test seam are
duplicated in every `finish()`. A single orchestrator costs one class and makes
those four concerns editable in one place — and gives the test suite one seam to
assert against instead of N.

**Batch Chunking vs. Queueable Flexibility:**
Batch Apex chunks records, resets governor limits per `execute()`, and can return
up to 50 million rows from a `QueryLocator`. Queueable runs one execution context
with no chunking, but chains without an enforced depth limit and accepts typed
constructor state. Use Batch for the links that process volume; use Queueable for
the coordination, notification and callout links between them. The guide's own
framing: *"Use chained batch jobs if you require sequential execution and batch
processing… Otherwise, if batch processing isn't needed, consider using Queueable
Apex."*

**Immediate vs. Delayed Hand-Off:**
`Database.executeBatch` starts the next link as soon as a slot frees.
`System.scheduleBatch` inserts at least a minute and consumes a scheduled-Apex
slot until the job queues. The delay is not waste when the next link may find no
work — the guide recommends it precisely to stop empty jobs from cycling through
the flex queue. Choose per link, and record the reason.

**Constructor State vs. Persisted State:**
Constructor parameters are clean and synchronous but bounded by what serializes.
`Database.Stateful` is the wrong tool for cross-link state — it is per-job — and
becomes a heap risk when the retained member is a collection that grows per
scope. For anything record-level, write to a staging sObject in `execute()` and
let the next link's `start()` query it: one DML/SOQL pair, and the state survives
a broken chain.

**Retry Depth vs. Wasted Executions:**
A Finalizer may re-enqueue a failed Queueable five consecutive times. Taking all
five is usually wrong: a deterministic failure consumes five async executions and
still fails. Bound retries at one or two, gate them on an exception-type
allowlist, and route everything else to a durable failure record.

## Anti-Patterns

1. **Unguarded hand-off in `finish()`** — no try/catch, so a `LimitException`
   from a full flex queue or a `System.AsyncException` from a lock failure ends
   the chain while the job reports `Completed`.
2. **One combined capacity count** — comparing `Holding + Queued + Preparing +
   Processing` to 100. The 100 is the Holding cap; the 5 is the concurrent cap;
   they are separate ceilings and an unfiltered count also includes internal
   `BatchApexWorker` rows.
3. **Testing the full chain in one test method** — treating `Test.stopTest()` as
   an end-to-end chain runner, in a context that permits one `execute()` and five
   batch submissions. Assert on a recorded hand-off request instead.
4. **No terminal condition on a recursive chain** — batch-to-batch chaining has
   no platform depth limit, so the stop is the 24-hour async cap, and that cap
   refuses the whole job rather than degrading.
5. **Two enqueues in one async transaction** — a `finish()`, Finalizer, or
   Queueable `execute()` may start exactly one job. Fan-out needs a coordinator
   or a Platform Event.
6. **`ParentJobId` as chain lineage** — it is internal `BatchApexWorker` linkage.
   Chains must carry their own correlation Id.
7. **A `Database.Stateful` collection that grows per scope** — re-serialized
   before every remaining chunk; fails late, in production, on volume.

## Official Sources Used

- Apex Developer Guide v67.0 (Summer '26), *Chaining Batch Jobs* — L17810–17841:
  chaining supported from API 26.0; `Database.executeBatch` **or**
  `System.scheduleBatch` from `finish`; an unhandled exception in `finish` breaks
  the sequence; the scheduled watchdog that restarts an interrupted chain; the
  API version that counts is the running batch class's, not the helper's.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide v67.0, *Holding Batch Jobs in the Apex Flex Queue* —
  L17234–17268: 100-job flex queue; `Database.executeBatch` throws a
  `LimitException` when it is full; the queue can transiently exceed its maximum;
  five queued-or-active jobs processed simultaneously; `FlexQueue.moveBeforeJob`
  reordering. (Supports gotchas 1 and 3.)
- Apex Developer Guide v67.0, *Batch Apex Limitations / Considerations and Best
  Practices* — L17683–17760: 5 concurrent, 100 Holding, 5 batch jobs per test,
  one `execute()` testable, 250,000 shared 24-hour async cap with the pre-emptive
  capacity check, 50-million-row `QueryLocator`, scope max 2,000 and factors of
  2000, 100 callouts per method, filter `BatchApexWorker` out of `AsyncApexJob`
  queries, extreme caution invoking a batch from a trigger. (Supports gotchas 3,
  8, 9, 11 and the checker's scope and trigger rules.)
- Apex Developer Guide v67.0, *Queueable Apex Limits*, *Chaining Jobs*,
  *Detecting Duplicate Queueable Jobs*, *Adding a Queueable Job with a Specified
  Stack Depth / Minimum Delay* — L16000–16280: one child job per parent, one
  enqueue per async transaction, `Limits.getQueueableJobs()`, no enforced chain
  depth except 5 in Developer/Trial, `AsyncOptions.MaximumQueueableStackDepth`,
  `MinimumQueueableDelayInMinutes` (0–10), `QueueableDuplicateSignature` and
  `DuplicateMessageException`. (Supports gotchas 7 and 12, and the Queueable link
  in `references/code-examples.md` § 5.)
- Apex Developer Guide v67.0, *Transaction Finalizers* — L16284–16535:
  `System.Finalizer`, the four `FinalizerContext` methods,
  `System.attachFinalizer`, separate Apex and database transactions, one
  finalizer per job, one async job enqueued per finalizer, five consecutive
  re-enqueues with the counter reset on success, and the caveat that an
  unexpectedly terminated request can skip the finalizer entirely. (Supports the
  Finalizer retry link and the retry-depth tradeoff above.)
- Apex Developer Guide v67.0, *Firing Platform Events from Batch Apex* and
  *Testing BatchApexErrorEvent Messages* — L17843–17925:
  `Database.RaisesPlatformEvents`, `BatchApexErrorEvent` available in API 44.0+,
  events fired for uncatchable exceptions including `LimitException`, the
  `AsyncApexJobId`/`JobScope`/`ExceptionType` sample trigger, and
  `Test.getEventBus().deliver()` after `Test.stopTest()`. (Supports
  `references/code-examples.md` § 6 and gotcha 10.)
- Apex Reference Guide v67.0, *Database.executeBatch*, *System.scheduleBatch*,
  *FlexQueue Class*, *Test.enqueueBatchJobs / getFlexQueueOrder* —
  L207000–207075, L215698–215800, L239887–239930, L240442–240470: the scope
  parameter's 2,000 ceiling and the iterable exemption; the versioned behaviour
  change at API 52.0 (`System.AsyncException` vs. the `000000000000000` return);
  the four and only four `FlexQueue` methods; `minutesFromNow` must exceed zero;
  the scheduled-Apex slot released once the job queues; `System.abortJob` on the
  returned CronTrigger Id. (Supports gotchas 1, 2 and 4.)
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apexref.pdf
- Object Reference for Salesforce v67.0, *AsyncApexJob* — L42262–42460: the
  `JobType` picklist values (including `BatchApex` and `BatchApexWorker`),
  `NumberOfErrors` as "batches with a failure", `ExtendedStatus` as the first
  error's description, `JobItemsProcessed`/`TotalJobItems`, and the `ParentJobId`
  description that scopes it to internal worker lineage. (Supports gotcha 9 and
  the verification queries.)
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- `standards/decision-trees/async-selection.md` Q7 and Q8 — the branch that lands
  on a Finalizer for resumable downstream work, and the scope-size branch this
  package's `clampScope` implements.
- Salesforce Well-Architected — Overview:
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
  (pillar framing for Reliability / Performance Efficiency / Operational
  Excellence above).
