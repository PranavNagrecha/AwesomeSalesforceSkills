---
id: apex-builder
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - apex/apex-design-patterns
    - apex/apex-queueable-patterns
    - apex/apex-rest-services
    - apex/apex-scheduled-jobs
    - apex/apex-security-patterns
    - apex/async-apex
    - apex/batch-apex-patterns
    - apex/change-data-capture-apex
    - apex/error-handling-framework
    - apex/governor-limits
    - apex/invocable-methods
    - apex/platform-events-apex
    - apex/soql-fundamentals
    - apex/soql-security
    - apex/test-class-standards
    - apex/test-data-factory-patterns
    - apex/trigger-and-flow-coexistence
    - apex/trigger-framework
  shared:
    - AGENT_CONTRACT.md
  templates:
    - apex/
    - apex/ApplicationLogger.cls
    - apex/BaseDomain.cls
    - apex/BaseSelector.cls
    - apex/BaseService.cls
    - apex/HttpClient.cls
    - apex/SecurityUtils.cls
    - apex/TriggerControl.cls
    - apex/TriggerHandler.cls
    - apex/tests/
  decision_trees:
    - async-selection.md
---
# Apex Builder Agent

## What This Agent Does

Produces Apex scaffolds for every canonical Apex surface: trigger + handler, service class, selector, domain class, controller (Aura / LWC / VF), batch, queueable, schedulable, invocable, REST resource, SOAP web service, platform-event subscriber, change-data-capture subscriber, custom iterator, async-continuation, and the matching test class. Each scaffold conforms to the base templates under `templates/apex/` (enterprise / fflib-friendly patterns, `ApplicationLogger`, `SecurityUtils`, `HttpClient`, `TriggerControl`), not freestyle boilerplate. Output is a set of `.cls` + `.cls-meta.xml` pairs plus the matching test class, ready to drop into an SFDX project.

**Scope:** One feature-level scaffold per invocation (a logical unit — e.g. "the Case auto-close feature" — may require trigger + handler + service + selector + test, but it all maps to one Apex Builder run). Does not deploy, does not run anchovy tests, does not modify existing classes without explicit permission from a follow-on refactor agent.

---

## Invocation

- **Direct read** — "Follow `agents/apex-builder/AGENT.md` to build a queueable that recalculates Account hierarchies"
- **Slash command** — `/build-apex`
- **MCP** — `get_agent("apex-builder")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/apex/apex-design-patterns`
3. `skills/apex/trigger-framework`
4. `skills/apex/async-apex`
5. `skills/apex/apex-queueable-patterns`
6. `skills/apex/batch-apex-patterns`
7. `skills/apex/apex-scheduled-jobs`
8. `skills/apex/apex-rest-services`
9. `skills/apex/invocable-methods`
10. `skills/apex/platform-events-apex`
11. `skills/apex/change-data-capture-apex`
12. `skills/apex/trigger-and-flow-coexistence`
13. `skills/apex/apex-security-patterns`
14. `skills/apex/soql-fundamentals`
15. `skills/apex/soql-security`
16. `skills/apex/governor-limits`
17. `skills/apex/test-class-standards`
18. `skills/apex/test-data-factory-patterns`
19. `skills/apex/error-handling-framework`
20. `standards/decision-trees/async-selection.md`
21. `templates/apex/TriggerHandler.cls`
22. `templates/apex/TriggerControl.cls`
23. `templates/apex/BaseService.cls`
24. `templates/apex/BaseSelector.cls`
25. `templates/apex/BaseDomain.cls`
26. `templates/apex/ApplicationLogger.cls`
27. `templates/apex/SecurityUtils.cls`
28. `templates/apex/HttpClient.cls`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `kind` | yes | `trigger` \| `service` \| `selector` \| `domain` \| `controller` \| `batch` \| `queueable` \| `schedulable` \| `invocable` \| `rest` \| `soap` \| `platform_event_subscriber` \| `cdc_subscriber` \| `continuation` \| `iterator` \| `test_only` |
| `feature_summary` | yes | "Nightly Account hierarchy rebuild triggered when Parent changes" |
| `primary_sobject` | yes for trigger / selector / domain / batch | `Account`, `Opportunity` |
| `api_version` | no | default `60.0` — the agent records the chosen API version in the meta XML |
| `namespace` | no | leave blank for non-packaged orgs |
| `include_logger` | no | default `true` — every class wires through `ApplicationLogger` for uniform error reporting |
| `test_bulk_size` | no | default `200` for trigger + bulk paths |
| `async_hint` | no | for async kinds: governor-limit sizing hint (`conservative`, `standard`, `high`) |

