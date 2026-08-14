---
name: order-of-execution-deep-dive
description: "Complete reference for the Salesforce record save order of execution: all 20 steps from DB load through commit, covering trigger placement, validation rule sequencing, Flow execution timing, workflow field update re-fire behavior, and recursion patterns. Use when debugging unexpected automation behavior, designing multi-layer automation, or analyzing trigger vs Flow execution order. NOT for trigger framework design — use apex/trigger-framework. NOT for record-triggered Flow design — use flow/record-triggered-flow-patterns."
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
  - "what is the Salesforce order of execution for triggers and flows"
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
  - "Annotated 20-step order of execution mapped to the specific org configuration"
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

### The 20-Step Canonical Order

The following steps apply to a single DML statement on a single record (bulk operations apply these steps per batch of up to 200 records). Numbering matches the current Apex Developer Guide, *Triggers and Order of Execution*:

1. **Load from database** — Loads the original record from the database, or initializes the record for an upsert statement.
2. **Overwrite with new field values** — Loads the new record field values from the request and overwrites the old values. Salesforce performs system validation checks that depend on the request type (for API requests, this pass is narrower than for UI requests).
3. **Before-save record-triggered Flows** — Executes record-triggered Flows configured to run before the record is saved ("Fast Field Updates"). They modify the in-memory record with no additional DML.
4. **Execute all before triggers** — All Apex before triggers on the object run. They run **after** step 3, so they see any value a before-save Flow just wrote and can overwrite it.
5. **System validation + custom validation rules** — Runs most system validation steps again (required fields have non-null values, field lengths, foreign keys) and runs all active custom validation rules. This is after both step 3 and step 4, so either can supply a value that satisfies a validation rule.
6. **Duplicate rules** — Active duplicate rules run. If a rule identifies the record as a duplicate and uses the block action, the record isn't saved and no further steps (after triggers, workflow rules) are taken.
7. **Save record to database (no commit)** — The record is written to the database but the transaction is not yet committed. Rollback is still possible.
8. **Execute all after triggers** — All Apex after triggers run. At this point the record has an Id (for inserts) and the values are persisted within the transaction. After triggers typically handle related record operations.
9. **Assignment rules** — Lead and Case assignment rules execute.
10. **Auto-response rules** — Auto-response rules for Cases and Leads execute.
11. **Workflow rules** — Active workflow rules evaluate and fire. If a workflow rule performs a **field update**, the platform updates the record again, runs system validations again, and executes before update and after update triggers **one more time — and only one more time**. Custom validation rules, duplicate rules, escalation rules, and record-triggered Flows are not re-run by this pass.
12. **Escalation rules** — Case escalation rules run.
13. **Legacy Flow automations, not in a guaranteed order** — Process Builder processes and Flows launched by workflow rules execute here. Salesforce explicitly does not guarantee their relative order; use record-triggered Flows (step 14) when you need control.
14. **After-save record-triggered Flows** — Executes record-triggered Flows configured to run after the record is saved. This is why a record-triggered Flow side effect appears after workflow and Process Builder side effects.
15. **Entitlement rules** — Entitlement rules run.
16. **Roll-up summary field on the parent** — If the record is a detail in a master-detail (or an eligible lookup roll-up) relationship, the parent's roll-up summary is recalculated and the parent record goes through its own save procedure — including parent triggers.
17. **Roll-up summary field on the grandparent** — If the parent was updated, the same recalculation cascades to the grandparent, which also goes through its own save procedure.
18. **Criteria-based sharing evaluation** — Criteria-based sharing rules are evaluated.
19. **Commit** — All DML operations are committed to the database.
20. **Post-commit logic** — Sending email, enqueued asynchronous Apex jobs (`@future`, Queueable, Batch), and asynchronous paths in record-triggered Flows run here.

### Before-Save Flows (Step 3) Run Immediately Before Before Triggers (Step 4)

The most frequently misunderstood timing, and the one most often stated incorrectly in AI-generated guidance: before-save record-triggered Flows and Apex before triggers are **two separate, consecutively numbered steps**, not one shared step. The Flow runs first (step 3), the before trigger runs second (step 4). The relative order is **determinate and documented** — it is not a race, and it does not vary by transaction, sandbox, or deployment order.

The practical consequence: if a before-save Flow and a before trigger both write the same field, **the before trigger wins**, every time, because it runs later. Fix such a conflict by assigning single ownership of the field, not by hoping for a particular ordering.

Before-save Flows do not run at step 14 — that is where **after-save** record-triggered Flows run, after workflow rules (11) and Process Builder (13) have already fired.

### Workflow Field Update Re-Fire Is Bounded

