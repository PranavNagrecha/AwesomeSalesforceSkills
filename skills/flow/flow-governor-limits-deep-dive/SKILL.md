---
name: flow-governor-limits-deep-dive
description: "Compute and budget governor-limit consumption per Flow type with worked math: SOQL, DML rows, CPU time, heap. Includes per-entry-point budget tables, cross-automation shared-limit math, and tuning strategies when a flow hits a ceiling. Triggers: 'flow too many SOQL queries 101', 'flow too many DML statements 150', 'which flow element spends which limit', 'FLOW_INTERVIEW_FINISHED_LIMIT_USAGE', 'FLOW_ELEMENT_LIMIT_USAGE', 'flowTransactionModel NewTransaction', 'AsyncAfterCommit scheduled path', 'flow 2000 elements limit', 'flow shares limits with trigger'. NOT for general bulkification — use flow/flow-bulkification. NOT for Apex limits — use apex/governor-limits."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
tags:
  - flow
  - governor-limits
  - performance
  - soql
  - dml
  - cpu
  - heap
triggers:
  - "flow governor limits"
  - "flow soql 101 error"
  - "flow cpu time limit"
  - "flow dml rows exceeded"
  - "flow heap size exceeded"
  - "shared limits trigger flow"
  - "work out which flow element is spending my SOQL limit"
  - "budget a record-triggered flow before adding it to a busy object"
  - "read FLOW_INTERVIEW_FINISHED_LIMIT_USAGE in a debug log"
  - "split a flow into two transactions without rewriting it in Apex"
  - "flow hit too many DML statements 150 but there is no DML in the loop"
  - "does a subflow get its own governor limits"
  - "is there still a 2000 executed elements limit in flow"
  - "estimate CPU time for a flow before deploying it"
  - "my flow only fails in production and passes in the sandbox"
  - "set flowTransactionModel to NewTransaction on an apex action"
  - "does an AsyncAfterCommit scheduled path get a fresh limit budget"
  - "count how many DML elements are active on one object"
inputs:
  - Flow type + entry context
  - Expected records per batch / per transaction
  - Concurrent automations on the same object
  - Existing Apex trigger limit consumption
  - Platform event publish behavior (Immediately vs After Commit) for any event the flow publishes
  - The invocable Apex action's own SOQL/DML/CPU, where the flow calls one
outputs:
  - Per-element limit budget
  - Shared-transaction budget forecast
  - Tuning recommendations (bulkify, split, async-ify)
  - Pre-deployment benchmark plan
  - A filled limits budget worksheet with the arithmetic rows separated from the measured rows
  - Checker findings mapped to the review checklist
dependencies: []
version: 2.0.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Flow Governor Limits Deep Dive

This skill answers one question: **what does this flow spend, and who else is spending it?**

It owns the per-transaction meter table as it applies to Flow, the mapping from each flow element to
the meter it consumes, how a flow shares one budget with triggers and Apex, how to read the four
limit-usage debug events, and the levers that move spend into another transaction.

It does **not** own where transaction boundaries belong — that is
`flow/flow-transactional-boundaries`. It does not own the DML-staging refactor
(`flow/flow-bulkification`), loop mechanics (`flow/flow-loop-element-patterns`), recursion design
(`flow/flow-record-save-order-interaction`), or reading a debug log in general
(`flow/flow-debugging`). This skill prices the choices those skills make.

---

## Before Starting

- What is the object and trigger type, and what **else** is active on it? The budget's unit is the
  transaction, so the unit of analysis is the object, not the flow.
- What is p99 batch size? A flow that is correct at 1 and correct at 200 can still be wrong at 200,
  because four meters scale with rows rather than with elements.
- Does the flow call an invocable Apex action? Then its budget is unknowable until you have read the
  class — under `CurrentTransaction` the class's SOQL, DML, CPU and callouts are charged here.
- Does it publish a platform event? Then the **event definition** decides which meter that element
  spends, and the flow XML does not say.
