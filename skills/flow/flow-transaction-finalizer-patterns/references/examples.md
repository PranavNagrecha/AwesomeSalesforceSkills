# Examples — Flow Transaction Finalizer Patterns

Worked examples for work that must happen *after* the triggering transaction
commits — and for the narrower case where it must also report whether it
succeeded.

The three mechanisms, in increasing order of what they guarantee:

| Mechanism | Runs | Survives publisher rollback | Callouts allowed | Reports its own outcome |
|---|---|---|---|---|
| After-save flow, inline | Same transaction, before commit | No | No | No |
| **Run Asynchronously** path | New transaction, after the original transaction commits | Yes | Yes | No |
| Platform Event (Publish After Commit) → subscriber | New transaction, after commit | Yes | Yes, in the subscriber | No |
| Queueable + `System.Finalizer` | Async, after commit | Yes | Yes | **Yes** |

Only the last row gives you a callback that runs whether the work succeeded or
threw. Flow has no equivalent. That single fact is what decides when this skill
sends you into Apex.

---

## Example 1: Wrong vs Right — A Callout After a Record Save

**Wrong:**

```text
Record-Triggered Flow "Notify Fulfilment" (after save, Order)
  └── Action: HTTP Callout to fulfilment API
```

The callout sits in the triggering transaction, after DML. The platform does not
allow a callout once DML has occurred in the same transaction, and even where the
sequencing appears to work, a later failure rolls the Order back while the
external system has already been told the order exists. The result is the failure
mode this whole skill exists to prevent: **the outside world believes something
that the database does not.**

**Right:**

```text
Record-Triggered Flow "Notify Fulfilment" (after save, Order)
  ├── Immediate path:  (nothing, or a same-transaction field stamp)
  └── Run Asynchronously path:
        ├── Action: HTTP Callout to fulfilment API
        │     fault -> Create Records: Integration_Log__c (severity ERROR)
        └── Update Records: Order.Fulfilment_Notified_At__c = {!$Flow.CurrentDateTime}
```

Setup path: open the record-triggered flow → **Start** element → **Include a Run
Asynchronously path to access an external system after the original transaction
for the triggering record is successfully committed**.

**Why it works:** The asynchronous path runs after the original transaction for
the triggering record is successfully committed, in its own transaction. That is
what makes the callout legal and what guarantees the external system is never
told about an Order that rolled back. It is available only on after-save
record-triggered flows.

**What it does not give you:** a time. You cannot schedule an asynchronous path
the way you schedule a scheduled path — it runs when it runs. And it is subject to
the asynchronous per-transaction Apex limits, so the higher ceilings apply (200
SOQL, 60,000 ms CPU, 12 MB heap) but ceilings still apply.

**Where to watch it:** asynchronous paths queue on the Time-Based Workflow page
in Setup, alongside scheduled paths.

---

## Example 2: The Zero-Minute Scheduled Path That Is Not the Right Answer

**Context:** A team wants an email sent only after a Contact insert commits, and
reaches for a scheduled path set to zero minutes after record creation.

**Problem:** It usually works, which is why it spreads. But the construct it is
imitating already exists and says what it means. A zero-offset scheduled path
communicates "at a scheduled time, which happens to be now" to every future
reader, and it inherits the scheduled-path machinery — a queue entry, a time
computation off a date field — for a case that has no time in it.

**Solution:** Use the **Run Asynchronously** path for "after the transaction
commits, as soon as practical." Reserve scheduled paths for cases where the
offset is real and business-meaningful: three days before a renewal date, one
hour after a Case is escalated, at 09:00 the following Monday.

**Why it matters beyond style:** the two constructs are configured differently
and fail differently. A scheduled path computes its run time from a date/time
field, so a null or past-dated field produces surprising behaviour; an
asynchronous path has nothing to compute. When a reader is debugging "why didn't
this run," the first question is which of the two it is, and a zero-minute
scheduled path answers that question misleadingly.

---

## Example 3: The Queueable Finalizer, and Exactly What It Buys

**Context:** An approval completes. An audit row must be written recording the
outcome, and it must exist whether the downstream posting succeeded or threw.

