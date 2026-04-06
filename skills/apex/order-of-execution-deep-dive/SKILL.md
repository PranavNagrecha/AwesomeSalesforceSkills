---
name: order-of-execution-deep-dive
description: "Complete reference for the Salesforce record save order of execution: all 18 steps from DB load through commit, covering trigger placement, validation rule sequencing, Flow execution timing, workflow field update re-fire behavior, and recursion patterns. Use when debugging unexpected automation behavior, designing multi-layer automation, or analyzing trigger vs Flow execution order. NOT for trigger framework design (use trigger-framework). NOT for record-triggered Flow patterns (use record-triggered-flow-patterns)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "why is my before trigger running after validation rules"
  - "flow running before or after trigger in save order"
  - "workflow field update causing infinite trigger loop"
  - "before-save flow vs before trigger which runs first"
  - "order of execution for apex triggers and flows"
tags:
  - order-of-execution
  - triggers
  - automation
  - flow
  - recursion
inputs:
  - "Object and DML operation type (insert, update, delete, undelete)"
  - "List of automations active on the object: triggers, flows, workflow rules, validation rules, process builder"
  - "Description of unexpected behavior or symptom being debugged"
outputs:
  - "Annotated 18-step order of execution mapped to the specific org configuration"
  - "Root cause identification for ordering-related bugs"
  - "Recursion guard implementation or refactoring guidance"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Order of Execution Deep Dive

This skill provides an authoritative, step-by-step walkthrough of the Salesforce record save order of execution for a single DML statement. It is the primary reference when debugging why an automation ran at the wrong time, why a field value was overwritten unexpectedly, or why triggers are firing more times than expected.

---

## Before Starting

Gather this context before working on anything in this domain:

- What object and DML operation (insert / update / delete / undelete) is in play?
- Which automations are active on the object: before triggers, after triggers, before-save Flows, after-save Flows, workflow rules with field updates, validation rules, duplicate rules, roll-up summary fields on parent objects?
- Is the symptom a wrong value, a wrong execution count, a governor limit error, or a missed side effect?
- Are there multiple automation types on the same object? If so, implicit ordering assumptions are the most common root cause.

---

## Core Concepts

### The 18-Step Canonical Order

The following steps apply to a single DML statement on a single record (bulk operations apply these steps per batch of up to 200 records):

1. **Load from database** — Salesforce loads the existing record from the database. For inserts, the record is initialized with default values.
2. **Overwrite with new field values** — The incoming field values from the DML operation overwrite the loaded record. The record is now in memory but not yet saved.
3. **Execute all before triggers** — All Apex before triggers on the object run. Before-save record-triggered Flows also run at this step, interleaved with before triggers in undefined relative order. Both can read and write the in-memory record before it is committed.
4. **System validation** — Salesforce enforces required fields, maximum field lengths, foreign key constraints, and layout rules. This happens after before triggers, meaning a before trigger can supply a required field value and pass validation.
5. **Custom validation rules** — All active validation rules on the object run. They execute after before triggers, so a before trigger that sets a field value can satisfy a validation rule.
6. **Duplicate rules** — Active duplicate rules run. Duplicate alerts or blocking occurs here.
7. **Save record to database (no commit)** — The record is written to the database but the transaction is not yet committed. Rollback is still possible.
8. **Execute all after triggers** — All Apex after triggers run. At this point the record has an Id (for inserts) and the values are persisted to the database within the transaction. After triggers typically handle related record operations.
9. **Assignment rules** — Lead and Case assignment rules execute.
10. **Auto-response rules** — Auto-response rules for Cases and Leads execute.
11. **Workflow rules** — Active workflow rules evaluate and fire. Immediate field updates, tasks, emails, and outbound messages are processed here.
12. **Workflow field update re-fire** — If any workflow rule fires a field update, Salesforce reruns all before and after triggers ONCE more (one additional pass, not infinitely). This re-fire also reruns validation rules, duplicate rules, and the save step. It does not re-fire workflow rules a second time.
13. **Process Builder (legacy processes)** — Process Builder processes execute. These are legacy and equivalent in timing to after-save automation.
14. **Escalation rules** — Case escalation rules run.
15. **Record-triggered after-save Flows** — After-save record-triggered Flows run here, after workflow rules and Process Builder have completed. This is the correct place to understand why a Flow side effect appears after workflow side effects.
16. **Entitlement rules** — Entitlement rules run.
17. **Roll-up summary fields** — If the record is a child in a master-detail relationship and the save affects a roll-up summary on the parent, the parent record is updated. This can cause parent-object triggers to re-fire through their own complete order of execution.
18. **Commit to database and post-commit logic** — The transaction commits. Post-commit operations run: `@future` method calls, outbound email sends (unless rolled back), and platform events.

