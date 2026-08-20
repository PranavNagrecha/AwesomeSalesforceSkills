# V2 Migration Profile: `waf-assessor`

## Current source

- Path: `agents/waf-assessor/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Runs a Well-Architected Framework (WAF) assessment against a Salesforce implementation across the framework's **three** pillars: **Trusted**, **Easy**, **Adaptable**. Scores each pillar, surfaces the top 3 concerns per pillar with org evidence, and produces a remediation backlog ordered by severity × cost-to-fix. Also documents NFRs and maps them to verifiable checks (limits, scalability, HA/DR).

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
| `target_org_alias` | yes | `prod` |
| `workload` | yes | `"sales cloud + CPQ + agentforce"` |
| `nfrs` | no | JSON: `{ "availability": "99.9%", "rpo_hours": 4 }` |
| `scope_pillars` | no | default: all 3 (`trusted`, `easy`, `adaptable`); subset allowed |

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

1. **Summary** — workload, org identity, 3-pillar scorecard (Trusted / Easy / Adaptable), each pillar carrying the sub-scores for its dimensions.
2. **NFR sheet** — each NFR with current-state measurement and gap.
3. **Pillar findings** — 3 sections, top 3 per pillar + evidence.
4. **Remediation backlog** — ordered by severity × cost-to-fix.
5. **Process Observations**:
   - **Healthy** — NFRs declared and measured; Shield enabled; modular package structure.
   - **Concerning** — NFRs undeclared; HA/DR is implicit (i.e., no backup plan); > 3 overlapping automations on the same sObject.
   - **Ambiguous** — storage trend unknown; integration inventory incomplete.
   - **Suggested follow-ups** — `audit-router --domain sharing`, `integration-catalog-builder`, `release-train-planner`, `sandbox-strategy-designer`.
6. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/waf-assessor/<run_id>.md`
- **JSON envelope:** `docs/reports/waf-assessor/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

### Dimensions (Wave 10 contract)

The agent's envelope MUST place every Well-Architected pillar below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `security` | FLS, sharing, auth, secret handling |
| `reliability` | Fault paths, governor headroom, recovery |
| `performance` | SOQL selectivity, CPU, heap |
| `scalability` | LDV patterns, bulk safety, async design |
| `user-experience` | Path guidance, navigation, error messaging |
| `operational-excellence` | Monitoring, deploy hygiene, incident runbooks |

## Current non-goals excerpt

- Does not remediate — produces a backlog.
- Does not run Salesforce Optimizer (different tool).
- Does not certify against WAF formally (advisory scorecard only).
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