- Is any part of the work required to be atomic with the save? That answer, not the limit arithmetic,
  decides whether the transaction can be split.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What else is Active on this object and trigger type, and what does the Apex trigger already spend?" | Meters are per transaction. The save order runs before-save flows, triggers, Process Builder, after-save flows and roll-ups before the single commit (`apexdev.txt` L15440–L15478), all from one budget | A co-tenant list with a number beside each — from `FlowDefinitionView` or from the checker's **W2** rule — so the budget's TOTAL column is real (Gotcha 1) |
| "What is the p99 number of records in one save, and how many child rows per record?" | Four meters scale with rows, not elements: SOQL rows 50,000, DML rows 10,000, heap, CPU (`apexdev.txt` L19546, L19556, L19577, L19579). A flow can be at 3% on DML statements and 60% on DML rows | Two numbers that turn every element count into a row count, which is the half of the worksheet that actually moves (`references/examples.md`) |
| "Which meter does the platform event this flow publishes spend?" | Publish After Commit "is counted as one DML statement"; Publish Immediately counts "against a separate event publishing limit of 150" (`apexrefguide.txt` L214524–L214528). Identical XML, different budgets | The event's configured publish behavior, recorded beside the element — not a guess from the flow file (Gotcha 5) |
| "What does the invocable Apex action itself consume, and what is its `flowTransactionModel`?" | `CurrentTransaction` "keeps the invocable action running in the same transaction" (`api_meta.txt` L68475–L68476), so the class's whole consumption lands in this flow's budget | The class's own SOQL/DML/callout counts, plus an explicit model value rather than an omitted field the checker flags as **A1** (Gotcha 2) |
| "Does any of this work have to be rolled back if a later step fails?" | It is the only question that decides whether `NewTransaction` or `AsyncAfterCommit` is available. Async paths are step-20 post-commit logic (`apexdev.txt` L15479, L15489) — nothing there is rolled back | A per-branch yes/no that turns a limits problem into a design decision, and an idempotency requirement for every "no" (Gotcha 16) |
| "Has anyone measured CPU and heap at peak batch size, or are those numbers estimated?" | No developer guide publishes a per-element cost, and CPU excludes database and callout wait time (`apexdev.txt` L19652–L19656). Ten meters are arithmetic; these two are not | A debug-log excerpt or a `Limits.getCpuTime()` assertion instead of a plausible millisecond figure (Gotcha 21, Anti-Pattern 9) |
| "Is any automation here from an installed managed package, and is that package certified?" | A certified package "gets its own 150 DML statements… its own 100-SOQL-query limit" but shares CPU (`apexdev.txt` L19671–L19682); a non-certified one spends yours (L19686–L19688) | The certification status per package, which decides whether that automation belongs in your budget's TOTAL column or only in the CPU row (Gotcha 9) |

**What a proper configuration adds over just doing it:** a budget whose TOTAL column counts every
automation on the object rather than only the flow in front of you, CPU and heap left blank until they
are measured instead of guessed, and a transaction split chosen from what must be atomic — so the flow
that fails first in production is one you predicted, not one you discover.

---

## The per-transaction meters

Every one of these is shared by every flow, trigger, validation rule, Apex class and package
automation in the transaction. Ceilings from the Apex Developer Guide's governor table
(`apexdev.txt` L19542–L19599).

| Meter | Synchronous | Asynchronous | Line |
|---|---|---|---|
| SOQL queries | 100 | 200 | L19544 |
| SOQL query rows | 50,000 | 50,000 | L19546 |
| `Database.getQueryLocator` rows | 10,000 | 10,000 | L19548 — no Flow element spends it |
| SOSL queries | 20 | 20 | L19550 — no Flow element spends it |
| DML statements | 150 | 150 | L19554 |
| DML rows (incl. `Approval.process`) | 10,000 | 10,000 | L19556 |
| Stack depth, recursive trigger-firing save | 16 | 16 | L19559–L19561 |
| Callouts | 100 | 100 | L19563 |
| `@future` methods per invocation | 50 | 0 in batch/future, 50 in queueable | L19568–L19571 |
| `System.enqueueJob` | 50 | 1 | L19573 |
| `sendEmail` invocations | 10 | 10 | L19575 |
| Heap | 6 MB | 12 MB | L19577 (email services: 50 MB, footnote 4 L19650) |
| CPU time | 10,000 ms | 60,000 ms | L19579 |
| `EventBus.publish`, publish-immediately events | 150 | 150 | L19598–L19599 |

