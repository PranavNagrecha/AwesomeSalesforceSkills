# Gotchas — Trigger And Flow Coexistence

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Before Trigger Silently Overwrites the Before-Save Flow

**What happens:** Before-save record-triggered Flows execute at step 3 of the order of execution; Apex before triggers execute at step 4. They are separate, consecutively numbered steps, so the order is documented and fixed -- the Flow runs first and the trigger runs second. If both write the same field, the **trigger's value is the one that persists**, on every transaction and in every org.

The gotcha is not unpredictability, it is invisibility: nothing surfaces the collision. No error is thrown, no debug log entry flags it, and the Flow appears in the log to have run successfully -- because it did. Its write was simply superseded one step later.

**Beware the stale version of this claim.** A great deal of older material (and AI-generated guidance trained on it) says both run at "step 3" with no guaranteed relative order, and that the result is indeterminate. That was written against a superseded numbering of the docs page. Acting on it leads teams to chase a phantom race condition -- adding retries, guards, or ordering hacks -- instead of fixing field ownership.

**When it occurs:** Any object where a before-save Flow and a before trigger both exist and write to at least one overlapping field.

**How to avoid:** Ensure that before-save Flows and before triggers on the same object write to completely disjoint field sets. Use the field ownership registry pattern to document and enforce this. If field overlap is unavoidable, make the **trigger** (the later writer, step 4) conditional -- e.g. assign only when the field is blank -- so it defers to the Flow instead of clobbering it. Adding the condition to the Flow accomplishes nothing, because the Flow has already finished by the time the trigger runs.

---

## Gotcha 2: Workflow Field Updates Re-Fire Triggers But Not Before-Save Flows

**What happens:** When a workflow rule performs a field update (step 11), the platform updates the record again, re-runs system validations, and executes before update and after update triggers "one more time (and only one more time)." Before-save Flows do not re-execute during this pass -- nor do custom validation rules, duplicate rules, or escalation rules. This means a before-save Flow will never see a value written by a workflow field update in the same transaction, but a before trigger will.

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

## Gotcha 5: In-Trigger Field Validation Can Be Undone Later in the Same Save

**What happens:** An Apex before trigger at step 4 that validates `Priority__c` with `addError()` only sees the record as it stands at step 4. Anything that writes the field later in the save -- most commonly a workflow field update at step 11, whose re-fire pass reaches before update triggers again but not the original insert-time validation path -- can change the value the trigger approved.

Note the direction carefully: a **before-save Flow cannot** undo a before trigger's validation, because the Flow runs at step 3, one step *earlier*. The classic phrasing of this gotcha ("a Flow can write after the trigger validated") is backwards and comes from the superseded numbering that put both at a shared step 3.

**When it occurs:** Orgs that rely on Apex before-trigger code for field validation instead of declarative validation rules, and that still have workflow field updates or other later-step automation writing the same fields.

**How to avoid:** Use declarative validation rules for field-level validation rather than trigger code. Custom validation rules execute at step 5, after both the before-save Flow (step 3) and the before trigger (step 4) have finished writing fields, so they see the final pre-save state regardless of which automation wrote it.
