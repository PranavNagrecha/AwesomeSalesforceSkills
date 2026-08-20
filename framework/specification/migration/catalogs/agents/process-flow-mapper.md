# V2 Migration Profile: `process-flow-mapper`

## Current source

- Path: `agents/process-flow-mapper/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `False`
- Modes: `single`

## Current purpose

Given a process narrative, transcript, or set of as-is/to-be requirements, produces a **swim-lane-ready process flow** for Salesforce — annotated with the canonical automation-tier syntax (`[FLOW] [APEX] [APPROVAL] [PLATFORM_EVENT] [INTEGRATION] [MANUAL]`) so an admin/developer can immediately read which step lives in which surface.

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
| `process_narrative_path` | yes | path to a markdown file describing the process; can be transcript, problem statement, as-is/to-be document, or hand-authored narrative |
| `process_kind` | yes | `as-is-only` \| `to-be-only` \| `as-is-to-be` \| `green-field` |
| `process_label` | yes | one-sentence label, e.g. "Quote-to-Cash for SaaS subscriptions" — bounds the flow |
| `backlog_path` | no | when supplied, the agent overlays `story_id`s onto each step (handoff to `/draft-stories` output) |
| `target_org_alias` | no | when supplied, runs `automation-graph-for-sobject` per object referenced to surface existing automation overlap |
| `personas_supplied` | no | persona inventory mapping persona → PSG / Profile / record-type / list view; if absent, the agent infers and flags |
| `surfaces_in_scope` | no | comma-separated list narrowing the flow to specific Salesforce surfaces, e.g. `sales-cloud,experience-cloud` |

If `process_narrative_path` is missing, vague, or under 4 distinct steps after parsing, refuse.

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

1. **Summary** — process label, step count, swim-lane count, tier distribution, story coverage (if backlog supplied), confidence (HIGH/MEDIUM/LOW).
2. **Swim-lane diagram** — markdown-rendered swim-lane (one column per lane, rows by ordering) per `skills/admin/process-flow-as-is-to-be`. Each cell carries `[TIER]` tag + step_id.
3. **Step inventory** — every step with `step_id`, `lane`, `tier`, `actor`, `object`, `action`, `data_passed`, `latency`, `nfr_class`, `story_id` (if backlog supplied), `source_quote`.
4. **Handoff catalog** — every handoff with `from_lane → to_lane`, `from_tier → to_tier`, `data_payload`, `latency`, `recommended_agents[]`, `recommended_skills[]`, `decision_tree_branch`.
5. **As-is vs to-be delta** (when `process_kind = as-is-to-be`) — added / removed / changed steps + tier shifts.
6. **Process Observations**:
   - **What was healthy** — clean lane separation, every integration has a pattern, every approval has an A, no over-stretching of `[FLOW]`.
   - **What was concerning** — missing accountable role, tier mismatches, integrations without patterns, cross-cloud without ADR, > 60% as-is/to-be delta.
   - **What was ambiguous** — steps where two tiers are plausible, integration patterns where two trees apply.
   - **Suggested follow-up agents** — `/build-flow` for `[FLOW]` lanes, `/plan-bulk-migration` for integration handoffs, `/catalog-integrations` to register external systems, `/audit-router --domain sharing` for sharing crossings, `/architect-perms` for new persona PSGs, `/author-config-workbook` to compile final admin handoff.
7. **Citations** — every skill, decision tree, probe, and MCP probe call.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/process-flow-mapper/<run_id>.md`
- **JSON envelope:** `docs/reports/process-flow-mapper/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

The JSON envelope MUST embed every step + handoff as structured objects:

```json
{
  "step_id": "S-014",
  "lane": "Sales Manager (PSG: Sales_Manager_PSG)",
  "tier": "FLOW",
  "actor": "Sales Manager",
  "object": "Opportunity",
  "action": "Submit for discount approval",
  "data_passed": "Opportunity.Id, Discount__c",
  "latency": "sync",
  "nfr_class": [],
  "story_id": "STORY-007",
  "decision_tree_branch": "automation-selection.md#approval-flow"
}
```

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** the supplied narrative + (optionally) the live-org `automation-graph-for-sobject` probe + (optionally) the supplied backlog. No web search, no other-system data sources.
- **No new project dep

## Current non-goals excerpt

- Does not deploy flows, does not generate Flow XML, does not write Apex.
- Does not invent process steps not supported by the narrative.
- Does not estimate hours / effort for any step.
- Does not auto-chain to `/build-flow`, `/plan-bulk-migration`, or `/author-config-workbook` — recommends in Process Observations only.
- Does not produce Visio / Lucidchart / BPMN XML output natively (defer to `skills/admin/agent-output-formats`).
- Does not assign owners by name — RACI uses role labels.
- Does not classify a `[FLOW]` step as `[APEX]` because the narrative said so — verifies against `automation-selection.md`.
- Does not probe orgs other than `target_org_alias` (when supplied).

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
