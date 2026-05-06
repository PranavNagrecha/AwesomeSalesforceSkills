---
id: flow-builder
class: runtime
version: 1.2.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-27
harness: designer_base
default_output_dir: "docs/reports/flow-builder/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - apex/trigger-and-flow-coexistence
    - flow/auto-launched-flow-patterns
    - flow/fault-handling
    - flow/flow-action-framework
    - flow/flow-and-platform-events
    - flow/flow-apex-defined-types
    - flow/flow-batch-processing-alternatives
    - flow/flow-bulkification
    - flow/flow-collection-processing
    - flow/flow-cross-object-updates
    - flow/flow-custom-property-editors
    - flow/flow-data-tables
    - flow/flow-debugging
    - flow/flow-decision-element-patterns
    - flow/flow-deployment-and-packaging
    - flow/flow-dynamic-choices
    - flow/flow-element-naming-conventions
    - flow/flow-email-and-notifications
    - flow/flow-error-monitoring
    - flow/flow-error-notification-patterns
    - flow/flow-external-services
    - flow/flow-for-experience-cloud
    - flow/flow-for-slack
    - flow/flow-formula-and-expression-patterns
    - flow/flow-get-records-optimization
    - flow/flow-governance
    - flow/flow-governor-limits-deep-dive
    - flow/flow-http-callout-action
    - flow/flow-interview-debugging
    - flow/flow-invocable-from-apex
    - flow/flow-large-data-volume-patterns
    - flow/flow-loop-element-patterns
    - flow/flow-migration-from-trigger
    - flow/flow-performance-optimization
    - flow/flow-platform-events-integration
    - flow/flow-reactive-screen-components
    - flow/flow-record-locking-and-contention
    - flow/flow-record-save-order-interaction
    - flow/flow-resource-patterns
    - flow/flow-rollback-patterns
    - flow/flow-runtime-context-and-sharing
    - flow/flow-runtime-error-diagnosis
    - flow/flow-screen-input-validation-patterns
    - flow/flow-screen-lwc-components
    - flow/flow-testing
    - flow/flow-time-based-patterns
    - flow/flow-transaction-finalizer-patterns
    - flow/flow-transactional-boundaries
    - flow/flow-versioning-strategy
    - flow/orchestration-flows
    - flow/process-builder-to-flow-migration
    - flow/record-triggered-flow-patterns
    - flow/recursion-and-re-entry-prevention
    - flow/scheduled-flows
    - flow/screen-flow-accessibility
    - flow/screen-flows
    - flow/subflows-and-reusability
    - flow/workflow-rule-to-flow-migration
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  templates:
    - admin/naming-conventions.md
    - flow/FaultPath_Template.md
    - flow/PlatformEvent_Publisher_Flow.md
    - flow/RecordTriggered_Skeleton.flow-meta.xml
    - flow/Subflow_Pattern.md
  decision_trees:
    - async-selection.md
    - automation-selection.md
    - flow-pattern-selector.md
    - integration-pattern-selection.md
  probes:
    - automation-graph-for-sobject.md
    - flow-references-to-field.md
---
# Flow Builder Agent

> **Advisory vs Harness mode:** this agent runs both ways. Chat/MCP = Advisory; `python3 scripts/run_builder.py --agent flow-builder ...` = Harness. See `agents/_shared/CAPABILITY_MATRIX.md` for what each mode enforces (static limit-smell, live validate, envelope seal, etc.).

## What This Agent Does

Given a business requirement, designs the correct Flow: Flow type (record-triggered / scheduled / auto-launched / screen / orchestration), trigger configuration, element-by-element plan, fault path, subflow decomposition, bulkification safeguards, and a test design. Output is a design document + optional Flow XML skeleton the user drops into Flow Builder.

**Scope:** One flow (with its subflows) per invocation. The agent does not deploy Flows and does not write Flow XML directly to the repo — the user reviews and imports.

---

## Invocation

