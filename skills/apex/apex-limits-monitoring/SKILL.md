---
name: apex-limits-monitoring
description: "Use this skill when writing Apex that must check governor limits at runtime before executing expensive operations — guard clauses, early-exit patterns, Queueable re-queue on limit approach, and batch scope sizing. Also covers building the monitoring layer above those checks: ApexTestResultLimits regression gates in CI, debug-log LIMIT_USAGE events, and a Scheduled Apex poller that writes OrgLimits readings into a Limit_Snapshot__c time series with threshold alerts. Trigger keywords: check governor limits before SOQL apex, defensive coding against limits apex, Limits.getDMLStatements getLimitDMLStatements, Limits class usage, guard clause governor limits, remaining SOQL queries Apex, heap size check before DML, LimitException handling, alert before we hit a governor limit, limit consumption regression in CI. NOT for diagnosing a limit you already hit — use apex/governor-limits. NOT for CPU and heap tuning — use apex/apex-cpu-and-heap-optimization. NOT for choosing which org limits matter or the org-wide alert routing architecture — use architect/org-limits-monitoring."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "check governor limits before SOQL apex"
  - "defensive coding against limits apex"
  - "Limits.getDMLStatements getLimitDMLStatements guard clause"
  - "how to avoid System.LimitException in Apex"
  - "Queueable re-queue when approaching CPU limit"
  - "batch scope sizing based on limit consumption"
  - "Limits.getQueries getDmlRows getCpuTime approaching ceiling alert"
  - "add a limit guard before an expensive query in Apex"
  - "warn me before a transaction hits the CPU ceiling"
  - "measure how much of the SOQL limit a service method consumes"
  - "fail the build when a test method's CPU consumption regresses"
  - "read ApexTestResultLimits after a test run"
  - "schedule an Apex job that snapshots OrgLimits into a custom object"
  - "alert when an org limit passes a percentage threshold"
  - "find out which governor limit a failed transaction actually blew"
  - "log the limit headroom at each phase of a long transaction"
  - "degrade gracefully instead of throwing when limits run low"
tags:
  - apex-limits
  - governor-limits
  - defensive-coding
  - limits-class
  - monitoring
  - orglimits
  - alerting
  - observability
inputs:
  - "The Apex class, trigger, or batch class under review"
  - "Expected data volume or iteration count if batch/bulk"
  - "Whether the transaction runs synchronously or asynchronously"
  - "Which limits matter for this org (from architect/org-limits-monitoring, if that work has been done)"
  - "The degrade behaviour the business will accept when headroom runs out"
outputs:
  - "Guard clauses inserted before expensive operations (SOQL, DML, heap-intensive work)"
  - "Early-exit and re-queue logic for Queueable jobs nearing the CPU or SOQL ceiling"
  - "Batch scope-size recommendation derived from per-record limit projection"
  - "Observability log statements that report remaining limit headroom as a percentage"
  - "A deployable LimitGuard class, OrgLimitsPoller Schedulable, Limit_Snapshot__c object, Limit_Threshold__mdt config and test class"
  - "A CI query over ApexTestResultLimits that fails the build on a per-test-method limit regression"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Apex Limits Monitoring

Activate this skill when writing Apex that must stay within Salesforce governor limits at runtime, or when building the layer that watches limit consumption over time. It covers the `Limits` class API, guard-clause patterns, early-exit and re-queue strategies, batch scope calculation, and the three places limit data can be observed: inside the transaction, after it, and across the org.

---

## Before Starting

- Confirm whether the code runs synchronously or asynchronously; ceilings differ (Apex Developer Guide, Per-Transaction Apex Limits, `apexdev L19540–19580`). Scheduled Apex is the trap: it is an async feature that runs under **synchronous** limits (`apexdev L19536`).
- Identify the highest-volume code path — that is where limit pressure accumulates, not average paths.
- `System.LimitException` is uncatchable, and so is the `finally` block you were relying on. Prevention is the only option (`apexdev L39720–39728`).
- Decide what "degrade" means for this code path before writing a guard. A guard that returns an empty list silently is a data-correctness bug wearing a reliability costume.

---

## Questions to Ask Before Configuring

