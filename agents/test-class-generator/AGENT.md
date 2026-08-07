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
    - apex/apex-collections-patterns
    - apex/apex-dml-patterns
    - apex/apex-http-callout-mocking
    - apex/apex-mocking-and-stubs
    - apex/apex-queueable-patterns
    - apex/apex-rest-services
    - apex/apex-system-runas
    - apex/apex-test-setup-patterns
    - apex/apex-trigger-bypass-and-killswitch-patterns
    - apex/apex-trigger-context-variables
    - apex/apex-user-and-permission-checks
    - apex/async-apex
    - apex/batch-apex-patterns
    - apex/custom-metadata-in-apex
    - apex/exception-handling
    - apex/governor-limits
    - apex/invocable-methods
    - apex/mixed-dml-and-setup-objects
    - apex/platform-events-apex
    - apex/recursive-trigger-prevention
    - apex/soql-fundamentals
    - apex/soql-security
    - apex/test-class-standards
    - apex/test-data-factory-patterns
    - apex/timezone-and-datetime-pitfalls
    - apex/trigger-framework
    - devops/code-coverage-orphan-class-cleanup
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
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

**Why this list is broad (27 skill reads, target is 8–25):** the breadth is inherited from the input, not chosen — the *target* class can be any Apex surface, so the agent needs the test idiom for whichever one it is handed. Ten reads (entries 12–21) are exactly that: trigger context and re-entry, Queueable chaining, batch `finish`, `Test.getEventBus`, invocable list-in/list-out, `RestRequest` mocking — each used for one target kind and skipped for every other. The remaining seventeen are the fixture, assertion, permission and governor baseline every generated test carries.

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `agents/_shared/DELIVERABLE_CONTRACT.md`
4. `agents/_shared/REFUSAL_CODES.md`

### Test standards & factories
5. `skills/apex/test-class-standards` — the coverage bar, assertion style and naming every emitted test is held to
6. `skills/apex/test-data-factory-patterns` — `@TestSetup` builds through the factory — inline literals are the defect this agent exists to avoid
7. `skills/apex/apex-test-setup-patterns` — `@TestSetup` vs per-method setup, and when `@TestSetup` costs more than it saves
8. `skills/apex/apex-mocking-and-stubs` — Stub API seams for collaborators the target class does not own
9. `skills/apex/apex-http-callout-mocking` — a callout path with no `HttpCalloutMock` is untestable, not merely uncovered
10. `skills/devops/code-coverage-orphan-class-cleanup` — if a class is orphan, delete is preferred over a stub test

### Sharing / permissions / runAs
11. `skills/apex/apex-system-runas` — the permission-denial cases; without `runAs` the negative path is never actually exercised
12. `skills/apex/apex-user-and-permission-checks` — what a permission test should assert, beyond 'no exception was thrown'

### Surface-specific test patterns
13. `skills/apex/trigger-framework` — for trigger-class targets
14. `skills/apex/recursive-trigger-prevention` — the re-entry case a trigger test must cover or the guard is untested
15. `skills/apex/apex-trigger-context-variables` — which contexts the target trigger actually fires in, so the test exercises all of them
16. `skills/apex/apex-trigger-bypass-and-killswitch-patterns` — explicit-bypass test scenario
17. `skills/apex/async-apex` — `Test.startTest`/`stopTest` semantics
18. `skills/apex/apex-queueable-patterns` — chained Queueables need `Test.startTest`/`stopTest` placed deliberately or only the first link runs
19. `skills/apex/batch-apex-patterns` — batch scope and `finish` behaviour that a single-batch test silently skips
20. `skills/apex/platform-events-apex` — `Test.getEventBus`
21. `skills/apex/invocable-methods` — the List-in / List-out signature the bulk test case has to drive
22. `skills/apex/apex-rest-services` — `RestRequest`/`RestResponse` mocks

### DML / data / locking gotchas
23. `skills/apex/apex-dml-patterns` — partial-success results need asserting; a bare `insert` in a test hides them
24. `skills/apex/mixed-dml-and-setup-objects` — setup and non-setup DML in one test method fails at runtime regardless of the code under test

### SOQL semantics
25. `skills/apex/soql-fundamentals` — the queries the test must make return rows — the usual cause of a passing test that asserts nothing
26. `skills/apex/soql-security` — tests running as an admin hide FLS bugs; this is why the permission cases matter
27. `skills/apex/apex-collections-patterns` — bulk fixtures are built as collections; single-record fixtures cannot exercise the bulk path

