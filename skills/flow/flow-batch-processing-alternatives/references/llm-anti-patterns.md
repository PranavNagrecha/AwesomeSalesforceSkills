# LLM Anti-Patterns — Flow Batch Processing Alternatives

Mistakes AI assistants reliably make when a Flow job outgrows a single run.

---

## Anti-Pattern 1: Recommending Batch Apex for Any Volume Concern

**What the LLM generates:** "Switch to `Database.Batchable`" as soon as record
counts are mentioned, with volume as the sole justification.

**Why it happens:** "Batch" is the word the training data associates with
"large," and the escalation reads as the responsible, senior recommendation.

**Correct pattern:** name what Apex actually buys — retry semantics with a known
outcome (`System.Finalizer`), callouts, cross-transaction state
(`Database.Stateful`), `QueryLocator` streaming past the 50,000-row transaction
ceiling, control of the transaction boundary. It does **not** buy daily headroom:
Batch Apex method executions are capped at 250,000 per 24 hours or user licenses
× 200, the same number and formula as schedule-triggered flow interviews.

**Detection hint:** an escalation recommendation whose only stated reason is a
record count.

---

## Anti-Pattern 2: "Increase the Batch Size"

**What the LLM generates:** advice to raise the scheduled flow's batch size to
reduce transaction overhead after a governor limit error.

**Why it happens:** in most batch-processing systems larger batches are more
efficient, and the model transfers that prior. Nothing in the phrasing of a
governor limit contradicts it.

**Correct pattern:** per-transaction limits are consumed by `per-interview cost ×
batch size`, so raising the batch size makes it worse. The settable range is 1 to
200 and 200 is already the default — the lever only moves down. Lower it to buy
headroom when per-interview work is irreducible; hoist the query out of the
per-record path when it is not.

**Detection hint:** the words "increase," "raise," or "larger" applied to batch
size in a limits discussion.

---

## Anti-Pattern 3: Analysing Governor Limits Per Interview

**What the LLM generates:** "this flow uses one SOQL query, well within the limit
of 100" — for a scheduled flow that will run 30,000 interviews.

**Why it happens:** the flow canvas shows one Get Records, and the limit is
stated per transaction. The model does not model the interview-to-transaction
batching in between.

**Correct pattern:** interviews are grouped into batches of up to 200, and every
interview in a batch shares one transaction's budget. One query per interview is
200 queries per transaction, and one Update per interview is 200 DML statements.
State the multiplication explicitly whenever you analyse a scheduled or
record-triggered flow — and cost SOQL and DML separately, because they sit against
different ceilings (see Anti-Pattern 10).

**Detection hint:** a limits analysis that counts elements without multiplying by
a batch size.

---

## Anti-Pattern 4: Calling an Invocable Action Inside a Loop

**What the LLM generates:** a Loop whose body is an Apex Action call, described
as "delegating the heavy lifting to Apex."

**Why it happens:** it mirrors the imperative shape of the requirement and reads
naturally on the canvas. The model's "call a function per item" prior is very
strong.

**Correct pattern:** build the collection in the loop and pass the whole
collection to the invocable once. Invocable methods take a `List<>` of requests
and return a `List<>` of results precisely so this works. A per-iteration call
defeats the Apex author's bulkification from outside the class, which is why
"we moved it to Apex" migrations sometimes end up slower than the flow.

**Detection hint:** an `<actionCalls>` element between a `<loops>` element and its
`nextValueConnector` target.

---

## Anti-Pattern 5: Presenting the Checkpoint Pattern as the Default

**What the LLM generates:** an elaborate `Batch_State__c` control record with a
last-processed Id, a fifteen-minute schedule, and resume logic — as the first
answer to any high-volume scheduled flow.

**Why it happens:** it is the pattern that dominated Flow blog content before
custom batch sizes existed, so it is heavily represented and reads as
sophisticated.

**Correct pattern:** for recurring work, set the batch size on the Start element
(runtime version 63.0 or later) and stop. The checkpoint pattern is still right
for a genuine one-shot backfill that needs an off switch, a progress counter, and
a resume point — none of which the platform provides — but it is a lot of moving
parts to maintain when a field would do.

**Detection hint:** a control-record design proposed for a *recurring* nightly
job with no mention of the Start element's batch size.

---

## Anti-Pattern 6: Rejecting a Fan-Out on the Delivery Allocation