Ask before writing the first guard. A monitor built without these answers reports numbers nobody acts on, and a guard built without them turns a loud failure into a quiet wrong answer.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "When this code runs out of headroom, is a partial result acceptable, or must the whole transaction fail?" | Decides whether the guard returns early, throws an application exception, or re-queues. Returning an empty collection where the caller expects completeness converts a visible `LimitException` into silent data loss | The degrade contract: what the caller receives, and how it can tell the result was truncated |
| "Which context does this code actually run in — trigger, Batch `execute`, Queueable, Scheduled, or a Finalizer?" | Every one of these has a different ceiling, and two of them surprise people: scheduled Apex gets synchronous limits, and a Finalizer gets synchronous limits with exactly three async exceptions | The right ceiling source (always `getLimitX()`), and whether re-queue is even available here |
| "What is the per-record cost of the loop body, in SOQL, DML rows, and callouts?" | Scope size and the guard threshold are both derived from this number; guessing it produces a batch that fails on chunk one or wastes 60% of its allocation | A scope formula in the class header that a reviewer can re-derive when the loop changes |
| "Does a managed package run inside this transaction?" | Certified managed packages get their own 150 DML and 100 SOQL allocations, so `Limits.getQueries()` in your namespace cannot see theirs, and the cumulative ceiling is 11× the per-namespace one | A decision to read `LIMIT_USAGE_FOR_NS` per namespace rather than trusting one number |
| "Which limits does the business actually care about, and what does 'too high' mean for each?" | Alerting on everything `OrgLimits.getAll()` returns is alerting on nothing. Percentage thresholds must come from observed peaks, not from 80 being a round number | The `Limit_Threshold__mdt` record set, and a defensible warning/critical pair per limit |
| "Who receives a threshold alert, and what are they expected to do that day?" | An alert with no owner and no runbook becomes noise within two weeks, after which the monitor is worse than nothing because it looks like coverage | A named owner per limit and the action that clears the alert |
| "How will we know a limit regression landed — before production, not after?" | `ApexTestResultLimits` records consumption per test method, but only between `Test.startTest()` and `Test.stopTest()`, only for async runs, and only in the default namespace | A CI gate with a committed baseline, and tests shaped so the object actually gets populated |

What a proper limits-monitoring layer adds over scattering `Limits.getQueries()` calls: the ceiling is read from the context instead of hardcoded, the degrade behaviour is a contract rather than an accident, a consumption regression fails the build instead of the customer's Tuesday, and when a transaction does blow a limit the exact meter is recoverable from outside the dead transaction.

---

## Core Concepts

### Three Monitoring Horizons

This skill owns all three. Each answers a different question and none substitutes for another.

| Horizon | Question it answers | Mechanism | Where it lives |
|---|---|---|---|
| In-transaction | "Can I afford the next operation?" | `Limits.getX()` vs `Limits.getLimitX()` → early-exit, degrade, or re-queue | `LimitGuard` in `references/code-examples.md` |
| Post-transaction | "Did consumption change since last release? Which meter blew?" | `ApexTestResultLimits` in CI; `CUMULATIVE_LIMIT_USAGE` in debug logs; a Finalizer; `EventLogFile` `ApexUnexpectedException` | CI pipeline + Event Monitoring |
| Org-wide | "Are we going to run out of API calls / storage / async executions this week?" | `OrgLimits.getAll()` or REST `/limits`, polled into a time series with thresholds | `OrgLimitsPoller` + `Limit_Snapshot__c` |

### The `Limits` Class — `getX()` / `getLimitX()` Pairs

"There are two versions of every method: the first returns the amount of the resource that has been used while the second version contains the word limit and returns the total amount of the resource that is available" (Apex Reference Guide, Limits Class, `apexrefguide L220166–220170`).

Pairs worth guarding, all from the class's own method list (`apexrefguide L220185–220390`):

| Concern | Used | Ceiling |
|---|---|---|
| SOQL queries | `Limits.getQueries()` | `Limits.getLimitQueries()` |
| SOQL rows returned | `Limits.getQueryRows()` | `Limits.getLimitQueryRows()` |
| `getQueryLocator` rows | `Limits.getQueryLocatorRows()` | `Limits.getLimitQueryLocatorRows()` |
| DML statements | `Limits.getDMLStatements()` | `Limits.getLimitDMLStatements()` |
| DML rows | `Limits.getDMLRows()` | `Limits.getLimitDMLRows()` |
| CPU time (ms) | `Limits.getCpuTime()` | `Limits.getLimitCpuTime()` |
| Heap size (bytes) | `Limits.getHeapSize()` | `Limits.getLimitHeapSize()` |
| Callouts | `Limits.getCallouts()` | `Limits.getLimitCallouts()` |
| SOSL queries | `Limits.getSoslQueries()` | `Limits.getLimitSoslQueries()` |
| Relationship subqueries | `Limits.getAggregateQueries()` | `Limits.getLimitAggregateQueries()` |
| `@future` calls | `Limits.getFutureCalls()` | `Limits.getLimitFutureCalls()` |
| Queueable jobs enqueued | `Limits.getQueueableJobs()` | `Limits.getLimitQueueableJobs()` |
| `sendEmail` invocations | `Limits.getEmailInvocations()` | `Limits.getLimitEmailInvocations()` |
| Publish-immediately events | `Limits.getPublishImmediateDML()` | `Limits.getLimitPublishImmediateDML()` |
| Mobile push Apex calls | `Limits.getMobilePushApexCalls()` | `Limits.getLimitMobilePushApexCalls()` |
| Apex cursors (24 h) | `Limits.getApexCursors()` | `Limits.getLimitApexCursors()` |

