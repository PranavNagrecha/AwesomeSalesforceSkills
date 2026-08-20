# P10 — Org Health Assessment

**Lifecycle target:** beta portfolio  
**Primary command:** `/assess-org-health`  
**Product agent:** `org-health-assessor-v2`

## User job

Produce an evidence-backed, prioritized Salesforce health roadmap across Trusted, Easy, and Adaptable dimensions without reducing the org to a superficial score.

## Personas and modes

- Personas: architect, admin, consultant, security-reviewer, engineering-lead
- Modes: fixture, live-read-only, hybrid, scratch-qa

## Inputs

| Input | Requirement | Meaning |
|---|---|---|
| `target_org` | conditional | Explicit read-only org |
| `assessment_scope` | optional | Full or selected architecture dimensions |
| `evidence_bundle` | conditional | Captured snapshot for offline mode |
| `business_context` | optional | Critical processes, compliance, release cadence |

At least one valid evidence input path must exist. Optional project inspection follows explicit path, one unambiguous active workspace, bounded roots, then standalone. The SfSkills repository itself is never assumed to be the target Salesforce project.

## Required evidence

- Org snapshot or explicit fixture

## Optional enrichment

- metadata inventory
- automation/security/access summaries
- limits/adoption/technical debt evidence
- release history supplied by user

## Evidence tools

`get_org_snapshot_manifest`, `get_automation_inventory`, `get_user_access_evidence`, `get_code_analysis_result`, `get_limits_snapshot`

Tools are product-read-only. QA setup may create scenario evidence only inside disposable scratch orgs under a separate authority.

## Required findings

- trusted/easy/adaptable evidence
- critical risks
- maintainability and lifecycle issues
- strengths
- sequenced 30/60/90-day roadmap
- measurement plan

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
  -> org-health-assessor-v2
  -> deterministic evidence lint
  -> sf-evidence-reviewer
  -> final envelope
```

Host limitations may require the parent to perform MCP calls and pass normalized evidence to a read-only subagent. The behavior contract remains the same.

## Known-truth scenarios

- `HLT-SECURITY`
- `HLT-AUTOMATION-DEBT`
- `HLT-LIMITS`
- `HLT-MAINTAINABILITY`
- `HLT-ALM`
- `HLT-DATA-INTEGRITY`

## Quality gates

- Every score/rating has evidence and caveats
- Strong areas are reported, not only defects
- Roadmap prioritizes impact and effort
- No unsupported maturity benchmark

## Failure and status behavior

- `refused`: unsafe request, missing mandatory input, or unresolved target ambiguity.
- `partial`: useful findings but missing/stale/truncated/contradictory evidence.
- `failed`: unexpected system/tool failure prevents valid output.
- `completed`: required evidence, deterministic lint, and independent review all pass.

## Known limitations

- Not a compliance audit
- Some business/process health requires interviews
- Org snapshots may omit managed/external behavior

## Product metrics

- time to first useful finding;
- required-finding recall;
- root-cause rank;
- unsupported material claim rate;
- evidence-reference validity;
- context files/tokens and tool bytes;
- status correctness;
- repeat use and user acceptance.
