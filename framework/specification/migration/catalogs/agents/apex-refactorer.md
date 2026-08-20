# V2 Migration Profile: `apex-refactorer`

## Current source

- Path: `agents/apex-refactorer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `False`
- Modes: `single`

## Current purpose

Takes an existing Apex class the user points at, compares it against the canonical patterns in `templates/apex/`, and returns a refactored version plus a test class. Targets: trigger bodies lifted into `TriggerHandler`, raw DML lifted to `BaseService`, raw SOQL lifted to `BaseSelector`, ad-hoc `HttpCallout` lifted to `HttpClient`, `System.debug` calls replaced with `ApplicationLogger`, and CRUD/FLS enforcement inserted via `SecurityUtils`. The agent produces a review-ready diff and a deploy-safe test class — it never writes to the target org.

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
| `source_path` | yes | `force-app/main/default/classes/AccountTrigger.cls` |
| `related_paths` | no | helper classes / existing test class paths |
| `target_org_alias` | no | if set, the agent also calls `validate_against_org("apex/trigger-framework", target_org=...)` |

If `source_path` is missing or doesn't exist, STOP and ask the user. Never guess at the path.

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

Return one markdown document with these sections:

1. **Summary** — shape classified, templates applied, confidence (HIGH/MEDIUM/LOW).
2. **Refactored files** — one code block per generated file, using fenced code blocks labelled with the target path. Include:
   - The refactored class
   - Any new dependency classes (e.g. a new `<Object>TriggerHandler.cls` if we lifted a trigger body)
   - The test class
3. **Diff summary** — bullet list of every transformation applied, each citing the skill / template the transformation came from.
4. **Risk notes** — ambiguities, pre-existing bugs, bulkification concerns, assumptions.
5. **Process Observations** — peripheral signal noticed during the refactor, separate from the direct diff.
   - **What was healthy** — base-class / framework already partially adopted; existing test class covers > 80% before refactor; existing Selector-equivalents in the codebase that the new shape can extend; consistent naming convention.
   - **What was concerning** — sharing keyword inferred but ambiguous (cite `apex-with-without-sharing-decision`); hardcoded IDs / secrets discovered (cite the matching skill); SOQL inside loops the agent could not safely rewrite; dynamic SOQL with string concatenation requiring `apex-dynamic-soql-binding-safety` follow-up; recursion guard absent on a multi-event handler.
   - **What was ambiguous** — whether `WITHOUT SHARING` is justified; whether existing Selector should be extended or a new one introduced; whether a Service/Domain/Selector split is warranted given current size.
   - **Suggested follow-up agents** — `security-scanner` (post-refactor FLS/CRUD verification); `soql-optimizer` (when new Selector emitted); `test-class-generator` (when test-class generation deferred); `trigger-consolidator` (when refactor reveals additional triggers on the same SObject); `score-deployment` (pre-deploy gate).
6. **Citations** — ids of every skill, template, and decision-tree branch consulted.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/apex-refactorer/<run_id>.md`
- **JSON envelope:** `docs/reports/apex-refactorer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a ca

## Current non-goals excerpt

- Does not deploy to an org.
- Does not modify files outside `source_path` + `related_paths`.
- Does not migrate from `fflib` to this repo's lightweight enterprise pattern without explicit user confirmation.
- Does not invent new Apex patterns — every change cites a template or a skill.
- Does not auto-chain to `security-scanner` or `soql-optimizer`; recommends them in the output instead.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