Three entries on that list are **not** usable in a monitor:

- `getAsyncCalls()` / `getLimitAsyncCalls()` are documented as "Reserved for future use" (`apexrefguide L220473–220490`). A monitor that reports them is reporting a placeholder.
- `getRunAs()`, `getSavepoints()` and `getSavepointRollbacks()` are deprecated and return the same value as `getDMLStatements()` (`apexrefguide L220295–220305`). Charting all four gives you one line drawn four times.
- `getFindSimilarCalls()` is deprecated and returns the same value as `getSoslQueries()` (`apexrefguide L220246–220249`).

Wording matters when you write the log line: `getHeapSize()` "returns the **approximate** amount of memory (in bytes) that has been used for the heap" (`apexrefguide L220711–220712`). `getCpuTime()` carries no such qualifier — it "returns the CPU time (in milliseconds) that has been used in the current transaction" (`apexrefguide L220544–220545`). Do not label a heap reading exact, and do not label a CPU reading approximate.

### Sync vs Async Ceilings — and Where "Async" Is a Lie

From the Per-Transaction Apex Limits table (`apexdev L19540–19580`):

| Limit | Synchronous | Asynchronous |
|---|---|---|
| SOQL queries | 100 | 200 |
| SOQL rows returned | 50,000 | 50,000 |
| DML statements | 150 | 150 |
| DML rows | 10,000 | 10,000 |
| Callouts | 100 | 100 |
| `System.enqueueJob` calls | 50 | 1 |
| `@future` methods per invocation | 50 | 0 in batch/future, 50 in queueable |
| CPU time | 10,000 ms | 60,000 ms |
| Heap size | 6 MB | 12 MB |
| `EventBus.publish` (publish immediately) | 150 | 150 |

Three notes on that table the platform prints right beside it:

- Scheduled Apex is asynchronous but runs under the **synchronous** column (`apexdev L19536`). A `Schedulable` that assumes 200 SOQL has half the room it thinks.
- A Finalizer also runs under synchronous limits, with three exceptions where async limits apply: total heap size, `System.enqueueJob` count, and `@future` methods per invocation (`apexdev L16297–16303`).
- Email services get a 50 MB heap (`apexdev L19650`), which is neither column.

Guard clauses must therefore call `Limits.getLimitX()` rather than a constant. The runtime already knows which column applies; a hardcoded number does not.

### What `getAggregateQueries()` Actually Counts

Not `COUNT()`, `SUM()` or `GROUP BY`. The Per-Transaction Apex Limits footnote is explicit: "In a SOQL query with parent-child relationship subqueries, each parent-child relationship counts as an extra query. These types of queries have a limit of three times the number for top-level queries. **The limit for subqueries corresponds to the value that `Limits.getLimitAggregateQueries()` returns**" (`apexdev L19612–19616`). So the meter tracks relationship subqueries, its ceiling is 3× the SOQL ceiling (300 sync, 600 async — derived, not printed), and an aggregate-function query still consumes an ordinary slot on `getQueries()`. Guard the subquery count in code that issues nested `SELECT (SELECT …)` shapes, not in code that issues `COUNT()`.

### `System.LimitException` Takes `finally` With It

"Some special types of built-in exceptions can't be caught… One such exception is the limit exception (`System.LimitException`)… **When exceptions are uncatchable, catch blocks, as well as `finally` blocks if any, aren't executed**" (`apexdev L39720–39728`). The second half is the part that costs people a logging strategy: a `finally { LogService.flush(); }` does not run either, so the transaction cannot record its own death. Post-mortem must come from outside — `BatchApexErrorEvent`, a Finalizer, or the `ApexUnexpectedException` event log. See `references/code-examples.md` for the three surfaces and what each yields.

