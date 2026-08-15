# Gotchas — Flow Batch Processing Alternatives

Non-obvious behaviours that decide whether a high-volume Flow job survives.

---

## Gotcha 1: Governor Limits Are Per Transaction, Not Per Interview

**What happens:** A scheduled flow that does one Get Records and one Update per
record fails on governor limits. The author checks the flow, counts one of each,
and cannot see the problem.

**When it occurs:** Always, and it is the single most consequential
misunderstanding in this domain. A schedule-triggered flow with an object and
filter runs one interview per matching record, and the platform groups those
interviews into batches. Every interview in a batch shares **one transaction's**
governor budget. One query and one DML per interview × a 200-interview batch is
200 SOQL and 200 DML statements in a single transaction.

**Which ceiling that lands against:** schedule-triggered flows run under the
**asynchronous** per-transaction limits from runtime version 61.0 onward — 200
SOQL, 60,000 ms CPU, 12 MB heap — which is what the *Improve Scheduled Flow
Performance with Updated Limits* release update changed. So the 200 queries sit
exactly on the ceiling rather than over it, and the DML limit (150, unchanged on
both sides) is what actually breaks. A flow still on a pre-61.0 runtime version
gets the synchronous 100 and fails on SOQL instead. The error number tells you
which one you are in: `Too many SOQL queries: 101` versus `: 201`, versus
`Too many DML statements: 151`.

**How to avoid:** Compute `per-interview cost × batch size` and compare it to the
per-transaction limit **for the regime the flow is actually in**. The flow fails
at 200 records for the same reason it fails at 300,000 — volume is not the
variable. Either hoist the data operation out of the per-record path, or lower
the batch size. And treat a full 200 queries as a failure even where it
technically fits: the transaction budget is shared with every Apex trigger,
second flow, and managed package on the object, so landing exactly on the ceiling
leaves them nothing.

---

## Gotcha 2: The Batch Size Field Does Nothing Below Runtime Version 63.0

**What happens:** An admin sets a batch size of 25 on the Start element, saves,
and the flow still fails exactly as before.

**When it occurs:** When the flow is on a runtime version earlier than 63.0.
Custom batch sizes for scheduled flows require runtime version 63.0 or later; an
older flow silently keeps the 200 default.

**How to avoid:** Check the flow version's API/runtime version before concluding
the setting had no effect. Raising it is itself a change with consequences — a
flow's behaviour is versioned, and bumping the version can pick up other run-time
changes at the same time. Test the bump, do not just save through it.

**Two thresholds sit close together here, and they are different things:** 61.0
moves a schedule-triggered flow onto asynchronous per-transaction limits, 63.0
enables the custom batch size. A flow on 63.0 has both, so the batch-size lever
and the 200-SOQL ceiling always arrive together. A flow on 61.0 or 62.0 has the
higher limits and no way to size the batch.

---

## Gotcha 3: You Can Only Lower the Batch Size, Never Raise It

**What happens:** A team hits a governor limit and "increases the batch size" to
reduce transaction overhead, then reports that it made no difference.

**When it occurs:** Whenever the intuition that bigger batches are more efficient
is applied to governor limits. The settable range is 1 to 200 and the default is
already 200 — there is nothing above it. Even if there were, raising it would
multiply the per-transaction cost, which is the wrong direction.

**How to avoid:** Treat the batch size as a headroom lever that only moves down.
It buys governor safety at a proportional cost in throughput, and it is the right
tool only when the per-interview work is genuinely irreducible.

---

## Gotcha 4: The Daily Interview Ceiling Is Org-Wide and Shared

**What happens:** A new scheduled flow is added and an unrelated existing one
stops running.

**When it occurs:** Schedule-triggered flow interviews are capped at 250,000 per
24 hours, or the number of user licenses in the org multiplied by 200, whichever
is greater. That is an *org* budget, not a per-flow one, so a new high-volume job
consumes headroom every other scheduled flow was relying on.

**How to avoid:** Inventory the org's scheduled flows and their daily record
counts before adding another. And note the arithmetic on the licence side: a
small org with 100 licences gets `max(250,000, 20,000)` = 250,000 — the licence
formula only raises the ceiling for large orgs, never lowers it.

---

## Gotcha 5: Moving to Batch Apex Does Not Raise That Ceiling

**What happens:** A team migrates a scheduled flow to Batch Apex specifically to
escape the daily interview limit, and hits an identically shaped wall.

**When it occurs:** The maximum number of Batch Apex method executions per
24-hour period is 250,000, or the number of user licenses multiplied by 200,
whichever is greater — the same number and the same formula as the flow
interview cap.

**How to avoid:** Escalate to Apex for what it actually buys — retry semantics
with a known outcome, callouts, cross-transaction state via `Database.Stateful`,
`QueryLocator` streaming past the 50,000-row transaction ceiling, and control of
the transaction boundary. Not for daily headroom. If the daily ceiling is the
binding constraint, the fix is to process fewer records (tighter filters,
incremental rather than full scans), not a different engine.

---

## Gotcha 6: Only Five Batch Jobs Run at Once

**What happens:** A fan-out design submits fifteen Batch Apex jobs and most of
them sit in Holding for a long time, or a nightly job is delayed behind an
unrelated one.

**When it occurs:** Up to 5 batch jobs can be queued or active concurrently, with
up to 100 more held in the Apex flex queue. It is an org-wide budget shared with
managed packages, which is why the contention often comes from somewhere nobody
owns.

