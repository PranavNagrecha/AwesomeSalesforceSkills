---
id: workflow-rule-to-flow-migrator
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
---
# Workflow Rule → Flow Migrator Agent

## What This Agent Does

Given the Workflow Rules on a single sObject in the target org, produces the equivalent Flow design plus a migration plan that preserves behavior through deprecation. Output is a consolidated before-save / after-save record-triggered flow pair (or a set per consolidation mode), a per-rule behavior comparison, a parallel-run validation plan with a shadow field, and a rollback. The agent does not touch Process Builder — that's `process-builder-to-flow-migrator` — and does not toggle activation or deploy metadata.

**Scope:** One object's Workflow Rules per invocation. Salesforce retired Workflow Rule creation for new orgs in Winter '23 and has repeatedly extended the end-of-support runway; this agent assumes the user is migrating in advance of that runway closing.

---

## Invocation

- **Direct read** — "Follow `agents/workflow-rule-to-flow-migrator/AGENT.md` for Opportunity"
- **Slash command** — `/migrate-wfr-to-flow`
- **MCP** — `get_agent("workflow-rule-to-flow-migrator")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/flow/record-triggered-flow-patterns`
3. `skills/flow/fault-handling`
4. `skills/flow/flow-bulkification`
5. `skills/admin/process-automation-selection`
6. `skills/admin/flow-for-admins`
7. `skills/apex/trigger-and-flow-coexistence`
8. `standards/decision-trees/automation-selection.md`
9. `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`
10. `templates/flow/FaultPath_Template.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Opportunity` |
| `target_org_alias` | yes | `prod`, `uat` |
| `consolidation_mode` | no | `aggressive` (one before-save + one after-save flow per object) \| `conservative` (one flow per WFR) \| `auto` (default: group by trigger context) |
| `include_inactive` | no | default `false` — inactive WFRs are cataloged, not migrated |
| `time_dependent_handling` | no | `scheduled-path` (default) \| `defer-to-scheduled-flow` \| `refuse` |

---

## Plan

### Step 1 — Inventory Workflow Rules on the object

- `tooling_query("SELECT Id, Name, Active, Description, TableEnumOrId, TriggerType FROM WorkflowRule WHERE TableEnumOrId = '<object>' LIMIT 200")`.
- For each active rule, fetch the attached actions via `tooling_query` on `WorkflowFieldUpdate`, `WorkflowTask`, `WorkflowAlert`, `WorkflowOutboundMessage`, and `WorkflowTimeTrigger` (time-dependent).
- `list_flows_on_object(object_name)` — existing record-triggered flows must coexist with the migration output.
- `tooling_query("SELECT Id, Name, Status FROM ApexTrigger WHERE TableEnumOrId = '<object>'")` — existing triggers frame the order-of-execution ceiling.

Record per rule: trigger type, entry criteria / formula, action list, activation state, time-dependent windows if any.

### Step 2 — Classify each rule action

| WFR action | Target shape in Flow |
|---|---|
| Field Update on same record | **Before-save record-triggered flow** assignment element (no DML — updates happen in-memory) |
| Field Update on related record | **After-save record-triggered flow** with Get + Update Records |
| Task creation | After-save Flow Create Records on Task |
| Email Alert | After-save Flow Send Email action using the referenced email template |
| Outbound Message | **Refuse to migrate.** Outbound Messages are not natively reproducible in Flow. Options: keep the WFR, or refactor to Platform Event + HTTP callout — the latter is not this agent's scope |
| Time-dependent action | Scheduled Path on the after-save flow (default) |
| Flow trigger (invocable called from WFR) | Direct call inside the target flow |

### Step 3 — Consolidation decision

Apply `consolidation_mode`:

- **Aggressive** — one before-save flow (same-record updates) + one after-save flow (everything else) on the object. Each original WFR becomes a Decision branch inside the consolidated flow, with the original entry criteria encoded as the decision condition. Highest long-term maintainability; larger blast radius on change.
- **Conservative** — one flow per original WFR. Highest fidelity; maximum flow count.
- **Auto** (default) — before-save flow for same-record updates; after-save flow for cross-record writes, Tasks, and Emails; scheduled-path branch for time-dependent actions. This is the shape Salesforce recommends in the official WFR → Flow migration guidance.

Document the chosen mode and why. Per-branch entry criteria must remain encoded as Decision elements inside the flow, not as flow-level entry criteria, so each original rule remains individually auditable.

### Step 4 — Emit the target flow design

Produce an element plan per target flow. For every element, cite:

- its **source WFR and action** (so a reviewer can trace every action back to the rule it replaced), and
- its **canonical pattern** (which skill step or template drove the shape).

