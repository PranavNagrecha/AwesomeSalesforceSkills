---
id: flow-analyzer
class: runtime
version: 1.1.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-27
default_output_dir: "docs/reports/flow-analyzer/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - apex/trigger-and-flow-coexistence
    - flow/flow-action-framework
    - flow/flow-and-platform-events
    - flow/flow-apex-defined-types
    - flow/flow-batch-processing-alternatives
    - flow/flow-bulkification
    - flow/flow-collection-processing
    - flow/flow-cross-object-updates
    - flow/flow-data-tables
    - flow/flow-debugging
    - flow/flow-decision-element-patterns
    - flow/flow-deployment-and-packaging
    - flow/flow-dynamic-choices
    - flow/flow-element-naming-conventions
    - flow/flow-error-monitoring
    - flow/flow-external-services
    - flow/flow-for-experience-cloud
    - flow/flow-formula-and-expression-patterns
    - flow/flow-get-records-optimization
    - flow/flow-governance
    - flow/flow-governor-limits-deep-dive
    - flow/flow-http-callout-action
    - flow/flow-invocable-from-apex
    - flow/flow-large-data-volume-patterns
    - flow/flow-loop-element-patterns
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
    - flow/flow-transaction-finalizer-patterns
    - flow/flow-transactional-boundaries
    - flow/flow-versioning-strategy
    - flow/screen-flow-accessibility
  shared:
    - AGENT_CONTRACT.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  templates:
    - flow/FaultPath_Template.md
    - flow/Subflow_Pattern.md
  decision_trees:
    - automation-selection.md
    - flow-pattern-selector.md
  probes:
    - automation-graph-for-sobject.md
    - flow-references-to-field.md
---
# Flow Analyzer Agent

## What This Agent Does

For a given Flow or sObject, decides whether the automation is in the right tool per `standards/decision-trees/automation-selection.md` (Flow vs Apex vs Agentforce), reviews existing Flow definitions for bulkification and fault-path compliance against `skills/flow/flow-bulkification/SKILL.md` and `templates/flow/FaultPath_Template.md`, and flags co-existing Apex triggers or Process Builder that could double-fire.

**Scope:** One Flow file or one sObject per invocation.

---

## Invocation