### Before-Save Flows Run at Step 3, Not Step 15

The most frequently misunderstood timing: a before-save record-triggered Flow runs at step 3, the same step as Apex before triggers. It does not run at step 15. Before-save Flows are more efficient than after-save Flows for field updates because they modify the in-memory record without an additional DML operation. After-save Flows run at step 15, after workflow rules and processes have already fired.

### Workflow Field Update Re-Fire Is Bounded

When a workflow rule fires a field update, steps 3 through 8 (before triggers, validation, save, after triggers) run one additional time. This re-fire is bounded: it happens at most once due to workflow field updates. Triggers that themselves perform DML on the same object within a transaction can still cause recursive behavior, but workflow field updates alone do not cause infinite loops.

### Recursion Guard Pattern

If an after trigger performs a DML update on the same object it fires on, or on a parent that cascades back, it can cause the trigger to fire again within the same transaction. The standard guard uses a static Boolean or static `Set<Id>` to track processed records:

```apex
public class AccountTriggerHandler {
    private static Set<Id> processedIds = new Set<Id>();

    public static void handleAfterUpdate(List<Account> newList) {
        List<Account> toProcess = new List<Account>();
        for (Account a : newList) {
            if (!processedIds.contains(a.Id)) {
                processedIds.add(a.Id);
                toProcess.add(a);
            }
        }
        if (toProcess.isEmpty()) return;
        // ... actual logic
    }
}
```

The static variable persists for the entire transaction, so any re-entry of the trigger will find the Id already in the set and skip processing.

---

## Common Patterns

### Pattern: Diagnosing a Field Value Overwrite

**When to use:** A field has the wrong value after a DML operation and you cannot tell whether a trigger, a Flow, or a workflow rule was the last writer.

**How it works:**
1. List all automations active on the object in step order.
2. Identify which step each automation occupies.
3. The last writer in the step sequence wins for before-commit field writes.
4. For after-save Flows (step 15): these must use DML to write back to the record, which starts a new mini-transaction and can re-fire triggers.
5. Add debug logging or a System.debug statement in each automation at the suspect write point.

**Why not the alternative:** Guessing which automation ran last without a step map routinely leads to incorrect fixes that break other automations.

### Pattern: Protecting a Before Trigger from Flow Interference

**When to use:** A before-save Flow and a before Apex trigger both write the same field, and the final value is wrong.

**How it works:**
- Both run at step 3 but with no guaranteed relative order between them.
- Move field-write responsibility to one tool only, or use a condition in the Flow or trigger to check whether the other has already set the value.
- Prefer before-save Flow for simple field derivation; use Apex trigger for logic that requires collections or complex computation.

**Why not the alternative:** Relying on undocumented execution order between a Flow and a trigger at step 3 is fragile and will break silently across releases.

### Pattern: Recursion Guard for Trigger-Triggered Updates

**When to use:** An after trigger updates a related record or the same object, and the trigger fires more times than expected.

**How it works:**
- Add a private static `Set<Id>` guard to the handler class (see Core Concepts).
- On entry, filter the incoming list to exclude already-processed Ids.
- Add all incoming Ids to the set before performing any DML.

