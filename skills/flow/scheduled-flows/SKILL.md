---
name: scheduled-flows
description: "Use when designing or reviewing schedule-triggered flows for recurring automation, replacement of time-based workflow patterns, bounded record selection, idempotent processing, and escalation to Apex when volume is too high. Triggers: 'scheduled flow design', 'nightly flow job', 'time based workflow replacement', 'schedule triggered flow limits'. NOT for record-triggered scheduled paths — use flow/flow-time-based-patterns. NOT for large-scale batch processing — use apex/batch-apex-patterns."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
tags:
  - scheduled-flows
  - schedule-triggered
  - recurring-automation
  - idempotency
  - batch-apex-boundary
triggers:
  - "when should i use a scheduled flow"
  - "nightly automation with schedule triggered flow"
  - "scheduled flow versus batch apex"
  - "time based workflow replacement with flow"
  - "scheduled flow volume and retry design"
  - "scheduled flows isn't working"
inputs:
  - "what recurrence is needed and whether the record set can be bounded tightly"
  - "how much data the flow will inspect or mutate on each run"
  - "what should happen on rerun, partial failure, or duplicate processing"
outputs:
  - "scheduled-flow design for record selection, processing, and escalation boundaries"
  - "review findings for unbounded scope, weak retry behavior, and volume risk"
  - "guidance on when to stay in Flow versus move heavy work to Apex"
dependencies: []
version: 2.1.1
author: Pranav Nagrecha
updated: 2026-10-20
---

Use this skill when automation needs to run on a recurring cadence rather than directly from a record event. Schedule-triggered flows work well for bounded recurring tasks such as reminders, renewals, or cleanup logic. They become risky when teams treat them like a general-purpose batch engine and let the record scope or side effects grow without discipline.

The three most common failure modes of scheduled flows in production: (1) unbounded start filter that touches half the org's records on every run, (2) missing idempotency so the same records get "reminded" on every nightly run, (3) silent failure because nobody reads the flow error emails or checks the Scheduled Jobs page (a scheduled flow is a `CronJobDetail` of `JobType` 6, obj 264 L86852). This skill exists to prevent all three — and to know when to stop and use Batch Apex instead.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- What recurrence is required, and is the automation tied to a business calendar or to a record event that might fit a scheduled path better?
- How many records could match the criteria on a normal day, and what is the worst-case volume during seasonal or data-load spikes?
- How will the flow avoid duplicate work if it runs again, partially fails, or overlaps with another automation?
- What is the expected runtime budget? UNVERIFIED (2026-10-20): which Apex governor limits a scheduled flow runs under is not in the corpus; scheduled Apex gets the synchronous limits (apexdev 264 L19739), so budget for the lower ones (10,000 ms CPU, 10 MB heap, apexdev 264 L19780-19782).
- Who owns the error-email recipient for this schedule? What's the SLA on response?

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is the trigger a calendar or a record event? | A record event with a delay is a scheduled path, not this skill (Choose The Right Time Primitive). | The primitive, with the reason the others were rejected. |
| What frequency does the requirement need? | A non-segment schedule offers Once, Daily or Weekly (Gotcha 8 and Decision Guidance). | Daily/Weekly fits, or escalation to scheduled Apex. |
| What is the worst-case record count on one run? | A recurring schedule amplifies weak scope (Gotcha 1). | Normal and peak volume, and the escalation threshold. |
| What marks a record as already processed? | Without a marker the same records are processed every run (Gotcha 2). | A flag, date, status or job-log rule used in the Start criteria. |
| Who receives the flow error email? | Recipients are the last modifier or the Apex Exception Email list (Gotcha 5). | A monitored mailbox and an owner with an SLA. |
| What happens after a failed run? | There is no documented automatic retry (Gotcha 6, UNVERIFIED). | Retry in the flow, a rerun procedure, or an accepted gap. |
| Do other schedules touch the same records or run at the same time? | Overlapping filters compete (Gotcha 7) and defaults pile up at 2am (Gotcha 9). | A time and filter plan across all scheduled flows. |

A proper configuration adds a bounded Start filter, an idempotency marker, a run log and a named error recipient, which "just scheduling it" leaves to chance.

## Core Concepts

The core design problem in scheduled flows is not the schedule itself. It is **bounded scope** plus **repeat-safe behavior**. A recurring automation that cannot explain which records it will touch, why it will touch them only once when appropriate, and when it should escalate out of Flow is not ready for production.

### Choose The Right Time Primitive

Three options; only one is a schedule-triggered flow:

