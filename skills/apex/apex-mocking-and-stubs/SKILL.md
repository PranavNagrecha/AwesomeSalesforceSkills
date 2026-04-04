---
name: apex-mocking-and-stubs
description: "Use when choosing or implementing Apex test doubles with `Test.setMock`, `HttpCalloutMock`, `StaticResourceCalloutMock`, or `StubProvider`, and when designing code seams to support those doubles cleanly. Triggers: 'StubProvider', 'Test.createStub', 'HttpCalloutMock', 'StaticResourceCalloutMock', 'mocking infrastructure'. NOT for general Apex test design outside the mocking and seam problem."
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
inputs:
  - "type of dependency being replaced such as HTTP, SOAP, service class, or helper"
  - "whether the seam is an interface, virtual class, or transport-level callout"
  - "test scenarios needed such as success, timeout, retry, or malformed response"
outputs:
  - "mocking strategy recommendation"
  - "review findings for missing seams or weak test doubles"
  - "test double scaffold for callouts or service collaborators"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when the main problem is not “write more tests” but “make this dependency replaceable in tests.” Apex mocking is split across transport-level mocks like `HttpCalloutMock` and seam-level stubs via `StubProvider`. The right choice depends on what is being replaced and whether the production code already has a clean boundary.

## Before Starting

- What exactly must be replaced: an HTTP callout, a SOAP/web-service call, or an internal collaborator?
- Does the production code expose an interface or virtual instance method boundary, or is everything static?
- Which scenarios matter: success, auth failure, timeout, malformed payload, retry exhaustion?

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

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

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

## Output Artifacts

| Artifact | Description |
|---|---|
| Mocking strategy | Recommendation for `Test.setMock`, static-resource fixtures, or `StubProvider` seams |
| Test-double review | Findings on seam quality and missing failure scenarios |
| Mock scaffold | Focused example for callout or collaborator substitution |

## Related Skills

- `apex/test-class-standards` — use when the broader testing design is the real issue and mocking is only one symptom.
- `apex/callouts-and-http-integrations` — use when the hardest part is the outbound HTTP contract itself.
- `apex/apex-design-patterns` — use when missing interfaces or injectable boundaries are blocking good mocks.
