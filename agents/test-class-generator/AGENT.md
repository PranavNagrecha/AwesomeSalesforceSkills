---
id: test-class-generator
class: runtime
version: 1.1.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
default_output_dir: "docs/reports/test-class-generator/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - apex/apex-collections-patterns
    - apex/apex-dml-patterns
    - apex/apex-flow-invocation-from-apex
    - apex/apex-future-method-patterns
    - apex/apex-http-callout-mocking
    - apex/apex-limits-monitoring
    - apex/apex-mocking-and-stubs
    - apex/apex-polymorphic-soql
    - apex/apex-queueable-patterns
    - apex/apex-rest-services
    - apex/apex-savepoint-and-rollback
    - apex/apex-scheduled-jobs
    - apex/apex-system-runas
    - apex/apex-test-setup-patterns
    - apex/apex-trigger-bypass-and-killswitch-patterns
    - apex/apex-trigger-context-variables
    - apex/apex-user-and-permission-checks
    - apex/apex-with-without-sharing-decision
    - apex/async-apex
    - apex/batch-apex-patterns
    - apex/callouts-and-http-integrations
    - apex/change-data-capture-apex
    - apex/common-apex-runtime-errors
    - apex/continuation-callouts
    - apex/cpq-test-automation
    - apex/custom-metadata-in-apex
    - apex/dynamic-apex
    - apex/error-handling-framework
    - apex/exception-handling
    - apex/feature-flags-and-kill-switches
    - apex/governor-limits
    - apex/invocable-methods
    - apex/mixed-dml-and-setup-objects
    - apex/platform-events-apex
    - apex/record-locking-and-contention
    - apex/recursive-trigger-prevention
    - apex/soql-fundamentals
    - apex/soql-security
    - apex/test-class-standards
    - apex/test-data-factory-patterns
    - apex/timezone-and-datetime-pitfalls
    - apex/trigger-framework
    - apex/visualforce-fundamentals
    - devops/code-coverage-orphan-class-cleanup
  shared:
    - AGENT_CONTRACT.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  templates:
    - apex/tests/
    - apex/tests/BulkTestPattern.cls
    - apex/tests/MockHttpResponseGenerator.cls
    - apex/tests/TestDataFactory.cls
    - apex/tests/TestRecordBuilder.cls
    - apex/tests/TestUserFactory.cls
---
# Test Class Generator Agent

## What This Agent Does

Generates a bulk-safe Apex test class for a target class, targeting ≥ 85% code coverage, using the canonical test factories in `templates/apex/tests/`. Produces positive, negative, bulk (200-record), and non-admin (`System.runAs`) scenarios by default. Stubs HTTP callouts via `MockHttpResponseGenerator` when the target makes callouts. Output is ready to paste into the user's force-app tree.

**Scope:** One target class per invocation. Generates the test class only.

---

## Invocation

- **Direct read** — "Follow `agents/test-class-generator/AGENT.md` for `force-app/main/default/classes/AccountService.cls`"
- **Slash command** — [`/gen-tests`](../../commands/gen-tests.md)
- **MCP** — `get_agent("test-class-generator")`

---

## Mandatory Reads Before Starting

2. `skills/apex/cpq-test-automation` — Cpq test automation

### Contract layer
2. `agents/_shared/AGENT_CONTRACT.md`
3. `agents/_shared/DELIVERABLE_CONTRACT.md`
4. `agents/_shared/REFUSAL_CODES.md`

### Test standards & factories
5. `skills/apex/test-class-standards`
6. `skills/apex/test-data-factory-patterns`
7. `skills/apex/apex-test-setup-patterns`
8. `skills/apex/apex-mocking-and-stubs`
9. `skills/apex/apex-http-callout-mocking`
10. `skills/devops/code-coverage-orphan-class-cleanup` — if a class is orphan, delete is preferred over a stub test

### Sharing / permissions / runAs
11. `skills/apex/apex-system-runas`
12. `skills/apex/apex-user-and-permission-checks`
13. `skills/apex/apex-with-without-sharing-decision`

