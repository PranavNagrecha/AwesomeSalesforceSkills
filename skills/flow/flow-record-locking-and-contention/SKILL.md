---
name: flow-record-locking-and-contention
description: "Diagnose and prevent UNABLE_TO_LOCK_ROW + parent-record contention in record-triggered, scheduled, and screen flows by mapping the implicit lock chain and applying decouple patterns (Platform Events, Queueable handoff, Scheduled Paths). NOT for general flow bulkification — see flow-bulkification — use apex/record-locking-and-contention."
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
  - "UNABLE_TO_LOCK_ROW row lock contention"
inputs:
  - "Flow XML or design + expected concurrent transaction volume"
  - "Object hierarchy (parent / child / Master-Detail relationships)"
  - "Per-day transaction profile (peak qps on the parent object)"
outputs:
  - "Lock-contention analysis + decouple recommendations"
  - "Refactored flow design (collect-then-update or asynchronous handoff)"
  - "Monitoring queries to detect future UNABLE_TO_LOCK_ROW occurrences"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Flow Record Locking And Contention

Activate when a record-triggered flow on a child object updates its parent under load, when fault emails surface `UNABLE_TO_LOCK_ROW`, or when migrating a serial Process Builder / Workflow Rule to Flow exposes contention the legacy serial engine had hidden. This skill maps the implicit lock chain Salesforce takes during DML, explains the documented 10-second lock-wait timeout (apexdev 264 L9395-9398) that produces the fault, and prescribes the three decouple patterns that move work off the locked transaction.

---

## Before Starting

Gather this context before refactoring anything:

- **Does this flow update a parent (high blast radius)?** A flow that updates `Account` from an `Opportunity` after-save trigger locks the Account row for the duration of the entire transaction. Every concurrent Opportunity DML on the same Account will queue. Changing a child record contending on its parent is documented: "When you perform a DML operation on one record, related records are locked in addition to the record in question" (apexdev 264 L9409), and the Large Data Volumes guide's "Minimizing parent record-locking conflicts" advice — "When changing child records, group them by parent ... to minimize locking conflicts" (ldv 264 L894-896). UNVERIFIED (2026-10-20): the Opportunity → Account case by name is Help-sourced.
- **What's the concurrent transaction rate on the locked object?** Sustained writes to a few "hot" Accounts (national retailer, Amazon, etc.) is the classic contention shape. 5 transactions/sec on a 50-row hot-account table will produce daily UNABLE_TO_LOCK_ROW bursts (an illustration, not a measured threshold; UNVERIFIED (2026-10-20)).
- **Are children processed in bulk or one-at-a-time?** A single Update of 200 Opportunities is one DML statement; a Loop iterating 200 times and calling Update inside the loop is 200 DML statements (apexdev 264 L19757 caps them at 150 synchronously). UNVERIFIED (2026-10-20): the count of parent lock acquisitions per statement is not in the corpus.
- **Is the relationship Master-Detail or Lookup?** UNVERIFIED (2026-10-20): that Master-Detail propagates the lock to the master automatically, and that a Lookup locks the parent only when reparented or when the field is on the update payload, are Help-sourced; the corpus has no lock-propagation table. The documented reparenting switch is `reparentableMasterDetail`, a field of master-detail relationships on custom objects, default false (api_meta 264 L45820-45822).
- **Does the flow change ownership?** The Bulk API 2.0 guide lists "Updating ownership for records with private sharing", "Creating users" and "Updating user roles" among operations "likely to cause lock contention" (api_asynch 264 L2637-2639). UNVERIFIED (2026-10-20): that an owner change locks the User row of both old and new owner, and the Group row of both queues for queue-owned records, and that mass reassignment is the #1 hidden source, are not in the corpus.
- **How long was the lock held?** A process "waits a maximum of 10 seconds for the lock to be released"; past that a `QueryException` is thrown for a `FOR UPDATE` query and a `DmlException` for an update (apexdev 264 L9395-9398). UNVERIFIED (2026-10-20): the `UNABLE_TO_LOCK_ROW` code and message text are not in the corpus outside the parallel-test note (apexdev 264 L41979). There is no automatic platform retry for synchronous DML — the fault is the first and only attempt's outcome. So the question to ask is what held the lock for a full 10 seconds, not how many retries were burned.

---

## Core Concepts

### Concept 1 — Implicit locks taken by Salesforce DML

