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

| `source_type`      | Replaces (now-deleted legacy agent)              | Target shape                      |
|---                 |---                                               |---                                |
| `wf_rule`          | `workflow-rule-to-flow-migrator` *(removed)*     | Record-triggered Flow             |
| `process_builder`  | `process-builder-to-flow-migrator` *(removed)*   | Record-triggered Flow             |
| `approval_process` | `approval-to-flow-orchestrator-migrator` *(removed)* | Flow Orchestrator (conditional)   |
| `auto`             | `workflow-and-pb-migrator` *(removed; union)*    | Dispatched to `wf_rule` then `process_builder` on the same object, merged output |

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
- `skills/flow/flow-loop-element-patterns` — collect-then-DML idiom; the WFR's per-rule action shape often translates to a Loop-with-Update if migrated naively
- `skills/flow/flow-formula-and-expression-patterns` — WFR formulas translate 1:1 to Flow formula resources but NULL-handling and ISPICKVAL semantics differ from WFR
- `skills/flow/flow-record-locking-and-contention` — record-triggered Flow reuses the WFR's parent-update pattern; lock-contention surfaces under bulk
- `skills/flow/flow-runtime-context-and-sharing` — Spring '21 default change shifted record-triggered Flows to System-Without-Sharing; document the shift per migrated rule
- `skills/flow/flow-element-naming-conventions` — every migrated WFR action gets an explicit element name (no `Update_Records_2` auto-names)
- `skills/flow/flow-deployment-and-packaging` — bundle the target Flow + FlowAccessPermission + dependent fields in a single deploy
- `skills/flow/scheduled-flows` — Scheduled Path is the canonical analog for WFR time-dependent actions
- `skills/flow/workflow-rule-to-flow-migration` — domain-specific migration playbook (WFR → Flow)
- `skills/flow/flow-versioning-strategy` — every emitted target Flow ships as v1; activation/deactivation rules during cutover
- `skills/flow/flow-error-monitoring` — org-level error-email-recipient signal recorded as healthy/concerning observation
- `skills/flow/flow-rollback-patterns` — shape of the rollback section (no SOQL/DML), shadow-field tear-down
- `skills/flow/flow-transactional-boundaries` — every emitted target Flow's commit-boundary decision (before-save vs after-save) must cite this skill
- `skills/flow/flow-large-data-volume-patterns` — when the WFR fires on an LDV object (> 100k rows), the migrated Flow needs the LDV guardrails
- `skills/flow/flow-action-framework` — when a WFR's flow-trigger invocable becomes an Apex action element on the target Flow, the Flow–Apex invocable contract applies
- `skills/flow/flow-runtime-error-diagnosis` — symptom-to-cause map cited in the parallel-run validation section
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
- `skills/flow/flow-loop-element-patterns` — PB's "Update Related Records" can balloon into a Loop+Update when migrated; collect-then-DML is mandatory
- `skills/flow/flow-formula-and-expression-patterns` — PB criteria expressions translate to Flow Decision conditions but NULL/ISPICKVAL semantics differ
- `skills/flow/flow-record-locking-and-contention` — PB's serial action execution masked contention that the Flow surfaces; design must decouple
- `skills/flow/flow-runtime-context-and-sharing` — record-triggered Flows default to System-Without-Sharing; document the shift from PB's User Context default per migrated process
- `skills/flow/flow-element-naming-conventions` — replace `myWaitEvent_4` style auto-names from PB conversion with VerbObject names
- `skills/flow/flow-deployment-and-packaging` — bundle target Flow + FlowAccessPermission + referenced subflows in a single deploy
- `skills/flow/subflows-and-reusability`
- `skills/flow/scheduled-flows` — Scheduled Path is the canonical analog for PB time-dependent groups
- `skills/flow/process-builder-to-flow-migration` — domain-specific migration playbook (PB → Flow)
- `skills/flow/flow-versioning-strategy` — versioning + activation rules for the emitted target Flow
- `skills/flow/flow-error-monitoring` — org-level error-email-recipient signal recorded as healthy/concerning observation
- `skills/flow/flow-rollback-patterns` — shape of the rollback section, shadow-field tear-down
- `skills/flow/flow-transactional-boundaries` — every emitted target Flow's commit-boundary decision (before-save vs after-save) must cite this skill; PB's serial behavior masked transaction concerns the Flow makes explicit
- `skills/flow/flow-large-data-volume-patterns` — when the PB fires on an LDV object, the migrated Flow needs LDV guardrails
- `skills/flow/flow-action-framework` — PB Apex Action / Quick Action / Launch-a-Flow → Flow Apex action / invocable / Subflow contract
- `skills/flow/flow-decision-element-patterns` — PB criteria nodes translate to Decision elements; default outcome + null-safe branching rules apply
- `skills/flow/flow-runtime-error-diagnosis` — symptom-to-cause map cited in the parallel-run validation section
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
- `skills/flow/screen-flows` — interactive approval steps map to Screen Flows on the orchestration stage
- `skills/flow/flow-screen-input-validation-patterns` — every approval-step Screen Flow validates approver inputs before completing the work item
- `skills/flow/flow-screen-lwc-components` — when a stage's approval UI requires an LWC (signature capture, custom matrix), the screen-flow contract applies
- `skills/flow/subflows-and-reusability` — every stage step is a subflow per `Subflow_Pattern.md`
- `skills/flow/pause-elements-and-wait-events` — work-item waiting + recall semantics
- `skills/flow/fault-handling`
- `skills/flow/flow-runtime-context-and-sharing` — orchestration runs as the work-item assignee; per-stage run-mode decision required for `$User`/`$Permission` resolution
- `skills/flow/flow-element-naming-conventions` — Stage_LegalReview > S1; Stage / Step / Subflow naming policy applied to every emitted orchestration
- `skills/flow/flow-deployment-and-packaging` — orchestration + dependent subflows + FlowAccessPermission for each persona must deploy together
- `skills/flow/flow-versioning-strategy` — orchestrations are versioned; in-flight instances during cutover
- `skills/flow/flow-error-monitoring` — org-level error-email-recipient + monitoring assertions
- `skills/flow/flow-transactional-boundaries` — orchestration commits at stage boundaries; recall behavior depends on which stages have committed
- `skills/flow/flow-rollback-patterns` — Rollback Records inside a stage subflow only undoes that subflow's DML; previous stages' commits are NOT reverted (cite when designing the rejection branch)
- `skills/flow/flow-runtime-error-diagnosis` — symptom-to-cause map cited in parallel-run validation + canary observations
- `skills/flow/flow-decision-element-patterns` — approval routing translates to Decision elements + transition conditions
- `skills/flow/flow-formula-and-expression-patterns` — approver-formula expressions translate to Flow formula resources, but NULL semantics differ
- `skills/admin/approval-processes`
- `skills/admin/queues-and-public-groups` — queue-as-assignee preflight (active member count) before activation
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
