---
name: long-running-process-orchestration
description: "Use when designing or reviewing multi-step Apex orchestration that spans multiple transactions, checkpoints state across async boundaries, or recovers from partial failure in a long-running workflow. Trigger keywords: 'multi-step Queueable chain', 'cross-transaction state', 'platform event state machine', 'Finalizer retry', 'orchestrate across transactions', 'workflow progress tracking'. NOT for single-job Queueable design (use apex-queueable-patterns), NOT for Flow Orchestration (use flow/orchestration-flows), NOT for bulk record processing where Batch Apex is the primary tool (use batch-apex-patterns)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
tags:
  - queueable
  - finalizer
  - platform-events
  - async-apex
  - orchestration
  - state-machine
  - cross-transaction
inputs:
  - "Description of the multi-step process and its steps, dependencies, and failure modes"
  - "Whether steps require callouts, DML, or external triggers to advance"
  - "Operational requirements: retry behavior, progress visibility, partial failure handling"
  - "Expected data volume per step (determines whether chaining or Batch is more appropriate)"
outputs:
  - "Orchestration pattern recommendation (Queueable chain vs Platform Event state machine vs hybrid)"
  - "Apex class scaffold with state-passing, Finalizer, and progress tracking"
  - "Review findings for existing multi-step async implementations"
  - "Decision guidance on checkpointing, retry depth, and step boundaries"
triggers:
  - how do I chain Queueable jobs across multiple transactions
  - Apex process needs to run across multiple transactions with state checkpointing
  - platform event state machine for long-running workflow
  - Finalizer interface retry pattern for Queueable failure recovery
  - track progress of a multi-step async Apex orchestration
dependencies:
  - apex/apex-queueable-patterns
  - apex/platform-events-apex
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Long-Running Process Orchestration

Use this skill when a business process must span multiple Apex transactions, cannot complete within a single execution context, and requires state preservation, progress tracking, and recovery from partial failure. The skill covers Queueable chaining with bounded depth, Platform Event state machines, Finalizer-based recovery, and Continuation for async UI callouts.

---

## Before Starting

Gather this context before working on anything in this domain:

- How many discrete steps does the process have, and are they sequential, parallel, or conditional?
- Can each step complete within a single Apex transaction (60 000 ms CPU, 100 SOQL, 150 DML)? If any step may exceed those limits, it needs its own Queueable or Batch boundary.
- Which steps involve callouts? Callout steps require `Database.AllowsCallouts` on their Queueable class.
- Where does progress need to be visible — operations dashboard, record field, email notification? This shapes the checkpoint mechanism.
- What is the correct recovery behavior when step N fails? Should the whole process abort, retry step N, or skip to a compensating action?
- Is the process already partially implemented in Flow Orchestration? If so, the Apex role may be limited to a single-step callout or heavy data operation delegated from Flow.

---

## Core Concepts

### Why Single Transactions Are Insufficient

Salesforce imposes hard transaction limits per execution context: 60 000 ms CPU, 100 SOQL queries, 150 DML statements, 12 MB heap, and a 10-second total callout timeout. A process that must send 20 batched callouts, process thousands of records in sequential dependency steps, or wait for external system responses cannot fit in one transaction. Multi-step orchestration is the platform-endorsed pattern for these cases: each step runs in its own transaction with a full allocation of governor limits, and state advances through controlled async handoffs.

### Queueable Chaining As A Step Sequencer

The most direct Apex orchestration mechanism is chaining Queueable jobs. Each Queueable's `execute()` method does its work and enqueues the next job in the sequence, passing forward a state object through the constructor. Key constraints that shape this pattern:

- Only one child Queueable may be enqueued per `execute()` call (Apex Developer Guide — Queueable Apex).
- `AsyncOptions.MaximumQueueableStackDepth` caps the chain length. The platform enforces a maximum of 5 levels in async contexts; in synchronous test contexts the default is 1. Every `System.enqueueJob()` call in the chain must re-pass `AsyncOptions` — it does not propagate automatically.
- `System.AsyncInfo.getCurrentQueueableStackDepth()` returns the current chain depth so logic can decide whether to continue or hand off.
- Fan-out (one step spawning multiple parallel children) is not supported through chaining alone. Use Platform Events or Batch Apex for fan-out.