Every DML statement (including those issued by Flow Update/Create/Delete elements) takes a row-level write lock. Salesforce also takes additional **implicit locks** that are not obvious from the visible operation: "When you perform a DML operation on one record, related records are locked in addition to the record in question" (apexdev 264 L9409). The Large Data Volumes guide adds that changing child records causes parent record-locking conflicts (ldv 264 L894-896). UNVERIFIED (2026-10-20): the per-relationship rows of the table below are Help-sourced (the record-locking pages are not in the corpus); the Bulk API 2.0 guide confirms only that creating users, updating ownership for records with private sharing, updating user roles and updating territory hierarchies are likely to cause lock contention (api_asynch 264 L2637-2640), and that an AccountTeamMember create or update locks its Account (L2644-2645).

| Operation | Locks taken |
|---|---|
| Update Account | Account row + (if owner changes) old + new User/Queue rows |
| Update Opportunity | Opportunity row + parent Account row + parent Account's Owner row |
| Update OpportunityLineItem | OpportunityLineItem row + parent Opportunity row + parent Opportunity's Account row |
| Update child of Master-Detail | Child row + master row (always — no flag to disable) |
| Update child of Lookup | UNVERIFIED (2026-10-20): the earlier row keyed this on `reparentableMasterDetail=false`, but that field belongs to master-detail relationships (api_meta 264 L45820-45822); the corpus does not say when a Lookup parent is locked |
| Update User | User row + Role row + (if role changes) old + new Role rows |
| Insert into a queue-owned record | Queue's Group row |

The lock is held **for the entire transaction** ("The lock gets released when the transaction completes", apexdev 264 L9383, for `FOR UPDATE`; other clients "have to wait until the transaction completes", L9392-9394), not just the duration of the DML — so a record-triggered flow that does Update Opportunity → Get Account → Update Account holds locks on the Opportunity, the original Account, the new Account (if owner changed), AND the owner User row from the moment of the first Update until the transaction commits or rolls back.

**Master-Detail vs Lookup is the single biggest contention lever.** UNVERIFIED (2026-10-20): "Master-Detail always propagates; Lookup only propagates if the parent field is on the update payload OR the lookup is reparented" is Help-sourced and not in the corpus.

### Concept 2 — UNABLE_TO_LOCK_ROW and the 10-second lock wait

When two transactions try to take the same row lock, the second one waits. Salesforce documents a maximum wait of **10 seconds** (apexdev 264 L9395-9398); if the lock is not released in that window an exception is thrown. UNVERIFIED (2026-10-20): the text `UNABLE_TO_LOCK_ROW: unable to obtain exclusive access to this record or 1 records: <Id>` is not in the corpus.

What practitioners often miss:

- The 10 seconds is a **wait**, not a retry loop. There is no documented automatic platform-level retry for synchronous DML lock acquisition — no exponential backoff, no silent second attempt. The fault you see is the outcome of the one attempt that waited and gave up. (Bulk API and platform-event subscribers *do* have their own documented retry semantics, which is where the "automatic retry" folklore comes from — the Bulk API 2.0 job `retries` property counts attempts to save results "due to a problem, such as a lock contention" (api_asynch 264 L1995-1997), and an Apex platform-event trigger retries only when it throws `EventBus.RetryableException`, up to 10 runs (the initial run plus 9 retries, platform_events 264 L3268). Those are different mechanisms, in different transactions.)
- Because there is no retry, a single fault email is evidence of **one** transaction that waited 10 seconds — not evidence of a system-wide retry storm. Judge severity from fault *frequency* and from how long the blocking transaction held the lock, not from an imagined retry count.
- Ten seconds is a long time. If a lock is held that long, something in the blocking transaction — a callout, a slow trigger, a large loop — is the real target of the fix.
- Flow surfaces the failure as a **fault** — and unlike Apex, Flow's default behavior is to **rollback the entire flow's DML** on an unhandled fault. Half-applied state is rare in Flow but the whole transaction is lost. UNVERIFIED (2026-10-20): the corpus describes no flow fault, rollback or fault-email behavior for lock timeouts; for Apex it says a trigger that does not complete successfully has its database changes rolled back (apexdev 264 L9429-9430).
- If your flow has a fault path connector, control passes there. If not, the user sees a generic error, the admin gets a fault email, and the data change is lost. UNVERIFIED (2026-10-20): same as above.

### Concept 3 — Bulk vs single contention shape

The shape of your DML matters more than the volume:

