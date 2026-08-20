# V2 Migration Profile: `business-hours-and-holidays-configurator`

## Current source

- Path: `agents/business-hours-and-holidays-configurator/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Designs and audits the Business Hours and Holidays configuration that every time-sensitive Salesforce feature keys off: Entitlement Processes + Milestones, Escalation Rules, Omni-Channel presence, Case business-hours math (`BusinessHours.diff`, `BusinessHours.add`), Email Routing Hours on email-to-case channels, and Approval Process "N days" constructs. Output is a region / tier / channel map of Business Hours calendars, linked Holidays (with recurring rules), the referenced-by inventory (what features read each calendar), and a phased deploy / remediation plan. Frequently the root cause of "the SLA fired at the wrong time" stories — this agent catches it before go-live.

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
| `target_org_alias` | yes |
| `coverage_summary` | yes | "Global 24x5 support M-F; APAC 8-20 local; EMEA 8-19 local; Americas 7-18 Central; country-specific holidays" |
| `regions` | no | list of regions to model; if omitted, derived from `coverage_summary` |
| `audit_existing` | no | default `true` — inventory current BH/Holidays before proposing |
| `holiday_source` | no | `manual` \| `ics-file-path` \| `country-standard` (agent lists country codes to use) |

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

1. **Summary** — regions, BH count proposed, Holiday count proposed, default BH, confidence.
2. **Current inventory** — existing BH + Holidays + referenced-by matrix.
3. **Target BH design** — table per BH with time zone, daily schedule, name, default flag, referenced features.
4. **Target Holidays design** — table per Holiday with date / recurrence, linked BH set, source (manual / ICS / country-standard).
5. **Internal consistency findings** — per Step 4.
6. **Downstream rebinding plan** — feature × old BH × new BH.
7. **Metadata stubs** — fenced XML per BH record and per Holiday record with target path (`force-app/main/default/businessHoursSettings/` + `force-app/main/default/holidays/`).
8. **Cutover checklist** — Step 6.
9. **Process Observations**:
   - **What was healthy** — existing BH records that can be reused unchanged, holidays already covering the coming year, time-zone settings aligned with the region's users.
   - **What was concerning** — multiple default BHs, Escalation Rules referencing a BH that no longer aligns with the region's staffing, floating holidays handled manually without a reminder process, Apex hard-coding BH names.
   - **What was ambiguous** — overnight coverage hand-offs between regions (does the Americas 18:00 hand-off to APAC start-of-day the next morning?), whether country-standard holidays include state / provincial days.
   - **Suggested follow-up agents** — `entitlement-and-milestone-designer` (if BH changes affect SLAs), `audit-router --domain case_escalation` (Escalation Rule rebinding verification), `omni-channel-routing-designer` (if channel presence keyed off BH).
10. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/business-hours-and-holidays-configurator/<run_id>.md`
- **JSON envelope:** `docs/reports/business-hours-and-holidays-configurator/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Current non-goals excerpt

- Does not create BH or Holiday records in the org.
- Does not rebind existing Entitlement Processes / Escalation Rules / Omni channels — produces the rebinding list only.
- Does not modify Apex that hard-codes BH by name.
- Does not fetch authoritative country-holiday data — skeleton only; the user confirms dates.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
