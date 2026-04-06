---
name: trigger-and-flow-coexistence
description: "Governance patterns for orgs where Apex triggers and record-triggered Flows both run on the same object. Covers field-write conflict prevention, single-entry-point consolidation, recursion guards across automation types, and automation inventory documentation. Use when inheriting a mixed-automation org, adding a Flow to an object that already has triggers, or resolving silent field-overwrite bugs. NOT for order-of-execution mechanics (use order-of-execution-deep-dive). NOT for trigger handler framework design (use trigger-framework). NOT for Flow-only design patterns (use record-triggered-flow-patterns)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how to manage triggers and flows on the same object without conflicts"
  - "trigger and flow both updating the same field and overwriting each other"
  - "before-save flow and before trigger running in unpredictable order"
  - "adding a new record-triggered flow to an object that already has apex triggers"
  - "automation inventory for objects with mixed trigger and flow automation"
  - "recursion between after-save flow and after trigger causing infinite loop"
tags:
  - trigger-and-flow-coexistence
  - automation-governance
  - field-conflict
  - recursion
  - order-of-execution
inputs:
  - "Object name and list of all active automations (triggers, flows, workflow rules, process builder)"
  - "Description of the field-write conflict or recursion symptom"
  - "Whether the org has a single-trigger-per-object pattern or multiple triggers"
outputs:
  - "Automation inventory matrix documenting every automation on the object, its type, timing, and field writes"
  - "Conflict analysis identifying field-write collisions and execution-order risks"
  - "Refactoring plan to eliminate or guard against coexistence problems"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Trigger And Flow Coexistence

This skill activates when an org has both Apex triggers and record-triggered Flows on the same object and needs to prevent silent conflicts, field-overwrite bugs, or recursion loops. It provides governance patterns for inventorying mixed automation, detecting field-write collisions, and establishing guard clauses that work across automation types.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which object has both triggers and Flows? List every active automation by name, type (before trigger, after trigger, before-save Flow, after-save Flow), and the fields each one reads or writes.
- Is there a single-trigger-per-object handler pattern already in place, or are there multiple trigger files on the same object?
- What is the symptom: a field being silently overwritten, an unexpected recursion loop, a governor limit error, or an automation that appears to not fire at all?

---

## Core Concepts

### Before-Save Timing Ambiguity

Before-save Flows and before Apex triggers both execute at step 3 of the order of execution (after initial record load and before system validation). Salesforce does not guarantee a fixed relative order between a before-save Flow and a before trigger on the same object. If both write to the same field, the result is indeterminate -- whichever runs second silently wins. This is the single most common source of coexistence bugs.

### After-Save Flow Placement

After-save Flows run at step 15 in the order of execution, after workflow rules, workflow field updates, and any re-invocation of before/after triggers caused by those field updates. This means an after-save Flow sees field values that may have been modified by a workflow field update that re-fired triggers. Conversely, DML performed inside an after-save Flow will re-enter the order of execution and fire triggers again, creating a recursion path that is invisible to trigger-only recursion guards.

### Single Entry-Point Principle

The Salesforce Well-Architected framework recommends a single automation entry point per object per timing slot. In practice this means either triggers or Flows own a given timing slot on a given object, not both. Coexistence is a tolerated legacy state, not a recommended architecture. The goal of this skill is to make coexistence safe while planning consolidation.

### Field Ownership Model

Each writeable field on an object should have at most one automation that sets its value during a given timing slot. When multiple automations write the same field at the same timing, you have a field-write collision. The field ownership model is a simple matrix: rows are fields, columns are automations, cells indicate read (R) or write (W). Any column with two or more W entries at the same timing is a conflict.

---

## Common Patterns

### Pattern 1: Field Ownership Registry

**When to use:** Any object with two or more automations that write fields during the same timing slot.

**How it works:**

1. Create a spreadsheet or metadata document listing every field on the object that is written by any automation.
2. For each field, record which automation writes it and at which timing (before-save, after-save).
3. Flag any field with more than one writer at the same timing as a conflict.
4. Resolve conflicts by moving one writer to a different timing, consolidating both writes into a single automation, or using a guard clause to ensure only one writer executes.

**Why not the alternative:** Without an explicit registry, developers add automations that silently overwrite each other. The bug only surfaces intermittently because the relative execution order is not guaranteed.

### Pattern 2: Cross-Automation Recursion Guard

**When to use:** An after trigger performs DML that re-enters the save and fires Flows, or an after-save Flow performs DML that fires triggers, causing a recursion loop.

**How it works:**

```apex
public class AutomationControl {
    // Static flag visible to triggers; Flow can read via Invocable
    public static Boolean flowOriginatedSave = false;
    public static Boolean triggerOriginatedSave = false;

    @InvocableMethod(label='Check If Trigger Originated Save')
    public static List<Boolean> isTriggerOriginated(List<String> unused) {
        return new List<Boolean>{ triggerOriginatedSave };
    }
}
```

In the trigger handler, set `AutomationControl.triggerOriginatedSave = true` before performing DML. In the Flow, use a Decision element to call the Invocable method and skip logic when the flag is true. This prevents the Flow from re-processing records that the trigger already handled.

