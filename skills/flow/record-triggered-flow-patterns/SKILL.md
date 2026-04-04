---
name: record-triggered-flow-patterns
description: "Use when designing or reviewing Salesforce record-triggered Flows, especially before-save vs after-save behavior, entry criteria, recursion avoidance, and when to escalate to Apex. Triggers: 'before save vs after save', '$Record__Prior', 'record-triggered flow', 'order of execution', 'flow recursion'. NOT for screen-flow UX or pure bulkification work when the trigger model is already correct."
category: flow
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
tags:
  - record-triggered-flow
  - before-save
  - after-save
  - order-of-execution
  - recursion
triggers:
  - "before save vs after save flow choice"
  - "record triggered flow running too often"
  - "after save flow updating the same record"
  - "how do I use $Record__Prior in flow"
  - "when should this be apex instead of flow"
  - "flow runs too many times on update"
inputs:
  - "business event that should trigger automation"
  - "whether only the current record or related records must change"
  - "existing Apex, validation rules, and other automation on the same object"
outputs:
  - "record-triggered flow design recommendation"
  - "review findings for trigger context and recursion risk"
  - "decision on before-save, after-save, or Apex"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when the hard part is not "how do I automate" but "what is the right record-triggered pattern for this object and this event?" The purpose is to choose the correct trigger context, control how often the flow runs, and keep record-triggered automation aligned with Salesforce order-of-execution behavior.

## Before Starting

- Is the requirement only to change fields on the triggering record, or must it touch related data, send notifications, or call external systems?
- What other automation already runs on the object: validation rules, Apex triggers, duplicate rules, or other record-triggered flows?
- Does the flow need to act on create only, update only, specific field changes, or every save?

## Core Concepts

### Before-Save Is For Fast Same-Record Changes

Before-save record-triggered flows are optimized for updating fields on the record currently being saved. They should be the default choice when the requirement is enrichment, normalization, or lightweight decisioning on that same record.

### After-Save Is For Committed Side Effects

After-save flows exist for related-record writes, notifications, subflows, actions, and work that depends on the record being committed. They are more flexible, but they are also more expensive and easier to design badly.

### Entry Criteria Is A Design Tool, Not Just A Filter

A record-triggered flow that runs on every update without clear conditions becomes hidden operational debt. Entry criteria, optimized start settings, and explicit field-change checks are what keep the flow from retriggering for irrelevant edits.

### Order Of Execution Still Applies

Record-triggered flows do not replace Salesforce order of execution; they participate in it. That means validation rules, duplicate rules, Apex triggers, and workflow side effects still matter when deciding whether Flow is safe or whether Apex should own the automation boundary.

## Common Patterns

### Before-Save Enrichment Pattern

**When to use:** Only the triggering record needs calculated defaults, normalized values, or field derivation.

**How it works:** Use a before-save flow with tight entry criteria and assignments on `$Record`, with no related-record work.

**Why not the alternative:** An after-save flow would spend extra DML and risks re-entry for a simple same-record requirement.

### After-Save Related-Record Pattern

**When to use:** Saving the parent record should create, update, or notify something else.

**How it works:** Use after-save with explicit changed-field checks, collect related writes carefully, and ensure the flow cannot keep retriggering itself.

**Why not the alternative:** Before-save cannot perform the full range of related-record side effects.

### Escalate To Apex For Complex Transaction Logic

**When to use:** The automation needs deep branching, complex collections, callouts, or precise control with other trigger logic.

**How it works:** Keep Flow as the orchestrator only if that is still simpler than a trigger or invocable Apex boundary. Otherwise move the logic into code intentionally.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Update fields on the saving record only | Before-save record-triggered flow | Fastest and simplest pattern |
| Create or update related records after commit | After-save record-triggered flow | Related side effects require after-save |
| Need field-change detection on update | Use entry criteria plus prior-value checks | Prevents irrelevant re-runs and recursion |
| Heavy orchestration or deep transaction control required | Apex or mixed Flow/Apex design | Record-triggered Flow is not always the best boundary |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] Before-save is used for same-record updates whenever possible.
- [ ] After-save paths justify every related-record write or action.
- [ ] Entry criteria and field-change logic prevent unnecessary reruns.
- [ ] The flow does not update the same record after-save without an explicit recursion guard.
- [ ] Order-of-execution interactions with Apex and validation rules were reviewed.
- [ ] The team explicitly considered whether the use case should move to Apex instead.

## Salesforce-Specific Gotchas

1. **After-save updates to the triggering record can retrigger automation** — this is one of the most common Flow recursion smells.
2. **Before-save cannot replace all trigger behaviors** — if the logic needs related-record work, notifications, or callouts, the design must move to after-save or another boundary.
3. **A broad start condition becomes hidden operational cost** — flows that fire on every edit are harder to debug and more likely to clash with other automation.
4. **Multiple automations on one object still interact** — record-triggered flows are not isolated from Apex triggers, duplicate rules, or validation behavior.

## Output Artifacts

| Artifact | Description |
|---|---|
| Trigger-context recommendation | Clear before-save, after-save, or Apex choice with reasons |
| Record-triggered flow review | Findings on entry criteria, recursion risk, and order-of-execution fit |
| Refactor plan | Specific changes to move a flow into the right trigger pattern |

## Related Skills

- `flow/flow-bulkification` — use when the pattern is correct but the volume behavior is unsafe.
- `flow/fault-handling` — use when the main concern is rollback behavior and user/admin error paths.
- `apex/trigger-framework` — use when Flow is no longer the right transaction boundary.