### The Finalizer Interface For Cross-Step Recovery

The `System.Finalizer` interface runs in a guaranteed separate transaction after its parent Queueable completes — regardless of whether the parent succeeded or threw an uncaught exception. This is the only safe mechanism for:

- Advancing the orchestration state on failure (compensating transaction)
- Retrying a failed step up to a bounded count
- Recording a dead-letter entry when retries are exhausted
- Triggering downstream notification or monitoring

The `FinalizerContext` provides `getResult()` (SUCCESS or UNHANDLED_EXCEPTION), `getException()`, and `getJobId()`. A Finalizer may enqueue one additional Queueable. `System.attachFinalizer()` must be called early in the parent's `execute()` before any code that could throw (Apex Developer Guide — Transaction Finalizers).

### Platform Event State Machine

When a process needs to cross system boundaries, tolerate external latency, or decouple step producers from step consumers, a Platform Event state machine is more flexible than direct Queueable chaining. The pattern:

1. Each step completion publishes a `StepCompleted__e` (or domain-specific) Platform Event with the next-step identifier and carry-forward state as payload fields.
2. An Apex `after insert` trigger on that event type reads the next-step field and dispatches a Queueable for the next step.
3. Progress and replay position are tracked on a Custom Object record (the "process instance"), which also serves as the operational dashboard.

Platform Events decouple publish time from subscribe time, survive transaction rollbacks (events published in a rolled-back DML transaction are still delivered — this is a feature, not a bug), and allow external systems to participate as steps in the process (Platform Events Developer Guide).

### Progress Tracking And Observability

A long-running process is operationally incomplete without a way to observe where each instance is and why it stopped. Checkpoint patterns:

- **Custom Object record** per process instance: `Status__c`, `CurrentStep__c`, `StepStartedAt__c`, `ErrorMessage__c`, `RetryCount__c`. Updated at the start and end of each step.
- **Platform Event broadcast** for real-time dashboards or monitoring triggers.
- **AsyncApexJob** records are queryable by job ID for built-in Queueable status.

Step start/end timestamps enable latency monitoring per step, which surfaces performance regressions before they cause timeouts.

### Continuation For Long-Running LWC Callouts

When the long-running operation is a callout initiated from Lightning UI, the `Continuation` class provides an async callout mechanism that does not block the user session. The controller initiates the callout by returning a `Continuation` object; Salesforce processes the callout asynchronously (up to 120 seconds) and invokes a callback method with the response. This is distinct from Queueable: Continuation is UI-initiated, synchronous from the user's perspective, and limited to callout contexts in LWC/Aura/Visualforce controllers (Apex Developer Guide — Continuation).

---

## Common Patterns

### Bounded Queueable Chain With State Object

**When to use:** A sequential process of 3–10 steps where each step is a distinct DML or callout operation, steps are ordered and have no parallelism, and the total chain depth fits within platform limits.

**How it works:**
1. Define a serializable `ProcessState` inner class or standalone class carrying: `currentStep` (integer or enum), `recordId`, `retryCount`, and any payload fields needed by subsequent steps.
2. Each Queueable receives a `ProcessState` instance, executes its step, updates the Custom Object checkpoint record, then evaluates whether to chain:

```apex
public class StepOneQueueable implements Queueable {
    private final ProcessState state;

    public StepOneQueueable(ProcessState state) {
        this.state = state;
    }

    public void execute(QueueableContext ctx) {
        System.attachFinalizer(new StepFinalizer(state));

        // Do step work
        doStepOneWork(state.recordId);

        // Update checkpoint
        updateCheckpoint(state.recordId, 'StepOne', 'Complete');

        // Chain to next step
        state.currentStep = 2;
        AsyncOptions opts = new AsyncOptions();
        opts.MaximumQueueableStackDepth = 5;
        System.enqueueJob(new StepTwoQueueable(state), opts);
    }
}
```

