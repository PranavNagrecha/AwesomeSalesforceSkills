# Gotchas — Flow Transaction Finalizer Patterns

Non-obvious behaviours around post-commit work in Flow.

---

## Gotcha 1: Flow Has No Finalizer, and Nothing Substitutes for One

**What happens:** A team builds an elaborate fault-path structure trying to
guarantee "this always logs whether it worked or not," and it still misses cases.

**When it occurs:** Always. A fault connector fires when the element it guards
throws. It does not fire when the interview is killed by an uncatchable limit
exception, and it cannot report on work that is still running in another
transaction. Apex's `System.Finalizer` runs after the Queueable completes
*either way* and can read `ParentJobResult.SUCCESS` or `UNHANDLED_EXCEPTION`.
Flow has nothing equivalent.

**How to avoid:** Be explicit about which guarantee the requirement needs.
Post-commit execution is available in Flow three different ways. Post-*outcome*
execution is not available in Flow at all, and a requirement that needs it is a
requirement to cross into Apex — not a reason to build more fault paths.

---

## Gotcha 2: The Asynchronous Path Is Not a Zero-Minute Scheduled Path

**What happens:** A zero-offset scheduled path is used for "run right after
commit." It mostly works, and then somebody debugs a case where it did not run
and cannot tell which construct they are looking at.

**When it occurs:** Whenever the two are conflated. The **Run Asynchronously**
path runs after the original transaction for the triggering record is
successfully committed, and you cannot define a time for it. A scheduled path
computes its run time from a date/time field, so a null or past-dated field
produces behaviour that has no analogue in the asynchronous case.

**How to avoid:** Use the asynchronous path for "after commit, as soon as
practical." Reserve scheduled paths for genuinely time-based requirements. Both
queue on the Time-Based Workflow page in Setup, so the monitoring surface is the
same — which is exactly why the distinction has to be made in the design.

---

## Gotcha 3: The Asynchronous Path Exists Only on After-Save Flows

**What happens:** An author looks for the Run Asynchronously option on a
before-save record-triggered flow and cannot find it.

**When it occurs:** Asynchronous paths are available for record-triggered flows
that run after the record is saved. Before-save flows cannot perform DML and
have no async path.

**How to avoid:** If the work needs to be post-commit, the flow is an after-save
flow. If the flow was before-save for performance reasons, note that the fast
path is for updating fields on the triggering record — it never covered anything
with an external effect.

---

## Gotcha 4: Publish Immediately Fires on Rollback

**What happens:** A team decouples via Platform Event specifically so downstream
never hears about a rolled-back record, and downstream hears about it anyway.

**When it occurs:** When the event definition is set to Publish Immediately
rather than Publish After Commit. The publish behaviour is a property of the
event definition, not of the publishing flow, so the flow author can do
everything right and still get the wrong semantics from a setting somebody else
made.

**How to avoid:** Read the event definition before trusting the pattern. The two
also differ in governor accounting: Publish After Commit counts as a DML
statement against the shared 150 limit; Publish Immediately draws on a separate
allocation of 150 publish-immediate calls.

---

## Gotcha 5: An Invocable Action Runs in the Calling Transaction

**What happens:** A flow calls invocable Apex expecting the work to be
asynchronous, and it rolls back with the flow.

**When it occurs:** Unless the invocable explicitly enqueues async work, it
executes inline in the caller's transaction and shares the caller's governor
budget and rollback. "It's Apex" is not "it's async."

**How to avoid:** Read the Apex. If the invocable is meant to be the async
boundary, its body should be enqueuing a Queueable and returning — and the flow
should not expect a result from it, because the result does not exist yet. An
invocable that both does the work and claims to be async is one or the other.

---

## Gotcha 6: A Finalizer Can Re-Enqueue Five Times, and Then Stops

**What happens:** A retry design assumes the finalizer will keep retrying until
success, and a persistent failure quietly stops being retried.

**When it occurs:** A Queueable job that failed with an unhandled exception can
be successively re-enqueued five times by a transaction finalizer. The count
resets on a successful execution. There is one finalizer per Queueable job, and
the finalizer may enqueue a single asynchronous job (Queueable, future, or Batch)
— it is not a fan-out point.

