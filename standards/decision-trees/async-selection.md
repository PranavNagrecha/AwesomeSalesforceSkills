# Decision Tree — Async Apex Selection

Which async mechanism should I use?
**`@future` · Queueable · Batch Apex · Schedulable · Platform Events · Scheduled Flow · Async SOQL / Bulk API**

Use this tree any time the work cannot complete inside the triggering
synchronous transaction.

---

## Strategic defaults

1. **Queueable** is the modern default for "run this later" work. It supports
   chaining, state (non-static members are serialized), interfaces
   (`Finalizer`, `AllowsCallouts`), and Apex-style testing.
2. **Batch Apex** remains the only choice for jobs > 50k records or > 5 minutes.
3. **`@future`** is legacy. Prefer Queueable unless you specifically need
   the separate-transaction-for-callout-from-trigger behavior and nothing else.
4. **Schedulable** is only for clock-based kickoff. Its body should delegate
   to Queueable/Batch immediately — don't put real work in `execute(SchedulableContext)`.
5. **Platform Events** decouple publisher and subscriber — use when the
   consumer is not part of the same business transaction.

---

## Core capability matrix

| Mechanism | Volume ceiling | Chaining | Callouts | State preserved | Monitoring | Start latency |
|---|---|---|---|---|---|---|
| `@future` | No row ceiling of its own — arguments must be primitives, arrays of primitives, or collections of primitives (no sObjects), so you pass Ids and re-query | No | Yes (`(callout=true)`) | No — only primitives as args | Apex Jobs | 0–minutes |
| Queueable | 50,000 rows is a practical guide, not a platform limit — the real ceiling is the async transaction (50,000 rows queried, 60 s CPU, 12 MB heap) | Yes (chain inside `execute()`) | Yes (`AllowsCallouts`) | Yes (member variables) | Apex Jobs | 0–minutes |
| Batch Apex | 50 million rows returned by `Database.QueryLocator` | `Database.executeBatch(next)` in `finish()` | Yes (`Database.AllowsCallouts`) | `Database.Stateful` | Apex Jobs + Bulk API Monitoring | seconds–minutes |
| Schedulable | n/a (delegates out) | n/a | n/a | No | Scheduled Jobs | cron-based |
| Platform Event | 250,000 published per hour (EE / PE / UE); 50,000/hour in Developer Edition. Delivery is the tighter allocation: 25,000 events per 24 h in EE, 50,000 in PE/UE | Subscribe → Queueable | Yes in subscriber | n/a | Event Monitoring | ~seconds |
| Schedule-triggered Flow | 250,000 interviews per 24 h org-wide, or user licenses × 200, whichever is greater — one interview per queried record | No | Limited | No | Paused/Waiting Interviews | cron-based |
| Async SOQL / Bulk API | billions | No | n/a | n/a | Bulk API job UI | seconds–minutes |

Note: ceilings shift with org edition and release, and the Platform Event row
above is the clearest case — the headline number is 5× different between
Developer Edition and production. Always confirm against the current
"Execution Governors and Limits" and "Platform Event Allocations" docs before
quoting one at a customer.

---

## Decision tree

```
START: Work cannot run in the synchronous transaction.

Q1. How many records / how long?
    ├── < 2,000 records, < 60s          → Q2
    ├── 2k – 50k, < 5 min                → Q5 (Queueable)
    ├── > 50k OR > 5 min                 → Q8 (Batch Apex)
    └── Truly massive, one-off ETL       → Bulk API 2.0 (async SOQL / external job)

Q2. Is the trigger a clock or an event?
    ├── Clock (cron)                     → Schedulable wrapper that enqueues Queueable
    ├── Record change in this org        → Q3
    └── Another transaction in this org  → Platform Event publish → subscriber

Q3. Does the work need to call an HTTP endpoint?
    ├── Yes  → Q4
    └── No   → Q5

Q4. Is the callout part of the user's immediate feedback?
    ├── Yes — user waits for response     → Continuation (stay synchronous)
    ├── No — user just needs it done soon → Queueable (AllowsCallouts)
    └── Callout AND large data processing → Batch Apex (Database.AllowsCallouts) — start(), execute() and finish() may each make up to 100 callouts

Q5. Do you need state between invocations (accumulators, retry counters)?
    ├── Yes — a few values        → Queueable with member variables
    ├── Yes — scoped per record   → Pass state in the Queueable constructor
    └── No                        → Queueable or @future (prefer Queueable)

--- The questions below are follow-ups and alternate entry points. Nothing in
--- Q1–Q5 routes into them; ask them on their own when the situation applies.

Q6. Is this replacing a legacy @future method?
    ├── Yes and it needs callouts OR chaining → Convert to Queueable
    ├── Yes but it's a one-line primitive     → Leave it, prioritize higher-value migrations
    └── No                                    → N/A

Q7. Does downstream work need to resume even if the main job fails?
    ├── Yes → Use a Queueable Finalizer to dispatch the compensating action
    └── No  → Normal try/catch is sufficient

Q8. Batch Apex. Which scope size? (default 200; max 2,000 when start()
    returns a QueryLocator)
    ├── Aggregation (group by) required                 → scope=1 (aggregate in finish())
    ├── Light per-record work, no callouts              → scope=200 (default)
    ├── Heavy per-record work or callouts               → scope=50–100
    └── External API rate-limited                       → scope=10–50 + delay via chained Queueable

Q9. Does the job need to run on a schedule AND be re-runnable ad hoc?
    ├── Yes → Schedulable invokes Batch/Queueable; expose a static `runNow()` helper for manual trigger
    └── No  → Direct Batch/Queueable only

Q10. Cross-app fan-out (1 event → many consumers inside the org)?
     ├── Yes → Platform Event; subscribers in Apex trigger or Flow
     └── No  → Keep it as a direct service call

Q11. Cross-system fan-out (subscriber is NOT Salesforce)?
     ├── Yes → Platform Event + Pub/Sub API gRPC subscriber
     └── No  → See Q10

Q12. User kicked off the job and needs progress feedback?
     ├── Yes → Queueable chain with status written to a custom "Job_Status__c" object read by an LWC poller
     └── No  → Apex Jobs UI is enough
```

