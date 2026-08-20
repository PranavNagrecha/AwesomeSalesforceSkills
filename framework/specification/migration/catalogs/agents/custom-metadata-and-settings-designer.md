# V2 Migration Profile: `custom-metadata-and-settings-designer`

## Current source

- Path: `agents/custom-metadata-and-settings-designer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `design, audit`

## Current purpose

Two modes:

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
| `mode` | yes | `design` \| `audit` |
| `target_org_alias` | yes |
| `scenario_summary` | design | "feature flag registry for 30 Apex classes; per-environment values; production reads must be fast" |
| `expected_usage` | design | `apex` \| `flow` \| `formula` \| `apex+flow` \| `apex+flow+formula` |
| `expected_record_count` | design | integer — approximate live record count |
| `environment_scoped` | design | `true` if values vary per sandbox/prod (tilts to CMT) |
| `audit_scope` | audit | `org` \| `type:<DeveloperName>` |

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

Design mode:

1. **Summary** — scenario, chosen artifact type, record count estimate, environment-scope, confidence.
2. **Decision rationale** — table of considered alternatives + why the chosen artifact won.
3. **Type / setting design** — fields, protection, naming, default record plan.
4. **Usage patterns** — Apex, Flow, Formula snippets aligned with `templates/apex/cmdt/`.
5. **Metadata stubs** — fenced XML for the type + 1–3 default records.
6. **Deploy plan** — type first, records second (CMT); for Custom Settings, type via metadata + records via data import.
7. **Runtime-mutation stance** — deliberate yes/no.
8. **Process Observations**:
   - **What was healthy** — existing CMT patterns reusable, Apex selectors that already read from CMT, environment values already decoupled from hard-coded constants.
   - **What was concerning** — scenarios that look like CMT but are really runtime state, expected record count creeping near 10k (the CMT/Settings exit point), protected-component decisions that don't match the org's packaging strategy.
   - **What was ambiguous** — feature-flag lifecycle (when is a flag retired?), whether per-user values are actually profile-level.
   - **Suggested follow-up agents** — `apex-builder` (if the feature needs a selector that reads the CMT), `deployment-risk-scorer` (before the first deploy).
9. **Citations**.

Audit mode:

1. **Summary** — type count, settings count, findings per severity.
2. **Dead-type report** — types with 0 records / 0 references.
3. **Mis-classification report** — List Settings to migrate, Custom Objects to collapse into CMT.
4. **Hierarchy Setting coverage report** — missing org-defaults, stale profile assignments.
5. **Runtime-mutation report** — types being updated via Metadata API, with reason-detected (Apex class name that emits `Metadata.DeployContainer`).
6. **Process Observations** — as above.
7. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/custom-metadata-and-settings-designer/<run_id>.md`
- **JSON envelope:** `docs/reports/custom-metadata-and-settings-designer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consum

## Current non-goals excerpt

- Does not create types or records.
- Does not import Custom Setting data.
- Does not refactor Apex classes that currently read from the wrong artifact — that's `apex-refactorer`.
- Does not design a managed-package shipping strategy — that's `release-train-planner` + `package-development-strategy` in the skill library.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
