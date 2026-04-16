# Eval: apex/async-apex

- **Skill under test:** `skills/apex/async-apex/SKILL.md`
- **Priority:** P0
- **Cases:** 3
- **Last verified:** 2026-04-16
- **Related templates:** `templates/apex/HttpClient.cls`, `templates/apex/ApplicationLogger.cls`
- **Related decision trees:** `standards/decision-trees/async-selection.md`

## Pass criteria

The AI must correctly route between `@future`, Queueable, Batch Apex, and
Platform Events per `async-selection.md`, justify the choice, and generate
safe code (chain-depth checks, Finalizer for critical paths, explicit
governor-limit assertions in tests).

## Case 1 — Legacy `@future` modernisation

**Priority:** P0

**User prompt:**

> "I have 40 `@future(callout=true)` methods across the org. I want to
> migrate them to something with chaining + state. What should I use and
> why? Keep the answer short but specific."

**Expected output MUST include:**

- Recommend Queueable with `Database.AllowsCallouts` for the bulk of them.
- State that Queueable preserves non-primitive member state between chained
  jobs — `@future` cannot.
- Finalizer (`Database.AllowsCallouts` Finalizer) as the mechanism for
  retry/compensation on failure.
- Cite the 50-depth chain cap and recommend depth-aware termination via
  `System.AsyncOptions.setMaximumQueueableStackDepth()` or `isValidDepth()`.
- Keep `@future` ONLY where migration risk outweighs benefit (e.g. stable,
  primitive-arg only, already tested).

**Expected output MUST NOT include:**

- A blanket "convert all 40" without discussing risk.
- Suggesting Batch Apex for every case — Batch adds start-up latency.
- Claiming `@future` is deprecated (it is not — it is legacy, not removed).

**Rubric (0–5):**

- **Correctness:** Chooses Queueable for the right reasons.
- **Completeness:** Covers chaining, state, Finalizer, depth cap, migration risk.
- **Bulk safety:** Example code handles bulk inputs.
- **Security:** Notes that callout credentials move to Named Credentials if still inline.
- **Citation of official docs:** Links to the Queueable + Finalizer pages.

**Reference answer (gold):**

"Move to Queueable for anything that (a) needs chaining, (b) passes non-primitive arguments, or (c) needs retry. Keep `@future` for the trivial cases where none of those apply — migration risk is not free.

Queueable gains you:

- Non-primitive member state across chained jobs.
- `System.enqueueJob(new JobB(state))` chaining from `execute()`.
- `Database.AllowsCallouts` for HTTP callouts.
- Finalizers for retry/compensation when the main execute fails.
- Testability via `Test.startTest()/stopTest()` without special markers.

Watch the 50-deep chain cap — check `AsyncInfo.getMaximumQueueableStackDepth()` and surface exit conditions, don't hope for them.

Migration plan: batch the 40 methods by risk tier. Tier 1 (clear wins) = the ones that chain or need retry — migrate immediately. Tier 2 (state improvements) = migrate next. Tier 3 (trivial primitive) = leave as `@future` for now. Move credentials inline in any method to Named Credentials regardless of async mechanism."

## Case 2 — Nightly reprocess of 3M records

**Priority:** P0

**User prompt:**

> "I need to reprocess every Order nightly (currently 3M rows) to
> recalculate a derived total. The current Scheduled Flow keeps hitting
> row limits. What's the right architecture?"

**Expected output MUST include:**

- Batch Apex — specifically `Database.Batchable<SObject>` with explicit
  `scope` sized to the per-record work (start at 200, drop if callouts).
- Selective `start()` query (indexed filter on Last_Modified_Date or a
  custom processing checkpoint).
- `Database.Stateful` for aggregation or checkpoint tracking.
- Schedulable wrapper that calls `Database.executeBatch` — not Schedulable
  with real logic inside.
- A 200-record test inside `Test.startTest()/stopTest()` that actually runs
  `finish()` (the boundary that runs `finish()` under test is important).
- Governor-limit and row-count assertions per batch.

**Expected output MUST NOT include:**

- Scheduled Flow as the answer (the user already tried it).
- A single Queueable chain to process 3M (governor headroom runs out).
- `SELECT Id FROM Order` without a selective filter.

