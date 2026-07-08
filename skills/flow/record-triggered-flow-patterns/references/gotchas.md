# Gotchas — Record Triggered Flow Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## The Wrong Save Context Creates Architecture Debt Fast

**What happens:** A same-record field update is implemented in after-save, and the org pays the cost forever through extra DML and re-entry risk.

**When it occurs:** Teams choose after-save by default instead of checking whether the requirement is only about the current record.

**How to avoid:** Start with before-save unless the design clearly needs committed side effects.

---

## Broad Entry Criteria Makes Debugging Look Random

**What happens:** The flow appears to run unpredictably because it fires on unrelated updates and collides with other automations.

**When it occurs:** Start conditions are set to run on every update without field-specific logic or prior-value checks.

**How to avoid:** Use explicit criteria and changed-field logic wherever the business event is narrower than "any save."

---

## Flow And Apex Still Share The Same Object Lifecycle

**What happens:** Admins design a record-triggered flow as if it owns the object, but an Apex trigger or validation rule changes the outcome.

**When it occurs:** Mixed-automation orgs with declarative and programmatic logic on the same object.

**How to avoid:** Review record-triggered flows alongside order-of-execution neighbors instead of in isolation.

---

## `$Record__Prior` Only Helps If The Logic Actually Uses It

**What happens:** A flow is configured to run on update, but it does not compare the old and new value of the important field.

**When it occurs:** Teams rely on broad start criteria and forget to encode the real business transition.

**How to avoid:** Use prior-value comparisons or equivalent start logic whenever the requirement depends on a field changing, not merely being present.

---

## Trigger Order Only Reorders Flows Inside One Phase

**What happens:** An admin sets a low trigger order value on an after-save flow expecting it to run ahead of the object's Apex trigger, and the flow still runs last. Nothing errors; the automation just does the wrong thing.

**When it occurs:** Mixed Flow-and-Apex orgs where the two disagree about who owns a field, and the admin reaches for the only ordering knob visible in Flow Builder.

**How to avoid:** Treat trigger order as flow-vs-flow-within-a-phase only. Salesforce documents that you can't prioritize an after-save flow to run before any before-save flow or before an Apex trigger. If the flow must win the field, move the write into before-save (step 3, ahead of the Apex before trigger at step 4) or move the logic into Apex.

---

## An Unset Trigger Order Is Not "Last"

**What happens:** A phase has three flows. Two are set to 1,200 and 1,400. A new flow ships with no trigger order value on the assumption that unordered means "runs at the end." It runs first.

**When it occurs:** Any object where flows were numbered above 1,000, which admins often do to "leave room at the bottom."

**How to avoid:** Remember the band structure — values 1–1,000 ascending, then unset flows in created-date order, then values 1,001–2,000 ascending. Assign an explicit value to every flow in the phase. Confirm in Flow Trigger Explorer, and remember that ties at the same value fall back to alphabetical API name, so renaming a flow can reorder execution.

---

## A Platform-Initiated Recursive Save Does Not Re-Run Your Flows

**What happens:** A designer reasons that "every save runs my flow," builds a marker-field guard around that assumption, and finds the flow silently absent from one pass of a multi-save transaction.

**When it occurs:** Saves that Salesforce re-runs internally — for example a workflow field update. The order-of-execution reference is explicit for that case: "Custom validation rules, flows, duplicate rules, processes built with Process Builder, and escalation rules aren't run again," while it "Executes before update triggers and after update triggers, regardless of the record operation (insert or update), one more time (and only one more time)." Separately, "during a recursive save, Salesforce skips steps 9 (assignment rules) through 17 (roll-up summary field in the grandparent record)" — and after-save record-triggered flows are step 14.

**How to avoid:** Build recursion guards around the DML your own automation issues, not around the platform's skip window. Apex triggers re-run on the platform's recursive pass; flows do not. A guard designed for one will not protect the other.
