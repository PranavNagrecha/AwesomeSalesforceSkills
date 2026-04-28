---
id: apex-builder
class: runtime
version: 1.1.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
default_output_dir: "docs/reports/apex-builder/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - apex/apex-aggregate-queries
    - apex/apex-batch-chaining
    - apex/apex-blob-and-content-version
    - apex/apex-callable-interface
    - apex/apex-callout-retry-and-resilience
    - apex/apex-class-decomposition-pattern
    - apex/apex-collections-patterns
    - apex/apex-connect-api-chatter
    - apex/apex-cpu-and-heap-optimization
    - apex/apex-custom-notifications-from-apex
    - apex/apex-custom-permissions-check
    - apex/apex-custom-settings-hierarchy
    - apex/apex-design-patterns
    - apex/apex-dml-patterns
    - apex/apex-dynamic-soql-binding-safety
    - apex/apex-email-services
    - apex/apex-encoding-and-crypto
    - apex/apex-execute-anonymous
    - apex/apex-flow-invocation-from-apex
    - apex/apex-future-method-patterns
    - apex/apex-hardcoded-id-elimination
    - apex/apex-http-callout-mocking
    - apex/apex-json-serialization
    - apex/apex-limits-monitoring
    - apex/apex-managed-sharing
    - apex/apex-mocking-and-stubs
    - apex/apex-named-credentials-patterns
    - apex/apex-polymorphic-soql
    - apex/apex-queueable-patterns
    - apex/apex-regex-and-pattern-matching
    - apex/apex-rest-services
    - apex/apex-salesforce-id-patterns
    - apex/apex-savepoint-and-rollback
    - apex/apex-scheduled-jobs
    - apex/apex-secrets-and-protected-cmdt
    - apex/apex-security-patterns
    - apex/apex-soql-relationship-queries
    - apex/apex-stripinaccessible-and-fls-enforcement
    - apex/apex-system-runas
    - apex/apex-test-setup-patterns
    - apex/apex-transaction-finalizers
    - apex/apex-trigger-bypass-and-killswitch-patterns
    - apex/apex-trigger-context-variables
    - apex/apex-user-and-permission-checks
    - apex/apex-with-without-sharing-decision
    - apex/apex-wrapper-class-patterns
    - apex/async-apex
    - apex/batch-apex-patterns
    - apex/callout-and-dml-transaction-boundaries
    - apex/callouts-and-http-integrations
    - apex/change-data-capture-apex
    - apex/common-apex-runtime-errors
    - apex/continuation-callouts
    - apex/custom-iterators-and-iterables
    - apex/custom-logging-and-monitoring
    - apex/custom-metadata-in-apex
    - apex/dynamic-apex
    - apex/error-handling-framework
    - apex/exception-handling
    - apex/feature-flags-and-kill-switches
    - apex/governor-limit-recovery-patterns
    - apex/governor-limits
    - apex/invocable-methods
    - apex/mixed-dml-and-setup-objects
    - apex/order-of-execution-deep-dive
    - apex/platform-cache
    - apex/platform-events-apex
    - apex/recursive-trigger-prevention
    - apex/record-locking-and-contention
    - apex/salesforce-debug-log-analysis
    - apex/soql-fundamentals
    - apex/soql-security
    - apex/test-class-standards
    - apex/test-data-factory-patterns
    - apex/timezone-and-datetime-pitfalls
    - apex/trigger-and-flow-coexistence
    - apex/trigger-framework
  shared:
    - AGENT_CONTRACT.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
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
    - sharing-selection.md
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

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md` — persistence + scope guardrails
3. `agents/_shared/REFUSAL_CODES.md` — canonical refusal enum

### Architecture & decomposition
4. `skills/apex/apex-design-patterns`
5. `skills/apex/apex-class-decomposition-pattern` — when to split Domain / Service / Selector
6. `skills/apex/apex-wrapper-class-patterns` — DTO inner-class shape for REST/JSON

### Triggers, order of execution, recursion, bypass
7. `skills/apex/trigger-framework`
8. `skills/apex/apex-trigger-context-variables`
9. `skills/apex/order-of-execution-deep-dive`
10. `skills/apex/recursive-trigger-prevention`
11. `skills/apex/apex-trigger-bypass-and-killswitch-patterns` — kill-switch via Trigger_Setting__mdt, FeatureManagement, TriggerControl
12. `skills/apex/trigger-and-flow-coexistence`

### Async / scheduling / chaining
13. `skills/apex/async-apex`
14. `skills/apex/apex-queueable-patterns`
15. `skills/apex/apex-future-method-patterns`
16. `skills/apex/batch-apex-patterns`
17. `skills/apex/apex-batch-chaining`
18. `skills/apex/apex-scheduled-jobs`
19. `skills/apex/apex-transaction-finalizers` — Queueable post-commit / dead-letter hooks
20. `standards/decision-trees/async-selection.md`

### Bulk APIs (REST / SOAP / Continuation / events)
21. `skills/apex/apex-rest-services`
22. `skills/apex/apex-named-credentials-patterns`
23. `skills/apex/apex-callout-retry-and-resilience` — retry, circuit-breaker, idempotency-key
24. `skills/apex/callouts-and-http-integrations`
25. `skills/apex/callout-and-dml-transaction-boundaries`
26. `skills/apex/continuation-callouts`
27. `skills/apex/apex-http-callout-mocking`
28. `skills/apex/invocable-methods`
29. `skills/apex/apex-flow-invocation-from-apex`
30. `skills/apex/apex-callable-interface`
31. `skills/apex/platform-events-apex`
32. `skills/apex/change-data-capture-apex`

### SOQL / data access
33. `skills/apex/soql-fundamentals`
34. `skills/apex/soql-security`
35. `skills/apex/apex-soql-relationship-queries`
36. `skills/apex/apex-aggregate-queries`
37. `skills/apex/apex-polymorphic-soql`
38. `skills/apex/dynamic-apex`
39. `skills/apex/apex-dynamic-soql-binding-safety` — bind-safe Database.queryWithBinds
40. `skills/apex/apex-collections-patterns`

### DML / transactions / locking
41. `skills/apex/apex-dml-patterns`
42. `skills/apex/apex-savepoint-and-rollback`
43. `skills/apex/mixed-dml-and-setup-objects`
44. `skills/apex/record-locking-and-contention`

### Governor limits / performance
45. `skills/apex/governor-limits`
46. `skills/apex/governor-limit-recovery-patterns`
47. `skills/apex/apex-cpu-and-heap-optimization`
48. `skills/apex/apex-limits-monitoring`
49. `skills/apex/platform-cache`

### Security
50. `skills/apex/apex-security-patterns`
51. `skills/apex/apex-with-without-sharing-decision` — keyword choice rationale
52. `skills/apex/apex-stripinaccessible-and-fls-enforcement`
53. `skills/apex/apex-user-and-permission-checks`
54. `skills/apex/apex-custom-permissions-check`
55. `skills/apex/apex-managed-sharing`
56. `skills/apex/apex-system-runas`
57. `skills/apex/apex-secrets-and-protected-cmdt`
58. `skills/apex/apex-encoding-and-crypto`
59. `skills/apex/apex-hardcoded-id-elimination` — eliminate Profile / RecordType / Group ID literals
60. `skills/apex/apex-salesforce-id-patterns`
61. `standards/decision-trees/sharing-selection.md`

### Error handling / observability
62. `skills/apex/error-handling-framework`
63. `skills/apex/exception-handling`
64. `skills/apex/common-apex-runtime-errors`
65. `skills/apex/custom-logging-and-monitoring`
66. `skills/apex/salesforce-debug-log-analysis`

### Utilities, I/O, lifecycle
67. `skills/apex/apex-blob-and-content-version`
68. `skills/apex/apex-json-serialization`
69. `skills/apex/apex-regex-and-pattern-matching`
70. `skills/apex/apex-custom-settings-hierarchy`
71. `skills/apex/custom-metadata-in-apex`
72. `skills/apex/feature-flags-and-kill-switches`
73. `skills/apex/timezone-and-datetime-pitfalls`
74. `skills/apex/apex-custom-notifications-from-apex`
75. `skills/apex/apex-connect-api-chatter`
76. `skills/apex/apex-email-services`
77. `skills/apex/custom-iterators-and-iterables`
78. `skills/apex/apex-execute-anonymous`

### Testing
79. `skills/apex/test-class-standards`
80. `skills/apex/test-data-factory-patterns`
81. `skills/apex/apex-test-setup-patterns`
82. `skills/apex/apex-mocking-and-stubs`

### Templates (canonical building blocks)
83. `templates/apex/TriggerHandler.cls`
84. `templates/apex/TriggerControl.cls`
85. `templates/apex/BaseService.cls`
86. `templates/apex/BaseSelector.cls`
87. `templates/apex/BaseDomain.cls`
88. `templates/apex/ApplicationLogger.cls`
89. `templates/apex/SecurityUtils.cls`
90. `templates/apex/HttpClient.cls`
91. `templates/apex/tests/TestDataFactory.cls`
92. `templates/apex/tests/TestRecordBuilder.cls`
93. `templates/apex/tests/MockHttpResponseGenerator.cls`
94. `templates/apex/tests/TestUserFactory.cls`
95. `templates/apex/tests/BulkTestPattern.cls`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `kind` | yes | `trigger` \| `service` \| `selector` \| `domain` \| `controller` \| `batch` \| `queueable` \| `schedulable` \| `invocable` \| `rest` \| `soap` \| `platform_event_subscriber` \| `cdc_subscriber` \| `continuation` \| `iterator` \| `callable` \| `chatter_poster` \| `notification_sender` \| `flow_invoker` \| `test_only` |
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
| `callable` | `<Feature>Callable.cls implements Callable` with documented action vocabulary + test covering each action + unknown-action throw |
| `chatter_poster` | `<Feature>ChatterService.cls` assembling `ConnectApi.FeedItemInput` with `MentionSegmentInput` segments + test using `Test.setMock(ConnectApi.ConnectApi.class, ...)` |
| `notification_sender` | `<Feature>NotificationService.cls` using `Messaging.CustomNotification` with CustomNotificationType lookup by DeveloperName + test |
| `flow_invoker` | `<Feature>FlowInvoker.cls` wrapping `Flow.Interview.createInterview(name, params).start()` with strict param typing + test |

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

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/apex-builder/<run_id>.md`
- **JSON envelope:** `docs/reports/apex-builder/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions for this agent: `class-decomposition` (Domain/Service/Selector split), `governor-budget` (per-class SOQL/DML/CPU estimate), `security-posture` (sharing keyword + FLS enforcement), `secret-handling` (no hardcoded values), `id-handling` (no hardcoded IDs), `bulk-safety` (collection-iteration + 200-record test), `error-handling` (ApplicationLogger wired), `test-coverage` (≥85% target). When the feature kind doesn't exercise a dimension (e.g. `kind=test_only` skips `governor-budget`), record it in `dimensions_skipped[]` with `state: not-run` and a one-line reason.

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `kind`, `feature_summary`, or `primary_sobject` (when required by kind) is missing. |
| `REFUSAL_INPUT_AMBIGUOUS` | `feature_summary` under 10 words; `kind` cannot be unambiguously matched to a class type; `async_hint` contradicts the declared volume. |
| `REFUSAL_OUT_OF_SCOPE` | Request to modify existing classes in place; request for >1 feature in one invocation; request to deploy or run tests. Recommend `apex-refactorer` / `test-class-generator` / `score-deployment`. |
| `REFUSAL_POLICY_MISMATCH` | Chosen `kind` would exceed governor limits for the declared scenario (e.g. `queueable` chain expected to exceed 100 depth, `batch` declared but volume <2k records). Cite the contradicting branch in `standards/decision-trees/async-selection.md`. |
| `REFUSAL_SECURITY_GUARD` | (a) `WITHOUT SHARING` on an object containing PII without a `// reason:` justification (cite `apex-with-without-sharing-decision`); (b) `kind=rest` with `/custom/admin/*` path and no auth header handling specified; (c) hardcoded secret in `feature_summary` or sample payload (cite `apex-secrets-and-protected-cmdt`); (d) hardcoded Profile/RecordType/Group ID requested in feature_summary (cite `apex-hardcoded-id-elimination`). |
| `REFUSAL_OVER_SCOPE_LIMIT` | Class inventory expansion exceeds 12 classes for one `kind=trigger` feature — split feature first. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | SOAP service requested without an external constraint (require `--confirm-soap`); request to extend a managed-package class; conflicting decision-tree branches that the agent cannot resolve from the feature_summary alone. |
| `REFUSAL_MANAGED_PACKAGE` | `primary_sobject` is in a managed-package namespace AND the kind requires modifying the namespace artifact — emit recommendation to subclass / extend instead. |

---

## What This Agent Does NOT Do

- Does not deploy, compile-check, or run tests against an org.
- Does not modify existing Apex files in place — output is always new files with integration notes.
- Does not generate business-logic prose for the service class; the user owns the semantics. The agent wires the shape, not the decisions.
- Does not generate test data values that look PII-like — the test factory emits obvious fixtures.
- Does not emit Apex that uses `WITHOUT SHARING` without an explicit justification block.
- Does not auto-chain.