**Why not the alternative:** Static variables in Apex are invisible to Flows by default. Without an Invocable bridge, the Flow has no way to know it was triggered by an Apex DML and will always execute, causing infinite recursion.

### Pattern 3: Consolidation Into Single Trigger Handler

**When to use:** Long-term refactoring of a mixed-automation object toward a single entry point.

**How it works:**

1. Inventory all before-save Flows on the object and document their logic.
2. Rewrite each Flow's logic as a method in the trigger handler class.
3. Deactivate the before-save Flows one at a time, testing after each deactivation.
4. Repeat for after-save Flows if the team prefers trigger-only automation.
5. Document the migration in the automation inventory so future developers do not recreate Flows on the object.

**Why not the alternative:** Consolidation into Flows is equally valid. The key is choosing one entry point per timing slot, not necessarily choosing triggers over Flows. The decision depends on the team's skill set and change management process.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Before trigger and before-save Flow both write the same field | Move one to a different timing or consolidate into a single automation | No guaranteed relative order at step 3; last writer wins silently |
| After trigger DML re-fires Flows that re-fire triggers | Implement cross-automation recursion guard with InvocableMethod bridge | Static variables alone do not cross the Apex-to-Flow boundary |
| New Flow being added to an object with existing triggers | Build automation inventory first; confirm no field-write collisions | Prevents introducing a silent overwrite bug in production |
| Org has process builder, workflow rules, triggers, and Flows on the same object | Prioritize consolidation; use Flow Trigger Explorer to sequence Flows | Four automation types on one object is unmaintainable at scale |
| Team is split between Flow-first and code-first developers | Establish a per-object ownership agreement and document it in the automation inventory | Mixed patterns are acceptable if governed; ungoverned mixing causes outages |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Build the automation inventory.** For the target object, list every trigger (before/after, insert/update/delete), every record-triggered Flow (before-save, after-save), every workflow rule with field updates, and every active Process Builder. Record the fields each automation reads and writes.
2. **Identify field-write collisions.** Using the inventory, flag any field that is written by more than one automation at the same timing slot. These are active or latent coexistence bugs.
3. **Check for cross-automation recursion paths.** Trace DML operations in after triggers and after-save Flows. If a trigger performs DML that re-enters the save, check whether Flows on the target object will fire and vice versa.
4. **Implement guards or resolve conflicts.** For field-write collisions, choose one owner per field per timing. For recursion paths, implement the cross-automation recursion guard pattern with an InvocableMethod bridge. For legacy automations (workflow rules, Process Builder), plan migration to either triggers or Flows.
5. **Document the ownership model.** Update the automation inventory with the resolved ownership. Store this document in the repo or wiki so future changes go through the same review.
6. **Test with the Flow Trigger Explorer.** In a sandbox, use Setup > Flow Trigger Explorer to visualize the execution sequence. Verify that field values match expectations after save.
7. **Validate in a full sandbox with data volume.** Run bulk DML (200+ records) to confirm that recursion guards hold under bulk and that governor limits are not hit by the combined automation stack.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Automation inventory exists and lists every trigger, Flow, workflow rule, and Process Builder on the object
- [ ] No field is written by more than one automation at the same timing slot (or conflicts are explicitly guarded)
- [ ] Cross-automation recursion paths are identified and guarded with InvocableMethod bridge or field-value checks
- [ ] Flow Trigger Explorer confirms expected execution sequence in sandbox
- [ ] Bulk DML test (200+ records) passes without governor limit errors
- [ ] Automation inventory document is committed or stored in a shared location
- [ ] Legacy automations (workflow rules, Process Builder) have a migration plan documented

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Before-save Flow and before trigger order is indeterminate** -- Salesforce documentation states both run at step 3 but does not specify which executes first. This means a before-save Flow and a before trigger that both set `Status__c` will produce unpredictable results. The field value after step 3 depends on internal platform scheduling, not deployment order.
2. **Workflow field updates re-fire before and after triggers but not before-save Flows** -- When a workflow rule performs a field update at step 9, the system re-evaluates before and after triggers (steps 3-4 again). However, before-save Flows do not re-run during this re-evaluation. This asymmetry means a trigger can see a value set by a workflow field update, but a before-save Flow cannot.
3. **After-save Flow DML is invisible to trigger recursion guards** -- A typical trigger recursion guard uses a static Boolean like `hasRun`. This prevents the trigger from running twice in the same transaction. However, DML performed by an after-save Flow enters a fresh save cycle that resets the trigger context. The static variable is still true, so the trigger skips -- but the Flow may not skip, causing a one-sided infinite loop.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Automation Inventory Matrix | Object-level document listing every automation, its type, timing, fields read, fields written, and ownership |
| Conflict Analysis Report | Identification of field-write collisions and recursion paths with severity ratings |
| Refactoring Plan | Step-by-step plan to consolidate or guard coexisting automations |

---

## Related Skills

- order-of-execution-deep-dive -- Use when you need the full 18-step order of execution reference rather than coexistence governance
- trigger-framework -- Use when designing or refactoring the trigger handler pattern itself
- record-triggered-flow-patterns -- Use when designing Flows in isolation without trigger coexistence concerns
- recursive-trigger-prevention -- Use when the recursion problem is trigger-to-trigger only, without Flow involvement
