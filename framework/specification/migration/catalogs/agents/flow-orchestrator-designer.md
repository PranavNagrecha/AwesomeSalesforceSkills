# V2 Migration Profile: `flow-orchestrator-designer`

## Current source

- Path: `agents/flow-orchestrator-designer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
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
| `scenario_summary` | design-mode only | "3-stage contract review: legal, procurement, customer sign-off; SLA 5 business days; recallable by originator" |
| `primary_object` | design-mode | `Contract`, `Opportunity`, `Custom__c` |
| `audit_scope` | audit-mode only | `org` \| `orchestration:<DeveloperName>` |
| `license_confirmed` | no | `true` to skip the edition-check refusal; default `false` |

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

1. **Summary** — scenario summary, stage count, step count, confidence.
2. **Stage/step/transition table**.
3. **Work-item assignment matrix**.
4. **Subflow spec list** — one paragraph each.
5. **Deployment order + activation checklist**.
6. **Process Observations**:
   - **What was healthy** — clean queue setup, existing Screen Flows reusable as steps, documented SLA targets.
   - **What was concerning** — proposed assignees that map to inactive queues, steps that should really be background but were specified as interactive (or vice versa), SLAs that no one owns operationally.
   - **What was ambiguous** — recall semantics the business hasn't decided on; whether a stage is truly linear or actually has parallel branches.
   - **Suggested follow-up agents** — `flow-builder` (for each subflow), `permission-set-architect` (orchestrator runtime permission), `automation-migration-router` with `--source-type=approval_process` (if this orchestration replaces a legacy approval process).
7. **`dimensions_skipped[]`** — every dimension touched but not fully designed (e.g. SLA proposed but no operational owner identified; recall semantics deferred); each entry uses `state: count-only | partial | not-run` per `agents/_shared/DELIVERABLE_CONTRACT.md`.
8. **Citations**.

Audit mode:

1. **Summary** — orchestrations inventoried, P0/P1/P2 counts, overall confidence.
2. **Findings table** — per orchestration × anti-pattern.
3. **Work-item concentration report** — top-10 users by open work item count.
4. **Stalled work item list** — age > 30 days with no movement.
5. **Process Observations** — as above, with `flow-analyzer` as a candidate follow-up for any orchestration with high work-item throughput.
6. **`dimensions_skipped[]`** — every audit dimension touched but not fully checked (e.g. work-item age sampled but not exhaustively scanned); each entry uses `state: count-only | partial | not-run` per `agents/_shared/DELIVERABLE_CONTRACT.md`.
7. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/flow-orchestrator-designer/<run_id>.md`
- **JSON envelope:** `docs/reports/flow-orchestrator-designer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion 

## Current non-goals excerpt

- Does not emit full subflow XML — hand each subflow spec to `flow-builder`.
- Does not deploy orchestrations.
- Does not reassign or cancel in-flight work items.
- Does not migrate from Approval Process — use `automation-migration-router --source-type=approval_process`.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