- **Single bulk Update of 200 children** → one DML statement → one parent lock acquisition → one contention window. Fast, low-risk.
- **Loop with Update inside, 200 iterations** → 200 DML statements → 200 parent lock acquisitions (UNVERIFIED (2026-10-20): the acquisition count) → 200 contention windows. Slow, contention-heavy, and certain to hit the 150-statement DML limit (apexdev 264 L19757) before iteration 151.
- **Two parallel bulk transactions on overlapping parents** → both queue on the parent lock; the second one waits up to 10 seconds (apexdev 264 L9395-9398), then faults. There is no retry (the earlier text said "retries 10x", which contradicted Concept 2).

The "collect-then-update" pattern (build a record collection inside the loop, then issue one Update on the collection after the loop) is the single most important refactor for flow contention.

### Concept 4 — `FOR UPDATE` and Flow's analog

Apex SOQL supports `FOR UPDATE` to acquire a lock at query time (`SELECT Id FROM Account WHERE Id = :acctId FOR UPDATE`; apexdev 264 L9384-9386). This pre-locks the row before subsequent DML, preventing a race where another transaction modifies it between query and update (L9399-9403). Documented limits: you can't use `ORDER BY` in a locking query (L9388); other clients can still query a locked record (L9394); and "The record locks that are obtained in Apex via FOR UPDATE clause are automatically released when making callouts" (L9404-9408), so a callout after a `FOR UPDATE` query drops the lock. The runtime locks parents before children and locks records of one type in ID order (L9436-9437).

**Flow has no native `FOR UPDATE` syntax.** Get Records does not lock. UNVERIFIED (2026-10-20): neither statement is made in the corpus; the Apex Developer Guide says only that you embed `FOR UPDATE` after an inline SOQL statement to lock (apexdev 264 L9384). The closest analog is to call an invocable Apex action that issues the `FOR UPDATE` query. In practice, this is rarely the right fix — `FOR UPDATE` reduces a lost-update race but does not reduce contention; if anything, it increases lock-hold time (the lock lasts until the transaction completes, apexdev 264 L9383). Use it only when you have a true read-modify-write race, not when you have generic contention.

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

**Why not the alternative:** A naive Update inside the Loop locks the Account on every iteration. With 200 Opportunities, that's 200 lock acquisitions in the same transaction — and you'll hit the 150 DML statement limit before iteration 151 (apexdev 264 L19757).

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

The publisher transaction never updates the Account (the Opportunity update itself still locks related records, apexdev 264 L9409, ldv 264 L894-896; see Concept 1). A platform-event-triggered flow "runs asynchronously in a separate transaction from the transaction that published the event message" (platform_events 264 L2187-2188). Whether it runs after the publisher commits depends on the event's publish behavior: with the default Publish Immediately "a subscriber can sometimes receive the event message before the data is committed"; choose Publish After Commit when the subscriber needs committed data (platform_events 264 L346-351). A flow subscriber receives batches of up to 200 messages (L2185). UNVERIFIED (2026-10-20): the "own retry budget" the earlier text claimed; a flow subscriber has no documented retry (see `references/examples.md`).

**Why not the alternative:** Synchronous Update Account inside the Opportunity flow holds the Account lock for the duration of the Opportunity transaction. Under load on a hot Account, every concurrent Opportunity update queues — and the slowest concurrent Opportunity flow becomes the bottleneck for all of them.

### Pattern 3 — Queueable Handoff for Long Locks

**When to use:** The work that needs the parent lock is non-trivial (e.g., recalculating across hundreds of related records, calling out to an external system) and would hold the lock for many seconds.

**How it works:**

1. Flow calls an invocable Apex action.
2. The action enqueues a `Queueable` (`System.enqueueJob(new RecalcAccountQueueable(acctIds))`) and returns immediately.
3. Flow ends; the parent is **never locked** in the user's transaction.
4. The Queueable runs in its own async transaction with its own governor limits (asynchronous limits column, apexdev 264 L19736-19790); it has no documented automatic retry.

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

**How it works:** On the record-triggered flow, add a **Scheduled Path** that runs N minutes after the trigger (`offsetNumber` and `offsetUnit`, api_meta 264 L74126-74146), or an asynchronous path (`pathType` `AsyncAfterCommit`, "runs asynchronously after a save", api_meta 264 L74148-74151; post-commit logic, apexdev 264 L15692). The parent update happens in that run, not in the user's transaction.

**Why not the alternative:** The path runs in a separate transaction from the user-initiated update, and a scheduled path batches interviews, up to `maxBatchSize` 1 to 200 with a default of 200 (api_meta 264 L74123-74124). UNVERIFIED (2026-10-20): that it runs as the Automated Process user, and that batching "naturally amortizes" lock contention, are not in the corpus; for platform-event-triggered flows the interview runs as the user who published the event and only the debug log appears under Automated Process (platform_events 264 L2190-2192).

