---
name: test-class-standards
description: "Use when writing, reviewing, or debugging Apex test classes, test data factories, async test behavior, negative-path assertions, or callout mocking. Triggers: 'SeeAllData', 'Test.startTest', 'HttpCalloutMock', 'test data factory', 'missing assertions'. NOT for the factory class itself — use apex/test-data-factory-patterns. NOT for the mock class itself — use apex/apex-http-callout-mocking."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - apex-testing
  - test-data-factory
  - seealldata
  - httpcalloutmock
  - async-testing
triggers:
  - "why is my Apex test using SeeAllData"
  - "how should I structure a test data factory"
  - "Test.startTest and stopTest for queueable or batch"
  - "my test has coverage but no real assertions"
  - "how do I mock HTTP callouts in Apex tests"
  - "test class best practices"
  - "Apex test best practices"
  - "writing and generating an Apex test class"
  - "migrate System.assertEquals to the Assert class"
  - "mock an Apex service class with the Stub API"
  - "every test failed at deploy with No such column on entity Case"
  - "Operation failed due to fields being inaccessible on Sobject during a validation deploy"
  - "which permission set should my test user hold"
inputs:
  - "class or trigger under test and its entry points"
  - "required data setup including users, permissions, and related records"
  - "whether the code under test performs async work or callouts"
outputs:
  - "test design recommendation"
  - "review findings for test hygiene and coverage quality"
  - "test class scaffold with factory, assertions, and mocks"
dependencies: []
version: 1.3.0
author: Pranav Nagrecha
updated: 2026-09-12
---

Use this skill when Apex tests need to prove behavior instead of merely satisfying deployment coverage. The objective is deterministic, isolated tests that verify positive paths, negative paths, bulk behavior, async execution, and callout behavior without depending on org data.

## Before Starting

- What business behavior must this test prove beyond "method executes without exception"?
- What data relationships and user context does the code require?
- Does the code under test enqueue async work, run in sharing-sensitive contexts, or make HTTP callouts?

## Questions to Ask Before Configuring

Every row below exists because a gotcha in `references/gotchas.md` bit someone who skipped it.

| Ask the requester | Why it matters | What a good answer adds | Traces to |
|---|---|---|---|
| What must be true after this runs that is not true before? | A test that only proves "no exception" passes forever while the behaviour rots. | One observable outcome per entry point, which becomes one test method name and one assertion. | Gotcha 4 |
| Which records must exist first, and is every one of them creatable inside a test transaction? | Some standard objects are not creatable, and history and feed-tracking records need committed parents that a test never commits. | A fixture plan that fails at design time instead of at run time, plus an explicit note where a stub replaces a record. | Gotcha 12 |
| Does any step read data the test did not create — record types, custom settings, queues, reports? | That is the pressure that produces `SeeAllData=true`, which then removes `@TestSetup` from the class and bars it from parallel execution. | Either a factory method for the missing data, or a written justification narrow enough to sit on one class. | Gotchas 2, 7 |
| Does the path enqueue async work or publish a platform event, and who consumes it? | Queueable, Batch and future work runs at `Test.stopTest()`; a published event does nothing until the test delivers it. | The correct boundary placement, and a `Test.getEventBus().deliver()` call per subscriber hop. | Gotchas 1, 10 |
| Does the path make an HTTP callout, and does DML have to run before it? | DML leaves uncommitted work that blocks callouts unless `Test.startTest()` is called before `Test.setMock(...)`. | The exact statement order, plus the failure status codes the mock must also return. | Gotcha 9 |
| Whose access does the behaviour depend on, and which permission set grants it? | Sharing and field-level bugs are invisible to a test that runs as the deploying admin, and every `runAs` call spends a DML statement. | A named profile plus permission set for the `runAs` user, and a bounded number of `runAs` blocks. | Gotchas 3, 11 |
| Which permission set does the running user hold in production, and does this deployment contain it? | Code that enforces user mode is read through the *running* user's FLS. At validation the running user is whoever is deploying, and a profile deployed by Metadata API carries field permissions only for objects in the same request — so fields shipped alongside the code are invisible to that profile and every test method fails before it asserts anything. | The exact permission set API name to assign inside `@TestSetup`, which turns the `runAs` user from decoration into the thing that makes the suite deployable. | Gotcha 13 |
| Does the code rely on static state or cached configuration between invocations? | Statics reinitialise for every test method, so state seeded in `@TestSetup` is gone by the time a test method reads it. | State passed through records rather than statics, and an explicit cache reset where the code under test caches. | Gotcha 8 |

A proper test design differs from "just write a test" in what it buys you later: the suite tells you *which* contract broke and *for whom*, rather than telling you that something somewhere in a 400-line class no longer compiles or no longer passes.

## Core Concepts

### `SeeAllData=false` Is The Safe Default