### Surface-specific test patterns
14. `skills/apex/trigger-framework` — for trigger-class targets
15. `skills/apex/recursive-trigger-prevention`
16. `skills/apex/apex-trigger-context-variables`
17. `skills/apex/apex-trigger-bypass-and-killswitch-patterns` — explicit-bypass test scenario
18. `skills/apex/async-apex` — `Test.startTest`/`stopTest` semantics
19. `skills/apex/apex-queueable-patterns`
20. `skills/apex/apex-future-method-patterns`
21. `skills/apex/batch-apex-patterns`
22. `skills/apex/apex-scheduled-jobs`
23. `skills/apex/platform-events-apex` — `Test.getEventBus`
24. `skills/apex/change-data-capture-apex`
25. `skills/apex/invocable-methods`
26. `skills/apex/apex-rest-services` — `RestRequest`/`RestResponse` mocks
27. `skills/apex/continuation-callouts`
28. `skills/apex/apex-flow-invocation-from-apex`
29. `skills/apex/callouts-and-http-integrations`
30. `skills/apex/visualforce-fundamentals`

### DML / data / locking gotchas
31. `skills/apex/apex-dml-patterns`
32. `skills/apex/apex-savepoint-and-rollback`
33. `skills/apex/mixed-dml-and-setup-objects`
34. `skills/apex/record-locking-and-contention`

### SOQL semantics
35. `skills/apex/soql-fundamentals`
36. `skills/apex/soql-security`
37. `skills/apex/apex-polymorphic-soql`
38. `skills/apex/dynamic-apex`
39. `skills/apex/apex-collections-patterns`

### Errors / governor limits
40. `skills/apex/governor-limits`
41. `skills/apex/apex-limits-monitoring`
42. `skills/apex/exception-handling`
43. `skills/apex/common-apex-runtime-errors`
44. `skills/apex/error-handling-framework`

### Stable test fixtures
45. `skills/apex/timezone-and-datetime-pitfalls`
46. `skills/apex/custom-metadata-in-apex`
47. `skills/apex/feature-flags-and-kill-switches`

### Templates
48. `templates/apex/tests/TestDataFactory.cls`
49. `templates/apex/tests/TestRecordBuilder.cls`
50. `templates/apex/tests/MockHttpResponseGenerator.cls`
51. `templates/apex/tests/TestUserFactory.cls`
52. `templates/apex/tests/BulkTestPattern.cls`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `source_path` | yes | `force-app/main/default/classes/AccountService.cls` |
| `target_coverage_pct` | no (default 85) | `90` |
| `include_bulk_test` | no (default true) | `false` for utility classes |

---

## Plan

### Step 1 — Read the source and extract the surface

Parse the source class. Record:
- Public methods (signature + return types)
- Instance vs static methods
- DML statements (insert / update / delete / upsert)
- SOQL queries
- HTTP callouts (`Http.send`, `HttpClient.request`)
- `System.runAs` needs — does the class use `with sharing` / `without sharing` / `inherited sharing`?
- External dependencies (picklist values, record types, custom settings, custom metadata)

### Step 2 — Determine required scenarios

Minimum scenario matrix:

| Scenario | When to include | Template |
|---|---|---|
| Single-record happy path | always | — |
| 200-record bulk | if target has DML or SOQL (default) | `BulkTestPattern` |
| Non-admin user | if class uses `with sharing` or enforces FLS | `TestUserFactory` |
| Negative / error path | if target throws custom exceptions | — |
| HTTP callout | if target makes callouts | `MockHttpResponseGenerator` |
| Governor-limit stress | if target loops with DML/SOQL inside | `BulkTestPattern` + asserts on `Limits.*` |

### Step 3 — Draft the test class

Skeleton:
```apex
@IsTest
private class <Source>_Test {
    @TestSetup
    static void setup() {
        // Use TestDataFactory for bulk defaults
    }

    @IsTest
    static void happyPath_singleRecord() { ... }

    @IsTest
    static void bulk_200Records() { ... }

    @IsTest
    static void runAs_standardUser_enforcesSharing() { ... }

    @IsTest
    static void callout_handlesRetryableError() { ... }
}
```

