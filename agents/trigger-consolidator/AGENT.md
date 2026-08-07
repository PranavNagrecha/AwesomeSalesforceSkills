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
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  probes:
    - automation-graph-for-sobject.md
  templates:
    - apex/TriggerControl.cls
    - apex/TriggerHandler.cls
    - apex/cmdt/Trigger_Setting__mdt/
    - apex/cmdt/Trigger_Setting__mdt/fields/
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
2. `AGENT_RULES.md`
3. `agents/_shared/DELIVERABLE_CONTRACT.md`
4. `agents/_shared/REFUSAL_CODES.md`

### Trigger framework canon
5. `skills/apex/trigger-framework` — the target shape. Without it "consolidate" has no definition and the agent invents a handler contract that the next class on the object will not match
6. `skills/apex/recursive-trigger-prevention` — merging N triggers merges N re-entry guards, and the most common consolidation bug is keeping one static flag where each original trigger had its own. Says which guard survives
7. `skills/apex/apex-trigger-context-variables` — `Trigger.oldMap` is null on insert and `Trigger.new` is read-only after-context; a method lifted out of a before trigger into an after slot fails on exactly this
8. `skills/apex/apex-trigger-bypass-and-killswitch-patterns` — the deactivation plan in Step 5 depends on the bypass being real. Tells the agent what a working kill switch looks like as opposed to a commented-out block
9. `skills/apex/order-of-execution-deep-dive` — Step 3's ordering adjudication: which of the merged bodies may safely mutate the record in place, and what a later step in the save order will overwrite regardless
10. `skills/apex/trigger-and-flow-coexistence` — the Step 1 probe usually finds record-triggered Flows on the same object. Decides whether consolidation is the right move at all or whether the Flow is the duplicate

### Architecture
11. `skills/apex/apex-design-patterns` — where the merged logic lands once it leaves the trigger files: Domain vs Service vs Selector, so the handler stays a router rather than becoming the god class the consolidation was supposed to prevent
12. `skills/apex/apex-collections-patterns` — N single-record trigger bodies concatenated into one handler is still N loops. These are the map/set idioms that turn the merge into one bulk pass

### Cross-automation visibility
13. `agents/_shared/probes/automation-graph-for-sobject.md` — finds Flows / PB / WF on the same SObject
14. `standards/decision-trees/automation-selection.md` — when consolidating reveals the wrong tier of automation

### Vertical-specific trigger patterns (object-aware mode)
15. `skills/apex/case-trigger-patterns` — on Case, escalation, entitlement and Email-to-Case each write back to the record; a naive merge re-fires them
16. `skills/apex/opportunity-trigger-patterns` — Opportunity carries stage/amount roll-ups and OpportunityLineItem cascades whose ordering relative to the merged handler is the whole risk
17. `skills/apex/lead-conversion-customization` — Lead triggers fire in a special sequence during Convert; a handler that assumes normal insert/update context misbehaves only on the conversion path, which no test written from the merged code will cover
18. `skills/apex/entitlement-apex-hooks` — Case milestone completion is driven from Apex hooks that the original triggers may own; the consolidation must keep the hook attached
19. `skills/apex/npsp-trigger-framework-extension` — NPSP orgs run TDTM, a second framework the agent must coexist with rather than replace. Consolidating NPSP-managed triggers into a custom handler breaks package upgrades

### Async offload (when triggers should defer work)
20. `skills/apex/async-apex` — consolidation frequently reveals that the merged synchronous body no longer fits one transaction; this is the decision of what may move off the synchronous path at all
21. `skills/apex/apex-future-method-patterns` — `@future` calls inside the merged bodies do not compose: limits are per-transaction, and two former triggers each calling one may exceed them once merged
22. `skills/apex/apex-queueable-patterns` — the default landing place for deferred work, plus the chaining depth limits that decide whether the deferral is even legal from a trigger context
23. `skills/apex/platform-events-apex` — publish-after-commit semantics, for merged logic that notified another system and must keep doing so at the same point in the transaction
24. `skills/apex/change-data-capture-apex` — when the right answer is that the merged after-trigger work belongs in a CDC subscriber rather than in the handler at all

