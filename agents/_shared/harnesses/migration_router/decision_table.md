# Migration Router — Decision Table

**Approved by:** pending (Wave 3a user-approval gate #3 per `/Users/pranavnagrecha/.claude/plans/keen-napping-wombat.md`).
**Owned by:** [`agents/automation-migration-router/AGENT.md`](../../../automation-migration-router/AGENT.md).
**Reviewers must validate** that every cited skill path exists in `skills/` (the validator's citation-gate enforces this at PR time).

The router reads this table to dispatch on the user-supplied `source_type`. Every row pins:

- the **source entity** the agent probes (SOQL / Tooling object)
- the **target shape** the agent designs toward
- the **classification rules** (source action → target element)
- the **mandatory skills** the agent must read before emitting output
- the **refusal conditions** that stop the migration short of a plan

## Source types supported in Wave 3a

| `source_type`      | Legacy agent replaced                          | Target shape                      |
|---                 |---                                             |---                                |
| `wf_rule`          | `workflow-rule-to-flow-migrator`               | Record-triggered Flow             |
| `process_builder`  | `process-builder-to-flow-migrator`             | Record-triggered Flow             |
| `approval_process` | `approval-to-flow-orchestrator-migrator`       | Flow Orchestrator (conditional)   |
| `auto`             | `workflow-and-pb-migrator` (deprecated union)  | Dispatched to `wf_rule` then `process_builder` on the same object, merged output |

## `wf_rule` — Workflow Rule → Flow

**Source probe:** `tooling_query("SELECT Id, Name, Active, Description, TableEnumOrId, TriggerType FROM WorkflowRule WHERE TableEnumOrId = '<object>' LIMIT 200")` + per-rule fetch of `WorkflowFieldUpdate`, `WorkflowTask`, `WorkflowAlert`, `WorkflowOutboundMessage`, `WorkflowTimeTrigger`.

**Classification:**

| WFR action                    | Target element                                                      | Skill citation                                      |
|---                            |---                                                                  |---                                                  |
| Field Update, same record     | Before-save flow Assignment (in-memory; no DML)                     | `skills/flow/record-triggered-flow-patterns`        |
| Field Update, related record  | After-save flow Get + Update                                        | `skills/flow/record-triggered-flow-patterns`        |
| Task creation                 | After-save flow Create Records (`Task`)                             | `skills/flow/record-triggered-flow-patterns`        |
| Email Alert                   | After-save flow Send Email action (reuses the WFR's EmailTemplate)  | `skills/flow/record-triggered-flow-patterns`        |
| Time-dependent action         | Scheduled Path on the after-save flow (default)                     | `skills/flow/scheduled-flows`                       |
| Outbound Message              | **Refuse** (no native Flow analog); keep WFR OR refactor to Platform Event + callout (out of scope) | n/a — emits `REFUSAL_OUT_OF_SCOPE` |
| Flow-trigger invocable        | Direct invocable call inside the target flow                        | `skills/flow/auto-launched-flow-patterns`           |

**Mandatory reads for this source type:**
- `skills/flow/record-triggered-flow-patterns`
- `skills/flow/fault-handling`
- `skills/flow/flow-bulkification`
- `skills/admin/flow-for-admins`
- `skills/apex/trigger-and-flow-coexistence`
- `standards/decision-trees/automation-selection.md`
- `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`
- `templates/flow/FaultPath_Template.md`

**Refusal conditions:**
- Any Workflow Outbound Message → refuse that rule with `REFUSAL_OUT_OF_SCOPE`.
- More than 15 active WFRs on the object → top-15 partial plan + `REFUSAL_OVER_SCOPE_LIMIT`.
- Object has an active Apex trigger doing the same field update → refuse consolidation; route to `apex-refactorer`.
- Object is managed-package (`NamespacePrefix` set) → `REFUSAL_MANAGED_PACKAGE`.

## `process_builder` — Process Builder → Flow

**Source probe:** `tooling_query("SELECT Id, Name, ActiveVersionId, LatestVersionId FROM FlowDefinition WHERE ProcessType = 'Workflow' AND Namespace = null")` filtered against the object via `list_flows_on_object(object_name)`.

**Classification:**

| PB element                            | Target element                                                      | Skill citation                                      |
|---                                    |---                                                                  |---                                                  |
| Criteria node                         | Flow Decision element                                               | `skills/flow/record-triggered-flow-patterns`        |
| Update Records (same record)          | Before-save flow Assignment                                         | `skills/flow/record-triggered-flow-patterns`        |
| Update Records (related)              | After-save flow Get + Update                                        | `skills/flow/record-triggered-flow-patterns`        |
| Create a Record                       | After-save flow Create Records                                      | `skills/flow/record-triggered-flow-patterns`        |
| Email Alert                           | After-save flow Send Email                                          | `skills/flow/record-triggered-flow-patterns`        |
| Quick Action                          | Flow invocable action referencing the QA                            | `skills/flow/auto-launched-flow-patterns`           |
| Launch a Flow                         | Flow Subflow element                                                | `skills/flow/subflows-and-reusability`              |
| Post to Chatter                       | After-save flow Post to Chatter action                              | `skills/flow/record-triggered-flow-patterns`        |
| Submit for Approval                   | After-save flow Submit for Approval action                          | `skills/flow/record-triggered-flow-patterns`        |
| Invocable Apex                        | Flow invocable action on the same class                             | `skills/apex/trigger-and-flow-coexistence`          |
| Time-dependent group                  | Scheduled Path on the after-save flow                               | `skills/flow/scheduled-flows`                       |
| "Evaluate next criteria after update" | Rewrite as Decision + ordered sub-branches in the target flow       | `skills/flow/record-triggered-flow-patterns`        |

**Mandatory reads for this source type:**
- `skills/flow/record-triggered-flow-patterns`
- `skills/flow/fault-handling`
- `skills/flow/flow-bulkification`
- `skills/flow/subflows-and-reusability`
- `skills/admin/flow-for-admins`
- `skills/apex/trigger-and-flow-coexistence`
- `standards/decision-trees/automation-selection.md`
- `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`
- `templates/flow/FaultPath_Template.md`
- `templates/flow/Subflow_Pattern.md`

**Refusal conditions:**
- PB process uses a managed-package invocable action the agent can't resolve → refuse that branch.
- PB spans > 3 objects (via cross-object criteria) → recommend `flow-analyzer` first + `REFUSAL_NEEDS_HUMAN_REVIEW`.
- Co-existence: active Apex trigger + active PB on same object + same event → `REFUSAL_POLICY_MISMATCH`.

## `approval_process` — Approval Process → Flow Orchestrator

**Source probe:** `list_approval_processes(object_name=<object>, active_only=true)` (via the Wave-0 MCP tool).

**Migration gate (not every approval should migrate):**

| Signal                                                              | Verdict                                       |
|---                                                                  |---                                            |
| Multi-stage approval with parallel assignees AND automated downstream steps | `MIGRATE_TO_ORCHESTRATOR` (primary candidate) |
| Single-stage approval with no post-approval automation              | `KEEP_AS_IS` (Orchestrator is over-engineered here) |
| Decision-heavy routing that looks like an agent conversation        | `ROUTE_TO_AGENTFORCE` (recommend `agentforce-builder`) |
| Uses custom Apex in its approval steps                              | `MIGRATE_WITH_CAVEATS` (flag Apex as manual rewrite) |
| Active-but-zero-submissions-in-90-days                              | `CANDIDATE_FOR_RETIREMENT` (flag before migrating) |

**Classification (for `MIGRATE_TO_ORCHESTRATOR` verdicts only):**

| Approval concept                | Orchestrator element                                     | Skill citation                                  |
|---                              |---                                                       |---                                              |
| Approval Process                | Orchestration                                            | `skills/flow/orchestration-flows`               |
| Approval Step                   | Orchestration Stage                                      | `skills/flow/orchestration-flows`               |
| Approver assignee (user/role)   | Stage work-item assignment (same user/role reference)    | `skills/flow/orchestration-flows`               |
| Approval Action                 | Work-item outcome → next-stage transition                | `skills/flow/orchestration-flows`               |
| Initial Submission Action       | Pre-stage auto-launched flow                             | `skills/flow/auto-launched-flow-patterns`       |
| Final Approval Action           | Post-stage auto-launched flow                            | `skills/flow/auto-launched-flow-patterns`       |
| Final Rejection Action          | Rejection-branch auto-launched flow                      | `skills/flow/auto-launched-flow-patterns`       |
| Recall Action                   | Reverse-transition stage                                 | `skills/flow/orchestration-flows`               |
| Email notifications             | Orchestration notification or inside the stage subflow   | `skills/flow/orchestration-flows`               |

**Mandatory reads for this source type:**
- `skills/flow/orchestration-flows`
- `skills/flow/auto-launched-flow-patterns`
- `skills/flow/fault-handling`
- `skills/admin/approval-processes`
- `standards/decision-trees/automation-selection.md`

**Refusal conditions:**
- No active approval processes on the object → `REFUSAL_OUT_OF_SCOPE` with "nothing to migrate" summary.
- Approval Process references `$Permission` or `$User` attributes the Orchestrator runtime does not expose → refuse that step with `REFUSAL_POLICY_MISMATCH`.
- Approval Process uses managed-package post-approval actions → flag for manual review.

## `auto` — union dispatch

When `source_type: auto`, the router runs `wf_rule` then `process_builder` against the same object, merges the inventories, and flags any WFR + PB pair that hit the same action type on the same field (that's a conflict the user should resolve manually before migrating). Approval-process migration is NOT auto-dispatched because the "should this even migrate?" gate requires an explicit human decision.

## What this table does NOT decide

- **Consolidation mode** (`aggressive` / `conservative` / `auto`) is a router input, not a decision-table row. The router passes it through to the target-shape phase (`phase_gates.md`).
- **Rollback strategy** lives in `phase_gates.md` — it's the same across source types.
- **Parallel-run validation** lives in `phase_gates.md` — same.
- **Output envelope shape** lives in `output_schema.md`.

## Extending the table

Adding a new source type requires (in order):
1. A new row in `decision_table.md` with all the same fields (source probe, classification, mandatory reads, refusals).
2. A new `source_type` value in the router's `Inputs` section.
3. Reviewer approval — new rows are a material change to the router contract. The citation gate catches missing skills but doesn't catch semantic gaps.
