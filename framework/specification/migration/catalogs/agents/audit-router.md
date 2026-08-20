# V2 Migration Profile: `audit-router`

## Current source

- Path: `agents/audit-router/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Dispatches one of the audit domains in the [`audit_harness`](../_shared/harnesses/audit_harness/README.md) into its domain-specific classifier, returning a uniform output envelope: inventory + findings (P0/P1/P2 with domain-scoped codes) + optional mechanical patches + Process Observations + citations. Replaces 15 single-mode auditor agents whose logic was 80% duplicated boilerplate. Wave 3b-1 shipped 5 domains; Wave 3b-2 adds the remaining 10 for a total of 15 audit surfaces through one router.

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
| `domain` | yes | 15 values: `validation_rule`, `picklist`, `approval_process`, `record_type_layout`, `report_dashboard`, `case_escalation`, `lightning_record_page`, `list_view_search_layout`, `quick_action`, `reports_dashboards_folder_sharing`, `field_audit_trail_history_tracking`, `sharing`, `org_drift`, `my_domain_session_security`, `prompt_library` |
| `target_org_alias` | yes | `prod`, `uat` |
| `object_name` | conditional — required by `validation_rule` / `record_type_layout`; optional for `picklist` / `approval_process` | `Opportunity` |
| `audit_scope` | conditional — for `approval_process` | `org` \| `object:<Name>` \| `process:<Name>` |
| `scope` | conditional — for `picklist` | `object:<Name>` \| `org` |
| `folder_filter` | optional — for `report_dashboard` | `Sales_Dashboards` |
| Domain-specific | optional | See the classifier's `Inputs` table |

If a required input is missing, STOP and ask — never guess.

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

Conforms to [`output_schema.md`](../_shared/harnesses/audit_harness/output_schema.md). At minimum:

1. **Summary** — domain, target_org_alias, scope, inventory_count, P0/P1/P2 counts, max severity, confidence.
2. **Inventory** — id / name / active + domain-specific columns.
3. **Findings** — one row per finding with all 7 strict fields.
4. **Patches** — optional; included only when the classifier produces mechanical patches.
5. **Process Observations** — four buckets or the literal "nothing notable" string.
6. **Citations** — per AGENT_CONTRACT.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/audit-router/<run_id>.md`
- **JSON envelope:** `docs/reports/audit-router/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

### Dimensions (Wave 10 contract)

The agent's envelope MUST place every classifier below in either `dimensions_compared[]` or `dimensions_skipped[]`. Classifier state reflects whether the underlying probe ran fully, partially, or not at all.

Domain classifiers (one dimension per `--domain` value):
`validation_rule`, `picklist`, `approval_process`, `record_type_layout`, `report_dashboard`, `case_escalation`, `lightning_record_page`, `list_view_search_layout`, `quick_action`, `report_folder_sharing`, `field_history`, `sharing`, `org_drift`, `my_domain_session`, `prompt_library`.

## Current non-goals excerpt

- Does not modify org metadata.
- Does not deploy patches — emits them for the human to apply.
- Does not chain to other agents — recommends them in Process Observations.
- Does not invent new finding codes — only codes declared in a classifier's Rule Table may appear in output.
- Does not audit multiple domains in one invocation — one `--domain` per run.
- Does not execute Apex or run cleanup jobs — strictly advisory.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
