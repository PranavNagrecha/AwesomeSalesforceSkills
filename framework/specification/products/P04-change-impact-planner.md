# P04 — Change Impact Planner

**Lifecycle target:** beta target  
**Primary command:** `/plan-metadata-change`  
**Product agent:** `change-impact-planner`

## User job

Before I change or retire Salesforce metadata, identify direct and transitive impact, deployment order, tests, permissions, data implications, and rollback constraints.

## Personas and modes

- Personas: architect, developer, admin, release-engineer, consultant
- Modes: fixture, local-project, live-read-only, hybrid, scratch-qa

## Inputs

| Input | Requirement | Meaning |
|---|---|---|
| `component` | required | Canonical metadata component identity |
| `proposed_change` | required | Typed change such as add/rename/delete/type-change/activate/deactivate |
| `project_path` | optional | Salesforce DX project |
| `target_org` | optional | Read-only org for deployed-state evidence |
| `scope` | optional | Package, application, or explicit roots |

At least one valid evidence input path must exist. Optional project inspection follows explicit path, one unambiguous active workspace, bounded roots, then standalone. The SfSkills repository itself is never assumed to be the target Salesforce project.

## Required evidence

- Component identity and proposed change

## Optional enrichment

- Local references
- org metadata dependencies
- Apex/LWC/Flow/report/permission references
- data usage/count summaries
- package and deployment boundaries

## Evidence tools

`get_component_dependency_evidence`, `describe_salesforce_component`, `get_org_snapshot_manifest`, `get_code_analysis_result`

Tools are product-read-only. QA setup may create scenario evidence only inside disposable scratch orgs under a separate authority.

## Required findings

- direct and transitive dependencies
- runtime/deployment/data/security impacts
- safe sequencing
- test matrix
- rollback/irreversibility
- unknown dynamic references
- change alternatives

Each material finding is a typed claim with support links. Recommendations reference the claims and constraints they address.

## Context plan

1. Load product contract, output schema, authority, and target identity.
2. Load 3–5 core Salesforce knowledge items.
3. Classify observed evidence and add only conditional packs needed for those classes.
4. Target no more than 8 knowledge/reference files; hard stop/overflow at 12.
5. Bound each injected tool page to 32 KiB and preserve continuation metadata.
6. Pass structured handoffs only.
7. Checkpoint at evidence-ready and draft-ready boundaries.

## Agent flow

```text
command/input validation
  -> sf-context-librarian
  -> sf-project-inspector (optional)
  -> sf-org-grounder or fixture loader
  -> change-impact-planner
  -> deterministic evidence lint
  -> sf-evidence-reviewer
  -> final envelope
```

Host limitations may require the parent to perform MCP calls and pass normalized evidence to a read-only subagent. The behavior contract remains the same.

## Known-truth scenarios

- `IMP-FIELD-DELETE`
- `IMP-FIELD-TYPE`
- `IMP-FLOW-ACTIVE`
- `IMP-PERMISSION`
- `IMP-PACKAGE-BOUNDARY`
- `IMP-DYNAMIC-REFERENCE`

## Quality gates

- Direct and inferred dependencies are distinguished
- Destructive/irreversible effects are prominent
- Dynamic references remain unknown unless evidenced
- Plan works in project-only or org-only reduced modes

## Failure and status behavior

- `refused`: unsafe request, missing mandatory input, or unresolved target ambiguity.
- `partial`: useful findings but missing/stale/truncated/contradictory evidence.
- `failed`: unexpected system/tool failure prevents valid output.
- `completed`: required evidence, deterministic lint, and independent review all pass.

## Known limitations

- Does not apply the change
- Cannot guarantee dynamic references absent runtime/log evidence
- Dependency completeness depends on available metadata/tool coverage

## Product metrics

- time to first useful finding;
- required-finding recall;
- root-cause rank;
- unsupported material claim rate;
- evidence-reference validity;
- context files/tokens and tool bytes;
- status correctness;
- repeat use and user acceptance.
