---
name: apex-mocking-and-stubs
description: "Choosing and implementing Apex test doubles — `Test.setMock` and `StubProvider` — and designing the code seams they need. Triggers: 'StubProvider', 'Test.createStub', 'HttpCalloutMock', 'StaticResourceCalloutMock', 'mocking infrastructure'. NOT for multi-response or per-endpoint HTTP mocks — use apex/apex-http-callout-mocking. NOT for general test design — use apex/test-class-standards. Also covers the documented Stub API cannot-mock list, dependency-injection seams, and recording stub providers."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - test-setmock
  - httpcalloutmock
  - stubprovider
  - test-doubles
  - staticresourcecalloutmock
triggers:
  - "when should I use StubProvider in Apex"
  - "HttpCalloutMock versus StaticResourceCalloutMock"
  - "how do I mock a dependency in Apex tests"
  - "Test.createStub pattern for service seams"
  - "mocking infrastructure for Apex tests"
  - "test setmock isn't working"
  - "Test.createStub throws at runtime on my class"
  - "can't mock a static method in Apex"
  - "mocking a Batchable class in an Apex test"
  - "stub an interface so I can inject a fake selector"
  - "you have uncommitted work pending when mocking a callout"
  - "handleMethodCall signature for StubProvider"
  - "how do I assert what arguments my service passed a collaborator"
  - "remove Test.isRunningTest from production Apex"
  - "Test.createStub fails on an inner class"
inputs:
  - "type of dependency being replaced such as HTTP, SOAP, service class, or helper"
  - "whether the seam is an interface, virtual class, or transport-level callout"
  - "test scenarios needed such as success, timeout, retry, or malformed response"
outputs:
  - "mocking strategy recommendation"
  - "review findings for missing seams or weak test doubles"
  - "test double scaffold for callouts or service collaborators"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when the main problem is not “write more tests” but “make this dependency replaceable in tests.” Apex mocking is split across transport-level mocks like `HttpCalloutMock` and seam-level stubs via `StubProvider`. The right choice depends on what is being replaced and whether the production code already has a clean boundary.

## Before Starting

- What exactly must be replaced: an HTTP callout, a SOAP/web-service call, or an internal collaborator?
- Does the production code expose an injectable instance boundary (constructor argument, top-level interface), or is everything static, inner, or `new`-ed inline? `virtual` is not required — see `references/gotchas.md`.
- Which scenarios matter: success, auth failure, timeout, malformed payload, retry exhaustion?

## Questions to Ask Before Configuring

Ask these before writing a line of stub code. An agent that skips them ships a `StubProvider` against a type the platform refuses to stub, and finds out only when the test runs.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is the thing you want to replace on the far side of an HTTP or SOAP boundary, or is it Apex calling Apex?" | Decides `Test.setMock` versus `Test.createStub`; `setMock` intercepts only the HTTP classes and WSDL-generated code, so it cannot fake a service class | The double family, before any code is written — see `references/examples.md` Example 3 |
| "Show me the declaration of the class you want to stub — is it top-level, and does it have a public constructor?" | Inner classes and classes with only private constructors are on the documented cannot-mock list, and `Test.createStub` fails at *runtime*, not compile time | Either a green light or a refactor task sized before the sprint starts |
| "Is the dependency reached through a static method, a `@future`, or a `Batchable` class?" | All three are unstubbable; the answer is a seam, not a mocking trick | A concrete extraction: which methods move onto an injectable interface |
| "How does the production code get its collaborator today — constructor argument, `new` inline, or a static singleton?" | An inline `new` gives the test no injection point; a `Test.isRunningTest()` branch means the seam was never built | The constructor-injection change in `references/code-examples.md` § 2, or confirmation it already exists |
| "Which failure modes must the test prove — a thrown exception, an empty result, a refusal, a partial success?" | One happy-path double leaves every error branch uncovered while coverage looks healthy | The list of stub registrations (`returns` / `throwsOn`) the test class needs |
| "Do you need to assert on *what the service passed* the collaborator, or only on what came back?" | Argument assertions are the reason to record invocations rather than hand-write a fake; without them a bulkification bug passes | Whether a recording provider is warranted or a two-line fake is enough |
| "Does the test insert its own data before the callout, or does it use `@TestSetup`?" | DML before a callout leaves uncommitted work; the fix is a strict `startTest` → `setMock` ordering, not a retry | The exact statement order that keeps the test green |
| "Is the class being stubbed in the same namespace as the test, and does it carry an explicit sharing declaration?" | `Test.createStub` requires the mocked type to share the caller's namespace, and API 67.0 reversed the default sharing mode for undeclared classes | A namespace check plus an explicit `with sharing` / `inherited sharing` on the seam |