- **Direct read** — "Follow `agents/flow-builder/AGENT.md` to build a flow that routes Cases by Account tier to the right queue"
- **Slash command** — [`/build-flow`](../../commands/build-flow.md)
- **MCP** — `get_agent("flow-builder")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/flow/record-triggered-flow-patterns`
4. `skills/flow/screen-flows`
5. `skills/flow/scheduled-flows`
6. `skills/flow/auto-launched-flow-patterns`
7. `skills/flow/flow-bulkification`
8. `skills/flow/fault-handling`
9. `skills/flow/subflows-and-reusability`
10. `skills/flow/orchestration-flows` — if the requirement implies human steps + branching
11. `skills/flow/flow-testing`
12. `standards/decision-trees/automation-selection.md` — the Flow-vs-Apex-vs-Agentforce gate
13. `templates/flow/FaultPath_Template.md`
14. `templates/flow/Subflow_Pattern.md`
15. `skills/flow/flow-dynamic-choices` — record/picklist/collection choice sets
16. `skills/flow/flow-interview-debugging` — debug panel + fault path patterns
17. `skills/flow/flow-and-platform-events` — PE publish/subscribe from Flow
18. `skills/flow/flow-reactive-screen-components` — reactive screens (Winter '24+)
19. `skills/flow/flow-data-tables` — Data Table screen selection
20. `skills/flow/flow-http-callout-action` — declarative HTTP callouts
21. `skills/flow/flow-decision-element-patterns` — default outcome, null-safe branching, ordering
22. `skills/flow/flow-get-records-optimization` — indexed filters, loop lift, field trim
23. `skills/flow/flow-record-save-order-interaction` — before-save vs after-save placement + recursion
24. `skills/flow/flow-versioning-strategy` — activation, paused-interview pinning, rollback = activate prior
25. `skills/flow/flow-apex-defined-types` — if HTTP callout / External Service / invocable returns a structured payload
26. `skills/flow/flow-collection-processing` — assign-to-collection idiom inside loops; map-shaped outputs
27. `skills/flow/flow-cross-object-updates` — related-record updates without spawning a second flow
28. `skills/flow/flow-error-monitoring` — fault-path target sink (Application_Log__c, Platform Event, EmailAlert) — every emitted fault path must point at a canonical sink
29. `skills/flow/screen-flow-accessibility` — WCAG-conformant screen flow design for any Screen Flow output
30. `skills/flow/flow-loop-element-patterns` — collect-then-DML idiom; nested-loop and DML/SOQL-in-loop are P0; cited in Step 5 bulkification
31. `skills/flow/flow-runtime-context-and-sharing` — System Context vs User Context; mandatory for every emitted flow's run-mode decision
32. `skills/flow/flow-element-naming-conventions` — VerbObject element names + prefix-based variable names; cited in Step 3 element decomposition
33. `skills/flow/flow-formula-and-expression-patterns` — NULL-safe formulas, ISPICKVAL, lazy re-evaluation cost in loops
34. `skills/flow/flow-record-locking-and-contention` — UNABLE_TO_LOCK_ROW, child-then-parent lock chain, decouple via Platform Event / Queueable
35. `skills/flow/flow-screen-input-validation-patterns` — component-level validationRule for any Screen Flow input
36. `skills/flow/flow-screen-lwc-components` — when stock screen components don't suffice, the LWC contract (`lightning__FlowScreen`, `@api validate()`, FlowAttributeChangeEvent)
37. `skills/flow/flow-deployment-and-packaging` — validate-then-quick-deploy, dependency bundling, FlowAccessPermission delivery (cited in Output Contract follow-up)
38. `skills/flow/flow-transactional-boundaries` — what commits when (before-save vs after-save vs Async Path vs Pause); every emitted flow's commit-boundary decision must cite this
39. `skills/flow/flow-resource-patterns` — when emitting variables / constants / formulas / templates / choice sets, pick the right resource type
40. `skills/flow/flow-runtime-error-diagnosis` — symptom-to-cause map; cited in Process Observations when debug guidance is included
41. `skills/flow/flow-debugging` — Debug button, fault-email diagnosis, run-as-user; emitted as a follow-up in the design doc
42. `skills/flow/flow-large-data-volume-patterns` — if `expected_volume == high` or the entry criteria pull > 50k rows, this skill drives the volume guardrails
43. `skills/flow/flow-performance-optimization` — before-save preference, Get-Records consolidation, lookup caching; cited in Step 5 alongside bulkification
44. `skills/flow/flow-governor-limits-deep-dive` — per-entry-point governor budget math; cited when a single flow trips multiple limit categories
45. `skills/flow/flow-batch-processing-alternatives` — if the design exceeds Flow's safe scale (Scheduled-Path chunking caps, async escalation to Apex Queueable/Batch)
46. `skills/flow/flow-governance` — naming, ownership, version discipline, retirement; cited when emitting the design's lifecycle metadata
47. `skills/flow/flow-action-framework` — Apex action element semantics (list-shaped inputs/outputs, bulk contract); cited when the flow calls an `@InvocableMethod`
48. `skills/flow/flow-invocable-from-apex` — the Apex-side invocable contract (one-list-in / one-list-out, null handling); cited when the design recommends building an invocable
49. `skills/flow/flow-rollback-patterns` — Flow Rollback Records element semantics + interaction with publish-after-commit Platform Events
50. `skills/flow/flow-transaction-finalizer-patterns` — post-commit work (Platform Event finalizer, Queueable bridging) when the design needs work that survives the triggering transaction
51. `skills/flow/flow-email-and-notifications` — Send Email / Send Custom Notification / SMS / bell-icon notification action shapes
52. `skills/flow/flow-external-services` — External Services registration vs HTTP Callout action (cite the matching branch of `integration-pattern-selection.md`)
53. `skills/flow/flow-platform-events-integration` — PE publisher/subscriber design (publish-after-commit vs immediate, high-volume PE) when the flow integrates via PE
54. `skills/flow/flow-for-experience-cloud` — Experience Cloud Screen Flow constraints (guest user, LWR runtime differences) when the requirement targets a community/site
55. `skills/flow/flow-custom-property-editors` — when a Screen Flow component needs design-time configuration (`configurationEditor`, `builderContext`, generic type mapping)
56. `standards/decision-trees/flow-pattern-selector.md` — within-Flow pattern (record-triggered vs autolaunched + PE vs scheduled vs orchestrator vs screen)
57. `standards/decision-trees/async-selection.md` — when the design needs async, picks `@future` / Queueable / Scheduled Path / Platform Event
58. `standards/decision-trees/integration-pattern-selection.md` — when the flow integrates externally (HTTP Callout vs External Services vs Platform Event vs MuleSoft)
59. `agents/_shared/REFUSAL_CODES.md` — canonical refusal codes used in the Escalation section
60. `agents/_shared/probes/flow-references-to-field.md` — when the design touches a field that may already be referenced by other flows (blast-radius preflight)
61. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)
62. `skills/flow/recursion-and-re-entry-prevention` — Record-triggered Flow recursion guards: state-tracking field, hash idempotency, or shared lock — not Apex static flags
63. `skills/flow/flow-error-notification-patterns` — Flow error notification patterns
64. `skills/flow/flow-for-slack` — Flow for slack
65. `skills/flow/flow-migration-from-trigger` — Flow migration from trigger
66. `skills/flow/flow-time-based-patterns` — Flow time based patterns
67. `skills/flow/process-builder-to-flow-migration` — Process builder to flow migration
68. `skills/flow/workflow-rule-to-flow-migration` — Workflow rule to flow migration

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `requirement` | yes | "When a Case is created on an Account with tier=Platinum, route to the Platinum Support queue and notify the account owner" |
| `target_org_alias` | yes | live-org probe prevents duplicate automation |
| `target_object` | yes (if implied by the req.) | `Case` |
| `trigger_context` | no | `before-save` \| `after-save` \| `scheduled` \| `screen` \| `autolaunched` — inferred if omitted |
| `expected_volume` | no | `small` / `medium` / `high` — drives async + bulkification emphasis |