3. The Finalizer handles failure — it increments `retryCount` on the state object and re-enqueues the same step if retries remain, or marks the process instance as failed.

**Why not the alternative:** Placing all steps in a single Queueable with a `switch` statement runs the risk of hitting governor limits mid-step with no safe boundary. Separate Queueables give each step its own full transaction allocation.

### Platform Event State Machine With Process Instance Record

**When to use:** The process involves external system responses between steps, steps may run minutes or hours apart, or you need strict decoupling between step producers and consumers.

**How it works:**
1. Create a Process Instance Custom Object (`OrchestrationRun__c`) with fields: `Status__c` (picklist: Pending/Running/Complete/Failed), `CurrentStep__c` (text), `RetryCount__c`, `LastError__c`.
2. When launching the process, insert the record with `Status__c = 'Running'` and `CurrentStep__c = 'StepOne'`, then publish a `StepAdvance__e` platform event with `RunId__c = record.Id` and `Step__c = 'StepOne'`.
3. The platform event trigger reads `Step__c` and enqueues the appropriate Queueable:

```apex
trigger StepAdvanceTrigger on StepAdvance__e (after insert) {
    for (StepAdvance__e evt : Trigger.new) {
        if (evt.Step__c == 'StepOne') {
            System.enqueueJob(new StepOneWorker(evt.RunId__c));
        } else if (evt.Step__c == 'StepTwo') {
            System.enqueueJob(new StepTwoWorker(evt.RunId__c));
        }
        // Additional steps...
    }
}
```

4. At the end of each worker, it updates `OrchestrationRun__c` and publishes the next `StepAdvance__e`.
5. On failure, the Finalizer updates `Status__c = 'Failed'` and `LastError__c`.

**Why not the alternative:** Queueable chaining alone cannot resume after an external system delay of hours without consuming a Queueable slot waiting for the response. Platform Events decouple the step trigger from the response and survive org restarts.

### Hybrid: Queueable Chain Within Steps, Platform Events Between Phases

**When to use:** The orchestration has distinct phases (e.g., Validation, Processing, Notification) where each phase consists of sequential sub-steps, and phases are separated by external events or significant time gaps.

**How it works:** Use a Queueable chain for the sub-steps within a phase; use a Platform Event to signal phase completion and trigger the next phase. The Custom Object record tracks both phase and sub-step. This hybrid keeps chain depth low per phase while maintaining decoupled phase transitions.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| 3–7 sequential steps, no external waits, completes in minutes | Bounded Queueable chain | Simpler, no event infrastructure needed |
| Steps separated by external system responses or human actions | Platform Event state machine | Decouples step timing from Apex transaction lifecycle |
| Fan-out required (one step spawns N parallel workers) | Platform Events or Batch | Queueable allows only one child per execution |
| Step failure should auto-retry up to N times | Finalizer-based retry | Only mechanism that handles all failure modes including system-level exceptions |
| Process is UI-initiated and involves a long callout | Continuation | Designed for async LWC/Aura callouts up to 120s |
| Step volume exceeds Queueable chain depth limits | Batch Apex for heavy step, Queueable to orchestrate transitions | Batch handles large data volume; Queueable manages step transitions |
| Operations team needs live process visibility | Custom Object checkpoint + Platform Event broadcast | Enables query-based dashboards and external monitoring |
| Process has 10+ steps or irregular branching | Platform Event state machine with dispatch table | Cleaner than deeply nested Queueable chain logic |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Gather context** — identify all steps, their sequencing rules, governor-limit risks per step, callout needs, and failure recovery expectations. Confirm whether the process is purely Apex or has external participants.
2. **Choose the primary pattern** — use the Decision Guidance table above. For simple sequential processes, start with Queueable chaining; for externally-triggered or time-separated steps, use the Platform Event state machine.
3. **Design the state model** — define the Custom Object (or state class) that will carry process instance data across transactions. Include step identifier, retry count, timestamps, and error message fields.
4. **Implement step boundaries** — each step should be a separate Queueable class. Attach a Finalizer in every Queueable that has side effects. Pass state only through constructor fields — not static variables.
5. **Implement the checkpoint mechanism** — update the Custom Object record at the start and end of each step. Publish a progress Platform Event if real-time dashboards are required.
6. **Validate** — run the checker script, verify governor limit exposure per step in test scenarios, confirm Finalizer coverage, and ensure chain depth respects `MaximumQueueableStackDepth`.
7. **Review against checklist** — confirm all items in the Review Checklist are satisfied before marking implementation complete.