---

## Decision Guidance

| Workload shape | Recommended pattern | Reason |
|---|---|---|
| Bulk DML on children of one shared parent | **Collect-then-Update** (single bulk Update after the loop) | Locks parent once instead of N times; avoids 150 DML governor |
| Child flow updates parent with high concurrent traffic | **Platform Event decouple** (publish in child flow, subscriber updates parent) | Publisher transaction never updates the parent; the subscriber runs in a separate transaction (platform_events 264 L2187-2188); choose Publish After Commit when it needs committed data (L349-351); a flow subscriber has no documented retry |
| Parent recalc is heavy or makes callouts | **Queueable handoff** via invocable Apex action | User's transaction never takes the parent lock; the async transaction has its own limits |
| Parent update can tolerate 1+ minute lag | **Scheduled Path** on the after-save flow | Runs in a later transaction; batches interviews (api_meta 264 L74123-74124) |
| Read-modify-write race on a counter/sequence field | Invocable Apex with `SELECT ... FOR UPDATE` | Pre-locks the row to prevent lost-update; only correct fix for true race conditions |
| Mass ownership reassignment | Schedule off-hours + chunk into batches of <100 | Owner change locks User/Queue/Role rows; off-hours minimizes user collision |
| One-at-a-time updates inside a loop are unavoidable (e.g., per-record validation differs) | Move the work to Apex + bulk pattern | Flow's loop-update shape is the worst case; don't try to fix it inside Flow |

---

## Recommended Workflow

1. **Identify the lock chain.** For the failing flow, list every Update/Create/Delete element and the implicit locks each takes (Account → User of owner → Group of queue, etc.). Use the table in Concept 1 as a checklist.
2. **Measure the contention.** Query `EventLogFile` (or check fault emails) for `UNABLE_TO_LOCK_ROW` over the last 7 days, grouped by record Id. UNVERIFIED (2026-10-20): that an `EventLogFile` type records this error is not in the corpus. Hot records will dominate the count. If you have no measurement, conservatively assume any flow that updates a frequently-accessed parent has contention.
3. **Classify the workload shape.** Is it (a) loop-update inside a bulk transaction, (b) parent update from a high-traffic child flow, (c) heavy/slow parent recalc, or (d) ownership reassignment? Each maps to a specific pattern in the table above.
4. **Apply the pattern.** Refactor to collect-then-update, or insert the Platform Event boundary, or hand off to a Queueable. Reference `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` for the canonical record-triggered shape.
5. **Add a fault path** at every DML element. Contention can still surface after any refactor; route the fault to `Integration_Log__c` (see `flow-error-monitoring`) so future occurrences are visible.
6. **Test under load.** Use Anonymous Apex to fire 10–20 parallel DML against the same parent (using `@future` jobs to genuinely run in parallel; UNVERIFIED (2026-10-20): the corpus does not describe `@future` jobs running in parallel). Verify the refactored flow does not surface UNABLE_TO_LOCK_ROW.
7. **Monitor going forward.** Subscribe to a weekly report of `UNABLE_TO_LOCK_ROW` from the EventLogFile or your central log object. Treat new occurrences as a regression signal.

---

## Questions to Ask Before Configuring

Ask these before refactoring. Each one maps to a gotcha in `references/gotchas.md` or a pattern above.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which parent or queue row do the failing transactions share?" | A lock wait is on one row for at most 10 seconds (apexdev 264 L9395-9398) (gotcha 1) | The record Id from the fault emails and the object it belongs to |
| "How long does the blocking transaction hold its locks, and what is in it?" | Locks last until the transaction completes (apexdev 264 L9383); a callout or large loop upstream is the real target (gotcha 4) | The slowest element in the blocker, measured |
| "Is the Update inside a Loop?" | One DML per iteration reaches 150 statements (apexdev 264 L19757) (Pattern 1) | A collect-then-update refactor |
| "Is the parent skewed?" | The LDV guide advises no parent with more than 10,000 children (ldv 264 L1052-1055, a deployment best practice) (gotcha 8) | A child count per parent from a grouped query |
| "Does the flow change ownership or reparent children?" | Ownership and role changes are listed lock-contention sources (api_asynch 264 L2637-2639) (gotchas 3, 9) | A volume of reassignments per hour |
| "Does anything call out after a `FOR UPDATE` query?" | A callout releases `FOR UPDATE` locks (apexdev 264 L9404-9408) (Concept 4, gotcha 6) | A decision to lock after the callout, not before |
| "What publish behavior will the decoupling event use?" | Publish Immediately lets a subscriber run before the data is committed (platform_events 264 L346-351) (Pattern 2, gotcha 7) | Publish After Commit set, or a stated reason for the default |