**Problem:** Every Flow-native mechanism gives you *post-commit execution*. None
gives you *post-outcome execution* — a callback that runs on the failure path
too. A fault connector fires when the element it guards throws; it does not fire
when the interview is killed by an uncatchable limit exception, and it has no way
to report "the async job I started ten minutes ago has now finished, and here is
how."

**Solution:** Flow calls an Invocable Action that enqueues a Queueable; the
Queueable attaches a finalizer.

```apex
public with sharing class PostApprovalPoster implements Queueable, Database.AllowsCallouts {
    private final Id approvalId;

    public PostApprovalPoster(Id approvalId) {
        this.approvalId = approvalId;
    }

    public void execute(QueueableContext ctx) {
        System.attachFinalizer(new PostApprovalFinalizer(approvalId));
        // ... the work that may throw ...
    }
}

public class PostApprovalFinalizer implements Finalizer {
    private final Id approvalId;

    public PostApprovalFinalizer(Id approvalId) {
        this.approvalId = approvalId;
    }

    public void execute(FinalizerContext ctx) {
        Audit__c row = new Audit__c(
            Approval__c   = approvalId,
            Job_Id__c     = ctx.getAsyncApexJobId(),
            Request_Id__c = ctx.getRequestId(),
            Outcome__c    = String.valueOf(ctx.getResult())
        );
        if (ctx.getResult() == ParentJobResult.UNHANDLED_EXCEPTION) {
            row.Error__c = ctx.getException().getMessage();
        }
        insert row;
    }
}
```

**Why it works:** `FinalizerContext.getResult()` returns `ParentJobResult.SUCCESS`
or `ParentJobResult.UNHANDLED_EXCEPTION`, and `getException()` carries the
exception in the failure case. `getAsyncApexJobId()` and `getRequestId()` give you
identifiers that correlate to the async job record and to Event Monitoring logs.
The audit row is written on both paths, which is the property Flow cannot supply
at any price.

**The limits that shape the retry design:**

- **One finalizer per Queueable job.** You cannot layer them.
- **A Queueable that failed with an unhandled exception can be re-enqueued five
  times by a finalizer,** and that count resets on a successful execution. Five is
  a hard ceiling, not a suggestion — design a give-up branch.
- **The finalizer may enqueue a single asynchronous job** (Queueable, future, or
  Batch). It is not a place to fan out.
- **Callouts are allowed** in a finalizer.

**Repo gap:** `templates/apex/` has no canonical `QueueableWithFinalizer` shape
today. The snippet above is illustrative and belongs here rather than in a
template; if a second skill starts needing it, promote it to `templates/apex/`
per the templates rule rather than copying it again.

---

## Example 4: Choosing Between the Three, Concretely

**Context:** Four requirements arrive in the same sprint.

| Requirement | Mechanism | Why |
|---|---|---|
| "Email the customer when their Case closes" | **Run Asynchronously** path | Must not fire on rollback; nobody needs a confirmation that the email attempt happened; no callout sequencing to manage |
| "Tell the warehouse system an Order shipped" | **Run Asynchronously** path with a fault-path log row | Callout must be post-commit; the log row is the reconciliation artifact |
| "Notify billing, analytics, and the partner portal on Close Won" | **Platform Event (Publish After Commit)** | Three independent consumers with independent failure domains; adding a fourth should not touch the publisher |
| "Record that the ledger posting completed, with its outcome, and retry twice on failure" | **Queueable + Finalizer** | The only one of the four that needs to know *whether* it worked and to act on the answer |

**Why the split lands there:** the first three need post-commit execution, which
all three Flow-native mechanisms give. Only the fourth needs post-*outcome*
execution and bounded retry, which is the boundary at which the work leaves Flow.
Note that "notify three systems" chose Platform Events over three asynchronous
paths not for durability but for coupling: three paths in one flow means the
publisher's author owns all three failure modes.

`standards/decision-trees/async-selection.md` formalizes this and is the thing to
cite in a design review, rather than re-deriving the table.

---

## Example 5: Idempotency Is a Requirement, Not a Nicety

**Context:** The asynchronous path posts to a payment provider. It ran twice for
one Order and the customer was charged twice.

