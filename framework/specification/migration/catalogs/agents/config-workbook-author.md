# V2 Migration Profile: `config-workbook-author`

## Current source

- Path: `agents/config-workbook-author/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Given a finalized story backlog, a fit-gap report, and (optionally) a process-flow map, compiles the **canonical 10-section Salesforce Configuration Workbook** — the single document an admin or developer reads to execute a phase of work without any further BA discovery.

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
| `backlog_path` | yes | path to a finalized story backlog (story-drafter JSON envelope or markdown table) |
| `fit_gap_path` | yes | path to a fit-gap report (fit-gap-analyzer JSON envelope or markdown) — descope decisions MUST be honored |
| `target_org_alias` | yes | the org being configured |
| `process_flow_path` | no | path to a process-flow-mapper output — when supplied, Automation section embeds handoff references |
| `release_window` | yes | release identifier (e.g. `R3-2026`) — used as the workbook header + RTM linkage |
| `personas_supplied` | no | persona inventory; if absent, the agent infers from the backlog and flags |
| `org_profile_overrides` | no | overrides for the Org Profile header (parent-org license that the sandbox doesn't show) |

If `backlog_path`, `fit_gap_path`, or `target_org_alias` is missing, refuse — the workbook is the *capstone*, not a from-scratch design doc.

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

One markdown document:

1. **Summary** — release window, target org, story count, total workbook rows by section, overall confidence (HIGH/MEDIUM/LOW).
2. **Section 1 — Org Profile** — header table + edition + license SKUs + flags.
3. **Section 2-10** — one heading per section with the row tables compiled in Step 4.
4. **Deployment order** — flat list from Step 5 with `row_id` + `deploy_order_position`.
5. **RTM rollup** — Step 9 sub-table.
6. **Process Observations**:
   - **What was healthy** — every row validated against runtime roster, every persona reconciled with `user-access-comparison`, no over-customization on the target objects, RTM integrity 100%, MoSCoW capacity respected.
   - **What was concerning** — descope items not honored, > 5 net-new objects, automation count > 5 per object (recommend consolidation first), persona drift, missing AI use-case assessment for AI-shaped rows, license gaps not covered by a SKU acquisition row.
   - **What was ambiguous** — rows whose `recommended_agent` could equally be two agents (e.g. `flow-builder` vs `process-flow-mapper` for an automation chain).
   - **Suggested follow-up agents** — every agent named in any row's `recommended_agent` field; ADR via `architect/architecture-decision-records` for cross-cloud rows.
7. **Citations** — every skill, decision tree, probe, and MCP probe call.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/config-workbook-author/<run_id>.md`
- **JSON envelope:** `docs/reports/config-workbook-author/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

The JSON envelope MUST embed:

- `sections.section_1.org_profile` — Step 1 output.
- `sections.section_<N>.rows[]` for sections 2–10, each row carrying every field from Step 4.
- `deployment_order[]` — Step 5 ordered list.
- `rtm_rollup[]` — Step 9 rows.
- `descope_decisions_honored[]` — Step 3 audit trail.
- `persona_drift[]` — Step 7 mismatches.
- `automation_overlap[]` — Step 8 results.
- `dimensions_compared[]` and `dimensions_skipped[]` — see Scope Guardrails.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** the supplied backlog + fit-gap + (optional) process-flow + the live-org probes declared in Steps 1, 7, 8. No web search, no other-org data sources.
- **No new project dependencies:** if a consumer asks for Excel / Smartsheet / Confluence output, refer to `skills/admin/agent-output-formats` for conversion paths. Do NOT install anything in the consumer's project.
- **No silent dimension drops:** dimensions skipped or partial get recorded in `dimensions_skipped[]` with `state: count-only | partial |

## Current non-goals excerpt

- Does not deploy metadata, does not modify the backlog or fit-gap files in place.
- Does not invent rows for stories not in the backlog.
- Does not estimate effort in hours / person-days.
- Does not assign rows to humans by name — uses persona / role.
- Does not auto-chain to any builder agent — workbook rows recommend; humans invoke.
- Does not produce Excel / Smartsheet / Confluence formats natively (defer to `skills/admin/agent-output-formats`).
- Does not bypass descope decisions — `REFUSAL_DESCOPE_BREACH` is the guard.
- Does not author rows whose `recommended_agent` doesn't exist on the runtime roster.
- Does not probe orgs other than `target_org_alias`.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
