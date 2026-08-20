# P09 — Data Migration Reconciliation

**Lifecycle target:** beta portfolio  
**Primary command:** `/reconcile-data-load`  
**Product agent:** `data-migration-reconciler`

## User job

Explain whether a Salesforce data migration reconciled, where records or relationships were lost/changed, and which deterministic checks should be performed next.

## Personas and modes

- Personas: data-engineer, admin, consultant, architect, release-engineer
- Modes: fixture, local-project, live-read-only, hybrid, scratch-qa

## Inputs

| Input | Requirement | Meaning |
|---|---|---|
| `migration_manifest` | required | Source/transform/load definitions and expected counts |
| `result_files` | required | Load success/error/reject outputs |
| `target_org` | optional | Read-only count/sample queries |
| `mapping_file` | optional | Field/object mapping |

At least one valid evidence input path must exist. Optional project inspection follows explicit path, one unambiguous active workspace, bounded roots, then standalone. The SfSkills repository itself is never assumed to be the target Salesforce project.

## Required evidence

- Expected source/transform/load counts and result files

## Optional enrichment

- Target aggregate counts
- reject samples
- external-ID/relationship checks
- ownership/record-type checks
- business invariants

## Evidence tools

`get_data_load_result`, `run_bounded_read_query`, `get_org_identity`, `describe_salesforce_component`

Tools are product-read-only. QA setup may create scenario evidence only inside disposable scratch orgs under a separate authority.

## Required findings

- count reconciliation
- reject/duplicate categories
- relationship and ownership gaps
- transformation anomalies
- business invariant violations
- confidence and sample limits
- safe correction plan

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
  -> data-migration-reconciler
  -> deterministic evidence lint
  -> sf-evidence-reviewer
  -> final envelope
```

Host limitations may require the parent to perform MCP calls and pass normalized evidence to a read-only subagent. The behavior contract remains the same.

## Known-truth scenarios

- `DATA-COUNT-MISMATCH`
- `DATA-DUPLICATE`
- `DATA-PARENT-MISSING`
- `DATA-OWNER`
- `DATA-TRANSFORM`
- `DATA-REJECTS`

## Quality gates

- Arithmetic is deterministic
- Sampling limits are explicit
- No corrective DML
- PII is minimized and redacted

## Failure and status behavior

- `refused`: unsafe request, missing mandatory input, or unresolved target ambiguity.
- `partial`: useful findings but missing/stale/truncated/contradictory evidence.
- `failed`: unexpected system/tool failure prevents valid output.
- `completed`: required evidence, deterministic lint, and independent review all pass.

## Known limitations

- Cannot prove full record equality from samples
- Does not re-run or fix a load
- Business invariants require user-defined rules

## Product metrics

- time to first useful finding;
- required-finding recall;
- root-cause rank;
- unsupported material claim rate;
- evidence-reference validity;
- context files/tokens and tool bytes;
- status correctness;
- repeat use and user acceptance.
