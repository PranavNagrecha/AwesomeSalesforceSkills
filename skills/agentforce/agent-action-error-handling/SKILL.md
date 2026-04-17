---
name: agent-action-error-handling
description: "Design Invocable Apex actions that return deterministic, agent-friendly errors instead of surfacing raw exceptions to the LLM. NOT for generic Apex exception handling or Flow fault paths."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
triggers:
  - "my agent action throws and the agent loops"
  - "invocable action leaks stack trace to user"
  - "how should I classify errors for an agent"
  - "agent retries after a validation rule failure"
tags:
  - agentforce
  - invocable-actions
  - error-handling
  - apex
inputs:
  - "Invocable action Apex class"
  - "expected agent behavior on failure"
outputs:
  - "Updated class returning typed error envelope"
  - "topic instruction update for retry vs. terminal errors"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Agent Action Error Handling

Agentforce agents receive the return value of an Invocable action as-is and feed it back into the LLM loop. An unhandled exception becomes a Flow or framework error — the agent cannot reason about it, often re-invokes the action with the same inputs, and occasionally confabulates success. This skill defines a Response type that always returns (status, reason_code, user_message) so the topic instructions can route deterministically.

## When to Use

Any custom Apex action exposed as an Invocable for Agentforce — callouts, DML, SOQL with user-supplied filters, Experience Cloud actions. Not for pure read-only actions whose failure is acceptable silence (rare).

Typical trigger phrases that should route to this skill: `my agent action throws and the agent loops`, `invocable action leaks stack trace to user`, `how should I classify errors for an agent`, `agent retries after a validation rule failure`.

## Recommended Workflow

1. Design a Response inner class with status (OK|USER_ERROR|SYSTEM_ERROR), reason_code (stable enum string), and user_message (≤140 char sentence the agent can repeat).
2. Wrap the entire @InvocableMethod body in try/catch; translate DmlException/CalloutException/QueryException to USER_ERROR or SYSTEM_ERROR with a reason_code; never rethrow.
3. Write tests that force each catch branch: invalid input, DML rollback, callout 500, governor-limit exceeded. Assert the returned reason_code, not just that no exception escaped.
4. In the Agent Topic instructions, add one rule per reason_code ('on reason_code=USER_ERROR restate the user_message to the user; on SYSTEM_ERROR apologize and hand off').
5. Deploy, run the Agentforce Testing Center scenarios that exercise each branch, and confirm the agent text matches the instruction for each reason_code.

## Key Considerations

- Agentforce appends the raw Flow error message to the conversation when an action throws. This leaks stack traces and implementation details to users.
- `user_message` is user-visible — never concatenate exception.getMessage() verbatim.
- The LLM will retry transient errors with the same inputs unless you classify them as terminal. Use reason_code to signal retryable vs. terminal.
- Log the raw exception to a custom Log__c or ApplicationLogger at USER_ERROR and SYSTEM_ERROR — the agent shouldn't see the detail but SRE needs it.

## Worked Examples (see `references/examples.md`)

- *Typed Response envelope for a Case-update action* — Agentforce service agent closes Cases on user request.
- *Stable reason_code enum across releases* — A new DML error type appears after a managed-package install.

## Common Gotchas (see `references/gotchas.md`)

- **Throwing AuraHandledException from an Invocable** — The agent receives an opaque framework message and loops.
- **Governor-limit exceptions pre-empt your catch** — LimitException (uncatchable) kills the transaction — agent sees raw Flow failure.
- **Empty list returned when input list is empty** — Agent receives an empty array and hallucinates a success message.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Rethrowing exceptions from an @InvocableMethod — the LLM cannot reason about framework errors.
- Putting `ex.getMessage()` directly into user_message — leaks internals and breaks deterministic topic routing.
- Using boolean `success` instead of a reason_code enum — the agent cannot distinguish retryable from terminal failures.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
