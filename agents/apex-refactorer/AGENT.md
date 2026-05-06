---
id: apex-refactorer
class: runtime
version: 1.1.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
default_output_dir: "docs/reports/apex-refactorer/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - apex/apex-aggregate-queries
    - apex/apex-callout-retry-and-resilience
    - apex/apex-class-decomposition-pattern
    - apex/apex-collections-patterns
    - apex/apex-cpu-and-heap-optimization
    - apex/apex-design-patterns
    - apex/apex-dml-patterns
    - apex/apex-dynamic-soql-binding-safety
    - apex/apex-enum-patterns
    - apex/apex-flow-invocation-from-apex
    - apex/apex-future-method-patterns
    - apex/apex-hardcoded-id-elimination
    - apex/apex-http-callout-mocking
    - apex/apex-limits-monitoring
    - apex/apex-mocking-and-stubs
    - apex/apex-named-credentials-patterns
    - apex/apex-polymorphic-soql
    - apex/apex-queueable-patterns
    - apex/apex-rest-services
    - apex/apex-savepoint-and-rollback
    - apex/apex-schema-describe
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
    - apex/async-apex
    - apex/batch-apex-patterns
    - apex/callout-and-dml-transaction-boundaries
    - apex/callouts-and-http-integrations
    - apex/change-data-capture-apex
    - apex/common-apex-runtime-errors
    - apex/continuation-callouts
    - apex/dynamic-apex
    - apex/error-handling-framework
    - apex/exception-handling
    - apex/fflib-enterprise-patterns
    - apex/field-level-security-in-async-contexts
    - apex/governor-limit-recovery-patterns
    - apex/governor-limits
    - apex/invocable-methods
    - apex/mixed-dml-and-setup-objects
    - apex/order-of-execution-deep-dive
    - apex/platform-events-apex
    - apex/recursive-trigger-prevention
    - apex/record-locking-and-contention
    - apex/soql-fundamentals
    - apex/soql-null-ordering-patterns
    - apex/soql-security
    - apex/test-class-standards
    - apex/test-data-factory-patterns
    - apex/trigger-and-flow-coexistence
    - apex/trigger-framework
    - apex/visualforce-fundamentals
    - devops/code-coverage-orphan-class-cleanup
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  probes:
    - apex-references-to-field.md
  templates:
    - apex/
    - apex/ApplicationLogger.cls
    - apex/BaseDomain.cls
    - apex/BaseSelector.cls
    - apex/BaseService.cls
    - apex/HttpClient.cls
    - apex/README.md
    - apex/SecurityUtils.cls
    - apex/TriggerControl.cls
    - apex/TriggerHandler.cls
    - apex/tests/BulkTestPattern.cls
    - apex/tests/MockHttpResponseGenerator.cls
    - apex/tests/TestDataFactory.cls
    - apex/tests/TestRecordBuilder.cls
    - apex/tests/TestUserFactory.cls
  decision_trees:
    - automation-selection.md
    - async-selection.md
    - sharing-selection.md
---
# Apex Refactorer Agent

## What This Agent Does

Takes an existing Apex class the user points at, compares it against the canonical patterns in `templates/apex/`, and returns a refactored version plus a test class. Targets: trigger bodies lifted into `TriggerHandler`, raw DML lifted to `BaseService`, raw SOQL lifted to `BaseSelector`, ad-hoc `HttpCallout` lifted to `HttpClient`, `System.debug` calls replaced with `ApplicationLogger`, and CRUD/FLS enforcement inserted via `SecurityUtils`. The agent produces a review-ready diff and a deploy-safe test class — it never writes to the target org.

**Scope:** One Apex class per invocation. Output is a patch the user applies in their editor or PR; nothing is auto-committed.

---

## Invocation

- **Direct read** — "Follow `agents/apex-refactorer/AGENT.md` on `force-app/main/default/classes/AccountTrigger.cls`"
- **Slash command** — [`/refactor-apex`](../../commands/refactor-apex.md)
- **MCP** — `get_agent("apex-refactorer")` on the SfSkills MCP server

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `agents/_shared/DELIVERABLE_CONTRACT.md`
4. `agents/_shared/REFUSAL_CODES.md`

