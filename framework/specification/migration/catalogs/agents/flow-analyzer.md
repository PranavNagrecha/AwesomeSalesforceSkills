# V2 Migration Profile: `flow-analyzer`

## Current source

- Path: `agents/flow-analyzer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

For a given Flow or sObject, decides whether the automation is in the right tool per `standards/decision-trees/automation-selection.md` (Flow vs Apex vs Agentforce), reviews existing Flow definitions for bulkification and fault-path compliance against `skills/flow/flow-bulkification/SKILL.md` and `templates/flow/FaultPath_Template.md`, and flags co-existing Apex triggers or Process Builder that could double-fire.

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
| `flow_path` or `object_api_name` | yes (one of) | `force-app/main/default/flows/X.flow-meta.xml` OR `Lead` |
| `target_org_alias` | no | enables `list_flows_on_object` for org-side cross-check |

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

1. **Summary** — flow(s) analyzed, verdict distribution, confidence.
2. **Per-flow report** — verdict, decision-tree branch, findings table, recommended fixes.
3. **Co-existence section** — if triggers + flows overlap on the same event.
4. **Process Observations** — peripheral signal noticed while analyzing, separate from the direct verdicts. Each observation cites its evidence (flow name, element id, MCP probe count).
   - **Healthy** — e.g. fault paths are present on every DML element; subflows already follow `Subflow_Pattern.md`; collection variables are typed; `list_flows_on_object` shows no duplicate record-triggered flows on the same event.
   - **Concerning** — e.g. the object has multiple active record-triggered flows on the same event (ordering is non-deterministic at scale); a Screen Flow performs DML inside a loop without chunking; no active error-email recipient for the org.
   - **Ambiguous** — e.g. a flow whose verdict depends on record volume the agent can't see without a target org; a subflow called from multiple parents with differing input contracts.
   - **Suggested follow-ups** — `trigger-consolidator` on any `COEXISTENCE_RISK` finding; `apex-refactorer` + `test-class-generator` on `MIGRATE_TO_APEX` verdicts; `agentforce-builder` on `MIGRATE_TO_AGENTFORCE` verdicts.
5. **`dimensions_skipped[]`** — every audit dimension touched but not fully checked (e.g. test-coverage counted but not loaded; CPU-budget probed only via static estimate, not real run-stats); each entry uses `state: count-only | partial | not-run` per `agents/_shared/DELIVERABLE_CONTRACT.md`.
6. **Citations** — decision-tree branch, skill ids, template paths, probe ids, MCP tool names.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/flow-analyzer/<run_id>.md`
- **JSON envelope:** `docs/reports/flow-analyzer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Current non-goals excerpt

- Does not modify the flow XML.
- Does not auto-run `trigger-consolidator` — recommends it.
- Does not make judgments about "Flow is bad" / "Apex is bad" — follows the decision tree.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
