# LLM Anti-Patterns — Flow Transaction Finalizer Patterns

Mistakes AI assistants reliably make around post-commit work in Flow.

---

## Anti-Pattern 1: The Zero-Minute Scheduled Path

**What the LLM generates:** "add a scheduled path set to 0 minutes after the
record is created" as the way to run work after commit.

**Why it happens:** scheduled paths have far more documentation and blog coverage
than the asynchronous path, and a zero offset is a plausible-looking way to mean
"immediately." It usually works, which keeps the pattern alive.

**Correct pattern:** the **Run Asynchronously** path is the construct for "after
the original transaction for the triggering record is successfully committed."
It cannot be given a time, which is the point. Scheduled paths are for real
offsets — three days before renewal, one hour after escalation. Conflating them
makes "why didn't this run" much harder to answer, because the two fail
differently.

**Detection hint:** a scheduled path with an offset of 0, or the phrase
"immediate scheduled path."

---

## Anti-Pattern 2: A Callout in an After-Save Flow

**What the LLM generates:** an HTTP Callout action, or an invocable Apex callout,
placed in the immediate path of an after-save record-triggered flow.

**Why it happens:** "after save" reads as "after the save is done," and the model
does not distinguish the save step from the transaction commit.

**Correct pattern:** after-save runs after the record's save step but still inside
the transaction, before commit. Callouts cannot follow DML in the same
transaction, and an effect that escapes before commit survives a rollback the
database does not. Put the callout in the **Run Asynchronously** path, which is
what it exists for.

**Detection hint:** an `<actionCalls>` performing a callout on the immediate path
of a flow whose `<triggerType>` is `RecordAfterSave`.

---

## Anti-Pattern 3: Claiming Flow Has a Finalizer

**What the LLM generates:** advice to "add a finalizer to the flow," or a fault
path described as "the flow's finalizer," or an invented Flow element named
Finalize.

**Why it happens:** the skill name and the requirement both contain the word, and
the model reaches for the nearest Flow construct that resembles one.

**Correct pattern:** Flow has no finalizer. A fault connector fires when the
element it guards throws and does not fire on an uncatchable limit exception or
on the outcome of work in another transaction. `System.Finalizer` — one per
Queueable, reading `ParentJobResult.SUCCESS` or `UNHANDLED_EXCEPTION` from
`FinalizerContext` — is Apex only. A requirement that needs post-*outcome*
execution is a requirement to cross into Apex.

**Detection hint:** the word "finalizer" describing anything inside flow
metadata.

---

## Anti-Pattern 4: Assuming a Finalizer Retries Indefinitely

**What the LLM generates:** "the finalizer will re-enqueue the job until it
succeeds," with no give-up branch and no attempt tracking.

**Why it happens:** retry-until-success is the default shape of every retry
example in the training data, and the ceiling is a single sentence in the
documentation.

**Correct pattern:** a Queueable that failed with an unhandled exception can be
re-enqueued five times by a finalizer; the count resets on success. There is one
finalizer per job and it may enqueue a single asynchronous job. Design the
give-up branch and write a record when you reach it — a silent stop at the
platform ceiling looks exactly like success in most logs.

**Detection hint:** a re-enqueue with no attempt counter and no terminal branch.

---

## Anti-Pattern 5: Non-Idempotent Post-Commit Work

**What the LLM generates:** an asynchronous path or event subscriber that
performs an external effect — a charge, an order, a notification — with no
duplicate guard.

**Why it happens:** the happy path is what the prompt asked for, and duplicate
delivery is a property of the platform rather than of the code the model is
writing.

**Correct pattern:** every mechanism here can run twice. An asynchronous path can
be re-queued, events are delivered at least once, and a finalizer re-enqueue
replays the whole Queueable body including the parts that already succeeded.
Guard locally with a record keyed on a deterministic idempotency key, and pass
the same key to the external system where it supports one.

**Detection hint:** a callout with an external side effect and no preceding
"already processed?" check.

---

## Anti-Pattern 6: Using the Interview GUID as the Idempotency Key

**What the LLM generates:** `$Flow.InterviewGuid` (or `$Flow.CurrentDateTime`) as
the deduplication key, which looks unique and correct.

**Why it happens:** it is the most unique-looking value available in a flow, and
"unique identifier" is what an idempotency key sounds like it needs.

**Correct pattern:** the key must be identical on the retry. The interview GUID
differs per interview, so it is different on precisely the run you are trying to
suppress. Derive the key from the record: Id plus the field values that define
this attempt, or Id plus `LastModifiedDate`.

**Detection hint:** `$Flow.InterviewGuid` or `$Flow.CurrentDateTime` assigned to
anything named key, token, or idempotency.

---

## Anti-Pattern 7: The Fault Path as a Compensating Transaction

**What the LLM generates:** a fault path that "undoes" earlier changes by
updating the same records back to their previous values.

**Why it happens:** compensating transactions are the standard distributed-systems
answer and the fault path is the nearest available hook.

**Correct pattern:** the fault path runs inside the same transaction as the
element that faulted, where the platform's own rollback is already going to
handle uncommitted DML. A manual compensation there either duplicates the
rollback or writes state the rollback discards — sometimes triggering downstream
automation on a record about to disappear. Fault paths record and stop. Use
**Custom Error** (record-triggered) or **Roll Back Records** (screen) to stop
deliberately. Real compensation for a committed external effect belongs in a
later transaction.

**Detection hint:** an `<recordUpdates>` on the fault path targeting the same
object the faulted element was writing.

---

## Anti-Pattern 8: Treating an Invocable Action as Automatically Asynchronous

**What the LLM generates:** "call the Apex action so the work happens
asynchronously and doesn't block the save."

**Why it happens:** "Apex" and "async" are strongly associated, and the flow
author cannot see the method body from the canvas.

**Correct pattern:** an invocable runs inline in the calling transaction unless
its body explicitly enqueues async work. It shares the caller's governor budget
and its rollback. If the invocable is the async boundary, the flow must not
expect a result from it — the result does not exist yet.

**Detection hint:** a flow that calls an invocable and then branches on a returned
value, described as asynchronous.

---

## Anti-Pattern 9: "Async Means No Governor Limits"

**What the LLM generates:** moving heavy work to an asynchronous path with the
justification that limits no longer apply.

**Why it happens:** the async ceilings are higher, and "asynchronous" carries a
connotation of unbounded background work from other platforms.

**Correct pattern:** asynchronous and scheduled paths are subject to the
asynchronous per-transaction Apex limits — 200 SOQL, 60,000 ms CPU, 12 MB heap.
Roughly a 6× CPU budget and a 2× query budget against synchronous, and still
ceilings. Work that needs more needs chunking or Batch Apex; see
`flow/flow-batch-processing-alternatives`.

**Detection hint:** the phrase "no governor limits" or "limits don't apply"
anywhere near an asynchronous path.
