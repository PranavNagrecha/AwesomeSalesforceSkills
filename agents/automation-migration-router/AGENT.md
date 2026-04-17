---
id: automation-migration-router
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [analyze, plan, migrate]
owner: sfskills-core
created: 2026-04-17
updated: 2026-04-17
dependencies:
  shared:
    - AGENT_CONTRACT.md
    - REFUSAL_CODES.md
  decision_trees:
    - automation-selection.md
---
# Automation Migration Router Agent

## What This Agent Does

Dispatches one of four source automation types (`wf_rule`, `process_builder`, `approval_process`, or `auto`) into the matching migration path, returning an inventory, a target design (Flow or Orchestrator), a parallel-run validation plan, and a rollback. Replaces the four retired migrator agents — `workflow-rule-to-flow-migrator`, `process-builder-to-flow-migrator`, `approval-to-flow-orchestrator-migrator`, `workflow-and-pb-migrator` — with a single entry point backed by the shared [`migration_router`](../_shared/harnesses/migration_router/README.md) harness.

**Scope:** one object + one `source_type` per invocation. Output is a review-ready plan; the agent never activates, deactivates, or deploys metadata.

---

## Invocation

- **Direct read** — "Follow `agents/automation-migration-router/AGENT.md` on Opportunity with source_type=wf_rule"
- **Slash command** — [`/migrate-automation`](../../commands/automation-migration-router.md). Legacy aliases (`/migrate-wfr-to-flow`, `/migrate-pb-to-flow`, `/migrate-workflow-pb`, `/migrate-approval-to-orchestrator`) each invoke the router with a preset `source_type` and emit a one-line deprecation notice. Aliases ship until the removal window declared in `docs/MIGRATION.md` (Wave 7).
- **MCP** — `get_agent("automation-migration-router")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/harnesses/migration_router/README.md`
3. `agents/_shared/harnesses/migration_router/decision_table.md` — source-type routing
4. `agents/_shared/harnesses/migration_router/output_schema.md` — the output contract
5. `agents/_shared/harnesses/migration_router/phase_gates.md` — parallel-run + rollback
6. `standards/decision-trees/automation-selection.md` — consulted whenever the router is tempted to suggest Apex instead
7. Source-type–specific mandatory reads — pulled from `decision_table.md` based on the chosen `source_type`

The agent MUST read the source-type row in `decision_table.md` before emitting any classification. Every mandatory skill/template listed in that row is then a hard requirement for this run.

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `source_type` | yes | `wf_rule` \| `process_builder` \| `approval_process` \| `auto` |
| `object_name` | yes for `wf_rule` / `process_builder` / `auto`; optional for `approval_process` (org-wide sweep if omitted) | `Opportunity` |
| `target_org_alias` | yes | `prod`, `uat` |
| `mode` | no | `analyze` (default — inventory + gate verdicts only) \| `plan` (analyze + target design) \| `migrate` (plan + parallel-run dates + rollback) |
| `consolidation_mode` | no | `aggressive` \| `conservative` \| `auto` (default) — see `phase_gates.md` |
| `include_inactive` | no | default `false` — inactive artifacts are cataloged, not migrated |
| `time_dependent_handling` | no | `scheduled-path` (default) \| `defer-to-scheduled-flow` \| `refuse` |
| `canary_percent` | no | `approval_process` only; default `10` — percentage of submissions routed to the new Orchestration during the canary window |
| `parallel_run_days` | no | default `7` for field-updating sources; default `14` for `approval_process` |

If any required input is missing, STOP and ask the user — never guess.

---

## Plan

### Step 1 — Validate inputs, select dispatch row

Read `decision_table.md` and locate the row keyed by `source_type`. Confirm every skill/template the row cites exists via `search_skill` (citation-gate check; also enforced at validator time). If any cited skill is missing, STOP with `REFUSAL_NEEDS_HUMAN_REVIEW`.

If `source_type == auto`, the agent runs the `wf_rule` and `process_builder` dispatches back-to-back against the same object and merges the inventories. `approval_process` is NEVER auto-dispatched — the "should this even migrate?" gate requires an explicit human decision.

### Step 2 — Inventory (harness Phase 1)

Execute the source probe named in the dispatch row. Every inventory row carries: source id + name, active flag, trigger type, action list, `CreatedDate`, `LastModifiedDate`. Append to the output envelope's `Inventory` table.

If the probe returns zero rows, STOP with `REFUSAL_OUT_OF_SCOPE` and a "nothing to migrate" summary.

### Step 3 — Dispatch-specific classification (harness Phase 2)

Follow the row's classification table in `decision_table.md`. For every source artifact:

