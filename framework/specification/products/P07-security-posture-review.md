# P07 — Security Posture Review

**Lifecycle target:** beta portfolio  
**Primary command:** `/review-security-posture`  
**Product agent:** `security-posture-reviewer`

## User job

Assess a Salesforce scope for evidence-backed access, code, session, integration, data, and configuration risks, prioritized by exploitability and business impact.

## Personas and modes

- Personas: security-reviewer, architect, developer, admin, consultant
- Modes: fixture, local-project, live-read-only, hybrid, scratch-qa

## Inputs

| Input | Requirement | Meaning |
|---|---|---|
| `scope` | required | Org, project, package, object set, or security domain |
| `project_path` | optional | Local project |
| `target_org` | optional | Read-only org |
| `policy_profile` | optional | Framework default or approved organization policy |

At least one valid evidence input path must exist. Optional project inspection follows explicit path, one unambiguous active workspace, bounded roots, then standalone. The SfSkills repository itself is never assumed to be the target Salesforce project.

## Required evidence

- Explicit scope and policy profile

## Optional enrichment

- Code Analyzer results
- CRUD/FLS/sharing/session evidence
- integration/credential metadata summary
- guest/external user exposure
- audit settings

## Evidence tools

`get_code_analysis_result`, `get_user_access_evidence`, `get_org_snapshot_manifest`, `get_integration_config_summary`, `describe_salesforce_component`

Tools are product-read-only. QA setup may create scenario evidence only inside disposable scratch orgs under a separate authority.

## Required findings

- evidence-backed risks
- affected assets/users
- severity/exploitability/impact
- false-positive and uncertainty notes
- least-privilege remediation sequence
- verification controls

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
  -> security-posture-reviewer
  -> deterministic evidence lint
  -> sf-evidence-reviewer
  -> final envelope
```

Host limitations may require the parent to perform MCP calls and pass normalized evidence to a read-only subagent. The behavior contract remains the same.

## Known-truth scenarios

- `SEC-INJECTION`
- `SEC-FLS`
- `SEC-SHARING`
- `SEC-NAMED-CREDENTIAL`
- `SEC-SESSION`
- `SEC-GUEST`

## Quality gates

- No security claim without evidence and scope
- Never exposes secrets
- Severity rationale is explicit
- Policy versus platform finding is distinguished

## Failure and status behavior

- `refused`: unsafe request, missing mandatory input, or unresolved target ambiguity.
- `partial`: useful findings but missing/stale/truncated/contradictory evidence.
- `failed`: unexpected system/tool failure prevents valid output.
- `completed`: required evidence, deterministic lint, and independent review all pass.

## Known limitations

- Not a penetration test or compliance certification
- Cannot inspect encrypted secrets
- Managed-package internals may be unavailable

## Product metrics

- time to first useful finding;
- required-finding recall;
- root-cause rank;
- unsupported material claim rate;
- evidence-reference validity;
- context files/tokens and tool bytes;
- status correctness;
- repeat use and user acceptance.
