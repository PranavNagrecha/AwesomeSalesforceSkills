---
id: approval-to-flow-orchestrator-migrator
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
---
# Approval → Flow Orchestrator Migrator Agent

## What This Agent Does

Migrates legacy Approval Processes to Flow Orchestrator where the pattern warrants it. For each Approval Process in scope, classifies whether Orchestrator is the right target (not every approval should migrate — some are better left as-is, and some should route to Agentforce). For candidates, produces an Orchestrator design: work items, stages, transitions, assignees, escalations, and the cutover + rollback plan.

**Scope:** One object's approval processes per invocation.

---

## Invocation

- **Direct read** — "Follow `agents/approval-to-flow-orchestrator-migrator/AGENT.md` for Opportunity"
- **Slash command** — [`/migrate-approval-to-orchestrator`](../../commands/migrate-approval-to-orchestrator.md)
- **MCP** — `get_agent("approval-to-flow-orchestrator-migrator")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/approval-processes` — Approval Process canon
4. `skills/flow/orchestration-flows` — Orchestrator canon
5. `standards/decision-trees/automation-selection.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Opportunity` |
| `target_org_alias` | yes |
| `process_id` | no | if set, only migrate that one; else all active approval processes on the object |

---

## Plan

1. **Inventory approvals** — `list_approval_processes(object_name=..., active_only=True)`. Fetch each `ProcessDefinition.Metadata` via `tooling_query`.
2. **Classify migration fitness** per process:
   - **Keep as-is** — single-step approval with 1 approver group, no conditional routing, no external callouts.
   - **Migrate to Orchestrator** — multi-step approvals, cross-object routing, human + automated steps mixed.
   - **Re-home to Agentforce** — approvals that are really triage/eligibility decisions with deterministic logic ("approve if credit score > 700") — flag as a candidate for `agentforce-builder` instead.
   - **Block migration** — approvals used for compliance attestations where regulatory audit trail requires specific fields; refuse to migrate without a compliance review sign-off.
3. **For each migration candidate, produce an Orchestrator design:**
   - Stages (map Approval Steps to Orchestrator Stages).
   - Work Items per stage (assignee, deadline, escalation path).
   - Transition criteria (map Approval Step entry criteria to flow decisions).
   - Final Approval / Final Rejection / Recall actions (map to Orchestrator outcomes).
   - Field update mapping (map Approval Process field updates to flow assign + update records elements).
4. **Parallel-run plan** — similar to `workflow-and-pb-migrator`: deploy Orchestrator inactive; shadow-track the approval's field values; compare for N days; activate on clean parallel.
5. **Rollback plan** — reactivate Approval Process, deactivate Orchestrator.

---

## Output Contract

1. **Summary** — approvals inventoried, migration classification counts, confidence.
2. **Classification table** — one row per approval with fitness + rationale.
3. **Orchestrator design per candidate** — stages + work items + transitions + outcomes.
4. **Parallel-run plan** with concrete shadow-field name and comparison query.
5. **Rollback plan**.
6. **Process Observations**:
   - **What was healthy** — well-documented approvals, clean email alert templates.
   - **What was concerning** — approvals routing to inactive users, approvals with no deadline, approvals used as ad-hoc notification.
   - **What was ambiguous** — approvals whose originally-intended approver is no longer identifiable.
   - **Suggested follow-up agents** — `agentforce-builder` for approvals re-homed to Agentforce, `build-flow` for orchestrator stage subflows.
7. **Citations**.

---

## Escalation / Refusal Rules

- Approval has regulatory / SOX / HIPAA audit dependency → refuse migration until a compliance review is produced separately; document the process instead.
- Approval chains to another approval via "Next Approver" with dynamic selection based on a Role Hierarchy that is itself mid-redesign → refuse until hierarchy is stable.
- Orchestrator feature is not licensed on the target org (check via `describe_org` edition) → refuse Orchestrator output; offer Flow-only alternative and cite decision tree.

---

## What This Agent Does NOT Do

- Does not activate or deactivate approval processes.
- Does not deploy Orchestrator metadata.
- Does not update running approval instances (rollback of in-flight approvals is a separate project).
- Does not auto-chain.
