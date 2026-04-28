---
name: flow-record-locking-and-contention
description: "Diagnose and prevent UNABLE_TO_LOCK_ROW + parent-record contention in record-triggered, scheduled, and screen flows by mapping the implicit lock chain and applying decouple patterns (Platform Events, Queueable handoff, Scheduled Paths). NOT for general flow bulkification — see flow-bulkification. NOT for fault-path catch logic — see flow-rollback-patterns."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
tags:
  - flow-record-locking-and-contention
  - concurrency
  - record-locking
  - unable-to-lock-row
  - parent-lock
  - platform-events
triggers:
  - "UNABLE_TO_LOCK_ROW from a flow"
  - "flow contention on parent record"
  - "Account lock when updating Opportunities"
  - "FOR UPDATE in flow Get Records"
  - "parallel transactions deadlock from record-triggered flow"
  - "child update locks parent in flow"
inputs:
  - "Flow XML or design + expected concurrent transaction volume"
  - "Object hierarchy (parent / child / Master-Detail relationships)"
  - "Per-day transaction profile (peak qps on the parent object)"
outputs:
  - "Lock-contention analysis + decouple recommendations"
  - "Refactored flow design (collect-then-update or asynchronous handoff)"
  - "Monitoring queries to detect future UNABLE_TO_LOCK_ROW occurrences"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-27
---

# Flow Record Locking And Contention

Activate when a record-triggered flow on a child object updates its parent under load, when fault emails surface `UNABLE_TO_LOCK_ROW`, or when migrating a serial Process Builder / Workflow Rule to Flow exposes contention the legacy serial engine had hidden. This skill maps the implicit lock chain Salesforce takes during DML, explains why Salesforce's automatic 10-retry exponential backoff sometimes still surfaces a fault, and prescribes the three decouple patterns that move work off the locked transaction.

---

## Before Starting

Gather this context before refactoring anything:

- **Does this flow update a parent (high blast radius)?** A flow that updates `Account` from an `Opportunity` after-save trigger locks the Account row for the duration of the entire transaction. Every concurrent Opportunity DML on the same Account will queue.
- **What's the concurrent transaction rate on the locked object?** Sustained writes to a few "hot" Accounts (national retailer, Amazon, etc.) is the classic contention shape. 5 transactions/sec on a 50-row hot-account table will produce daily UNABLE_TO_LOCK_ROW bursts.
- **Are children processed in bulk or one-at-a-time?** A single Update of 200 Opportunities locks the parent Account exactly once. A Loop iterating 200 times and calling Update inside the loop locks it 200 times — each iteration is its own contention window.
- **Is the relationship Master-Detail or Lookup?** Master-Detail propagates the lock to the master automatically. Lookup with `Reparent = true` also locks the new and old parent. Lookup without reparenting only locks if the field is on the update payload.
- **Does the flow change ownership?** Owner change locks the User row of both old and new owner — and for queue-owned records, the Group row of both queues. Mass reassignment is the #1 hidden contention source.
- **Has Salesforce already retried?** The platform retries DML up to 10 times with exponential backoff before surfacing the fault. If the fault is firing, contention is already severe.

---

## Core Concepts

### Concept 1 — Implicit locks taken by Salesforce DML

Every DML statement (including those issued by Flow Update/Create/Delete elements) takes a row-level write lock. Salesforce also takes additional **implicit locks** that are not obvious from the visible operation:

| Operation | Locks taken |
|---|---|
| Update Account | Account row + (if owner changes) old + new User/Queue rows |
| Update Opportunity | Opportunity row + parent Account row + parent Account's Owner row |
| Update OpportunityLineItem | OpportunityLineItem row + parent Opportunity row + parent Opportunity's Account row |
| Update child of Master-Detail | Child row + master row (always — no flag to disable) |
| Update child of Lookup with `reparentableMasterDetail=false` | Child row only (parent is touched only if reparenting) |
| Update User | User row + Role row + (if role changes) old + new Role rows |
| Insert into a queue-owned record | Queue's Group row |

The lock is held **for the entire transaction**, not just the duration of the DML — so a record-triggered flow that does Update Opportunity → Get Account → Update Account holds locks on the Opportunity, the original Account, the new Account (if owner changed), AND the owner User row from the moment of the first Update until the transaction commits or rolls back.

**Master-Detail vs Lookup is the single biggest contention lever.** Master-Detail always propagates; Lookup only propagates if the parent field is on the update payload OR the lookup is reparented.

### Concept 2 — UNABLE_TO_LOCK_ROW and the invisible 10-retry