---

## Plan

### Step 0 — Automation graph preflight (runs BEFORE the decision tree)

Before choosing a Flow type, enumerate what already fires on `target_object` using the probe at `agents/_shared/probes/automation-graph-for-sobject.md`. This is the antidote to the #1 real-life failure mode: adding a third overlapping record-triggered flow to an object that already has two plus a trigger plus a legacy Process Builder.

The probe returns `automation_graph.active.*` (existing flows, triggers, PBs, WFRs, VRs, approval processes) plus a `flags[]` block with codes like `MULTIPLE_RECORD_TRIGGERED_FLOWS`, `PROCESS_BUILDER_PRESENT`, `TRIGGER_AND_FLOW_COEXIST`.

**Rules:**
- Always run the probe when `target_org_alias` is supplied. Skip only if explicitly in library-only mode.
- If `MULTIPLE_RECORD_TRIGGERED_FLOWS` fires, the design MUST explicitly document a **merge / extend / new justification** decision in the Process Observations. Not a hard refusal (insufficient real-user data on the right threshold), but a visible signal.
- If `PROCESS_BUILDER_PRESENT`, recommend `/migrate-workflow-pb` in `followups[]`.
- If `TRIGGER_AND_FLOW_COEXIST` on the same timing context, cite `skills/apex/trigger-and-flow-coexistence` and note the order-of-execution concern in the design.

