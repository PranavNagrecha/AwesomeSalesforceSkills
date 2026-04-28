---
name: flow-transaction-finalizer-patterns
description: "Use when a Flow needs to do work that must survive the triggering transaction — post-commit notifications, callouts, audit rows, or compensating actions. Covers Flow Transaction Control element, scheduled paths, Platform Event + finalizer escalation, and Apex Queueable finalizer bridging. Does NOT cover general Flow async decisions (see async-selection)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
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

## Recommended Workflow

1. **Classify the step.** Is it pre-commit (validation), in-transaction
   (DML), or post-commit (notify / callout / external effect)?
2. **Prefer Scheduled Path for simple post-commit work.** A 0-minute
   scheduled path runs in a new transaction, so effects happen after the
   trigger commits.
3. **Use Platform Events for fan-out.** Publish-after-commit semantics
   guarantee the event is not emitted on rollback.
4. **Use Apex Queueable + Finalizer when the work must report success or
   chain.** A finalizer runs whether the Queueable succeeded or failed —
   essential for durable notification.
5. **Design idempotency.** Post-commit work may retry; steps must be safe to
   rerun.
6. **Log every run.** A custom object or Platform Event records that the
   post-commit step actually fired.

## Available Mechanisms

| Mechanism | Runs in | Survives rollback? | Retryable? |
|---|---|---|---|
| Pre-commit Flow step | Same txn | No (step rolls back with the txn) | N/A |
| After-Save Record-Triggered Flow | Same txn | No | N/A |
| Scheduled Path (0 min) | New txn | Yes | Via scheduled re-run pattern |
| Platform Event (publish-after-commit) | New txn via subscriber | Yes | Via replay / dead-letter |
| Queueable + `System.Finalizer` | Async, post-commit | Yes | Yes (finalizer sees outcome) |

## Patterns

### Pattern A: Scheduled Path For Email / Simple Update

Record-Triggered Flow triggers an immediate (0 min) Scheduled Path that
sends the email or updates a related record. If the parent DML rolls back,
the scheduled path does not run.

### Pattern B: Platform Event For Fan-Out

Record-Triggered Flow publishes a Platform Event (configured publish-after-
commit). Subscribers (Flow or Apex) react in their own transactions.

### Pattern C: Apex Queueable + Finalizer

When work is complex (multi-step, requires error handling, must emit an
end-to-end result), Flow calls an Invocable Action that enqueues a
Queueable. The Queueable registers a Finalizer that logs success/failure
and triggers compensating actions on failure.

See `templates/apex/` for the repo-canonical `QueueableWithFinalizer`
shape.

## Durability Cheatsheet

- "Must happen after commit, nice-to-have reliability" → Scheduled Path.
- "Must happen after commit, multiple consumers" → Platform Event.
- "Must happen after commit, guaranteed acknowledge, able to compensate on
  failure" → Queueable + Finalizer.

## Anti-Patterns (see references/llm-anti-patterns.md)

- Send email directly from a pre-save Flow.
- Use an "after-save" Flow for a callout and assume rollback protection.
- Catch an exception in Flow and continue as if nothing happened.
- Queue work without logging that it ran.

## Official Sources Used

- Flow Trigger & Scheduled Paths — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_schedule.htm
- Platform Events Publish Behavior — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_publish_after_commit.htm
- Apex Queueable Finalizer — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueable_finalizer.htm
- Salesforce Well-Architected Resilient — https://architect.salesforce.com/docs/architect/well-architected/resilient/resilient
