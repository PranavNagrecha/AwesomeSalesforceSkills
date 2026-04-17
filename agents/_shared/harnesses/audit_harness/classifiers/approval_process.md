# Classifier: approval_process

## Purpose

Audit legacy Approval Processes for broken references (inactive approvers, deleted fields, empty queues), anti-patterns (no filter, 10+ steps, always-true entry criteria), concurrent-automation conflicts (final action writes a field an active Flow/Apex trigger also writes), operational debt (stale in-flight requests), and migration fitness (keep / fix / migrate to Orchestrator / re-home to Agentforce / retire). Not for designing new approval processes — this is an audit, not a design exercise.

## Replaces

`approval-process-auditor` (now a deprecation stub pointing at `audit-router --domain approval_process`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `audit_scope` | yes | `org` \| `object:<sObjectName>` \| `process:<DeveloperName>` |
| `include_inactive` | no | default `true` — inactive approvals clutter too |
| `stale_days` | no | default `90` — in-flight requests older than this are flagged |

## Inventory Probe

1. `list_approval_processes(object_name=...)` when scope is object-bound.
2. `tooling_query("SELECT Id, DeveloperName, Name, Type, TableEnumOrId FROM ProcessDefinition")` for org-wide scope.
3. Per process: `tooling_query("SELECT Metadata FROM ProcessDefinition WHERE Id = '<id>'")` — metadata exposes entry criteria, approval steps, initial submitters, final actions.
4. Per process: `tooling_query("SELECT COUNT() FROM ProcessInstance WHERE ProcessDefinitionId = '<id>' AND Status = 'Pending'")` — operational load.
5. For concurrent-automation check: `list_flows_on_object(object)` + probe_apex_references (Wave-2 MCP tool).
6. For queue-member check: `tooling_query("SELECT COUNT() FROM GroupMember WHERE GroupId = '<queue_id>' AND Group.Type = 'Queue'")`.

Inventory columns (beyond id/name/active):
`table_object`, `step_count`, `in_flight_count`, `entry_criteria_summary`, `migration_class` (filled in Step 4: keep / rewrite / migrate / rehome / retire).

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `APPROVAL_INACTIVE_APPROVER` | P0 | Approver is a user who is `IsActive=false` (resolved via hierarchy or direct assignment) | step id + user id + user name | Reassign to active approver or deactivate the process |
| `APPROVAL_EMPTY_QUEUE` | P0 | Queue used as approver has 0 active members | step id + queue developer name + member count | Populate the queue or reassign step |
| `APPROVAL_FIELD_NOT_FOUND` | P0 | Entry/step criteria references a deleted or retired field | process id + step id + missing field API name | Route via `field-impact-analyzer`; halt migration planning |
| `APPROVAL_INACTIVE_WITH_PENDING` | P0 | Process is inactive but has in-flight pending requests | process id + pending count | Reactivate briefly to clear pending OR recall + reject them per policy |
| `APPROVAL_FLOW_CONFLICT` | P0 | Final approval action writes a field also written by an active Flow on the same object | field API name + process id + conflicting flow | Single-owner rule — move one write out |
| `APPROVAL_APEX_CONFLICT` | P0 | Final approval action writes a field also written by an active Apex trigger | field API name + process id + trigger name | Single-owner rule — reconcile ownership |
| `APPROVAL_OUTBOUND_RETIRED` | P0 | Final action includes Outbound Message to a retired RemoteSite or NamedCredential | process id + action name + target | Replace with Platform Event or remove; document upstream |
| `APPROVAL_TEMPLATE_INACTIVE` | P1 | Email template referenced by a final action is inactive or deleted | process id + action + template developer name | Reactivate template or swap in an active equivalent |
| `APPROVAL_MANAGER_NULLABLE` | P1 | Step uses "manager hierarchy" AND submitter's Manager field is routinely null (> 20% sampled) | sample null rate + process id | Switch to role-hierarchy step OR populate Manager via user provisioning |
| `APPROVAL_STALE_INFLIGHT` | P1 | Count of pending ApprovalRequests older than `stale_days` > 0 | process id + count + oldest submit date | Operational debt — recall stale requests or document why they're held |
| `APPROVAL_NO_FILTER` | P1 | Entry criteria is "always" and process fires on every record | process id + filter blank | Add meaningful entry criteria or retire the process |
| `APPROVAL_OWNER_MISMATCH` | P1 | First step's Initial Submitter Role is "owner" but object uses queue ownership | process id + step id + object ownership model | Switch to queue-based submitter OR document the edge case |
| `APPROVAL_DYNAMIC_INACTIVE_RISK` | P1 | Dynamic approver field is a User lookup that may point at an inactive user | field API name + % currently inactive | Add a user-active filter or fall back to role/queue |
| `APPROVAL_TOO_MANY_STEPS` | P2 | Process has > 10 steps | process id + step count | Migration candidate to Flow Orchestrator |
| `APPROVAL_NAME_NONCOMPLIANT` | P2 | Developer name / label doesn't conform to naming conventions | process id + current name | Rename on next deploy window |
| `APPROVAL_SKIP_UNDECIDABLE` | P2 | Step skip logic references a formula that can't be statically evaluated | process id + step id + formula | Simplify skip condition or document the runtime dependency |

### Step-4 migration classification (inventory metadata, feeds Process Observations — not a finding code)

| Signal | `migration_class` |
|---|---|
| Single-step, 1 approver group, clean entry criteria | `keep_as_is` |
| Has P0/P1 findings fixable without reshape | `rewrite_in_place` |
| Multi-step, mixed human + background, cross-object | `migrate_to_orchestrator` — route via `automation-migration-router --source-type approval_process` |
| Deterministic eligibility (e.g. "approve if credit > 700") | `rehome_to_agentforce` — route via `agentforce-builder` |
| Zero submissions in last 180 days OR zero active approvers | `retire` — 30-day observation window recommended |

## Patches

None. Approval-process findings are advisory — mechanical patching of ProcessDefinition metadata is error-prone and the migration path typically changes the target shape anyway (Orchestrator, Agentforce, or retirement). Fixes are captured in `suggested_fix` and routed to the appropriate follow-up agent.

## Mandatory Reads

- `skills/admin/approval-processes`
- `skills/admin/queues-and-public-groups`
- `skills/flow/orchestration-flows`
- `standards/decision-trees/automation-selection.md`
- `templates/admin/naming-conventions.md`

## Escalation / Refusal Rules

- Org has > 200 active Approval Processes and `audit_scope=org` → return top-50 by in-flight count. `REFUSAL_OVER_SCOPE_LIMIT`. Recommend repeated scoped runs per object.
- Process references regulatory / SOX / HIPAA audit fields → audit still runs, but migration recommendations are suppressed. Add a compliance-review-required note. Refuse `retire` / `rehome_to_agentforce` recommendations — `REFUSAL_POLICY_MISMATCH`.
- `audit_scope=process:<name>` and the process doesn't exist → `REFUSAL_INPUT_AMBIGUOUS`.

## What This Classifier Does NOT Do

- Does not recall or reject in-flight approval requests.
- Does not deactivate approval processes.
- Does not migrate processes — recommends `automation-migration-router --source-type approval_process` in `migration_class`.
- Does not redesign approval chains — an audit is not a design exercise.
