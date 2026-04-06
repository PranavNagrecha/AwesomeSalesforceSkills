# Gotchas — Trigger And Flow Coexistence

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Before-Save Flow and Before Trigger Have No Guaranteed Relative Order

**What happens:** Both before-save Flows and before Apex triggers execute at step 3 of the order of execution. Salesforce does not document or guarantee which one runs first. If both write the same field, the result is indeterminate. The "winner" can change between transactions, sandbox refreshes, or platform releases without any notification.

**When it occurs:** Any object where a before-save Flow and a before trigger both exist and write to at least one overlapping field. The bug is silent -- no error is thrown, no debug log entry flags the conflict.

**How to avoid:** Ensure that before-save Flows and before triggers on the same object write to completely disjoint field sets. Use the field ownership registry pattern to document and enforce this. If field overlap is unavoidable, consolidate the logic into a single automation type.

---

## Gotcha 2: Workflow Field Updates Re-Fire Triggers But Not Before-Save Flows

**What happens:** When a workflow rule performs a field update (step 9), the platform re-evaluates before and after triggers (returning to steps 3-4). However, before-save Flows do not re-execute during this re-evaluation pass. This means a before-save Flow will never see a value written by a workflow field update in the same transaction, but a before trigger will.

**When it occurs:** Orgs that still have active workflow rules with field updates alongside both triggers and before-save Flows. The asymmetry is especially confusing when migrating from workflow rules to Flows, because the trigger behavior changes (it no longer re-fires if the workflow rule is replaced by a Flow that does not perform a field update the same way).

**How to avoid:** Migrate workflow rules with field updates to before-save Flows or trigger logic before analyzing trigger-Flow coexistence. The asymmetric re-fire behavior makes it nearly impossible to reason about field values when all three automation types are active.

---

## Gotcha 3: Static Variable Guards Do Not Cross the Apex-to-Flow Boundary

**What happens:** A common trigger recursion guard uses a static Boolean like `TriggerHandler.hasAlreadyRun`. This prevents the trigger from firing twice. However, when an after-save Flow performs DML that re-enters the save cycle on the same or a different object, the Flow's execution is not aware of the static variable. The trigger's guard prevents the trigger from running again, but the Flow has no such guard and will execute every time.

**When it occurs:** After-save Flows that perform create or update DML. The DML enters a new save cycle, and while the trigger skips (because the static flag is already true), the Flow runs again because Flows do not have access to static Apex variables by default.

**How to avoid:** Use an InvocableMethod that exposes the static flag to the Flow. Add a Decision element at the start of the Flow that calls the Invocable and skips processing if the flag is true. Alternatively, use a field-value guard: set a hidden checkbox field in the trigger, and have the Flow's entry criteria exclude records where that checkbox is true.

---

## Gotcha 4: Flow Trigger Explorer Only Shows Flow Order, Not Trigger Interleaving

**What happens:** The Flow Trigger Explorer (Setup > Flow Trigger Explorer) shows the execution order of multiple record-triggered Flows on the same object. It does not show where Apex triggers execute relative to those Flows. Practitioners who rely on the Explorer to understand the full automation sequence will miss trigger interactions entirely.

**When it occurs:** Any debugging or design session where the practitioner uses Flow Trigger Explorer as the sole tool for understanding automation order. The Explorer is useful for Flow-to-Flow sequencing but incomplete for trigger-Flow coexistence analysis.

**How to avoid:** Supplement Flow Trigger Explorer with debug logs that include the `FLOW_START_INTERVIEWS` and `CODE_UNIT_STARTED` events. Cross-reference the two to build a complete picture of trigger and Flow interleaving during a save.

---

## Gotcha 5: Before-Save Flow Field Assignments Bypass Apex Trigger.new Validation

**What happens:** A before-save Flow can write to fields on the record without going through the trigger's `Trigger.new` validation logic, because the Flow may execute after the before trigger at step 3. If the before trigger validates that `Priority__c` is not null and a before-save Flow subsequently sets `Priority__c` to null, no error is thrown because validation rules run at step 4 (after both before triggers and before-save Flows have completed) and the trigger's in-code validation already passed.

**When it occurs:** Orgs that rely on Apex before-trigger code for field validation instead of declarative validation rules. A before-save Flow can undo the trigger's work without being caught.

**How to avoid:** Use declarative validation rules for field-level validation rather than trigger code. Validation rules execute at step 4, after both before triggers and before-save Flows have finished writing fields. This ensures validation sees the final field state regardless of which automation wrote last.
