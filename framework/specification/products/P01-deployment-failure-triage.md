# P01 — Deployment Failure Triage

**Lifecycle target:** release-candidate target  
**Primary command:** `/triage-deployment`  
**Product agent:** `deployment-failure-triager`

## User job

Tell me why this Salesforce deployment failed, group downstream symptoms under likely shared causes, and give me the safest remediation order.

## Personas and modes

- Personas: developer, release-engineer, consultant, architect
- Modes: fixture, live-read-only, local-project, hybrid, scratch-qa

## Inputs

| Input | Requirement | Meaning |
|---|---|---|
| `job_id` | conditional | Existing Salesforce deployment job ID; never guessed |
| `target_org` | conditional | Explicit org alias/username; required with live retrieval unless safely resolved and confirmed |
| `result_file` | conditional | Captured Salesforce CLI/API deployment-result JSON |
| `project_path` | optional | External Salesforce DX project for source mapping |
| `failure_limit` | optional | Bounded page size, default 100 |

At least one valid evidence input path must exist. Optional project inspection follows explicit path, one unambiguous active workspace, bounded roots, then standalone. The SfSkills repository itself is never assumed to be the target Salesforce project.

## Required evidence

- Existing deployment result with status, timestamp, target org association, and failure details

## Optional enrichment

- External Salesforce DX project
- Relevant component source and metadata
- Current official API/tool behavior
- Existing Apex test result details

## Evidence tools

`get_deployment_result`, `get_org_identity`, `describe_salesforce_component`, `get_code_analysis_result`

Tools are product-read-only. QA setup may create scenario evidence only inside disposable scratch orgs under a separate authority.

## Required findings

- component failure groups
- Apex test failure groups
- coverage/warning groups
- primary and contributing root causes
- affected components and resolvable local paths
- ordered remediation plan
- safe verification commands
- unknowns and contradictions

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
  -> deployment-failure-triager
  -> deterministic evidence lint
  -> sf-evidence-reviewer
  -> final envelope
```

Host limitations may require the parent to perform MCP calls and pass normalized evidence to a read-only subagent. The behavior contract remains the same.

## Known-truth scenarios

- `DEP-MISSING-DEPENDENCY`
- `DEP-APEX-COMPILE`
- `DEP-TEST-FAILURE`
- `DEP-COVERAGE`
- `DEP-DUPLICATE-SYMPTOMS`
- `DEP-ORG-MISMATCH`

## Quality gates

- Every material cause links to deployment evidence
- Duplicate symptoms preserve counts and evidence IDs
- No most-recent job fallback
- Standalone diagnosis works without a local project
- Unsafe deploy/cancel/retry actions are not executed

## Failure and status behavior

- `refused`: unsafe request, missing mandatory input, or unresolved target ambiguity.
- `partial`: useful findings but missing/stale/truncated/contradictory evidence.
- `failed`: unexpected system/tool failure prevents valid output.
- `completed`: required evidence, deterministic lint, and independent review all pass.

## Known limitations

- Does not start, retry, cancel, quick-deploy, or modify a deployment
- Cannot prove local source state without a selected project
- May return partial when job data is expired or truncated

## Product metrics

- time to first useful finding;
- required-finding recall;
- root-cause rank;
- unsupported material claim rate;
- evidence-reference validity;
- context files/tokens and tool bytes;
- status correctness;
- repeat use and user acceptance.
