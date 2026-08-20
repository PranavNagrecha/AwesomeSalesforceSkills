# P12 — Multi-Org Drift Analysis

**Lifecycle target:** beta portfolio  
**Primary command:** `/compare-orgs`  
**Product agent:** `multi-org-drift-analyzer`

## User job

Compare two explicit Salesforce org snapshots and distinguish expected environmental differences from dangerous deployment or configuration drift.

## Personas and modes

- Personas: release-engineer, architect, consultant, admin, developer
- Modes: fixture, live-read-only, hybrid, scratch-qa

## Inputs

| Input | Requirement | Meaning |
|---|---|---|
| `left_org_or_snapshot` | required | Explicit org alias or captured snapshot |
| `right_org_or_snapshot` | required | Explicit org alias or captured snapshot |
| `scope` | optional | Metadata types, packages, settings, permissions, or components |
| `difference_policy` | optional | Expected-difference rules |

At least one valid evidence input path must exist. Optional project inspection follows explicit path, one unambiguous active workspace, bounded roots, then standalone. The SfSkills repository itself is never assumed to be the target Salesforce project.

## Required evidence

- Two explicit identities/snapshots and capture times

## Optional enrichment

- project source
- package/version manifests
- expected environment policy
- deployment history

## Evidence tools

`get_org_snapshot_manifest`, `compare_org_snapshots`, `describe_salesforce_component`, `get_component_dependency_evidence`

Tools are product-read-only. QA setup may create scenario evidence only inside disposable scratch orgs under a separate authority.

## Required findings

- added/removed/changed components
- expected differences
- dangerous drift
- dependency consequences
- promotion/reconciliation recommendations
- snapshot limitations

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
  -> multi-org-drift-analyzer
  -> deterministic evidence lint
  -> sf-evidence-reviewer
  -> final envelope
```

Host limitations may require the parent to perform MCP calls and pass normalized evidence to a read-only subagent. The behavior contract remains the same.

## Known-truth scenarios

- `DRIFT-FIELD`
- `DRIFT-FLOW-VERSION`
- `DRIFT-PERMISSION`
- `DRIFT-SETTING`
- `DRIFT-PACKAGE`
- `DRIFT-EXPECTED`

## Quality gates

- Never compares implicit/default orgs
- Snapshot versions and scope are visible
- Expected policy is separate from observed diff
- No synchronization or deployment

## Failure and status behavior

- `refused`: unsafe request, missing mandatory input, or unresolved target ambiguity.
- `partial`: useful findings but missing/stale/truncated/contradictory evidence.
- `failed`: unexpected system/tool failure prevents valid output.
- `completed`: required evidence, deterministic lint, and independent review all pass.

## Known limitations

- Does not mutate either org
- Completeness depends on snapshot coverage
- Some secrets/settings cannot be compared directly

## Product metrics

- time to first useful finding;
- required-finding recall;
- root-cause rank;
- unsupported material claim rate;
- evidence-reference validity;
- context files/tokens and tool bytes;
- status correctness;
- repeat use and user acceptance.