**Rubric (0–5):**

- **Correctness:** Batch Apex + Schedulable with selective query.
- **Completeness:** Scope, state, tests, checkpoints all addressed.
- **Bulk safety:** No SOQL/DML in loops within `execute()`.
- **Security:** `WITH USER_MODE` or documented `SYSTEM_MODE` exception.
- **Citation of official docs:** Links to Batchable interface + Database.QueryLocator.

**Reference answer (gold):**

"Batch Apex is the correct primitive — Scheduled Flow's 250k/run cap will never hold 3M, and Queueable chains will run out of headroom.

Architecture:

- `OrderTotalRecalcBatch implements Database.Batchable<SObject>, Database.Stateful`
- `start()` uses a selective query on `LastModifiedDate >= :checkpointDate`
  and/or a custom `Recalc_Checkpoint__c` so each run only processes the delta.
- `execute(scope)` with `scope = 200`; read orders + line items in one SOQL
  per batch, compute totals, update orders. No callouts — total is internal.
- `finish()` stores the new checkpoint in `Custom_Settings__c` for the next run.
- `OrderTotalRecalcScheduler implements Schedulable` calls
  `Database.executeBatch(new OrderTotalRecalcBatch(), 200)` — no real logic
  inside `execute(SchedulableContext)`.

Tests:

- Insert 200 Orders in `@TestSetup`.
- `Test.startTest(); Database.executeBatch(new OrderTotalRecalcBatch()); Test.stopTest();`
- Assert per-batch `Limits.getQueries() < 10` and updated total fields.

If 3M starts to hit total-processing-time limits, move from nightly full
pass to CDC-driven incremental + a reconciliation Batch weekly."

## Case 3 — Choosing between Queueable, Platform Event, and Scheduled Flow

**Priority:** P0

**User prompt:**

> "When I save an Opportunity that crosses $1M, I need to (a) update a
> `Deal_Desk` case, (b) notify a Slack channel, and (c) log to our data
> warehouse. What's the right async shape?"

**Expected output MUST include:**

- Reference `async-selection.md` and `integration-pattern-selection.md`.
- Split by direction: internal Salesforce work (a) = Queueable OR
  after-save Flow; fan-out to Slack (b) = Platform Event subscribed by a
  Flow HTTP callout OR MuleSoft; warehouse log (c) = CDC or Platform Event
  → external Pub/Sub API subscriber.
- One Platform Event acts as the fan-out hub — avoid bespoke code per
  consumer.
- Explicit reasoning: Platform Event rather than Scheduled Flow, because
  the trigger is record-based, not time-based.

**Expected output MUST NOT include:**

- A single Queueable doing all three (tight coupling).
- Scheduled Flow (wrong primitive — event, not schedule).
- HTTP callout directly from the trigger (blocks DML, security).

**Rubric (0–5):**

- **Correctness:** Picks Platform Event as the fan-out.
- **Completeness:** All three consumers addressed with named mechanisms.
- **Bulk safety:** Event publish inside `afterInsert()` handles 200 rows.
- **Security:** Named Credentials for Slack + warehouse.
- **Citation of official docs:** Platform Events + Pub/Sub API docs.

**Reference answer (gold):**

"Two layers. Layer 1 (trigger): after-save Flow or `OpportunityTriggerHandler.afterUpdate()` publishes a single `High_Value_Opportunity__e` Platform Event with the Opportunity Id + Amount. That's bulk-safe — one publish per matching record.

Layer 2 (subscribers):

- (a) Deal Desk case — Apex subscriber on the event enqueues a Queueable
  that creates/updates the `Case`. Keeps DML off the publishing transaction.
- (b) Slack notify — subscriber Flow uses an HTTP Callout action through a
  Named Credential for the Slack Incoming Webhook. Retry settings + fault
  path per `templates/flow/FaultPath_Template.md`.
- (c) Warehouse log — external consumer subscribes to the Platform Event
  via Pub/Sub API (gRPC). No Salesforce-side work per consumer.

This is `async-selection.md` Q12 + `integration-pattern-selection.md` Q10.
Scheduled Flow is wrong — the trigger is the Opportunity save, not a clock.
Queueable alone is wrong because you'd duplicate dispatch per consumer."