### Architecture / decomposition
5. `skills/apex/apex-design-patterns`
6. `skills/apex/apex-class-decomposition-pattern` — Domain/Service/Selector split decision
7. `skills/apex/fflib-enterprise-patterns` — recognize fflib-shaped code; do NOT auto-migrate
8. `templates/apex/README.md` — template dependency order
9. `skills/devops/code-coverage-orphan-class-cleanup` — delete orphan classes to lower coverage denominator instead of stubbing tests
10. `skills/apex/apex-enum-patterns` — Apex enum dispatch, valueOf safety, ordinals

### Triggers & order
11. `skills/apex/trigger-framework`
12. `skills/apex/apex-trigger-context-variables`
13. `skills/apex/recursive-trigger-prevention`
14. `skills/apex/apex-trigger-bypass-and-killswitch-patterns`
15. `skills/apex/order-of-execution-deep-dive`
16. `skills/apex/trigger-and-flow-coexistence`

### Async surfaces (refactor target candidates)
17. `skills/apex/async-apex`
18. `skills/apex/apex-queueable-patterns`
19. `skills/apex/apex-future-method-patterns`
20. `skills/apex/batch-apex-patterns`
21. `skills/apex/apex-transaction-finalizers`
22. `standards/decision-trees/async-selection.md`
23. `skills/apex/field-level-security-in-async-contexts` — When refactoring sync Apex into async, preserve the originating user's FLS — async hops change the running user

### Callouts (refactor to HttpClient + Named Credentials)
24. `skills/apex/callouts-and-http-integrations`
25. `skills/apex/apex-named-credentials-patterns`
26. `skills/apex/apex-callout-retry-and-resilience`
27. `skills/apex/callout-and-dml-transaction-boundaries`
28. `skills/apex/continuation-callouts`
29. `skills/apex/apex-rest-services`

### SOQL refactor targets
30. `skills/apex/soql-fundamentals`
31. `skills/apex/soql-security`
32. `skills/apex/apex-soql-relationship-queries`
33. `skills/apex/apex-aggregate-queries`
34. `skills/apex/apex-polymorphic-soql`
35. `skills/apex/dynamic-apex`
36. `skills/apex/apex-dynamic-soql-binding-safety`
37. `skills/apex/apex-collections-patterns`
38. `skills/apex/soql-null-ordering-patterns` — explicit NULLS clause + Id tiebreaker for stable order
39. `skills/apex/apex-schema-describe` — Schema describe API perf, FLS, picklist enumeration

### DML / transactions
40. `skills/apex/apex-dml-patterns`
41. `skills/apex/apex-savepoint-and-rollback`
42. `skills/apex/mixed-dml-and-setup-objects`
43. `skills/apex/record-locking-and-contention`

### Governor / performance
44. `skills/apex/governor-limits`
45. `skills/apex/governor-limit-recovery-patterns`
46. `skills/apex/apex-cpu-and-heap-optimization`
47. `skills/apex/apex-limits-monitoring`

### Security (refactor → SecurityUtils)
48. `skills/apex/apex-security-patterns`
49. `skills/apex/apex-with-without-sharing-decision`
50. `skills/apex/apex-stripinaccessible-and-fls-enforcement`
51. `skills/apex/apex-user-and-permission-checks`
52. `skills/apex/apex-system-runas`
53. `skills/apex/apex-secrets-and-protected-cmdt`
54. `skills/apex/apex-hardcoded-id-elimination`
55. `standards/decision-trees/sharing-selection.md`

### Error handling
56. `skills/apex/error-handling-framework`
57. `skills/apex/exception-handling`
58. `skills/apex/common-apex-runtime-errors`

### Test rebuild after refactor
59. `skills/apex/test-class-standards`
60. `skills/apex/test-data-factory-patterns`
61. `skills/apex/apex-test-setup-patterns`
62. `skills/apex/apex-mocking-and-stubs`
63. `skills/apex/apex-http-callout-mocking`

