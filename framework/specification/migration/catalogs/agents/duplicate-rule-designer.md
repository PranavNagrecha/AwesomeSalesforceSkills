# V2 Migration Profile: `duplicate-rule-designer`

## Current source

- Path: `agents/duplicate-rule-designer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.2.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Given an sObject (typically Lead, Contact, Account, or a custom object with human-identity data), designs the **Matching Rule + Duplicate Rule** pair that enforces the org's dedup policy: which fields to match, with what fuzzy-vs-exact logic, what action to take on user-created vs API-created duplicates, which profiles/PSes are exempt, and how the rule interacts with `Lead.Convert`, `Merge`, and the `data-loader-pre-flight` integration path. Output is a Setup-ready design + metadata XML stubs.

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
| `object_name` | yes | `Lead` |
| `target_org_alias` | yes |
| `policy` | yes | `block` (hard block on exact match) \| `alert` (warn + allow) \| `block-on-create-only` \| `alert-on-create-only` |
| `match_basis` | yes | `email` \| `phone` \| `name+company` \| custom: a comma-separated list of field API names |
| `fuzziness` | no | `exact` (default) \| `fuzzy` (standard Salesforce match algo) — some match fields only support exact |
| `integration_exempt` | no | default `true` — integration principals are exempted via a `duplicateRuleFilter` on a `$User` field, or by the integration's Apex setting `Database.DMLOptions.DuplicateRuleHeader.allowSave`. Not via a Custom Permission: DuplicateRule has no such hook |

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

1. **Summary** — object, policy, match_basis, fuzziness, confidence.
2. **Matching Rule XML** — fenced block, labelled with target path.
3. **Duplicate Rule XML** — fenced block, labelled with target path.
4. **Bypass artefacts** — the `duplicateRuleFilter` block and/or the User-field stub, or the Apex `DMLOptions` snippet, whichever Step 6 chose. Never a Custom Permission wired to the rule.
5. **Interaction notes** — Convert behavior, Merge behavior, Person Accounts caveat if applicable.
6. **Test plan** — table from Step 7.
7. **Process Observations** — per `AGENT_CONTRACT.md`:
   - **What was healthy** — existing clean match fields, an existing integration-user flag already usable as a `$User` filter.
   - **What was concerning** — competing active dup rules, policies that conflict with Lead Convert semantics, fields with poor data quality that make fuzzy match unreliable.
   - **What was ambiguous** — custom objects with no obvious natural key (the agent made a choice).
   - **Suggested follow-up agents** — `permission-set-architect` (if the integration principal's flag or PSG is new), `data-loader-pre-flight` (if integrations will hit the rule), `field-impact-analyzer` (to understand what else uses the matched fields).
8. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/duplicate-rule-designer/<run_id>.md`
- **JSON envelope:** `docs/reports/duplicate-rule-designer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Each entry MUST name one of: `existing-rule-conflict`, `match-basis-validation`, `boolean-filter-shape`, `policy-action`, `bypass-permission`, `convert-behavior`, `merge-behavior`, `person-account-edge-cases`, `cross-account-contact-shape`, `test-plan`. If a dimension was skipped because the underlying probe could not run, the skip reason MUST link the refusal code.

### Dimensions (Wave 10 contract)

Every duplicate-rule design dimension below MU

## Current non-goals excerpt

- Does not activate or deploy rules.
- Does not merge existing duplicates (that's a separate job — cite `skills/data/large-scale-deduplication`).
- Does not modify match fields (the agent designs to the source data, it doesn't reshape data).
- Does not override Convert or Merge behavior.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
