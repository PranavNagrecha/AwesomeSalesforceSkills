# V2 Migration Profile: `entitlement-and-milestone-designer`

## Current source

- Path: `agents/entitlement-and-milestone-designer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
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
| `sla_summary` | design | "Gold tier: 2h response, 8h resolution, 24x7; Silver: 4h/24h, 9x5 business hours; renewal clock resets per-case" |
| `tier_count` | design | integer — number of SLA tiers to model |
| `business_hours_model` | design | `single-org-wide` \| `per-tier` \| `per-region` |
| `audit_scope` | audit | `org` \| `entitlement_process:<DeveloperName>` |

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

1. **Summary** — tier count, business-hours model, total milestones, proposed Flow count, confidence.
2. **Business Hours + Holidays table** — per calendar.
3. **Entitlement Process design** — per tier, with Milestones table and action matrix.
4. **Entitlement Template design**.
5. **Auto-resolution logic** — description + pseudocode.
6. **Coexistence notes** — with Assignment Rules, Escalation Rules, Omni.
7. **Metadata stubs** — fenced XML per Business Hours, Entitlement Process, Milestone, Entitlement Template.
8. **Cutover checklist**.
9. **Process Observations**:
   - **What was healthy** — existing BH records reusable, clean product-to-entitlement binding, existing Case queues well-named.
   - **What was concerning** — SLA tiers that would overlap at edge conditions (e.g. 2h response for Gold but clock starts at Case creation regardless of channel latency), renewal model implied but not specified, tier targets that violate the posted Business Hours coverage (24x7 SLA on a 9x5 BH record).
   - **What was ambiguous** — "business hours" interpretation across regions, whether case re-open resets the clock.
   - **Suggested follow-up agents** — `flow-builder` (Milestone action flows), `omni-channel-routing-designer` (if Omni integrates), `audit-router --domain case_escalation` (post-design verification).
10. **Citations**.

Audit mode:

1. **Summary** — processes audited, active / inactive, finding counts.
2. **Findings table** — process × finding × severity × evidence × remediation.
3. **SLA metrics** — per process × per tier × last 6 months.
4. **Dead-config report** — processes, milestones, templates with zero live usage.
5. **Gap report** — Cases closed without an Entitlement.
6. **Process Observations** — as above.
7. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/entitlement-and-milestone-designer/<run_id>.md`
- **JSON envelope:** `docs/reports/entitlement-and-milestone-designer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions

## Current non-goals excerpt

- Does not activate processes or deploy metadata.
- Does not assign Entitlements to Accounts / Contacts.
- Does not generate the Case resolution flow — emits the spec for `flow-builder`.
- Does not configure Omni-Channel routing — that's `omni-channel-routing-designer`.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
