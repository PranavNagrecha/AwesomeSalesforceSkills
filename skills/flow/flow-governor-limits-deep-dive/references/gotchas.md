# Gotchas — Flow Governor Limits Deep Dive

Non-obvious platform behaviour about what a flow spends and who else is spending it. Line citations
are into the Summer '26 / v62 text extracts of the Apex Developer Guide (`apexdev.txt`), the Apex
Reference Guide (`apexrefguide.txt`) and the Metadata API Developer Guide (`api_meta.txt`); the PDF
sources are listed in `well-architected.md` § Official Sources Used.

---

## Gotcha 1: Limits are shared; your flow does not own 100 SOQL

**What happens:** a flow that measures clean in isolation breaches in production, and the debug log
shows the breach happening on the flow's *first* element.

**When it occurs:** whenever anything else fires on the same save. The save order runs before-save
flows at step 3, before triggers at 4, Process Builder at 13, after-save flows at 14, roll-up
recalculation at 16–17 and Criteria Based Sharing at 18, all before the single commit at step 19
(`apexdev.txt` L15440–L15478). Everything in that list draws from one set of meters.

**How to avoid:** budget against what is left, not against the printed ceiling. The number you need
is on the `FLOW_START_INTERVIEW_LIMIT_USAGE` line — usage "at the interview's start time"
(`apexdev.txt` L38874–L38876), which is non-zero exactly to the extent that other automation ran
first. `scripts/check_flow_governor_limits_deep_dive.py` rule **W2** answers the same question from
the source tree with no org.

---

## Gotcha 2: A subflow spends the parent's meters, and no Flow field can change that

**What happens:** decomposing a large flow into subflows for readability moves no cost whatsoever.
The parent's budget is the subflow's budget.

**When it occurs:** always. `flowTransactionModel` — the only field in Flow metadata that opens a
transaction — is declared on `FlowActionCall` and nowhere else (`api_meta.txt` L68472–L68479).
`FlowSubflow` has no equivalent field, so there is no XML you can write that gives a subflow its own
meters.

**How to avoid:** count subflow elements in the parent's budget. If the goal was isolation rather
than readability, the lever is an invocable Apex action with `flowTransactionModel` `NewTransaction`,
or an `AsyncAfterCommit` scheduled path — not a subflow.

---

## Gotcha 3: A Get Records with related records costs more than one query

**What happens:** a Get Records element is budgeted at 1 SOQL and consumes several.

**When it occurs:** when the element uses `relatedRecords` (beta), which "specifies the related
records to look up in the database" (`api_meta.txt` L71205–L71207). That is a parent-child
relationship subquery, and "in a SOQL query with parent-child relationship subqueries, each
parent-child relationship counts as an extra query" (`apexdev.txt` footnote 1, L19613). Those
subqueries have their own ceiling of three times the top-level number, and their rows still count
against the 50,000-row meter (L19614–L19615).

**How to avoid:** count one query per element **plus one per related-record relationship**, and use
`Limits.getLimitAggregateQueries()` (named at L19614) rather than `getLimitQueries()` when you are
checking the subquery headroom in Apex.

---

## Gotcha 4: The CPU meter does not count the time your flow is actually slow for

**What happens:** a flow that takes eight seconds to save reports a few hundred milliseconds of CPU,
so raising the CPU headroom fixes nothing.

**When it occurs:** whenever the wall time is database time or callout wait. CPU time is measured
"for all executions on the Salesforce application servers"; "the portion of execution time spent in
the database for DML, SOQL, and SOSL isn't counted, nor is waiting time for Apex callouts"
(`apexdev.txt` footnote 5, L19652–L19656). A Get Records that scans a large unindexed table burns
wall-clock, not CPU.

**How to avoid:** separate the two symptoms before tuning. "CPU time limit exceeded" means loops,
formulas and Apex — go to `apex/apex-cpu-and-heap-optimization`. Slow-but-passing means query shape
or row volume — go to `flow/flow-get-records-optimization`. The two have no fix in common. Note the
one place they meet: "application server CPU time spent in DML operations *is* counted towards the
Apex CPU limit" (L19654), so a large collection DML does show up on the CPU meter.

---

## Gotcha 5: Two identical-looking Create Records on a platform event spend different meters

**What happens:** a flow publishes an event and the DML statement count does not move — or moves
when you expected it not to. The XML is the same either way; nothing in the flow says which.

