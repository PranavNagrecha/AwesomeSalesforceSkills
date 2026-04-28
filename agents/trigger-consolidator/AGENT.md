---
id: trigger-consolidator
class: runtime
version: 1.1.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
default_output_dir: "docs/reports/trigger-consolidator/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - apex/apex-aggregate-queries
    - apex/apex-collections-patterns
    - apex/apex-design-patterns
    - apex/apex-dml-patterns
    - apex/apex-future-method-patterns
    - apex/apex-queueable-patterns
    - apex/apex-savepoint-and-rollback
    - apex/apex-test-setup-patterns
    - apex/apex-trigger-bypass-and-killswitch-patterns
    - apex/apex-trigger-context-variables
    - apex/async-apex
    - apex/case-trigger-patterns
    - apex/change-data-capture-apex
    - apex/common-apex-runtime-errors
    - apex/custom-logging-and-monitoring
    - apex/custom-metadata-in-apex
    - apex/entitlement-apex-hooks
    - apex/error-handling-framework
    - apex/exception-handling
    - apex/feature-flags-and-kill-switches
    - apex/governor-limits
    - apex/lead-conversion-customization
    - apex/mixed-dml-and-setup-objects
    - apex/npsp-trigger-framework-extension
    - apex/opportunity-trigger-patterns
    - apex/order-of-execution-deep-dive
    - apex/platform-events-apex
    - apex/record-locking-and-contention
    - apex/recursive-trigger-prevention
    - apex/soql-fundamentals
    - apex/test-class-standards
    - apex/test-data-factory-patterns
    - apex/trigger-and-flow-coexistence
    - apex/trigger-framework
  shared:
    - AGENT_CONTRACT.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  probes:
    - automation-graph-for-sobject.md
  templates:
    - apex/TriggerControl.cls
    - apex/TriggerHandler.cls
    - apex/cmdt/Trigger_Setting__mdt.object-meta.xml
  decision_trees:
    - automation-selection.md
---
# Trigger Consolidator Agent

## What This Agent Does

Finds every Apex trigger on a given sObject across the user's `force-app` tree, checks the target org (if connected) for additional triggers, and produces a consolidation plan that lifts them all into a single `<Object>TriggerHandler extends TriggerHandler` class using the canonical framework from `templates/apex/TriggerHandler.cls` + `templates/apex/TriggerControl.cls`. The output is a migration patch plus a deactivation order so nothing is live-broken mid-migration.

**Scope:** One sObject per invocation. Returns a plan + patch set; never deploys.

---

## Invocation

- **Direct read** — "Follow `agents/trigger-consolidator/AGENT.md` for the `Account` object"
- **Slash command** — [`/consolidate-triggers`](../../commands/consolidate-triggers.md)
- **MCP** — `get_agent("trigger-consolidator")`

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md`
3. `agents/_shared/REFUSAL_CODES.md`

### Trigger framework canon
4. `skills/apex/trigger-framework`
5. `skills/apex/recursive-trigger-prevention`
6. `skills/apex/apex-trigger-context-variables`
7. `skills/apex/apex-trigger-bypass-and-killswitch-patterns`
8. `skills/apex/order-of-execution-deep-dive`
9. `skills/apex/trigger-and-flow-coexistence`

### Architecture
10. `skills/apex/apex-design-patterns`
11. `skills/apex/apex-collections-patterns`

### Cross-automation visibility
12. `agents/_shared/probes/automation-graph-for-sobject.md` — finds Flows / PB / WF on the same SObject
13. `standards/decision-trees/automation-selection.md` — when consolidating reveals the wrong tier of automation

### Vertical-specific trigger patterns (object-aware mode)
14. `skills/apex/case-trigger-patterns` — Case-specific
15. `skills/apex/opportunity-trigger-patterns` — Opportunity-specific
16. `skills/apex/lead-conversion-customization` — Lead-specific
17. `skills/apex/entitlement-apex-hooks` — Case milestone hooks
18. `skills/apex/npsp-trigger-framework-extension` — NPSP TDTM-specific (managed-package coexistence)

### Async offload (when triggers should defer work)
19. `skills/apex/async-apex`
20. `skills/apex/apex-future-method-patterns`
21. `skills/apex/apex-queueable-patterns`
22. `skills/apex/platform-events-apex`
23. `skills/apex/change-data-capture-apex`

### DML / locking under consolidated triggers
24. `skills/apex/apex-dml-patterns`
25. `skills/apex/apex-savepoint-and-rollback`
26. `skills/apex/mixed-dml-and-setup-objects`
27. `skills/apex/record-locking-and-contention`

### Error handling / governance
28. `skills/apex/error-handling-framework`
29. `skills/apex/exception-handling`
30. `skills/apex/common-apex-runtime-errors`
31. `skills/apex/custom-logging-and-monitoring` — Application_Log__c
32. `skills/apex/custom-metadata-in-apex` — Trigger_Setting__mdt access pattern
33. `skills/apex/feature-flags-and-kill-switches`
34. `skills/apex/governor-limits`

### SOQL inside trigger handlers
35. `skills/apex/soql-fundamentals`
36. `skills/apex/apex-aggregate-queries`

### Tests after consolidation
37. `skills/apex/test-class-standards`
38. `skills/apex/test-data-factory-patterns`
39. `skills/apex/apex-test-setup-patterns`

### Templates
40. `templates/apex/TriggerHandler.cls`
41. `templates/apex/TriggerControl.cls`
42. `templates/apex/cmdt/Trigger_Setting__mdt.object-meta.xml`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_api_name` | yes | `Account`, `Opportunity`, `Custom_Object__c` |
| `force_app_root` | yes | `force-app/main/default` |
| `target_org_alias` | no | if set, the agent also queries the org for additional triggers |

