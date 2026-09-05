---
name: process-automation-selection
description: "Use when deciding which Salesforce automation tool should own a requirement, including before-save and after-save Flow, screen Flow, scheduled Flow, invocable Apex, Apex triggers, and migration off Workflow Rules or Process Builder. Triggers: 'Flow or Apex trigger', 'which automation tool should I use', 'Process Builder migration', 'Workflow Rule retirement', 'same-record update or trigger', 'automation decision record', 'why did we reject Apex', 'one object one order', 'automation inventory for this object', 'scheduled Flow or Batch Apex'. NOT for 'which tool should stamp this field on save, and will it recurse' — use admin/workflow-field-update-patterns. NOT for actually running the conversion of an existing Process Builder — use flow/process-builder-to-flow-migration."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
triggers:
  - "should this be a flow or an apex trigger"
  - "how do I choose between before save flow and apex"
  - "process builder or workflow rule migration decision"
  - "which salesforce automation tool fits this requirement"
  - "same business rule exists in multiple automation layers"
  - "write an automation decision record for this requirement"
  - "should the nightly job be a scheduled flow or batch apex"
  - "flow and apex trigger on the same object share the same governor limits"
  - "inventory every automation on this object before adding another"
  - "justify why we rejected apex for this automation"
  - "flow vs apex which should I use for this requirement"
tags:
  - automation-selection
  - flow-vs-apex
  - process-builder-migration
  - workflow-rule-retirement
  - trigger-decision
  - decision-record
inputs:
  - "triggering event, user interaction model, and record volume"
  - "whether the work is same-record, related-record, async, or integration-heavy"
  - "existing automation already attached to the object or process"
outputs:
  - "automation tool recommendation"
  - "deployable decision record citing the decision-tree steps that resolved the choice"
  - "migration or consolidation findings"
  - "boundary decision for Flow, Apex, or legacy retirement"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Process Automation Selection

Use this skill when the hard question is not how to build the automation, but which automation surface should own it. Salesforce gives teams several ways to automate work, and most production problems start with the wrong boundary choice: using Apex when a before-save Flow was enough, forcing a Flow to behave like a service layer, or leaving legacy Workflow Rules and Process Builder logic in place because it still appears to work.

**This skill does not hold the routing logic — the decision trees do.** `standards/decision-trees/automation-selection.md` picks the technology, `standards/decision-trees/flow-pattern-selector.md` picks which kind of Flow once that tree has said Flow, and `standards/decision-trees/async-selection.md` picks the async mechanism once it has said Apex. What this skill adds is the worked application for an admin: how to run those trees against one real requirement, write the answer down as a decision record that survives the person who made it, and hand the record to whoever builds it. Cite tree question numbers (`automation-selection.md Q3`), never paraphrase the branch.

Treat legacy tools as migration targets, not fresh design options. Workflow Rules and Process Builder reached end of support on 31 December 2025; existing rules and processes still execute and can still be activated, deactivated and edited, but they receive no fixes and no enhancements, so build nothing new in them (`standards/decision-trees/automation-selection.md`, Strategic defaults). UNVERIFIED (2026-09-04): the end-of-support date does not appear in the extracted Summer '26 Metadata API, Apex Developer or Object Reference guides — the tree sources it to Salesforce Help article 001096524, which cannot be fetched from this environment. Do not restate a date beyond that citation.

---

## Before Starting

Gather this context before working on anything in this domain:

- What actually triggers the process: record save, user click, time schedule, event, or external call?
- Does the automation only update the triggering record, or does it coordinate related records, integrations, or user interaction?
- What record volume or transaction pressure exists in real life, not just in demo data?
- Is legacy Workflow Rule, Process Builder, or overlapping trigger logic already attached to the same business process?

---

## Questions to Ask Before Configuring

Ask these before opening Flow Builder or a `.trigger` file. Each one maps to a tree question and to a gotcha in `references/gotchas.md`; an agent that skips them produces a defensible-sounding recommendation with no record of what it rejected.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What actually fires this — a record save, a click, a clock, an inbound call, or an event?" | This is `automation-selection.md` Q1, and every other branch depends on it | The tree entry point, and whether the requirement is even record-triggered |
| "Does the work write anything other than fields on the triggering record?" | Decides before-save vs after-save (`flow-pattern-selector.md` Q3); a before-save flow has no Create/Update/Delete Records element to reach for | The Flow type, or the escalation to Apex |
| "What already runs on this object — flows, triggers, workflow rules, duplicate rules?" | Order of execution runs them in a fixed sequence and a workflow field update re-fires update triggers one more time (gotcha 5) | The automation inventory table, produced before anything new is added |
| "What is the real peak volume in one transaction and in 24 hours, at import time, not in the sandbox?" | The whole transaction shares one budget (100 SOQL, 150 DML statements, 10,000 ms CPU), so Flow's cost is not separable from Apex's (gotcha 8) | The `automation-selection.md` Q3 / Q10 answer, with a number behind it |
| "Does any step need a rollback, a retry, or a deployment gate with assertions?" | These are the named graduation conditions to Apex in `automation-selection.md` Q3 | An explicit yes/no, so "Apex is cleaner" never becomes the reason |
| "Who owns this rule in eighteen months, and when is it next reviewed?" | An unowned decision record is a rumour; the owner and review date are what make it re-openable | The `owner` and `review_date` fields on the record |
| "If we say Flow, what would have to become true for that to be the wrong answer?" | Forces the rejected alternatives to carry reasons rather than a shrug | The `rejected` block the checker script lints |