**When it occurs:** the platform event definition, not the flow, chooses. "For events configured with
the Publish After Commit behavior, each method execution is counted as one DML statement against the
Apex DML statement limit… For events configured with the Publish Immediately behavior, each method
execution is counted against a separate event publishing limit of 150 `EventBus.publish()` calls"
(`apexrefguide.txt` L214524–L214528). The 150-call publish meter is its own row in the governor table
(`apexdev.txt` L19598–L19599), and Publish After Commit publishes appear in footnote 2's list of
calls that count as DML (L19635).

**How to avoid:** read the event's publish behavior before you budget a flow that publishes it, and
record it beside the element. In Apex, `Limits.getPublishImmediateDML()` and
`Limits.getDMLStatements()` are two different counters (`apexrefguide.txt` L220246–L220251).

---

## Gotcha 6: A fault path cannot catch a limit breach

**What happens:** a flow with a fault connector on every element still produces no
`Application_Log__c` row when it blows the SOQL or CPU limit. The fault route looks broken; it never
ran.

**When it occurs:** on any governor breach. `System.LimitException` is one of the exceptions that
"can't be caught… Those exceptions are associated with critical situations in the Lightning Platform.
These situations require the abortion of code execution", and "when exceptions are uncatchable, catch
blocks, as well as finally blocks if any, aren't executed" (`apexdev.txt` L39720–L39727).
UNVERIFIED (2026-09-05): the guides state this for Apex `catch`/`finally`; they do not describe
`faultConnector` behaviour in those words. The Flow "Per-Transaction Flow Limits" help page is the
only stated home for the flow-level rule.

**How to avoid:** stop treating fault paths as limit insurance. The only defences against a limit
breach are spending less (bulkification), spending elsewhere (`NewTransaction`, `AsyncAfterCommit`),
and a pre-deploy budget. And note that the fault route itself costs a DML statement and a row from
the same budget that was already under pressure.

---

## Gotcha 7: Email alerts are capped at 10 for the transaction, not 10 per flow

**What happens:** the eleventh email action on a busy save fails, and the flow that fails is whichever
one happens to run last — not the one that added the eleventh alert.

**When it occurs:** the ceiling is "total number of `sendEmail` methods allowed: 10"
(`apexdev.txt` L19575), a per-transaction meter like every other. Both flow email action types spend
it: `emailAlert` "sends an email by referencing a workflow email alert" and `emailSimple` "sends an
email by using flow resources" (`api_meta.txt` L68729, L68731).

**How to avoid:** count email actions across every automation on the object, the way you count DML.
Ten is a small number, and `triggerOrder` decides who gets the last one. Move notifications onto an
`AsyncAfterCommit` path, where they spend a different transaction's ten.

---

## Gotcha 8: There is no executed-elements limit any more, and the flow's own logs prove it

**What happens:** a review rejects a flow for exceeding "the 2,000 executed elements limit", or an
assistant invents a budget line for it. Neither has a source.

**When it occurs:** the platform emits four flow limit-usage debug events —
`FLOW_START_INTERVIEW_LIMIT_USAGE`, `FLOW_ELEMENT_LIMIT_USAGE`, `FLOW_BULK_ELEMENT_LIMIT_USAGE` and
`FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` (`apexdev.txt` L38730–L38744, L38795–L38820, L38821–L38834,
L38874–L38888). All four enumerate the same twelve meters, and **none lists an element count**.
Neither does the Apex-side `LIMIT_USAGE_FOR_NS` (L38930–L38948). `grep -n -i "2,\?000
element|executed elements|number of elements" apexdev.txt api_meta.txt
salesforce_app_limits_cheatsheet.txt` returns four hits, none of them a limit: three are
`FlowTestCoverage.numElements` / `numElementsNotCovered`, which count a flow version's elements for
test-coverage reporting (`api_meta.txt` L7715, L7727, L7729), and one is a UI display cap
(L48167).

**How to avoid:** budget the twelve meters the interview actually reports against. An element count
is a proxy for CPU at best, and CPU has its own meter.

---

## Gotcha 9: A certified managed package gets its own SOQL and DML — but shares your CPU

**What happens:** an installed package's flow or invocable action appears to spend nothing from your
budget, right up until the transaction dies on CPU.

**When it occurs:** "if you install a certified managed package, all the Apex code in that package
gets its own 150 DML statements… Similarly, the certified managed package gets its own
100-SOQL-query limit for synchronous Apex, in addition to the org's native code limit"
(`apexdev.txt` L19671–L19675). The cumulative cross-namespace ceiling is 11× the per-namespace limit,
so 1,100 SOQL across all namespaces (L19678–L19680). But: "the cumulative limit doesn't affect limits
that are shared across all namespaces, such as the limit on maximum CPU time" (L19681–L19682).