---

## Review Checklist

- [ ] Each step is implemented as a separate Queueable with its own transaction boundary.
- [ ] `System.attachFinalizer()` is called at the start of every Queueable `execute()` method with side effects.
- [ ] `AsyncOptions.MaximumQueueableStackDepth` is set on every `System.enqueueJob()` call in a chain.
- [ ] `System.AsyncInfo.getCurrentQueueableStackDepth()` is used to guard against exceeding the cap.
- [ ] State is passed through serializable constructor fields — no static variables cross transaction boundaries.
- [ ] A Custom Object or equivalent checkpoint record tracks the current step, retry count, and error state.
- [ ] Finalizer retry logic increments a counter and aborts after a configurable maximum.
- [ ] Platform Event triggers are thin and delegate heavy work to Queueable workers.
- [ ] Callout Queueables implement `Database.AllowsCallouts`.
- [ ] Test classes use `Test.startTest()` / `Test.stopTest()` boundaries and verify the Custom Object checkpoint state.

---

## Salesforce-Specific Gotchas

1. **`MaximumQueueableStackDepth` does not propagate** — setting the option on the first `enqueueJob` call does not carry forward to child jobs. Every subsequent `enqueueJob` in the chain must re-set it explicitly, or the depth guard is silently absent on all jobs beyond the first.
2. **Platform Events published in a rolled-back DML transaction are still delivered** — this is by design. A Queueable that fails mid-transaction but already published a step-advance event will advance the state machine while leaving the DML changes rolled back, causing state inconsistency. Publish step-advance events only after confirming the DML in that step succeeded.
3. **Finalizer failures are silent unless monitored** — the Finalizer runs in a separate transaction with its own governor limits. If the Finalizer itself hits a limit or throws, it fails without surfacing to the original job's error context. Log from the Finalizer to a Custom Object or named credential endpoint so these failures are observable.
4. **`System.AsyncInfo.getCurrentQueueableStackDepth()` returns 0 in synchronous test context** — test methods that call Queueables synchronously via `Test.stopTest()` will always see a depth of 0, so depth-guard branches that skip enqueuing will never be exercised in unit tests. Add an explicit integration test or set a low `MaximumQueueableStackDepth` in test context to cover boundary logic.
5. **Continuation is LWC/Aura/VF only** — attempting to create a `Continuation` from a trigger, Queueable, Batch class, or `@AuraEnabled` method that is not a controller action throws a runtime exception. The async callout pattern for non-UI contexts is always Queueable with `Database.AllowsCallouts`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Orchestration pattern recommendation | Decision on Queueable chain vs Platform Event state machine vs hybrid, with rationale |
| State model design | Custom Object schema and state class fields required for this process |
| Step scaffold | Queueable class skeletons with Finalizer, state passing, and checkpoint update |
| Platform Event trigger dispatch table | Thin trigger routing step-advance events to the correct Queueable worker |
| Review findings | Assessment of an existing multi-step async implementation against the review checklist |

---

## Related Skills

- `apex/apex-queueable-patterns` — use for single-job Queueable design, Finalizer API details, and `AsyncOptions` reference.
- `apex/platform-events-apex` — use for Platform Event schema design, publish result handling, and CDC vs Platform Event selection.
- `apex/batch-apex-patterns` — use when individual steps involve large-volume record processing that exceeds Queueable limits.
- `apex/async-apex` — use when the question is whether Queueable, Batch, Future, or Scheduled is the right async mechanism.
- `apex/exception-handling` — use when the broader error handling framework and logging strategy are the primary concern.
- `apex/governor-limits` — use when steps are hitting specific limits that require redesign.
- `flow/orchestration-flows` — use when the orchestration can be entirely managed in Flow Orchestration without Apex.