What a proper configuration adds over just picking a tool: the choice is traceable to a numbered tree step, the alternatives carry recorded reasons instead of taste, the object's existing automation was inventoried before anything new was attached, and the record names an owner and a date at which the choice gets re-examined.

---

## Core Concepts

### Choose By Execution Model, Not Team Habit

Before-save Flow, after-save Flow, scheduled Flow, screen Flow, and Apex trigger all solve different execution problems. Pick the one whose runtime behavior matches the requirement rather than the one the team is most comfortable editing.

### Flow First Does Not Mean Flow For Everything

Flow is the preferred default for declarative, maintainable automation, especially when the logic is readable and the platform already provides the needed behavior. Apex becomes the right choice when strict transaction control, heavier reuse, complex looping, or fine-grained performance control matter more than declarative ownership.

### Same-Record Versus Related-Record Work Is A Major Split

Simple updates to the triggering record belong in before-save record-triggered Flow whenever possible. Related-record DML, richer orchestration, or custom service boundaries usually move the decision to after-save Flow, invocable Apex, or triggers.

### The Decision Is Positional, Not Just Technological

The save procedure runs before-save record-triggered flows at step 3, all before triggers at step 4, all after triggers at step 8 and after-save record-triggered flows at step 14 (Apex Developer Guide, *Triggers and Order of Execution*). Choosing a tool therefore chooses a position in that sequence, which is what makes a rule split across Flow and Apex hard to reason about later.

### Legacy Automation Must Be Retired Deliberately

Workflow Rules and Process Builder should be treated as migration inventory. Even if they are still present in metadata, they should not remain the design center for new work.

### The Output Is A Record, Not An Opinion

The deliverable of this skill is a decision record: requirement, trigger, volume, cross-object answer, timing, chosen mechanism, the tree steps cited, the rejected alternatives with their reasons, an owner and a review date. `references/decision-record-examples.md` holds the shape, three worked records, the skeleton each choice hands off to, and the inventory queries.

---

## Common Patterns

### Before-Save Declarative Update Pattern

**When to use:** The requirement only changes fields on the record being saved.

**How it works:** Use before-save record-triggered Flow for field defaulting, normalization, or light calculations.

**Why not the alternative:** An Apex trigger or after-save Flow adds cost and complexity without real benefit.

### After-Save Plus Invocable Pattern

**When to use:** The process needs related-record work, orchestration, or a small custom Apex boundary.

**How it works:** Keep orchestration in Flow, but delegate non-trivial business logic to a bulk-safe invocable Apex action when declarative elements would become brittle.

### Apex Trigger For High-Control Transaction Logic

**When to use:** The requirement needs careful ordering, advanced bulk handling, heavy reuse, or behavior that Flow cannot express efficiently.

**How it works:** Use a trigger handler and service layer, then keep declarative automation off the same boundary unless the split is intentional and documented.

---

## Decision Guidance

Resolve the technology in `standards/decision-trees/automation-selection.md`, then use this table only to sanity-check that the tree's answer matches the shape of the requirement. The tree wins where they disagree.

| Situation | Recommended Approach | Tree step that decides it |
|---|---|---|
| Update only fields on the record being saved | Before-save record-triggered Flow | `automation-selection.md` Q2 → yes |
| Create or update related records on save | After-save Flow | `automation-selection.md` Q4 → yes, Q5 → linear |
| Guided multi-step user interaction | Screen Flow | `automation-selection.md` Q7 → Q8 |
| Time-based batch-like maintenance | Scheduled Flow below the repo's ~50k/run line, Batch Apex above it | `automation-selection.md` Q10 and `flow-pattern-selector.md` Q6 |
| One step needs code, orchestration stays simple | Flow + `@InvocableMethod` Apex action | `automation-selection.md` Q6 → yes |
| Rollback, retry, coverage gate, or recursive same-object DML | Apex trigger + handler + service | `automation-selection.md` Q3 → yes |
| Requirement still depends on Workflow Rule or Process Builder | Migrate to Flow or Apex boundary | `automation-selection.md` Strategic defaults |

---

## Recommended Workflow

