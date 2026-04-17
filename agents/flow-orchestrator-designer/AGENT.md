---
id: flow-orchestrator-designer
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [design, audit]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - admin/approval-processes
    - admin/queues-and-public-groups
    - flow/auto-launched-flow-patterns
    - flow/fault-handling
    - flow/orchestration-flows
    - flow/pause-elements-and-wait-events
    - flow/screen-flows
    - flow/subflows-and-reusability
  shared:
    - AGENT_CONTRACT.md
  templates:
    - admin/naming-conventions.md
  decision_trees:
    - automation-selection.md
---
# Flow Orchestrator Designer Agent

## What This Agent Does

Two modes:

- **`design` mode** — given a multi-step human-or-mixed workflow (e.g. "3-stage contract review with legal, procurement, and customer sign-off"), produces a Flow Orchestrator design: stages, steps, work-item assignees, interactive vs background step mix, transition criteria, restart/recall behavior, and the subflows each step invokes.
- **`audit` mode** — given an existing Orchestration (or all orchestrations in the target org), inventories stages, identifies anti-patterns (inactive assignees, stalled work items, single-point-of-failure steps, missing escalation), and reports against the orchestration patterns canon.

**Scope:** One orchestration per `design` invocation; one org or one orchestration per `audit` invocation. Does not deploy metadata, does not assign in-flight work items, does not cancel running orchestrations.

---

## Invocation