**What the LLM generates:** "Platform Events won't work here — Enterprise only
allows 25,000 event deliveries per day."

**Why it happens:** the delivery allocation is prominent in the allocations
table and reads as the binding one. The exclusion is a sentence of qualifying
text.

**Correct pattern:** flows, Apex triggers, and Process Builder are explicitly
excluded from the delivery allocation; they consume the **publishing** allocation
(250,000 per hour on Enterprise, Performance, and Unlimited; 50,000 on
Developer). The delivery figure bounds Pub/Sub API, CometD, empApi, and event
relays. Size internal fan-outs against publishing, at peak hour.

**Detection hint:** a delivery allocation cited in a design whose subscribers are
all internal.

---

## Anti-Pattern 7: Assuming the Next Run Retries the Failures

**What the LLM generates:** a scheduled flow with no failure handling and a note
that failed records will be reprocessed on the next run.

**Why it happens:** it is true for a well-designed filter and false for the
design the model just wrote, and the difference is not visible on the canvas.

**Correct pattern:** the next run re-evaluates the filter. If the flow flipped
the record's "needs processing" flag before the work succeeded, the record no
longer qualifies and is permanently excluded with no log entry. Flip the flag
last. Log every failure. And distinguish transient from systematic before
building any automatic retry — an unattended retry against a systematic failure
consumes the org's daily interview allocation on records that will never
succeed.

**Detection hint:** an Update that sets a processed flag positioned before the
element doing the real work.

---

## Anti-Pattern 8: Expecting Chunking to Fix Mixed DML

**What the LLM generates:** "process the User updates in smaller batches to avoid
the Mixed DML error."

**Why it happens:** Mixed DML surfaces as a per-transaction error, and smaller
transactions is the model's general answer to per-transaction errors.

**Correct pattern:** Mixed DML restricts *combining* setup objects (User, Group,
GroupMember, permission set assignments) with non-setup objects in one
transaction. Chunking makes transactions smaller, not homogeneous — every chunk
still touches both kinds. Split the setup-object DML into a separate async step:
a scheduled path, a platform event, or a Queueable.

**Detection hint:** a batch-size or chunk-count recommendation offered in
response to a `MIXED_DML_OPERATION` error.

---

## Anti-Pattern 9: Ignoring the Concurrency Ceiling When Fanning Out to Apex

**What the LLM generates:** a design that submits a dozen Batch Apex jobs in
parallel to "process the segments simultaneously."

**Why it happens:** parallelism is the natural answer to throughput, and nothing
in the Batchable API signals a concurrency cap.

**Correct pattern:** up to 5 batch jobs can be queued or active concurrently,
with up to 100 more Holding in the flex queue — and that budget is org-wide,
shared with managed packages. Design for a small number of long jobs and use
`Database.executeBatch`'s scope parameter (200 default, 2,000 maximum for a
`QueryLocator`) to size the transaction, rather than splitting into more jobs.

**Detection hint:** more than five concurrent `Database.executeBatch` calls in a
proposed design, or any wording implying unbounded parallel batch jobs.

---

## Anti-Pattern 10: Costing a Scheduled Flow Against the Synchronous SOQL Limit

**What the LLM generates:** "200 interviews × 1 Get Records = 200 SOQL against a
limit of 100, so this flow cannot work in Flow — move it to Batch Apex."

**Why it happens:** 100 is the SOQL number that dominates training data, and the
`Too many SOQL queries: 101` error string is the most-quoted governor failure on
the internet. The asynchronous column exists in the same table but is rarely the
one quoted, and nothing on the Flow canvas announces which regime a flow is in.

**Correct pattern:** schedule-triggered flows run under **asynchronous**
per-transaction limits from runtime version 61.0 onward — 200 SOQL, 60,000 ms
CPU, 12 MB heap — under the *Improve Scheduled Flow Performance with Updated
Limits* release update. Establish the flow's runtime version before you do the
arithmetic. Then cost DML separately: 150 statements, unchanged on both sides, is
the limit a one-Update-per-interview flow actually breaches. The conclusion
"therefore rewrite it in Apex" is doubly wrong, because Batch Apex runs against
those same asynchronous ceilings.

**Detection hint:** the number 100 used as the SOQL ceiling in an analysis of a
schedule-triggered flow, or any limits conclusion that never names the flow's
runtime version.