**How to avoid:** treat a managed-package action as free on the SOQL and DML meters and expensive on
CPU. And note the boundary: "namespaces in non-certified packages don't have their own separate
governor limits" (L19686–L19688) — an uncertified package spends yours.

---

## Gotcha 10: A flow's DML re-enters the save order, and the stack depth is 16

**What happens:** a flow updates a record, that update fires automation, which updates another record,
and somewhere down that chain the transaction dies with a stack-depth error rather than a limits
error.

**When it occurs:** "when a process or flow executes a DML operation, the affected record goes
through the save procedure" (`apexdev.txt` L15468). The ceiling is "total stack depth for any Apex
invocation that recursively fires triggers due to insert, update, or delete statements: 16"
(L19559–L19561), and footnote 3 explains why it is so much tighter than the other limits: "recursive
Apex that fires a trigger spawns the trigger in a new Apex invocation… Spawning a new invocation of
Apex is a more expensive operation than a recursive call in a single invocation" (L19637–L19648).

**How to avoid:** count the depth of the cascade, not just the elements. Sixteen is reached quickly by
a pair of flows that write to each other's objects. Designing the re-entry guard is
`flow/flow-record-save-order-interaction` and `flow/recursion-and-re-entry-prevention`.

---

## Gotcha 11: A recursive save skips after-save flows but not before-save flows

**What happens:** a flow's own DML triggers before-save automation again but not after-save
automation, so the same logic behaves differently depending on which half of the save order it sits
in.

**When it occurs:** "during a recursive save, Salesforce skips steps 9 (assignment rules) through 17
(roll-up summary field in the grandparent record)" (`apexdev.txt` L15414–L15415). Step 13 (Process
Builder) and step 14 ("executes record-triggered flows that are configured to run after the record is
saved", L15470) are inside that range and are skipped. Steps 3 (before-save flows, L15440), 4 (before
triggers) and 8 (after triggers) are outside it and run again.

**How to avoid:** when you budget the cascade a flow's DML sets off, count before-save flows and both
trigger phases, and do **not** count after-save flows at the second level. This changes the arithmetic
in both directions: fewer meters spent than you feared, and an after-save flow you were relying on
that silently does not fire.

---

## Gotcha 12: `triggerOrder` sequences flows; it does not budget them

**What happens:** a team sets `triggerOrder` to control which flow "gets" the limits and is surprised
when the last flow fails.

**When it occurs:** `triggerOrder` is "the run order of a record-triggered flow, from 1 to 2,000"
(`api_meta.txt` L68438–L68439). It is an ordering field. Ordering decides *who fails*: the flow at
order 2,000 inherits everything orders 1–1,999 already spent, so the flow that breaches is usually
not the flow that caused the pressure.

**How to avoid:** read `triggerOrder` as a blame-assignment field, not a budget field. When a flow
starts failing without changing, look at what was added *ahead* of it — and confirm with the
`FLOW_START_INTERVIEW_LIMIT_USAGE` line, which shows exactly what it inherited.

---

## Gotcha 13: A single Get Records can legally consume 40% of the row budget

**What happens:** one element that passes every review takes 20,000 of the 50,000 SOQL rows, and the
next Get Records in the transaction has nowhere to go.

**When it occurs:** `FlowRecordLookup.limit` accepts "values between 2 and 20,000" and is "supported
only when `getFirstRecordOnly` is false" (`api_meta.txt` L71173–L71180, API 63.0 and later). The row
ceiling is 50,000 (`apexdev.txt` L19546). Nothing warns you: a Get with no `limit` at all is
unbounded up to the ceiling, and one with `limit` set to 20,000 is *deliberately* unbounded up to 40%
of it.

**How to avoid:** set `limit` to the number the business actually needs rather than to the field's
maximum, and remember that the ceiling it eats into is shared. On API versions below 63.0 the field
does not exist, so the cap has to be a filter instead.

---

## Gotcha 14: The App Limits cheat sheet has no Flow row at all

**What happens:** someone cites a "Flow limit" from the Salesforce App Limits cheat sheet. There is
nothing there to cite.

**When it occurs:** always. `grep -n -i "flow|workflow|interview" salesforce_app_limits_cheatsheet.txt`
over the 1,259-line document returns four hits and not one is a Flow limit: three are incidental prose
about CPU time, Bulk API workloads and workflow interruption, and none names a flow, an interview or a
flow element. Flow's per-transaction spend lives in the Apex governor table (`apexdev.txt`
L19542–L19599) because it is the *same* set of meters; Flow's own runtime ceilings live only on
help.salesforce.com.