---

## `@future` vs Queueable — pick Queueable unless

| Keep `@future` when | Move to Queueable when |
|---|---|
| Method is already stable, infrequently touched | You need chaining |
| You only pass primitives as arguments | You need to preserve non-primitive state |
| You rely on the "fire and forget from trigger" idiom | You need a Finalizer for retry/cleanup |
| You depend on its isolation from the parent transaction | You need to monitor progress across the chain |

---

## Batch Apex — the must-do checklist

- [ ] `scope` is explicit (default 200 is rarely the right number for production).
- [ ] `start()` query is selective — otherwise it hits `TOTAL_ROWS_EXCEEDED`.
- [ ] Callout budget is understood: with `Database.AllowsCallouts`, `start()`, `execute()` and `finish()` may each make up to 100 callouts. Rate-limited endpoints usually want far fewer — that is a design choice, not the platform limit.
- [ ] State is declared `Database.Stateful` OR state is explicitly not needed.
- [ ] `finish()` is idempotent — batches can be restarted.
- [ ] Errors logged via `ApplicationLogger` with batch ID correlation.
- [ ] Test class runs a batch of **exactly 200** records inside `Test.startTest()/stopTest()` (the boundary that actually runs `finish()`).

---

## Platform Event decision points

Use a Platform Event when all three are true:

1. Multiple consumers may want the notification (fan-out).
2. Consumers can tolerate "at-least-once" delivery semantics.
3. The producer does NOT need to block on consumer success.

Do NOT use a Platform Event when:

- The "event" is just one service calling another in the same org — direct
  service call is simpler.
- Ordering across partitions matters — PE replay semantics do not guarantee
  strict cross-topic ordering.
- You need transactional rollback across publisher + subscriber.

---

## Anti-patterns

- **`@future` chain disguised as Queueable.** Enqueueing from
  `Queueable.execute` is supported. Developer Edition and Trial orgs cap the
  chain at a stack depth of 5 (the parent plus four children); other editions
  have no documented cap — which means a runaway chain fails in production
  rather than in your scratch org. Always check for the terminating condition.
- **Schedulable with real logic in `execute()`.** You cannot test it at scale
  and cannot re-run ad hoc. Always wrap a Queueable/Batch.
- **Batch Apex for < 10k records.** Overkill, and batch start-up latency
  dominates total runtime. Queueable is faster.
- **Platform Event publish inside a trigger with no `EventBus.publish()`
  result check.** Partial failures go silent.
- **Missing Finalizer on a long Queueable chain.** First failure kills the
  whole chain silently.
- **Scheduled Flow doing work a Batch should do.** Scheduled Flow has lower
  governor ceilings and no retry semantics.

---

## Related skills

- `apex/async-apex` — Queueable, @future, async patterns
- `apex/batch-apex-patterns` — Batch design with scope + state guidance
- `apex/apex-queueable-patterns` — chaining, Finalizers, state
- `apex/apex-scheduled-jobs` — Schedulable wrapper and cron
- `integration/platform-events-integration` — fan-out and subscribers
- `integration/pub-sub-api-patterns` — external gRPC subscribers
- `integration/change-data-capture-integration` — replication vs event fan-out

## Related templates

- `templates/apex/HttpClient.cls` — use from Queueable with `AllowsCallouts`
- `templates/apex/ApplicationLogger.cls` — correlate logs across the async chain via `Request_Id__c`
- `templates/apex/tests/BulkTestPattern.cls` — the 200-record pattern for Batch tests

## Official Sources Used

- Apex Developer Guide — Execution Governors and Limits (100/200 SOQL, 150 DML, 10,000 DML rows, 10 s / 60 s CPU, 6 MB / 12 MB heap, 100 callouts, 120 s cumulative callout timeout): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide — Invoking Future Methods ("The specified parameters must be primitive data types, arrays of primitive data types, or collections of primitive data types"): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_invoking_future_methods.htm
- Apex Developer Guide — Queueable Apex (50 jobs per synchronous transaction, 1 from an async transaction; stack depth of 5 for Developer Edition and Trial orgs): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
- Apex Developer Guide — Use Batch Apex (default scope 200, max 2,000 with a QueryLocator; 50 million rows per QueryLocator; "The start, execute, and finish methods can implement up to 100 callouts each"; 5 concurrent batch jobs; 250,000 executions per 24 h or licenses × 200): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface.htm
- Platform Events Developer Guide — Platform Event Allocations (250,000 published per hour in EE/PE/UE, 50,000 in Developer Edition; 25,000 delivered per 24 h in EE, 50,000 in PE/UE): https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
- Salesforce Help — Schedule-Triggered Flow Considerations (250,000 interviews per 24 h, or user licenses × 200, whichever is greater): https://help.salesforce.com/s/articleView?language=en_US&id=platform.flow_considerations_trigger_schedule.htm&type=5
- Apex Developer Guide — Asynchronous Callout Limits (Continuation: 120 s max timeout, 3 parallel callouts, 3 chained callouts, 1 MB max HTTP response): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_continuation_limits.htm
