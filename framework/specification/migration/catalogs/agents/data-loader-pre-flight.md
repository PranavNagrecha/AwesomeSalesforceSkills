# V2 Migration Profile: `data-loader-pre-flight`

## Current source

- Path: `agents/data-loader-pre-flight/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Given a planned data load — sObject, volume, source CSV or mapping, intent (insert / upsert / update / delete) — produces a go/no-go checklist covering every org-side concern that will turn a load into an incident: active automation on the object, validation rules without bypass, sharing recalculation cost at the target volume, duplicate rule interactions, record type defaults, required fields with no source mapping, External ID selection, and storage quota impact. Output is a pre-flight report + a deployed-loader configuration recommendation (Data Loader, Data Import Wizard, Bulk API 2.0, CLI).

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
| `object_name` | yes | `Account` |
| `operation` | yes | `insert` \| `upsert` \| `update` \| `delete` \| `hard-delete` |
| `row_count` | yes | integer |
| `target_org_alias` | yes |
| `source_description` | yes | "NetSuite customer export, one row per account, external-id = `netsuite_customer_id__c`" |
| `external_id_field` | upsert-only |
| `window` | no | business-hours boundary ("this Saturday 2am-6am PT"); drives async sizing |

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

1. **Summary** — object, operation, row count, go/no-go, confidence.
2. **Findings** — table sorted P0 → P1 → P2. Each finding: category (automation, VR, dup-rule, RT, required field, sharing, storage), evidence, suggested fix, owner (admin / integration-user admin / DBA).
3. **Loader recommendation** — exact CLI + batch size + concurrency.
4. **Pre-load checklist** — numbered steps the user executes before the window starts.
5. **Post-load checklist** — re-enable deferred sharing calc, re-enable VR bypass de-toggle, re-assign dup rule actions, verify counts, run delta report.
6. **Rollback plan** — Step 9 instantiated.
7. **Process Observations** — per `AGENT_CONTRACT.md`:
   - **What was healthy** — bypass provisioning, dedicated integration PSG, indexed External ID, under-utilized storage.
   - **What was concerning** — VR bypass gaps not specific to this load (fix once, benefits every future load), data-skew hotspots, orphaned active flows.
   - **What was ambiguous** — source row volume estimate vs reality, CSV column → API name mapping that the agent couldn't verify.
   - **Suggested follow-up agents** — `audit-router --domain validation_rule` (if bypass gaps surfaced), `duplicate-rule-designer` (if dup-rule blocks surfaced), `audit-router --domain sharing` (if OWD + volume are dangerous), `audit-router --domain org_drift` (post-load verification).
8. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/data-loader-pre-flight/<run_id>.md`
- **JSON envelope:** `docs/reports/data-loader-pre-flight/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Each entry MUST name one of: `automation-stack`, `validation-rules`, `duplicate-rules`, `record-types`, `required-fields`, `csv-column-mapping`, `picklist-validation`, `sharing-recalc`, `storage-quota`, `loader-selection`, `rollback-plan`. If a d

## Current non-goals excerpt

- Does not execute the load.
- Does not generate the source CSV.
- Does not clone or enrich the source data.
- Does not deactivate flows, triggers, VRs, or dup rules.
- Does not provision the integration PSG (suggest `permission-set-architect`).
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
