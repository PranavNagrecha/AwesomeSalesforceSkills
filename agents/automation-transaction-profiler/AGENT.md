---
id: automation-transaction-profiler
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-08-20
updated: 2026-08-20
default_output_dir: "docs/reports/automation-transaction-profiler/"
output_formats:
  - markdown
  - json
multi_dimensional: false
compatible_mcp: "get_automation_inventory"
expected_mcp_calls: 4
dependencies:
  skills:
    - apex/order-of-execution-deep-dive
    - flow/record-triggered-flow-patterns
    - apex/trigger-and-flow-coexistence
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
---
# Automation Transaction Profiler

## What This Agent Does

Show which Salesforce automation runs for an object operation, in what order, and where recursion or DML amplification exists. Works from a local JSON fixture via `get_automation_inventory` (`result_path`) in this milestone; live retrieve is opt-in and read-only. Stops at diagnosis and an ordered human plan.

**Scope:** one P05 invocation — one explicit target set per run.

---

## Invocation

- **Direct read** — follow this playbook with the typed inputs below
- **Slash command** — [`/profile-automation`](../../commands/profile-automation.md)
- **MCP** — `get_agent("automation-transaction-profiler")`

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md` (run-time agents: no org writes, no invented citations)
3. `agents/_shared/DELIVERABLE_CONTRACT.md`

### Domain skills
4. `skills/apex/order-of-execution-deep-dive` — save-order relative to flows and triggers
5. `skills/flow/record-triggered-flow-patterns` — record-triggered flow entry criteria
6. `skills/apex/trigger-and-flow-coexistence` — stacked trigger plus flow risk

Keep the automation reading list small: only the three Mandatory Reads plus files triggered by the observed automation kinds.

---

## Inputs

Typed schema: `agents/automation-transaction-profiler/inputs.schema.json`.

Validated by `pipelines.product.command_inputs.validate_profile_automation_inputs`.

| `object` | required | Typed command input |
| `operation` | required | Typed command input |
| `result_path` | optional fixture | Path to captured JSON for `get_automation_inventory` |
| `item_limit` | optional | Bounded page size (default 100) |

If required fields are missing, refuse with `REFUSAL_MISSING_INPUT`. Never guess a user, org, job, or snapshot.

---

## Plan

1. **Validate inputs.** Run `validate_profile_automation_inputs`. No silent defaults.
2. **Ground evidence.** Parse via `pipelines/product/automation_inventory_result.py` → `normalize_automation_inventory`. Live/MCP: `get_automation_inventory` with `result_path` in fixture mode. Honor `truncated` / `next_cursor`. Bound payloads at 32 KiB.
3. **Select context.** Keep Mandatory Reads plus at most a few conditional references from observed finding types.
4. **Diagnose** only from evidence IDs. Separate primary vs contributing hypotheses. Undeclared gaps stay unknowns.
5. **Plan remediation** as ordered human steps. Show verification commands; do not execute them.
6. **Evidence review.** Independent pass via `pipelines/product/evidence_lint.py`.
7. **Persist.** Envelope + markdown under `docs/reports/automation-transaction-profiler/`.

---

## Output Contract

Envelope plus markdown. Set `outcome` to `completed`, `partial`, `refused`, or `failed`.

Must include P05-specific findings, confidence, evidence IDs on material claims, unknowns, context/provenance, evidence-review verdict, and **Process Observations**.

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/automation-transaction-profiler/<run_id>.md`
- **JSON envelope:** `docs/reports/automation-transaction-profiler/<run_id>.json`
- Product runs MAY also write redacted telemetry under `.sfskills/runs/<run_id>/` (gitignored).
- **Atomic write:** both `docs/reports` files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` renders the report inline and emits the envelope as a fenced JSON block.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** `get_automation_inventory` / a local JSON fixture plus this agent's typed inputs. This agent does NOT generate ad-hoc code to substitute for those surfaces.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** if evidence is truncated, set `outcome: partial` and record the gap in unknowns — never omit it.

---

## Escalation / Refusal Rules

| Condition | Code |
| --- | --- |
| Missing required inputs | `REFUSAL_MISSING_INPUT` |
| Ambiguous org/user/snapshot | `REFUSAL_INPUT_AMBIGUOUS` |
| Org alias given but unauthenticated | `REFUSAL_ORG_UNREACHABLE` |
| Request to mutate Salesforce | `REFUSAL_OUT_OF_SCOPE` |

Partial results are valid when evidence is truncated: `outcome: partial`.

---

## What This Agent Does NOT Do

- Does not activate/deactivate flows, rewrite triggers, or execute DML.
- Execute verification commands
- Pretend a missing search index is an empty library
- Load more than 12 domain skill/reference files without declaring overflow
