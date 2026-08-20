# V2 Migration Profile: `omni-channel-routing-designer`

## Current source

- Path: `agents/omni-channel-routing-designer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `True`
- Modes: `design, audit`

## Current purpose

Designs or audits an Omni-Channel routing configuration across Case, Chat/Messaging, and Lead. Produces queue topology, routing-config (push vs most-available vs skills-based vs external), capacity model per presence status, service channel mapping, and a bot-to-agent handoff plan. The agent either (a) greenfields a new Omni-Channel design from business inputs, or (b) audits an existing configuration against the capacity model and surfaces over-loaded presence statuses, skills gaps, and misconfigured declines.

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
| `target_org_alias` | yes for audit; optional for design | `uat` |
| `channels` | yes for design | `["case","chat","messaging","lead"]` |
| `business_hours_id` / `operating_hours_id` | no | used to bound routing windows |
| `peak_volume` | yes for design | interactions per channel per peak hour |
| `agent_count_and_skills` | yes for design | e.g. `{ "tier1": 40, "billing": 12, "spanish": 6 }` |

If `mode=audit` and `target_org_alias` is missing, STOP.

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

1. **Summary** — channels in scope, mode, top 3 risks.
2. **Capacity model** — per-channel table: target concurrent, agents needed, gap.
3. **Queue + routing topology** — ASCII/mermaid graph + per-routing-config table.
4. **Presence configuration** — statuses, capacities, decline behavior.
5. **Handoff plan** — bot → agent, fallback behavior.
6. **Audit findings** (audit mode only) — each with severity and rationale.
7. **Process Observations** per `AGENT_CONTRACT.md`:
   - **Healthy** — skills granularity matches agent skill matrix; presence decline set to `Busy`.
   - **Concerning** — queue sprawl, mismatched service channel capacity, missing overflow.
   - **Ambiguous** — agent skills not documented anywhere queryable.
   - **Suggested follow-ups** — `audit-router --domain case_escalation` if SLAs are undefined; `permission-set-architect` for Omni-Channel user perms.
8. **Citations** — skills, templates, and MCP tools used.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/omni-channel-routing-designer/<run_id>.md`
- **JSON envelope:** `docs/reports/omni-channel-routing-designer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Current non-goals excerpt

- Does not deploy queues, routing configs, presence configs, or service channels.
- Does not train or build Einstein Bots.
- Does not size headcount — uses the inputs given.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