- **Direct read** — "Follow `agents/flow-analyzer/AGENT.md` for `force-app/main/default/flows/Lead_AutoConvert.flow-meta.xml`"
- **Slash command** — [`/analyze-flow`](../../commands/analyze-flow.md)
- **MCP** — `get_agent("flow-analyzer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `standards/decision-trees/automation-selection.md`
3. `skills/flow/flow-bulkification/SKILL.md`
4. `skills/flow/flow-large-data-volume-patterns/SKILL.md`
5. `templates/flow/FaultPath_Template.md`
6. `templates/flow/Subflow_Pattern.md`
7. `skills/apex/trigger-and-flow-coexistence/SKILL.md`
8. `skills/flow/flow-collection-processing/SKILL.md` — collection bulkification + map-vs-loop signal for Step 3
9. `skills/flow/flow-cross-object-updates/SKILL.md` — Update-Records-via-related-list footguns flagged in Step 3
10. `skills/flow/flow-get-records-optimization/SKILL.md` — Get-Records-in-loop and selective-filter signals
11. `skills/flow/flow-decision-element-patterns/SKILL.md` — decision branching anti-patterns and isChanged()/isNew() pitfalls
12. `skills/flow/flow-resource-patterns/SKILL.md` — variable / formula / template usage signals
13. `skills/flow/flow-record-save-order-interaction/SKILL.md` — before-save vs after-save ordering vs Apex triggers (Step 4 co-existence)
14. `skills/flow/flow-transactional-boundaries/SKILL.md` — when an action commits / when DML rolls back, drives the fault-path verdict
15. `skills/flow/flow-error-monitoring/SKILL.md` — org-level error-email-recipient + fault sink Healthy/Concerning observations
16. `skills/flow/flow-runtime-error-diagnosis/SKILL.md` — symptoms-to-cause map cited in `MIGRATE_TO_APEX` and `FIX_IN_PLACE` rationale
17. `skills/flow/flow-debugging/SKILL.md` — Flow Debug Logs / Interview Logs interpretation when target_org_alias is set
18. `skills/flow/flow-loop-element-patterns/SKILL.md` — `dml-in-loop` / `soql-in-loop` / `subflow-with-DML-in-loop` signal definitions for Step 3 bulkification check
19. `skills/flow/flow-record-locking-and-contention/SKILL.md` — `COEXISTENCE_RISK` / parent-lock signal for Step 4 + Process Observations under load
20. `skills/flow/flow-runtime-context-and-sharing/SKILL.md` — without-sharing audit signal in Process Observations (FLS-bypass risk)
21. `skills/flow/flow-formula-and-expression-patterns/SKILL.md` — picklist `=` vs ISPICKVAL bugs, NULL-propagation, lazy-re-eval-in-loop performance findings
22. `skills/flow/flow-element-naming-conventions/SKILL.md` — naming-quality observation in Process Observations (Decision_1 / Get_Records_2 → maintainability concern)
23. `skills/flow/flow-screen-input-validation-patterns/SKILL.md` — Screen Flows missing input validation = junk-data-in audit finding
24. `skills/flow/flow-action-framework/SKILL.md` — invocable / Apex action element shape; finds wrong list-cardinality at the Flow–Apex boundary
25. `skills/flow/flow-and-platform-events/SKILL.md` — Platform Event publisher / subscriber audit; publish-immediate vs publish-after-commit detection
26. `skills/flow/flow-apex-defined-types/SKILL.md` — Apex-defined type drift in External Services / HTTP Callout payloads
27. `skills/flow/flow-batch-processing-alternatives/SKILL.md` — flow that should have been Apex Queueable/Batch (LDV ceiling exceeded)
28. `skills/flow/flow-data-tables/SKILL.md` — Data Table component misuse (unbounded rows; no column trim)
29. `skills/flow/flow-deployment-and-packaging/SKILL.md` — packaging dependency cycles; missing FlowAccessPermission for the run-as persona
30. `skills/flow/flow-dynamic-choices/SKILL.md` — Record / Picklist / Collection choice set misconfiguration (e.g. unbounded record choice on a 100k-row object)
31. `skills/flow/flow-external-services/SKILL.md` — registered API specs without Named Credential, missing fault path on the generated invocable
32. `skills/flow/flow-for-experience-cloud/SKILL.md` — Screen Flow on a guest user profile without the right Sharing Set / object-access guard
33. `skills/flow/flow-governance/SKILL.md` — naming / ownership / version pinning / retirement signals (stale flows w/ no runs in 90 days)
34. `skills/flow/flow-governor-limits-deep-dive/SKILL.md` — per-entry-point limit budget audit; finds flows that systematically blow CPU / SOQL ceilings
35. `skills/flow/flow-http-callout-action/SKILL.md` — declarative HTTP callouts without Named Credential or fault path
36. `skills/flow/flow-invocable-from-apex/SKILL.md` — invocable contract drift (one-list-in vs one-list-out, null handling)
37. `skills/flow/flow-performance-optimization/SKILL.md` — perf signals (after-save where before-save would do, redundant Get Records)
38. `skills/flow/flow-platform-events-integration/SKILL.md` — high-volume PE design issues; subscriber-side error handling
39. `skills/flow/flow-reactive-screen-components/SKILL.md` — non-reactive screen components in a reactive design (Winter '24+) → UX inefficiency
40. `skills/flow/flow-rollback-patterns/SKILL.md` — Rollback Records element misuse (publish-after-commit PE interaction; partial commit)
41. `skills/flow/flow-screen-lwc-components/SKILL.md` — custom Flow screen LWC contract violations (`@api validate()` missing, FlowAttributeChangeEvent missing)
42. `skills/flow/flow-testing/SKILL.md` — flow has no Flow Tests = test-coverage finding
43. `skills/flow/flow-transaction-finalizer-patterns/SKILL.md` — post-commit work shape; finalizer audit
44. `skills/flow/flow-versioning-strategy/SKILL.md` — version pinning gaps; obsolete versions still referenced by paused interviews
45. `skills/flow/screen-flow-accessibility/SKILL.md` — Screen Flow a11y audit findings
46. `standards/decision-trees/flow-pattern-selector.md` — within-Flow pattern audit (e.g. flow chose Auto-launched + Pause where Scheduled-Triggered would be cleaner)
47. `agents/_shared/REFUSAL_CODES.md` — canonical refusal codes used in the Escalation section
48. `agents/_shared/probes/automation-graph-for-sobject.md` — analyzer also runs the automation-graph probe to detect coexistence
49. `agents/_shared/probes/flow-references-to-field.md` — used to map flow → field references in cross-object audits
50. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `flow_path` or `object_api_name` | yes (one of) | `force-app/main/default/flows/X.flow-meta.xml` OR `Lead` |
| `target_org_alias` | no | enables `list_flows_on_object` for org-side cross-check |

---

## Plan

### Step 1 — Gather the automation surface

If `flow_path` given: parse that single flow.
If `object_api_name` given: scan `force-app/main/default/flows/` for flows whose `<object>` or `<triggerObjectType>` matches, plus triggers on that object.

If `target_org_alias` set:
- Call `list_flows_on_object(object_name=..., active_only=true)` and merge.
- Run the **automation-graph-for-sobject** probe (`agents/_shared/probes/automation-graph-for-sobject.md`) to surface every active piece of automation on the object — Flows, Process Builders, Workflow Rules, Apex Triggers, Validation Rules, Approval Processes. Cite as `{"type":"probe","id":"automation-graph-for-sobject"}`.
- Surface the probe's `flags[]` in Process Observations (`MULTIPLE_RECORD_TRIGGERED_FLOWS`, `PROCESS_BUILDER_PRESENT`, `TRIGGER_AND_FLOW_COEXIST`).

### Step 2 — Decide the correct tool

For each flow, walk `standards/decision-trees/automation-selection.md`:
- Does the flow make a callout? (Only External Services can — most cases should be Apex.)
- Does it loop > 100 elements? (Flow bulkification limits apply.)
- Is it record-triggered and needs async? (Queueable > Flow async.)
- Does it need custom error handling beyond Screen + Fault?
- Is it a user-facing decision agent? (Agentforce, not Flow.)

Record which branch the flow lands on. If the branch says "use Apex", flag the flow as `SHOULD_MIGRATE`.

### Step 3 — Findings catalog (bulkification + perf + UX + governance)

Walk every element in the flow and apply the catalog below. Each finding cites the skill that defines the signal.

| Check | Signal | Severity | Skill |
|---|---|---|---|
| **dml-in-loop** | `<assignments>` with DML-adjacent elements (Update Records / Create Records / Delete Records) inside a loop | P0 | `flow-loop-element-patterns` |
| **soql-in-loop** | Get Records inside a loop | P0 | `flow-loop-element-patterns` |
| **no-fault-path** | DML / callout element has no outbound edge labelled as fault | P1 | `fault-handling`, `templates/flow/FaultPath_Template.md` |
| **untyped-collection** | Collection var without `<objectType>` | P2 | `flow-collection-processing` |
| **subflow-without-contract** | Subflow called but no matching subflow spec per `Subflow_Pattern.md` | P2 | `subflows-and-reusability` |
| **callout-no-named-credential** | HTTP Callout action or generated External Service action with hard-coded URL or basic-auth header | P0 | `flow-http-callout-action`, `flow-external-services` |
| **callout-no-fault-path** | HTTP Callout action without a fault edge | P0 | `flow-http-callout-action` |
| **invocable-list-mismatch** | Apex action element passes a single record where the @InvocableMethod expects `List<>` (or vice versa) | P1 | `flow-action-framework`, `flow-invocable-from-apex` |
| **rollback-with-publish-immediate-pe** | Rollback Records element in a flow that also publishes a publish-immediate Platform Event (rollback does not undo the PE) | P0 | `flow-rollback-patterns`, `flow-platform-events-integration` |
| **picklist-equality-bug** | Decision condition compares a picklist via `=` instead of `ISPICKVAL()` | P1 | `flow-formula-and-expression-patterns` |
| **lazy-formula-in-loop** | Formula resource referencing a Get-Records output inside a loop body (re-evaluated each iteration) | P1 | `flow-formula-and-expression-patterns` |
| **without-sharing-on-screen-flow** | Screen flow set to System Context without explicit FLS guard on a sensitive object | P0 | `flow-runtime-context-and-sharing` |
| **screen-flow-no-input-validation** | Screen with input fields and no component-level `validationRule` or cross-field validator | P1 | `flow-screen-input-validation-patterns` |
| **screen-flow-no-a11y** | Screen with image / icon component lacking alt-text or label-for-element | P1 | `screen-flow-accessibility` |
| **screen-component-non-reactive** | Custom screen component used in a Winter '24+ reactive context but missing `@api` getter-setter for reactivity | P2 | `flow-reactive-screen-components`, `flow-screen-lwc-components` |
| **data-table-unbounded** | Data Table component bound to a collection sourced from a Get Records with no row cap | P1 | `flow-data-tables` |
| **dynamic-choice-unbounded** | Record Choice Set against an object with > 50k rows and no filter | P1 | `flow-dynamic-choices` |
| **decision-no-default-outcome** | Decision element without a labelled default outcome | P2 | `flow-decision-element-patterns` |
| **auto-named-elements** | Element labels like `Decision_1`, `Get_Records_2`, `Assignment_3` (auto-generated, never renamed) | P2 | `flow-element-naming-conventions` |
| **stale-flow** | Flow active for > 90 days with zero runs (probe: `FlowExecutionErrorEvent` + Tooling stats) | P2 | `flow-governance` |
| **no-version-pinned-active-paused-interviews** | Active version retired but paused interviews still reference an obsolete version | P1 | `flow-versioning-strategy` |
| **no-test-coverage** | Flow has no associated `FlowTest` records | P1 | `flow-testing` |
| **missing-flow-access-permission** | Deployed flow lacks a FlowAccessPermission for the run-as persona | P1 | `flow-deployment-and-packaging` |
| **ldv-ceiling-exceeded** | Flow's entry-criteria estimate pulls > 50k rows in a single run | P0 | `flow-large-data-volume-patterns`, `flow-batch-processing-alternatives` |
| **cpu-budget-blown** | Flow systematically reports CPU-limit warnings in Setup → Flow Errors | P1 | `flow-governor-limits-deep-dive`, `flow-performance-optimization` |
| **after-save-where-before-save-fits** | After-save flow that only sets fields on the same record (no DML, no related-record updates) | P2 | `flow-performance-optimization`, `flow-record-save-order-interaction` |
| **finalizer-misuse** | Auto-launched flow called as a Queueable finalizer without the documented Platform Event bridge | P1 | `flow-transaction-finalizer-patterns` |
| **experience-cloud-guest-without-guard** | Screen Flow exposed to a Guest User Profile without the matching Sharing Set / object-access guard | P0 | `flow-for-experience-cloud` |
| **subscriber-no-error-handling** | PE-triggered flow without a fault path on the publisher and no replay strategy on the subscriber | P1 | `flow-platform-events-integration`, `flow-and-platform-events` |
| **apex-defined-type-drift** | External Service or HTTP Callout returns an Apex-defined type whose schema has drifted from the registered OpenAPI spec | P1 | `flow-apex-defined-types` |

### Step 4 — Co-existence check

If the object has **both** triggers and record-triggered flows firing on the same event:

- Flag as `COEXISTENCE_RISK`.
- Recommend consolidating per `skills/apex/trigger-and-flow-coexistence` — typically: do all work in Apex OR Flow, not both.
- Cite the ordering rule: "For a given event, Flow executes after Apex before-triggers and after Apex after-triggers."

### Step 5 — Recommendations

For each flow analyzed, produce:
- **Verdict**: `KEEP` / `FIX_IN_PLACE` / `MIGRATE_TO_APEX` / `MIGRATE_TO_AGENTFORCE`
- **If FIX_IN_PLACE**: list the specific element changes needed.
- **If MIGRATE_TO_APEX**: produce a migration plan citing `trigger-framework` and `flow-bulkification` skills; recommend running the `trigger-consolidator` agent after.

---

## Output Contract

1. **Summary** — flow(s) analyzed, verdict distribution, confidence.
2. **Per-flow report** — verdict, decision-tree branch, findings table, recommended fixes.
3. **Co-existence section** — if triggers + flows overlap on the same event.
4. **Process Observations** — peripheral signal noticed while analyzing, separate from the direct verdicts. Each observation cites its evidence (flow name, element id, MCP probe count).
   - **Healthy** — e.g. fault paths are present on every DML element; subflows already follow `Subflow_Pattern.md`; collection variables are typed; `list_flows_on_object` shows no duplicate record-triggered flows on the same event.
   - **Concerning** — e.g. the object has multiple active record-triggered flows on the same event (ordering is non-deterministic at scale); a Screen Flow performs DML inside a loop without chunking; no active error-email recipient for the org.
   - **Ambiguous** — e.g. a flow whose verdict depends on record volume the agent can't see without a target org; a subflow called from multiple parents with differing input contracts.
   - **Suggested follow-ups** — `trigger-consolidator` on any `COEXISTENCE_RISK` finding; `apex-refactorer` + `test-class-generator` on `MIGRATE_TO_APEX` verdicts; `agentforce-builder` on `MIGRATE_TO_AGENTFORCE` verdicts.
5. **`dimensions_skipped[]`** — every audit dimension touched but not fully checked (e.g. test-coverage counted but not loaded; CPU-budget probed only via static estimate, not real run-stats); each entry uses `state: count-only | partial | not-run` per `agents/_shared/DELIVERABLE_CONTRACT.md`.
6. **Citations** — decision-tree branch, skill ids, template paths, probe ids, MCP tool names.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/flow-analyzer/<run_id>.md`
- **JSON envelope:** `docs/reports/flow-analyzer/<run_id>.json`
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

