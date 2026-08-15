# Examples — Flow Batch Processing Alternatives

Worked examples for the moment a Flow-based job outgrows a single run. Each one
states the constraint that actually binds, the pattern, and what it costs.

The numbers that matter before any of this:

| Constraint | Value | Scope |
|---|---|---|
| Schedule-triggered flow interviews | 250,000 per 24 hours, or user licenses × 200, whichever is greater | Per org |
| Scheduled flow batch size | 200 by default; settable 1–200 from the Start element on runtime version 63.0+ | Per flow |
| Platform-event-triggered flow batch size | 200 maximum | Per flow |
| SOQL queries per transaction | 100 synchronous / 200 asynchronous | Per transaction, shared |
| SOQL rows per transaction | 50,000 | Per transaction, shared |
| DML statements per transaction | 150 | Per transaction, shared |
| DML rows per transaction | 10,000 | Per transaction, shared |
| CPU time | 10,000 ms synchronous / 60,000 ms asynchronous | Per transaction |
| Batch Apex jobs queued or active | 5 concurrently (plus up to 100 Holding in the flex queue) | Per org |
| Batch Apex method executions | 250,000 per 24 hours, or user licenses × 200, whichever is greater | Per org |
| `Database.executeBatch` scope | 200 default, 2,000 maximum for a QueryLocator | Per job |

**Which column a schedule-triggered flow is measured against:** the asynchronous
one, from runtime version 61.0 onward. That is what the *Improve Scheduled Flow
Performance with Updated Limits* release update changed, and since a custom batch
size needs 63.0, every flow this page tells you to size is on asynchronous limits
— 200 SOQL and 60,000 ms CPU. Note what did **not** move: DML statements are 150
on both sides, DML rows 10,000, SOQL rows 50,000. A record-triggered flow running
inside a synchronous transaction still gets 100 SOQL and 10,000 ms.

Note the symmetry in the first and the second-to-last rows: the daily ceiling on
schedule-triggered flow interviews and the daily ceiling on Batch Apex method
executions are the same shape and the same number. Moving to Apex does not buy
headroom against *that* limit. What it buys is control of the transaction
boundary, and retry semantics.

---

## Example 1: Reading the Real Constraint Before Choosing a Pattern

**Context:** A nightly schedule-triggered flow re-scores 30,000 Contacts. It
started failing on governor limits.

**Problem:** The obvious diagnosis — "30,000 is too many for Flow" — is almost
always wrong, and leads to an expensive Apex rewrite that fails the same way. The
second-most-obvious one — costing the transaction against the synchronous SOQL
limit of 100 — is also wrong on any current flow, and produces the same rewrite.

**Solution:** Work out which limit is being hit, at what granularity, and under
which limit regime.

A schedule-triggered flow with an object and filter runs **one interview per
matching record**, and the platform groups those interviews into batches — 200
by default. Every interview in a batch shares one transaction's governor budget.
So the arithmetic is not 30,000 against anything; it is:

```text
per-interview cost × batch size  vs  per-transaction limit

Schedule-triggered flow on runtime version 61.0+   (asynchronous limits)
  1 Get Records × 200 interviews = 200 SOQL  vs  200 SOQL  -> fits, zero headroom
  1 Update      × 200 interviews = 200 DML   vs  150 DML   -> FAILS
  2 Get Records × 200 interviews = 400 SOQL  vs  200 SOQL  -> FAILS
  0 Get Records × 200 interviews =   0 SOQL  vs  200 SOQL  -> fine

The same flow on a pre-61.0 runtime version        (synchronous limits)
  1 Get Records × 200 interviews = 200 SOQL  vs  100 SOQL  -> FAILS
```

Read the error number before diagnosing anything. `Too many SOQL queries: 101`
says the flow is still on synchronous limits, and the cheapest fix is the runtime
version bump rather than a redesign. `: 201` says it is already on asynchronous
limits and the per-interview work genuinely has to come down. `Too many DML
statements: 151` says the queries were never the problem.

Treat the "fits, zero headroom" row as a failure in waiting: that transaction's
budget is shared with every Apex trigger, second flow, and managed package on
Contact, so a design that lands exactly on 200 breaks the next time anyone adds
anything to the object.

The flow fails at 200 records and at 30,000 records for exactly the same reason.
Volume is not the problem; a data operation inside the per-record path is.

