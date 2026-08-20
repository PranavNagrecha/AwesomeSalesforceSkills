# V2 Migration Profile: `fit-gap-analyzer`

## Current source

- Path: `agents/fit-gap-analyzer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Given a backlog of user stories (from `/draft-stories` or hand-authored) and a target Salesforce org, classifies every story into one of five fit tiers — **Standard / Config / Low-Code / Custom / Unfit** — based on what the org actually has installed, licensed, and configured. Produces:

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
| `backlog_path` | yes | path to a story backlog markdown OR JSON envelope (story-drafter output, hand-authored Markdown table, or a CSV exported from Jira) |
| `backlog_format` | yes | `story-drafter-json` \| `markdown-table` \| `csv` |
| `target_org_alias` | yes | the org being fit-gapped (sandbox or production); analyzer refuses without one |
| `release_window` | no | release identifier (e.g. `R3-2026`) for tagging RTM rows |
| `assume_licenses` | no | list of license SKUs to assume present even if not detected (used when the org probe is on a sandbox missing parent-org licenses) |
| `descope_threshold` | no | `M` / `L` / `XL` — stories at this size or larger AND fit tier = Unfit are surfaced as descope candidates. Defaults to `L` |

If `target_org_alias` is missing, refuse — fit-gap without an org is just guesswork (the story-drafter already did that pass).

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

1. **Summary** — backlog name, story count, target org, license posture, MoSCoW distribution if present, overall confidence (HIGH/MEDIUM/LOW).
2. **Per-story scorecard** — one row per story with `story_id`, `title`, `persona`, `size`, `fit_tier`, `confidence`, `evidence` (cited org artifact or gap), `recommended_agent` (carry-through from backlog or newly suggested).
3. **Gap inventory** — 6 tables from Step 4.
4. **Effort-shape rollup** — Step 5 table + cross-cloud / NFR notes.
5. **Descope candidate list** — Step 6.
6. **Process Observations**:
   - **What was healthy** — license fit overall, persona reuse opportunities, automation already in place that stories can extend, mature naming convention, etc.
   - **What was concerning** — license gaps, > 30% Unfit stories, > 5 net-new objects in one release, missing AI use-case assessment, story-fit-tier vs decision-tree mismatch, missing automation governance.
   - **What was ambiguous** — stories where two tiers are plausible (Config vs Low-Code), persona anchors that don't yet exist as PSGs, gap items that could be solved by extending vs creating.
   - **Suggested follow-up agents** — `/architect-perms`, `/design-object`, `/build-flow`, `/audit-router --domain lightning_record_page`, `/audit-router --domain sharing`, `/plan-bulk-migration`, `/audit-router --domain record_type_layout`, `/audit-router --domain picklist` per gap category; `/author-config-workbook` once the project commits to descope/rescope decisions.
7. **Citations** — every skill, decision tree, probe, and MCP probe call.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/fit-gap-analyzer/<run_id>.md`
- **JSON envelope:** `docs/reports/fit-gap-analyzer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

The JSON envelope MUST embed:

- `dimensions_compared[]` — the dimensions the run actually evaluated.
- `dimensions_skipped[]` — see Scope Guardrails.
- `per_story_scorecard[]` — every story with tier, confidence, evidence, and `recommended_agents[]` carried through.
- `gap_inventory.{licenses, feature_flags, objects, fields, permissions, automation}[]` — Step 4 tables.
- `effort_shape` — Step 5 rollup.
- `descope_candidates[]` — Step 6.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** the supplied backlog + the live-org probe set declared in Step 1. No web search, no other-org data sources.
- **No new project dependencies:** if a consumer asks for Excel / PDF / Confluence output, refer them to `skills/admin/agent-output-formats`. Do NOT install anything in the consumer's project.
- **No sil

## Current non-goals excerpt

- Does not deploy gap-fix metadata, does not order licenses, does not modify the backlog file in place.
- Does not estimate effort in hours / person-days — sizing is S/M/L/XL only.
- Does not make a build-vs-buy recommendation (escalate to architecture review).
- Does not auto-chain to `/draft-stories`, `/map-process-flow`, or `/author-config-workbook` — recommends in Process Observations only.
- Does not invent stories that aren't in the backlog.
- Does not probe orgs other than `target_org_alias`.
- Does not classify a story as Unfit when a license override is plausible — surfaces the license gap and lets the steering committee decide.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
