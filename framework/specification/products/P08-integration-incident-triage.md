# P08 — Integration Incident Triage

**Lifecycle target:** beta portfolio  
**Primary command:** `/triage-integration`  
**Product agent:** `integration-incident-triager`

## User job

Correlate Salesforce and supplied integration evidence to classify an incident, identify the likely failing boundary, and propose safe verification and recovery steps.

## Personas and modes

- Personas: developer, integration-engineer, support-engineer, architect, consultant
- Modes: fixture, local-project, live-read-only, hybrid, scratch-qa

## Inputs

| Input | Requirement | Meaning |
|---|---|---|
| `integration` | required | Named integration/interface identifier |
| `time_window` | required | Explicit bounded window |
| `target_org` | optional | Read-only org |
| `evidence_files` | optional | Sanitized logs/events/response samples |
| `project_path` | optional | Local project |

At least one valid evidence input path must exist. Optional project inspection follows explicit path, one unambiguous active workspace, bounded roots, then standalone. The SfSkills repository itself is never assumed to be the target Salesforce project.

## Required evidence

- Integration identity and time window

## Optional enrichment

- Named Credential/External Credential summary
- Apex/Flow source
- event/log summaries
- HTTP status and contract samples
- downstream status supplied by user

## Evidence tools

`get_integration_config_summary`, `get_integration_event_summary`, `get_org_identity`, `describe_salesforce_component`, `get_code_analysis_result`

Tools are product-read-only. QA setup may create scenario evidence only inside disposable scratch orgs under a separate authority.

## Required findings

- incident boundary classification
- timeline
- auth/network/contract/limit/downstream/idempotency hypotheses
- supporting and contradictory evidence
- blast radius
- safe verification/recovery steps

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
  -> integration-incident-triager
  -> deterministic evidence lint
  -> sf-evidence-reviewer
  -> final envelope
```

Host limitations may require the parent to perform MCP calls and pass normalized evidence to a read-only subagent. The behavior contract remains the same.

## Known-truth scenarios

- `INT-AUTH`
- `INT-TIMEOUT`
- `INT-SCHEMA-DRIFT`
- `INT-RATE-LIMIT`
- `INT-IDEMPOTENCY`
- `INT-DOWNSTREAM`

## Quality gates

- Secrets are never reproduced
- Salesforce versus downstream cause is not guessed
- Time correlation and freshness are explicit
- Recovery does not perform customer mutation

## Failure and status behavior

- `refused`: unsafe request, missing mandatory input, or unresolved target ambiguity.
- `partial`: useful findings but missing/stale/truncated/contradictory evidence.
- `failed`: unexpected system/tool failure prevents valid output.
- `completed`: required evidence, deterministic lint, and independent review all pass.

## Known limitations

- Cannot prove downstream state without supplied evidence
- Logs may be sampled or unavailable
- Does not rotate credentials or replay transactions

## Product metrics

- time to first useful finding;
- required-finding recall;
- root-cause rank;
- unsupported material claim rate;
- evidence-reference validity;
- context files/tokens and tool bytes;
- status correctness;
- repeat use and user acceptance.