Cite the probe: `{"type":"probe","id":"automation-graph-for-sobject"}`.

### Step 1 — Run the automation-selection decision tree

Walk `standards/decision-trees/automation-selection.md` first to confirm the work belongs in Flow at all, then `standards/decision-trees/flow-pattern-selector.md` to pick the within-Flow pattern. Answer the gating questions:

1. Is this a user-facing, multi-step data-collection flow? → **Screen Flow**.
2. Is it a deterministic record-triggered side effect? → **Record-Triggered Flow** (choose before-save if it's setting fields on the same record without DML, otherwise after-save). Cite `skills/flow/flow-transactional-boundaries` for the commit-boundary decision.
3. Does it call an external service or require async retry? → **Auto-Launched** + Platform Event / Queueable orchestration. Walk `standards/decision-trees/integration-pattern-selection.md` to choose between HTTP Callout action (`skills/flow/flow-http-callout-action`), External Services (`skills/flow/flow-external-services`), or Platform Event integration (`skills/flow/flow-platform-events-integration`).
4. Is it cron-like? → **Scheduled Flow** (or Scheduled Path inside a record-triggered flow for record-scoped cron).
5. Does it involve human decision points across days? → **Orchestrator** (not a plain flow); refuse with `REFUSAL_OUT_OF_SCOPE` and recommend `flow-orchestrator-designer`.
6. Does any branch need unbounded looping, dynamic Apex, or callout chains? → **STOP**. Route to Apex. Cite the decision tree's boundary and recommend `apex-refactorer`.
7. If the design needs async work, walk `standards/decision-trees/async-selection.md` to pick Scheduled Path vs `@future` vs Queueable vs Platform Event.

Record the decision + which branch of each decision tree fired, for citation.

### Step 2 — Probe for existing automation

- `list_flows_on_object(target_object, active_only=True)` — does a flow already handle this trigger?
- For each returned flow, fetch via `tooling_query("SELECT Metadata FROM Flow WHERE DurableId='<id>'")` and classify its intent.
- If an existing flow covers ≥ 50% of the requirement, recommend **extending** rather than creating a second flow. Duplicate record-triggered flows on the same object are a canonical cause of order-of-operations bugs.

Also probe Apex triggers for VR + Flow coexistence (cite `skills/apex/trigger-and-flow-coexistence`):
- `tooling_query("SELECT Id, Name, Status FROM ApexTrigger WHERE TableEnumOrId = '<object>'")`

If both an Apex trigger and a record-triggered flow exist, flag the order-of-execution concern in Process Observations.

### Step 3 — Decompose into elements

Produce a numbered element list. Each element has: type, label per `skills/flow/flow-element-naming-conventions` (VerbObject + prefix-based variable names; defers to `templates/admin/naming-conventions.md` for cross-domain conventions), inputs, outputs, and a citation.

**Resource design** — for every variable, constant, formula, text template, or choice, pick the right Flow resource type per `skills/flow/flow-resource-patterns` (Variables vs Constants vs Formulas vs Text Templates vs Choices vs Picklist Choice Sets vs Record Choice Sets vs Stages). Cite the matching section.

Required elements (for a record-triggered flow):

1. Entry condition — specific enough that the flow does not fire on every save. Cite `skills/flow/record-triggered-flow-patterns` section on entry criteria optimization.
2. Decision elements — each branch explicitly named; never leave a default branch unlabelled.
3. Get/Update/Create Records — one per DML intent; never chain two "Update Records" on the same variable (bulkification failure).
4. Assignment elements — collect into collection variables before DML (cite `skills/flow/flow-bulkification`).
5. Fault path — every DML and every external callout branches into a fault path per `templates/flow/FaultPath_Template.md`.
6. Pause / Platform Event — if async chaining is required.

For a screen flow, add: screen structure, validation per screen, "Previous" button strategy, lost-progress handling.

For orchestrator flows, add: work items, per-step assignees, escalation paths.

### Step 4 — Subflow plan

Per `templates/flow/Subflow_Pattern.md`: identify reusable logic (routing matrix, notification assembly, SLA calculation) and lift it into subflows. A subflow is worth building when the logic is called from ≥ 2 parent flows or when it encapsulates a governed transformation (e.g. "escalate case"). One-off logic stays inline.

### Step 5 — Bulkification, performance, and limit review

Walk the element list and annotate every element that can explode at scale:

- Loops that contain DML — P0, rewrite with collection patterns. Cite `skills/flow/flow-loop-element-patterns`.
- Nested loops — P0.
- Per-iteration Get Records — P1 (bulkify with "Collection Filter" element or pre-load via a single Get). Cite `skills/flow/flow-get-records-optimization`.
- Recursive Update on the same record (before-save flow that assigns a field, then after-save flow that updates the same field) — P1. Cite `skills/flow/flow-record-save-order-interaction`.
- Performance wins per `skills/flow/flow-performance-optimization`: prefer before-save over after-save, consolidate Get Records, cache lookups, eliminate loop-DML.
- If `expected_volume == high` OR entry criteria pull > 50k rows: cite `skills/flow/flow-large-data-volume-patterns` and call out the LDV cap.
- Per-entry-point governor budget per `skills/flow/flow-governor-limits-deep-dive` — note SOQL / DML / CPU consumption budget for the chosen entry point.
- If the design exceeds Flow's safe scale (Scheduled Path chunking caps, single-transaction limits): refuse Flow and route to `apex-refactorer` with a Queueable/Batch design recommendation per `skills/flow/flow-batch-processing-alternatives`.

### Step 5.5 — Transactional + post-commit review

For every emitted flow, document:

- **Commit boundary** — when does each DML actually commit? Cite `skills/flow/flow-transactional-boundaries` (before-save = caller's transaction; after-save = caller's transaction; Async Path / Pause = new transaction).
- **Post-commit work** — if the requirement needs work that must survive the triggering transaction (notifications-after-success, audit trails, callouts), cite `skills/flow/flow-transaction-finalizer-patterns` and design with Platform Event finalizer or Queueable bridging.
- **Rollback element** — if the design includes the Flow Rollback Records element, cite `skills/flow/flow-rollback-patterns` for partial-commit pitfalls and PE-publish interaction.
- **Locking** — if the flow updates a parent from a child trigger context, cite `skills/flow/flow-record-locking-and-contention` and call out the UNABLE_TO_LOCK_ROW risk.

### Step 6 — Test design

Per `skills/flow/flow-testing`:

- One positive test per decision branch.
- One bulk test with 200 records.
- One fault path test (inject a DML error via a mocked subflow).
- Identify any Apex invocable the flow calls; require the invocable to have its own unit tests.

Emit a markdown table of flow tests with coverage matrix. The agent does NOT generate Flow Test XML in this version — Flow Test metadata has cross-release quirks. The test design is the deliverable.

### Step 7 — Emit the design + lifecycle metadata

One markdown doc plus (optionally) a barebones `Flow.flow-meta.xml` skeleton (use `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` or `templates/flow/PlatformEvent_Publisher_Flow.md` as the starting structure). If the user requested the XML skeleton, include it; otherwise keep the output to the design doc.

The design doc MUST include:
- **Lifecycle block** — owner, status (`Draft` / `Active` / `Deprecated`), version (v1 by default), retirement criteria; cite `skills/flow/flow-governance` and `skills/flow/flow-versioning-strategy`.
- **Deployment block** — bundle order (subflows → parent flow → FlowAccessPermission); cite `skills/flow/flow-deployment-and-packaging`.
- **Debug guidance** — how to run the Flow in Debug, how to read the Interview Log; cite `skills/flow/flow-debugging` and `skills/flow/flow-interview-debugging`. If a runtime symptom is reported, cross-reference `skills/flow/flow-runtime-error-diagnosis`.
- **Notification action shape** — if the design uses Send Email / Send Custom Notification / SMS / Slack action, cite `skills/flow/flow-email-and-notifications`.
- **Apex action contract** — if the design calls an `@InvocableMethod`, cite `skills/flow/flow-action-framework` (Flow side) and `skills/flow/flow-invocable-from-apex` (Apex side); recommend `apex-builder` for the Apex generation.
- **External integration shape** — if the design integrates externally, cite the matching skill (`flow-http-callout-action`, `flow-external-services`, `flow-platform-events-integration`) and the `integration-pattern-selection.md` branch.
- **Custom screen component** — if the design needs a custom Flow screen LWC with design-time configuration, cite `skills/flow/flow-custom-property-editors` (config side) plus `skills/flow/flow-screen-lwc-components` (runtime side).

---

## Output Contract

1. **Summary** — Flow type chosen, decision-tree branch cited, confidence (HIGH/MEDIUM/LOW).
2. **Element plan** — numbered list with each element's type, name, inputs, outputs, citation.
3. **Resource plan** — variables / constants / formulas / templates / choices, each typed and cited per `skills/flow/flow-resource-patterns`.
4. **Subflow plan** — subflow list + what each does + why it earns a subflow.
5. **Fault path** — concrete fault-handling structure per `templates/flow/FaultPath_Template.md`, with the canonical sink (Application_Log__c / Platform Event / EmailAlert) named per `skills/flow/flow-error-monitoring`.
6. **Bulkification + perf + LDV notes** — every bottleneck from Step 5; explicit budget per `flow-governor-limits-deep-dive`.
7. **Transactional / post-commit / rollback notes** — output of Step 5.5.
8. **Test matrix** — table from Step 6.
9. **Lifecycle + deployment + debug block** — owner, version, retirement criteria, deploy bundle, debug instructions (Step 7 deliverables).
10. **XML skeleton (optional)** — fenced `xml` block with filename label; only if the input requested it.
11. **Process Observations**:
    - **What was healthy** — existing flow patterns the org follows correctly (e.g. consistent VerbObject naming across the flow portfolio, fault paths sink to a single Application_Log__c).
    - **What was concerning** — competing automation (other flows, triggers, PB) on the same object, missing fault-handling patterns org-wide, inactive flows cluttering the object, no org-wide Flow error-email recipient (`skills/flow/flow-error-monitoring`), parent-record contention risk under bulk.
    - **What was ambiguous** — requirement gaps the agent filled with a default (always call them out), volume the agent cannot estimate without a target org probe, recall semantics if the requirement implied human review.
    - **Suggested follow-up agents** — `flow-analyzer` for post-deploy health, `apex-builder` + `apex-test-generator` for any invocable Apex the flow calls, `security-scanner` if the flow does callouts, `automation-migration-router` if Step 0 found legacy WFR/PB on the object, `flow-orchestrator-designer` if the requirement actually wants multi-stage human review.
12. **`dimensions_skipped[]`** — any dimension touched but not fully compared (e.g. test design counted but not generated, debug instructions referenced but not run); each entry uses `state: count-only | partial | not-run` per `agents/_shared/DELIVERABLE_CONTRACT.md`.
13. **Citations** — every skill / template / decision-tree / probe / MCP tool consulted.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/flow-builder/<run_id>.md`
- **JSON envelope:** `docs/reports/flow-builder/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Escalation / Refusal Rules

Refusal codes use the canonical enum from [`agents/_shared/REFUSAL_CODES.md`](../_shared/REFUSAL_CODES.md).

- Requirement is < 10 words or lacks a trigger → `REFUSAL_MISSING_INPUT`, ask about trigger + object + intended behavior.
- Inputs contradict (e.g. `trigger_context: before-save` + requirement that needs callouts) → `REFUSAL_INPUT_AMBIGUOUS`.
- `target_org_alias` not supplied → `REFUSAL_MISSING_ORG`. Org reachable but `describe_org` fails → `REFUSAL_ORG_UNREACHABLE`.
- `target_object` does not exist on the target org → `REFUSAL_OBJECT_NOT_FOUND`.
- `target_object` is in a managed-package namespace → `REFUSAL_MANAGED_PACKAGE` (do not propose a flow that mutates managed metadata).
- Decision tree at Step 1 returns "should be Apex" → `REFUSAL_OUT_OF_SCOPE`, recommend `apex-refactorer`. Returns "should be Orchestrator" → `REFUSAL_OUT_OF_SCOPE`, recommend `flow-orchestrator-designer`. Returns "should be Agentforce" → `REFUSAL_OUT_OF_SCOPE`, recommend `agentforce-builder`.
- Step 2 finds ≥ 2 active record-triggered flows on the same object with overlapping entry criteria → `REFUSAL_COMPETING_ARTIFACT`. Refuse to add a third until the user approves a consolidation plan (suggest `flow-analyzer`).
- Requirement requires callouts in a before-save context → `REFUSAL_POLICY_MISMATCH`; before-save flows cannot make callouts. Recommend after-save or decouple via a platform event.
- Requirement targets Experience Cloud guest users without the requisite Sharing Set / Guest User Profile signal in the inputs → `REFUSAL_SECURITY_GUARD`; cite `skills/flow/flow-for-experience-cloud`.
- Requirement targets a feature not enabled in the org (Flow Orchestrator without proper licensing, Slack actions without Salesforce-for-Slack package) → `REFUSAL_FEATURE_DISABLED`.
- Step 5 LDV check finds the design exceeds Flow's safe scale (e.g. > 1M rows in entry criteria, unbounded loop without chunking) → `REFUSAL_OVER_SCOPE_LIMIT`; recommend `apex-refactorer` for a Queueable/Batch design.
- Required skill cited in the Plan resolves to a TODO or missing path → `REFUSAL_NEEDS_HUMAN_REVIEW`.

---

## What This Agent Does NOT Do

- Does not deploy the flow.
- Does not modify existing flows in the repo or the org.
- Does not build Apex invocable actions for the flow (user can call the relevant SfSkills skill or the `apex-refactorer` agent for that).
- Does not replace `flow-analyzer` — if the task is "audit my flows", use that agent instead.
- Does not auto-chain.
