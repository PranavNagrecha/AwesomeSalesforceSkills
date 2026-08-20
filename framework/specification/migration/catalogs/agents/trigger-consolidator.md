# V2 Migration Profile: `trigger-consolidator`

## Current source

- Path: `agents/trigger-consolidator/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `False`
- Modes: `single`

## Current purpose

Finds every Apex trigger on a given sObject across the user's `force-app` tree, checks the target org (if connected) for additional triggers, and produces a consolidation plan that lifts them all into a single `<Object>TriggerHandler extends TriggerHandler` class using the canonical framework from `templates/apex/TriggerHandler.cls` + `templates/apex/TriggerControl.cls`. The output is a migration patch plus a deactivation order so nothing is live-broken mid-migration.

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
| `object_api_name` | yes | `Account`, `Opportunity`, `Custom_Object__c` |
| `force_app_root` | yes | `force-app/main/default` |
| `target_org_alias` | no | if set, the agent also queries the org for additional triggers |

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

1. **Discovery** — every trigger found (local + org), with event matrix.
2. **Adjacent automation** — Flows, PB, WF, Approval, VR, DR, AR enumerated via `automation-graph-for-sobject` probe. Order of execution implications called out.
3. **Audit signals** (12 catalog rows — flag any present):

| Signal | Severity |
|---|---|
| Multiple triggers on same SObject | P0 (consolidate) |
| Trigger with inline business logic (no handler) | P0 |
| Trigger using `Trigger.isExecuting` recursion guard instead of framework | P1 |
| Trigger missing kill-switch wiring (cite `apex-trigger-bypass-and-killswitch-patterns`) | P1 |
| Trigger handler not extending `TriggerHandler` template | P1 |
| Trigger calls `@future` mid-handler (cite `apex-future-method-patterns`) | P2 |
| Trigger does DML on same SObject (mixed-DML / recursion risk) | P1 |
| Trigger does DML on Setup objects (cite `mixed-dml-and-setup-objects`) | P1 |
| Process Builder / WF Rule on same SObject + events | P1 (cite `automation-selection.md`) |
| Record-Triggered Flow on same events (cite `trigger-and-flow-coexistence`) | P1 |
| Trigger uses `try {} catch (Exception e) {}` empty-swallow | P0 |
| Managed-package trigger present | flag, exclude |

4. **Proposed consolidation** — the new handler class + new trigger file, fenced by target path.
5. **Migration steps** — numbered deployment sequence.
6. **Risk notes** — triggers that touch the same event in conflicting ways, order-of-execution concerns, any handler that uses `Trigger.isExecuting` gymnastics the framework handles differently.
7. **Process Observations**.
   - **Healthy** — only one trigger on the SObject already; framework already partially adopted; logging via `Application_Log__c` already in place; tests use `TestDataFactory`.
   - **Concerning** — Flow/PB/WF Rule + trigger overlap on same events (cite probe output); managed-package trigger present (excluded but flagged); kill-switch missing on a high-traffic handler.
   - **Ambiguous** — whether to consolidate the new handler with NPSP TDTM (cite `npsp-trigger-framework-extension`); whether async-offload should be inserted as part of consolidation.
   - **Suggested follow-ups** — `flow-analyzer` (when adjacent Flows discovered); `apex-refactorer` (after consolidation, to lift business logic in handler bodies); `test-class-generator` (for the new handler); `security-scanner` (post-consolidation FLS check); `score-deployment` (pre-deploy gate).
8. **Citations** — skill ids + template paths + probe id.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/trigger-consolidator/<run_id>.md`
- **JSON envelope:** `docs/reports/trigger-consolidator/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline an

## Current non-goals excerpt

- Does not refactor business logic inside the triggers — preserves it verbatim.
- Does not run the security-scanner or soql-optimizer — recommends them.
- Does not deploy anything.
- Does not modify managed-package triggers.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
