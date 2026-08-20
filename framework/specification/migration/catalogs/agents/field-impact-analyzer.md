# V2 Migration Profile: `field-impact-analyzer`

## Current source

- Path: `agents/field-impact-analyzer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Given a field on an sObject, produces a blast-radius report: every Apex class, trigger, Flow, LWC, report, dashboard, formula, validation rule, workflow field update, approval process, email template, record type, page layout, permission set, and integration endpoint that references the field, together with a classification of each reference (read / write / metadata-only) and a deletion/rename risk score. Used before any "can I rename this field?" or "can I delete this field?" decision.

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
| `field_name` | yes | `Industry` (or `Industry__c` for custom) |
| `target_org_alias` | yes | `prod`, `uat`, `mydevsandbox` |
| `repo_path` | no | path to the sfdx project root; default `force-app/main/default` |
| `intent` | no | `rename` / `delete` / `audit` — changes severity thresholds |
| `integration_principals` | no | usernames or permission-set names the org treats as integrations, e.g. `["MuleSoft Integration", "Boomi_API_User@acme.com"]` — consumed by the Step 4 rename P0 criterion, which cannot be evaluated without it |

If `target_org_alias` is missing, STOP and ask — live-org metadata is required for an honest score.

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

1. **Summary** — field API name, data type, overall risk (P0/P1/P2), confidence (HIGH/MEDIUM/LOW).
2. **Reference inventory** — table grouped by system (Apex, Flow, LWC, VR, Formula, Reports, Layouts, Perms, Integrations). Each row: artifact, access type, evidence excerpt, citation link.
3. **Risk breakdown** — the specific rules from Step 4 that triggered, each with a one-line justification.
4. **Mitigation plan** — phased steps specific to `intent`, no auto-patch.
5. **Process Observations** — per `AGENT_CONTRACT.md`:
   - **What was healthy** — naming convention adherence, FLS hygiene, tracked vs untracked.
   - **What was concerning** — sibling fields with overlapping semantics, dynamic SOQL anywhere in the repo, fields with no help text.
   - **What was ambiguous** — reports not probeable by Tooling, managed-package fields colliding with name.
   - **Suggested follow-up agents** — `object-designer` for model-level redesign, `permission-set-architect` for FLS tidy-up, `data-loader-pre-flight` if the field is referenced by upcoming loads.
6. **Citations** — every skill, template, and MCP tool invocation the agent used.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/field-impact-analyzer/<run_id>.md`
- **JSON envelope:** `docs/reports/field-impact-analyzer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions for this agent: `apex-references` (ApexClass/Trigger Body via `apex-references-to-field` probe), `flow-references` (Flow Metadata via `flow-references-to-field` probe), `automation-graph` (full Flow/PB/WF/Approval graph via `automation-graph-for-sobject` probe), `validation-rules` (VR formulas), `formula-fields` (transitive formula chains on same object), `lwc-aura-references` (`AuraDefinition` / `LightningComponentResource` body scan), `reports-dashboards` (report column references — LOW confidence on Tooling), `layouts` (page / compac

## Current non-goals excerpt

- Does not rename or delete the field.
- Does not modify the repo or the org.
- Does not produce a migration PR — mitigation is advisory.
- Does not analyze cross-object dependencies beyond formula and relationship fans (cross-object impact is the `data-model-reviewer` agent's job — suggest it in Process Observations if the field is a lookup/external-id).
- Does not auto-chain to any other agent.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
