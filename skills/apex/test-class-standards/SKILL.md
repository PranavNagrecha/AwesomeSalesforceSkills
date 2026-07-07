---
name: test-class-standards
description: "Use when writing, reviewing, or debugging Apex test classes, test data factories, async test behavior, negative-path assertions, or callout mocking. Triggers: 'SeeAllData', 'Test.startTest', 'HttpCalloutMock', 'test data factory', 'missing assertions'. NOT for LWC Jest tests or code-coverage-only conversations detached from test design."
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
inputs:
  - "class or trigger under test and its entry points"
  - "required data setup including users, permissions, and related records"
  - "whether the code under test performs async work or callouts"
outputs:
  - "test design recommendation"
  - "review findings for test hygiene and coverage quality"
  - "test class scaffold with factory, assertions, and mocks"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-07
---

Use this skill when Apex tests need to prove behavior instead of merely satisfying deployment coverage. The objective is deterministic, isolated tests that verify positive paths, negative paths, bulk behavior, async execution, and callout behavior without depending on org data.

## Before Starting

- What business behavior must this test prove beyond "method executes without exception"?
- What data relationships and user context does the code require?
- Does the code under test enqueue async work, run in sharing-sensitive contexts, or make HTTP callouts?

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

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] Tests create their own data or use a documented factory pattern.
- [ ] `SeeAllData=true` is absent or explicitly justified.
- [ ] Assertions verify behavior, not just "no exception thrown."
- [ ] Async code is exercised with `Test.startTest()` and `Test.stopTest()`.
- [ ] Bulk-sensitive code has multi-record tests, not only single-record happy paths.
- [ ] Callout code uses mocks and verifies error handling as well as success.

## Salesforce-Specific Gotchas

1. **Async Apex does not execute inside a test until `Test.stopTest()`** — asserting before that point gives misleading failures.
2. **`SeeAllData=true` couples tests to org state** — a passing sandbox test can still fail in another org because the hidden data assumptions differ.
3. **Mixed DML still affects tests** — creating Users and setup-related data in the wrong sequence can fail test methods even when business logic is correct.
4. **One assertion at the end is not enough** — bulk, negative, and security-sensitive behaviors need focused assertions, not just a single record-count check.

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
