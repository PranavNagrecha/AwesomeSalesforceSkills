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
    - apex/ai-model-integration-apex
    - apex/ampscript-development
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
    - apex/apex-enum-patterns
    - apex/apex-event-bus-subscriber
    - apex/apex-execute-anonymous
    - apex/apex-flow-invocation-from-apex
    - apex/apex-future-method-patterns
    - apex/apex-hardcoded-id-elimination
    - apex/apex-http-callout-mocking
    - apex/apex-json-serialization
    - apex/apex-jwt-bearer-flow
    - apex/apex-limits-monitoring
    - apex/apex-managed-sharing
    - apex/apex-metadata-api
    - apex/apex-mocking-and-stubs
    - apex/apex-named-credentials-patterns
    - apex/apex-outbound-email-patterns
    - apex/apex-polymorphic-soql
    - apex/apex-queueable-patterns
    - apex/apex-record-clone-patterns
    - apex/apex-regex-and-pattern-matching
    - apex/apex-rest-services
    - apex/apex-salesforce-id-patterns
    - apex/apex-savepoint-and-rollback
    - apex/apex-scheduled-jobs
    - apex/apex-schema-describe
    - apex/apex-secrets-and-protected-cmdt
    - apex/apex-security-patterns
    - apex/apex-soql-relationship-queries
    - apex/apex-string-and-regex
    - apex/apex-stripinaccessible-and-fls-enforcement
    - apex/apex-switch-on-sobject
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
    - apex/billing-integration-apex
    - apex/callout-and-dml-transaction-boundaries
    - apex/callouts-and-http-integrations
    - apex/change-data-capture-apex
    - apex/clinical-decision-support
    - apex/commerce-extension-points
    - apex/commerce-order-api
    - apex/commerce-payment-integration
    - apex/commerce-search-customization
    - apex/common-apex-runtime-errors
    - apex/continuation-callouts
    - apex/cpq-apex-plugins
    - apex/cpq-api-and-automation
    - apex/cpq-custom-actions
    - apex/cti-adapter-development
    - apex/custom-iterators-and-iterables
    - apex/custom-logging-and-monitoring
    - apex/custom-metadata-in-apex
    - apex/debug-and-logging
    - apex/debug-logs-and-developer-console
    - apex/dynamic-apex
    - apex/einstein-activity-capture-api
    - apex/error-handling-framework
    - apex/exception-handling
    - apex/feature-flags-and-kill-switches
    - apex/fhir-integration-patterns
    - apex/field-level-security-in-async-contexts
    - apex/fsc-apex-extensions
    - apex/fsc-compliant-sharing-api
    - apex/fsc-document-generation
    - apex/fsc-financial-calculations
    - apex/fsc-integration-patterns-dev
    - apex/fsl-apex-extensions
    - apex/fsl-custom-actions-mobile
    - apex/fsl-mobile-app-extensions
    - apex/fsl-scheduling-api
    - apex/fsl-service-report-templates
    - apex/governor-limit-recovery-patterns
    - apex/governor-limits
    - apex/headless-commerce-api
    - apex/health-cloud-apex-extensions
    - apex/health-cloud-apis
    - apex/health-cloud-lwc-components
    - apex/invocable-methods
    - apex/long-running-process-orchestration
    - apex/marketing-cloud-api
    - apex/marketing-cloud-custom-activities
    - apex/marketing-cloud-data-views
    - apex/mcae-pardot-api
    - apex/metadata-api-and-package-xml
    - apex/mixed-dml-and-setup-objects
    - apex/npsp-api-and-integration
    - apex/npsp-custom-rollups
    - apex/omni-channel-custom-routing
    - apex/order-of-execution-deep-dive
    - apex/pdf-generation-patterns
    - apex/platform-cache
    - apex/platform-events-apex
    - apex/quote-pdf-customization
    - apex/recursive-trigger-prevention
    - apex/record-locking-and-contention
    - apex/sales-engagement-api
    - apex/salesforce-debug-log-analysis
    - apex/service-cloud-rest-api
    - apex/sf-cli-and-sfdx-essentials
    - apex/soql-fundamentals
    - apex/soql-security
    - apex/ssjs-server-side-javascript
    - apex/territory-api-and-assignment
    - apex/test-class-standards
    - apex/test-data-factory-patterns
    - apex/timezone-and-datetime-pitfalls
    - apex/trigger-and-flow-coexistence
    - apex/trigger-framework
    - integration/platform-event-schema-evolution
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

