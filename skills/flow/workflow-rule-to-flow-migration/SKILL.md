---
name: workflow-rule-to-flow-migration
description: "Migrate Workflow Rules to record-triggered Flows: field update mapping, email alert migration, outbound message alternatives using Flow Core Actions, time-based workflow replacement with Scheduled Paths. NOT for Process Builder migration (use process-builder-to-flow-migration), NOT for building new flows from scratch."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how to migrate workflow rules to flow builder"
  - "workflow rule retirement migration guide"
  - "convert workflow field update to record-triggered flow"
  - "replace time-based workflow with flow scheduled path"
  - "outbound message replacement in flow after workflow retirement"
  - "workflow rule end of support December 2025 migration"
  - "ISCHANGED ISNEW criteria workflow rule cannot migrate"
tags:
  - workflow-rules
  - migration
  - flow-builder
  - record-triggered-flow
  - automation-modernization
  - outbound-message
  - time-based-workflow
  - retire-workflow-rules
inputs:
  - "List of active and inactive Workflow Rules on target org per object"
  - "Action types used: field updates, email alerts, tasks, outbound messages"
  - "Time-based workflow actions inventory (evaluation criteria and scheduled offsets)"
  - "Existing Outbound Message definitions (must exist before Flow can reference them)"
outputs:
  - "Record-triggered Flow(s) replacing Workflow Rule criteria and actions"
  - "Scheduled Paths replacing time-based workflow actions"
  - "Outbound Message Core Action configurations"
  - "Inventory of unsupported criteria/actions requiring manual rebuild"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Workflow Rule to Flow Migration

Use this skill when orgs still have active Workflow Rules that must migrate to record-triggered Flows before the December 31 2025 end-of-support deadline. New Workflow Rule creation was blocked in Spring '25; existing rules continue to execute but receive no bug fixes. This skill is distinct from process-builder-to-flow-migration — Workflow Rules and Process Builder share the same retirement timeline but require different migration approaches.

---

## Before Starting

Gather this context before working on anything in this domain:

- Export all Workflow Rules per object via Setup > Process Automation > Workflow Rules or query `WorkflowRule` via Tooling API
- Identify action types per rule: field updates, email alerts, tasks, outbound messages, time-based actions
- Any rule using `ISCHANGED()`, `ISNEW()`, global variables, record-type-based criteria, or related-record field updates requires manual rebuild — the Migrate to Flow tool cannot handle these
- Confirm that Outbound Message definitions exist in Setup before attempting to reference them as Flow Core Actions

---

## Core Concepts

### What the Migrate to Flow Tool Handles

Setup > Migrate to Flow converts Workflow Rules to INACTIVE record-triggered flows for review. The tool converts:
- **Field updates** → Update Records or Assignment elements
- **Email alerts** → Send Email Action elements
- **Outbound messages** → Outbound Message Core Action elements (definition must pre-exist)

The tool does **NOT** handle:
- **Task creation** → must be rebuilt as Create Records elements
- **`ISCHANGED()` / `ISNEW()` criteria** → rebuild with `{!$Record__Prior.FieldName}` comparisons
- **Global variables in criteria** → no equivalent in Flow
- **Record-type-based criteria** → rebuild with explicit Decision conditions
- **Related-record field updates** → rebuild with Get Records + Update Records

### Outbound Message Migration

Workflow Rules can invoke Outbound Messages (SOAP callouts to external endpoints). In Flow, outbound messages are available as **Core Actions** — but the Outbound Message definition must already exist in Setup > Outbound Messages before the Flow can reference it. The tool generates the action reference; it does not create the definition.

If the receiving endpoint expects the original Workflow Rule SOAP schema, verify that the Flow-generated outbound message produces the same WSDL payload structure. Schema differences can break integrations silently.

### Time-Based Action Replacement

Workflow time-based actions (e.g., "send email 5 days after close date") are replaced using **Scheduled Paths** on record-triggered flows. Set the Scheduled Path's time source field to the same date/time field used in the workflow time trigger. When the original Workflow Rule is deactivated, pending time-based actions in the queue are cancelled — they do not transfer to the Flow.

---

## Common Patterns

### Tool-Eligible Field Update Migration

**When to use:** Workflow Rule updates fields on the same record, uses no ISCHANGED/ISNEW criteria, no tasks, no global variables.

**How it works:**
1. Setup > Migrate to Flow > select rule > Convert
2. Review the generated inactive flow in Flow Builder: verify Decision conditions match original rule criteria
3. Add Fault Paths to Update Records elements (tool never generates fault paths)
4. Set Flow Trigger Explorer priority matching intended execution order
5. Test with 200+ records in sandbox; activate and deactivate source Workflow Rule simultaneously

### Time-Based Action to Scheduled Path

**When to use:** Workflow Rule has time-based actions (e.g., send follow-up email N days after OpportunityCloseDate).

