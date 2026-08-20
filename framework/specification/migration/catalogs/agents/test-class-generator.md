# V2 Migration Profile: `test-class-generator`

## Current source

- Path: `agents/test-class-generator/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `False`
- Modes: `single`

## Current purpose

Generates a bulk-safe Apex test class for a target class, targeting ≥ 85% code coverage, using the canonical test factories in `templates/apex/tests/`. Produces positive, negative, bulk (200-record), and non-admin (`System.runAs`) scenarios by default. Stubs HTTP callouts via `MockHttpResponseGenerator` when the target makes callouts. Output is ready to paste into the user's force-app tree.

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
| `source_path` | yes | `force-app/main/default/classes/AccountService.cls` |
| `target_coverage_pct` | no (default 85) | `90` |
| `include_bulk_test` | no (default true) | `false` for utility classes |

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

1. **Summary** — target class, public method count, scenarios generated, estimated coverage %.
2. **Test class** — fenced code block labelled with the target path `force-app/main/default/classes/<Source>_Test.cls` + its `-meta.xml`.
3. **Coverage gaps** — methods not covered + why.
4. **Dependencies to deploy** — template files the test depends on (`TestDataFactory`, etc.) that the user must have already deployed.
5. **Process Observations** — peripheral signal noticed while reading the source.
   - **Healthy** — target uses `with sharing` correctly; existing `<Object>_Test` already exists as scaffold; clean separation between data construction and assertions; method signatures are simple/test-friendly.
   - **Concerning** — target invokes `Database.executeBatch(this)` from a method (recursion in test risk); target performs DML on Setup objects + non-Setup objects in same method (cite `mixed-dml-and-setup-objects`); target uses `Datetime.now()` inline (cite `timezone-and-datetime-pitfalls`); target hits `@AuraEnabled` and `WITHOUT SHARING` together — flag for security re-check.
   - **Ambiguous** — runAs persona unclear (no obvious permission-set constraints); whether bulk path triggers governor-limit assertions; whether mock callouts need a sequence of failures-then-success.
   - **Suggested follow-up agents** — `apex-refactorer` if untestable code shape (private methods used as DUT); `security-scanner` if FLS/CRUD gaps appeared; `score-deployment` pre-deploy.
6. **Citations** — skill + template ids.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/test-class-generator/<run_id>.md`
- **JSON envelope:** `docs/reports/test-class-generator/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions: `happy-path`, `bulk-200`, `runAs-non-admin`, `negative-path`, `callout-mock`, `governor-stress`, `recursio

## Current non-goals excerpt

- Does not refactor the source class — that is the `apex-refactorer` agent.
- Does not run the tests — produces a test class the user deploys.
- Does not use hardcoded record ids.
- Does not silently raise coverage thresholds — stops at `target_coverage_pct`.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