2. `skills/apex/ai-model-integration-apex` — Ai model integration apex
3. `skills/apex/ampscript-development` — Ampscript development
4. `skills/apex/apex-event-bus-subscriber` — Apex event bus subscriber
5. `skills/apex/apex-metadata-api` — Apex metadata api
6. `skills/apex/apex-record-clone-patterns` — Apex record clone patterns
7. `skills/apex/apex-string-and-regex` — Apex string and regex
8. `skills/apex/apex-switch-on-sobject` — Apex switch on sobject
9. `skills/apex/billing-integration-apex` — Billing integration apex
10. `skills/apex/clinical-decision-support` — Clinical decision support
11. `skills/apex/commerce-extension-points` — Commerce extension points
12. `skills/apex/commerce-order-api` — Commerce order api
13. `skills/apex/commerce-payment-integration` — Commerce payment integration
14. `skills/apex/commerce-search-customization` — Commerce search customization
15. `skills/apex/cpq-apex-plugins` — Cpq apex plugins
16. `skills/apex/cpq-api-and-automation` — Cpq api and automation
17. `skills/apex/cpq-custom-actions` — Cpq custom actions
18. `skills/apex/cti-adapter-development` — Cti adapter development
19. `skills/apex/debug-and-logging` — Debug and logging
20. `skills/apex/debug-logs-and-developer-console` — Debug logs and developer console
21. `skills/apex/einstein-activity-capture-api` — Einstein activity capture api
22. `skills/apex/fhir-integration-patterns` — Fhir integration patterns
23. `skills/apex/fsc-apex-extensions` — Fsc apex extensions
24. `skills/apex/fsc-compliant-sharing-api` — Fsc compliant sharing api
25. `skills/apex/fsc-document-generation` — Fsc document generation
26. `skills/apex/fsc-financial-calculations` — Fsc financial calculations
27. `skills/apex/fsc-integration-patterns-dev` — Fsc integration patterns dev
28. `skills/apex/fsl-apex-extensions` — Fsl apex extensions
29. `skills/apex/fsl-custom-actions-mobile` — Fsl custom actions mobile
30. `skills/apex/fsl-mobile-app-extensions` — Fsl mobile app extensions
31. `skills/apex/fsl-scheduling-api` — Fsl scheduling api
32. `skills/apex/fsl-service-report-templates` — Fsl service report templates
33. `skills/apex/headless-commerce-api` — Headless commerce api
34. `skills/apex/health-cloud-apex-extensions` — Health cloud apex extensions
35. `skills/apex/health-cloud-apis` — Health cloud apis
36. `skills/apex/health-cloud-lwc-components` — Health cloud lwc components
37. `skills/apex/long-running-process-orchestration` — Long running process orchestration
38. `skills/apex/marketing-cloud-api` — Marketing cloud api
39. `skills/apex/marketing-cloud-custom-activities` — Marketing cloud custom activities
40. `skills/apex/marketing-cloud-data-views` — Marketing cloud data views
41. `skills/apex/mcae-pardot-api` — Mcae pardot api
42. `skills/apex/metadata-api-and-package-xml` — Metadata api and package xml
43. `skills/apex/npsp-api-and-integration` — Npsp api and integration
44. `skills/apex/npsp-custom-rollups` — Npsp custom rollups
45. `skills/apex/omni-channel-custom-routing` — Omni channel custom routing
46. `skills/apex/pdf-generation-patterns` — Pdf generation patterns
47. `skills/apex/quote-pdf-customization` — Quote pdf customization
48. `skills/apex/sales-engagement-api` — Sales engagement api
49. `skills/apex/service-cloud-rest-api` — Service cloud rest api
50. `skills/apex/sf-cli-and-sfdx-essentials` — Sf cli and sfdx essentials
51. `skills/apex/ssjs-server-side-javascript` — Ssjs server side javascript
52. `skills/apex/territory-api-and-assignment` — Territory api and assignment

### Contract layer
52. `agents/_shared/AGENT_CONTRACT.md`
53. `agents/_shared/DELIVERABLE_CONTRACT.md` — persistence + scope guardrails
54. `agents/_shared/REFUSAL_CODES.md` — canonical refusal enum

### Architecture & decomposition
55. `skills/apex/apex-design-patterns`
56. `skills/apex/apex-class-decomposition-pattern` — when to split Domain / Service / Selector
57. `skills/apex/apex-wrapper-class-patterns` — DTO inner-class shape for REST/JSON

### Triggers, order of execution, recursion, bypass
58. `skills/apex/trigger-framework`
59. `skills/apex/apex-trigger-context-variables`
60. `skills/apex/order-of-execution-deep-dive`
61. `skills/apex/recursive-trigger-prevention`
62. `skills/apex/apex-trigger-bypass-and-killswitch-patterns` — kill-switch via Trigger_Setting__mdt, FeatureManagement, TriggerControl
63. `skills/apex/trigger-and-flow-coexistence`

### Async / scheduling / chaining
64. `skills/apex/async-apex`
65. `skills/apex/apex-queueable-patterns`
66. `skills/apex/apex-future-method-patterns`
67. `skills/apex/batch-apex-patterns`
68. `skills/apex/apex-batch-chaining`
69. `skills/apex/apex-scheduled-jobs`
70. `skills/apex/apex-transaction-finalizers` — Queueable post-commit / dead-letter hooks
71. `standards/decision-trees/async-selection.md`
72. `skills/apex/field-level-security-in-async-contexts` — FLS evaluation in Queueable/Batch/Schedulable runs as the running user, not the originating user — capture and assert