**How to avoid:** Design the give-up branch explicitly. Track the attempt count
in your own state (the job is re-enqueued, so a constructor argument survives),
stop before five, and write a record when you give up. A silent stop at the
platform ceiling is indistinguishable from success in most log designs.

---

## Gotcha 7: Re-Enqueue Replays the Whole Queueable Body

**What happens:** A Queueable that writes a record and then makes a callout is
re-enqueued after the callout throws. The record is written twice.

**When it occurs:** Every retry. The finalizer re-enqueues the *job*, not the
remaining work. Everything before the failure point runs again.

**How to avoid:** Make the body idempotent, or structure it so the
non-idempotent step is first and guarded by a check. This is the same idempotency
requirement the asynchronous path and Platform Events have; the finalizer just
makes it unavoidable rather than occasional.

---

## Gotcha 8: The Idempotency Key Cannot Be the Interview GUID

**What happens:** A well-intentioned idempotency guard keys off
`$Flow.InterviewGuid` and never dedupes anything.

**When it occurs:** Always. The GUID identifies the interview, and a retry is a
*new* interview with a new GUID — which is precisely the case being guarded
against. The same trap catches `$Flow.CurrentDateTime`.

**How to avoid:** Derive the key deterministically from the record and the state
that defines this attempt: the record Id plus the field values, or the record Id
plus `LastModifiedDate`. It must produce the same value on the retry that it
produced on the original.

---

## Gotcha 9: The Fault Path Runs Inside the Transaction, Not After It

**What happens:** A fault path is used as a compensating-action hook and produces
races with the platform's own rollback and with downstream automation.

**When it occurs:** Always. The fault connector's branch executes in the same
transaction as the element that faulted. In an after-save flow the interview's
DML has not committed, so a "compensating" update either duplicates the rollback
or writes state the rollback then discards — sometimes triggering automation on a
record that is about to cease to exist.

**How to avoid:** A fault path records and stops. To stop and roll back
deliberately, use the **Custom Error** element in a record-triggered flow or
**Roll Back Records** in a screen flow. Compensation for an already-committed
external effect belongs in a later transaction.

---

## Gotcha 10: Mixed DML Applies to the Asynchronous Path Too

**What happens:** Work is moved into an asynchronous path partly to escape a
Mixed DML error, and the error follows it.

**When it occurs:** The asynchronous path is a new transaction, so it is a
*different* transaction from the trigger — which does help if the setup-object DML
and the non-setup DML were split across the two. It does not help if the
asynchronous path itself touches both kinds. Mixed DML is a per-transaction
restriction, and the async path is still a transaction.

**How to avoid:** Split by kind, not by timing. Put the User/Group/permission-set
DML in one transaction and the standard-object DML in another. Moving both into
the same asynchronous path changes nothing.

---

## Gotcha 11: Asynchronous Paths Get Async Limits — Which Are Higher, Not Absent

**What happens:** A heavy operation is moved to an asynchronous path on the
assumption that limits no longer apply, and it fails on CPU.

**When it occurs:** Asynchronous and scheduled paths are subject to the
asynchronous per-transaction Apex limits. Those are more generous — 200 SOQL
queries, 60,000 ms CPU, 12 MB heap against 100 / 10,000 ms / 6 MB synchronous —
and they are still ceilings.

**How to avoid:** Treat the move as buying roughly a 6× CPU budget and a 2× query
budget, not an exemption. If the work needs more than that, it needs Batch Apex
or chunking, and `flow/flow-batch-processing-alternatives` owns that decision.

---

## Gotcha 12: "Post-Commit" Does Not Mean the Record Is Still What You Saw

**What happens:** An asynchronous path reads `$Record` and acts on values that
have since changed, or acts on a record that has since been deleted.

**When it occurs:** Any time between commit and the async path running. Other
users, other automation, and integrations are all writing in that window. The
`$Record` values the path carries are a snapshot from the triggering transaction,
not a live read.

**How to avoid:** Decide per requirement whether the snapshot or the current
state is correct. If the current state is what matters, Get Records fresh at the
start of the async path and handle the not-found case — a deleted record is a
real outcome, not an error. If the snapshot is what matters (an audit of what was
approved), say so in the flow's description so the next reader does not "fix" it.