When a workflow rule fires a field update at step 11, before update and after update triggers run one additional pass, along with system validations. The Apex Developer Guide is explicit that this happens "one more time (and only one more time)." Custom validation rules, duplicate rules, escalation rules, and record-triggered Flows are not re-run. Triggers that themselves perform DML on the same object within a transaction can still cause recursive behavior, but workflow field updates alone do not cause infinite loops.

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
3. The last writer in the step sequence wins for before-commit field writes. Because step numbers are ordered and documented, "last writer" is determinable from the step map — it is not a guess.
4. For after-save Flows (step 14): these must use DML to write back to the record, which starts a new save cycle and can re-fire triggers.
5. Add debug logging or a System.debug statement in each automation at the suspect write point.

**Why not the alternative:** Guessing which automation ran last without a step map routinely leads to incorrect fixes that break other automations.

### Pattern: Reconciling a Before-Save Flow and a Before Trigger That Write the Same Field

**When to use:** A before-save Flow and a before Apex trigger both write the same field, and the final value is wrong.

**How it works:**
- The Flow runs at step 3, the trigger at step 4. The trigger runs second, so **the trigger's value is the one that survives** — deterministically, on every transaction. If the observed symptom is "the Flow's value disappeared," this is the explanation; nothing is racing.
- Move field-write responsibility to one tool only. That is the fix; do not attempt to reorder the two.
- If both must remain, make the later writer (the trigger) conditional — e.g. only assign when the field is blank — so it acts as a fallback rather than an unconditional overwrite.
- Prefer before-save Flow for simple field derivation; use Apex trigger for logic that requires collections or complex computation.

**Why not the alternative:** Trying to "sequence" the Flow ahead of or behind the trigger is not a supported control. Only the ordering of multiple record-triggered Flows on the same object is configurable, via the Flow `triggerOrder` field (Metadata API 54.0+ / Flow Trigger Explorer). Apex trigger placement relative to Flows is fixed by the platform.

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
| Need to set a field value before save, no related record work | Before-save record-triggered Flow (step 3) | No extra DML; runs before validation (step 5) |
| Need to set a field value based on complex Apex logic | Before Apex trigger (step 4) | Full Apex capability; runs immediately after before-save Flows |
| Before-save Flow and before trigger both write the field | Give the field one owner | Step 4 runs after step 3, so the trigger always wins — this is determinate, not a race |
| Need to create a related record after save | After Apex trigger (step 8) | Record Id is available; can create child records in same transaction |
| Need to send an email or call an external API | After-save Flow (step 14) or @future (step 20) | Avoid DML in before trigger; keep callouts post-commit |
| Debugging "trigger fires twice" | Check for a workflow field update (step 11) or recursive DML in an after trigger | Both are common causes of double-fire |
| Validation must pass before automation runs | Put automation in a before trigger (step 4) to supply a field value that satisfies validation (step 5) | Correct sequencing |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Map all active automations on the object** — List every before trigger, after trigger, before-save Flow, after-save Flow, workflow rule, validation rule, and Process Builder process active on the object and DML event type.
2. **Assign each automation to its step number** — Using the 20-step sequence, annotate each automation with its execution step. Note any automations that can cause re-fire (workflow field updates at step 11, roll-up summary updates at steps 16-17).
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
- [ ] After-save Flows (step 14) are not used where a before-save Flow (step 3) would be more efficient
- [ ] Tests exercise the full automation stack (not triggers in isolation) for the objects in scope
- [ ] Roll-up summary parent trigger re-fire behavior has been considered for master-detail relationships

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Before-save Flow runs at step 3, one step *before* the before trigger at step 4 — not at step 14** — Most practitioners expect all Flows to run late in the order. Before-save record-triggered Flows are the first automation in the save. Their values are visible to before triggers, which run next and can overwrite them, and to validation rules at step 5.
2. **Workflow field update re-fire is exactly once, not infinite — but it still surprises** — The platform reruns before update and after update triggers when a workflow field update fires at step 11, "one more time (and only one more time)." Triggers that are not written to be idempotent (e.g., they unconditionally create child records) will create duplicates on this second pass. Record-triggered Flows do not re-run on this pass.
3. **Roll-up summary update at step 16 puts the parent through its own save procedure** — When a child record save causes a roll-up summary update, the parent record's own full order of execution runs, and step 17 cascades the same behavior to the grandparent. Any trigger on the parent object fires as a side effect of a child record DML. This is a common source of governor limit surprises in large data volumes.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Annotated 20-step map | A copy of the 20-step sequence annotated with which specific automations in the org occupy each step |
| Recursion guard implementation | Apex static Set<Id> guard added to the handler class |
| Root cause summary | One-paragraph explanation of which step caused the observed symptom and why |

---

## Related Skills

- trigger-framework — Use when the problem is trigger architecture (single trigger per object, handler class pattern) rather than execution ordering.
- record-triggered-flow-patterns — Use when the problem is designing or debugging record-triggered Flow logic specifically, not the full order of execution.

---

## Official Sources Used

- Apex Developer Guide — Triggers and Order of Execution (20-step list; before-save Flows step 3, before triggers step 4) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Metadata API Developer Guide — Flow (`triggerOrder`, API 54.0+) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
