# V2 Migration Profile: `data-model-reviewer`

## Current source

- Path: `agents/data-model-reviewer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Reviews the data model of a target domain (a parent object + its descendants, or a list of related objects): relationship patterns (Lookup vs Master-Detail), cross-object rollups, External ID strategy, junction objects, data-growth forecast, and candidate indexes. Produces a health report scored against `skills/data/data-model-design-patterns`, `skills/data/external-id-strategy`, and `skills/data/roll-up-summary-alternatives`.

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
| `root_object` | yes | `Opportunity` |
| `include_related` | no | comma-separated list; else inferred from `EntityDefinition` relationships |
| `target_org_alias` | yes |

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

1. **Summary** — root object, related count, max severity, confidence.
2. **Domain graph** — ASCII diagram (nodes + edges with relationship type).
3. **Findings table** — per object + per relationship.
4. **Rollup analysis** — rollup counts + conflict notes.
5. **Growth forecast** — object → projected row count in 12 months.
6. **Index recommendations.**
7. **Process Observations**:
   - **What was healthy** — clean External ID usage, consistent relationship naming, rollup discipline.
   - **What was concerning** — objects on the growth curve without partitioning strategy, MD-lookup confusion, 4+ hop queries implied by downstream flows.
   - **What was ambiguous** — relationships the agent couldn't confirm are used (ChildRelationships with no SOQL references).
   - **Suggested follow-up agents** — `object-designer` (for new objects suggested by consolidation), `field-impact-analyzer` for the External ID rollout, `audit-router --domain sharing` if cascade behavior is unclear.
8. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/data-model-reviewer/<run_id>.md`
- **JSON envelope:** `docs/reports/data-model-reviewer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

### Dimensions (Wave 10 contract)

The agent's envelope MUST place every dimension below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `object-design` | Standard vs custom, record-type usage, fields |
| `relationships` | Lookup vs master-detail vs junction |
| `sharing-posture` | OWD + sharing rules + teams |
| `indexes` | Custom indexes, skinny tables, LDV markers |
| `history-tracking` | Field History + Audit Trail configuration |
| `external-id-coverage` | Upsert-ready external IDs per integration |
| `validation-rule-hygiene` | VR count, bypass pattern compliance |

## Current non-goals excerpt

- Does not modify relationships.
- Does not design new objects (that's `object-designer`).
- Does not analyze sharing cascading (that's `audit-router --domain sharing`).
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
