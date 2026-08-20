# P02 — Apex Test Failure Triage

**Lifecycle target:** release-candidate target  
**Primary command:** `/triage-apex-tests`  
**Product agent:** `apex-test-failure-triager`

## User job

Explain why an existing Apex test run failed, identify shared root causes across methods, and propose the smallest evidence-backed fix and regression plan.

## Personas and modes

- Personas: developer, release-engineer, consultant
- Modes: fixture, live-read-only, local-project, hybrid, scratch-qa

## Inputs

| Input | Requirement | Meaning |
|---|---|---|
| `test_run_id` | conditional | Existing Apex test run ID |
| `target_org` | conditional | Explicit org alias/username for live retrieval |
| `result_file` | conditional | Captured test-result JSON |
| `project_path` | optional | External Salesforce DX project |
| `method_limit` | optional | Bounded page size |

At least one valid evidence input path must exist. Optional project inspection follows explicit path, one unambiguous active workspace, bounded roots, then standalone. The SfSkills repository itself is never assumed to be the target Salesforce project.

## Required evidence

- Existing Apex test result with methods, messages, stack traces, timing, and org association

## Optional enrichment

- Apex class/test source
- trigger/flow inventory relevant to the transaction
- coverage result
- current platform guidance

## Evidence tools

`get_apex_test_run`, `get_org_identity`, `describe_salesforce_component`, `get_automation_inventory`, `get_code_analysis_result`

Tools are product-read-only. QA setup may create scenario evidence only inside disposable scratch orgs under a separate authority.

## Required findings

- failure clusters
- shared root causes
- test-data/setup assumptions
- limit and async boundaries
- affected classes and methods
- reproducibility/flakiness assessment
- minimal correction plan
- regression test plan

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
  -> apex-test-failure-triager
  -> deterministic evidence lint
  -> sf-evidence-reviewer
  -> final envelope
```

Host limitations may require the parent to perform MCP calls and pass normalized evidence to a read-only subagent. The behavior contract remains the same.

## Known-truth scenarios

- `APX-ASSERTION`
- `APX-MIXED-DML`
- `APX-MISSING-MOCK`
- `APX-GOVERNOR`
- `APX-SHARING-CONTEXT`
- `APX-ASYNC-BOUNDARY`
- `APX-SHARED-ROOT`

## Quality gates

- Shared-cause clustering improves over one-error-per-test restatement
- Stack/source claims cite exact evidence
- No test is started by the product
- Flaky/unknown is distinguished from deterministic root cause

## Failure and status behavior

- `refused`: unsafe request, missing mandatory input, or unresolved target ambiguity.
- `partial`: useful findings but missing/stale/truncated/contradictory evidence.
- `failed`: unexpected system/tool failure prevents valid output.
- `completed`: required evidence, deterministic lint, and independent review all pass.

## Known limitations

- Retrieves existing runs only in product mode
- Cannot inspect unprovided local source in standalone mode
- May not distinguish production-only behavior without relevant evidence

## Product metrics

- time to first useful finding;
- required-finding recall;
- root-cause rank;
- unsupported material claim rate;
- evidence-reference validity;
- context files/tokens and tool bytes;
- status correctness;
- repeat use and user acceptance.
