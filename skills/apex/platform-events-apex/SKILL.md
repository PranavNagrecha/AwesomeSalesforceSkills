---
name: platform-events-apex
description: "Use when publishing or subscribing to Salesforce Platform Events from Apex, comparing Platform Events with Change Data Capture, or designing event-triggered error handling and monitoring. Triggers: 'EventBus.publish', 'platform event trigger', 'CDC vs Platform Events', 'replay ID', 'high-volume event', 'publishBehavior', 'PublishAfterCommit', 'EventBus.RetryableException', 'Test.getEventBus().deliver()', 'EventBusSubscriber', 'PlatformEventSubscriberConfig', 'publish callback'. NOT for external publishers or subscribers — use integration/platform-events-integration. NOT for subscriber batch size and retries — use apex/apex-event-bus-subscriber."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
tags:
  - platform-events
  - eventbus
  - cdc
  - replay-id
  - event-trigger
triggers:
  - "how do I publish platform events from Apex"
  - "CDC vs platform events for integration"
  - "platform event trigger subscriber pattern"
  - "EventBus publish results handling"
  - "replay ID management for event consumers"
  - "publish a platform event from an Apex service class"
  - "my platform event fired even though the transaction rolled back"
  - "EventBus.publish returns success but no subscriber ran"
  - "write a test for a platform event trigger"
  - "platform event subscriber stopped receiving events"
  - "throw EventBus.RetryableException without looping forever"
  - "set publishBehavior on a platform event object"
  - "check whether an event trigger is in the error state"
  - "deploy a platform event and its Apex trigger together"
  - "publish a platform event from apex code and check the save result"
inputs:
  - "publisher or subscriber use case and event volume"
  - "whether consumers are Apex triggers, external subscribers, or both"
  - "failure handling and retry expectations"
  - "the __e object definition, including eventType and publishBehavior"
outputs:
  - "event architecture recommendation"
  - "review findings for publication, subscription, and monitoring risks"
  - "Apex publish and subscribe pattern with error handling"
  - "deployable __e object XML, publisher class, subscriber trigger, PlatformEventSubscriberConfig, test class and package.xml"
dependencies: []
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-09-12
---

Use this skill when a design is moving toward event-driven integration and Apex is involved on the publishing or subscriber side. The goal is to publish events deliberately, consume them in a decoupled way, and separate Platform Events from Change Data Capture instead of treating them as interchangeable.

## Before Starting

- Is the system broadcasting a business event it owns, or mirroring a record change that Salesforce owns already?
- Will the subscriber be Apex, Flow, middleware, Pub/Sub API, or a mix?
- Do you need eventual consistency, replay handling for external consumers, or immediate transaction-level validation?

## Questions to Ask Before Configuring

Ask these before writing the first line of Apex. Each one changes an element in the `__e` object file or a branch in the subscriber, and each maps to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "If the publishing transaction rolls back, must the downstream system still hear about it?" | Decides `publishBehavior`. Omitting the element gives `PublishImmediately`, which fires anyway (`api_meta` L42228–42229) | The explicit `<publishBehavior>` element, and which limit meter the publisher spends — DML statements or the 150-call publish-immediately budget |
| "What is the worst thing that happens if one event is silently lost?" | Decides whether the `Database.SaveResult` check is enough or the publish needs an `EventPublishFailureCallback`. `isSuccess()` only means "queued" (`apexrefguide` L214510–214513) | Either a logged-failure path, or the callback class plus a pre-populated `EventUuid` to correlate with |
| "What is the worst thing that happens if one event is processed twice?" | Decides whether the subscriber needs an idempotency store keyed on `EventUuid` | A dedupe object and the query that loads seen UUIDs in bulk, instead of a handler that quietly double-charges |
| "Which subscriber failures are transient, and which will fail identically every time?" | `EventBus.RetryableException` retries the batch; exceeding the budget puts the subscription in `Status = Error` and it later resumes from the tip, skipping the backlog (`object_reference` L131382–131390) | A named list of retryable status codes and a retry cap below nine, instead of a blanket `catch (Exception)` that throws |
| "Who should own the records this subscriber creates, and will it ever send email?" | The trigger runs as the Automated Process entity by default; email is not supported from that context (`api_meta` L96453–96462) | A `PlatformEventSubscriberConfig` with a real `user`, or a documented decision that Automated Process is correct |
| "What peak event rate must one trigger invocation survive?" | The platform-event trigger batch is 2,000, not 200 (`apexdev` L19862) | A handler sized or chunked for 2,000, and a deliberate `batchSize` — never 1 (`api_meta` L96416–96419) |
| "Who is alerted, and how, when the subscription stops?" | Nothing in Apex reports a dead subscription; only `EventBusSubscriber` does | A scheduled query on `Status`, `Retries` and `LastError`, so a month-long gap becomes a same-day one |
| "Which personas publish this event, and which permission set carries Create on it?" | At the API 67.0 user-mode default, `EventBus.publish` needs Create on the `__e` object for the running user; nothing about the trigger, the Apex, or the object file fails at deploy time if it's missing — only the runtime publish is rejected (`references/gotchas.md`, "API 67.0 Silently Moves Publishing Into User Mode") | A named permission set per publishing persona that grants Create (and Read) on the event, checked by `scripts/check_platform_events_apex.py`, instead of a publish that fails silently into a failure log the first time a version bump or a new persona hits it |

