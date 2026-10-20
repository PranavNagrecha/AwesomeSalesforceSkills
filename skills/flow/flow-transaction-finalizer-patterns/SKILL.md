---
name: flow-transaction-finalizer-patterns
description: "Use when a Flow needs to do work that must survive the triggering transaction — post-commit notifications, callouts, audit rows, or compensating actions. Covers Flow Transaction Control element, scheduled paths, Platform Event + finalizer. NOT for general Flow async decisions (see async-selection) — use apex/apex-transaction-finalizers."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Scalability
triggers:
  - "flow post commit action"
  - "run flow logic after save"
  - "flow transaction control element"
  - "guaranteed post-commit step"
  - "flow callout after transaction"
tags:
  - flow
  - transaction
  - finalizer
  - reliability
  - post-commit
inputs:
  - Flow that currently does pre- or in-transaction work
  - Work that must happen post-commit (email, callout, event emit, compensating update)
  - Failure tolerance for the post-commit step
outputs:
  - Post-commit execution pattern (scheduled path, platform event, Apex Queueable finalizer)
  - Retry / durability story
  - Monitoring hook
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-19
---

# Flow Transaction Finalizer Patterns

## Purpose

Salesforce transactions are atomic: either every DML commits or none does.
But some work should only run AFTER commit — sending an email, firing a
webhook, writing an audit log to an external system, or issuing a
compensating action if a callout later fails. Getting this wrong produces
two common failures: "email sent but record rolled back," or "record saved
but downstream never notified." This skill codifies the patterns Flow
designers should use for reliable post-transaction behavior, and when to
escalate to Apex Queueable with a Finalizer.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Must this work run only if the record commits?" | Flow has no finalizer, and a fault path runs inside the transaction it guards (gotchas 1, 9) | The pattern choice: asynchronous path, platform event, or Queueable with Finalizer |
| "Is the flow before-save or after-save?" | The asynchronous path exists only on after-save flows (gotcha 3) | Whether Pattern A is available at all |
| "If a platform event carries it, what is the event's publish behaviour?" | Publish Immediately fires even when the transaction rolls back (gotcha 4) | Publish After Commit on the event definition |
| "Does the invocable Apex this flow calls enqueue its own async work?" | Otherwise it runs in, and rolls back with, the calling transaction (gotcha 5) | An explicit enqueue inside the invocable |
| "How many retries are acceptable, and what happens after the last one?" | Finalizer re-enqueue stops after five attempts (gotcha 6) | A dead-letter record and an owner for it |
| "What business key makes a replay safe?" | Re-enqueue replays the whole Queueable body, and the interview GUID changes per run (gotchas 7, 8) | An idempotency key derived from the record, not the interview |
| "Does the post-commit work touch setup objects, or rely on the record still holding its saved values?" | Mixed DML follows work into the asynchronous path, and `$Record` can change before it runs (gotchas 10, 12) | A re-query at the top of the path and a setup/non-setup split |

A proper configuration decides where post-commit work lives and how it retries, instead of learning it from the first rolled-back record that still sent an email.

## Recommended Workflow

1. **Classify the step.** Pre-commit (validation), in-transaction (DML), or
   post-commit (notify / callout / external effect)?
2. **Separate two guarantees that sound alike.** *Post-commit execution* — the
   work runs only if the transaction committed — is available three ways in Flow.
   *Post-outcome execution* — a callback that runs whether the work succeeded or
   threw — is not available in Flow at all.
3. **For post-commit work, default to the Run Asynchronously path.** It runs
   after the original transaction for the triggering record is successfully
   committed, in its own transaction, and it is what makes a callout legal. It is
   available only on after-save record-triggered flows, and you cannot give it a
   time.
4. **Use Platform Events when the consumers should be decoupled,** not merely
   deferred — three independent subscribers where adding a fourth should not
   touch the publisher. Confirm the definition is set to Publish After Commit.
5. **Cross into Apex when the work must report its own outcome or retry with a
   bound.** A Queueable's `System.Finalizer` reads `ParentJobResult.SUCCESS` or
   `UNHANDLED_EXCEPTION` and can re-enqueue a failed job up to five times.
6. **Design idempotency at the boundary.** Every mechanism here can run twice.
   The key must be deterministic and derived from the record — never
   `$Flow.InterviewGuid`, which differs on exactly the run you are guarding
   against.