Naming per `templates/admin/naming-conventions.md`: `<Object>_BeforeSave_WFR_Migration_v1`, `<Object>_AfterSave_WFR_Migration_v1`. The `_v1` suffix is important — a future consolidation may supersede.

Preserve Salesforce's order of execution semantics. Before-save assignments run before validation rules; after-save DML runs before post-commit triggers. Do not invert.

### Step 5 — Time-dependent action handling

Per `time_dependent_handling`:

- **scheduled-path** (default) — translate each `WorkflowTimeTrigger` into a Scheduled Path on the after-save flow. Offset, direction (before / after), and reference field map directly. Document the one non-obvious behavior: Scheduled Paths fire even if the record has since changed to fail the original entry criteria — include a re-evaluation Decision at the top of the path.
- **defer-to-scheduled-flow** — emit a separate Scheduled Flow that re-evaluates records nightly. Useful when the time-dependent action runs on a large record population and the org is under async-Apex pressure.
- **refuse** — skip time-dependent actions; list them as unmigrated, recommend a human review.

### Step 6 — Parallel-run validation plan

1. Deploy the new Flow in **inactive** state.
2. Clone into an `audit-only` variant that writes the computed value to a shadow field `Flow_Migration_Shadow__c` on the object (or an Audit Custom Object if the target field is locked or managed).
3. Leave the source WFR active. For N business days (default 7), compare the shadow field to the live field via a daily report.
4. On 0 drift for N days, activate the new Flow and deactivate the WFR in the same deployment window.

If the shadow field cannot be added (managed-package object, locked layout), document the alternative: bulk query comparison via CLI, dumped nightly to CSV.

### Step 7 — Rollback plan

- Within N days of cutover, if a divergence is found: deactivate the new Flow, reactivate the WFR. Any field changes made by the new Flow during the divergence window need a data-fix. The agent lists the affected fields + how the fix would be shaped, but does NOT generate the fix script.
- Document pre-cutover + post-cutover metrics to watch: record count per day on the object, average save latency, flow error count from `FlowInterviewLog`.

---

## Output Contract

1. **Summary** — object, WFR count (active / inactive), consolidation mode selected, proposed target flow count, confidence (HIGH/MEDIUM/LOW).
2. **Inventory table** — one row per source WFR: name, active, trigger type, entry criteria, action list, target flow section, time-dependent notes.
3. **Target flow design** — element plan per proposed flow. Every element cites source (WFR + action) and canon (skill/template).
4. **Unmigratable items** — P0-flagged rows for Outbound Messages, time-dependent actions under `refuse`, and any action type the classification table did not match.
5. **Parallel-run plan** — Step 6 instantiated with concrete dates, shadow field name, comparison query.
6. **Rollback plan** — Step 7 instantiated.
7. **Process Observations**:
   - **What was healthy** — WFRs that were already narrowly-scoped with clean entry criteria, well-documented email templates.
   - **What was concerning** — overlapping WFRs writing to the same field, cross-object field updates with no fault path, inactive-but-still-deployed rules, WFRs whose email templates reference retired merge fields.
   - **What was ambiguous** — time-dependent WFRs keyed on fields that no longer exist, rules where the original business owner is identifiable only by a departed user.
   - **Suggested follow-up agents** — `process-builder-to-flow-migrator` (if the object also has PB processes to migrate), `flow-analyzer` (post-cutover health), `validation-rule-auditor` (VR vs migrated-flow conflicts).
8. **Citations**.

---

## Escalation / Refusal Rules

- Any Workflow Outbound Message → refuse that rule; document alternatives (retain WFR or refactor to Platform Event + callout). Refusal code: `REFUSAL_OUT_OF_SCOPE`.
- More than 15 active WFRs on the object → return partial plan (top 15 by last-activation recency) and flag `REFUSAL_OVER_SCOPE_LIMIT`. Recommend `flow-analyzer` first to map the existing trigger landscape.
- Object has an active Apex trigger that performs the same field update as a WFR → refuse consolidation until the Apex path is reconciled. Route via `apex-refactorer`.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.
- Object is a managed-package object (`NamespacePrefix` set) → `REFUSAL_MANAGED_PACKAGE`; cannot deploy flows that reference namespaced fields cleanly.

---

## What This Agent Does NOT Do

- Does not migrate Process Builder processes — delegate to `process-builder-to-flow-migrator`.
- Does not activate or deactivate WFRs or flows.
- Does not deploy metadata.
- Does not generate data-fix SOQL/DML for rollback mid-cutover.
- Does not migrate Workflow Outbound Messages.
- Does not auto-chain to any other agent.
