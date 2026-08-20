# P05 — Automation Transaction Profiler

**Lifecycle target:** beta target  
**Primary command:** `/profile-automation`  
**Product agent:** `automation-transaction-profiler`

## User job

Show what Salesforce automation executes for an object operation, in what order, where recursion/DML/limit risk exists, and which automation should be consolidated.

## Personas and modes

- Personas: developer, admin, architect, consultant
- Modes: fixture, local-project, live-read-only, hybrid, scratch-qa

## Inputs

| Input | Requirement | Meaning |
|---|---|---|
| `object` | required | Object API name |
| `operation` | required | insert/update/delete/undelete or supported business event |
| `scenario` | optional | Changed fields, entry conditions, user context, volume |
| `project_path` | optional | Local project |
| `target_org` | optional | Read-only org |

At least one valid evidence input path must exist. Optional project inspection follows explicit path, one unambiguous active workspace, bounded roots, then standalone. The SfSkills repository itself is never assumed to be the target Salesforce project.

## Required evidence

- Object and operation

## Optional enrichment

- Flow inventory and versions
- triggers/handlers
- validation rules
- workflow/process legacy automation
- rollups and cross-object updates
- async branches/events
- debug/test evidence

## Evidence tools

`get_automation_inventory`, `get_component_dependency_evidence`, `describe_salesforce_component`, `get_apex_test_run`

Tools are product-read-only. QA setup may create scenario evidence only inside disposable scratch orgs under a separate authority.

## Required findings

- ordered transaction graph
- conditional branches
- recursion and re-entry paths
- DML/query/callout/async amplification
- conflicts and duplicate ownership
- hotspots and consolidation options
- verification scenarios

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
  -> automation-transaction-profiler
  -> deterministic evidence lint
  -> sf-evidence-reviewer
  -> final envelope
```

Host limitations may require the parent to perform MCP calls and pass normalized evidence to a read-only subagent. The behavior contract remains the same.

## Known-truth scenarios

- `AUT-FLOW-TRIGGER-ORDER`
- `AUT-RECURSION`
- `AUT-DML-AMPLIFICATION`
- `AUT-ASYNC-BRANCH`
- `AUT-ROLLUP-REENTRY`
- `AUT-LEGACY-CONFLICT`

## Quality gates

- Does not pretend static inventory proves runtime branch execution
- Order follows current Salesforce semantics
- Volume assumptions are explicit
- Graph remains bounded and useful

## Failure and status behavior

- `refused`: unsafe request, missing mandatory input, or unresolved target ambiguity.
- `partial`: useful findings but missing/stale/truncated/contradictory evidence.
- `failed`: unexpected system/tool failure prevents valid output.
- `completed`: required evidence, deterministic lint, and independent review all pass.

## Known limitations

- Does not execute transactions in customer orgs
- Runtime-only managed-package behavior may remain opaque
- Exact governor consumption requires representative execution evidence

## Product metrics

- time to first useful finding;
- required-finding recall;
- root-cause rank;
- unsupported material claim rate;
- evidence-reference validity;
- context files/tokens and tool bytes;
- status correctness;
- repeat use and user acceptance.
