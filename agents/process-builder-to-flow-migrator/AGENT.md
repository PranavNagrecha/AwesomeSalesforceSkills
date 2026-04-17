---
id: process-builder-to-flow-migrator
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
---
# Process Builder → Flow Migrator Agent

## What This Agent Does

Given the Process Builder processes running on a single sObject in the target org, produces the equivalent Flow design plus a migration plan that preserves behavior through deprecation. Output is a consolidated record-triggered flow design (or multiple flows per consolidation mode), a process-by-process comparison, a parallel-run validation plan, and a rollback. The agent does not touch Workflow Rules — that's `workflow-rule-to-flow-migrator` — and does not toggle activation or deploy metadata.

**Scope:** One object's Process Builder processes per invocation. Salesforce stopped allowing new Process Builder processes to be created in Winter '23 and continues to phase out runtime support; this agent assumes the user is migrating ahead of the phased runway.

---

## Invocation

- **Direct read** — "Follow `agents/process-builder-to-flow-migrator/AGENT.md` for Case"
- **Slash command** — `/migrate-pb-to-flow`
- **MCP** — `get_agent("process-builder-to-flow-migrator")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/flow/record-triggered-flow-patterns`
3. `skills/flow/fault-handling`
4. `skills/flow/flow-bulkification`
5. `skills/flow/subflows-and-reusability`
6. `skills/admin/process-automation-selection`
7. `skills/admin/flow-for-admins`
8. `skills/apex/trigger-and-flow-coexistence`
9. `skills/apex/order-of-execution-deep-dive`
10. `standards/decision-trees/automation-selection.md`
11. `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Case` |
| `target_org_alias` | yes |
| `consolidation_mode` | no | `aggressive` (one flow per object) \| `conservative` (one flow per process) \| `auto` (default: group by trigger context) |
| `include_inactive` | no | default `false` |
| `invocable_handling` | no | `preserve` (default, reuse as-is) \| `inline` (inline the invocable action into the flow if it's a single Flow action) |

---

## Plan

### Step 1 — Inventory Process Builder processes

Process Builder processes are stored as Flow metadata with `ProcessType` in `{Workflow, InvocableProcess}`:

- `tooling_query("SELECT Id, DeveloperName, MasterLabel, Status, Description, ProcessType, Metadata FROM Flow WHERE ProcessType IN ('Workflow','InvocableProcess')")`. Filter the results by the object — the `Metadata.processMetadataValues` entries carry the object API name.
- `list_flows_on_object(object_name)` — existing record-triggered flows and legacy PB shells both surface here; a Process Builder process appears as a flow entry whose metadata discloses `ProcessBuilder` as the source.
- `tooling_query("SELECT Id, Name, Status FROM ApexTrigger WHERE TableEnumOrId = '<object>'")` — existing triggers frame the order-of-execution ceiling.

Record per process: trigger context (create / update / create-or-update), criteria node tree, action groups per node, activation state.

### Step 2 — Walk the action tree and classify

A Process Builder process is a sequence of criteria nodes; each criterion has one action group; PBs can also loop via "Evaluate the Next Criteria" behavior.

| PB action | Target shape |
|---|---|
| Update Records (same record) | **Before-save** record-triggered flow assignment |
| Update Records (related record) | **After-save** Get + Update Records |
| Create a Record | After-save Flow Create Records |
| Post to Chatter | Flow Post to Chatter action |
| Send Email (to Email Template) | Flow Send Email action |
| Submit for Approval | Flow Submit for Approval action — confirm the target Approval Process still exists and is not itself mid-migration |
| Invoke a Process | Subflow; the target process becomes a subflow of the same name |
| Launch a Flow | Direct subflow call; preserve input variables |
| Call Apex (Invocable) | Preserve invocable action as-is unless `invocable_handling=inline` and the invocable is itself a single action |
| Quick Action | Flow quick-action element |
| Quip / external | Usually refuses; these often aren't representable cleanly in Flow |

PB "Evaluate the Next Criteria" semantics matter: unlike "Stop" or "Evaluate the Next Criteria on the Same Record", the default in some process versions stops after the first matching criterion. Replicate exactly by reading `Metadata.processMetadataValues[nextCriteria]` per criterion node.

### Step 3 — Consolidation decision

Apply `consolidation_mode`:

- **Aggressive** — one before-save + one after-save flow on the object. Each original PB criterion becomes a Decision inside the appropriate flow.
- **Conservative** — one flow per source PB. Highest fidelity; highest flow count.
- **Auto** (default) — before-save flow for same-record updates; after-save flow for cross-record writes, Chatter posts, Create Records, Submit for Approval, and Invocables.

Document the chosen mode. Per-criterion entry conditions are encoded as Decision elements inside the flow, not as flow-level entry criteria, so each original criterion remains individually auditable.

### Step 4 — Respect the PB order-of-execution quirk

PB fires AFTER Flow and triggers in the create/update save order. When consolidating, the new record-triggered flow must execute at the correct position: before-save flows move the work earlier in the save order (cheaper but cannot do DML), after-save flows stay in the same general slot PB occupied.

If any PB action relies on the AFTER position of PB (e.g. reads a field that a trigger set earlier in the save order), it MUST migrate to an after-save flow, never before-save — otherwise the read returns a stale value.

### Step 5 — Subprocess (InvocableProcess) handling

Process Builder could invoke another Process Builder (a subprocess). Migrate by:

1. Migrate the subprocess first (recursively). If out of scope for this invocation, flag it and refuse to migrate the parent until the subprocess is handled.
2. Replace the parent's "Invoke a Process" action with a Subflow element pointing at the migrated subprocess's Flow.

Cycles (Process A calls Process B calls A) → refuse; cycles are not valid in Flow either but must be broken by a human.

### Step 6 — Emit the target flow design

Produce an element plan per target flow. Every element cites:

- its **source PB + criterion node** (traceability),
- its **canonical pattern** (skill / template citation).

Naming per `templates/admin/naming-conventions.md`: `<Object>_BeforeSave_PB_Migration_v1`, `<Object>_AfterSave_PB_Migration_v1`.

### Step 7 — Parallel-run validation plan

Identical structure to `workflow-rule-to-flow-migrator`:

1. Deploy new Flow inactive. Clone into an `audit-only` variant writing to `Flow_Migration_Shadow__c` (or a dedicated Audit Custom Object).
2. Leave the source PB active. Compare shadow vs live for N business days (default 7) via a daily report.
3. On 0 drift, activate Flow + deactivate PB in the same deployment.

Note: Process Builder instances in flight at cutover complete under PB semantics. Document this boundary and track for N days post-cutover.

### Step 8 — Rollback plan

- Reactivate PB, deactivate Flow within N days if drift surfaces. Field changes made by Flow during the drift window require a data-fix — agent lists affected fields + fix shape, does NOT generate the fix script.
- Watch post-cutover: per-day record count, average save latency, flow error count from `FlowInterviewLog`.

---

## Output Contract

1. **Summary** — object, PB count (active / inactive), consolidation mode, proposed target flow count, confidence (HIGH/MEDIUM/LOW).
2. **Inventory table** — one row per source PB: name, active, trigger context, criterion node count, action group summary, target flow section, subprocess references.
3. **Target flow design** — element plan per proposed flow. Every element cites source (PB + criterion) and canon (skill/template).
4. **Order-of-execution notes** — per Step 4, flag any criterion that MUST stay after-save.
5. **Subprocess dependency list** — per Step 5; name each referenced subprocess and its migration state.
6. **Unmigratable items** — P0-flagged for Quip / external actions, invoked processes that are out of scope, actions the classification table didn't match.
7. **Parallel-run plan** — Step 7 instantiated.
8. **Rollback plan** — Step 8 instantiated.
9. **Process Observations**:
   - **What was healthy** — narrowly-scoped criterion nodes, PBs already using Invocable Apex rather than multi-step field updates, clean subprocess hierarchies.
   - **What was concerning** — PBs writing to the same field via multiple criterion nodes, PBs calling Apex that themselves call PBs, inactive-but-deployed processes, email-alert actions referencing retired templates.
   - **What was ambiguous** — criterion-node ordering where multiple criteria match; "Evaluate the Next Criteria" semantics that diverge from the documented default.
   - **Suggested follow-up agents** — `workflow-rule-to-flow-migrator` (if the object also has WFRs), `flow-analyzer` (post-cutover), `approval-process-auditor` (Submit-for-Approval targets).
10. **Citations**.

---

## Escalation / Refusal Rules

- Cyclic process invocation (A → B → A) → `REFUSAL_INPUT_AMBIGUOUS`; require the human to break the cycle.
- PB with more than 50 criterion nodes → partial plan for top-15 most-recently-active criteria + `REFUSAL_OVER_SCOPE_LIMIT`; recommend `flow-analyzer` to map first.
- Apex trigger on the same object already performs a conflicting field update → refuse consolidation; route via `apex-refactorer`.
- Invoked subprocess is not on the target object and not in scope → `REFUSAL_OUT_OF_SCOPE`; migrate subprocesses first.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.
- Object is managed-package → `REFUSAL_MANAGED_PACKAGE`.

---

## What This Agent Does NOT Do

- Does not migrate Workflow Rules — delegate to `workflow-rule-to-flow-migrator`.
- Does not activate or deactivate PBs or flows.
- Does not deploy metadata.
- Does not generate data-fix scripts for rollback.
- Does not auto-chain.