What a proper configuration adds over just calling `EventBus.publish`: the event's transactional semantics are written down in the object file instead of inherited by accident, rejected publishes are visible, redelivery cannot duplicate downstream work, the retry budget cannot silently kill the subscription, and the subscriber's health is a monitored number rather than something discovered during an incident.

---

## Core Concepts

### Platform Events Are Explicit Business Messages

Platform Events are event records designed for decoupled publication and subscription. In Apex, publishers create event instances and call `EventBus.publish`. That is different from CDC, where Salesforce emits change events when records mutate. Use Platform Events when you want to define the payload and timing of the message instead of mirroring all record changes automatically.

### Publication Success Is Not "No Exception Thrown"

`EventBus.publish` returns `Database.SaveResult` for a single event and `List<Database.SaveResult>` for a list, and *"doesn't throw exceptions caused by an unsuccessful publish operation. It's similar in behavior to the Apex `Database.insert` method when called with the partial success option"* (`apexrefguide` L214561–214565). A `try/catch` around a publish catches almost nothing. The results are positional, so the index is the only link back to the record the event described.

And a successful result is weaker than it looks: *"If the `isSuccess()` method returns true, the publish request is queued in Salesforce and the event message is published asynchronously"* (`apexrefguide` L214510–214513). The final asynchronous outcome only reaches you through an Apex publish callback.

### The Object File Decides The Transaction Semantics, Not The Apex

Two elements on the `__e` `CustomObject` change everything about how the same `EventBus.publish` call behaves:

| Element | Values | Effect |
|---|---|---|
| `publishBehavior` | `PublishAfterCommit` / `PublishImmediately` (default `PublishImmediately` when omitted) | After-commit is lost if the transaction fails and costs one DML statement; immediate fires regardless of the transaction and draws on a separate 150-call meter |
| `eventType` | `HighVolume` / `StandardVolume` (deprecated) | New events are always `HighVolume`; existing standard-volume events migrate through `PlatformEventMigration`, which is an outage window |

Sources: `api_meta` L42091–42097, L42206–42230; `apexdev` L19598, L19635.

### Subscriber Shape Depends On The Consumer

Apex platform event triggers subscribe asynchronously and run in an `after insert` context. External consumers using Streaming or Pub/Sub APIs care about replay positions and subscriber durability, which is their own state to keep. Inside Apex the equivalent, much narrower control is `EventBus.TriggerContext.setResumeCheckpoint()`, which bookmarks a position *within the current batch only* — it throws `EventBus.InvalidReplayIdException` for any `ReplayId` outside `Trigger.new` (`apexrefguide` L157888–157892).

UNVERIFIED (2026-09-05): the rule that a platform event trigger supports *only* `after insert` is stated in the Platform Events Developer Guide, which is not in the offline corpus and whose host cannot be fetched. Every platform-event and change-event trigger example in the Apex Developer Guide is declared `(after insert)` (`apexdev` L17882 for `BatchApexErrorEvent`, L29634 for a change event), and the checker enforces it on that basis.

### CDC Solves A Different Problem

Change Data Capture is best when the event should represent Salesforce row changes. Platform Events are better when the event is a business fact or orchestration signal such as "Order Approved" or "Invoice Sync Requested." Mixing these without a decision rule creates noisy payloads and unclear ownership. Apex-side CDC specifics — `EventBus.ChangeEventHeader`, GAP events, entity selection — belong to `apex/change-data-capture-apex`.

## Common Patterns

### Publish Via A Service Boundary

**When to use:** Business logic has decided that an event should be emitted.

**How it works:** Build the event payload in a service class extending `templates/apex/BaseService.cls`, publish a list where possible, and loop the results by index for failure logging. Artifact 2 in `references/code-examples.md`.

**Why not the alternative:** Inline event creation inside many triggers or controllers duplicates payload rules and weakens monitoring.