Two things this table does not say, and both matter more than any row in it:

- **CPU excludes the time your flow is slow for.** "The portion of execution time spent in the
  database for DML, SOQL, and SOSL isn't counted, nor is waiting time for Apex callouts"
  (footnote 5, L19655–L19656) — but application-server CPU spent *in* DML operations is counted
  (L19654). A slow flow and a CPU-limit flow are different problems with no shared fix.
- **A certified managed package brings its own SOQL and DML meters but shares yours for CPU**
  (L19671–L19682). Its automation is free on two rows of your budget and expensive on one.

**Which flow element spends which meter** is the meter-by-element table in
`references/metadata-examples.md` § 1, with a fully annotated flow beneath it. Read that before
budgeting anything; the short version is: Get Records → SOQL + rows; Create/Update/Delete → DML +
rows; Loop/Assignment/Decision/processors → CPU only; email actions → the 10-invocation meter;
Apex action → whatever the class spends, unless `NewTransaction`; a `__e` create → DML **or** the
publish meter, depending on the event.

---

## Interview vs transaction

These are different units and confusing them is the most common budgeting error.

- An **interview** is per record. "A flow interview starts for each record that meets the filter
  conditions" (`api_meta.txt` L72403–L72405).
- A **transaction** is per save. All of the interviews a single DML produces run inside it and share
  one set of meters.
- The engine executes an element **once across the batch** where it can — which is why a Get Records
  above the loop costs 1 query for 200 interviews, not 200. The debug log distinguishes the two:
  `FLOW_BULK_ELEMENT_LIMIT_USAGE` is per bulk element, `FLOW_ELEMENT_LIMIT_USAGE` is per element per
  interview (`apexdev.txt` L38730–L38744, L38795–L38820). `FLOW_BULK_ELEMENT_NOT_SUPPORTED` names the
  "operation, element name, and entity name that doesn't support bulk operations" (L38746–L38747) —
  that element is the per-interview one, and it is where a batch gets expensive.

UNVERIFIED (2026-09-05): the widely-quoted figure of **200 record-triggered interviews per
transaction** is not stated in `apexdev.txt`, `api_meta.txt` or the App Limits cheat sheet. The one
documented 200 in this area is `FlowScheduledPath.maxBatchSize`, "the maximum number of scheduled path
interviews to execute in a single batch, from 1 to 200. Default is 200" (`api_meta.txt`
L71397–L71398). Budget the async side from that number; confirm the synchronous side from
`FLOW_START_INTERVIEWS_BEGIN`, which logs the request count.

---

## The transaction-splitting levers

Four, in the order you should try them. The full trade table is in
`references/well-architected.md` § The Budget Ladder.

1. **Spend less** — hoist DML and SOQL out of loops. The only lever that reduces the bill rather than
   relocating it. Owned by `flow/flow-bulkification` and `flow/flow-loop-element-patterns`.
2. **`flowTransactionModel` `NewTransaction`** on an `actionCalls` element — "creates a transaction
   before the invocable action is executed" (`api_meta.txt` L68477–L68478, API 51.0+). Isolates that
   action's meters. Costs atomicity.
3. **`scheduledPaths` with `pathType` `AsyncAfterCommit`** — the branch runs post-commit
   (`api_meta.txt` L71412–L71414; `apexdev.txt` L15489 lists it as step-20 post-commit logic). Tune
   `maxBatchSize` (1–200, default 200) to decide how many interviews share the async transaction.