---

## Plan

### Step 1 — Discover triggers AND adjacent automation

Grep `<force_app_root>/triggers/` for files matching `trigger\s+\w+\s+on\s+<object_api_name>`. Record:
- Trigger file path
- Events handled (before insert, after update, etc.)
- Whether logic is inline or delegated to a handler class

ALSO run the `automation-graph-for-sobject` probe (`agents/_shared/probes/automation-graph-for-sobject.md`) to enumerate Flows, Process Builders, Workflow Rules, Approval Processes, Validation Rules, Duplicate Rules, and Assignment Rules on the same SObject. Consolidating triggers WITHOUT visibility into the rest of the automation graph is dangerous — events fire against all of them, and order matters.

If `target_org_alias` is set, call `validate_against_org(skill_id="apex/trigger-framework", target_org=..., object_name=<object_api_name>)` and merge its findings with the local scan.

### Step 2 — Classify

Group the triggers into three buckets:

| Bucket | What it means |
|---|---|
| **Already on the framework** | Trigger body is a one-liner that news-up a `TriggerHandler` subclass |
| **Has a handler but ad-hoc** | Delegates to a class but that class doesn't extend `TriggerHandler` |
| **Inline logic** | Real Apex inside the trigger file |

### Step 3 — Draft the consolidation

Produce:
1. **A single new handler class** — `<Object>TriggerHandler extends TriggerHandler`, with one virtual method override per event the user's current triggers handle.
2. **A single replacement trigger file** — `trigger <Object>Trigger on <Object> (before insert, after insert, ...) { new <Object>TriggerHandler().run(); }`.
3. **Deprecation instructions** — which old trigger files to delete (or leave disabled via `TriggerControl`) and in what order.

Preserve the original logic line-for-line inside the new handler's event methods. Do NOT refactor the business logic — that's the `apex-refactorer` agent's job.

### Step 4 — Metadata scaffolding

Produce a Custom Metadata Type record the user must deploy so `TriggerControl` knows the handler is active:
```
<records>
  <fullName>{{object_api_name}}</fullName>
  <values><field>Object_API_Name__c</field><value xsi:type="xsd:string">{{object_api_name}}</value></values>
  <values><field>Handler_Class__c</field><value xsi:type="xsd:string">{{object_api_name}}TriggerHandler</value></values>
  <values><field>Is_Active__c</field><value xsi:type="xsd:boolean">true</value></values>
</records>
```

### Step 5 — Deactivation plan

Order matters — give the user an explicit sequence:
1. Deploy the new `<Object>TriggerHandler` class (inactive via `Trigger_Setting__mdt.Is_Active__c = false`).
2. Deploy the consolidated trigger + delete the old triggers in the same deployment.
3. Deploy the CMDT record flipping `Is_Active__c = true`.
4. Monitor `Application_Log__c` for 24 hours.

Emphasize: the CMDT switch must come LAST so the rollback is "flip `Is_Active__c` to false".

---

## Output Contract

