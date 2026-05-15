# Gotchas — Apex Savepoint and Rollback

Non-obvious Salesforce platform behaviors that bite even
experienced Apex developers when using `Database.Savepoint` and
`Database.rollback`. Each gotcha here is distinct from the
high-level rules in `SKILL.md` — these surface in specific
combinations of DML, queries, and transaction lifecycle.

## Gotcha 1: Rollback does NOT undo Platform Event publishes

**What happens:** A method publishes a Platform Event with
`EventBus.publish(...)`, then a subsequent DML fails and the
catch block calls `Database.rollback(sp)`. The DML is reverted —
the Platform Event is **not**. Subscribers (LWC empApi, CometD
clients, Apex Triggers on the event) all receive the event as
if everything succeeded. Downstream systems take action on a
notification for work that no longer exists.

**When it occurs:** Any service-layer pattern that publishes a
"WorkCompleted__e" or similar event mid-transaction, then catches
a downstream error and rolls back. Especially common in
record-triggered automation where the Platform Event is used to
signal an integration partner and the rollback path was added
later as a "defensive" change.

**How to avoid:** Publish Platform Events from inside the `finally`
or AFTER the commit boundary — never between the savepoint and a
possible rollback. The reliable pattern: collect events into an
`EventBus.publish(events)` call placed AFTER the try/catch
closes successfully, OR use `EventBus.publish(events,
EventBus.TransactionFinalizerOptions...)` (when supported by
your API version) to defer publish until transaction commit.

---

## Gotcha 2: SOQL query counter is NOT reset by rollback (and limit-exhaustion can survive)

**What happens:** Inside a loop, code does
`SELECT ... FROM Account WHERE Id = :id` (one SOQL per iteration —
already wrong, but a common starting point), and on every failure
calls `Database.rollback(sp)`. The developer assumes the rollback
"resets the transaction." It does not — SOQL counts are not
governed by savepoint. After the 101st query the transaction
throws `LimitException: Too many SOQL queries: 101` regardless of
how many rollbacks have been performed.

**When it occurs:** Per-row processing loops with an inner "validate
then insert with rollback on validation failure" pattern. Also:
any retry loop that re-queries the database after a rollback to
re-validate the state.

**How to avoid:** Treat savepoint as a DML-only mechanism. If you
need to retry an operation, retry on the *collected* result set,
not from inside the savepoint scope. For bulk validation, query
the validation data once at the top of the method (outside the
loop) and reuse the cached map inside.

---

## Gotcha 3: Nested savepoints have surprising cleanup semantics

**What happens:** A service uses nested savepoints:

```apex
Savepoint outer = Database.setSavepoint();
try {
    insert parents;
    Savepoint inner = Database.setSavepoint();
    try {
        insert children;
    } catch (Exception e) {
        Database.rollback(inner);  // expectation: only children rolled back
    }
} catch (Exception e) {
    Database.rollback(outer);
}
```

When the *inner* try succeeds and the outer rollback fires later,
both inner and outer DML are reverted — fine. But if the inner
rollback fires *first*, the platform invalidates the `outer`
savepoint reference under certain combinations of DML and the
outer rollback throws `IllegalArgumentException: Save Point with
specified id does not exist`. The behavior depends on the order
of operations and is not consistently documented.

**When it occurs:** Service patterns that nest atomicity boundaries
to support partial-undo semantics. The bug manifests under load —
unit tests that exercise the happy path see neither failure mode.

**How to avoid:** Avoid nested savepoints unless you have a specific
reason. If you genuinely need per-step rollback granularity, design
the operation so each step is independently committable (split into
separate Queueable jobs), or use `Database.SaveResult` with
`allOrNone=false` for per-row error handling. The savepoint mechanism
was designed for **one atomicity boundary per transaction**, not
arbitrary nesting.

---

## Gotcha 4: Static variables and `Limits` counters that DID get touched stay touched

**What happens:** A trigger handler uses a static bypass flag:
`TriggerControl.disable(AccountTriggerHandler.class);`. Mid-transaction
a savepoint is set, DML happens, and a rollback fires. The expectation
is that the static state is reverted. It is not — `TriggerControl`'s
`Set<Type> disabled` retains the entries it had before rollback, plus
any added during the rolled-back section. The next DML in the same
transaction will skip the trigger handler entirely, which the
developer didn't intend.

**When it occurs:** Any retry-after-rollback flow that bypasses
triggers during the first attempt and expects "fresh" trigger
behavior on the second. Also: orchestration patterns where one
sub-service disables a trigger, fails, rolls back, and the parent
service then tries a different path that needed the trigger to fire.

**How to avoid:** Re-initialize any static state explicitly after
a rollback. The cleanest pattern: capture the relevant flags
before the savepoint and restore them in the catch block:

```apex
Set<Type> disabledBefore = TriggerControl.disabledSnapshot();
Savepoint sp = Database.setSavepoint();
try {
    TriggerControl.disable(AccountTriggerHandler.class);
    insert accs;
} catch (Exception e) {
    Database.rollback(sp);
    TriggerControl.restoreSnapshot(disabledBefore);
    throw e;
}
```

---

## Gotcha 5: `Database.rollback` after a successful `EmailMessage` insert does NOT recall the email

**What happens:** A workflow sends a transactional email via
`Messaging.sendEmail(...)`, then attempts to update a related
Account, the update fails, and the rollback fires. The Account
change is reverted; the email is already in flight (or delivered)
and cannot be unsent. The system's audit trail shows a "rolled back"
transaction; the customer still received the notification.

**When it occurs:** Order-confirmation flows, password-reset flows,
and any "side-effect-then-DML" pattern where the side effect is
a user-visible communication. The same pattern bites with
`Database.executeBatch` calls (the job is enqueued before rollback
and runs anyway), `System.enqueueJob` (Queueable runs anyway), and
any `@future` invocation queued before the rollback (it executes
after transaction commit *or* rollback — same path).

**How to avoid:** Defer all side-effecting calls — email, async job
enqueue, callouts — until AFTER the try block confirms success.
Build a "deferred actions" pattern: collect side effects into a
list, run DML, and only fire side effects on commit success. The
`templates/apex/ApplicationFinalizer` skeleton in this repo
implements this with `System.attachFinalizer(...)` (API 60+) for
exactly this reason.
