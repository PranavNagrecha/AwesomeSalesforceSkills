# V2 Migration Profile: `changeset-builder`

## Current source

- Path: `agents/changeset-builder/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `build, validate`

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
| `mode` | yes | `build` \| `validate` |
| `source_org_alias` | yes | the sandbox to build the Change Set from |
| `target_org_alias` | yes (for dependency pre-check) | where the Change Set will be uploaded |
| `feature_summary` | build-mode | "Opportunity stage approval + new VR + updated page layout + new PSG" |
| `seed_components` | build-mode | comma-separated component names the user already knows must be included |
| `changeset_name` | validate-mode | the Outbound Change Set developer name |
| `include_destructive` | no | default `true` — include a `destructiveChanges.xml` if any components require removal |
| `profile_handling` | no | `permset-only` (default, recommended) \| `include-profiles` \| `permset-and-profiles` |

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

Build mode:

1. **Summary** — feature, source org, target org, total component count, confidence.
2. **Change Set manifest** — table with component type + API name + why it's included (primary / implicit) + deploy-order group.
3. **Metadata-API coverage gaps** — per Step 4.
4. **Destructive list** (if applicable).
5. **Deployment order** — numbered.
6. **Post-deploy checklist**.
7. **Process Observations**:
   - **What was healthy** — clean naming, feature already decomposed into cohesive components, existing PSGs the new feature can compose into.
   - **What was concerning** — profiles riding in the Change Set despite `permset-only` default, components whose dependencies span retired artifacts, Change Set size > 500 components (risks upload timeouts).
   - **What was ambiguous** — components that might be renamed-not-rebuilt (would look like a delete + create).
   - **Suggested follow-up agents** — `deployment-risk-scorer` (run before upload), `permission-set-architect` (if PSG composition is new), `release-train-planner` (if this should graduate off Change Sets).
8. **Citations**.

Validate mode:

1. **Summary** — Change Set name, declared component count, reconstructed dependency count, count of gaps.
2. **Gap table** — P0 (missing-from-declared but required), P1 (present-but-redundant), P2 (recommended additions).
3. **Target-org impact** — per-component create / update / type-change-destructive / skip.
4. **Process Observations** — as above, focused on what the human missed during manual assembly.
5. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/changeset-builder/<run_id>.md`
- **JSON envelope:** `docs/reports/changeset-builder/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Current non-goals excerpt

- Does not upload the Change Set to the target org.
- Does not run deploy validation via Metadata API.
- Does not create the deployment connection.
- Does not reassign Permission Sets after deploy.
- Does not convert Change Sets to SFDX projects — that's a separate path; cite `skills/devops/migration-from-change-sets-to-sfdx`.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
