# V2 Migration Profile: `story-drafter`

## Current source

- Path: `agents/story-drafter/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `False`
- Modes: `single`

## Current purpose

Given a discovery transcript, problem statement, or set of business requirements, produces a backlog of INVEST-conformant Salesforce user stories. Every story is sized (S/M/L/XL by complexity), MoSCoW-prioritized, equipped with given/when/then acceptance criteria, and tagged with `recommended_agents[]` + `recommended_skills[]` so the admin or developer who picks it up knows exactly which run-time agent to invoke next (`/design-object`, `/architect-perms`, `/build-flow`, `/build-lwc`, `/preflight-load`, `/design-duplicate-rule`, etc.).

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
| `discovery_artifact_path` | yes | path to a transcript, a markdown problem statement, a meeting summary, or a list of requirements (one per bullet) |
| `discovery_artifact_kind` | yes | `transcript` \| `problem-statement` \| `requirements-list` \| `process-narrative` |
| `feature_scope` | yes | one-sentence scope label, e.g. "Account-team automation for Mid-Market accounts" — used to bound the backlog |
| `target_org_alias` | no | when supplied, the agent calls a fit-gap probe (license + similar-object check) per story to elevate fit-tier confidence |
| `personas_supplied` | no | known persona list with PSG anchors; if absent, the agent infers and flags inferred personas as ambiguities |
| `release_capacity_points` | no | story-points capacity per release window — used by MoSCoW 60% rule and to flag overcommit |
| `priority_overrides` | no | map of `{requirement_id: priority}` — caller-supplied overrides applied AFTER MoSCoW pass |

If `discovery_artifact_path` is empty, vague, or under 5 distinct requirements, STOP and ask clarifying questions (see Escalation).

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

1. **Summary** — feature scope, story count, point total, MoSCoW distribution (M/S/C/W), confidence (HIGH/MEDIUM/LOW).
2. **Persona anchors** — table of every persona used + Profile + PSG + record-type + list view anchor.
3. **Story backlog** — every story with full body, AC, sizing, fit tier, NFR class, training impact, MoSCoW, `recommended_agents[]`, `recommended_skills[]`. Group by epic.
4. **Requirements Traceability Matrix** — Step 8 rows.
5. **MoSCoW capacity check** — 60% rule result + WSJF descope candidates if overcommitted.
6. **Process Observations**:
   - **What was healthy** — clean discovery artifact, well-anchored personas, clear scope boundary, license fit, etc.
   - **What was concerning** — XL stories not split, > 60% Must-have overcommit, persona gaps, license gaps, missing AI use-case assessment.
   - **What was ambiguous** — inferred personas, requirements with multiple plausible owners, cross-cloud splits.
   - **Suggested follow-up agents** — `/run-fit-gap` for the L/XL stories, `/map-process-flow` for cross-system stories, `/author-config-workbook` to compile final admin handoff, plus the agents named in `recommended_agents[]`.
7. **Citations** — every skill, decision tree, and probe consulted.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/story-drafter/<run_id>.md`
- **JSON envelope:** `docs/reports/story-drafter/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

The JSON envelope MUST embed every story as a structured object per `skills/admin/user-story-writing-for-salesforce` handoff shape:

```json
{
  "story_id": "STORY-001",
  "epic": "Account-Team Automation",
  "title": "Sales Manager assigns Account Team for Mid-Market account",
  "body": {
    "as_a": "Sales Manager (PSG: Sales_Manager_PSG)",
    "i_want": "to assign an Account Team when an Opportunity is created on a Mid-Market account",
    "so_that": "all team members get visibility within 2 minutes"
  },
  "acceptance_criteria": [{"id": "AC-001", "scenario": "...", "given": "...", "when": "...", "then": "..."}],
  "size": "M",
  "fit_tier": "Config",
  "nfr_class": ["performance"],
  "training_impact": "email-blast",
  "moscow": "Must",
  "moscow_algorithmic": "Must",
  "moscow_overridden": false,
  "wsjf_score": 7.4,
  "recommended_agents": ["flow-builder", "permission-set-architect"],
  "recommended_skills": ["admin/permission-set-architecture", "flow/record-triggered-flow-patterns"],
  "rtm_req_ids": ["REQ-014", "REQ-015"]
}
```

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** the supplied discovery artifact +

## Current non-goals excerpt

- Does not estimate stories in hours or person-days — sizes are S/M/L/XL only.
- Does not assign owners by name or capacity.
- Does not push to Jira / ADO / Linear / any backlog tool.
- Does not invent requirements beyond what the artifact supplies.
- Does not auto-chain to `/run-fit-gap`, `/map-process-flow`, or `/author-config-workbook` — these are recommended in Process Observations but never auto-invoked.
- Does not write code, metadata, or any artifact for the executing agents — its output IS the spec the executing agents will read.
- Does not deploy anything to any org.
- Does not draft NFR text — names the NFR class only; defers to `architect/nfr-definition-for-salesforce` for content.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