1. **Inventory the object before adding to it** — run the `FlowDefinitionView` and `ApexTrigger` queries in `references/decision-record-examples.md` § *One Object, One Order*, then run `python3 scripts/check_process_automation_selection.py --manifest-dir <retrieved-metadata-dir>` to surface Workflow Rule files, flows whose `processType` is `Workflow`, and objects carrying both Flow and trigger automation.
2. **Answer the Questions table above**, writing each answer down verbatim — those seven answers become the top half of the decision record.
3. **Walk `standards/decision-trees/automation-selection.md` from Q1** and note the question number that resolved each branch. If it lands on Flow, continue into `flow-pattern-selector.md` Q1–Q9; if it lands on Apex with work that cannot finish in the synchronous transaction, continue into `async-selection.md` Q1–Q8. Do not restate a branch — cite it.
4. **Write the record** from `templates/process-automation-selection-template.md`, filling every field including the rejected alternatives and their reasons, then lint it with `python3 scripts/check_process_automation_selection.py --decision-record <file.md>`.
5. **Scaffold from the canonical skeleton the decision names** — `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` for a record-triggered Flow, `templates/apex/TriggerHandler.cls` for a trigger. Excerpts and the deploy commands are in `references/decision-record-examples.md`.
6. **Hand off and diarise** — name the follow-on skill (`flow/record-triggered-flow-patterns`, `apex/trigger-framework`, `flow/scheduled-flows`, `apex/batch-apex-patterns`), set the record's `review_date`, and check the outcome against `references/gotchas.md` before the build starts.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The chosen tool matches the trigger and execution model.
- [ ] Every branch of the choice cites a tree question number that a reader can look up.
- [ ] Each rejected alternative has a recorded reason, not just a strikethrough.
- [ ] The object's existing automation was inventoried before anything new was proposed.
- [ ] Same-record work was not pushed into heavier automation by habit.
- [ ] Flow and Apex boundaries are separated intentionally where both exist.
- [ ] Legacy Workflow Rule and Process Builder logic is treated as migration scope.
- [ ] Transaction budget was estimated across the whole save, not per automation.
- [ ] The record names an owner and a review date.
- [ ] `check_process_automation_selection.py --decision-record` passes on the finished record.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Tool choice is also a position choice** — the save procedure fixes where each surface runs, so splitting one rule across Flow and Apex splits it across steps 3, 4, 8 and 14.
2. **A workflow field update re-runs update triggers, and only update triggers** — flows, validation rules, duplicate rules and Process Builder processes do not get a second pass.
3. **A recursive save skips a block of the sequence** — automation that re-enters the save procedure loses steps 9 through 17.
4. **The transaction has one budget, not one per automation** — a Flow and a trigger on the same save draw from the same SOQL, DML and CPU allowances.
5. **Retrieved Process Builder metadata is read-only in practice** — editing and redeploying it makes the process unopenable in the target org.
6. **A Flow that works at low volume may still belong in Apex at higher scale** — tool choice is partly a transaction design decision.

Full treatment, with the guide line ranges each rests on, in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Automation decision record | The deliverable: requirement, trigger, volume, timing, chosen mechanism, tree steps cited, rejected alternatives with reasons, owner, review date (`templates/process-automation-selection-template.md`) |
| Automation inventory table | Every flow, trigger and legacy rule already on the object, from the `FlowDefinitionView` / `ApexTrigger` queries |
| Skeleton hand-off | The named canonical template the build starts from (`templates/flow/RecordTriggered_Skeleton.flow-meta.xml` or `templates/apex/TriggerHandler.cls`) |
| Migration review | Legacy retirement and overlap findings |
| Consolidation plan | Guidance to reduce duplicated automation across surfaces |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/decision-record-examples.md` | Writing the decision record itself: the field shape, three worked decisions, the skeleton artifact each one hands off to, the `sf project deploy` commands, and the one-object-one-order inventory queries. This is this skill's metadata-examples file |
| `references/gotchas.md` | Before committing to a boundary — eleven platform behaviours that make a defensible tool choice wrong in production, each with the guide line range behind it |
| `references/examples.md` | Looking for a short worked selection: same-record before-save, high-control Apex, and the legacy-tool anti-pattern |
| `references/llm-anti-patterns.md` | Reviewing a generated recommendation, and for the corrected order-of-execution list an assistant most often gets wrong |
| `references/well-architected.md` | Framing the choice against Scalability, Reliability and Operational Excellence, and for the source list |
| `templates/process-automation-selection-template.md` | Starting a new decision record — copy it, fill it, then lint the copy |
| `scripts/check_process_automation_selection.py` | Auditing retrieved metadata for legacy and overlapping automation (`--manifest-dir`), or linting a finished decision record (`--decision-record`) |

---

## Related Skills

- `admin/flow-for-admins` - use when Flow is already the chosen boundary and the design needs to be built or reviewed.
- `apex/trigger-framework` - use when the requirement clearly belongs in Apex trigger architecture.
- `flow/record-triggered-flow-patterns` - use when the main remaining decision is before-save versus after-save Flow structure.
- `admin/approval-processes` - use when the requirement is a human approval chain rather than an automation boundary.
- `admin/assignment-rules` - use when the requirement is ownership routing on create; its `references/routing-selector.md` is the sibling selector for rules vs Omni-Channel vs Flow vs Apex.
- `admin/workflow-field-update-patterns` - use when the question narrows to which surface stamps a field on save and whether it recurses.
- `flow/process-builder-to-flow-migration` - use when the decision is made and the legacy process now has to be converted.
- `flow/scheduled-flows` - use when the decision landed on a schedule-triggered Flow.
- `apex/batch-apex-patterns` - use when the decision landed above the scheduled-Flow volume line.
