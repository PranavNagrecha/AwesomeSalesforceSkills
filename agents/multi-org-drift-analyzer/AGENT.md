---
id: multi-org-drift-analyzer
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-08-20
updated: 2026-08-20
default_output_dir: "docs/reports/multi-org-drift-analyzer/"
output_formats:
  - markdown
  - json
multi_dimensional: false
compatible_mcp: "compare_org_snapshots"
expected_mcp_calls: 4
dependencies:
  skills:
    - architect/multi-org-strategy
    - devops/source-tracking-and-conflict-resolution
    - devops/package-development-strategy
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
---
# Multi-Org Drift Analysis

## What This Agent Does

Compare two explicit org snapshots and separate expected environmental differences from dangerous configuration drift. Works from a local JSON fixture via `compare_org_snapshots` (`result_path`) in this milestone; live retrieve is opt-in and read-only. Stops at diagnosis and an ordered human plan.

**Scope:** one P12 invocation — one explicit target set per run.

---

## Invocation

- **Direct read** — follow this playbook with the typed inputs below
- **Slash command** — [`/compare-orgs`](../../commands/compare-orgs.md)
- **MCP** — `get_agent("multi-org-drift-analyzer")`

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md` (run-time agents: no org writes, no invented citations)
3. `agents/_shared/DELIVERABLE_CONTRACT.md`

### Domain skills
4. `skills/architect/multi-org-strategy` — expected vs dangerous org differences
5. `skills/devops/source-tracking-and-conflict-resolution` — source vs org drift
6. `skills/devops/package-development-strategy` — packaging boundary drift

Keep the drift reading list small: only the three Mandatory Reads plus files triggered by difference class.

---

## Inputs

Typed schema: `agents/multi-org-drift-analyzer/inputs.schema.json`.

Validated by `pipelines.product.command_inputs.validate_compare_orgs_inputs`.

| `left_org_or_snapshot` | required | Typed command input |
| `right_org_or_snapshot` | required | Typed command input |
| `result_path` | optional fixture | Path to captured JSON for `compare_org_snapshots` |
| `item_limit` | optional | Bounded page size (default 100) |

If required fields are missing, refuse with `REFUSAL_MISSING_INPUT`. Never guess a user, org, job, or snapshot.

---

## Plan

1. **Validate inputs.** Run `validate_compare_orgs_inputs`. No silent defaults.
2. **Ground evidence.** Parse via `pipelines/product/org_compare_result.py` → `normalize_org_compare`. Live/MCP: `compare_org_snapshots` with `result_path` in fixture mode. Honor `truncated` / `next_cursor`. Bound payloads at 32 KiB.
3. **Select context.** Keep Mandatory Reads plus at most a few conditional references from observed finding types.
4. **Diagnose** only from evidence IDs. Separate primary vs contributing hypotheses. Undeclared gaps stay unknowns.
5. **Plan remediation** as ordered human steps. Show verification commands; do not execute them.
6. **Evidence review.** Independent pass via `pipelines/product/evidence_lint.py`.
7. **Persist.** Envelope + markdown under `docs/reports/multi-org-drift-analyzer/`.

---

## Output Contract

Envelope plus markdown. Set `outcome` to `completed`, `partial`, `refused`, or `failed`.

Must include P12-specific findings, confidence, evidence IDs on material claims, unknowns, context/provenance, evidence-review verdict, and **Process Observations**.

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/multi-org-drift-analyzer/<run_id>.md`
- **JSON envelope:** `docs/reports/multi-org-drift-analyzer/<run_id>.json`
- Product runs MAY also write redacted telemetry under `.sfskills/runs/<run_id>/` (gitignored).
- **Atomic write:** both `docs/reports` files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` renders the report inline and emits the envelope as a fenced JSON block.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** `compare_org_snapshots` / a local JSON fixture plus this agent's typed inputs. This agent does NOT generate ad-hoc code to substitute for those surfaces.
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

- Does not sync orgs, deploy to either side, or invent a left/right target.
- Execute verification commands
- Pretend a missing search index is an empty library
- Load more than 12 domain skill/reference files without declaring overflow
