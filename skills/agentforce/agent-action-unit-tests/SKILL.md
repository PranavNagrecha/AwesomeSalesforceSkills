---
name: agent-action-unit-tests
description: "Apex test patterns for @InvocableMethod agent actions: per-reason-code branch coverage, bulk safety, callout mocking, deterministic assertions. NOT for testing whether the agent routes to the right topic or answers well — use agentforce/agent-testing-and-evaluation. NOT for designing the error envelope the tests assert on — use agentforce/agent-action-error-handling."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "my invocable action has low coverage"
  - "how do I test every reason_code branch"
  - "bulk test for agent action"
  - "flaky test on invocable class"
  - "write an apex test class for my agentforce invocable action"
  - "test an agent action that makes a callout without hitting the real endpoint"
tags:
  - agentforce
  - apex-tests
  - invocable
  - coverage
inputs:
  - "@InvocableMethod class"
outputs:
  - "Test class with per-branch assertions + bulk test"
dependencies: []
version: 1.1.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Agent Action Unit Tests

Agent actions are Apex classes with `@InvocableMethod`. They need the same testing rigor as any deployed Apex — plus two extras: every reason_code branch must be asserted, and the documented size-and-order contract (the i-th output corresponds to the i-th input) must be verified at a request count above one. UNVERIFIED (2026-10-03): earlier versions of this skill gave a 200-requests-per-invocation bound; no source read for this revision documents that number for agent actions, so 200 is used below as a test size, not as a platform limit.

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Which reason codes (or success/failure states) can the action return? | The Apex Developer Guide says an invocable method must report failures in its result objects and return as many results as inputs. | The list of literals the class can assign, one test per literal. | Every failure the agent may narrate is exercised before production. |
| Does the action call out, and does any DML run before the callout? | Test methods do not support real callouts, and DML before a mock callout needs `Test.startTest()` before `Test.setMock()` with the DML outside that block. | The callout order and the status classes (2xx, 4xx, 5xx, malformed) to mock. | Callout branches are tested without uncommitted-work failures. |
| Does the action enqueue Queueable, future, or batch work? | Async calls made after `Test.startTest()` run synchronously at `Test.stopTest()`; without the boundary they run after the test method's assertions. | Which async jobs to wait for and what they write. | Assertions check what the async job actually did. |
| Which user will the agent run as? | The agent user determines what the agent can access, and `System.runAs` enforces a user's sharing and object- and field-level permissions in tests. | A test user with the agent user's permission sets. | Tests fail when the agent user lacks access, not after deployment. |
| What is the team's coverage and assertion bar? | Line coverage is reported per class; the branch contract is a separate check. | A coverage bar plus the rule "one asserted test per reason code". | Coverage numbers stop hiding untested branches. |

## Recommended Workflow

1. List every reason_code the action can return; write one test per code.
2. Write a bulk test that submits 200 Request records, asserts 200 Response records come back in input order, and asserts query and DML counts stay flat (the synchronous limits are 100 SOQL queries and 150 DML statements per transaction).
3. For callout actions, use `Test.setMock` with canned 200/4xx/5xx responses and assert the branch classification. Put test-data DML before `Test.startTest()`, and call `Test.setMock()` after it.
4. Assert on `Response.reason_code`, never on `Response.user_message` text (the text can change for UX; the code is the contract).
5. Run `sf apex run test -c` and confirm per-class coverage meets the team bar (85% is this skill's bar; the platform minimum for deployment is lower) AND every reason_code has an explicit assertion. A complete action class, test class, mock, and manifest are in `references/metadata-examples.md`.

## Key Considerations

- Coverage % alone is misleading; the requirement is per-reason-code assertion coverage.
- Don't assert on user_message — it's UX copy; it will change.
- Mock every callout; no real HTTP from tests.

## Worked Examples (see `references/examples.md`)

- *Per-reason-code test matrix* — CloseCaseAction returns OK | VALIDATION_BLOCKED | UNKNOWN.
- *Bulk-safety harness* — Agent batches 200 requests into one action invocation.

## Common Gotchas (see `references/gotchas.md`)

| Gotcha | Symptom | Fix |
|---|---|---|
| Test.startTest/stopTest required for async | Async work queued outside the boundary runs after the test method's assertions | Call the action between `Test.startTest()` and `Test.stopTest()` |
| DML before a mock callout | Uncommitted-work failure on the mocked callout | DML first, then `Test.startTest()`, then `Test.setMock()` |
| @InvocableVariable default values | Missing fields on Request become null, not default | Set every field in a helper factory |
| Asserting on user_message strings | A UX change breaks 40 tests at once | Assert on the reason code; own the copy in one test |

Five more, with sources, are in `references/gotchas.md`.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Testing only the happy path with coverage padding.
- Asserting on user_message text.
- Skipping the bulk test because 'the agent only sends one at a time right now'.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html (returned HTTP 404 on 2026-10-03; current guide: https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-build-tests.html)
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
- Apex Developer Guide (Spring '26 PDF), testing and invocable sections: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Full list with the claim each source supports: `references/well-architected.md`
