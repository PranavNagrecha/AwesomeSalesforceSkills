# Examples — Save Order Interactions

## Example 1: Before-Save Flow Beats Before Trigger

**Situation:** want to populate `Territory__c` from Zip code.

**Good:** before-save Flow with a Decision and Assignment. Runs at
step 3, no DML, no SOQL.

**Bad:** after-save Flow that does a second DML to set the field, plus
a `@future` trigger.

Save-order trace for the two designs:

```text
GOOD — before-save Flow
  step  3  Set_Territory (before-save Flow)   Territory__c = 'WEST'
  step  5  validation rules see 'WEST'
  step  7  save
  step 19  commit
  → one save, no DML element, no re-entry

BAD — after-save Flow + @future
  step  7  save                                Territory__c = null
  step  8  AccountTrigger (after)              enqueues @future
  step 14  Set_Territory (after-save Flow)     Update Records → NEW SAVE CYCLE
             ↳ step 3..8 run again for the same record
  step 19  commit
  step 20  @future runs in a separate transaction, may re-save again
  → two+ save cycles, extra DML, recursion risk
```

Note the trigger interaction the good design still has to account for:
if an Apex before trigger on Account also writes `Territory__c`, it runs
at **step 4** — one step after the Flow — and its value is the one that
saves.

## Example 2: Validation Runs After Before-Save Flow

A before-save Flow sets `Stage = 'Closed Won'` but an active validation
rule blocks `Closed Won` without `Close Date`. Custom validation rules
run at step 5, **after** the before-save Flow at step 3 (and after the
before trigger at step 4), so the rule fires using the flow-populated
value. Either set Close Date in the same flow or relax the rule.

## Example 3: Recursion Through After-Save → After Trigger

After-save Flow updates `Last_Touch__c`, firing an after trigger that
updates another field, triggering the record-triggered Flow again.

**Fix:** guard on `Trigger.oldMap` vs `Trigger.newMap`; detect no-op
and skip DML. Or move `Last_Touch__c` to before-save so no DML fires.

## Example 4: Roll-Up Not Visible In Before-Save

Before-save Flow reads `Amount_Total__c` (a roll-up) — always stale in
the same transaction. The Flow runs at step 3; the parent's roll-up is
not recalculated until step 16, eleven steps later in the child's save.
(Step 16 is still before the commit at step 19 — the value is stale
because the recalculation is *later in the save*, not because it happens
after commit.)

**Fix:** move any logic that needs roll-up to the after-save Flow on the
**parent** object, triggered by the child's DML.
