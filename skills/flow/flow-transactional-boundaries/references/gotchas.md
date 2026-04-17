# Flow Transactional Boundaries — Gotchas

## 1. Before-Save Looks Free Until You Need A Callout Or Platform Event

Before-Save flows are the cheapest path for same-record field enrichment, but the element set is restricted. You cannot call external services, publish Platform Events with `Publish After Commit` semantics the way after-save does, send email, or create/update related records. Teams discover the restriction late and retrofit an After-Save flow that duplicates logic.

Avoid it:
- Before starting a Before-Save design, confirm all planned work fits the restricted element set.
- If callouts or Platform Events are needed, route those portions to an After-Save path or Scheduled Path from the start.

## 2. "Run Asynchronously" Path Re-Evaluates Criteria At Async Time

The Run Asynchronously path on a record-triggered flow is gated by the flow's entry criteria BOTH at save time and at async dispatch time. If another automation modifies the triggering record between save and async dispatch, the async path may silently skip. This surprises teams who assume the path is guaranteed.

Avoid it:
- Treat the async path as "best-effort" and pair it with a recoverable fallback (scheduled batch sweep, retry event).
- Avoid entry criteria that reference fields likely to be mutated by other automation in the same window.

## 3. Mixed DML Can Hide Behind A Single Flow

Setup objects (User, Group, PermissionSetAssignment, Queue) cannot be written in the same transaction as normal sObjects. A Flow that updates a User record AND a Case in one After-Save branch will throw `MIXED_DML_OPERATION` at bulk or single-record time. The symptom reads as a Flow error, not a transaction-boundary error.

Avoid it:
- Split setup-object DML into a separate async path (Scheduled Path, invocable Apex with `@future` or Queueable).
- In Apex callers, use `System.runAs(new Version())` test patterns; in Flow, the only clean split is async.

## 4. Scheduled Path Offset 0 Is Not Immediate

A Scheduled Path with "0 Hours" offset is queued to an internal scheduler and typically runs within a few minutes, but there is no SLA. Teams sometimes use it as a "commit-then-do" and assume the async work finishes before the user's next page load. It does not.

Avoid it:
- Never use Scheduled Path offset 0 for work the user expects to be "done" when the page returns.
- If the UX requires fast post-commit work, use a Platform Event Published After Commit with a PE-triggered flow, which the platform dispatches more promptly (though still asynchronously).

## 5. Pause Elements Persist Variables But Not Sharing Context

When a Screen Flow resumes after a Pause, the interview variables are rehydrated, but the running user context may change. Resumption by the scheduler runs as the "Automated Process" user unless the Pause resumes by user action. The sharing / record visibility after resumption may be narrower or wider than before.

Avoid it:
- Audit any DML or Get Records performed after Pause for sharing implications.
- Prefer Orchestration for approval-style processes, which defines the running user per step explicitly.

## 6. Flow Called From `@future` Cannot Do Callouts And DML Mixing

An `@future(callout=true)` Apex method that then calls a Flow which does DML will still be subject to the async transaction's mixed-DML and callout ordering rules. The Flow does not get a reset; it inherits the `@future` transaction's constraints.

Avoid it:
- If the Flow must do callouts and DML, structure the Flow to do all callouts first, then all DML.
- Prefer Queueable + `System.enqueueJob` chaining to separate callouts from DML across transactions.

## 7. Orchestration Work Items Do Not Retry Automatically

When an Orchestration Background Step fails, the Work Item is marked Failed and sits waiting for a human to retry from the Orchestration Work Guide. The platform does not back off and retry on its own.

Avoid it:
- Add a fault step on every Background Step that writes a ticket to an operations queue / error-log object.
- For self-healing, emit a Platform Event on fault that a retry-coordinator flow subscribes to.

## 8. Flow Interview Storage Accumulates From Long Pauses

Every paused Screen Flow interview takes up storage and shows in the Paused and Waiting Interviews list. A process that averages 100 interviews paused at any time for days is fine; one that reaches thousands will bump into org-wide limits and make the admin monitoring view unusable.

Avoid it:
- Set a reasonable max wait and fail the interview if the wait exceeds it.
- Switch to Orchestration for long-running processes with more than a few dozen concurrent instances.

## 9. Calling A Flow From Another Flow Does Not Start A New Transaction

Subflows do NOT create a new transaction boundary. A subflow called from a record-triggered flow runs in the same transaction as the parent, with the same shared budget. Teams sometimes assume subflows isolate limit consumption.

Avoid it:
- For isolation, use Platform Events or Scheduled Paths, not subflows.
- Budget the parent + subflow together against the transaction limit.

## 10. `Publish After Commit` Semantics Are Not The Same As Async

A Platform Event published with `Publish After Commit` delivers AFTER the current DML commits, but the SUBSCRIBER runs in its own async transaction. The publisher still publishes in the current transaction's context and the publish DML counts against the publish limit (6,000/hour org-wide). This is NOT the same as "move work to async" — it's "defer delivery until commit".

Avoid it:
- Read the publisher's and subscriber's transaction contexts separately when debugging.
- See `flow/flow-platform-events-integration` for detail.