4. **Screens and Pause elements.** UNVERIFIED (2026-09-05): neither `api_meta.txt` nor `apexdev.txt`
   states that a screen or a `waits` element ends the transaction; that rule lives only on the Flow
   help pages. Documented and adjacent: `FlowRecordRollback`, which "rolls back the current
   transaction and cancels its pending record changes", is "available only in screen flows"
   (`api_meta.txt` L71247–L71250), and a screen-flow callout action can make the flow "commit the
   current transaction, start a new transaction, and make the call" when Transaction Control is set to
   let the flow decide (`apexdev.txt` L26866–L26875).

What none of them do: **a subflow does not get its own budget.** `flowTransactionModel` is declared on
`FlowActionCall` alone (`api_meta.txt` L68472); no field in Flow metadata gives a subflow a
transaction.

---

## Reading the four limit-usage events

Set the **Workflow** log category to `FINER` or above. Four events, all reporting the same twelve
meters (`apexdev.txt` L38730–L38744, L38795–L38820, L38821–L38834, L38874–L38888):

| Event | Answers |
|---|---|
| `FLOW_START_INTERVIEW_LIMIT_USAGE` | what was already spent before this flow ran — your real headroom |
| `FLOW_ELEMENT_LIMIT_USAGE` | which element spent what, per interview |
| `FLOW_BULK_ELEMENT_LIMIT_USAGE` | what one element cost across the whole batch |
| `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` | this interview's total, **and the denominator** — which is how you find out whether it was metered at synchronous or asynchronous ceilings |

The twelve: SOQL queries, SOQL query rows, SOSL queries, DML statements, DML rows, CPU time in ms,
heap size in bytes, callouts, email invocations, future calls, jobs in queue, push notifications.
**No element count appears in any of them**, which is the evidence that the "2,000 executed elements"
limit is retired (`references/gotchas.md` Gotcha 8). An annotated excerpt, plus the guide's one
verbatim `LIMIT_USAGE_FOR_NS` block, is in `references/metadata-examples.md` § 7a.

---

## Review Checklist

- [ ] No DML element is reachable from a loop's `nextValueConnector` — checker **E1**.
- [ ] No Get Records is reachable from a loop's `nextValueConnector` — checker **W1**.
- [ ] The non-loop DML elements of every Active flow on this object + trigger type sum below the
      agreed threshold — checker **W2**.
- [ ] Every `actionCalls` with `actionType` `apex` states its `flowTransactionModel` — checker **A1**.
- [ ] A flow with three or more DML elements has a deliberate answer on whether any branch belongs on
      an `AsyncAfterCommit` path — checker **A2**.
- [ ] Every element's meter is named in the budget worksheet, including which meter the `__e` create
      spends.
- [ ] The invocable Apex action's own consumption is counted, or the action is `NewTransaction`.
- [ ] Every arithmetic row of the worksheet is below 70% of its ceiling at p99 batch size.
- [ ] CPU and heap rows are **measured**, not estimated, and the log excerpt is attached.
- [ ] No fault path is being relied on to handle a limit breach.
- [ ] Any Flow-runtime number that came from help.salesforce.com carries an UNVERIFIED marker.

## Recommended Workflow

1. **Enumerate the co-tenants, not just the flow.** Run
   `python3 skills/flow/flow-governor-limits-deep-dive/scripts/check_flow_governor_limits_deep_dive.py --manifest-dir <source tree>`
   to get the per-flow element counts and the **W2** cross-flow DML total for the object. Add the Apex
   trigger's consumption by hand — the checker reads flows only.
2. **Map every element to its meter** using the table in `references/metadata-examples.md` § 1. Two
   elements need an answer from outside the XML: the platform event's publish behavior, and the
   invocable action's own consumption plus its `flowTransactionModel`.
3. **Fill the arithmetic rows** of the worksheet in `references/examples.md`, multiplying element
   counts by p99 batch size and rows-per-record. Leave CPU and heap blank. If any row is above 70%,
   stop and fix the spend before considering a split.
