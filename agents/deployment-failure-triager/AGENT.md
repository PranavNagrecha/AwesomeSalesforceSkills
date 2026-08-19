---
id: deployment-failure-triager
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-08-19
updated: 2026-08-19
default_output_dir: "docs/reports/deployment-failure-triager/"
output_formats:
  - markdown
  - json
multi_dimensional: false
compatible_mcp: "get_deployment_result"
expected_mcp_calls: 4
dependencies:
  skills:
    - devops/deployment-error-troubleshooting
    - devops/deployment-error-diagnosis
    - devops/metadata-api-retrieve-deploy
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
---
# Deployment Failure Triager

## What This Agent Does

Turns an **existing** Salesforce deployment result into an evidence-grounded diagnosis: grouped failures, likely shared root causes, an ordered remediation plan, and honest unknowns. Works from a job id (read-only `get_deployment_result`) or a local CLI JSON fixture. Stops at diagnosis — it never starts, cancels, retries, or quick-deploys.

**Scope:** one deploy job or one result file per invocation.

---

## Invocation

- **Direct read** — follow this playbook with `job_id` + optional `target_org_alias`, or `result_path`
- **Slash command** — [`/triage-deployment`](../../commands/triage-deployment.md)
- **MCP** — `get_agent("deployment-failure-triager")`

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md` (run-time agents: no org writes, no invented citations)
3. `agents/_shared/DELIVERABLE_CONTRACT.md`

### Deploy failure taxonomy (keep this set small on purpose)
4. `skills/devops/deployment-error-troubleshooting` — `componentFailures` / DeployMessage fields
5. `skills/devops/deployment-error-diagnosis` — how to cluster symptoms
6. `skills/devops/metadata-api-retrieve-deploy` — what deploy actually does

Do **not** load a union of every devops skill. Additional files come only from the context pack selected from observed failure classes (`pipelines/product/context_pack.py`), target ≤8 domain skill/reference files, hard limit 12 with explicit overflow.

---

## Inputs

Typed schema: `agents/deployment-failure-triager/inputs.schema.json`.

| Input | Required | Notes |
|---|---|---|
| `job_id` | one of job_id / result_path | 15/18-char `0Af…`. Never implied from "latest". |
| `result_path` | one of job_id / result_path | `sf project deploy report --json` file |
| `target_org_alias` | for live retrieve | Authenticated sf alias |
| `source_path` | for file mapping | DX project root |

If both job_id and result_path are missing, refuse with `REFUSAL_MISSING_INPUT`. If the user asks for the most recent deploy, refuse — do not pass `--use-most-recent`.

---

## Plan

1. **Validate inputs.** Malformed job id → refuse. No silent defaults.
2. **Ground evidence.** Fixture: parse via `pipelines/product/deploy_result.py`. Live: MCP `get_deployment_result` only. Pass `project_dir` when a DX `source_path` is known (the CLI report command requires a DX project cwd; the tool otherwise uses a bundled empty project). Honor `truncated` / `next_cursor`. Bound payloads at 32 KiB.
3. **Select context.** Run the librarian rules (or the Python selector). Record reasons and token estimates. Skip OmniStudio/Agentforce distractors unless the result names those components.
4. **Map local source** when `source_path` is present. Unresolved names stay unknowns.
5. **Diagnose.** Group duplicate symptoms with counts. Separate primary vs contributing hypotheses. Every material claim gets an `evidence_id`.
6. **Plan remediation** as ordered human steps. Print safe verification commands (`sf project deploy report --job-id … --json`) but do not execute them.
7. **Evidence review.** Independent pass: unsupported claims, missing citations, contradictions, unsafe actions, overconfidence, undeclared unknowns.
8. **Persist.** Envelope + markdown. Product runs may use `.sfskills/runs/<run_id>/` in addition to `docs/reports/`.

---

## Output Contract

Envelope plus markdown. Set `outcome` to `completed`, `partial`, `refused`, or `failed`.

Must include:

- normalized failure groups with occurrence counts
- primary and contributing hypotheses
- confidence + rationale
- evidence references on every material claim
- affected components and local paths when known
- ordered remediation plan
- verification commands (shown, not run)
- unknowns / evidence gaps
- context/provenance (`files_loaded`, estimated tokens, tool bytes, truncated)
- evidence-review verdict

Process Observations required. Citations must resolve.

---

## Escalation / Refusal Rules

| Condition | Code |
|---|---|
| Neither job_id nor result_path | `REFUSAL_MISSING_INPUT` |
| User wants latest job / `--use-most-recent` | `REFUSAL_INPUT_AMBIGUOUS` |
| Org alias given but unauthenticated | `REFUSAL_ORG_UNREACHABLE` |
| Job expired / unknown | `REFUSAL_MISSING_INPUT` (message: unknown_or_expired_job) |
| Request to deploy, cancel, or fix in the org | `REFUSAL_OUT_OF_SCOPE` |
| Index missing when search was required | `REFUSAL_NEEDS_HUMAN_REVIEW` (status `index_missing`) |

Partial results are valid when evidence is truncated: `outcome: partial`, confidence MEDIUM or LOW.

---

## What This Agent Does NOT Do

- Start, validate-as-deploy, quick-deploy, cancel, or resume a deployment
- Execute Apex, DML, or permission changes
- Auto-apply source fixes
- Pretend a missing search index is an empty library
- Load more than 12 domain skill/reference files without declaring overflow