**Why not the alternative:** A static Boolean is simpler but coarser: it blocks ALL re-entry, including legitimate second calls on different records in the same transaction.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to set a field value before save, no related record work | Before-save record-triggered Flow (step 3) | No extra DML; runs before validation |
| Need to set a field value based on complex Apex logic | Before Apex trigger (step 3) | Full Apex capability, same timing as before-save Flow |
| Need to create a related record after save | After Apex trigger (step 8) | Record Id is available; can create child records in same transaction |
| Need to send an email or call an external API | After-save Flow (step 15) or @future (step 18) | Avoid DML in before trigger; keep callouts post-commit |
| Debugging "trigger fires twice" | Check for workflow field update (step 12) or recursive DML in after trigger | Both are common causes of double-fire |
| Validation must pass before automation runs | Put automation in before trigger (step 3) to supply field value that satisfies validation (step 5) | Correct sequencing |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Map all active automations on the object** — List every before trigger, after trigger, before-save Flow, after-save Flow, workflow rule, validation rule, and Process Builder process active on the object and DML event type.
2. **Assign each automation to its step number** — Using the 18-step sequence, annotate each automation with its execution step. Note any automations that can cause re-fire (workflow field updates at step 12, roll-up summary updates at step 17).
3. **Identify the symptom's location in the sequence** — Map the observed wrong behavior (wrong field value, unexpected re-fire, missing side effect) to the step where it likely occurred.
4. **Check for recursion risks** — If any after trigger performs DML on the triggering object or on a parent with a roll-up summary, verify a recursion guard is in place.
5. **Validate workflow field update re-fire scope** — If workflow rules with field updates exist, confirm that the before and after triggers handle being called twice gracefully (idempotent logic or guard).
6. **Implement the fix** — Apply the minimum change needed: add a recursion guard, move logic to the correct step, or remove a duplicate write.
7. **Test with full automation stack enabled** — Run tests with all automations active, not just the trigger under test. Isolating triggers in tests hides step-interaction bugs.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All active automations on the object are listed and assigned to their correct step number
- [ ] Any workflow rules with field updates are identified, and triggers handle the one-time re-fire correctly
- [ ] Recursion guards are in place for any after trigger that performs DML on the triggering object or its master-detail parent
- [ ] Before-save Flows and before triggers that write the same field have been reconciled (single owner for each field)
- [ ] After-save Flows (step 15) are not used where a before-save Flow (step 3) would be more efficient
- [ ] Tests exercise the full automation stack (not triggers in isolation) for the objects in scope
- [ ] Roll-up summary parent trigger re-fire behavior has been considered for master-detail relationships

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Before-save Flow runs at step 3, not step 15** — Most practitioners expect all Flows to run late in the order, but before-save record-triggered Flows run at the same step as before Apex triggers. A before-save Flow that sets a field will have its value visible to the before trigger and will satisfy validation rules.
2. **Workflow field update re-fire is exactly once, not infinite — but it still surprises** — The platform reruns before and after triggers when a workflow field update fires. Triggers that are not written to be idempotent (e.g., they unconditionally create child records) will create duplicates on this second pass.
3. **Roll-up summary update at step 17 starts a new transaction on the parent** — When a child record save causes a roll-up summary update, the parent record's own full order of execution runs. Any trigger on the parent object fires as a side effect of a child record DML. This is a common source of governor limit surprises in large data volumes.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Annotated 18-step map | A copy of the 18-step sequence annotated with which specific automations in the org occupy each step |
| Recursion guard implementation | Apex static Set<Id> guard added to the handler class |
| Root cause summary | One-paragraph explanation of which step caused the observed symptom and why |

---

## Related Skills

- trigger-framework — Use when the problem is trigger architecture (single trigger per object, handler class pattern) rather than execution ordering.
- record-triggered-flow-patterns — Use when the problem is designing or debugging record-triggered Flow logic specifically, not the full order of execution.

---

## Official Sources Used

- Apex Developer Guide — Triggers and Order of Execution — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