4. **Clear checker ERRORs, then decide the split.** **E1** (DML in loop) is a defect; **W1** (SOQL in
   loop) is nearly always one. Only once the shape is right do **A2** and the levers in § The
   transaction-splitting levers apply — async relocates a failure, it never shrinks it.
5. **Measure CPU and heap.** Deploy the flow `Draft` to a sandbox, run the bulk Apex test in
   `references/metadata-examples.md` § 7b at p99 batch size, and read
   `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` at Workflow `FINER` (§ 7a). Fill the measured rows and note
   the denominator.
6. **Write the `FlowTest` and the budget assertions.** The `FlowTest` (§ 4) proves correctness at bulk
   size 1; the Apex test asserts the counters at 200. Both are needed — neither substitutes.
7. **Record what the guides could not settle** in the flow's `<description>` and in
   `templates/flow-governor-limits-deep-dive-template.md`: the async path's ceiling denominator, the
   interviews-per-transaction number, and any help-page figure you had to rely on.

---

## Salesforce-Specific Gotchas

Full statements with grounding in `references/gotchas.md`; the index:

1. Limits are shared; your flow does not own 100 SOQL.
2. A subflow spends the parent's meters, and no Flow field can change that.
3. A Get Records with `relatedRecords` costs more than one query.
4. The CPU meter does not count the time your flow is actually slow for.
5. Two identical-looking `__e` creates spend different meters.
6. A fault path cannot catch a limit breach.
7. Email alerts are capped at 10 for the transaction, not 10 per flow.
8. There is no executed-elements limit any more, and the flow's own logs prove it.
9. A certified managed package gets its own SOQL and DML but shares your CPU.
10. A flow's DML re-enters the save order, and the stack depth is 16.
11. A recursive save skips after-save flows but not before-save flows.
12. `triggerOrder` sequences flows; it does not budget them.
13. A single Get Records can legally consume 40% of the row budget.
14. The App Limits cheat sheet has no Flow row at all.
15. `maxBatchSize` is a limits lever wearing a throughput costume.
16. Async paths are post-commit, so nothing they do is rolled back.
17. Get Records stores every queried field, and heap is 6 MB.
18. Platform-Event subscriber batches can surprise.
19. A Scheduled Path's fresh budget is fresh, not larger.
20. Async meters reset per execution, not per job.
21. Nobody publishes what an element costs, so nobody can predict CPU.
22. The costs nobody has documented, stated as unknowns.
23. Scheduled-path batches are concurrent, and concurrent writes contend.

---

## Proactive Triggers

Surface these WITHOUT being asked:

- **A DML element inside a loop** → Critical. Breaches at iteration 150 whatever the batch size.
- **A Get Records inside a loop** → Critical. 100 queries, shared with everything else on the save.
- **A CPU or heap figure with no measurement behind it** → Critical. No per-element cost is published;
  the number was invented.
- **A fault path presented as limit handling** → High. `System.LimitException` is uncatchable; the
  route does not run.
- **An `actionCalls` `apex` with no `flowTransactionModel`** → High. The action's consumption cannot be
  attributed by reading the source.
- **A budget that counts only this flow** → High. The TOTAL column is the only column that means
  anything.
- **"2,000 executed elements"** → High. Retired; the flow's own limit-usage events list no element
  count.
- **"Move it to a Scheduled Path to fix the limit"** on a flow with SOQL or DML in a loop → High.
  Relocates the failure, does not fix it.
- **A `__e` create budgeted as DML with no check of the event's publish behavior** → Medium. Fifty-fifty
  it is the wrong meter.
