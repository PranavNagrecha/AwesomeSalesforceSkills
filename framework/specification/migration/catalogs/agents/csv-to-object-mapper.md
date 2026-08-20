# V2 Migration Profile: `csv-to-object-mapper`

## Current source

- Path: `agents/csv-to-object-mapper/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Given a CSV file header (or a schema description), produces a mapping to an existing or new sObject: column → field decisions with type inference, naming per `templates/admin/naming-conventions.md`, External ID candidate identification, required-field detection, and a Data Loader CSV mapping file. The agent handles the specific case a Salesforce admin or BA faces 10× a year: "a partner sent me a spreadsheet, how do I load it?"

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
| `csv_header` | yes | comma-separated header line, OR a bullet list of column names with 1-2 sample values |
| `target_object` | no | `Account` \| `new:<ProposedName>` (if creating a new object) |
| `target_org_alias` | yes | `uat` — Step 1 describes the target object against it; the mapping table is not produced without one |
| `mode` | no | `map` (default — map to existing fields, create missing ones) \| `create-new-object` (design a new object from the CSV) |

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

1. **Summary** — mode, column count, new fields proposed, confidence.
2. **Mapping table** — CSV column → target field → type → justification.
3. **New fields to create** — fenced XML per field (for sfdx deployment).
4. **New object design** — only in `create-new-object` mode; spec + scaffold as in `object-designer`.
5. **Data Loader mapping file** — fenced block labelled with target filename.
6. **Pre-check** — required-field gaps, PII warnings.
7. **Process Observations**:
   - **What was healthy** — source data has an obvious primary key, column naming hints at clean semantics.
   - **What was concerning** — columns with embedded delimiters (common with copied Excel), columns whose names are identical to standard fields (collision risk), columns that look like compound values (full name, address).
   - **What was ambiguous** — columns where the agent guessed a type; flag each.
   - **Suggested follow-up agents** — `object-designer` (if more than half the columns implied a new object), `preflight-load` (before actually running the load).
8. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/csv-to-object-mapper/<run_id>.md`
- **JSON envelope:** `docs/reports/csv-to-object-mapper/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Current non-goals excerpt

- Does not read the CSV data itself (only the header + optional samples).
- Does not deploy new fields or objects.
- Does not run the data load.
- Does not auto-chain to `preflight-load`.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