When two transactions try to take the same row lock, the second one waits. If it waits longer than ~10 seconds, the platform raises `UNABLE_TO_LOCK_ROW: unable to obtain exclusive access to this record or 1 records: <Id>`.

What practitioners often miss:

- Salesforce **automatically retries** the failing DML up to **10 times with exponential backoff** before surfacing the error to the flow's fault path. By the time you see one fault email, dozens of retries already happened invisibly.
- The retry budget is per-transaction, not per-flow. A single contention burst can exhaust it for a whole batch.
- Flow surfaces the failure as a **fault** — and unlike Apex, Flow's default behavior is to **rollback the entire flow's DML** on an unhandled fault. Half-applied state is rare in Flow but the whole transaction is lost.
- If your flow has a fault path connector, control passes there. If not, the user sees a generic error, the admin gets a fault email, and the data change is lost.

### Concept 3 — Bulk vs single contention shape

The shape of your DML matters more than the volume:

- **Single bulk Update of 200 children** → one DML statement → one parent lock acquisition → one contention window. Fast, low-risk.
- **Loop with Update inside, 200 iterations** → 200 DML statements → 200 parent lock acquisitions → 200 contention windows. Slow, contention-heavy, and likely to hit the 150 DML governor before it hits the lock issue.
- **Two parallel bulk transactions on overlapping parents** → both queue on the parent lock; second one waits up to 10s, retries 10x, then faults.

The "collect-then-update" pattern (build a record collection inside the loop, then issue one Update on the collection after the loop) is the single most important refactor for flow contention.

### Concept 4 — `FOR UPDATE` and Flow's analog

Apex SOQL supports `FOR UPDATE` to acquire a lock at query time (`SELECT Id FROM Account WHERE Id = :acctId FOR UPDATE`). This pre-locks the row before subsequent DML, preventing a race where another transaction modifies it between query and update.

**Flow has no native `FOR UPDATE` syntax.** Get Records does not lock. The closest analog is to call an invocable Apex action that issues the `FOR UPDATE` query. In practice, this is rarely the right fix — `FOR UPDATE` reduces a lost-update race but does not reduce contention; if anything, it increases lock-hold time. Use it only when you have a true read-modify-write race, not when you have generic contention.

---

## Common Patterns

### Pattern 1 — Bulk Update Children Once (collect-then-update)

**When to use:** Any flow that iterates over a record collection and modifies child records that share a parent.

**How it works:**

```
[Get Records: Opportunities WHERE AccountId = :acctId]
        │
        ▼
[Loop over Opportunities]
        │
        ├── [Assignment: opp.Forecast_Reviewed__c = true]
        ├── [Assignment: oppCollection.add(opp)]   ← collect, do NOT Update here
        │
        ▼
[After Loop — Update Records: oppCollection]   ← single bulk Update
```

This locks the parent Account exactly once (when the bulk Update commits), regardless of how many Opportunities are in the collection.

**Why not the alternative:** A naive Update inside the Loop locks the Account on every iteration. With 200 Opportunities, that's 200 lock acquisitions in the same transaction — and you'll hit the 150 DML statement governor limit before iteration 151.

### Pattern 2 — Defer Parent Update via Platform Event

**When to use:** A child-record flow needs to update the parent (e.g., recalculate Account.Total_Pipeline__c when an Opportunity changes), but the parent has high concurrent write traffic.

**How it works:**

```
Record-triggered Flow on Opportunity (after-save):
        │
        ▼
[Update Opportunity: own field changes]   ← in-transaction
        │
        ▼
[Create Records: Opportunity_Changed__e Platform Event]
        │
        ▼
[End — original transaction commits, Opportunity lock released]

Subscriber Flow on Opportunity_Changed__e:
        │
        ▼
[Get Records: Account]
        │
        ▼
[Update Account: recalculated fields]
```

The publisher transaction never takes the Account lock. The subscriber runs in a separate transaction, after the publisher commits, with its own retry budget.

**Why not the alternative:** Synchronous Update Account inside the Opportunity flow holds the Account lock for the duration of the Opportunity transaction. Under load on a hot Account, every concurrent Opportunity update queues — and the slowest concurrent Opportunity flow becomes the bottleneck for all of them.

### Pattern 3 — Queueable Handoff for Long Locks

**When to use:** The work that needs the parent lock is non-trivial (e.g., recalculating across hundreds of related records, calling out to an external system) and would hold the lock for many seconds.

**How it works:**

1. Flow calls an invocable Apex action.
2. The action enqueues a `Queueable` (`System.enqueueJob(new RecalcAccountQueueable(acctIds))`) and returns immediately.
3. Flow ends; the parent is **never locked** in the user's transaction.
4. The Queueable runs in its own async transaction with its own governor + retry budget.