**How to avoid:** cite `apexdev.txt` for anything per-transaction. For anything else — paused-interview
caps, scheduled-flow daily volumes — the honest answer is UNVERIFIED (2026-09-05): those numbers exist
only on the Flow "Per-Transaction Flow Limits" and "Flow Runtime Limits" help pages, which cannot be
fetched, and no developer guide restates them.

---

## Gotcha 15: `maxBatchSize` is a limits lever wearing a throughput costume

**What happens:** an `AsyncAfterCommit` path still breaches, because moving work to a fresh
transaction did not reduce how much work is in it.

**When it occurs:** `maxBatchSize` is "the maximum number of scheduled path interviews to execute in a
single batch, from 1 to 200. Default is 200" (`api_meta.txt` L71397–L71398). At the default, 200
interviews share one async transaction and one set of meters — the same arithmetic as the synchronous
path it was moved off. Lowering it to 50 quarters the per-transaction spend at the cost of four times
the transactions.

**How to avoid:** treat `maxBatchSize` as the async equivalent of the batch size you cannot control on
the synchronous side, and set it deliberately. UNVERIFIED (2026-09-05): whether the async path's
transaction is metered at synchronous (100 SOQL / 10,000 ms) or asynchronous (200 / 60,000) ceilings
is not stated in `apexdev.txt`, `api_meta.txt` or the App Limits cheat sheet — the
`FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` line prints the denominator, so measure rather than assume.

---

## Gotcha 16: Async paths are post-commit, so nothing they do is rolled back

**What happens:** the immediate path fails after the async path has already run, and the org is left
half-updated with no rollback.

**When it occurs:** the Apex Developer Guide lists "asynchronous paths in record-triggered flows"
among the examples of step-20 post-commit logic — "after the changes are committed to the database,
executes post-commit logic" (`apexdev.txt` L15479, L15489). Step 19 is the commit (L15478). Anything
after it is outside the transaction that could be rolled back.

**How to avoid:** only move work onto an async path when it does not need to be atomic with the save,
and make it idempotent — a post-commit path can run against a record that later automation changes
again. `flow/flow-transactional-boundaries` owns where the boundary belongs; this skill only prices
each side of it.

---

## Gotcha 17: Get Records stores every queried field, and heap is 6 MB

**What happens:** a Get Records that returns a few thousand wide records exhausts heap before it
exhausts the row meter.

**When it occurs:** heap is 6 MB synchronous and 12 MB asynchronous (`apexdev.txt` L19577), and
heap size in bytes is one of the twelve meters every flow limit-usage event reports (L38801,
L38830). `queriedFields` is "an array that specifies which fields from the selected record are saved
to the specified record variable" (`api_meta.txt` L71202–L71204) — but it is "supported only when
`storeOutputAutomatically` is false" for the assignment path, and the guides do not state what the
automatic-output mode retrieves. UNVERIFIED (2026-09-05): the claim that Get Records fetches *all*
fields by default is not supported by anything in `api_meta.txt`; what is documented is that you can
name the fields explicitly.

**How to avoid:** name `queriedFields` explicitly rather than relying on a default nobody has
documented, and cap rows with `limit`. Heap is one of the two meters (with CPU) that no static
analysis can predict — read it off the log.

---

## Gotcha 18: Platform-Event subscriber batches can surprise

**What happens:** an event-triggered flow that is correct at one event per batch breaches CPU at
production volume.

**When it occurs:** PE subscribers receive up to 2,000 event messages per batch — the documented
maximum and default for both standard-volume and high-volume events, lowerable (not raisable) via
`PlatformEventSubscriberConfig`. Each run has fresh limits, but a big loop inside the subscriber flow
can still breach CPU at 2,000 events.

**How to avoid:** budget the subscriber flow at 2,000, not at 1, and lower the configured batch size
before adding loop work. Source: Salesforce Developer Documentation, "Configure the User and Batch
Size for Your Platform Event Trigger".

---

## Gotcha 19: A Scheduled Path's fresh budget is fresh, not larger

**What happens:** a team moves a SOQL-in-loop flow onto a scheduled path and the same error returns,
delayed.

**When it occurs:** always. A fresh transaction resets the counters; it does not change what an
element costs. A Get Records inside a loop over 300 records is 300 queries against a 100-query meter
(`apexdev.txt` L19544) in any transaction, immediate or async.

**How to avoid:** fix the shape first, then decide whether it also needs its own transaction. The
checker orders these correctly: **E1** and **W1** (shape) are findings; **A2** (transaction split) is
advisory, because splitting a badly-shaped flow just relocates the failure.