- `flow_path` AND `object_api_name` both omitted → `REFUSAL_MISSING_INPUT`.
- Both supplied but they conflict (path's flow targets a different object) → `REFUSAL_INPUT_AMBIGUOUS`.
- Flow XML does not parse → `REFUSAL_INPUT_AMBIGUOUS`; ask the user for a valid `.flow-meta.xml`.
- `target_org_alias` supplied but `describe_org` fails → `REFUSAL_ORG_UNREACHABLE`.
- `object_api_name` supplied does not exist on the org → `REFUSAL_OBJECT_NOT_FOUND`.
- Flow is in a managed-package namespace → `REFUSAL_MANAGED_PACKAGE`; surface read-only audit findings, do not propose changes.
- Flow uses managed-package invocable actions the agent cannot resolve → continue with `confidence: MEDIUM` for those actions; not a hard refusal.
- Object scope returns > 25 active flows → top-25 partial audit + `REFUSAL_OVER_SCOPE_LIMIT`; recommend re-running per-flow.
- Flow is a Screen Flow (not record-triggered) AND the question implied record-triggered behavior → `REFUSAL_INPUT_AMBIGUOUS`; clarify before producing a verdict.
- Audit detects a feature that requires a license the org doesn't have (Slack actions without Salesforce-for-Slack, Orchestrator without proper edition) → `REFUSAL_FEATURE_DISABLED` for that finding row only; rest of audit continues.
- Required skill cited in the Plan resolves to a TODO or missing path → `REFUSAL_NEEDS_HUMAN_REVIEW`.

---

## What This Agent Does NOT Do

- Does not modify the flow XML.
- Does not auto-run `trigger-consolidator` — recommends it.
- Does not make judgments about "Flow is bad" / "Apex is bad" — follows the decision tree.