### Org-Wide: `OrgLimits` and REST `/limits` Disagree on Purpose

`OrgLimits.getAll()` returns `List<System.OrgLimit>`; `getMap()` keys the same by name (`apexrefguide L226226–226256`). Each instance exposes `getName()`, `getLimit()` (maximum) and `getValue()` (**usage**) (`apexrefguide L226101–226166`). The REST resource returns `Max` and `Remaining` instead (`api_rest L2000–2002`). One reports consumed, the other reports left; a poller that treats them as interchangeable inverts every reading. Both lag: "Limit values are updated asynchronously, in near-real-time" (`apexrefguide L226215`), and "tabulated limits returned by the API are accurate within five minutes of resource consumption" (`api_rest L7792–7793`).

---

## Common Patterns

### Guard Clause Before an Expensive Operation

**When to use:** any service-layer method that issues SOQL, DML, or heap-intensive work inside a loop or reachable from several code paths.

**How it works:** compare consumption to a percentage of `getLimitX()`, not to a constant. `LimitGuard.nearSoql(80)` in `references/code-examples.md` is the reusable form; `LimitGuard.hasRoomFor('soql', 3)` is the exact form to prefer when the per-call cost is known.

**Why not the alternative:** a `try/catch (System.LimitException)` compiles and never runs.

```apex
if (LimitGuard.nearSoql(80)) {
    LogService.warn('ContactService.enrich', 'degraded: ' + LimitGuard.snapshot());
    return partial;                       // and the caller can tell it is partial
}
```

### Queueable Re-Queue on Limit Approach

**When to use:** long-running Queueable jobs over variable-size datasets.

**How it works:** check headroom after each slice; when it drops, persist a cursor and enqueue the remainder. Bound the chain: "no limit is enforced on the depth of chained jobs… For Developer Edition and Trial organizations, the maximum stack depth for chained jobs is 5" (`apexdev L16182–16185`). Use `AsyncOptions.MaximumQueueableStackDepth` with `System.enqueueJob(queueable, asyncOptions)` and read `AsyncInfo.getCurrentQueueableStackDepth()` inside `execute` to stop deliberately rather than by accident (`apexdev L16044–16057`). Each execution counts once against the shared 24-hour asynchronous ceiling (`apexdev L17689–17694`), so an unbounded chain is an org-wide problem, not a local one.

### Batch Scope Size From Per-Record Cost

**When to use:** designing a Batch class where per-record limit cost is estimable.

**How it works:** divide the applicable ceiling by the per-record cost, apply a safety factor, and write the derivation into the class header so the next change re-derives it. Governor limits reset for each `execute` invocation (`apexdev L17712–17713`), which is what makes the arithmetic per-chunk rather than per-job. `scope` caps at 2,000 when `start` returns a `QueryLocator`, and the optimal value is a factor of 2000 (`apexdev L17704–17708`). Worked example in `references/examples.md`.

### Checkpoint Logging and the Snapshot Shape

**When to use:** high-volume service methods and batch `execute` bodies.

`apex/debug-and-logging` already ships `LogService.limitsSnapshot()`. Do not write a second one. `LimitGuard.snapshot()` in this skill emits the same `name=used/ceiling` shape and adds the meters `LogService` omits, so one parser reads both strings.

### Threshold Polling Into a Time Series

**When to use:** the org needs to see a limit climbing, not just its current value.

`OrgLimitsPoller` reads `OrgLimits.getAll()`, classifies each reading against `Limit_Threshold__mdt`, and writes one `Limit_Snapshot__c` row per limit per run. Which limits are worth monitoring, what the alert routing should be, and who owns each alert are `architect/org-limits-monitoring` questions; the Apex that implements the answer is here.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Service method called from a trigger, may issue SOQL | `LimitGuard.hasRoomFor('soql', n)` before the query, with an explicit degrade contract | Trigger context has no retry; the exact-cost form beats a percentage guess |
| Queueable over a variable-size dataset | Headroom check inside the loop, cursor re-queue, bounded with `AsyncOptions.MaximumQueueableStackDepth` | Chain depth is otherwise unbounded and consumes the org's shared async allocation |
| Batch `execute` with uncertain per-record SOQL cost | Derive scope from the binding constraint; document the formula in the class header | Limits reset per `execute`, so scope is the only lever that matters |
| Heap-intensive transformation | `LimitGuard.nearHeap(pct)` inside the build loop, not only at method entry | `getHeapSize()` is an approximate reading of a number that grows as you allocate |
| Need to know which meter is closest to its ceiling | `LimitGuard.worst()` in the log line | One name in the alert beats twelve numbers nobody reads |
| Consumption regression must not reach production | `ApexTestResultLimits` diff in CI against a committed baseline | The only per-test-method consumption record the platform keeps |
| A transaction died and you need to know which limit | `EventLogFile` `ApexUnexpectedException` → `EXCEPTION_CATEGORY` | Names the meter (`LimitException: CpuTime`) from outside the dead transaction |
| Org-level allocation trending toward exhaustion | `OrgLimitsPoller` → `Limit_Snapshot__c` → threshold alert | `OrgLimits` gives a current value; the object gives a slope |
| Choosing sync vs async in the first place | `standards/decision-trees/async-selection.md` | This skill covers defensive coding, not job-type selection |
| Deciding *which* org limits matter and who is paged | `architect/org-limits-monitoring` | That skill owns the monitoring architecture; this one owns the Apex |