```apex
public class EnqueueRecalcAction {
    @InvocableMethod(label='Enqueue Account recalc')
    public static void enqueue(List<Id> acctIds) {
        System.enqueueJob(new RecalcAccountQueueable(acctIds));
    }
}
```

**Why not the alternative:** A synchronous flow holds locks for the user's full screen-time if it's a screen flow, or for the trigger-stack duration if it's record-triggered. Either is unacceptable when the work itself can take seconds.

### Pattern 4 — Scheduled Path on Record-Triggered Flow

**When to use:** The parent update doesn't need to happen in the same second as the child change. Acceptable lag: 1+ minute.

**How it works:** On the record-triggered flow, add a **Scheduled Path** that runs N minutes after the trigger. The parent update happens in that scheduled run, not in the user's transaction.

**Why not the alternative:** A scheduled path runs as the Automated Process user, in a separate transaction from the user-initiated update. It batches with other scheduled-path executions for the same flow, naturally amortizing lock contention.

---

## Decision Guidance

| Workload shape | Recommended pattern | Reason |
|---|---|---|
| Bulk DML on children of one shared parent | **Collect-then-Update** (single bulk Update after the loop) | Locks parent once instead of N times; avoids 150 DML governor |
| Child flow updates parent with high concurrent traffic | **Platform Event decouple** (publish in child flow, subscriber updates parent) | Publisher transaction releases parent lock immediately; subscriber retries independently |
| Parent recalc is heavy or makes callouts | **Queueable handoff** via invocable Apex action | User's transaction never takes the parent lock; async transaction has its own retry budget |
| Parent update can tolerate 1+ minute lag | **Scheduled Path** on the after-save flow | Runs as Automated Process user in a later transaction; naturally batches |
| Read-modify-write race on a counter/sequence field | Invocable Apex with `SELECT ... FOR UPDATE` | Pre-locks the row to prevent lost-update; only correct fix for true race conditions |
| Mass ownership reassignment | Schedule off-hours + chunk into batches of <100 | Owner change locks User/Queue/Role rows; off-hours minimizes user collision |
| One-at-a-time updates inside a loop are unavoidable (e.g., per-record validation differs) | Move the work to Apex + bulk pattern | Flow's loop-update shape is the worst case; don't try to fix it inside Flow |

---

## Recommended Workflow

1. **Identify the lock chain.** For the failing flow, list every Update/Create/Delete element and the implicit locks each takes (Account → User of owner → Group of queue, etc.). Use the table in Concept 1 as a checklist.
2. **Measure the contention.** Query `EventLogFile` (or check fault emails) for `UNABLE_TO_LOCK_ROW` over the last 7 days, grouped by record Id. Hot records will dominate the count. If you have no measurement, conservatively assume any flow that updates a frequently-accessed parent has contention.
3. **Classify the workload shape.** Is it (a) loop-update inside a bulk transaction, (b) parent update from a high-traffic child flow, (c) heavy/slow parent recalc, or (d) ownership reassignment? Each maps to a specific pattern in the table above.
4. **Apply the pattern.** Refactor to collect-then-update, or insert the Platform Event boundary, or hand off to a Queueable. Reference `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` for the canonical record-triggered shape.
5. **Add a fault path** at every DML element. Even with retries, contention can still surface; route the fault to `Integration_Log__c` (see `flow-error-monitoring`) so future occurrences are visible.
6. **Test under load.** Use Anonymous Apex to fire 10–20 parallel DML against the same parent (using `@future` jobs to genuinely run in parallel). Verify the refactored flow does not surface UNABLE_TO_LOCK_ROW.
7. **Monitor going forward.** Subscribe to a weekly report of `UNABLE_TO_LOCK_ROW` from the EventLogFile or your central log object. Treat new occurrences as a regression signal.

---

## Review Checklist

