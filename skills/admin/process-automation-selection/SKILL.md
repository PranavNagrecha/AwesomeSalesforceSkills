---
name: process-automation-selection
description: "Use when deciding which Salesforce automation tool should own a requirement, including before-save and after-save Flow, screen Flow, scheduled Flow, invocable Apex, Apex triggers, and migration off Workflow Rules or Process Builder. Triggers: 'Flow or Apex trigger', 'which automation tool should I use', 'Process Builder migration', 'Workflow Rule retirement', 'same-record update or trigger'. NOT for detailed implementation of a Flow or trigger after the automation boundary has already been chosen."
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
tags:
  - automation-selection
  - flow-vs-apex
  - process-builder-migration
  - workflow-rule-retirement
  - trigger-decision
inputs:
  - "triggering event, user interaction model, and record volume"
  - "whether the work is same-record, related-record, async, or integration-heavy"
  - "existing automation already attached to the object or process"
outputs:
  - "automation tool recommendation"
  - "migration or consolidation findings"
  - "boundary decision for Flow, Apex, or legacy retirement"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# Process Automation Selection

Use this skill when the hard question is not how to build the automation, but which automation surface should own it. Salesforce gives teams several ways to automate work, and most production problems start with the wrong boundary choice: using Apex when a before-save Flow was enough, forcing a Flow to behave like a service layer, or leaving legacy Workflow Rules and Process Builder logic in place because it still appears to work.

The decision should be based on execution model, scale, ownership, and migration posture. A same-record field normalization rule belongs in a different tool than a high-volume cross-object transaction or a guided user journey. Treat legacy tools as migration targets, not fresh design options. Salesforce migration guidance published in 2022 stated that Workflow Rules and Process Builder would stop functioning after December 31, 2025, so by March 13, 2026 they should be considered retirement work, not architecture choices for new delivery.

---

## Before Starting

Gather this context before working on anything in this domain:

- What actually triggers the process: record save, user click, time schedule, event, or external call?
- Does the automation only update the triggering record, or does it coordinate related records, integrations, or user interaction?
- What record volume or transaction pressure exists in real life, not just in demo data?
- Is legacy Workflow Rule, Process Builder, or overlapping trigger logic already attached to the same business process?

---

## Core Concepts

### Choose By Execution Model, Not Team Habit

Before-save Flow, after-save Flow, scheduled Flow, screen Flow, and Apex trigger all solve different execution problems. Pick the one whose runtime behavior matches the requirement rather than the one the team is most comfortable editing.

### Flow First Does Not Mean Flow For Everything

Flow is the preferred default for declarative, maintainable automation, especially when the logic is readable and the platform already provides the needed behavior. Apex becomes the right choice when strict transaction control, heavier reuse, complex looping, or fine-grained performance control matter more than declarative ownership.

### Same-Record Versus Related-Record Work Is A Major Split

Simple updates to the triggering record belong in before-save record-triggered Flow whenever possible. Related-record DML, richer orchestration, or custom service boundaries usually move the decision to after-save Flow, invocable Apex, or triggers.

### Legacy Automation Must Be Retired Deliberately

Workflow Rules and Process Builder should be treated as migration inventory. Even if they are still present in metadata, they should not remain the design center for new work.

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

| Situation | Recommended Approach | Reason |
|---|---|---|
| Update only fields on the record being saved | Before-save record-triggered Flow | Lowest-cost platform option |
| Create or update related records on save | After-save Flow | Declarative and explicit |
| Guided multi-step user interaction | Screen Flow | Built for user-driven process |
| Time-based batch-like maintenance | Scheduled Flow | Fits periodic execution |
| Complex transaction behavior, heavy reuse, or strict service logic | Apex trigger or service + invocable boundary | Better control and testability |
| Requirement still depends on Workflow Rule or Process Builder | Migrate to Flow or Apex boundary | Legacy tools are retirement targets |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The chosen tool matches the trigger and execution model.
- [ ] Same-record work was not pushed into heavier automation by habit.
- [ ] Flow and Apex boundaries are separated intentionally where both exist.
- [ ] Legacy Workflow Rule and Process Builder logic is treated as migration scope.
- [ ] The object does not accumulate overlapping automation with no clear owner.
- [ ] The team can explain why a simpler automation surface was rejected.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Before-save Flow is often the cheapest answer for same-record updates** - teams still overuse Apex or after-save logic for work the platform already optimizes.
2. **Mixed Flow and trigger automation can be individually valid but collectively opaque** - the support burden is often the real defect.
3. **Legacy tools distort architecture discussions** - if Workflow Rule or Process Builder logic still exists, teams sometimes design around the old implementation instead of replacing it.
4. **A Flow solution that works at low volume may still belong in Apex at higher scale** - tool choice is partly a transaction design decision.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Automation boundary recommendation | Best-fit tool choice and why |
| Migration review | Legacy retirement and overlap findings |
| Consolidation plan | Guidance to reduce duplicated automation across surfaces |

---

## Related Skills

- `admin/flow-for-admins` - use when Flow is already the chosen boundary and the design needs to be built or reviewed.
- `apex/trigger-framework` - use when the requirement clearly belongs in Apex trigger architecture.
- `flow/record-triggered-flow-patterns` - use when the main remaining decision is before-save versus after-save Flow structure.
