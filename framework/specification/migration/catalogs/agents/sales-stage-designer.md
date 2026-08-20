# V2 Migration Profile: `sales-stage-designer`

## Current source

- Path: `agents/sales-stage-designer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `True`
- Modes: `design, audit`

## Current purpose

Designs or audits the Opportunity sales process: stages, probabilities, forecast categories, required fields per stage, stage-gate validation, pipeline-review cadence, and Collaborative Forecasts rollups. Produces a stage ladder that a sales ops team can take to Setup (Sales Process, Opportunity stage picklist, Path, Forecasts) plus the backing validation rules, required fields, and history tracking. The agent also audits an existing sales process and flags stage bloat, non-monotonic probabilities, and forecast-category drift.

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
| `target_org_alias` | yes for audit | `prod` |
| `business_motion` | yes for design | `"new-logo enterprise SaaS"` |
| `avg_cycle_length_days` | yes for design | `120` |
| `deal_band_min_max_usd` | no | `[50k, 2M]` |
| `record_type_name` | no | `Opportunity.NewBusiness` |

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

1. **Summary** — motion, cycle, stage count, forecast coverage, top 3 risks.
2. **Stage ladder** — table: stage, probability, forecast category, exit criteria, guidance text, history-tracked fields.
3. **Validation rules + Path** — VR payloads in pseudo-XML with bypass wired per `templates/admin/validation-rule-patterns.md`.
4. **Collaborative Forecasts config notes**.
5. **Audit findings** (audit mode).
6. **Process Observations**:
   - **Healthy** — stages monotonic; Path in use; history tracking on core fields.
   - **Concerning** — > 8 stages; probabilities not monotonic; forecast categories missing for a stage; stage gates implemented via required field at the field level (breaks integrations).
   - **Ambiguous** — deal bands overlap across record types; Commit stages < 70%.
   - **Suggested follow-ups** — `lead-routing-rules-designer` if conversion-to-Opportunity is out of scope; `permission-set-architect` for sales-ops access on forecasts.
7. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/sales-stage-designer/<run_id>.md`
- **JSON envelope:** `docs/reports/sales-stage-designer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Current non-goals excerpt

- Does not deploy OpportunityStages, SalesProcesses, VRs, or Path configurations.
- Does not build reports or dashboards for pipeline reviews (recommend `audit-router --domain report_dashboard`).
- Does not train sales reps.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