**How to avoid:** Design for a small number of long jobs rather than many short
ones, and use `Database.executeBatch`'s scope parameter to size the transaction
rather than splitting into more jobs. Scope defaults to 200 and caps at 2,000 for
a `QueryLocator`; the documentation notes the optimal scope is a factor of 2,000.

---

## Gotcha 7: `Database.Stateful` Keeps Instance Variables, Not Static Ones

**What happens:** A Batchable accumulates a running total in a `static` variable,
implements `Database.Stateful`, and the total resets to zero every 200 records.

**When it occurs:** Always. With `Database.Stateful`, only instance member
variables retain their values between transactions; static member variables are
reset. Without the interface, everything resets.

**How to avoid:** Use instance fields for anything that must survive across
`execute` invocations. This matters to a Flow author when a chunked job is
escalated to Apex and someone ports "the running count" without noticing that
Flow variables and Apex statics behave differently across transaction
boundaries.

---

## Gotcha 8: Fanning Out Does Not Exempt the Subscriber From Bulkification

**What happens:** A publisher carefully chunks 120,000 records into 600 events,
and the subscriber flow fails on governor limits anyway.

**When it occurs:** A platform-event-triggered flow is itself batched, at up to
200 event messages per transaction. One Get Records per event in a full
subscriber batch is 200 queries against a limit of 100. The chunking happened on
the wrong side.

**And here 100 is the right number, unlike Gotcha 1.** Platform event subscribers
do not inherit the scheduled flow's asynchronous ceiling: the Platform Events
Developer Guide states that "when governor limits are different for synchronous
and asynchronous Apex, the synchronous limits apply to platform event triggers,"
because they are short-lived processes that execute in batches quickly. Fanning
out to events therefore *lowers* the per-transaction budget relative to the
scheduled flow that published them.

**How to avoid:** Bulkify the subscriber as carefully as the publisher — collect
across the batch, one Get with an `In` filter, one Update against the collection
— or lower the subscriber's batch size. See `flow/flow-and-platform-events`.

---

## Gotcha 9: The Delivery Allocation Is Not What Bounds a Flow Fan-Out

**What happens:** A workable Platform Event fan-out design is rejected because
"we only get 25,000 event deliveries a day."

**When it occurs:** Whenever the delivery allocation is read as universal. Apex
triggers, flows, and Process Builder are explicitly excluded from the delivery
allocation — they consume the *publishing* allocation instead (250,000 per hour
on Enterprise, Performance, and Unlimited; 50,000 on Developer). The delivery
figure applies to Pub/Sub API, CometD, empApi, and event relays.

**How to avoid:** Size an internal Flow-to-Flow fan-out against publishing, per
hour, at peak. Reserve the delivery arithmetic for external subscribers.

---

## Gotcha 10: A Scheduled Flow Guarantees No Ordering

**What happens:** A job that assigns sequence numbers, or that assumes parent
records are processed before children, produces inconsistent results between
runs.

**When it occurs:** Interviews within and across batches carry no ordering
guarantee. Nothing in the platform promises record A is processed before record
B, and nothing promises batch boundaries fall in the same place twice.

**How to avoid:** Design the per-record work to be order-independent and
idempotent. If ordering is genuinely required, it has to be encoded in the data
(process parents in one scheduled run and children in a later one, keyed off a
status field) rather than assumed from the engine. The checkpoint pattern's `Id >`
ordering is the exception that proves the rule: it works because it explicitly
sorts, not because the engine ordered anything.

---

## Gotcha 11: Mixed DML Survives Chunking

**What happens:** A chunked job that touches User or Group alongside a standard
object fails with a Mixed DML error, and the team assumes smaller chunks will
help.

**When it occurs:** Mixed DML is a per-transaction restriction on combining setup
objects (User, Group, GroupMember, Permission Set assignments, and similar) with
non-setup objects. Chunking makes transactions smaller; it does not make them
homogeneous. Every chunk still touches both kinds.

**How to avoid:** Split the setup-object DML into a separate asynchronous step —
a scheduled path, a platform event, or a Queueable — so the two kinds of DML land
in different transactions. Sizing does not enter into it.

---

## Gotcha 12: The Next Scheduled Run Is Not a Retry

**What happens:** A record fails, the team assumes tomorrow's run will pick it
up, and it never does.

**When it occurs:** When the flow flips the record's "needs processing" flag
before the work succeeds, or when the failure is systematic. The next run
re-evaluates the *filter*, and a record that no longer matches is now permanently
excluded with no log entry.

**How to avoid:** Flip the flag last, after the work has succeeded, so a failed
record naturally re-qualifies. Log every failure with the record Id. And
distinguish transient from systematic before building anything that retries
automatically — an unattended retry against a systematic failure burns the org's
daily interview allocation on records that will never succeed.

---

## Gotcha 13: A Long-Running Chunked Job Is Not Isolated From Business Hours

**What happens:** A backfill running every fifteen minutes starts colliding with
users, producing `UNABLE_TO_LOCK_ROW` errors that were absent in overnight
testing.

**When it occurs:** Any chunked pattern that spreads work across hours rather
than concentrating it. Contention that a single overnight batch never sees
becomes routine when the same work is spread across a business day, particularly
on records with hot parents.

**How to avoid:** Gate the chunk runner on a time window as well as a status
flag — the `Status__c` field in the checkpoint pattern is the natural place — and
size chunks so a single transaction holds its locks briefly. Record contention
itself is `flow/flow-record-locking-and-contention`; what belongs here is
knowing that spreading a job out trades one failure mode for another rather than
removing it.
