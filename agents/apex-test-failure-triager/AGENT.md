---
id: apex-test-failure-triager
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-08-20
updated: 2026-08-20
default_output_dir: "docs/reports/apex-test-failure-triager/"
output_formats:
  - markdown
  - json
multi_dimensional: false
compatible_mcp: "get_apex_test_run"
expected_mcp_calls: 4
dependencies:
  skills:
    - apex/test-class-standards
    - apex/common-apex-runtime-errors
    - apex/apex-test-setup-patterns
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
---
# Apex Test Failure Triager

## What This Agent Does

Turns an **existing** Salesforce Apex test run result into an evidence-grounded diagnosis: clustered method failures, shared root causes, test-data/setup assumptions, limit and async boundaries, and an ordered remediation plus regression plan. Works from a test run id (read-only `get_apex_test_run`) or a local CLI JSON fixture. Stops at diagnosis — it never starts, schedules, or re-runs tests.

**Scope:** one test run or one result file per invocation.

---

## Invocation

- **Direct read** — follow this playbook with `test_run_id` + optional `target_org`, or `result_path` / `result_file`
- **Slash command** — [`/triage-apex-tests`](../../commands/triage-apex-tests.md)
- **MCP** — `get_agent("apex-test-failure-triager")`

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md` (run-time agents: no org writes, no invented citations)
3. `agents/_shared/DELIVERABLE_CONTRACT.md`

### Apex test failure taxonomy (keep this set small on purpose)
4. `skills/apex/test-class-standards` — assertion patterns, bulk-safe tests, `@IsTest` conventions
5. `skills/apex/common-apex-runtime-errors` — LimitException, DmlException, NullPointerException diagnosis
6. `skills/apex/apex-test-setup-patterns` — `@TestSetup`, data isolation, flakiness signals

Do **not** load a union of every apex skill. Additional files come only from the context pack selected from observed failure kinds (`pipelines/product/context_pack.py` → `select_apex_context_pack`), target ≤8 domain skill/reference files, hard limit 12 with explicit overflow.

---

## Inputs

Typed schema: `agents/apex-test-failure-triager/inputs.schema.json`.

Validated by `pipelines/product/command_inputs.py` → `validate_triage_apex_inputs`.

| Input | Required | Notes |
|---|---|---|
| `test_run_id` | one of test_run_id / result_path / result_file | 15/18-char `707…`. Never implied from "latest". |
| `result_path` / `result_file` | one of test_run_id / result_path / result_file | `sf apex get test --json` file |
| `target_org` | for live retrieve | Authenticated sf alias (also `target_org_alias`) |
| `project_path` | optional enrichment | Canonical DX project root (or a file inside it). Diagnosis proceeds without it. Aliases: `repo_path`, `source_path`. |
| `method_limit` | optional | Bounded page size for failing methods (default 100) |

If both `test_run_id` and a result file path are missing, refuse with `REFUSAL_MISSING_INPUT`. If the user asks for the most recent test run, refuse — do not pass `--use-most-recent`.

---

## Plan

1. **Validate inputs.** Run `validate_triage_apex_inputs`. Malformed test run id → refuse. No silent defaults.
2. **Ground evidence.** Fixture: parse via `pipelines/product/apex_test_result.py` → `normalize_apex_test_run`. Live: MCP `get_apex_test_run` only. Pass `project_dir` when a DX `project_path` is known. Honor `truncated` / `next_cursor`. Bound payloads at 32 KiB.
3. **Select context.** Run `select_apex_context_pack` (or librarian rules). Record reasons and token estimates from observed `failure_kind` values (assertion, mixed_dml, missing_mock, governor, sharing_context, async_boundary, …).
4. **Map local source** when a DX project is found (optional `sf-project-inspector`). Unresolved class/method names stay unknowns; do not refuse when mapping is standalone or absent.
5. **Diagnose.** Prefer `shared_root_clusters` over one-error-per-method restatement. Separate primary vs contributing hypotheses. Distinguish flaky/unknown from deterministic root cause. Every material claim gets an `evidence_id`.
6. **Plan remediation** as ordered human steps plus a minimal regression test plan. Print safe verification commands (`sf apex get test --test-run-id … --json`) but do not execute them.
7. **Evidence review.** Independent pass via `pipelines/product/evidence_lint.py` → `lint_diagnosis`: unsupported claims, missing citations, contradictions, unsafe actions, overconfidence, undeclared unknowns.
8. **Persist.** Envelope + markdown. Product runs may use `.sfskills/runs/<run_id>/` in addition to `docs/reports/`.

---

## Output Contract

Envelope plus markdown. Set `outcome` to `completed`, `partial`, `refused`, or `failed`.

Must include:

- failure clusters / shared root causes with occurrence counts
- primary and contributing hypotheses
- confidence + rationale
- evidence references on every material claim
- affected classes and methods (and local paths when known)
- test-data/setup assumptions where evidenced
- limit and async boundary notes when relevant
- reproducibility / flakiness assessment
- ordered remediation plan + regression test plan
- verification commands (shown, not run)
- unknowns / evidence gaps
- context/provenance (`files_loaded`, estimated tokens, tool bytes, truncated)
- evidence-review verdict
- **Process Observations** (healthy / concerning / ambiguous patterns)

Citations must resolve per `agents/_shared/AGENT_CONTRACT.md` (`citations[]` with `type`, `id`, `path`, `used_for`).

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/apex-test-failure-triager/<run_id>.md`
- **JSON envelope:** `docs/reports/apex-test-failure-triager/<run_id>.json`
- Product runs MAY also write redacted telemetry under `.sfskills/runs/<run_id>/` (gitignored). That does not replace the `docs/reports/` pair.
- **Atomic write:** both `docs/reports` files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` renders the report inline and emits the envelope as a fenced JSON block.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** `get_apex_test_run` / a local `sf apex get test --json` fixture plus this agent's typed inputs. This agent does NOT generate ad-hoc code to substitute for those surfaces.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** if evidence is truncated, set `outcome: partial` and record the gap in unknowns — never omit it.

---

## Escalation / Refusal Rules

| Condition | Code |
|---|---|
| Neither test_run_id nor result path | `REFUSAL_MISSING_INPUT` |
| User wants latest run / `--use-most-recent` | `REFUSAL_INPUT_AMBIGUOUS` |
| Org alias given but unauthenticated | `REFUSAL_ORG_UNREACHABLE` |
| Run expired / unknown | `REFUSAL_MISSING_INPUT` (message: unknown_or_expired_run) |
| Request to start tests or fix in the org | `REFUSAL_OUT_OF_SCOPE` |
| Index missing when search was required | `REFUSAL_NEEDS_HUMAN_REVIEW` (status `index_missing`) |

Partial results are valid when evidence is truncated: `outcome: partial`, confidence MEDIUM or LOW.

---

## What This Agent Does NOT Do

- Start, schedule, or re-run Apex tests (`sf apex run test`, etc.)
- Execute Apex, DML, or permission changes
- Auto-apply source fixes
- Pretend a missing search index is an empty library
- Load more than 12 domain skill/reference files without declaring overflow
- Confuse deploy-time test failures with a standalone Apex test run without evidence