- **`triggerOrder` used as a budgeting device** → Medium. It decides who fails, not who gets a budget.
- **A Flow limit quoted from the App Limits cheat sheet** → Medium. There are none in it.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Limits budget worksheet | The per-object worksheet from `references/examples.md`, arithmetic rows filled, CPU/heap left for measurement |
| Meter attribution | Every element in the flow mapped to the meter it spends, including the event publish behavior and the Apex action's model |
| Checker report | ERROR/WARN/ADVISORY findings from `scripts/check_flow_governor_limits_deep_dive.py`, mapped to the Review Checklist |
| Split recommendation | Which branches move to `NewTransaction` or `AsyncAfterCommit`, with the atomicity each one gives up |
| Measured baseline | The `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` excerpt and the Apex budget-test counters at p99 batch size |
| Deployable XML | The annotated flow and its split variant from `references/metadata-examples.md`, plus the `FlowTest` and `package.xml` |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing or reviewing actual `*.flow-meta.xml`: the element-to-meter table, a fully annotated record-triggered flow, the same flow split across `AsyncAfterCommit` and `NewTransaction` with the budget before and after, a `FlowTest`, `package.xml`, deploy order, the four limit-usage debug events, and the bulk Apex budget test |
| `references/gotchas.md` | The flow deploys and then breaches something you did not budget — shared meters, the publish-behavior split, the uncatchable limit exception, the managed-package CPU rule, the recursive-save skip, and the things the guides genuinely do not document |
| `references/llm-anti-patterns.md` | You are reviewing generated Flow advice or your own — including the retired element limit, invented CPU figures, `System.assertTrue`, and "a subflow gets its own limits" |
| `references/examples.md` | You need the limits budget worksheet, or a narrative walk-through of a SOQL-in-loop breach, a shared-transaction forecast, or an async offload |
| `references/well-architected.md` | You need the pillar framing, the Budget Ladder trade table, or the source and guide line behind any claim in this skill |
| `templates/flow-governor-limits-deep-dive-template.md` | You are recording a budget or a review for someone else to act on |
| `scripts/check_flow_governor_limits_deep_dive.py` | Before every deploy and against any fixture directory. `--manifest-dir <source tree>`, optional `--dml-budget N` and `--strict`; exits 1 on any ERROR |

## Related Skills

- **flow/flow-bulkification** — owns the DML-staging refactor and the escalate-to-Apex threshold. Go
  there the moment the answer is "spend less" rather than "spend elsewhere".
- **flow/flow-loop-element-patterns** — owns loop mechanics and the collect-then-DML pattern that keeps
  the DML statement meter at 1.
- **flow/flow-collection-processing** — owns which loop-free element does a collection task, which is
  usually how the CPU spend comes down.
- **flow/flow-transactional-boundaries** — owns *where* a transaction should start and end. This skill
  prices each side of the boundary; that one decides where to put it.
- **flow/flow-record-save-order-interaction** — owns recursion, re-entry and the save order itself,
  including the stack-depth-16 cascade.
- **flow/flow-debugging** — owns trace flags, log retention and every flow debug event that is not one
  of the four limit-usage ones.
- **flow/flow-get-records-optimization** — owns query shape, selectivity and row volume when the
  problem is wall time rather than the CPU meter.
- **flow/flow-record-locking-and-contention** — owns concurrent batches writing to the same records.
- **apex/apex-cpu-and-heap-optimization** — owns the CPU and heap side once the flow calls Apex.
- **apex/governor-limits** — owns the same meters from the Apex side, including the `Limits` class.

## Official Sources Used

- Apex Developer Guide — Execution Governors and Limits (per-transaction table and footnotes 1–5):
  <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf>
- Apex Developer Guide — Triggers and Order of Execution, and Debug Log Levels (Workflow events):
  <https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm>
- Apex Reference Guide — `EventBus.publish`, `Limits`, `Assert`, `Flow.Interview`:
  <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apexref.pdf>
- Metadata API Developer Guide — `Flow`, `FlowActionCall`, `FlowScheduledPath`, `FlowRecordLookup`,
  `FlowStart`, `FlowTest`:
  <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf>
- Salesforce Help — Flow "Per-Transaction Flow Limits" and "Flow Runtime Limits":
  <https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limit.htm>. UNVERIFIED
  (2026-09-05): not fetchable in this environment; every claim resting only on it is marked at the
  claim.

The full list, with the specific claim each source supports, is in
`references/well-architected.md` § Official Sources Used.