- [ ] Every Update/Create inside a Loop has been refactored to collect-then-update (single DML after loop).
- [ ] Flows that update a parent from a child-record trigger have been evaluated for Platform Event decouple.
- [ ] Heavy/slow parent recalcs are handed off to Queueable Apex, not synchronous in the user's transaction.
- [ ] Ownership changes are batched off-hours when affecting >100 records.
- [ ] Every DML element in the flow has a fault path that logs to a central error log.
- [ ] Master-Detail vs Lookup decisions have been documented — Master-Detail always propagates the lock.
- [ ] The flow has been load-tested with parallel DML against the same parent record.
- [ ] No `FOR UPDATE` invocable Apex is used as a generic "fix" for contention (it's only correct for true read-modify-write races).
- [ ] The refactored flow does not exceed 100 DML statements or 150 SOQL queries per transaction.

---

## Salesforce-Specific Gotchas

1. **Child Update locks the parent automatically** — Updating a single Opportunity locks the parent Account row for the entire transaction. There is no flag to disable this, no `WITHOUT_PARENT_LOCK` keyword. The only escape is to decouple via Platform Event, Queueable, or Scheduled Path.
2. **Queue-owned records lock the Group row on every insert/update** — If a Case record-triggered flow inserts a Task into a queue, the queue's Group row is locked. With many concurrent Cases routing into the same support queue, contention concentrates on that single Group row, not on the Cases themselves.
3. **Master-Detail reparenting locks both old and new master** — Reassigning a Master-Detail child takes write locks on both the old parent, the new parent, and the child itself. With deep hierarchies (LineItem → Opportunity → Account), reparenting can lock 4+ rows simultaneously across two object trees.
4. **The 10-retry exponential backoff is invisible** — Salesforce silently retries the failing DML up to 10 times. Your fault email represents the 11th attempt. By the time you see one fault, hundreds of retries may have happened across other concurrent transactions; system load is already significantly elevated.
5. **Flow's automatic rollback masks partial state** — Unlike Apex (where DML between savepoints can persist), an unhandled flow fault rolls back **the entire flow's DML** to the start of the trigger. This makes contention failures invisible: there's no "half-committed" record to spot — just a missing record that should exist. Always log to a fault path.
6. **`Get Records` does not take a lock** — Practitioners assume reading a record before updating it pre-locks it. It doesn't. The lock is only acquired at the moment of the Update DML. A race between Get and Update is possible; only `FOR UPDATE` (via invocable Apex) closes it.
7. **Platform Event subscriber flows still take locks** — Decoupling via Platform Event moves the work to a separate transaction, but that transaction still takes parent locks when it updates. The benefit is the publisher transaction completes fast; the subscriber's contention is independent and self-throttling (events batch).
8. **Skew amplifies contention** — Account skew (>10k child Opportunities under one Account) means even a single Opportunity update takes longer to acquire the parent lock, because the parent row is touched constantly. Skew assessment is a precondition to lock-contention assessment.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Lock-chain map | A per-flow document listing every DML element and the implicit locks it takes (parent, owner, queue, role) |
| Refactored flow | The original flow restructured per the appropriate pattern (collect-then-update, Platform Event, Queueable, Scheduled Path) |
| Fault-path log entries | Wired-in logging to `Integration_Log__c` (or equivalent) for every DML element, so future contention is observable |
| Load-test script | Anonymous Apex that fires N parallel `@future` jobs against the same parent record, verifying the refactor holds under contention |
| Monitoring query | A SOQL or EventLogFile query that surfaces `UNABLE_TO_LOCK_ROW` occurrences per week, grouped by flow + record Id |

---

## Related Skills

- `skills/flow/flow-bulkification` — the foundational discipline that makes collect-then-update the natural shape; activate first if the flow has any Loop+DML pattern.
- `skills/flow/flow-rollback-patterns` — what happens to the rest of the flow when a DML faults; pairs with this skill's fault-path guidance.
- `skills/apex/callout-and-dml-transaction-boundaries` — when the parent update involves callouts; transaction-boundary discipline is critical.
- `standards/decision-trees/integration-pattern-selection.md` — when the decouple pattern should escalate to Platform Events vs Pub/Sub vs CDC.
- `standards/decision-trees/async-selection.md` — choosing between Queueable, `@future`, Batch, and Platform Events for the handoff target.
- `skills/flow/flow-error-monitoring` — wiring fault paths to a central log so future contention is visible.

---

## Official Sources Used

- Salesforce Help — Record Locking Overview: https://help.salesforce.com/s/articleView?id=platform.record_locking_overview.htm
- Salesforce Help — What Records Are Locked: https://help.salesforce.com/s/articleView?id=platform.record_locking_locks.htm
- Apex Developer Guide — Locking Statements (`FOR UPDATE`): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_locking_statements.htm
- Apex Developer Guide — Locking Records: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_locking_records.htm
- Salesforce Help — Flow Considerations and Limits: https://help.salesforce.com/s/articleView?id=sf.flow_considerations.htm
- Salesforce Knowledge — Resolving UNABLE_TO_LOCK_ROW: https://help.salesforce.com/s/articleView?id=000385621&type=1
- Salesforce Architects — Asynchronous Processing Patterns: https://architect.salesforce.com/decision-guides/async/
