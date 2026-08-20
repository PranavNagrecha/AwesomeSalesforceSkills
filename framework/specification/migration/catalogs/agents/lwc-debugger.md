# V2 Migration Profile: `lwc-debugger`

## Current source

- Path: `agents/lwc-debugger/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `False`
- Modes: `single`

## Current purpose

Diagnoses a live LWC failure — a stack trace, "Unknown error", a wire that never populates, a silently empty render, a quick action that won't close, a datatable cell that displays raw JSON — and returns the most likely root cause with the exact file / line to change. Consumes a symptom description, the bundle, and optionally a browser console snippet / network HAR / Lightning Inspector capture. Produces a ranked hypothesis list with diagnostic commands, then the recommended fix.

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
| `bundle_path` | yes | `force-app/main/default/lwc/accountDetail` |
| `symptom` | yes | Free-text description of the observed failure. ≥ 10 words. Examples: "record page tile renders blank with no console error, but wire payload logs correctly in `handleRecord`" / "quick action opens but `Close` button does nothing" |
| `error_text` | no | Stack trace, `ShowToastEvent` body, `console.error(...)` line, Lightning Inspector event payload, HAR excerpt |
| `reproduction_context` | no | `record-page` / `flow-screen` / `quick-action` / `experience-cloud` / `local-jest` — where the bug reproduces |
| `recently_changed` | no | Path(s) / commit SHA(s) of the most recent edits to the bundle, if known |
| `allow_transient_edits` | no | default `false`. When `true`, the agent may propose (never apply) temporary `console.log` / `debugger;` instrumentation listed as a separate "Diagnostic Probe" block |

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

1. **Symptom classification** — axis + 1-sentence rephrasing.
2. **Ranked hypotheses** — top 3, each with skill citation and a 1-sentence "why this matches."
3. **Diagnostic probes** — read-only commands / console expressions to run **now** to confirm the top hypothesis. Labeled per probe kind (grep / console / checker / network / transient).
4. **Proposed fix** — before/after code block for the top-ranked hypothesis.
5. **Related likely-broken patterns** — bundle-local sibling smells the investigation surfaced.
6. **Confidence** — HIGH if the symptom text and a skill-local checker both point to the same root cause; MEDIUM if the hypothesis is the best-fit but unverified; LOW if the symptom is ambiguous and the user needs to run probes first.
7. **Process Observations**:
   - **Healthy** — bundle already uses `lwc:ref`, tagged console calls, `refreshGraphQL` for GraphQL wires — signals the user has read the skills.
   - **Concerning** — bundle mixes `this.template.querySelector` with `lwc:ref`, or mixes `refreshApex` and `refreshGraphQL` inconsistently.
   - **Ambiguous** — symptom is "intermittent" with no reproduction steps; the agent can only propose probes, not a definitive fix.
   - **Suggested follow-up agents** — `lwc-auditor` (full static pass once the immediate bug is fixed), `lwc-builder` (if the fix implies a rewrite), `apex-refactorer` (if a backing `@AuraEnabled` method is the real offender), `security-scanner` (if the probe uncovered a CSP / Locker finding).
8. **Citations** — skill ids, template paths, and any skill-local checker scripts invoked.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/lwc-debugger/<run_id>.md`
- **JSON envelope:** `docs/reports/lwc-debugger/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** the bundle on disk + the user-supplied `symptom` / `error_text` / `reproduction_context`. The agent does not fetch live org state; any hypothesis requiring org introspection is labeled as a probe for the user to run.
- **No new project dependencies:** diagnostic probes are grep + stdlib Python + browser console. Never instructs the user to `npm install` / `pip install` anything.
- **No destructive suggestions:** the agent may propose diffs but never writes to the bundle. Transient instrumentation is allowed only when `allow_transient_edits=true` and is explicitly labeled as a paste-and-revert probe.
- **No silent dimension drops:** if the symptom straddles multiple axes (e.g. "slow **and** blank"), the envelope records each axis with `state: primary | 

## Current non-goals excerpt

- Does not modify bundle files. Proposes diffs.
- Does not run the bundle, deploy, or run Jest. Probes are user-executed.
- Does not convert its output beyond `markdown` or `json` — if a consumer asks for another format, refer them to `skills/admin/agent-output-formats` for conversion paths.
- Does not replace `lwc-auditor` for a full bundle audit.
- Does not replace `lwc-builder` for net-new authoring.
- Does not auto-chain to other agents.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