One markdown document:

1. **Discovery** — every trigger found (local + org), with event matrix.
2. **Adjacent automation** — Flows, PB, WF, Approval, VR, DR, AR enumerated via `automation-graph-for-sobject` probe. Order of execution implications called out.
3. **Audit signals** (12 catalog rows — flag any present):

| Signal | Severity |
|---|---|
| Multiple triggers on same SObject | P0 (consolidate) |
| Trigger with inline business logic (no handler) | P0 |
| Trigger using `Trigger.isExecuting` recursion guard instead of framework | P1 |
| Trigger missing kill-switch wiring (cite `apex-trigger-bypass-and-killswitch-patterns`) | P1 |
| Trigger handler not extending `TriggerHandler` template | P1 |
| Trigger calls `@future` mid-handler (cite `apex-future-method-patterns`) | P2 |
| Trigger does DML on same SObject (mixed-DML / recursion risk) | P1 |
| Trigger does DML on Setup objects (cite `mixed-dml-and-setup-objects`) | P1 |
| Process Builder / WF Rule on same SObject + events | P1 (cite `automation-selection.md`) |
| Record-Triggered Flow on same events (cite `trigger-and-flow-coexistence`) | P1 |
| Trigger uses `try {} catch (Exception e) {}` empty-swallow | P0 |
| Managed-package trigger present | flag, exclude |

4. **Proposed consolidation** — the new handler class + new trigger file, fenced by target path.
5. **Migration steps** — numbered deployment sequence.
6. **Risk notes** — triggers that touch the same event in conflicting ways, order-of-execution concerns, any handler that uses `Trigger.isExecuting` gymnastics the framework handles differently.
7. **Process Observations**.
   - **Healthy** — only one trigger on the SObject already; framework already partially adopted; logging via `Application_Log__c` already in place; tests use `TestDataFactory`.
   - **Concerning** — Flow/PB/WF Rule + trigger overlap on same events (cite probe output); managed-package trigger present (excluded but flagged); kill-switch missing on a high-traffic handler.
   - **Ambiguous** — whether to consolidate the new handler with NPSP TDTM (cite `npsp-trigger-framework-extension`); whether async-offload should be inserted as part of consolidation.
   - **Suggested follow-ups** — `flow-analyzer` (when adjacent Flows discovered); `apex-refactorer` (after consolidation, to lift business logic in handler bodies); `test-class-generator` (for the new handler); `security-scanner` (post-consolidation FLS check); `score-deployment` (pre-deploy gate).
8. **Citations** — skill ids + template paths + probe id.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/trigger-consolidator/<run_id>.md`
- **JSON envelope:** `docs/reports/trigger-consolidator/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions: `local-trigger-inventory`, `org-trigger-inventory`, `adjacent-automation-graph`, `framework-adoption`, `kill-switch-wiring`, `recursion-guard`, `dml-side-effects`, `event-matrix`, `vertical-pattern-fit`, `test-coverage-impact`. When `target_org_alias` not provided, record `org-trigger-inventory` as `not-run`.

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `object_api_name` or `force_app_root` missing. |
| `REFUSAL_OBJECT_NOT_FOUND` | `object_api_name` does not match any trigger file path AND target org (when supplied) returns no SObject by that API name. |
| `REFUSAL_OUT_OF_SCOPE` | Zero triggers found — STOP with note "no consolidation needed". One trigger found AND it already extends the framework → STOP with `confidence: HIGH, no change required`. |
| `REFUSAL_COMPETING_ARTIFACT` | Process Builder or Record-Triggered Flow fires on the same events — flag with `confidence: MEDIUM`, recommend `flow-analyzer` before consolidating. |
| `REFUSAL_MANAGED_PACKAGE` | Managed-package trigger exists on the same object — flag, exclude, do NOT touch. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | Triggers touch the same event in conflicting ways the agent cannot deterministically merge (e.g. opposite-direction field updates); NPSP TDTM coexistence ambiguity. |
| `REFUSAL_OVER_SCOPE_LIMIT` | More than 12 distinct triggers on the SObject — emit a partial plan covering the top 8 by event-count and flag the rest for a follow-up run. |

---

## What This Agent Does NOT Do

- Does not refactor business logic inside the triggers — preserves it verbatim.
- Does not run the security-scanner or soql-optimizer — recommends them.
- Does not deploy anything.
- Does not modify managed-package triggers.