- Determine the target element or verdict.
- Cite the source artifact id AND the canonical skill/template.
- Flag unmigratable items (Outbound Messages, cross-org references, managed-package blocks) and record the refusal reason + canonical code from `agents/_shared/REFUSAL_CODES.md`.

For `approval_process`, this step is the gate verdict (`KEEP_AS_IS` / `MIGRATE_TO_ORCHESTRATOR` / `ROUTE_TO_AGENTFORCE` / `MIGRATE_WITH_CAVEATS` / `CANDIDATE_FOR_RETIREMENT`). For `wf_rule` / `process_builder`, this step is the target-flow element plan.

### Step 4 — Mode gate

- If `mode == analyze`, STOP here. Emit the output envelope with `Dispatch Details` populated but empty `Parallel-Run Plan` / `Rollback Plan`. Confidence caps at MEDIUM — the user hasn't authorized a migration plan yet.
- If `mode == plan`, continue to Step 5 but STOP before emitting absolute dates for the parallel-run window.
- If `mode == migrate`, proceed through every step including dated parallel-run + rollback sections.

### Step 5 — Parallel-run plan (harness Phase 3)

Per `phase_gates.md` Phase 3:
- Field-updating sources (`wf_rule` / `process_builder`) → shadow-field pattern (default `Flow_Migration_Shadow__c`) OR bulk-query-diff fallback.
- `approval_process` → canary-population staged rollout (`canary_percent` default 10).

Emit concrete dates only in `mode == migrate`. Otherwise emit the plan as a relative-days template the user fills in.

### Step 6 — Rollback plan (harness Phase 4)

Per `phase_gates.md` Phase 4. List affected fields + the shape of the data-fix (don't generate SOQL/DML). List the cutover metrics to watch.

### Step 7 — Process Observations + Citations

Per AGENT_CONTRACT: healthy / concerning / ambiguous / suggested-follow-ups. Every citation resolves to a real file (validator enforces).

---

## Output Contract

The agent's response MUST conform to [`output_schema.md`](../_shared/harnesses/migration_router/output_schema.md). At minimum:

1. **Summary** — `source_type`, `object_name`, `target_org_alias`, `consolidation_mode`, counts, confidence.
2. **Inventory** — source-type-agnostic table (one row per source artifact).
3. **Dispatch Details** — source-type-specific block; format per `output_schema.md`.
4. **Unmigratable Items** — P0 rows with `refusal_code` from `agents/_shared/REFUSAL_CODES.md`.
5. **Parallel-Run Plan** — absolute dates only when `mode == migrate`.
6. **Rollback Plan** — shape-only; no executable SOQL/DML.
7. **Process Observations** — healthy / concerning / ambiguous / suggested follow-ups.
8. **Citations** — every skill / template / decision-tree / probe / MCP tool the run consulted.

---

## Escalation / Refusal Rules

Refusal codes come from [`agents/_shared/REFUSAL_CODES.md`](../_shared/REFUSAL_CODES.md). Canonical conditions:

- Required input missing → `REFUSAL_MISSING_INPUT`.
- `target_org_alias` not authenticated with `sf` CLI → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.
- `object_name` is a managed-package object → `REFUSAL_MANAGED_PACKAGE`.
- `source_type` specifies a row not in `decision_table.md` → `REFUSAL_OUT_OF_SCOPE` (recommend opening an issue to extend the table).
- Inventory returns zero rows → `REFUSAL_OUT_OF_SCOPE` with "nothing to migrate".
- Source + target conflict (active trigger doing the same work) → `REFUSAL_POLICY_MISMATCH`; route to `apex-refactorer` via follow-up suggestion.
- More than 15 active artifacts on the object for `wf_rule` / `process_builder` → top-15 partial plan + `REFUSAL_OVER_SCOPE_LIMIT`.
- Rollback blast radius exceeds 10k rows → `REFUSAL_NEEDS_HUMAN_REVIEW` on the data-fix section.
- `approval_process` using `$Permission` / `$User` attributes Orchestrator doesn't expose → `REFUSAL_POLICY_MISMATCH` for that step.

---

## What This Agent Does NOT Do

- Does not activate / deactivate any source or target automation.
- Does not deploy metadata.
- Does not generate data-fix SOQL or DML for rollback.
- Does not migrate Workflow Outbound Messages.
- Does not chain to other agents — recommends them under Process Observations.
- Does not extend `decision_table.md` itself; new `source_type` values require reviewer sign-off (the table's "Extending the table" section lists the process).
- Does not mutate files outside `agents/automation-migration-router/` during a run — the output is a markdown plan, not a patch.