Salesforce testing guidance favors isolated tests that create their own data. Tests that rely on production-like org data are brittle, order-dependent, and hard to maintain. Use factories or `@testSetup` to build what the test needs. Reach for `SeeAllData=true` only in rare, justified edge cases and document why.

### Coverage Is A Side Effect, Not The Goal

A test with no meaningful assertions can still raise coverage. That does not make it valuable. A good Apex test verifies outcomes: field values, records created, exceptions thrown, side effects prevented, and access or security behavior preserved.

### Prefer The `System.Assert` Class For Assertions

The `Assert` class (added in Winter '23, API 56.0) is Salesforce's recommended assertion style. Its methods read as intent — `Assert.areEqual`, `Assert.areNotEqual`, `Assert.isNull`, `Assert.isNotNull`, `Assert.isTrue`, `Assert.isFalse`, `Assert.isInstanceOfType`, `Assert.isNotInstanceOfType`, and `Assert.fail` — and its failure output is easier to read than the legacy methods. The optional message argument must be a `String`, which is stricter than the legacy `System.assert*` methods that accepted arbitrary objects and could emit unhelpful debug output. The legacy `System.assert`, `System.assertEquals`, and `System.assertNotEquals` methods remain supported with no announced retirement, so existing tests do not need a rewrite, but new tests should default to the `Assert` class.

### Mock Non-HTTP Dependencies With The Stub API

Callout mocking (below) covers HTTP dependencies. For everything else — a service class calling a selector, a controller calling a service — Apex provides a general-purpose Stub API: implement the `StubProvider` interface and build the stub with `Test.createStub(TypeToMock.class, providerInstance)`. This isolates the class under test from collaborators without writing a hand-rolled fake subclass, so a unit test can verify one layer's logic independently of the layers it depends on.

### `Test.startTest()` And `Test.stopTest()` Have A Specific Job

These methods reset governor limits for the measured block and force async work to complete by `stopTest()`. Do not wrap half the test in `startTest()` just because it is fashionable. Use it around the action under test, especially for Queueable, Batch, Scheduled Apex, future methods, and limit-sensitive code.

### Mock External Dependencies

Callouts never belong in real tests. Use `Test.setMock(HttpCalloutMock.class, mock)` or the relevant mock interface so the test is deterministic and can assert on success and failure responses explicitly.

## Common Patterns

### `@testSetup` Plus Test Data Factory

**When to use:** Multiple test methods need a common baseline such as Accounts, Opportunities, or custom settings.

**How it works:** Keep object creation in reusable factory methods. Use `@testSetup` for shared baseline data, then modify or extend the data in each individual test method as needed.

**Why not the alternative:** Rebuilding the same graph in every test makes the suite noisy and harder to maintain.

### Arrange / Act / Assert For Positive, Negative, And Bulk Paths

**When to use:** Any service, trigger, or controller that handles business logic.

**How it works:** Create explicit inputs, invoke the code once in a focused action block, then assert on results. Include at least one negative test and one bulk or multi-record test for code that is supposed to be bulk-safe.

### Mock-Driven Callout Test

**When to use:** The code under test performs an HTTP callout.

**How it works:** Register a mock before the action, execute inside `startTest()/stopTest()` if async is involved, and assert both the data mutation and failure behavior.

### Stub API For Non-HTTP Collaborators

**When to use:** The class under test delegates to another Apex class (service, selector, or gateway) and you want to test it in isolation without touching that collaborator's real implementation.

**How it works:** Write a `StubProvider` whose `handleMethodCall` returns canned values for the intercepted methods, build the stub with `Test.createStub()`, and inject it into the class under test. Assert on how the class under test reacts to the stubbed responses.

**Why not the alternative:** Hand-written fake subclasses drift from the real interface and add maintenance overhead; the Stub API generates the double at runtime and fails loudly if the mocked type changes. Note the API's boundaries — it cannot mock static or `@future` methods, private methods, properties, triggers, inner classes, system types, classes that implement the `Batchable` interface, or classes that have only private constructors — so keep those seams behind mockable instance methods.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Many tests need the same baseline records | `@testSetup` plus factory methods | Consistent setup with less duplication |
| Code under test enqueues async work | `Test.startTest()` / `Test.stopTest()` around the action | Ensures the async job actually runs in the test |
| Service makes HTTP callouts | `Test.setMock(HttpCalloutMock.class, mock)` | Deterministic, offline, and assertion-friendly |
| Class under test delegates to a non-HTTP collaborator | `StubProvider` + `Test.createStub()` | Isolates one layer without a hand-rolled fake |
| New assertions in fresh tests | `Assert.areEqual` / `Assert.isTrue` / `Assert.fail` | Clearer failure output and a discoverable, centralized API |
| Team wants to use `SeeAllData=true` because setup feels hard | Build a factory instead | Reliability of the suite matters more than short-term convenience |


## Recommended Workflow

1. **Name the contracts before the fixture.** Work through the questions above and write one observable outcome per entry point. Each becomes a test method name; anything you cannot state as an outcome is not yet testable.
2. **Choose the fixture source.** `templates/apex/tests/TestDataFactory.cls` covers Account, Contact, Opportunity, Case and Lead through `createXxx(count, overrides)`; `templates/apex/tests/TestRecordBuilder.cls` covers everything the factory does not; `templates/apex/tests/TestUserFactory.cls` mints the `System.runAs` user with its permission sets. Put the shared baseline in `@TestSetup` — unless the class needs `SeeAllData=true`, which forbids it.
3. **Write the four mandatory methods:** a bulk-200 method modelled on `templates/apex/tests/BulkTestPattern.cls`, a negative method that names the expected exception, an access method wrapped in `System.runAs`, and — whenever the path calls out — a mock method built on `templates/apex/tests/MockHttpResponseGenerator.cls`, ordered DML, `Test.startTest()`, `Test.setMock(...)`, action, `Test.stopTest()`.
   **If the code under test enforces user mode** — `WITH USER_MODE` on a query, `as user` on a DML statement, `AccessLevel.USER_MODE` on a `Database` method, `Security.stripInaccessible`, or a legacy `WITH SECURITY_ENFORCED` clause — `System.runAs` stops being one method's concern and becomes the shape of the whole class: mint the user in `@TestSetup` with `TestUserFactory`, assign the permission set(s) the deployment ships, and put every body that touches the code under test inside `System.runAs(testUser)`. Skipping it does not weaken the suite, it breaks the deploy (Gotcha 13). Worked example: `references/examples.md` Example 5.
4. **Ship every template class the test names.** A test that references `TestDataFactory` and deploys without `TestDataFactory.cls` fails with `Variable does not exist`. Copy each template verbatim with its `-meta.xml` and record it in the deploy order.
5. **Run the checker** — `python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py --manifest-dir <class directory>`. Exit 1 means an ERROR rule fired (missing assertion, unjustified `SeeAllData=true`, unmocked callout); add `--strict` in CI to fail on WARN findings too.
6. **Deploy dry.** `sf project deploy start --manifest package.xml --dry-run --test-level RunSpecifiedTests --tests <TestClass>` compiles the package and runs the tests without persisting metadata — the last check that the provenance set is complete. UNVERIFIED (2026-09-12): the `sf` CLI flag spellings are not corpus-grounded — check `sf project deploy start --help` before using this command in a runbook.
7. **Record what you could not prove.** Any behaviour left untested because the record is not creatable, or the member is not stubbable, belongs in a comment beside the test, not in the commit message.

A full worked package — service, Queueable, test class, `-meta.xml`, `package.xml`, deploy order and checker run — is in `references/code-examples.md`.

---

## Review Checklist

- [ ] Tests create their own data or use a documented factory pattern.
- [ ] `SeeAllData=true` is absent or explicitly justified.
- [ ] Assertions verify behavior, not just "no exception thrown."
- [ ] Async code is exercised with `Test.startTest()` and `Test.stopTest()`.
- [ ] Bulk-sensitive code has multi-record tests, not only single-record happy paths.
- [ ] Callout code uses mocks and verifies error handling as well as success.
- [ ] Tests for user-mode code run inside `System.runAs` of a user holding the permission set(s) the deployment ships — not the deploying admin, and not `runAs(new User(Id = UserInfo.getUserId()))`.

## Salesforce-Specific Gotchas

1. **Async Apex does not execute inside a test until `Test.stopTest()`** — asserting before that point gives misleading failures.
2. **`SeeAllData=true` couples tests to org state** — a passing sandbox test can still fail in another org because the hidden data assumptions differ.
3. **Mixed DML still affects tests** — creating Users and setup-related data in the wrong sequence can fail test methods even when business logic is correct.
4. **One assertion at the end is not enough** — bulk, negative, and security-sensitive behaviors need focused assertions, not just a single record-count check.
5. **User-mode code makes the test suite a deployment gate** — when the running user cannot see a field that shipped in the same request, the tests fail during `--dry-run` validation rather than merely passing for the wrong reason. See `references/gotchas.md` Gotcha 13.

## Output Artifacts

| Artifact | Description |
|---|---|
| Test review findings | Findings on isolation, assertions, async behavior, and mocking quality |
| Test scaffold | A structure for factory setup, focused actions, and strong assertions |
| Coverage-quality remediation plan | Specific changes that turn brittle coverage tests into trustworthy behavioral tests |

## Related Skills

- `apex/exception-handling` — use to define how negative tests should assert exceptions or boundary-safe error messages.
- `apex/async-apex` — use when the test problem is really caused by wrong Queueable, Batch, or scheduler design.
- `apex/callouts-and-http-integrations` — use when mock design depends on outbound integration structure or Named Credential usage.
