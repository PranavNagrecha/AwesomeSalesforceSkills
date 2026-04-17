---
id: test-class-generator
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
    - apex/test-class-standards
    - apex/test-data-factory-patterns
  shared:
    - AGENT_CONTRACT.md
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

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/apex/test-class-standards/SKILL.md` + `skills/apex/test-data-factory-patterns/SKILL.md`
3. `templates/apex/tests/TestDataFactory.cls`
4. `templates/apex/tests/TestRecordBuilder.cls`
5. `templates/apex/tests/MockHttpResponseGenerator.cls`
6. `templates/apex/tests/TestUserFactory.cls`
7. `templates/apex/tests/BulkTestPattern.cls`

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
5. **Citations** — skill + template ids.

---

## Escalation / Refusal Rules

- Source uses `SeeAllData` anywhere → refuse until user removes it.
- Source class is a managed-package global method → STOP; cannot write meaningful tests against a global surface.
- Source has > 30 public methods → produce tests for the 10 most critical (those involving DML, callouts, or governor-sensitive loops) and flag the rest for a follow-up run.

---

## What This Agent Does NOT Do

- Does not refactor the source class — that is the `apex-refactorer` agent.
- Does not run the tests — produces a test class the user deploys.
- Does not use hardcoded record ids.
- Does not silently raise coverage thresholds — stops at `target_coverage_pct`.