7. **Log every run and every give-up.** Nobody is watching post-commit work. A
   silent stop at the platform's retry ceiling is indistinguishable from success.

## Available Mechanisms

| Mechanism | Runs | Survives rollback | Callouts | Reports its own outcome |
|---|---|---|---|---|
| Pre-commit Flow step | Same txn | No | No | No |
| After-save flow, immediate path | Same txn, before commit | No | No | No |
| **Run Asynchronously path** | New txn, after commit | Yes | Yes | No |
| Platform Event (Publish After Commit) → subscriber | New txn | Yes | Yes, in the subscriber | No |
| Queueable + `System.Finalizer` | Async, after commit | Yes | Yes | **Yes** |

The last column is the whole decision. Everything above the bottom row defers
work; only the bottom row tells you what happened to it.

## Patterns

### Pattern A: Run Asynchronously Path

The default for "must not fire on rollback" and for any callout. Open the
after-save record-triggered flow → **Start** element → include a Run
Asynchronously path. The path runs after the original transaction for the
triggering record commits, so the external system is never told about a record
that rolled back. Add a fault connector to a log record — it is the only evidence
the path ran.

Subject to the asynchronous per-transaction Apex limits (200 SOQL, 60,000 ms CPU,
25 MB heap — `apexdev.txt` 264 L19747, L19780–19782; the heap figure is a
Winter '27 release-level change for every org, not an API-version gate; Summer '26 was 12 MB): higher than synchronous, not absent. Queued entries are visible on
the Time-Based Workflow page in Setup.

### Pattern B: Platform Event For Fan-Out

Choose this over three asynchronous paths when the consumers are genuinely
independent — the benefit is that adding a fourth subscriber does not touch the
publisher, not extra durability. Verify Publish Behavior on the event definition:
Publish Immediately fires even on rollback, and it draws on a different governor
allocation. See `flow/flow-and-platform-events`.

### Pattern C: Apex Queueable + Finalizer

Reach for this when the requirement is to know *whether* the work succeeded and
act on the answer. Flow calls an Invocable Action that enqueues a Queueable; the
Queueable attaches a finalizer that writes the outcome and, on failure, decides
whether to retry.

The ceilings that shape the design: one finalizer per Queueable job; a failed job
can be re-enqueued five times and the count resets on success; the finalizer may
enqueue a single asynchronous job; callouts are allowed. Re-enqueue replays the
**whole** Queueable body, so everything before the failure point runs again.

`templates/apex/` has no canonical `QueueableWithFinalizer` today — the
illustrative shape is in `references/examples.md`, and this is a flagged template
gap rather than an oversight.

## Durability Cheatsheet

- "After commit, one consumer, possibly a callout" → **Run Asynchronously** path.
- "After commit, several independent consumers" → Platform Event, Publish After
  Commit.
- "After commit, and I need to record whether it worked and retry with a bound"
  → Queueable + Finalizer.
- "The user must not be able to save without this" → not a post-commit problem.
  Block the save with a **Custom Error** element.

## Anti-Patterns (see `references/llm-anti-patterns.md`)

- The zero-minute scheduled path standing in for the asynchronous path.
- A callout on the immediate path of an after-save flow.
- Describing a fault path as "the flow's finalizer".
- Assuming a finalizer retries indefinitely.
- `$Flow.InterviewGuid` as an idempotency key.
- Using the fault path as a compensating transaction.
- "Async means no governor limits."

## Related

- `flow/flow-transactional-boundaries` — what commits when.
- `flow/flow-and-platform-events` — publish and subscribe mechanics.
- `flow/flow-interview-debugging` — instrumenting work nobody watches.
- `flow/flow-batch-processing-alternatives` — when the async ceilings also fail.
- `apex/apex-transaction-finalizers` — the Apex side in full.
- `standards/decision-trees/async-selection.md` — the formal engine choice. Cite
  the branch that resolved it rather than re-deriving it.

## Official Sources Used

- Transaction Finalizers — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_transaction_finalizers.htm
- Connect a Record-Triggered Flow to an External System Using an Asynchronous Path — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_asynchronous_path.htm&release=234&type=5
- Scheduled Paths — https://help.salesforce.com/s/articleView?id=platform.flow_concepts_trigger_scheduled_path.htm&type=5
- Publish Platform Event Messages Using Apex — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_publish_apex.htm
- Per-Transaction Apex Governor Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm

The full annotated list is in `references/well-architected.md`.
