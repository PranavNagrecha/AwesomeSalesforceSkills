# V2 Migration Profile: `flow-builder`

## Current source

- Path: `agents/flow-builder/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.2.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Given a business requirement, designs the correct Flow: Flow type (record-triggered / scheduled / auto-launched / screen / orchestration), trigger configuration, element-by-element plan, fault path, subflow decomposition, bulkification safeguards, and a test design. Output is a design document + optional Flow XML skeleton the user drops into Flow Builder.

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
| `requirement` | yes | "When a Case is created on an Account with tier=Platinum, route to the Platinum Support queue and notify the account owner" |
| `target_org_alias` | yes | live-org probe prevents duplicate automation |
| `target_object` | yes (if implied by the req.) | `Case` |
| `trigger_context` | no | `before-save` \| `after-save` \| `scheduled` \| `screen` \| `autolaunched` — inferred if omitted |
| `expected_volume` | no | `small` / `medium` / `high` — drives async + bulkification emphasis |

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

1. **Summary** — Flow type chosen, decision-tree branch cited, confidence (HIGH/MEDIUM/LOW).
2. **Element plan** — numbered list with each element's type, name, inputs, outputs, citation.
3. **Resource plan** — variables / constants / formulas / templates / choices, each typed and cited per `skills/flow/flow-resource-patterns`.
4. **Subflow plan** — subflow list + what each does + why it earns a subflow.
5. **Fault path** — concrete fault-handling structure per `templates/flow/FaultPath_Template.md`, with the canonical sink (Application_Log__c / Platform Event / EmailAlert) named per `skills/flow/flow-error-monitoring`.
6. **Bulkification + perf + LDV notes** — every bottleneck from Step 5; explicit budget per `flow-governor-limits-deep-dive`.
7. **Transactional / post-commit / rollback notes** — output of Step 5.5.
8. **Test matrix** — table from Step 6.
9. **Lifecycle + deployment + debug block** — owner, version, retirement criteria, deploy bundle, debug instructions (Step 7 deliverables).
10. **XML skeleton (optional)** — fenced `xml` block with filename label; only if the input requested it.
11. **Process Observations**:
    - **What was healthy** — existing flow patterns the org follows correctly (e.g. consistent VerbObject naming across the flow portfolio, fault paths sink to a single Application_Log__c).
    - **What was concerning** — competing automation (other flows, triggers, PB) on the same object, missing fault-handling patterns org-wide, inactive flows cluttering the object, no org-wide Flow error-email recipient (`skills/flow/flow-error-monitoring`), parent-record contention risk under bulk.
    - **What was ambiguous** — requirement gaps the agent filled with a default (always call them out), volume the agent cannot estimate without a target org probe, recall semantics if the requirement implied human review.
    - **Suggested follow-up agents** — `flow-analyzer` for post-deploy health, `apex-builder` + `apex-test-generator` for any invocable Apex the flow calls, `security-scanner` if the flow does callouts, `automation-migration-router` if Step 0 found legacy WFR/PB on the object, `flow-orchestrator-designer` if the requirement actually wants multi-stage human review.
12. **`dimensions_skipped[]`** — any dimension touched but not fully compared (e.g. test design counted but not generated, debug instructions referenced but not run); each entry uses `state: count-only | partial | not-run` per `agents/_shared/DELIVERABLE_CONTRACT.md`.
13. **Citations** — every skill / template / decision-tree / probe / MCP tool consulted.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/flow-builder/<run_id>.md`
- **JSON envelope:** `docs/reports/flow-builder/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** source excerpt truncated here; consult `agents/flow-builder/AGENT.md` in the implementation repository.

## Current non-goals excerpt

- Does not deploy the flow.
- Does not modify existing flows in the repo or the org.
- Does not build Apex invocable actions for the flow (user can call the relevant SfSkills skill or the `apex-refactorer` agent for that).
- Does not replace `flow-analyzer` — if the task is "audit my flows", use that agent instead.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
