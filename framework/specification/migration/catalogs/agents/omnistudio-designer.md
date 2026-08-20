# V2 Migration Profile: `omnistudio-designer`

## Current source

- Path: `agents/omnistudio-designer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `design, audit`

## Current purpose

Designs or audits a complete OmniStudio capability across all four asset families — OmniScript (guided journeys), FlexCard (contextual display), DataRaptor (data shaping), and Integration Procedure (server-side orchestration) — plus the Business Rules Engine, Calculation Procedures, and document generation that hang off them. In `design` mode it turns a business capability into a layered build plan: which layer uses which asset, what the JSON data contract between layers looks like, how faults and session state are handled, and how the whole tree is versioned and promoted. In `audit` mode it inspects an existing implementation (live org, DataPack export, or retrieved metadata) and returns severity-ranked findings across ten named dimensions, with every dimension it could not cover recorded explicitly rather than dropped.

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
| `capability` | yes for design | `guided quote-to-application journey` |
| `layers` | yes | `["omniscript","integration_procedure","dataraptor"]` |
| `runtime_flavor` | yes | `native-omnistudio` \| `vlocity-managed-package` |
| `user_surface` | yes for design | `internal` \| `experience-cloud-authenticated` \| `guest` |
| `expected_volume` | no | `800 journey starts per day, peak 120 per hour` |
| `repo_path` | no | `force-app/main/default/` or a DataPack export directory to read when no org is connected |

Ask for every missing required input before starting. Never infer `runtime_flavor` from the industry — inspect the org or the source tree.

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

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`, `agents/_shared/schemas/output-envelope.schema.json`, and the five-section shape in `agents/_shared/harnesses/designer_base/shared_output_shape.md`.

### Deliverables

1. **Summary** — one paragraph plus the harness key-value block:

   ```
   - mode: <design | audit>
   - target_org_alias: <alias or "(none — design-only)">
   - scope: <capability name + layers in scope>
   - runtime_flavor: <native-omnistudio | vlocity-managed-package>
   - max_severity: <P0 | P1 | P2 | NONE>   [audit mode only]
   - confidence: <HIGH | MEDIUM | LOW>
   ```

2. **Design** (design mode only) — the layered build plan, one subsection per layer in scope: tool-boundary decision, journey design, card design, data contract, orchestration, rules and calculation, failure behaviour, security posture, performance and caching, versioning and promotion, test design.

3. **Audit Findings** (audit mode only) — the harness seven-column table, one row per finding, severity strictly P0 / P1 / P2:

   ```
   | code | severity | subject_id | subject_name | description | evidence | suggested_fix |
   ```

   Codes use the `OMNISTUDIO_` prefix, for example `OMNISTUDIO_GUEST_DATARAPTOR_OVERBROAD`, `OMNISTUDIO_MIXED_PIPELINE_MODE`, `OMNISTUDIO_DEPENDENCY_GRAPH_UNPARSED`.

4. **Migration recommendations** (optional; audit mode) — emitted when the audit shows the org is on the managed package and a native cutover is warranted, or a journey still runs on the older Visualforce-based runtime. Names the blockers, not just the target state.

5. **Cutover plan** (optional; audit mode) — emitted only alongside Migration recommendations: sequence, side-by-side test window, rollback trigger, and the components whose feature gap blocks decommissioning the managed package.

6. **Process Observations** — Healthy / Concerning / Ambiguous / Suggested follow-ups, each citing what was being looked at when the observation was made (a retrieved metadata file, a probe result, a count). Suggested follow-ups name real agents with a one-line reason — for example `agents/lwc-auditor` when the journey embeds custom components, `agents/security-scanner` when an Apex action's sharing context is the real exposure, `agents/release-train-planner` when promotion is ad hoc, `agents/flow-builder` when a layer belongs in Flow instead.

7. **Citations** — every skill, decision-tree branch, harness doc, and MCP tool consulted, in the citation schema from `agents/_shared/AGENT_CONTRACT.md`.

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/omnistudio-designer/<run_id>.md`
- **JSON envelope:** `docs/reports/omnistudio-designer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a 

## Current non-goals excerpt

- Does not deploy anything: no metadata deploy, no DataPack import or export execution, no `vlocity` CLI invocation, no activation or deactivation of a live version.
- Does not write outside the paths the caller supplied plus its own `default_output_dir`.
- Does not author Lightning Web Component bundles or Apex classes. It specifies their contracts and routes to `agents/lwc-builder` and `agents/apex-builder`.
- Does not design Omni-Channel routing, queues, presence configuration, or agent capacity — that is `agents/omni-channel-routing-designer`.
- Does not size licenses or headcount, and does not advise on Industries licensing entitlement.
- Does not process more than one capability per invocation, and does not run `design` and `audit` in the same run.
- Does not chain to other agents automatically; follow-ups are recommendations for the human to invoke.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