| Primitive | When to use | When NOT |
|---|---|---|
| **Schedule-triggered flow** | Periodic scan of records matching time-based criteria independently of save events (nightly lease-renewal reminders, quarterly data cleanup) | When triggered from a record event — use scheduled path instead |
| **Scheduled Path on record-triggered flow** | Record event → wait N days → do work (send follow-up email 14d after Case created) | When there's no triggering record — schedule-triggered is the answer |
| **Batch Apex scheduled via System.schedule** | High-volume periodic processing, complex joins, large record sets | When the workload truly fits Flow's model (small set, simple operations, admin-maintainable) |

A wrong primitive choice is the most common scheduled-flow design error. If the requirement starts "when a record is X and Y days old", it's likely a scheduled path, not a schedule-triggered flow.

### Two Execution Modes: With Or Without An Object

The object in the Start element is **optional**, and that single choice changes the flow's entire execution model. Decide it before you draw anything else.

| | **Object selected** (+ criteria) | **No object selected** |
|---|---|---|
| What runs | The platform queries matching records and creates **one interview per record** | A single interview, once per scheduled run |
| `$Record` | Available — the flow's logic operates on one record | Not available |
| Batching | UNVERIFIED (2026-10-20): "interviews run in batches, default 200, settable 1–200 in the Start element" is not in the corpus | N/A — one interview |
| Get + Loop over the same object | **Anti-pattern** — the platform already iterates for you | Correct and expected |

The Object Reference defines a schedule-triggered flow as one that "launches at a specified time and frequency for each record that meets the flow criteria" (obj 264 L143558-143560). UNVERIFIED (2026-10-20): the Trailhead quotes this section used earlier (`$Record` available only when an object and criteria are set; `$Record` "actually refers to multiple records") and the object-less single-interview mode are not in the corpus; within any single interview `$Record` resolves to exactly one record, which is why you author for one.

The consequence most builders miss: **when an object is selected, you author the flow as if it handles exactly one record.** Adding a Get Records + Loop over that same object re-fetches the whole set inside every interview — N interviews × N iterations instead of N. The record scope belongs in the Start element's criteria, not in a Loop.

Conversely, an object-less schedule-triggered flow is just a scheduled job. There is no `$Record` and nothing iterates for you, so Get Records + Loop (or Transform / Collection Filter / Collection Sort) is the correct shape — a loop at the top of *this* mode is not an anti-pattern.

### Bounded Selection Comes First

The start criteria should narrow the job to a realistic set of records. Wide-open scans with complex branching downstream create both performance risk and support ambiguity. Good scheduled flows have clear filters, explicit stop conditions, and a manageable result set per run (UNVERIFIED 2026-10-20: "< 250 records per run" is a rule of thumb, not a documented limit).

Concrete selection criteria should combine:
- **Type/status filter** — `Status = 'Open' AND RecordType = 'Support'`.
- **Time-window filter** — `LastModifiedDate < TODAY - 30` or `CreatedDate = THIS_MONTH`.
- **Processing marker** — `Last_Reminded_Date__c != TODAY` (see idempotency below).

Filters that rely on computed fields or formula predicates WILL slow the scheduled query. Prefer indexed fields + date ranges + processing flags.

### Idempotency Matters In Recurring Automation

A recurring flow should be able to answer: "has this record already been processed for this job window?" Without idempotency, the same records get reminded, updated, or emailed every run — a frequent source of "the system spammed our customers" incidents.

Idempotency patterns:

| Pattern | Implementation | Tradeoff |
|---|---|---|
| Processing flag | `Processed_Today__c = true` set at end of processing; reset nightly | Simple; requires a reset job |
| Last-processed date | `Last_Processed_At__c = <timestamp>`; filter on `Last_Processed_At__c < TODAY` | No reset needed; field can stale |
| Status transition | Move record to a terminal status that the filter excludes | Cleanest; requires business-meaningful status |
| External lock | Write to a custom "job log" object; check before processing | Most robust; highest overhead |

### Flow Is Not Always The Final Execution Engine

When the recurring job becomes large (UNVERIFIED 2026-10-20: the 500-record figure is a rule of thumb, not a documented limit), computationally heavy (complex joins or multi-step transformations), or deeply iterative (nested loops with DML), the right answer may be to use the scheduled flow only as a lightweight orchestration layer or move the workload into Batch Apex entirely. The schedule does not justify using the wrong execution model.

**Signals Flow is no longer the right engine:**
- Record count per run > 500 (rule of thumb, UNVERIFIED 2026-10-20).
- CPU time approaches the limit (10,000 ms synchronous, 60,000 ms asynchronous, apexdev 264 L19782; scheduled Apex gets the synchronous figure, apexdev 264 L19739).
- The Flow has > 5 DML operations in a loop.
- The job needs to run more than daily to stay current (a non-segment schedule offers Once, Daily or Weekly; Hourly is listed for segment-triggered flows only, meta 264 L74076-74077, L74087-74092).
- Apex invocables are doing most of the real work (then just make it Batch Apex).

## Common Patterns