---

## Recommended Workflow

1. **Establish the context and its ceilings.** Determine whether the target code is a trigger, Batch `execute`, Queueable, Scheduled job, or Finalizer, then check it against the sync/async table above — scheduled Apex and Finalizers both run under synchronous limits with exceptions. Replace every hardcoded ceiling with the matching `Limits.getLimitX()` call.
2. **Map the per-record cost of each loop.** For every loop and fan-out method, count SOQL statements, relationship subqueries, DML statements, DML rows, and callouts per iteration. This number feeds both the guard threshold and the batch scope formula; record it in a class-header comment.
3. **Deploy `LimitGuard` and replace the ad-hoc subtractions.** Take the class from `references/code-examples.md`, then convert each `getLimitX() - getX() < n` expression at a call site into `LimitGuard.hasRoomFor(meter, n)` or `LimitGuard.nearX(pct)`. Write the degrade contract into the method's doc comment: what the caller receives and how it detects truncation.
4. **Wire the degrade path into `LogService`.** Every guard that trips must emit one line carrying `LimitGuard.snapshot()` and `LimitGuard.worst().name`. Do not add a `finally` block for this — a limit breach skips `finally` entirely, so the log has to be written by the guard, before the operation.
5. **Stand up the org-wide poller.** Deploy `Limit_Snapshot__c`, `Limit_Threshold__mdt` and `OrgLimitsPoller` from `references/code-examples.md` in the deploy order given there, populate one threshold record per limit the org actually cares about, and schedule the job last from anonymous Apex.
6. **Run `scripts/check_apex_limits_monitoring.py --manifest-dir <source root>`.** It flags the seven defects this skill's gotchas describe — hardcoded ceilings, `catch (System.LimitException)`, per-iteration `getCpuTime()` polling, a poller with no dispatch, a snapshot object with no DateTime column, threshold literals duplicated across classes, and guard tests that assert without consuming anything. Add `--strict` in CI to promote WARN to failure.
7. **Close the loop in CI.** Run `sf apex run test` asynchronously, query `ApexTestResultLimits` for the run, and diff `Cpu`, `Soql`, `QueryRows`, `Dml` and `DmlRows` per method against the committed baseline. Verify the tests actually populate the object — no `Test.startTest()`/`Test.stopTest()` block means no row, and no row reads as zero consumption.

---

## Review Checklist

- [ ] No hardcoded limit constants — every ceiling comes from `Limits.getLimitX()` at runtime
- [ ] Scheduled Apex classes are sized against **synchronous** ceilings, not async ones
- [ ] Every SOQL or DML inside or reachable from a loop is preceded by a headroom check
- [ ] Each guard's degrade behaviour is documented and detectable by the caller — no silent empty collections
- [ ] No `try/catch (System.LimitException)` anywhere; no `finally` block relied on for limit-breach logging
- [ ] `Limits.getCpuTime()` is not polled on every iteration of a tight loop
- [ ] Queueable re-queue chains are bounded via `AsyncOptions.MaximumQueueableStackDepth`
- [ ] Batch `execute` scope size is documented with its per-record cost derivation
- [ ] Threshold percentages live in `Limit_Threshold__mdt`, not as literals in two or more classes
- [ ] `Limit_Snapshot__c` (or equivalent) carries a DateTime column — otherwise it is not a time series
- [ ] Guard tests consume real limit budget before asserting; assertions on an untouched transaction prove nothing
- [ ] CI queries `ApexTestResultLimits` and the tests are shaped so it is actually populated

---

## Salesforce-Specific Gotchas

