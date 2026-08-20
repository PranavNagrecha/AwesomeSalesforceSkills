# V2 Migration Profile: `soql-optimizer`

## Current source

- Path: `agents/soql-optimizer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `False`
- Modes: `single`

## Current purpose

Scans a user-specified scope (file, folder, or entire `force-app/`) for SOQL anti-patterns — queries inside loops, missing selective filters, SELECTing unused fields, filtering on non-indexed fields at high volume, missing user-mode enforcement — and produces ranked fix recommendations with before/after code. Consults data-skew and LDV skills for high-volume scenarios.

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
| `scope_path` | yes | `force-app/main/default/classes/` or a single `.cls` |
| `expected_record_count` | no | `2_000_000` — used to escalate findings for LDV |
| `target_org_alias` | no | if set, call `describe_org` to grab record counts for sObjects referenced |

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

1. **Summary** — files scanned, queries analyzed, findings by severity.
2. **Findings table** — one row per finding: file, line, severity, finding code, one-line description.
3. **Per-finding fix** — each P0 and P1 gets a before/after code block and a citation.
4. **Centralization recommendation** — if applicable.
5. **Process Observations** — peripheral signal noticed while scanning, separate from the direct findings. Each observation cites its evidence (file, query count, sObject name).
   - **Healthy** — e.g. repo already has a `<Object>Selector extends BaseSelector` pattern in place for the most-queried objects; queries consistently use `WITH USER_MODE` even on classes whose API version does not yet default to it; `LIMIT` clauses present on every paginated query.
   - **Concerning** — e.g. more than 3 `SELECT` on a single sObject are distributed across unrelated classes (centralization gap); dynamic-SOQL string concatenation patterns that the agent can't safely rewrite; use of `Database.getQueryLocator` outside of Batch contexts.
   - **Ambiguous** — e.g. a query that is `query-in-loop` only in a code path guarded by a flag the agent can't evaluate; a non-selective WHERE where the agent cannot confirm live record count.
   - **Suggested follow-ups** — `apex-refactorer` when centralization is needed (to introduce a Selector); `security-scanner` on any `no-security` P1 finding; `test-class-generator` when new Selectors are created.
6. **Citations** — skill + template ids.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/soql-optimizer/<run_id>.md`
- **JSON envelope:** `docs/reports/soql-optimizer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions: `query-in-loop`, `selectivity`, `field-projection`, `security-clause`, `dynamic-soql-safety`, `pagination`, `aggregation`, `relationship-shape`, `

## Current non-goals excerpt

- Does not modify files. All output is review-only.
- Does not deploy custom indexes — only recommends.
- Does not run `sf data query` — uses only static analysis + optional `describe_org`.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