### Publish Callback For Events You Cannot Afford To Lose

**When to use:** The event asserts something a downstream system will act on financially or contractually.

**How it works:** `EventBus.publish(events, callback)` with a class implementing `EventBus.EventPublishFailureCallback`. Pre-populate `EventUuid` with `SObjectType.newSObject(recordTypeId, loadDefaults)` so the callback can be joined back to your record (`apexrefguide` L194227–194229). Artifact 3 in `references/code-examples.md`.

### Idempotent, Checkpointed, Retry-Capped Subscriber

**When to use:** Always, for any Apex `__e` trigger that writes records or calls out.

**How it works:** Trigger is a one-line adapter; the handler loads seen `EventUuid` values in bulk, processes in chunks, checkpoints after each chunk succeeds, and throws `EventBus.RetryableException` only for classified-transient failures and only while `EventBus.TriggerContext.currentContext().retries` is under the cap. Artifact 4 in `references/code-examples.md`.

### Event Trigger To Queueable Worker

**When to use:** Subscriber logic needs callouts, retries beyond the event bus budget, or heavier processing.

**How it works:** Keep the platform event trigger thin and hand off durable work to Queueable Apex. Note this trades away the retry semantics of the event bus for the retry semantics of the queue — see `apex/async-apex`.

### CDC Versus Platform Event Decision

**When to use:** Architects are unsure whether to publish a custom event or consume record-change events.

**How it works:** Use CDC when record mutation itself is the signal. Use Platform Events when the signal is business-defined and may not map one-to-one to DML.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to broadcast a domain event like "Application Submitted" | Platform Event, `publishBehavior` = `PublishAfterCommit` | The event asserts a committed fact; a rollback must not release it |
| Need to signal that a transaction is failing (audit, error telemetry) | Platform Event, `publishBehavior` = `PublishImmediately` | The signal must escape the doomed transaction; spends the 150-call meter, not DML |
| Need downstream systems to react to Account or Contact data changes | CDC | Change stream already represents row changes |
| Losing one message is a business incident | Publish callback + `EventUuid` correlation | `isSuccess()` only proves the request was queued |
| Apex subscriber needs callouts or heavier orchestration | Platform event trigger + Queueable | Thin trigger, safer processing boundary |
| Subscriber writes records that need a real owner, or sends email | `PlatformEventSubscriberConfig` with `user` | Default Automated Process entity cannot send email and owns nothing meaningfully |
| External consumer must recover after downtime | Replay-aware external subscriber | Replay handling belongs with external consumer state — see `integration/platform-events-integration` |

## Recommended Workflow

1. **Settle the two object-file elements first.** Answer the rollback question and the volume question from `## Questions to Ask Before Configuring`, then write `<publishBehavior>` and `<eventType>` explicitly into the `__e` `CustomObject` (Artifact 1 in `references/code-examples.md`). Everything downstream depends on these two lines, and both have defaults that will not be what you meant.
2. **Build the publisher against `templates/apex/BaseService.cls`** and inspect `List<Database.SaveResult>` by index, logging through `templates/apex/ApplicationLogger.cls`. Add the `EventPublishFailureCallback` (Artifact 3) if the answer to "what if one is lost" was anything other than "nothing".
3. **Build the subscriber as trigger-plus-handler** (Artifact 4): one-line `(after insert)` trigger, handler that is idempotent on `EventUuid`, chunked for a 2,000-event batch, checkpointed after each chunk, and retry-capped below nine. Ship the `PlatformEventSubscriberConfig` (Artifact 5) alongside it if the subscriber writes records or sends email.
4. **Write the test class before deploying** (Artifact 6). Every delivery path needs an explicit `Test.getEventBus().deliver()`; the failure-callback path needs `Test.getEventBus().fail()`. A green test with no `deliver()` call proves nothing.
5. **Run the checker** over the source tree: `python3 skills/apex/platform-events-apex/scripts/check_platform_events_apex.py --manifest-dir force-app/main/default`. Its nine rules map one-to-one to gotchas in `references/gotchas.md`; exit 0 is the gate (add `--strict` to also fail on the WARN-level permission-set gap, rule R9).
6. **Deploy in dependency order** (`references/code-examples.md`, Deploy order) and run `sf apex run test --tests <YourEventTest>`.
7. **Verify the live subscription**, not just the tests: query `EventBusSubscriber` for `Status`, `Retries`, `LastError` and the `LastProcessed` / `LastPublished` gap, and put that query on a schedule. `references/examples.md` Example 3 explains how to read each column.

---

## Review Checklist

