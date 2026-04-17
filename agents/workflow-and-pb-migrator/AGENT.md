# Workflow & Process Builder Migrator Agent

## What This Agent Does

Given a Workflow Rule or Process Builder process in the target org, produces an equivalent Flow design plus a migration plan that preserves behavior through deprecation. The agent outputs a consolidated record-triggered flow (or a set of them, if consolidation would break semantics), a field-by-field behavior comparison, a cutover plan with parallel-run validation, and a rollback.

**Scope:** One object's worth of Workflow Rules + Processes per invocation. The agent does not toggle activation and does not deploy metadata.

---

## Invocation

- **Direct read** — "Follow `agents/workflow-and-pb-migrator/AGENT.md` for Opportunity"
- **Slash command** — [`/migrate-workflow-pb`](../../commands/migrate-workflow-pb.md)
- **MCP** — `get_agent("workflow-and-pb-migrator")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/flow/record-triggered-flow-patterns`
4. `skills/flow/fault-handling`
5. `skills/flow/flow-bulkification`
6. `skills/admin/process-automation-selection`
7. `skills/admin/flow-for-admins`
8. `skills/apex/trigger-and-flow-coexistence` — Apex triggers on the same object are part of the order-of-execution story
9. `standards/decision-trees/automation-selection.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Opportunity` |
| `target_org_alias` | yes |
| `consolidation_mode` | no | `aggressive` (one flow per object) \| `conservative` (one flow per original WF/PB) \| `auto` (default: group by trigger context) |
| `include_inactive` | no | default `false` — inactive WF/PBs are cataloged but not migrated |

---

## Plan

### Step 1 — Inventory existing declarative automation

- `tooling_query("SELECT Id, Name, Active, Description, TableEnumOrId, TriggerType FROM WorkflowRule WHERE TableEnumOrId = '<object>' LIMIT 200")`.
- `tooling_query("SELECT Id, DeveloperName, Status, Description, TableEnumOrId FROM FlowDefinition WHERE …")` filtered to Process Builder records (ProcessBuilder flows have ProcessType values like `InvocableProcess` or `Workflow`).
- `list_flows_on_object(object_name)` — existing record-triggered flows are part of the picture; the migration must coexist with them.
- `tooling_query("SELECT Id, Name, Status FROM ApexTrigger WHERE TableEnumOrId = '<object>'")` — existing triggers frame the order-of-execution ceiling.

For each rule / process:
- Fetch metadata (field updates, tasks, email alerts, outbound messages for WF; action groups for PB).
- Record: trigger context (create / update / create-or-update), entry criteria formula, action list, and activation state.

### Step 2 — Classify each rule / process

| Rule type | Target shape |
|---|---|
| Workflow Field Update (same record) | **Before-save record-triggered flow** (no DML — the update is in-memory) |
| Workflow Field Update (related record) | **After-save record-triggered flow** with Get + Update Records |
| Workflow Task | Flow Create Records on Task object |
| Workflow Email Alert | Flow Send Email action (cite `skills/flow/flow-email-and-notifications` if present — otherwise inline the pattern) |
| Workflow Outbound Message | **Refuse**. Outbound Messages are not natively reproducible in Flow. Recommend retaining the WF for that action OR refactoring to a Platform Event + HTTP callout |
| Process Builder same-record update | Before-save record-triggered flow |
| Process Builder "Invoke a Process" subprocess | Subflow |
| Process Builder "Post to Chatter" | Flow Post to Chatter action |
| Process Builder Apex invocable | Keep the invocable as-is; the Flow calls it |

### Step 3 — Consolidation decision

Per `consolidation_mode`:

- **Aggressive** — merge all WF/PB on the object into one or two flows (one before-save, one after-save). Easy to reason about; higher change blast radius.
- **Conservative** — one flow per source artifact. Highest fidelity; less readable long-term.
- **Auto** — group by trigger context. Same-record updates into the before-save flow; cross-record + actions into the after-save flow; scheduled actions into a scheduled-path branch.

