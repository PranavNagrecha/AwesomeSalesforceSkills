# P11 — Agentforce Quality Engineer

**Lifecycle target:** beta portfolio  
**Primary command:** `/review-agentforce-agent`  
**Product agent:** `agentforce-quality-engineer`

## User job

Review an Agentforce agent, topics/subagents, actions, grounding, guardrails, tests, and implementation dependencies for correctness, safety, and release readiness.

## Personas and modes

- Personas: agentforce-builder, developer, architect, security-reviewer, consultant
- Modes: fixture, local-project, live-read-only, hybrid, scratch-qa

## Inputs

| Input | Requirement | Meaning |
|---|---|---|
| `agent_metadata_path` | required | Retrieved Agentforce metadata path |
| `agent_developer_name` | required | Explicit agent identity |
| `target_org` | optional | Read-only org for action implementations/test results |
| `review_depth` | optional | overview/topics/actions/full |

At least one valid evidence input path must exist. Optional project inspection follows explicit path, one unambiguous active workspace, bounded roots, then standalone. The SfSkills repository itself is never assumed to be the target Salesforce project.

## Required evidence

- Agentforce metadata and explicit agent identity

## Optional enrichment

- Action Apex/Flow source
- Agentforce test definitions/results
- grounding sources
- prompt/templates
- permission/security evidence

## Evidence tools

`get_agentforce_test_result`, `describe_salesforce_component`, `get_code_analysis_result`, `get_flow_test_result`

Tools are product-read-only. QA setup may create scenario evidence only inside disposable scratch orgs under a separate authority.

## Required findings

- topic/subagent coherence
- action input/output and side effects
- grounding/evidence quality
- guardrail gaps
- permission/data risks
- test coverage and failures
- release readiness

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
  -> agentforce-quality-engineer
  -> deterministic evidence lint
  -> sf-evidence-reviewer
  -> final envelope
```

Host limitations may require the parent to perform MCP calls and pass normalized evidence to a read-only subagent. The behavior contract remains the same.

## Known-truth scenarios

- `AFX-ACTION-CONTRACT`
- `AFX-GROUNDING`
- `AFX-GUARDRAIL`
- `AFX-PERMISSION`
- `AFX-TEST-GAP`
- `AFX-TOPIC-ROUTING`

## Quality gates

- Uses current Agentforce metadata concepts
- Does not infer hidden production behavior
- Side-effect surface is explicit
- Test and grounding evidence are traceable

## Failure and status behavior

- `refused`: unsafe request, missing mandatory input, or unresolved target ambiguity.
- `partial`: useful findings but missing/stale/truncated/contradictory evidence.
- `failed`: unexpected system/tool failure prevents valid output.
- `completed`: required evidence, deterministic lint, and independent review all pass.

## Known limitations

- Does not publish or activate agents
- Cannot inspect proprietary model internals
- Quality depends on available test telemetry

## Product metrics

- time to first useful finding;
- required-finding recall;
- root-cause rank;
- unsupported material claim rate;
- evidence-reference validity;
- context files/tokens and tool bytes;
- status correctness;
- repeat use and user acceptance.