**How it works:**
In the record-triggered flow, add a Scheduled Path:
- Set path to run "N Days After" the relevant date field
- Move all actions that previously ran as time-based into this Scheduled Path
- Note: pending in-flight actions from the original Workflow Rule will be cancelled on deactivation — plan cutover timing accordingly

### Manual Rebuild for ISCHANGED Criteria

**When to use:** Workflow Rule uses `ISCHANGED(FieldName)` or `ISNEW()` in entry criteria.

**How it works:** In a new record-triggered flow's Decision element:
- `ISCHANGED(FieldName)` → `{!$Record.FieldName} != {!$Record__Prior.FieldName}` (for after-save) or "Is Changed" condition (for entry criteria)
- `ISNEW()` → trigger set to "Only when a record is created" OR Decision: `{!$Record__Prior.Id} Is Null`

---

## Decision Guidance

| Scenario | Recommended Approach | Reason |
|---|---|---|
| Field updates, email alerts only | Migrate to Flow tool | Fastest, lowest risk |
| Outbound messages | Migrate to Flow tool (definition must exist) | Tool handles Core Action reference |
| Task creation | Manual rebuild with Create Records | Tool cannot convert |
| Time-based actions | Manual rebuild with Scheduled Paths | Tool cannot convert async |
| ISCHANGED/ISNEW criteria | Manual rebuild with `$Record__Prior` | No direct tool mapping |
| Multiple rules on same object | Consolidate into one flow with Decision elements | Simplifies execution order |

---

## Recommended Workflow

1. **Inventory all Workflow Rules**: query `SELECT Id, Name, TableEnumOrId, Active FROM WorkflowRule` via Tooling API or SOQL; note action types for each rule.
2. **Triage tool-eligible vs. manual-rebuild**: mark any rule with ISCHANGED/ISNEW criteria, task actions, or global variables as manual-rebuild.
3. **Verify Outbound Message definitions exist**: for any rule with outbound message actions, confirm the definition exists in Setup before running the tool.
4. **Run Migrate to Flow on eligible rules**: Setup > Migrate to Flow > select rule > Convert. Tool creates INACTIVE flow — review in Flow Builder.
5. **Rebuild unsupported elements**: add Create Records for tasks, Scheduled Paths for time-based actions, rebuild ISCHANGED criteria with `$Record__Prior`.
6. **Add Fault Paths**: add fault connectors to all Update Records and Create Records elements — the tool never generates them.
7. **Assign Flow Trigger Explorer priorities**: open Flow Trigger Explorer for the object; assign priority integers preserving intended order relative to other flows.
8. **Test in sandbox with bulk data**: load 200+ records, verify field values and email alerts, confirm time-based path scheduling. 
9. **Activate Flow, deactivate Workflow Rule simultaneously**: never run both active on the same object.

---

## Review Checklist

- [ ] All Workflow Rules inventoried; unsupported criteria/actions identified before running tool
- [ ] Outbound Message definitions confirmed existing before running tool
- [ ] ISCHANGED()/ISNEW() criteria rebuilt with `$Record__Prior` comparisons
- [ ] Task creation rebuilt as Create Records elements
- [ ] Scheduled Paths added for all time-based actions
- [ ] Fault Paths added to all DML elements
- [ ] Flow Trigger Explorer priorities assigned
- [ ] Workflow Rule deactivated the same moment the Flow is activated
- [ ] Pending time-based actions in flight accounted for in cutover plan

---

## Salesforce-Specific Gotchas

1. **Pending time-based workflow actions are cancelled on deactivation** — Like Process Builder scheduled actions, pending time-based workflow queue entries are silently cancelled when the Workflow Rule is deactivated. No transfer occurs. Audit `ProcessInstanceStep` and `AsyncApexJob` for in-flight actions before cutting over.
2. **Outbound message SOAP schema may differ from Flow-generated payload** — If the receiving endpoint validates the incoming SOAP envelope against the original Workflow-generated WSDL, verify that the Flow Core Action sends the same structure. Schema differences can silently break integrations without error in Salesforce.
3. **ISCHANGED() and ISNEW() silently dropped or mis-mapped by the tool** — The Migrate to Flow tool does not warn about ISCHANGED/ISNEW criteria and may omit them or fire unconditionally. Always audit these criteria before using the tool.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Inactive record-triggered flow | Generated by tool or manually built; review before activation |
| Scheduled Paths | Replace time-based workflow actions in the flow |
| Outbound Message Core Actions | Reference pre-existing Outbound Message definitions |
| Workflow Rule deactivation log | Timestamp record of each rule deactivated |

---

## Related Skills

- `flow/process-builder-to-flow-migration` — companion skill for Process Builder retirement
- `flow/record-triggered-flow-patterns` — canonical patterns for the destination flow type
- `flow/fault-handling` — add fault paths to migrated flows
- Decision tree: `standards/decision-trees/automation-selection.md`