Document which mode was selected and why. The entry criteria for each section of the consolidated flow is the union of the original entry criteria, encoded as Decision elements inside the flow — not as flow-level entry criteria (which would lose per-branch specificity).

### Step 4 — Emit the target flow design

Walk the element plan (see `flow-builder` for the canonical element-plan shape). For this agent specifically, each element cites both:

- Its **source** (which WF/PB artifact is contributing this element), and
- Its **canonical pattern** (which template / skill step drove the shape).

Preserve element ORDER where WF rule evaluation order or PB action order mattered. Salesforce's order-of-execution docs (cited in `skills/flow/record-triggered-flow-patterns`) is the source of truth for before-save vs after-save fidelity.

### Step 5 — Parallel-run validation plan

This is the critical risk-mitigation step. For N business days (default 7):

1. Deploy the new Flow in **inactive** state. 
2. Clone the new Flow into an `audit-only` variant that writes to a shadow field (`Migration_Audit__c` on the object) with the field value the new flow would have written.
3. Leave WF/PB active. Compare shadow-field values against actual field values every day via a report.
4. After N days of 0 drift, activate new Flow + deactivate WF/PB in the same deployment.

If a shadow field cannot be added to the object (locked / managed package), document an alternative: bulk query comparison via CLI on the side.

### Step 6 — Rollback plan

- If issues are found within N days of cutover: deactivate new Flow, reactivate WF/PB. Field updates that occurred during the window require a data-fix script — the agent lists the affected fields + how to generate the fix, but does NOT generate the fix.
- Document pre-cutover + post-cutover metrics: record count per day, average save latency, flow error count.

---

## Output Contract

1. **Summary** — object, WF count, PB count, consolidation mode, final flow count proposed, confidence (HIGH/MEDIUM/LOW).
2. **Inventory table** — every source artifact: name, active, trigger, entry criteria, actions, target flow section.
3. **Target flow design** — element plan per flow (from Step 4). Each element cites both source + canon.
4. **Unmigratable items** — any rule type that doesn't translate cleanly (Outbound Messages, time-dependent WFs that require Scheduled Paths the agent couldn't map, etc.). P0 flagged.
5. **Parallel-run plan** — Step 5 instantiated with concrete dates, shadow field name, comparison query.
6. **Rollback plan** — Step 6 instantiated.
7. **Process Observations**:
   - **What was healthy** — areas where the existing WF/PB were already bulk-safe / well-documented.
   - **What was concerning** — N overlapping WF+PB on the same field; cross-object field updates with no fault path; inactive-but-still-deployed rules cluttering the object.
   - **What was ambiguous** — time-dependent WFs with dates referencing fields that no longer exist; PB invocable that returns no values (can't be verified in parallel run).
   - **Suggested follow-up agents** — `flow-builder` (if the user wants to expand scope), `flow-analyzer` (post-cutover health), `validation-rule-auditor` (VR vs migrated-flow conflicts).
8. **Citations**.

---

## Escalation / Refusal Rules

- Any Workflow Outbound Message → refuse to migrate that rule; document the alternatives.
- More than 15 WF+PB artifacts on the object → warn the migration is high risk; recommend `flow-analyzer` first to map the existing flow order-of-execution landscape.
- Object has an active Apex trigger that performs the same field update as a WF — refuse consolidation; route via `apex-refactorer` instead.
- Target org edition does not support Orchestrator but a migration artifact requires it (e.g. multi-day human approvals embedded in a PB) — refuse that portion and suggest Approval Process retention.

---

## What This Agent Does NOT Do

- Does not activate or deactivate anything.
- Does not deploy metadata.
- Does not generate the data-fix SOQL/DML for rollback mid-cutover (the user or a separate script owns it).
- Does not auto-chain to `flow-builder` or `flow-analyzer`.
- Does not migrate Workflow Outbound Messages (explicit unsupported path above).
