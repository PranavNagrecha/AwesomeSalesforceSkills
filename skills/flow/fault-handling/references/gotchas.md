# Flow Fault Handling — Gotchas

## 1. Missing Fault Connectors Roll Back More Than You Expect

In record-triggered automation, one unhandled exception can fail the entire save batch. The user often reports "the import failed" rather than "one record failed."

Avoid it:
- Add fault connectors to every DML, Action, and Subflow element.
- Decide whether the right failure response is rollback, log-and-stop, or user message.

## 2. `$Flow.FaultMessage` Is Diagnostic Text, Not Finished UX

The platform message can include raw validation or Apex text. That is useful for support, but poor for business users.

Avoid it:
- Capture `$Flow.FaultMessage` into a log or admin notification.
- Show users a controlled explanation and next step.

## 3. Shared Transactions Still Share Governor Limits

A Flow invoked by Apex or operating alongside other automation still consumes the same transaction budget. A "Flow error" may really be a combined Apex-plus-Flow design issue.

Avoid it:
- Review the entire transaction path.
- Move expensive work to safer boundaries when possible.

## 4. Subflows Do Not Magically Isolate Bad Error Design

If the called subflow fails and the parent flow does not handle it intentionally, you still get poor failure behavior.

Avoid it:
- Handle the failure where the subflow is called.
- Treat subflow boundaries as design boundaries, not safety boundaries.