What a proper mocking design adds over just writing a mock class: the dependency is replaceable in production too (a second notifier, a sandbox-safe gateway), the test proves the arguments and not just the return value, and the seam survives the next refactor because it is a published interface rather than a test-only escape hatch.

---

## Core Concepts

### `Test.setMock` Is For Platform-Level Outbound Behavior

Use `HttpCalloutMock`, `WebServiceMock`, or `StaticResourceCalloutMock` when the code under test interacts with a platform-managed transport. These mocks are ideal when the test needs to simulate the remote system’s response shape.

### `StubProvider` Is For Replaceable Collaborators

`Test.createStub` with `StubProvider` is useful when the dependency is an Apex collaborator that can be represented by an interface or class seam. This supports behavior-focused tests without branching on `Test.isRunningTest()`.

### The Seam Matters More Than The Mock

If the production code uses static utility methods and hardcoded constructors everywhere, the test framework is not the real issue. The design seam is. Good mocking in Apex starts with injectable or overridable boundaries.

### Mock Variety Beats Single Happy-Path Doubles

One success mock is not enough. Reliable tests exercise failure modes, retries, and malformed responses too. The point of mocking infrastructure is control, not just convenience.

## Common Patterns

### Scenario-Specific `HttpCalloutMock`

**When to use:** Callout behavior changes with status code or payload.

**How it works:** Create separate mocks for success, auth failure, timeout-like exceptions, and invalid payloads.

**Why not the alternative:** One universal mock hides error-path bugs.

### Static Resource Mock For Stable Payload Fixtures

**When to use:** Response bodies are large, fixed, and easier to keep as sample files.

**How it works:** Use `StaticResourceCalloutMock` to return known payloads without embedding massive JSON in the test.

### Interface + StubProvider Seam

**When to use:** Business services depend on an internal collaborator rather than a raw transport.

**How it works:** Define an interface or stub-friendly class, then use `Test.createStub` to control return values and behavior in tests.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to simulate outbound HTTP responses | `HttpCalloutMock` | Purpose-built for HTTP transport behavior |
| Need large static response fixtures | `StaticResourceCalloutMock` | Cleaner payload management in tests |
| Need to replace an internal collaborator | `StubProvider` + `Test.createStub` | Better seam-level control than transport mocks |
| Production code only offers static helpers | Refactor seam first, then mock | Missing seam is the real blocker |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Classify the dependency.** Walk the routing table in `references/examples.md` Example 3 top to bottom and stop at the first match. If it lands on "Refactor first", stop writing test code — the deliverable is a seam, not a mock.
2. **Screen the target against the cannot-mock list.** Check `references/gotchas.md` § "The Stub API's Cannot Mock List Is Exact" before calling `Test.createStub`: top-level (not inner), public constructor, no `Database.Batchable`, no static/private/property target, no iterator in the signature, same namespace as the test.
3. **Build the seam.** Extract a top-level interface and give the consumer two constructors — a no-arg one that wires production collaborators and an injecting one for tests. Copy the shape from `references/code-examples.md` § 1–2; extend `templates/apex/BaseSelector.cls` for query seams and `templates/apex/BaseService.cls` for orchestration. Never add a `Test.isRunningTest()` branch.
4. **Write the provider.** Use the recording `StubProvider` in `references/code-examples.md` § 3 — canned returns by method name, every invocation recorded, an exception (not `null`) for unstubbed value-returning methods, and explicit `allowsVoid` registration for commands. For transport doubles use `templates/apex/tests/MockHttpResponseGenerator.cls` instead of writing a new `HttpCalloutMock`.
5. **Write the tests, including the failure and bulk paths.** Assert on recorded arguments, not only on return values (`references/code-examples.md` § 4). Order any callout test as DML → `Test.startTest()` → `Test.setMock()` → call → `Test.stopTest()`. Add the 200-record case using `templates/apex/tests/BulkTestPattern.cls`.
6. **Run the checker over the source tree**, then the tests:
   `python3 skills/apex/apex-mocking-and-stubs/scripts/check_apex_mocking_and_stubs.py --manifest-dir force-app/main/default/classes`
   then `sf apex run test --tests <ServiceTest> --result-format human --code-coverage --synchronous`.