Eleven non-obvious platform behaviours, each with **What happens / When it occurs / How to avoid** and a guide citation, are in `references/gotchas.md`. The four that most often invalidate a monitoring design:

1. A limit breach skips `finally`, not just `catch` — so in-transaction logging cannot record it.
2. `getAggregateQueries()` counts relationship subqueries, not aggregate functions.
3. `ApexTestResultLimits` is populated only between `startTest`/`stopTest`, only for async runs, only in the default namespace — and it has no heap column.
4. Certified managed packages get their own limit allocations, so your `Limits.getQueries()` reading is per-namespace, not per-transaction.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `LimitGuard.cls` + `-meta.xml` | Percentage and exact-cost guards over nine meters, plus `snapshot()` matching `LogService`'s shape |
| `OrgLimitsPoller.cls` | Thin `Schedulable` writing `Limit_Snapshot__c` rows from `OrgLimits.getAll()` with CMDT-driven classification |
| `Limit_Snapshot__c` + fields | The limit time series: name, consumed, maximum, percent, severity, captured-at, run id |
| `Limit_Threshold__mdt` + one record | Deployable warning/critical percentages per limit name |
| `LimitGuardTest.cls` | Threshold assertions against measured consumption; poller row shape through an injection seam |
| `package.xml`, deploy order, verification SOQL | Ordered deployment and the `CronTrigger` / `Limit_Snapshot__c` queries that prove it ran |
| CI limits gate | `ApexTestResultLimits` query plus the three conditions that must hold for it to return rows |
| Guard-clause and re-queue snippets | Paste-ready patterns for service classes and Queueable jobs |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are building it: `LimitGuard`, `OrgLimitsPoller`, `Limit_Snapshot__c`, `Limit_Threshold__mdt`, the test class, package.xml, deploy order, verification SOQL, the CI gate, and the three post-mortem surfaces |
| `references/gotchas.md` | A guard did not fire, a monitor reported nothing, or a limit blew where you thought you had headroom — eleven platform behaviours with guide citations |
| `references/llm-anti-patterns.md` | Reviewing generated limit-handling code; eight failure shapes with detection hints |
| `references/examples.md` | You need the worked guard clause, the batch scope derivation, checkpoint logging, or the CI regression baseline |
| `references/well-architected.md` | Justifying guard granularity, alert thresholds, or the cost of the monitoring layer to a reviewer |
| `templates/apex-limits-monitoring-template.md` | Running a limits review over someone else's Apex |
| `scripts/check_apex_limits_monitoring.py` | Before deploying — seven rules over the `.cls` and `.object-meta.xml` files this skill produces |

## Related Skills

- `apex/governor-limits` — owns the limit definitions themselves and diagnosing a breach after the fact. Go there when the question is "what is this limit"; stay here when it is "how do I watch it".
- `apex/governor-limit-recovery-patterns` — owns what to do once a limit has been hit: chunking, retry, and restart strategies. This skill tries to prevent that call.
- `apex/apex-cpu-and-heap-optimization` — owns reducing consumption. This skill measures it and decides when to stop.
- `apex/debug-and-logging` — owns `LogService`, the `Application_Log__c` sink, and the per-transaction `Limits` snapshot. This skill decides *when* to log a limit reading; that skill owns *how* it is stored and survives rollback.
- `apex/exception-handling` — owns the exception hierarchy and rethrow policy, including why `System.LimitException` sits outside it.
- `apex/apex-transaction-finalizers` — owns the Finalizer contract. This skill uses it as one of three post-mortem surfaces.
- `apex/apex-scheduled-jobs` — owns cron expressions, `System.abortJob`, the 100-scheduled-job ceiling, and deploying a class with an active job. `OrgLimitsPoller` is deliberately thin so that skill stays authoritative.
- `apex/batch-apex-patterns` — owns Batch lifecycle and `AsyncApexJob`; pair with this skill when sizing scope.
- `apex/apex-queueable-patterns` — owns chaining, `AsyncOptions`, and duplicate-job detection for the re-queue pattern used here.
- `architect/org-limits-monitoring` — owns the org-wide monitoring architecture: which limits matter, alert routing, dashboards, and baselining. This skill implements it in Apex.
- `architect/limits-and-scalability-planning` — owns designing for headroom before code exists.
- Decision tree: `standards/decision-trees/async-selection.md` — read before deciding which async mechanism to use.
- Decision tree: `standards/decision-trees/performance-tuning.md` — read when the question is where the time is going rather than how close the meter is.
