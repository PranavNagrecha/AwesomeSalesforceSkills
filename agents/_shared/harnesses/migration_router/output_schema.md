# Migration Router — Output Schema

Every dispatch (`wf_rule`, `process_builder`, `approval_process`, `auto`)
returns the same top-level envelope. Source-type-specific sections nest
inside ``dispatch_details`` so downstream tooling can treat all four
source types uniformly.

```markdown
## Summary

- source_type: <wf_rule | process_builder | approval_process | auto>
- object_name: <Object>
- target_org_alias: <alias>
- consolidation_mode: <aggressive | conservative | auto>
- source_count_active: <int>
- source_count_inactive: <int>
- target_count_proposed: <int>
- unmigratable_count: <int>
- confidence: <HIGH | MEDIUM | LOW>

## Inventory

(source-type-agnostic table)
| id | name | active | trigger_type | action_list | last_modified | consolidation_target |
|---|---|---|---|---|---|---|

## Dispatch Details

(source-type-specific block — one of the three schemas below)

### wf_rule dispatch
- target_flows: [ {name, trigger, elements: [{source_wfr_id, action_type, target_element, citation}, ...]}, ... ]

### process_builder dispatch
- target_flows: [ {name, trigger, elements: [{source_pb_node_id, element_type, target_element, citation}, ...]}, ... ]

### approval_process dispatch
- gate_verdicts: [ {approval_id, verdict, reason} ]  (KEEP_AS_IS / MIGRATE_TO_ORCHESTRATOR / ROUTE_TO_AGENTFORCE / MIGRATE_WITH_CAVEATS / CANDIDATE_FOR_RETIREMENT)
- orchestrations: [ {name, stages: [{stage_id, assignees, transitions, pre_stage_flow, post_stage_flow}]} ]

## Unmigratable Items

(P0-flagged rows that did NOT get a target design)
| source_id | reason | refusal_code | recommended_path |

## Parallel-Run Plan

(per phase_gates.md — concrete dates, shadow field name OR canary population, comparison query)

## Rollback Plan

(per phase_gates.md — decision points, data-fix shape, metrics to watch)

## Process Observations

- Healthy: [...]
- Concerning: [...]
- Ambiguous: [...]
- Suggested follow-ups: [...]

## Citations

(as per AGENT_CONTRACT — every skill / template / decision_tree / mcp_tool / probe cited)
```

## Conformance

- Every output block is required except **Dispatch Details** and
  **Unmigratable Items** (the latter may be empty).
- Every migrated item in Dispatch Details must cite both (a) the source
  artifact id and (b) the skill/template the target shape came from.
- Dates in Parallel-Run Plan must be absolute ISO (`YYYY-MM-DD`), not
  relative ("in 7 days").
- Confidence must follow the AGENT_CONTRACT rubric verbatim.