Fill in each test using:
- `TestDataFactory.accounts(200)` / `.contacts(n, parentAccount)` / etc. — never hand-build data
- `Test.setMock(HttpCalloutMock.class, MockHttpResponseGenerator.forEndpoint(...))` for callouts
- `TestUserFactory.standardUser()` + `System.runAs(...)` for FLS tests
- `Test.startTest()` / `Test.stopTest()` around the DUT invocation
- Explicit `System.assertEquals` with a meaningful message

### Step 4 — Coverage estimate

List the branches/methods the generated tests cover. If any public method is uncovered, add a specific `// TODO: cover <method>(<signature>)` comment with a reason (usually: needs a specific external dependency the agent couldn't infer).

### Step 5 — Output checklist

Verify:
- No `SeeAllData=true` (refuse to add it).
- No raw `insert new Account(...)` — everything routes through the factory.
- No commented-out assertions.
- Every assertion has a failure message.
- `@TestSetup` only contains data creation, no business logic.

---

## Output Contract

1. **Summary** — target class, public method count, scenarios generated, estimated coverage %.
2. **Test class** — fenced code block labelled with the target path `force-app/main/default/classes/<Source>_Test.cls` + its `-meta.xml`.
3. **Coverage gaps** — methods not covered + why.
4. **Dependencies to deploy** — template files the test depends on (`TestDataFactory`, etc.) that the user must have already deployed.
5. **Process Observations** — peripheral signal noticed while reading the source.
   - **Healthy** — target uses `with sharing` correctly; existing `<Object>_Test` already exists as scaffold; clean separation between data construction and assertions; method signatures are simple/test-friendly.
   - **Concerning** — target invokes `Database.executeBatch(this)` from a method (recursion in test risk); target performs DML on Setup objects + non-Setup objects in same method (cite `mixed-dml-and-setup-objects`); target uses `Datetime.now()` inline (cite `timezone-and-datetime-pitfalls`); target hits `@AuraEnabled` and `WITHOUT SHARING` together — flag for security re-check.
   - **Ambiguous** — runAs persona unclear (no obvious permission-set constraints); whether bulk path triggers governor-limit assertions; whether mock callouts need a sequence of failures-then-success.
   - **Suggested follow-up agents** — `apex-refactorer` if untestable code shape (private methods used as DUT); `security-scanner` if FLS/CRUD gaps appeared; `score-deployment` pre-deploy.
6. **Citations** — skill + template ids.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/test-class-generator/<run_id>.md`
- **JSON envelope:** `docs/reports/test-class-generator/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions: `happy-path`, `bulk-200`, `runAs-non-admin`, `negative-path`, `callout-mock`, `governor-stress`, `recursion-guard`, `setup-vs-data-dml`. Record each in `dimensions_compared[]` (with the test method name) or `dimensions_skipped[]` with reason.

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `source_path` not provided. |
| `REFUSAL_INPUT_AMBIGUOUS` | Source is empty / non-Apex / unparseable. |
| `REFUSAL_SECURITY_GUARD` | Source uses `SeeAllData=true` — refuse until user removes it. |
| `REFUSAL_MANAGED_PACKAGE` | Source is a managed-package `global` method — cannot write meaningful tests against a global surface; recommend extension class instead. |
| `REFUSAL_OVER_SCOPE_LIMIT` | Source has > 30 public methods — produce tests for the 10 most critical (DML / callout / governor-sensitive loops) and flag the rest for a follow-up run. |
| `REFUSAL_OUT_OF_SCOPE` | Request to refactor source class (route to `apex-refactorer`) or to run tests against a real org (route to `score-deployment`). |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | Source instantiates `Test.setMock` for a type the agent cannot resolve; mocking strategy ambiguous. |

---

## What This Agent Does NOT Do

- Does not refactor the source class — that is the `apex-refactorer` agent.
- Does not run the tests — produces a test class the user deploys.
- Does not use hardcoded record ids.
- Does not silently raise coverage thresholds — stops at `target_coverage_pct`.