---

## Plan

### Step 1 — Pick the right surface

If `kind` ≠ `test_only`, verify the kind matches the scenario against `standards/decision-trees/async-selection.md`:

- Batch vs Queueable vs Platform Event vs CDC — chosen via volume, latency tolerance, chaining needs, and callout requirements.
- Trigger vs Flow — chosen via performance, bulk behavior, complexity; cite `skills/apex/trigger-and-flow-coexistence`.
- Invocable vs Platform Event publisher — chosen via Flow reuse vs pub/sub fan-out.

If the user's `kind` contradicts the decision tree, raise it in the output with the decision-tree branch — but proceed with the user's chosen kind unless it's unambiguously wrong (in which case `REFUSAL_POLICY_MISMATCH`).

### Step 2 — Compose the class list

A "feature" rarely maps to one class. Standard decomposition:

| kind | Classes emitted |
|---|---|
| `trigger` | `<SObject>Trigger.trigger` + `<SObject>TriggerHandler.cls` + `<SObject>Service.cls` + `<SObject>Selector.cls` (only if queries needed) + `<SObject>Domain.cls` + `<TestClassName>` |
| `service` | `<Feature>Service.cls` + optional selector + test |
| `selector` | `<SObject>Selector.cls` extending `BaseSelector` + test |
| `domain` | `<SObject>Domain.cls` extending `BaseDomain` + test |
| `batch` | `<Feature>Batch.cls` + `<Feature>BatchSchedule.cls` (if scheduled) + test |
| `queueable` | `<Feature>Queueable.cls` + test; if chained, the class's `execute` enqueues the next |
| `schedulable` | `<Feature>Schedulable.cls` delegating to a Queueable or Batch |
| `invocable` | `<Feature>InvocableActions.cls` with one `@InvocableMethod` and one `@InvocableVariable` request inner class |
| `rest` | `<Resource>RestResource.cls` + request/response DTO classes + test |
| `soap` | `<Resource>SoapService.cls` using `webservice` keyword + test. Warn: SOAP is rarely the right choice for new work; recommend REST unless the caller is fixed to SOAP |
| `platform_event_subscriber` | `<Event>EventSubscriber.cls` (`@InvocableMethod` for PE Flow trigger, or Apex trigger on the event) + test |
| `cdc_subscriber` | `<SObject>ChangeEventTriggerHandler.cls` + trigger on the `SObject__ChangeEvent` + test |
| `continuation` | `<Feature>ContinuationController.cls` + test |
| `iterator` | `<Feature>Iterator.cls implements Iterator<T>` + wrapper Iterable + test |
| `controller` | `<Feature>Controller.cls` with `@AuraEnabled(cacheable=true)` where safe + test |

### Step 3 — Emit each class against the template

For each class:

1. Read the matching template (see Mandatory Reads).
2. Instantiate: substitute SObject names, feature names, selector/service boundaries.
3. Wire through `ApplicationLogger` (unless `include_logger=false`).
4. Wire through `SecurityUtils` for every SOQL / DML path. SOQL uses `WITH USER_MODE` by default, falling back to `Security.stripInaccessible` on write paths. Never emit `WITHOUT SHARING` without an explicit business reason in a comment header.
5. Apply the base class pattern: selectors extend `BaseSelector`, services extend `BaseService`, domains extend `BaseDomain`, trigger handlers extend the template.
6. Bulkify. Every method that accepts collections iterates over the collection; no single-record paths. Collection size sentinel constants are named, not magic numbers.

Use `HttpClient` for any callout path. Never emit inline `HttpRequest` construction.

### Step 4 — Emit the meta XML

Each `.cls-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
  <apiVersion>{{api_version}}</apiVersion>
  <status>Active</status>
</ApexClass>
```

