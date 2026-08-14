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

## 11. A Roll-Up-Driven Parent Save Never Reaches The After-Save Flow

The parent save launched at step 16 is a recursive save, and the docs
state: "During a recursive save, Salesforce skips steps 9 (assignment
rules) through 17 (roll-up summary field in the grandparent record)."
After-save Flows are step 14 — inside that skipped range. So a parent
after-save Flow you expect a child roll-up to fire simply never
executes, and neither do assignment, auto-response, workflow,
escalation or entitlement rules on the parent. What *does* still run on
that parent save: before-save Flows (3), before triggers (4),
validation rules (5), duplicate rules (6), the save (7), after
triggers (8) — so a parent before or after trigger does fire, and does
see the recalculated roll-up. That is the in-transaction hook. A
**child** after-save Flow is not a substitute for reading the value: it
runs at step 14 of the child's save, before the parent recalculation at
step 16, so it has to compute the number itself.

## 12. After Triggers Cannot See The Assignment-Rule Owner

Assignment rules are step 9; all after triggers are step 8. An
after-insert trigger on Case or Lead that reads `OwnerId` sees the owner
from the request or the object default — never the one the assignment
rule is about to pick. Emailing "the assigned owner" from that trigger
mails the wrong person. After-save Flows are step 14, so ordering alone
does not rule them out — but the docs do not say whether the flow's
record snapshot is refreshed with the assignment-rule owner, so verify
in a debug log before depending on it.