**Problem:** Every post-commit mechanism here can run a second time. An
asynchronous path can be re-queued; an event is delivered at least once; a
finalizer explicitly re-enqueues on failure, which means the *body* of the
Queueable runs again — including any part of it that already succeeded before the
exception.

**Solution:** Make the effect idempotent at the boundary, not the invocation.

```text
Run Asynchronously path
  ├── Get Records: Payment_Attempt__c where Order__c = {!$Record.Id}
  │                                    and Idempotency_Key__c = {!varKey}
  ├── Decision: already attempted?
  │     ├── Yes -> End
  │     └── No  ->
  │           ├── Create Records: Payment_Attempt__c (key, status = 'Pending')
  │           ├── Action: callout, passing varKey as the provider's
  │           │           idempotency header
  │           │     fault -> Update Payment_Attempt__c status = 'Failed', log
  │           └── Update Records: Payment_Attempt__c status = 'Succeeded'
  └── End
```

**Why it works:** two independent guards. The local `Payment_Attempt__c` record
stops a second interview from starting the work, and the idempotency key sent to
the provider stops a duplicate charge in the window where the local record exists
but the callout has already left. Either guard alone has a race; both together
close it.

**The key has to be deterministic.** `{!$Flow.InterviewGuid}` is *not* a valid
idempotency key — it differs per interview, which is precisely the case you are
guarding against. Derive it from the record: Order Id plus the field values that
define this attempt.

---

## Anti-Pattern: Sending the Email From a Before-Save Flow

**What practitioners do:** Put a Send Email action in a before-save
record-triggered flow, because before-save is the fast path and the email
"belongs with" the record creation.

**What goes wrong:** Before-save flows cannot perform DML at all, so this often
fails at authoring time. Where an equivalent is reachable — an action with an
external effect anywhere before commit — the email goes out and a later
validation rule, trigger, or roll-up failure rolls the record back. The customer
has a welcome email for an account that does not exist.

**Correct approach:** external effects belong after commit. Use the **Run
Asynchronously** path. If the requirement genuinely is "the user must not be able
to save without the email going out," that is a validation requirement, not a
notification one — block the save with a Custom Error element and let the email
follow the successful save.

---

## Anti-Pattern: The Fault Path as a Post-Commit Handler

**What practitioners do:** Treat a fault connector as the compensating-action
hook — "if the callout fails, the fault path will undo the record changes."

**What goes wrong:** The fault path runs inside the same transaction as the
element that faulted. If DML earlier in that transaction has already been
performed, the fault path's "compensating" update is racing with the platform's
own rollback and with any downstream automation the earlier DML triggered. In an
after-save flow the interview's changes have not committed yet, so the
compensation is either redundant (the rollback would have handled it) or actively
harmful (it writes state the rollback then discards, or it triggers automation on
a record about to disappear).

**Correct approach:** a fault path's job is to *record* and to *stop*, not to
compensate. Log the failure with enough context to act on. To stop and roll back
in a record-triggered flow, use the **Custom Error** element; in a screen flow,
**Roll Back Records**. Genuine compensating action for an already-committed
external effect belongs in a separate transaction — an asynchronous path, an
event subscriber, or a finalizer — where it can see the committed state and act
on it deliberately.

---

## Anti-Pattern: Retrying by Rescheduling

**What practitioners do:** "If the callout fails, we'll set a flag and the
nightly scheduled flow will pick it up tomorrow."

**What goes wrong:** it is a retry with a 24-hour period, no attempt counter, and
no give-up condition. A systematic failure — a revoked credential, a changed
endpoint — retries forever, consuming the org's daily scheduled-flow interview
allocation on work that cannot succeed. Nobody notices, because each individual
run looks like a normal run.

**Correct approach:** if retry semantics matter, use the mechanism that has them.
A finalizer can re-enqueue a failed Queueable up to five times and knows how many
attempts have happened; a flag-and-reschedule loop knows nothing. If the work
genuinely must stay in Flow, then at minimum store an attempt counter on the
record, stop at a threshold, and alert when the threshold is reached — which is
re-implementing a worse finalizer, and is the argument for not staying in Flow.
