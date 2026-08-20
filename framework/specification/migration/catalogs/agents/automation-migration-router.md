# V2 Migration Profile: `automation-migration-router`

## Current source

- Path: `agents/automation-migration-router/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `analyze, plan, migrate`

## Current purpose

Dispatches one of four source automation types (`wf_rule`, `process_builder`, `approval_process`, or `auto`) into the matching migration path, returning an inventory, a target design (Flow or Orchestrator), a parallel-run validation plan, and a rollback. Replaces the four retired migrator agents — `workflow-rule-to-flow-migrator`, `process-builder-to-flow-migrator`, `approval-to-flow-orchestrator-migrator`, `workflow-and-pb-migrator` — with a single entry point backed by the shared [`migration_router`](../_shared/harnesses/migration_router/README.md) harness.

## V2 role

- Exposure: command/catalog specialist; not default subagent.
- This agent is a **catalog specialist**, not automatically a Cursor subagent.
- It MUST execute through the V2 run contract when invoked by a V2 command or adapter.
- Its existing Salesforce domain guidance remains canonical until explicitly superseded by a reviewed V2 product specification.

## Required V2 inputs

The adapter MUST validate the existing `inputs.schema.json` when present. It MUST additionally accept a run context containing `run_id`, execution mode, host capabilities, context budget, evidence policy, and optional project/org locators. Missing hard inputs produce `refused`; unavailable optional enrichment produces `partial` or a documented standalone path.

### Current input excerpt

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

## Evidence requirements

- Material statements about the target org require live read-only org evidence or an explicit `org_evidence_unavailable` unknown.
- Material statements about local source require project-inspector evidence or an explicit standalone result.
- Platform behavior claims require a current official source, a versioned SfSkills skill based on an official source, or a clearly labelled hypothesis.
- Skill citations justify recommendations; they do not prove org state.
- Every material claim MUST appear in the claim-evidence graph.

## Evidence prohibited

- Uncited model memory as proof of org state.
- A stale deployment/test result represented as current without timestamp and org association.
- A skill used as evidence that a component exists.
- Hidden raw tool output not represented in the evidence index.
- Product-side Salesforce mutation.

## Context contract

- Core contract and safety context: always loaded.
- Domain context target: at most 8 selected skill/reference files.
- Hard domain context limit: 12 unless the run returns an explicit overflow state.
- Raw MCP output in the model context: at most 32 KiB per page.
- Full subagent transcripts: prohibited.
- Existing broad mandatory-read lists MUST be converted to core plus conditional packs before this agent can be labelled V2-native.

## Framework collaborators

- `sf-context-librarian`: required when more than three candidate knowledge files exist.
- `sf-project-inspector`: optional enrichment; never assume the SfSkills repository is the Salesforce project.
- `sf-org-grounder`: required when `requires_org` is true and live mode is requested; host fallback applies when subagents cannot call MCP.
- `sf-evidence-reviewer`: required before a completed V2 product result.
- Deterministic output validation: always required.

## Failure modes

- Ambiguous target org or project.
- Missing or stale evidence.
- Context overflow or silent truncation.
- Contradictory repository and org evidence.
- Unsupported claim or invalid citation.
- Host lacks a required capability.
- Unsafe requested action.

## Success criteria

1. Inputs are schema-valid and execution mode is explicit.
2. Context stays within the declared budget or reports overflow.
3. Every material claim has valid evidence.
4. Unknowns and contradictions are surfaced.
5. The evidence reviewer produces no blocking finding.
6. The output envelope and product-specific schema validate.
7. No product mutation occurs.

## Current output excerpt

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

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/automation-migration-router/<run_id>.md`
- **JSON envelope:** `docs/reports/automation-migration-router/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Current non-goals excerpt

- Does not activate / deactivate any source or target automation.
- Does not deploy metadata.
- Does not generate data-fix SOQL or DML for rollback.
- Does not migrate Workflow Outbound Messages.
- Does not chain to other agents — recommends them under Process Observations.
- Does not extend `decision_table.md` itself; new `source_type` values require reviewer sign-off (the table's "Extending the table" section lists the process).
- Does not mutate files outside `agents/automation-migration-router/` during a run — the output is a markdown plan, not a patch.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