### Other targets
64. `skills/apex/visualforce-fundamentals` — when refactoring a VF controller
65. `skills/apex/invocable-methods`
66. `skills/apex/apex-flow-invocation-from-apex`
67. `skills/apex/platform-events-apex`
68. `skills/apex/change-data-capture-apex`

### Templates
69. `templates/apex/TriggerHandler.cls`
70. `templates/apex/TriggerControl.cls`
71. `templates/apex/BaseService.cls`
72. `templates/apex/BaseSelector.cls`
73. `templates/apex/BaseDomain.cls`
74. `templates/apex/ApplicationLogger.cls`
75. `templates/apex/SecurityUtils.cls`
76. `templates/apex/HttpClient.cls`
77. `templates/apex/tests/BulkTestPattern.cls`
78. `templates/apex/tests/TestDataFactory.cls`
79. `templates/apex/tests/MockHttpResponseGenerator.cls`
80. `templates/apex/tests/TestRecordBuilder.cls`
81. `templates/apex/tests/TestUserFactory.cls`

### Probes
82. `agents/_shared/probes/apex-references-to-field.md` — for understanding field-impact before lifting selector queries

### Decision trees
83. `standards/decision-trees/automation-selection.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `source_path` | yes | `force-app/main/default/classes/AccountTrigger.cls` |
| `related_paths` | no | helper classes / existing test class paths |
| `target_org_alias` | no | if set, the agent also calls `validate_against_org("apex/trigger-framework", target_org=...)` |

If `source_path` is missing or doesn't exist, STOP and ask the user. Never guess at the path.

---

## Plan

### Step 1 — Classify the class

Read the source file. Identify which of these shapes it is:

| Shape | Signal |
|---|---|
| Object trigger body | File is a `trigger` with inline logic |
| Handler class | References `Trigger.new` / `Trigger.old`, implements ad-hoc dispatch |
| Service class | Implements business logic, calls DML |
| Selector class | Contains SOQL queries |
| HTTP callout class | `Http`, `HttpRequest`, `HttpResponse` |
| Mixed | More than one of the above |

For "Mixed", output a refactor plan that splits the class along `BaseDomain` / `BaseService` / `BaseSelector` boundaries before applying any other pattern.

### Step 2 — Apply templates

Cross-reference each shape against `templates/apex/`:

| Shape | Target template | What to do |
|---|---|---|
| Trigger body | `templates/apex/TriggerHandler.cls` | Move all logic into a new `<Object>TriggerHandler extends TriggerHandler` class; trigger body becomes `new <Object>TriggerHandler().run();` |
| Handler with ad-hoc dispatch | `TriggerHandler` | Replace dispatch with the template's virtual methods (`beforeInsert`, `afterUpdate`, etc.); add `TriggerControl` check if missing |
| Service | `BaseService.cls` | Subclass `BaseService`; move DML through `SecurityUtils.requireCreatable/Updateable/Deletable` |
| Selector | `BaseSelector.cls` | Subclass `BaseSelector`; centralize SOQL; enforce `WITH SECURITY_ENFORCED` or `stripInaccessibleFields` per `apex-security-patterns` |
| HTTP callout | `HttpClient.cls` | Replace raw `Http.send()` with `HttpClient` calls; move endpoints to Named Credentials |
| Any | `ApplicationLogger.cls` | Replace `System.debug` with `ApplicationLogger.info/warn/error` |

### Step 3 — Insert CRUD/FLS enforcement

Per `skills/apex/apex-security-patterns`, every DML path must call `SecurityUtils` unless the class runs `with sharing` AND all fields are system-managed.

### Step 4 — Generate the test class

Invoke the `test-class-generator` agent's plan inline (do not auto-chain to a separate agent — just apply its rules):
- Use `templates/apex/tests/TestDataFactory.cls` for data
- Use `templates/apex/tests/BulkTestPattern.cls` for the 200-record test
- Use `TestUserFactory` for `System.runAs` coverage of non-admin users
- Target ≥ 85% coverage; name the test `<OriginalClass>_Test`

### Step 5 — Optional: check the org

If `target_org_alias` was provided, call:
```
validate_against_org(skill_id="apex/trigger-framework", target_org=...)
```
If an existing `*TriggerHandler` / `*Handler` already exists in the org, add a note to the output recommending the user align with that rather than introducing a second framework. Do NOT fail the refactor — just warn.

---

## Output Contract

Return one markdown document with these sections:

1. **Summary** — shape classified, templates applied, confidence (HIGH/MEDIUM/LOW).
2. **Refactored files** — one code block per generated file, using fenced code blocks labelled with the target path. Include:
   - The refactored class
   - Any new dependency classes (e.g. a new `<Object>TriggerHandler.cls` if we lifted a trigger body)
   - The test class
3. **Diff summary** — bullet list of every transformation applied, each citing the skill / template the transformation came from.
4. **Risk notes** — ambiguities, pre-existing bugs, bulkification concerns, assumptions.
5. **Process Observations** — peripheral signal noticed during the refactor, separate from the direct diff.
   - **What was healthy** — base-class / framework already partially adopted; existing test class covers > 80% before refactor; existing Selector-equivalents in the codebase that the new shape can extend; consistent naming convention.
   - **What was concerning** — sharing keyword inferred but ambiguous (cite `apex-with-without-sharing-decision`); hardcoded IDs / secrets discovered (cite the matching skill); SOQL inside loops the agent could not safely rewrite; dynamic SOQL with string concatenation requiring `apex-dynamic-soql-binding-safety` follow-up; recursion guard absent on a multi-event handler.
   - **What was ambiguous** — whether `WITHOUT SHARING` is justified; whether existing Selector should be extended or a new one introduced; whether a Service/Domain/Selector split is warranted given current size.
   - **Suggested follow-up agents** — `security-scanner` (post-refactor FLS/CRUD verification); `soql-optimizer` (when new Selector emitted); `test-class-generator` (when test-class generation deferred); `trigger-consolidator` (when refactor reveals additional triggers on the same SObject); `score-deployment` (pre-deploy gate).
6. **Citations** — ids of every skill, template, and decision-tree branch consulted.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/apex-refactorer/<run_id>.md`
- **JSON envelope:** `docs/reports/apex-refactorer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions for this agent: `class-shape` (trigger / handler / service / selector / callout / mixed), `templates-applied` (which canonical templates wired in), `crud-fls-enforcement`, `sharing-keyword`, `id-handling`, `secret-handling`, `dynamic-soql-safety`, `bulk-safety`, `transaction-boundaries`, `test-class-generation`. When the source file doesn't exercise a dimension, record it in `dimensions_skipped[]` with `state: not-run` and a one-line reason.

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `source_path` not provided. |
| `REFUSAL_INPUT_AMBIGUOUS` | `source_path` exists but file is empty / non-Apex / unreadable. |
| `REFUSAL_OVER_SCOPE_LIMIT` | File > 2000 lines — recommend pre-splitting; or refactor introduces > 6 new files in one pass. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | (a) File references missing types the agent cannot resolve from `related_paths`; (b) class implements `fflib` or another framework outside the canonical templates — do NOT auto-migrate; (c) existing test class is green and covers > 90% — refactor risks regression. |
| `REFUSAL_OUT_OF_SCOPE` | Request to refactor managed-package class, request to deploy, request to refactor more than one class per invocation. |
| `REFUSAL_MANAGED_PACKAGE` | Source class is in a managed-package namespace. Recommend extension/wrapping pattern instead. |
| `REFUSAL_SECURITY_GUARD` | Refactor would silently drop an existing `with sharing` keyword, bypass an existing `SecurityUtils` call, or expose a previously-hidden secret. |
| `REFUSAL_POLICY_MISMATCH` | Decision-tree consultation shows the class should be a Flow / Platform Event / external service — recommend the appropriate agent (cite `automation-selection.md` branch). |

---

## What This Agent Does NOT Do

- Does not deploy to an org.
- Does not modify files outside `source_path` + `related_paths`.
- Does not migrate from `fflib` to this repo's lightweight enterprise pattern without explicit user confirmation.
- Does not invent new Apex patterns — every change cites a template or a skill.
- Does not auto-chain to `security-scanner` or `soql-optimizer`; recommends them in the output instead.