### DML / locking under consolidated triggers
25. `skills/apex/apex-dml-patterns` — partial-success vs all-or-none changes meaning when two former triggers' DML lands in one transaction: one failing row can now roll back work the other trigger used to commit
26. `skills/apex/apex-savepoint-and-rollback` — whether the merged handler needs an explicit savepoint boundary that the separate triggers got for free
27. `skills/apex/mixed-dml-and-setup-objects` — if any merged body touched User / permission-set objects, combining it with data DML in one transaction raises `MIXED_DML_OPERATION` where the split triggers never did
28. `skills/apex/record-locking-and-contention` — merging serialises what used to interleave; the parent-record lock window gets longer, which is where consolidation shows up as `UNABLE_TO_LOCK_ROW` under load

### Error handling / governance
29. `skills/apex/error-handling-framework` — one handler means one failure surface: the framework that keeps a failure in one merged concern from taking down the others
30. `skills/apex/exception-handling` — which exceptions the handler may catch versus must let propagate, so consolidation does not silently swallow an error the original trigger surfaced to the user
31. `skills/apex/common-apex-runtime-errors` — the symptom-to-cause map for the errors a consolidation actually produces in the first week
32. `skills/apex/custom-logging-and-monitoring` — `Application_Log__c`; Step 5's 24-hour monitoring window is meaningless without the logging the merged handler is supposed to write
33. `skills/apex/custom-metadata-in-apex` — `Trigger_Setting__mdt` access pattern, and why the CMDT read must not itself consume a SOQL query per record
34. `skills/apex/feature-flags-and-kill-switches` — the rollback story for Step 5: flipping `Is_Active__c` only works if the flag is read where the skill says it should be
35. `skills/apex/governor-limits` — the merged handler inherits the sum of the old triggers' SOQL, DML and CPU. This is the budget the consolidation has to fit inside, and the reason a naive merge fails at bulk size

### SOQL inside trigger handlers
36. `skills/apex/soql-fundamentals` — relationship and bind syntax for the queries being hoisted out of the merged bodies into a single bulk query
37. `skills/apex/apex-aggregate-queries` — where two former triggers each rolled up child records, the merge should do it once as an aggregate rather than twice in a loop

### Tests after consolidation
38. `skills/apex/test-class-standards` — what the post-consolidation test must assert, given that coverage alone cannot show behaviour was preserved
39. `skills/apex/test-data-factory-patterns` — the merged handler needs one bulk fixture rather than each old trigger's ad-hoc setup
40. `skills/apex/apex-test-setup-patterns` — `@TestSetup` vs per-method setup for a handler whose methods now share state, where a shared fixture can hide the recursion bug the tests exist to catch

### Templates
41. `templates/apex/TriggerHandler.cls`
42. `templates/apex/TriggerControl.cls`
43. `templates/apex/cmdt/Trigger_Setting__mdt/` — the CMDT the framework switches on. Read the whole folder, not just the object file: `fields/` holds `Object_API_Name__c`, `Handler_Class__c` and `Is_Active__c`, and Step 4 emits a record against all three. An `.object-meta.xml` with no field files does not deploy.

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

### Step 6 — Gate C: verify the emitted code before returning it

This agent hands the user a deployable trigger + handler, so `AGENT_CONTRACT.md` rule 11 applies. Run the three checks in [`AGENT_CONTRACT.md` § Gate C](../_shared/AGENT_CONTRACT.md#gate-c--self-verification-for-code-emitting-agents) and report each outcome — a check that did not run is reported as not run.

1. **Symbol grounding** — every field the handler reads or writes appeared in the Step 1 discovery output, not in the model's picture of the object.
2. **Identifier provenance** — each non-platform `Type.method(...)` is quoted from `templates/apex/TriggerHandler.cls` or `templates/apex/TriggerControl.cls`, and the CMDT field names in Step 4 match `templates/apex/cmdt/Trigger_Setting__mdt/fields/`.
3. **Compile** — with a `target_org_alias`, `sf project deploy start --dry-run --test-level RunLocalTests`; without one, state that no compile check ran and cap `confidence` at MEDIUM.

Then the check specific to this agent: **consolidation replaces a platform-nondeterministic execution order with a fixed one.** N triggers on an sObject fire in an order Salesforce does not guarantee; one handler runs its methods in the order you wrote them. If the plan never asked which order is intended, the output is a silent behaviour change, and Gate C is the last place to catch it — confirm the ordering was adjudicated in Step 3 with the user, and refuse to present the consolidation as behaviour-preserving if it was not.

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