---

## Gotcha 20: Async meters reset per execution, not per job

**What happens:** a team budgets an asynchronous chain as if the whole job shared one 200-SOQL
allowance, and either over-engineers or under-estimates by an order of magnitude.

**When it occurs:** "these limits count for each Apex transaction. For Batch Apex, these limits are
reset for each execution of a batch of records in the `execute` method" (`apexdev.txt`
L19530–L19531). So a job that runs 100 batches gets the asynchronous ceilings 100 times, not once.
Two exceptions sit in the same note: "although scheduled Apex is an asynchronous feature, synchronous
limits apply to scheduled Apex jobs", and for Bulk API "the effective limit is the higher of the
synchronous and asynchronous limits" (L19536–L19539).

**How to avoid:** budget per execution and count how many executions a batch size produces. The
scheduled-Apex exception is the one that catches people: asynchronous *feature*, synchronous
*ceilings*. UNVERIFIED (2026-09-05): this note is written about Apex; whether a scheduled **flow**
inherits the same synchronous-ceilings rule is not stated in any guide in this corpus. Measure the
denominator on `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE`.

---

## Gotcha 21: Nobody publishes what an element costs, so nobody can predict CPU

**What happens:** a design review asks for a CPU estimate and gets a fabricated one — "a Decision is
about 2 ms, so 15 Decisions × 500 iterations is 15 seconds."

**When it occurs:** always. There is no per-element cost table in any Salesforce developer guide, and
CPU time is measured across "all executions on the Salesforce application servers occurring in one
Apex transaction… for the executing Apex code, and for any processes that are called from this code,
such as package code and workflows" (`apexdev.txt` footnote 5, L19652–L19653). The cost of one
element therefore depends on the row width, the formula complexity and any Apex the action calls —
none of which is a published constant. This is why
`scripts/check_flow_governor_limits_deep_dive.py` reports element counts and explicitly refuses to
print a millisecond figure.

**How to avoid:** never state a CPU number that did not come from a measurement. The two that count
are `FLOW_ELEMENT_LIMIT_USAGE`, which reports "incremented usage toward a limit for this element"
including "CPU time in ms" (`apexdev.txt` L38795–L38801), and `Limits.getCpuTime()` in an Apex test
(`apexrefguide.txt` L220218–L220219). Both are cheap; both are the only honest source.

---

## Gotcha 22: The costs nobody has documented, stated as unknowns

**What happens:** a review argues about whether an empty loop, a Decision on a null collection, or a
screen render costs anything, and both sides cite nothing.

**When it occurs:** these are genuine gaps, not oversights on the reader's part. NOT FOUND
(2026-09-05) in `apexdev.txt`, `apexrefguide.txt` or `api_meta.txt`: (a) any statement that a
zero-iteration Loop consumes CPU; (b) any statement that a screen or a Pause element ends the
transaction; (c) any per-element CPU or heap cost; (d) any cap on collection variable size. What *is*
documented and adjacent: `FlowRecordRollback` "rolls back the current transaction and cancels its
pending record changes" and is "available only in screen flows" (`api_meta.txt` L71247–L71250), and
`FLOW_INTERVIEW_PAUSED` / `FLOW_INTERVIEW_RESUMED` are separate log events (`apexdev.txt`
L38834–L38841). Both imply a screen flow spans more than one transaction without stating the rule.

**How to avoid:** when one of these comes up, say it is unmeasured rather than guessing a direction,
and settle it in a scratch org with a Workflow-`FINER` log. Two elements' worth of CPU is not worth
an argument; a wrong claim about where the transaction boundary is will cost a rollback design.

---

## Gotcha 23: Scheduled-path batches are concurrent, and concurrent writes contend

**What happens:** a scheduled path that is correct at 200 records produces `UNABLE_TO_LOCK_ROW` at
1,000, and the failures are not reproducible.

**When it occurs:** `maxBatchSize` caps a batch at 200 interviews (`api_meta.txt` L71397–L71398), so a
save of 1,000 qualifying records produces five batches. Each batch is its own transaction with its own
meters — which is the point — but batches that write to a shared parent record, a shared roll-up, or
the same `Application_Log__c` rows contend with each other. Fresh limits and safe concurrency are
different properties. UNVERIFIED (2026-09-05): the developer guides in this corpus do not state
whether those batches run in parallel or in sequence; the failure mode is well known in the field and
the ordering is not documented here.

**How to avoid:** budget the meters per batch and design the writes for contention separately. Record
locking is `flow/flow-record-locking-and-contention`; this skill only settles that each batch gets its
own meters.