### Pattern 1: Narrow Nightly Follow-Up Flow

**When to use:** Recurring reminder or status update on a bounded slice of records.

**Structure** (object-selected mode — the platform iterates, so author for ONE record):
```text
Start: Daily at 2am
  Object: Case
  Criteria: Status = 'Pending' AND CreatedDate < TODAY - 7 AND Last_Reminded_Date__c != TODAY
Plan (runs once per matching record, $Record is that record):
  └── [Send Custom Notification OR Email Alert]  → addressed from $Record
  └── [Update Records: $Record.Last_Reminded_Date__c = TODAY]
  └── [Fault path: log + notify admin]
```

No Get Records. No Loop. The Start element's criteria *are* the record selection; adding a Get + Loop here would re-query every matching Case inside every interview.

**Object-less variant:** if you leave the object blank (say, to build a daily digest across several objects), the flow runs as one interview and you *do* need Get Records + Loop — plus an explicit `LIMIT` and a bulk Update after the loop, since nothing bounds the set for you.

**Why not the alternative:** A broad nightly sweep without clear selection becomes unpredictable and expensive.

### Pattern 2: Scheduled Flow As Lightweight Orchestrator

**When to use:** The timing belongs in Flow, but the heavy work belongs elsewhere.

**Structure:**
```text
Schedule: Weekly on Monday 3am
Plan:
  └── [Get Records: this week's candidates (narrow filter)]
  └── [Decision: record_count > threshold?]
       └── Yes → [Invocable Apex: kick off Batch Apex job with candidate IDs]
       └── No  → [Process inline via Loop + subflow]
```

Flow owns the timing and the "is this worth running today" check. Apex owns the work.

### Pattern 3: Replace Time-Based Workflow With Explicit Criteria

**When to use:** Legacy time-based Workflow Rule being migrated to Flow.

**Structure:** The Workflow Rule's "Evaluate every time a record is created or edited" + time-based action becomes a record-triggered flow's Scheduled Path (NOT a schedule-triggered flow) — because the behavior is record-event-driven, not portfolio-scan-driven.

For ACTUAL portfolio-scan automation being migrated from custom Apex scheduled jobs: evaluate whether it's really Flow-shaped first. Many scheduled Apex jobs exist because there was no good Flow primitive; now that scheduled flows + scheduled paths exist, some can migrate, but not all.

### Pattern 4: Run Log + Monitoring

**When to use:** Any production scheduled flow — this is not optional.

**Structure:**
```text
Start of run → [Create Records: Scheduled_Flow_Run__c with start_time + run_id]
... main work ...
End of run → [Update Records: the same log record with end_time + record_count + status]
Fault path → [Update Records: log record with status='failed' + fault_message]
```

A Scheduled_Flow_Run__c object (or equivalent) gives operations; the platform side is visible by querying `CronJobDetail` with `JobType = 6` (Scheduled Flow, obj 264 L86852):
- **Run history** — did the 3am job actually run last night?
- **Duration trends** — is the nightly job taking longer over time?
- **Failure visibility** — alert when `status='failed'` appears without alerting on every successful run.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Recurring job scans a bounded set of records daily or weekly | Schedule-triggered flow (Pattern 1) | Good fit for predictable recurring automation |
| Follow-up tied to a specific record save event | Scheduled path on record-triggered flow | Event-based, not portfolio-wide |
| Job volume or processing complexity high | Batch Apex or async code boundary | Flow is not the best execution engine for heavy batch work |
| Repeated reminders need duplicate prevention | Add idempotent markers or date fields | Recurring runs must know what's already processed |
| Selection criteria vague or unbounded | Redesign before scheduling | Schedule will amplify poor scope decisions |
| Job needs to run multiple times per day | Move to scheduled Apex or Batch Apex; `FlowSchedule.frequency` offers Once, Daily, Weekly, and Hourly/Monthly/Weekdays/Yearly/OnActivate are "for segment-triggered flows only" (meta 264 L74076-74096) | Flow scheduling granularity does not fit |
| Requires external callout per record | HTTP Action inline for small sets; async via Platform Events for large | Per-record callouts exhaust callout limits |

## Review Checklist

- [ ] Schedule primitive is correct (scheduled flow vs scheduled path vs Batch Apex).
- [ ] Start criteria narrow the candidate record set intentionally (no bare `Active=true`).
- [ ] Idempotent markers prevent duplicate tasks, emails, or updates across runs.
- [ ] Failure handling exists for every DML element (Pattern A from `flow/fault-handling`).
- [ ] Volume expectations were reviewed for normal and worst-case runs.
- [ ] Heavy work was escalated out of Flow when appropriate.
- [ ] Run log exists (custom object or equivalent) for operational monitoring.
- [ ] Error-email recipient is a monitored mailbox, not a single inactive admin.

## Recommended Workflow