7. **Record the decision.** Fill in `templates/apex-mocking-and-stubs-template.md` with the dependency type, the chosen double, and any cannot-mock item that forced a refactor, so the next reviewer does not re-litigate it.

---

## Review Checklist

- [ ] Mock choice matches the dependency type, not team habit.
- [ ] Tests cover at least one failure mode, not only success.
- [ ] Internal collaborators have interface or overridable seams where needed.
- [ ] No production branching exists solely to bypass dependencies in tests.
- [ ] Static resource mocks are used when fixture payload size justifies them.
- [ ] Mock classes remain focused and readable rather than becoming mini-frameworks.

## Salesforce-Specific Gotchas

1. **`StubProvider` does not rescue a design with only static dependencies** — the seam still has to exist.
2. **Transport mocks and seam stubs solve different problems** — do not use `HttpCalloutMock` to fake internal services.
3. **One global success mock can create false confidence** — retry and failure logic stay untested.
4. **Static resource mocks improve readability, but can hide contract drift if the payload is never reviewed** — keep fixtures intentional.
5. **The cannot-mock list is documented and exact** — statics (including `@future`), private methods, properties, triggers, inner classes, system types, `Batchable` implementors, private-constructor-only classes; iterators cannot be parameter or return types.
6. **A non-`virtual` class is stubbable** — stubs are anonymous subclasses generated at runtime, so sprinkling `virtual` around "to enable mocking" is cargo cult.
7. **`Test.createStub` failures are runtime failures** — a rejected type saves and deploys cleanly, then errors when the test executes.
8. **`Test.startTest()` goes before `Test.setMock()`** whenever the test does its own DML first.

Full detail, with the guide line ranges, in `references/gotchas.md` (12 entries).

## Output Artifacts

| Artifact | Description |
|---|---|
| Mocking strategy | Recommendation for `Test.setMock`, static-resource fixtures, or `StubProvider` seams |
| Test-double review | Findings on seam quality and missing failure scenarios |
| Mock scaffold | Focused example for callout or collaborator substitution |

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are building the seam — interface, injecting constructor, recording `StubProvider`, the test that asserts on recorded arguments, the negative example, `-meta.xml`, `package.xml`, and the `sf apex run test` verification |
| `references/gotchas.md` | Before calling `Test.createStub` or `Test.setMock` — the exact cannot-mock list, the namespace rule, the `startTest`/`setMock` ordering, void-method handling, and the API 67.0 sharing change |
| `references/examples.md` | You need the routing table that picks the double, or a worked `HttpCalloutMock` retry scenario and a compilable `StubProvider` seam |
| `references/llm-anti-patterns.md` | Reviewing generated test code — seven failure shapes with detection hints, including the `virtual`-is-required myth |
| `references/well-architected.md` | Tagging findings as Reliability or Operational Excellence, or citing the official sources behind any claim here |
| `templates/apex-mocking-and-stubs-template.md` | Recording the dependency-type / chosen-double / refactor decision for review |
| `scripts/check_apex_mocking_and_stubs.py` | Auditing an existing source tree: `--manifest-dir <classes dir>` |

## Related Skills

- `apex/test-class-standards` — use when the broader testing design is the real issue and mocking is only one symptom.
- `apex/callouts-and-http-integrations` — use when the hardest part is the outbound HTTP contract itself.
- `apex/apex-design-patterns` — use when missing interfaces or injectable boundaries are blocking good mocks.
- `apex/apex-http-callout-mocking` — use when the mock itself needs per-endpoint routing, sequenced responses, or static-resource fixtures; that skill owns `HttpCalloutMock` depth.
- `apex/apex-test-setup-patterns` — use when the question is `@TestSetup` scope, data isolation, or why the fixture is not visible in the test method.
- `apex/test-data-factory-patterns` — use when the stub is fine but the records it returns are the problem.