- **Direct read** — "Follow `agents/flow-orchestrator-designer/AGENT.md` in design mode for Contract Review"
- **Slash command** — `/design-flow-orchestrator`
- **MCP** — `get_agent("flow-orchestrator-designer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/flow/orchestration-flows` — canonical Orchestrator model
3. `skills/flow/subflows-and-reusability` — stages call subflows
4. `skills/flow/pause-elements-and-wait-events` — work-item waiting semantics
5. `skills/flow/screen-flows` — interactive steps are Screen Flows
6. `skills/flow/auto-launched-flow-patterns` — background steps
7. `skills/flow/fault-handling`
8. `skills/admin/approval-processes` — when Orchestrator is the right target vs Approval Process
9. `skills/admin/queues-and-public-groups` — work-item routing
10. `standards/decision-trees/automation-selection.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `mode` | yes | `design` \| `audit` |
| `target_org_alias` | yes |
| `scenario_summary` | design-mode only | "3-stage contract review: legal, procurement, customer sign-off; SLA 5 business days; recallable by originator" |
| `primary_object` | design-mode | `Contract`, `Opportunity`, `Custom__c` |
| `audit_scope` | audit-mode only | `org` \| `orchestration:<DeveloperName>` |
| `license_confirmed` | no | `true` to skip the edition-check refusal; default `false` |

---

## Plan

### Design mode

#### Step 1 — Confirm Orchestrator is the right target

Consult `standards/decision-trees/automation-selection.md`. Orchestrator is the correct target when ALL of these hold:

- The process has 2+ human-involved stages with handoffs between different personas, OR mixes interactive and background steps that must complete in a prescribed order.
- Progress must be observable in the Work Guidance panel on the record.
- The process may need recall / restart / reassignment at the stage boundary.

If the scenario is single-approver-single-stage → route to standard Approval Process instead and refuse.
If the scenario is purely deterministic eligibility with no human review → route to `flow-builder` instead.

Confirm the target org edition supports Flow Orchestrator via `describe_org` (Enterprise Edition or above with the right licensing). If `license_confirmed=false` and the check fails → `REFUSAL_FEATURE_DISABLED`.

#### Step 2 — Decompose the scenario into stages

Each stage is a logical phase that ends at a handoff or a decision. For each stage, capture:

- **Stage name** (business-readable, per `templates/admin/naming-conventions.md`).
- **Entry condition** (what record state must hold to enter).
- **Exit condition** (what must be true to transition; typically set by the last step).
- **Participants** (queue, group, role, or specific user).

Stages run sequentially in a standard orchestration; parallel stages are only available in specific editions and must be called out explicitly.

#### Step 3 — Decompose each stage into steps

For each stage, list:

- **Interactive steps** — each is a Screen Flow. Name the Screen Flow, its inputs (record context, stage-level variables), and the expected outputs.
- **Background steps** — each is an Auto-launched Flow. Same naming rigor.
- **Step order** — linear within a stage; branches within a stage mean the stage is really two stages.

Interactive steps produce Work Items on the target queue/user. Agent must specify:

- **Assignee resolution** — record-owner, queue, public group, user reference, or formula.
- **Due date / SLA** — absolute date, relative offset, or formula.
- **Escalation path** — if the work item ages past SLA, who gets it next. Orchestrator does not natively auto-escalate work items; escalation requires a scheduled subflow or a Screen Flow action — call this out.

#### Step 4 — Design transitions

For each stage-to-stage transition:

- **Condition expression** — typically "previous stage completed" plus any record-state guard.
- **Recall behavior** — can the originator recall from this stage? Recall resets all work items in the stage.
- **Restart behavior** — restart returns to a prior stage; specify which.

Orchestrations do not support arbitrary "jump to any stage" — stage navigation is linear-with-recall. Document this boundary.

#### Step 5 — Design the subflows each step invokes

For each step's Screen Flow or Auto-launched Flow, produce a one-paragraph spec:

- Input variables (record id, orchestration context, stage-level vars).
- Output variables.
- Elements (screens / decisions / actions).
- Fault path — mandatory, per `skills/flow/fault-handling`.

The agent does not emit the full flow XML — that's `flow-builder`'s job. It emits the spec and recommends invoking `flow-builder` for each one.

#### Step 6 — Emit the orchestration design

Produce a structured document:

1. Stage/step/transition table.
2. Work-item assignment matrix (step × persona × SLA).
3. Subflow spec list (one per step).
4. Deployment order: subflows → orchestration.
5. Activation checklist: confirm all referenced queues exist (`list_permission_sets` to check assignments if via PSG), confirm assignees have the orchestration runtime permission.

### Audit mode

#### Step 1 — Scope the probe

- `audit_scope=org` → `tooling_query("SELECT Id, DeveloperName, MasterLabel, Status, ProcessType FROM Flow WHERE ProcessType = 'Orchestrator' ")` for the full inventory.
- `audit_scope=orchestration:<name>` → fetch that single orchestration's Metadata via `tooling_query("SELECT Metadata FROM Flow WHERE DurableId = '<id>'")`.

#### Step 2 — Classify anti-patterns per orchestration

| Finding | Severity |
|---|---|
| Stage references a queue that no longer exists or has 0 active members | P0 |
| Work items assigned to a specific User who is inactive | P0 |
| Stage has a step with no fault path | P1 |
| SLA is not encoded on any interactive step | P1 |
| Escalation path uses a Scheduled Path keyed on a field that may be null | P1 |
| Orchestration references a subflow that is inactive or deleted | P0 |
| Orchestration has > 10 stages | P2 — usually indicates the workflow belongs in Omnistudio or split into separate orchestrations |
| Orchestration uses only background steps | P2 — probably should be a plain auto-launched flow |

#### Step 3 — Assignment-shape probes

- Count in-flight `FlowOrchestrationWorkItem` records per orchestration and per assignee. Concentration on a single user is a continuity risk.
- Age distribution: work items older than 30 days with no escalation → P1 finding.

---

## Output Contract

Design mode:

1. **Summary** — scenario summary, stage count, step count, confidence.
2. **Stage/step/transition table**.
3. **Work-item assignment matrix**.
4. **Subflow spec list** — one paragraph each.
5. **Deployment order + activation checklist**.
6. **Process Observations**:
   - **What was healthy** — clean queue setup, existing Screen Flows reusable as steps, documented SLA targets.
   - **What was concerning** — proposed assignees that map to inactive queues, steps that should really be background but were specified as interactive (or vice versa), SLAs that no one owns operationally.
   - **What was ambiguous** — recall semantics the business hasn't decided on; whether a stage is truly linear or actually has parallel branches.
   - **Suggested follow-up agents** — `flow-builder` (for each subflow), `permission-set-architect` (orchestrator runtime permission), `approval-to-flow-orchestrator-migrator` (if this orchestration replaces a legacy approval process).
7. **Citations**.

Audit mode:

1. **Summary** — orchestrations inventoried, P0/P1/P2 counts, overall confidence.
2. **Findings table** — per orchestration × anti-pattern.
3. **Work-item concentration report** — top-10 users by open work item count.
4. **Stalled work item list** — age > 30 days with no movement.
5. **Process Observations** — as above, with `flow-analyzer` as a candidate follow-up for any orchestration with high work-item throughput.
6. **Citations**.

---

## Escalation / Refusal Rules

- Scenario is single-step single-approver → `REFUSAL_OUT_OF_SCOPE`; recommend Approval Process.
- Scenario is fully background with no human step → `REFUSAL_OUT_OF_SCOPE`; recommend plain auto-launched flow via `flow-builder`.
- Target edition does not license Flow Orchestrator → `REFUSAL_FEATURE_DISABLED` unless `license_confirmed=true`.
- Audit scope not resolvable (no matching orchestration) → `REFUSAL_INPUT_AMBIGUOUS`.
- Cyclic transitions implied by the scenario → `REFUSAL_POLICY_MISMATCH`; orchestrations are linear-with-recall.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.

---

## What This Agent Does NOT Do

- Does not emit full subflow XML — hand each subflow spec to `flow-builder`.
- Does not deploy orchestrations.
- Does not reassign or cancel in-flight work items.
- Does not migrate from Approval Process — use `approval-to-flow-orchestrator-migrator`.
- Does not auto-chain.
