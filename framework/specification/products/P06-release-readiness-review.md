# P06 — Release Readiness Review

**Lifecycle target:** beta target  
**Primary command:** `/review-release-readiness`  
**Product agent:** `release-readiness-reviewer`

## User job

Given a release scope, tell me whether it is ready, what blocks it, what should be tested or sequenced, and what evidence is still missing.

## Personas and modes

- Personas: release-engineer, architect, developer, consultant, security-reviewer
- Modes: fixture, local-project, live-read-only, hybrid, scratch-qa

## Inputs

| Input | Requirement | Meaning |
|---|---|---|
| `release_scope` | required | Manifest, Git diff/range, package directory, or structured change list |
| `project_path` | optional | Salesforce DX project |
| `target_org` | optional | Read-only validation target |
| `risk_tolerance` | optional | Conservative/default/aggressive with explicit policy |

At least one valid evidence input path must exist. Optional project inspection follows explicit path, one unambiguous active workspace, bounded roots, then standalone. The SfSkills repository itself is never assumed to be the target Salesforce project.

## Required evidence

- Versioned release scope

## Optional enrichment

- deployment validation result
- Apex/Flow tests
- code analysis
- dependencies
- permissions
- data migration plan
- rollback/runbook
- environment drift

## Evidence tools

`get_deployment_result`, `get_apex_test_run`, `get_code_analysis_result`, `get_component_dependency_evidence`, `get_org_snapshot_manifest`, `get_flow_test_result`

Tools are product-read-only. QA setup may create scenario evidence only inside disposable scratch orgs under a separate authority.

## Required findings

- hard blockers
- risk-ranked concerns
- test and validation coverage
- deployment ordering
- environment prerequisites
- rollback gaps
- go/no-go/conditional recommendation

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
  -> release-readiness-reviewer
  -> deterministic evidence lint
  -> sf-evidence-reviewer
  -> final envelope
```

Host limitations may require the parent to perform MCP calls and pass normalized evidence to a read-only subagent. The behavior contract remains the same.

## Known-truth scenarios

- `REL-MISSING-DEPENDENCY`
- `REL-TEST-GAP`
- `REL-SECURITY-RISK`
- `REL-DATA-SEQUENCING`
- `REL-DRIFT`
- `REL-ROLLBACK-GAP`

## Quality gates

- Readiness is evidence-specific, not a generic score
- Missing validation cannot produce unconditional go
- Recommendations map to release components
- No deployment execution

## Failure and status behavior

- `refused`: unsafe request, missing mandatory input, or unresolved target ambiguity.
- `partial`: useful findings but missing/stale/truncated/contradictory evidence.
- `failed`: unexpected system/tool failure prevents valid output.
- `completed`: required evidence, deterministic lint, and independent review all pass.

## Known limitations

- Does not approve business readiness or organizational change
- Cannot validate unavailable external systems
- A release can remain conditional despite high technical quality

## Product metrics

- time to first useful finding;
- required-finding recall;
- root-cause rank;
- unsupported material claim rate;
- evidence-reference validity;
- context files/tokens and tool bytes;
- status correctness;
- repeat use and user acceptance.