1. Pick the time primitive: schedule-triggered flow, scheduled path, or scheduled Batch Apex (Core Concepts table); stop here if the trigger is a record event.
2. Decide object-selected or object-less mode, then write the Start criteria so the candidate set is bounded and excludes already-processed records.
3. Add the idempotency marker (flag, last-processed date, status transition, or job log) and a fault connector on every DML and action element.
4. Estimate normal and worst-case volume; if it crosses the escalation signals, keep Flow as the orchestrator and hand the work to Apex (Pattern 2).
5. Add the run log (Pattern 4) and confirm who receives flow error emails (Gotcha 5).
6. Run `python3 scripts/check_scheduled_flows.py --manifest-dir <flows dir>` and walk the Review Checklist; record deviations in `templates/scheduled-flows-template.md`.

---

## Salesforce-Specific Gotchas

1. **A recurring schedule amplifies weak selection logic** — broad filters turn into repeated large jobs quickly.
2. **Recurring automation needs duplicate prevention explicitly** — without markers, the same records can be processed on every run.
3. **Scheduled flows are not a substitute for true batch architecture** — the timing may fit, while the execution model does not.
4. **A record-event requirement may fit scheduled paths better** — choosing the wrong time primitive creates unnecessary complexity.
5. **Flow error emails go to the user who last modified the flow, or to the Apex Exception Email addresses when `enableFlowUseApexExceptionEmail` is true** (default false; meta 264 L120062-120065). UNVERIFIED (2026-10-20): the earlier "Process Automation user" recipient is not in the corpus. Verify the recipient is monitored.
6. **Scheduled flows DO NOT retry automatically on failure (UNVERIFIED 2026-10-20: not in the corpus)** — a failed run just... doesn't run. The next scheduled run tries fresh. Build retry logic into the flow if the business needs it.
7. **Two schedules overlapping can compete for records** — if two scheduled flows both filter "Status = Open", run one, the records transition, then the second flow sees different results than the first. Design mutually-exclusive filters or serialize schedules.
8. **Check the scheduled-job and run limits before adding the Nth schedule.** The documented cap of 100 scheduled jobs is for Apex (apexdev 264 L17151); UNVERIFIED (2026-10-20): whether scheduled flows count against it is not in the corpus. The Limits resource exposes `ScheduledFlowRunLimit`, "number of scheduled flow runs in a 24-hour period" (rest 264 L8172).
9. **Daily-at-2am is everyone's default** — UNVERIFIED (2026-10-20): scheduler peak load at 2am is not in the corpus. Spread actual scheduled times anyway; `startTime` is the time of day in the org's default time zone (meta 264 L74110-74111).
10. **Scheduled flows can't be paused mid-run (UNVERIFIED 2026-10-20: not in the corpus)** — once started, they run to completion or failure. Design the scope accordingly.

## Proactive Triggers

Surface these WITHOUT being asked:

- **Scheduled flow with no idempotency marker** → Flag as Critical. Will double-process on retry or next run.
- **Scheduled flow with unbounded start criteria (e.g. "Active = true" alone)** → Flag as Critical. Volume bomb waiting to happen.
- **Record-event requirement being built as scheduled flow instead of scheduled path** → Flag as High. Wrong primitive.
- **Scheduled flow > 500 records per run with no escalation plan** → Flag as High. Probably needs Batch Apex (500 is a rule of thumb, UNVERIFIED 2026-10-20).
- **No run log / monitoring surface for production scheduled flow** → Flag as High. Silent failure invitation.
- **Multiple scheduled flows on same object with overlapping filters** → Flag as Medium. Coordination risk.
- **Scheduled flow error email recipient is inactive** → Flag as Critical. Unseen failure pattern (recipient rules: Gotcha 5).
- **All scheduled flows set for 2am** → Flag as Low. Spread schedules (peak-load rationale UNVERIFIED 2026-10-20, Gotcha 9).

## Output Artifacts

| Artifact | Description |
|---|---|
| Scheduling design | Recommendation for schedule-triggered flow, scheduled path, or Apex |
| Scope and idempotency plan | Rules for bounded selection and duplicate prevention |
| Volume review findings | Risks around record set size, side effects, execution model choice |
| Run-log specification | Scheduled_Flow_Run__c schema + dashboard guidance |

## Related Skills

- **flow/flow-bulkification** — use when the recurring job may still break under shared limit pressure.
- **flow/fault-handling** — use when the main challenge is how background failures should be surfaced.
- **flow/record-triggered-flow-patterns** — use when a scheduled path on a record-triggered flow is the right primitive instead.
- **apex/batch-apex-patterns** — use when the workload has clearly crossed into true batch-processing territory.
- **standards/decision-trees/async-selection.md** — upstream decision tree for scheduled flow vs Batch Apex vs Queueable.