**Why it works:** It correctly separates two questions that get conflated. "Does
each interview do too much?" is a bulkification question with a Flow answer.
"Are there too many interviews in a day?" is a capacity question with an org-wide
answer (250,000 per 24 hours, or licenses × 200). Only the second is a reason to
leave Flow.

**Diagnostic order:**

0. Read the flow's runtime version, so you know whether you are costing against
   100 SOQL / 10,000 ms or 200 SOQL / 60,000 ms. 61.0 is the threshold.
1. Count the Get Records and DML elements on the path an individual interview
   takes. Anything above zero, multiplied by 200, is your transaction cost — and
   cost DML separately from SOQL, because 150 is the tighter of the two and did
   not rise with the asynchronous change.
2. Check the daily interview volume against the org ceiling.
3. Check CPU: 60,000 ms asynchronous covers 200 interviews of formula-heavy work
   less comfortably than people expect, and a pre-61.0 flow has 10,000 ms.

Only if (2) is the binding constraint does the workload genuinely need a
different engine.

---

## Example 2: Wrong vs Right — Chunking With the Start Element

**Wrong (pre-Summer '26 workaround, still widely copied):**

```text
Scheduled Flow "Nightly Contact Rescore"
  Start: runs daily at 02:00, object Contact, filter Needs_Rescore__c = true
  └── Get Records: Scoring_Rule__c (all active rules)     <- 1 SOQL per interview
      └── Loop rules
          └── Assignment: accumulate score
      └── Update Records: $Record                          <- 1 DML per interview
```

Two per-interview data operations × a 200-interview batch = 200 SOQL and 200 DML
statements. On asynchronous limits the queries exactly fill their 200 ceiling and
the DML blows through 150, so it fails on the first full batch — on DML, not on
queries. (The same flow on a pre-61.0 runtime version fails on both.) The point
survives either way, but the fix you would prescribe from "SOQL is over" and from
"DML is over" are not the same fix.

The workaround teams reached for was a control record holding a "last processed
Id" and a flow scheduled every fifteen minutes to grab the next slice. That
works, and it is a lot of moving parts to maintain for what is now a field on the
Start element.

**Right:**

```text
Scheduled Flow "Nightly Contact Rescore"
  Start: runs daily at 02:00, object Contact, filter Needs_Rescore__c = true
         Batch size: 50                                    <- runtime version 63.0+
  └── Get Records: Scoring_Rule__c                          <- still 1 per interview
      ...
```

Setting the batch size to 50 brings the per-transaction cost to 50 SOQL and 50
DML — comfortably under both limits, with room left for the other automation
sharing the transaction. The flow now runs four times as many transactions to
process the same set, each one safe.

**Why it works, and what it does not do:** Lowering the batch size divides the
per-transaction cost by the same factor it divides throughput. It is the correct
tool when the per-interview work is genuinely irreducible — a callout, an
invocable Apex call that must be per-record, a formula whose CPU cost cannot be
amortized. It is the *wrong* tool when the per-interview work is a query that
could have been hoisted, because it pays four times the transaction overhead to
avoid fixing the actual defect.

**Requirement:** custom batch size needs the flow on runtime version 63.0 or
later. A flow left on an older runtime version silently keeps the 200 default,
which is a confusing way to discover that the field you set had no effect.

**Setup path:** open the flow → click the **Start** element → select the object →
set the maximum batch size.

---

## Example 3: Fan-Out via Platform Event, and Its Real Ceiling

**Context:** A one-off cleanup has to touch 120,000 Contacts. The admin team has
no Apex resource this sprint.

**Problem:** A single scheduled flow processes the set in 200-interview batches
serially. If each batch takes a couple of seconds, that is on the order of twenty
minutes of wall clock — usually fine. The reason to fan out is not speed; it is
that a single long-running scheduled flow has no partial-failure story. One bad
record fails its interview and the rest continue, but you have no record of which
ones failed and no way to retry just those.

**Solution:** Publish a chunk event per slice and let a subscriber process each
slice in its own transaction, with its own log row.

```text
Scheduled Flow "Cleanup Dispatcher"              (runs every 15 minutes)
  Get Records: Contact where Needs_Cleanup__c = true, limit 5000, store Ids
  Loop in slices of 200
    Assignment: build Cleanup_Chunk__e record (chunkId, comma-joined Ids)
    Assignment: add to eventCollection
  Create Records: eventCollection                <- ONE publish, after the loop
  Create Records: Cleanup_Run__c (chunk count, started timestamp)

Platform-Event-Triggered Flow "Cleanup Worker"
  Start: object Cleanup_Chunk__e
  Get Records: Contact where Id IN (parsed Ids)
  Loop / Assignment: compute new values
  Update Records: the collection                 <- ONE DML
    fault -> Create Records: Cleanup_Chunk_Log__c (chunkId, fault message)
```

**Why it works:** Each chunk is an independent transaction with its own fault
path and its own log row, so a failure is scoped to 200 records and is
identifiable by chunk id. Re-running a failed chunk is a matter of republishing
one event.

**The ceilings this design runs into — and the one it does not:**

- The publish is charged against the **publishing** allocation: 250,000 events
  per hour on Enterprise, Performance, and Unlimited; 50,000 on Developer. At 200
  records per event, 120,000 records is 600 events. Not close.
- The **delivery** allocation — 25,000 per 24 hours on Enterprise — does *not*
  apply here. Flows, Apex triggers, and Process Builder consume the publishing
  allocation, not the delivery one. This is the single most common reason a
  workable fan-out design gets rejected.
- The subscriber is itself batched at up to 200 event messages per transaction.
  With one Get and one Update per event, a full subscriber batch is 200 SOQL
  against a limit of 100. That 100 is deliberate and is *not* the asynchronous
  200 the publishing scheduled flow enjoys: "when governor limits are different
  for synchronous and asynchronous Apex, the synchronous limits apply to platform
  event triggers." Fanning out to events lowers the per-transaction budget.
  Either keep the subscriber's per-event cost at one data operation and lower its
  batch size, or design the subscriber to handle a batch of chunks rather than a
  chunk.

That last point is the one that catches people: fanning out at the publisher
does not exempt the subscriber from being bulkified. See
`flow/flow-and-platform-events`.

---

## Example 4: The Checkpoint Pattern, and Why It Is Now a Last Resort

**Context:** A one-shot 400,000-record backfill with no Apex resource.

**Problem:** 400,000 exceeds what a single scheduled run should attempt, and the
work has to survive being interrupted.

**Solution:**

```text
Custom object Backfill_State__c (one record, protected by a validation rule
  that prevents a second one):
    Last_Processed_Id__c   Text(18), External Id
    Records_Processed__c   Number
    Status__c              Picklist: Running / Paused / Complete
    Last_Run_At__c         DateTime

Scheduled Flow "Backfill Runner"                 (every 15 minutes)
  Get Records: Backfill_State__c
  Decision: Status = 'Running'?  -> no: End
  Get Records: Contact
      where Id > {!State.Last_Processed_Id__c}
      sort by Id ascending, limit 2000
  Decision: any records?  -> no: set Status = 'Complete', End
  Loop / Assignment: build the update collection
  Update Records: collection                     <- ONE DML
    fault -> set Status = 'Paused', log, End
  Assignment: Last_Processed_Id__c = last Id in the collection
  Update Records: Backfill_State__c
```

**Why it works:** Ordering by Id ascending and filtering `Id >` the checkpoint
gives a total order with no gaps and no re-processing, which is what makes the
job resumable and idempotent. The `Status` field gives a human an off switch that
does not require deactivating the flow. The fault path pauses rather than
continuing, so a systematic failure stops after one batch instead of after
twenty thousand.

**Why it is a last resort now:** this pattern predates a custom batch size on the
Start element, and it exists to work around a constraint that a field can now
address for recurring work. It is still the right answer for a genuine one-shot
backfill where you need an off switch, a progress counter, and a resume point —
none of which the platform gives you — but reach for it deliberately, not by
habit.

**The trap in the ordering:** `Id >` on a Salesforce Id is a string comparison
over an 18-character case-sensitive value. It gives a stable total order within
one object, which is all this pattern needs. Do not extend the same trick across
two objects or assume Id order means creation order.

---

## Example 5: The Escalation to Apex, Stated Honestly

**Context:** The nightly job is now 900,000 records and the per-record work
involves a callout to a pricing service.

**Problem:** Teams reach for Batch Apex as "the thing that handles volume."
Being specific about what it actually buys prevents both premature and overdue
escalation.

**Solution:** Escalate for one of these reasons, not for volume alone.

| Reason to leave Flow | Why Flow cannot do it |
|---|---|
| You need retry semantics with a known outcome | Flow has no finalizer. A Queueable's `System.Finalizer` runs whether the job succeeded or threw, sees `ParentJobResult.SUCCESS` or `UNHANDLED_EXCEPTION`, and can re-enqueue a failed job up to five times |
| The per-record work is a callout | Callouts cannot follow DML in the same transaction; Flow's callout affordances are narrower and harder to sequence |
| You need state carried across transactions | `Database.Stateful` on a Batchable keeps instance member variables between transactions (static variables still reset) |
| The scan is a genuine multi-million-record sweep | `Database.QueryLocator` streams the set; a Flow's Get Records is bounded by 50,000 rows per transaction |
| You need chained steps that survive partial failure | Queueable chaining plus a finalizer gives explicit control; a scheduled flow's next run is not a retry |

And what escalation does **not** buy:

- **Not headroom against the daily ceiling.** Batch Apex method executions are
  capped at 250,000 per 24 hours or user licenses × 200, whichever is greater —
  the same shape and number as the schedule-triggered flow interview cap.
- **Not unlimited concurrency.** Up to 5 batch jobs can be queued or active at
  once, with up to 100 more Holding in the flex queue.
- **Not per-transaction limits.** Batch Apex gets the asynchronous ceilings — 200
  SOQL, 60,000 ms CPU, 12 MB heap — which are the *same* ceilings a
  schedule-triggered flow on runtime version 61.0 or later already has. Escalating
  does not raise them, and 150 DML statements is the same number in both engines.
  A badly scoped batch breaches them exactly like a badly batched flow.

**Keep the admin-visible surface:** expose the Apex entry point as an Invocable
Action and keep a thin scheduled flow as the trigger. Admins keep an
orchestration view they can read and disable; the heavy lifting sits where the
control is.

`standards/decision-trees/async-selection.md` formalizes the choice between
`@future`, Queueable, Batch, Schedulable, Platform Events, and Scheduled Flow.
Cite the branch that resolved it rather than re-deriving it here.

---

## Anti-Pattern: "Just Increase the Batch Size"

**What practitioners do:** Hit a governor limit on a scheduled flow and raise the
batch size, reasoning that fewer, larger transactions means less overhead.

**What goes wrong:** It is exactly backwards. Per-transaction limits are consumed
by `per-interview cost × batch size`. Raising the batch size raises the numerator
on the wrong side of the inequality. And 200 is the maximum, so the lever only
moves down anyway — a team that "raised it" was already at the ceiling and
changed nothing.

**Correct approach:** Lower the batch size to buy governor headroom at the cost
of throughput, and only when the per-interview cost is irreducible. When the
per-interview cost is a query or a DML that could have been hoisted out of the
per-record path, fix that instead — it is free, where a smaller batch is not.

---

## Anti-Pattern: Calling an Invocable Action Inside a Flow Loop

**What practitioners do:** Loop a collection and call an invocable Apex action per
iteration, because that reads naturally on the canvas.

**What goes wrong:** Each call is a separate invocation. Two hundred iterations
is two hundred Apex entries, each with its own queries and DML inside, and the
Apex author's careful bulkification is defeated by the caller. This is the
single most common way a "we moved it to Apex" migration produces a job that is
slower and less reliable than the flow it replaced.

**Correct approach:** Build the collection in the loop and pass the whole
collection to the invocable once. Invocable methods take a `List<>` of requests
and return a `List<>` of results precisely so this works; a signature that does
not is a defect in the Apex, not a reason to loop.

---

## Anti-Pattern: Treating the Next Scheduled Run as a Retry

**What practitioners do:** Omit failure handling on the theory that "it runs
again tomorrow, so it'll pick up whatever failed."

**What goes wrong:** It only picks up what the *filter* still matches. If the
failure happened after the flow had already flipped the record's "needs
processing" flag — or if the failure is systematic rather than transient — the
record is now permanently excluded and nobody knows. Six months later a report
shows a cohort that was never processed and no log explains why.

**Correct approach:** Flip the flag last, after the work has succeeded, so a
failed record naturally re-qualifies. Log every failure with enough context to
identify the record. Alert on a rate change rather than on individual failures.
And distinguish transient from systematic: an unattended retry loop against a
systematic failure is an infinite loop that consumes the daily interview
allocation.