- [ ] `<publishBehavior>` is written explicitly in every `__e` object file, and the choice matches how the publisher describes itself.
- [ ] `<eventType>` is `HighVolume`; any `StandardVolume` definition has a migration plan.
- [ ] Publishers capture `Database.SaveResult` and loop it by index; failures reach a queryable log, not `System.debug`.
- [ ] Events whose loss is a business incident publish with an `EventPublishFailureCallback`.
- [ ] Platform event triggers are `(after insert)` only and delegate to a handler class.
- [ ] The subscriber is idempotent on `EventUuid` and safe at a 2,000-event batch.
- [ ] Every `EventBus.RetryableException` throw is guarded by a `TriggerContext.retries` cap below nine.
- [ ] `setResumeCheckpoint` is called only with a `ReplayId` from the current batch, and only after that work completed.
- [ ] A `PlatformEventSubscriberConfig` exists wherever the running user or batch size matters, and deploys after the trigger.
- [ ] Tests call `Test.getEventBus().deliver()` (and `.fail()` for callback paths).
- [ ] `EventBusSubscriber.Status` and `Retries` are monitored on a schedule.
- [ ] External replay expectations are documented when non-Apex consumers exist.

## Salesforce-Specific Gotchas

1. **The default `publishBehavior` is `PublishImmediately`** — the event survives a rollback unless you write `PublishAfterCommit` yourself.
2. **`EventBus.publish` never throws for a rejected event** — the `SaveResult` is the only failure signal, and `isSuccess()` means "queued", not "delivered".
3. **Apex platform event triggers are asynchronous `after insert` subscribers** — do not design them like normal object triggers.
4. **The subscriber batch is 2,000, not 200** — a per-record SOQL/DML handler will not survive peak volume.
5. **Exceeding the `RetryableException` budget stops the subscription** — and when it is fixed it resumes from the tip, so the backlog is lost.
6. **`setResumeCheckpoint` only accepts a `ReplayId` from the current batch** — it is a within-invocation bookmark, not a durable cursor.
7. **The subscriber runs as Automated Process by default** — no meaningful record ownership, no email, and no debug log under the user you enabled.
8. **API 67.0 moves publishing from system mode to user mode** — a version bump alone can start failing, with `Database.SaveResult` errors reading `"<Event>__e publish rejected: Access to entity '<Event>__e' denied"` until a permission set grants Create on the event.

Full detail, with line-cited sources, in `references/gotchas.md`.

## Output Artifacts

| Artifact | Description |
|---|---|
| Event decision guide | Recommendation for Platform Events vs CDC, and the `publishBehavior` / `eventType` choice with its reason |
| Deployable slice | `__e` object XML, publisher class, publish callback, subscriber trigger + handler, `PlatformEventSubscriberConfig`, test class, `package.xml`, deploy order |
| Publish/subscribe review | Findings on payload design, result handling, idempotency, retry capping, and consumer reliability |
| Subscription monitoring query | Scheduled `EventBusSubscriber` SOQL with a reading guide for each column |

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are building or reviewing the actual slice — event XML, publisher, callback, subscriber trigger + handler, subscriber config, test class, `package.xml`, deploy order, verification |
| `references/gotchas.md` | A publish or a subscription is behaving in a way the code does not explain, or you are choosing `publishBehavior` / batch size / retry cap |
| `references/examples.md` | You want worked scenarios: bulk publishing from a service, a thin trigger delegating to Queueable, and how to read `EventBusSubscriber` to prove a subscriber is alive |
| `references/llm-anti-patterns.md` | You are reviewing generated Apex or XML — nine failure modes with detection hints, including the limit and retention numbers assistants routinely invent |
| `references/well-architected.md` | You are tagging findings by pillar, or you need the exact source and line range behind a claim in this package |

## Related Skills

- `apex/apex-event-bus-subscriber` — use when the subscriber's runtime semantics are the problem: checkpoint-versus-`RetryableException`, batch-size tuning, and running-user selection in depth.
- `apex/change-data-capture-apex` — use when the trigger is on a `ChangeEvent` instead: `ChangeEventHeader`, GAP events, entity selection.
- `integration/platform-events-integration` — use when a publisher or subscriber lives outside the org: REST publish, CometD or Pub/Sub API, durable replay state.
- `flow/flow-and-platform-events` — use when the publisher or subscriber is a Flow rather than Apex.
- `apex/async-apex` — use when the subscriber workload really needs Queueable or Batch design rather than event design alone.
- `apex/exception-handling` — use when publication failures or subscriber exceptions need better classification and logging.
- `apex/callouts-and-http-integrations` — use when event consumers ultimately call external HTTP systems.