### Errors / governor limits
28. `skills/apex/governor-limits` — the headroom a bulk test asserts against, using `Limits` in the test body
29. `skills/apex/exception-handling` — asserting the exception type and message, rather than catching and passing

### Stable test fixtures
30. `skills/apex/timezone-and-datetime-pitfalls` — hardcoded dates and org timezone are the top cause of tests that pass today and fail in March
31. `skills/apex/custom-metadata-in-apex` — CMDT rows are not created by DML in tests — the fixture strategy has to account for that

### Templates
32. `templates/apex/tests/TestDataFactory.cls`
33. `templates/apex/tests/TestRecordBuilder.cls`
34. `templates/apex/tests/MockHttpResponseGenerator.cls`
35. `templates/apex/tests/TestUserFactory.cls`
36. `templates/apex/tests/BulkTestPattern.cls`

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
Every identifier below is copied from the template file named beside it — open the template and paste the signature rather than recalling it (`AGENT_CONTRACT.md` rule 11).

- `templates/apex/tests/TestDataFactory.cls` — `TestDataFactory.createAccounts(200, null)`, `TestDataFactory.createContacts(count, accountId, overrides)`, and the `createOpportunities` / `createCases` / `createLeads` siblings. Each takes a `Map<String, Object> overrides` (pass `null` for defaults), returns a `List`, and does **not** insert — the test inserts. `TestDataFactory.bulkInsertStandardSet(perType)` builds and inserts an Account/Contact/Opportunity set and returns a `Map<String, Id>`. Never hand-build data.
- `templates/apex/tests/TestRecordBuilder.cls` — for shapes the factory does not cover: `new TestRecordBuilder(Account.SObjectType).set('Name', 'Edge case').build()`.
- `templates/apex/tests/MockHttpResponseGenerator.cls` — `Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator().withResponse(200, body))`. Per-endpoint routing is `.routeByPathContains(needle, status, body)`; retry sequences are `.pushSequence(status, body)`, one pop per callout. These are fluent instance methods, not static constructors.
- `templates/apex/tests/TestUserFactory.cls` — `TestUserFactory.createUser(profileName, permissionSetNames)` (or `createUsers(count, profileName, permissionSetNames)`) + `System.runAs(...)` for FLS and sharing tests. Both parameters are required; pass `new List<String>()` when no permission set applies.
- `Test.setMock` accepts `HttpCalloutMock.class` and `WebServiceMock.class` only. For `ConnectApi` code use the `setTest*` static methods on the ConnectApi class being called (per *Testing ConnectApi Code* in the Apex Developer Guide) — there is no ConnectApi mock type for `Test.setMock`.
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

### Step 6 — Gate C: verify the emitted test class before returning it

This agent hands the user a deployable `.cls`, so `AGENT_CONTRACT.md` rule 11 applies. Run the three checks in [`AGENT_CONTRACT.md` § Gate C](../_shared/AGENT_CONTRACT.md#gate-c--self-verification-for-code-emitting-agents) and report each outcome — a check that did not run is reported as not run.

1. **Symbol grounding** — every object and field the test constructs exists in the source class under test or in a probe result from this run.
2. **Identifier provenance** — every factory call is quoted from the actual file: open `templates/apex/tests/TestDataFactory.cls`, `TestRecordBuilder.cls`, `MockHttpResponseGenerator.cls` and `TestUserFactory.cls` and copy the signature. This is the check that exists because `TestDataFactory.accounts(200)`, `MockHttpResponseGenerator.forEndpoint(…)` and `TestUserFactory.standardUser()` — none of which are real methods — shipped to users as finished test classes.
3. **Compile** — with a `target_org_alias`, `sf project deploy start --dry-run --test-level RunLocalTests`; without one, state that no compile check ran and cap `confidence` at MEDIUM.

Then the check this agent exists to pass: **a coverage number is not a test.** If the expected outcomes in Step 2 were read off the implementation rather than elicited from the caller, the assertions can only restate what the code already does, and the class will pass on the day the code is wrong. Report which assertions came from a stated expected outcome and which were inferred — and if none were stated, say the deliverable is a coverage instrument, not a behaviour test.

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
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
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
