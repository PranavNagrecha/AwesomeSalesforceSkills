# V2 Migration Profile: `lwc-builder`

## Current source

- Path: `agents/lwc-builder/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `False`
- Modes: `single`

## Current purpose

Produces a full Lightning Web Component bundle for a described feature: `.js`, `.html`, `.css`, `.js-meta.xml`, `__tests__/*.test.js`, and — where the component binds to server data — the matching `@AuraEnabled(cacheable=true)` Apex controller class stub. Every bundle conforms to `templates/lwc/component-skeleton/`, uses `templates/lwc/patterns/` where one fits, and ships with Jest tests configured via `templates/lwc/jest.config.js`. Accessibility, reactive data (`@wire`), and security defaults are baked in; no freestyle component shapes.

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
| `component_name` | yes | `opportunityClosePlan` (camelCase per LWC convention) |
| `feature_summary` | yes | "Edit an Opportunity's Close Plan checklist with draft persistence and validation" |
| `binding_kind` | yes | `record-page` \| `flow-screen` \| `app-page` \| `experience-cloud` \| `utility-bar` \| `home-page` \| `record-action` \| `standalone` |
| `data_shape` | yes | `record-form` (wires to one record) \| `list-view` \| `search` \| `no-data` |
| `target_objects` | record-form / list-view / search | comma-separated sObjects the component uses |
| `public_api` | no | comma-separated list of `@api` properties to expose (e.g. `recordId,showHeader`) |
| `a11y_tier` | no | `wcag-aa` (default) \| `wcag-aaa` (adds focus-management + live-region extras) |
| `include_tests` | no | default `true` |
| `emit_controller` | no | default `true` if `data_shape` is not `no-data` AND the data cannot be satisfied by UI API alone |

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

1. **Summary** — component name, binding kind, data shape, API version, confidence.
2. **Bundle files** — fenced blocks for each file in the bundle with the target path label. Never omit any file.
3. **Controller class + test** (if emitted) — fenced Apex with target paths.
4. **Data strategy note** — one paragraph: UI API vs imperative, and why.
5. **Exposure matrix** — which page types the bundle targets and its design-attribute surface.
6. **Test coverage summary** — paths covered, expected coverage.
7. **Process Observations**:
   - **What was healthy** — reuse opportunities (existing base components in the org), standard sObject coverage via UI API.
   - **What was concerning** — data shapes that hint at a server-side aggregation that belongs in a report or a formula, duplicate component shapes (the repo may already have one like it), `isExposed=true` on components that are really utility children.
   - **What was ambiguous** — `binding_kind=flow-screen` with ambiguous input/output variables (the user may intend a screen flow signature that the agent can't infer).
   - **Suggested follow-up agents** — `lwc-auditor` (post-build check), `apex-refactorer` (if controller grows), `security-scanner` (FLS/CRUD enforcement review), `test-class-generator` (for related Apex classes not in scope here).
8. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/lwc-builder/<run_id>.md`
- **JSON envelope:** `docs/reports/lwc-builder/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions for this agent: `data-strategy` (UI API / GraphQL / imperative Apex chosen + why), `accessibility` (WCAG-AA defaults + tier-specific extras), `public-api-shape` (`@api` typing + design-attribute coercion), `event-shape` (CustomEvent bubbles/composed/detail), `dom-mode` (shadow vs light decision), `styling-isolation`

## Current non-goals excerpt

- Does not deploy or Jest-run the bundle.
- Does not modify existing bundles in place.
- Does not emit a design spec for a page — it builds components that go onto pages.
- Does not generate test data beyond obvious Jest fixtures.
- Does not emit Aura components — LWC only.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