A proper configuration adds a named hot row, a measured hold time and a decoupling choice tied to a publish behavior, none of which "just adding a retry" provides.

## Review Checklist

- [ ] Every Update/Create inside a Loop has been refactored to collect-then-update (single DML after loop).
- [ ] Flows that update a parent from a child-record trigger have been evaluated for Platform Event decouple.
- [ ] Heavy/slow parent recalcs are handed off to Queueable Apex, not synchronous in the user's transaction.
- [ ] Ownership changes are batched off-hours when affecting >100 records.
- [ ] Every DML element in the flow has a fault path that logs to a central error log.
- [ ] Master-Detail vs Lookup decisions have been documented — Master-Detail always propagates the lock.
- [ ] The flow has been load-tested with parallel DML against the same parent record.
- [ ] No `FOR UPDATE` invocable Apex is used as a generic "fix" for contention (it's only correct for true read-modify-write races).
- [ ] The refactored flow does not exceed 150 DML statements or 100 SOQL queries per transaction (apexdev 264 L19757, L19747).

---

## Salesforce-Specific Gotchas

1. **Child Update locks the parent automatically** (related records are locked with the record, apexdev 264 L9409; child changes cause "parent record-locking conflicts", ldv 264 L894-896; UNVERIFIED (2026-10-20): the "no flag" statement below) — Updating a single Opportunity locks the parent Account row for the entire transaction. There is no flag to disable this, no `WITHOUT_PARENT_LOCK` keyword. The only escape is to decouple via Platform Event, Queueable, or Scheduled Path.
2. **Queue-owned records lock the Group row on every insert/update** (UNVERIFIED (2026-10-20): not in the corpus) — If a Case record-triggered flow inserts a Task into a queue, the queue's Group row is locked. With many concurrent Cases routing into the same support queue, contention concentrates on that single Group row, not on the Cases themselves.
3. **Master-Detail reparenting locks both old and new master** (UNVERIFIED (2026-10-20): the lock claim is Help-sourced; `reparentableMasterDetail` is api_meta 264 L45820-45822) — Reassigning a Master-Detail child takes write locks on both the old parent, the new parent, and the child itself. With deep hierarchies (LineItem → Opportunity → Account), reparenting can lock 4+ rows simultaneously across two object trees.
4. **The 10-second lock wait is invisible in the debug log** (UNVERIFIED (2026-10-20): the debug-log behavior is not in the corpus; the 10-second wait is apexdev 264 L9395-9398) — the waiting transaction shows no element activity while it blocks, so the CPU-time profile looks fine and the pause is easy to attribute to the wrong element. Your fault email represents one attempt that waited the full 10 seconds and gave up; there is no automatic retry behind it. Correlate the fault timestamp against what else was writing to the same parent row at that moment.
5. **Flow's automatic rollback masks partial state** (UNVERIFIED (2026-10-20): not described in the corpus) — Unlike Apex (where DML between savepoints can persist), an unhandled flow fault rolls back **the entire flow's DML** to the start of the trigger. This makes contention failures invisible: there's no "half-committed" record to spot — just a missing record that should exist. Always log to a fault path.
6. **`Get Records` does not take a lock** — Practitioners assume reading a record before updating it pre-locks it. It doesn't. The lock is only acquired at the moment of the Update DML. A race between Get and Update is possible; only `FOR UPDATE` (via invocable Apex) closes it.
7. **Platform Event subscriber flows still take locks** — Decoupling via Platform Event moves the work to a separate transaction (platform_events 264 L2187-2188), but that transaction still takes parent locks when it updates. The benefit is the publisher transaction completes fast; the subscriber's contention is independent and self-throttling (events batch).
8. **Skew amplifies contention** — Account skew (the Large Data Volumes guide's deployment best practice is to "Distribute child records so that no parent has more than 10,000 child records", ldv 264 L1052-1055; UNVERIFIED (2026-10-20): that 10,000 is the skew threshold for lock contention is not stated) means even a single Opportunity update takes longer to acquire the parent lock, because the parent row is touched constantly. Skew assessment is a precondition to lock-contention assessment.

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