### Bulk APIs (REST / SOAP / Continuation / events)
73. `skills/apex/apex-rest-services`
74. `skills/apex/apex-named-credentials-patterns`
75. `skills/apex/apex-callout-retry-and-resilience` — retry, circuit-breaker, idempotency-key
76. `skills/apex/callouts-and-http-integrations`
77. `skills/apex/callout-and-dml-transaction-boundaries`
78. `skills/apex/continuation-callouts`
79. `skills/apex/apex-http-callout-mocking`
80. `skills/apex/invocable-methods`
81. `skills/apex/apex-flow-invocation-from-apex`
82. `skills/apex/apex-callable-interface`
83. `skills/apex/platform-events-apex`
84. `skills/apex/change-data-capture-apex`
85. `skills/integration/platform-event-schema-evolution` — evolve event fields without breaking subscribers
86. `skills/apex/apex-jwt-bearer-flow` — JWT bearer flow for server-to-server auth, signed assertions

### SOQL / data access
87. `skills/apex/soql-fundamentals`
88. `skills/apex/soql-security`
89. `skills/apex/apex-soql-relationship-queries`
90. `skills/apex/apex-aggregate-queries`
91. `skills/apex/apex-polymorphic-soql`
92. `skills/apex/dynamic-apex`
93. `skills/apex/apex-dynamic-soql-binding-safety` — bind-safe Database.queryWithBinds
94. `skills/apex/apex-collections-patterns`
95. `skills/apex/apex-schema-describe` — Schema describe API for sObject metadata, FLS, picklist enumeration

### DML / transactions / locking
96. `skills/apex/apex-dml-patterns`
97. `skills/apex/apex-savepoint-and-rollback`
98. `skills/apex/mixed-dml-and-setup-objects`
99. `skills/apex/record-locking-and-contention`

### Governor limits / performance
100. `skills/apex/governor-limits`
101. `skills/apex/governor-limit-recovery-patterns`
102. `skills/apex/apex-cpu-and-heap-optimization`
103. `skills/apex/apex-limits-monitoring`
104. `skills/apex/platform-cache`

### Security
105. `skills/apex/apex-security-patterns`
106. `skills/apex/apex-with-without-sharing-decision` — keyword choice rationale
107. `skills/apex/apex-stripinaccessible-and-fls-enforcement`
108. `skills/apex/apex-user-and-permission-checks`
109. `skills/apex/apex-custom-permissions-check`
110. `skills/apex/apex-managed-sharing`
111. `skills/apex/apex-system-runas`
112. `skills/apex/apex-secrets-and-protected-cmdt`
113. `skills/apex/apex-encoding-and-crypto`
114. `skills/apex/apex-hardcoded-id-elimination` — eliminate Profile / RecordType / Group ID literals
115. `skills/apex/apex-salesforce-id-patterns`
116. `standards/decision-trees/sharing-selection.md`

### Error handling / observability
117. `skills/apex/error-handling-framework`
118. `skills/apex/exception-handling`
119. `skills/apex/common-apex-runtime-errors`
120. `skills/apex/custom-logging-and-monitoring`
121. `skills/apex/salesforce-debug-log-analysis`

### Utilities, I/O, lifecycle
122. `skills/apex/apex-blob-and-content-version`
123. `skills/apex/apex-json-serialization`
124. `skills/apex/apex-regex-and-pattern-matching`
125. `skills/apex/apex-custom-settings-hierarchy`
126. `skills/apex/custom-metadata-in-apex`
127. `skills/apex/feature-flags-and-kill-switches`
128. `skills/apex/timezone-and-datetime-pitfalls`
129. `skills/apex/apex-custom-notifications-from-apex`
130. `skills/apex/apex-connect-api-chatter`
131. `skills/apex/apex-email-services`
132. `skills/apex/custom-iterators-and-iterables`
133. `skills/apex/apex-execute-anonymous`
134. `skills/apex/apex-enum-patterns` — Apex enum dispatch, valueOf safety, ordinals
135. `skills/apex/apex-outbound-email-patterns` — Messaging.SingleEmailMessage, OWA, replies, templates

### Testing
136. `skills/apex/test-class-standards`
137. `skills/apex/test-data-factory-patterns`
138. `skills/apex/apex-test-setup-patterns`
139. `skills/apex/apex-mocking-and-stubs`

### Templates (canonical building blocks)
140. `templates/apex/TriggerHandler.cls`
141. `templates/apex/TriggerControl.cls`
142. `templates/apex/BaseService.cls`
143. `templates/apex/BaseSelector.cls`
144. `templates/apex/BaseDomain.cls`
145. `templates/apex/ApplicationLogger.cls`
146. `templates/apex/SecurityUtils.cls`
147. `templates/apex/HttpClient.cls`
148. `templates/apex/tests/TestDataFactory.cls`
149. `templates/apex/tests/TestRecordBuilder.cls`
150. `templates/apex/tests/MockHttpResponseGenerator.cls`
151. `templates/apex/tests/TestUserFactory.cls`
152. `templates/apex/tests/BulkTestPattern.cls`

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