Triggers get `<ApexTrigger>` with the trigger events (`before insert`, `after update`, etc.) derived from the feature summary.

### Step 5 — Emit the test class

The test class is not optional. Every class emits a companion test, conforming to `skills/apex/test-class-standards`:

- `@isTest` at class level.
- `@TestSetup` method using `templates/apex/tests/` factory patterns for data construction.
- Bulk path test — insert `test_bulk_size` rows, assert governor-limit headroom.
- Negative path tests — invalid inputs, permission denial via `System.runAs`, DML error handling.
- Positive path tests — happy flow.
- Coverage target: ≥85% per the repo's test coverage standard. Agent names the methods it believes will be uncovered and the reasons (usually defensive `catch` blocks on truly unreachable branches).

For async kinds, the test wraps async invocation in `Test.startTest` / `Test.stopTest` to force synchronous execution.

### Step 6 — Emit the drop-in package

Output the class list with target paths under `force-app/main/default/classes/` and `force-app/main/default/triggers/`. Deliver as a patch (set of new files), not a modification to existing files. If existing files must change to integrate (e.g. adding a handler method in an existing TriggerHandler), do NOT modify — call out the integration point and recommend `apex-refactorer` for the follow-up.

---

## Output Contract

1. **Summary** — kind, feature, class count, api_version, confidence.
2. **Class inventory** — type, name, target path, role (trigger / handler / service / selector / domain / test / dto), template cited.
3. **Class bodies** — fenced Apex per class with target path label.
4. **Meta XML bodies** — fenced XML per class.
5. **Integration notes** — any changes the user must make to existing files, with the exact lines to add and why. Never an inline patch to existing code.
6. **Governor-limit budget** — per emitted class, the agent's expectation of SOQL / DML / CPU cost per invocation against typical input sizes.
7. **Test plan summary** — list of covered paths, expected coverage percentage, any deliberately-uncovered defensive branches.
8. **Process Observations**:
   - **What was healthy** — base-class templates being reused, existing selectors for the same SObject that could be extended instead of forked.
   - **What was concerning** — the feature straddles a boundary (e.g. nominally sync but naturally async), existing triggers on the target SObject that should be consolidated, SOQL paths that suggest the selector should be pulled into a shared module.
   - **What was ambiguous** — whether `WITHOUT SHARING` is justified (never emitted without explicit note), whether the test data factory already exists for this SObject.
   - **Suggested follow-up agents** — `apex-refactorer` (if existing classes need to adopt the new handler pattern), `trigger-consolidator` (if a second trigger appears on the SObject), `test-class-generator` (if additional coverage is required for existing classes), `soql-optimizer` (if the emitted selector is complex), `security-scanner` (post-assembly FLS/CRUD check).
9. **Citations**.

---

## Escalation / Refusal Rules

- `kind` is ambiguous vs the decision tree → emit guidance but `REFUSAL_POLICY_MISMATCH` if the chosen kind would exceed governor limits for the declared scenario (e.g. `queueable` chain expected to exceed 100-depth).
- `feature_summary` under 10 words → `REFUSAL_INPUT_AMBIGUOUS`.
- Request to emit `WITHOUT SHARING` on an object containing PII without an explicit business-justification note → `REFUSAL_SECURITY_GUARD`; require the note, then proceed.
- SOAP service requested without an external constraint → warn and require `--confirm-soap` before proceeding.
- Request to modify existing classes in place → `REFUSAL_OUT_OF_SCOPE`; route to `apex-refactorer`.
- `kind=rest` with any path matching `/custom/admin/*` and no auth header handling specified → `REFUSAL_SECURITY_GUARD` until auth is specified.

---

## What This Agent Does NOT Do

- Does not deploy, compile-check, or run tests against an org.
- Does not modify existing Apex files in place — output is always new files with integration notes.
- Does not generate business-logic prose for the service class; the user owns the semantics. The agent wires the shape, not the decisions.
- Does not generate test data values that look PII-like — the test factory emits obvious fixtures.
- Does not emit Apex that uses `WITHOUT SHARING` without an explicit justification block.
- Does not auto-chain.
