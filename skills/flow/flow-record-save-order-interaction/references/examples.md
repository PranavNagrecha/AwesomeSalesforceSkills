# Examples — Save Order Interactions

## Example 1: Before-Save Flow Beats Before Trigger

**Situation:** want to populate `Territory__c` from Zip code.

**Good:** before-save Flow with a Decision and Assignment. Runs in
step 2, no DML, no SOQL.

**Bad:** after-save Flow that does a second DML to set the field, plus
a `@future` trigger.

## Example 2: Validation Runs After Before-Save Flow

A before-save Flow sets `Stage = 'Closed Won'` but an active validation
rule blocks `Closed Won` without `Close Date`. Validation runs **after**
the before-save Flow, so the rule fires using the flow-populated value.
Either set Close Date in the same flow or relax the rule.

## Example 3: Recursion Through After-Save → After Trigger

After-save Flow updates `Last_Touch__c`, firing an after trigger that
updates another field, triggering the record-triggered Flow again.

**Fix:** guard on `Trigger.oldMap` vs `Trigger.newMap`; detect no-op
and skip DML. Or move `Last_Touch__c` to before-save so no DML fires.

## Example 4: Roll-Up Not Visible In Before-Save

Before-save Flow reads `Amount_Total__c` (a roll-up) — always stale in
the same transaction. Roll-ups recalc at step 14 (after commit in the
parent's save chain).

**Fix:** move any logic that needs roll-up to the after-save Flow on the
**parent** object, triggered by the child's DML.
