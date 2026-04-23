# Gotchas — Save Order Interactions

## 1. Validation Runs After Before-Save Flow

A before-save Flow can write values that then fail validation. Not a
bug — but confusing.

## 2. Duplicate Rules Run After Before-Save

Flow-populated dedup keys are seen by the duplicate rule. Good for
enforcing; dangerous if the flow sets a value that unintentionally
matches.

## 3. Before-Save Flow Cannot Do DML

You cannot insert/update related records from a before-save Flow. That
is an after-save Flow's job.

## 4. After-Save Flow Causes Re-Entry

After-save Flow update → fires triggers and other flows again. Max
recursion depth is 16 (per the engine) but practically you want 1.

## 5. Platform-Event and Schedule Flows Are Not In The Save Order

They run in their own transactions. Don't reason about them in the
above sequence.

## 6. Workflow Field Updates Re-Enter Before Triggers

Legacy workflows that do a field update re-enter before triggers with
the updated value. A flow replacing a workflow may change the visible
before-trigger state.

## 7. Assignment Rules Only Fire On Lead/Case

Other objects don't have step 8 — don't assume "assignment rules fire".

## 8. Async Apex & Platform Events Run Post-Commit

`@future`, Queueable, and platform-event-publish-via-DML run only after
step 15 (commit). Anything that depends on them cannot be consumed in
the same transaction.

## 9. Fast Field Updates Do Not Refire Same-Record Automation

A before-save Flow writing back into the same record does not retrigger
the same save. An after-save Flow doing a DML update does — this is the
usual recursion trap.
