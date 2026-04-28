---
name: agent-action-unit-tests
description: "Apex test patterns for @InvocableMethod agent actions: per-branch coverage, bulk safety, deterministic assertions. NOT for UI/LWC testing or agent conversational quality scoring."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Agent Action Unit Tests

Agent actions are Apex classes with `@InvocableMethod`. They need the same testing rigor as any deployed Apex — plus two extras: every reason_code branch must be asserted, and the bulk-size contract (≤200 per invocation) must be verified.

## Recommended Workflow

1. List every reason_code the action can return; write one test per code.
2. Write a bulk test that submits 200 Request records and asserts 200 Response records come back — no Limits.getDMLStatements() >150 failures.
3. For callout actions, use `Test.setMock` with canned 200/4xx/5xx responses and assert the branch classification.
4. Assert on `Response.reason_code`, never on `Response.user_message` text (the text can change for UX; the code is the contract).
5. Run `sf apex run test -c` and confirm per-class coverage ≥85% AND every reason_code has an explicit assertion.

## Key Considerations

- Coverage % alone is misleading; the requirement is per-reason-code assertion coverage.
- Don't assert on user_message — it's UX copy; it will change.
- Mock every callout; no real HTTP from tests.

## Worked Examples (see `references/examples.md`)

- *Per-reason-code test matrix* — CloseCaseAction returns OK | VALIDATION_BLOCKED | UNKNOWN.
- *Bulk-safety harness* — Agent batches 200 requests into one action invocation.

## Common Gotchas (see `references/gotchas.md`)

- **Test.startTest/stopTest required for async** — Queueable from inside Invocable doesn't run in test without the boundary.
- **@InvocableVariable default values** — Missing fields on Request become null, not default.
- **Asserting on user_message strings** — UX change breaks 40 tests at once.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Testing only the happy path with coverage padding.
- Asserting on user_message text.
- Skipping the bulk test because 'the agent only sends one at a time right now'.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
