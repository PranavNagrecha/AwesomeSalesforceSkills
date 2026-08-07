# Gotchas — Save Order Interactions

## 1. Validation Runs After Before-Save Flow

Custom validation rules run at step 5; the before-save Flow ran at
step 3. A before-save Flow can write values that then fail validation.
Not a bug — but confusing.

## 2. Duplicate Rules Run After Before-Save

Duplicate rules run at step 6, so flow-populated dedup keys are seen by
the duplicate rule. Good for enforcing; dangerous if the flow sets a
value that unintentionally matches.

## 3. The Before Trigger Overwrites the Before-Save Flow, Not the Reverse

Before-save Flows are step 3; Apex before triggers are step 4. If both
write the same field, the trigger's value saves — deterministically, on
every transaction. Anything claiming the two share a step or race is
quoting a superseded numbering. Fix a collision by giving the field one
owner, and if both must write, put the condition in the **trigger** —
the Flow has already finished by then.

## 4. Before-Save Flow Cannot Do DML

You cannot insert/update related records from a before-save Flow. That
is an after-save Flow's job.

## 5. After-Save Flow Causes Re-Entry

After-save Flow update (step 14) → fires triggers and other flows
again. Apex caps this: "Total stack depth for any Apex invocation that
recursively fires triggers due to insert, update, or delete statements"
is **16** (Apex Developer Guide, Per-Transaction Apex Limits). That is a
crash barrier, not a design budget — practically you want a re-entry
count of 1.

## 6. Platform-Event and Schedule Flows Are Not In The Save Order

They run in their own transactions. Don't reason about them in the
above sequence.

## 7. Workflow Field Updates Re-Enter Before Triggers, But Not Flows

A legacy workflow field update at step 11 re-runs system validations
and before update / after update triggers one more time, and only one
more time. Record-triggered Flows, custom validation rules, duplicate
rules, and escalation rules do NOT re-run. So a before trigger can see
the workflow-updated value; a before-save Flow never will.

## 8. Assignment Rules Only Fire On Lead/Case

Other objects skip step 9 — don't assume "assignment rules fire".

## 9. Async Apex & Platform Events Run Post-Commit

`@future`, Queueable, and platform-event-publish-via-DML run at step 20,
after the commit at step 19. Anything that depends on them cannot be
consumed in the same transaction.

## 10. Fast Field Updates Do Not Refire Same-Record Automation

A before-save Flow writing back into the same record does not retrigger
the same save. An after-save Flow doing a DML update does — this is the
usual recursion trap.
