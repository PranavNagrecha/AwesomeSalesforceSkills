---
name: agent-action-error-handling
description: "Design Invocable Apex actions that return deterministic, agent-friendly errors instead of surfacing raw exceptions to the LLM. NOT for authoring the action itself — @InvocableMethod schema, labels, security context — use agentforce/custom-agent-actions-apex. NOT for the Apex tests that force each error branch — use agentforce/agent-action-unit-tests."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Agent Action Error Handling

Agentforce agents receive the return value of an Invocable action as-is and feed it back into the LLM loop. An unhandled exception becomes a Flow or framework error — the agent cannot reason about it, often re-invokes the action with the same inputs, and occasionally confabulates success. This skill defines a Response type that always returns (status, reason_code, user_message) so the subagent instructions can route deterministically.

> **Terminology.** Salesforce renamed agent *topics* to *subagents* in April 2026.
> Nothing about behaviour changed, and the API surface kept the old word —
> `GenAiPlugin` is still the metadata type behind a subagent, and `GenAiFunction`
> is still the action. This skill says *subagent instructions* for what older
> docs and your org's metadata call *topic instructions*.

## The Platform Rule Everything Follows From

An `@InvocableMethod` must return one result per input, **in the same order,
even when errors occur** — the inputs and outputs *"must match on both the size
and the order"*
([InvocableMethod Annotation](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm)).

So an error is not an exception you throw. It is a **value you return in the
slot belonging to the failing request**. A thrown exception breaks the contract
for the whole batch, not just the request that failed.

Two further platform rules shape the class: the method must be `static`,
`public` or `global`, and live in an **outer** class; and there is **one
invocable method per class**. One action is one verb — see
`templates/agentforce/AgentActionSkeleton.cls`.

## The Envelope

| Field | Type | Purpose |
|---|---|---|
| `status` | `OK` \| `USER_ERROR` \| `SYSTEM_ERROR` | Locus of control — whose problem is this |
| `reasonCode` | stable enum string | What the subagent instructions branch on |
| `userMessage` | ≤140 chars, authored | Safe to read aloud verbatim |
| `retryable` | Boolean | Would the *same* inputs plausibly succeed |

`status` and `retryable` are independent axes. A row lock is a retryable system
error; a validation failure is a terminal user error; a 503 is a retryable
system error. Collapsing them into one `Boolean success` is the single most
common cause of agent retry loops.

## Recommended Workflow

1. Design the Response class with the four fields above. Register every
   `reasonCode` in `Agent_Reason_Code__mdt` so Apex, subagent instructions, and
   dashboards share one contract.
2. Structure the method in two phases — validate and collect, then one bulkified
   `Database.<dml>(records, false, AccessLevel.USER_MODE)` — and assign results
   back by index into a pre-sized output list. Per-row DML raises an
   *uncatchable* `LimitException` under bulk invocation, which defeats every
   `catch` you write.
3. Classify by locus of control, branching on `Database.Error.getStatusCode()`
   or the HTTP status code — never on message text, which is localised and
   reworded between releases. Log the raw exception to
   `templates/apex/ApplicationLogger.cls`; never put `getMessage()` in
   `userMessage`.
4. Write one test per reason code asserting the code, the `retryable` flag, and
   that no raw platform error text reached `userMessage`. Coverage percentage is
   not the signal; assertions-per-reason-code is.
5. Add one subagent instruction per outcome class, including an explicit *"do not
   call the action again"* for terminal codes — the planner's default on an
   unsatisfied goal is to retry.
6. Run the Testing Center / `sf agent test run` scenarios that exercise each
   branch and confirm the agent's wording matches the instruction for each code.

## Key Considerations

- `userMessage` is user-visible and lands in a stored transcript. Validation-rule
  error text can interpolate field values, so `getMessage()` is a PII channel as
  well as an implementation-detail leak.
- Distinguishing `NOT_FOUND` from `NO_ACCESS` helps internal users and leaks
  record existence on a guest channel. Decide per channel.
- `retryable = true` on a mutating action requires idempotency (a caller-supplied
  key upserted on an External Id). Otherwise a retried timeout is a duplicate
  write.
- The `@InvocableMethod` and `@InvocableVariable` `description` values are read
  by the planner to decide whether to call the action, and pre-fill the
  instruction fields in Agentforce Builder — they are functional, not
  documentation.
- Watch the `SYSTEM_ERROR/UNKNOWN` **ratio** in production. It is the direct
  measure of classification debt; a jump after a release means an upstream
  contract changed.

## Worked Examples (see `references/examples.md`)

- *Typed Response envelope for a Case-update action* — Agentforce service agent closes Cases on user request.
- *Stable reason_code enum across releases* — A new DML error type appears after a managed-package install.

## Common Gotchas (see `references/gotchas.md`)

- **Throwing AuraHandledException from an Invocable** — The agent receives an opaque framework message and loops.
- **Governor-limit exceptions pre-empt your catch** — LimitException (uncatchable) kills the transaction — agent sees raw Flow failure.
- **Empty list returned when input list is empty** — Agent receives an empty array and hallucinates a success message.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Rethrowing exceptions from an @InvocableMethod — the LLM cannot reason about framework errors.
- Putting `ex.getMessage()` directly into user_message — leaks internals and breaks deterministic subagent routing.
- Using boolean `success` instead of a reason_code enum — the agent cannot distinguish retryable from terminal failures.

## Official Sources Used

- InvocableMethod Annotation (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm
- Create Custom Actions Using Apex InvocableMethod — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-invocablemethod.html
- Agentforce Actions — https://developer.salesforce.com/docs/ai/agentforce/guide/get-started-actions.html
- Agentforce Metadata Types — https://developer.salesforce.com/docs/ai/agentforce/references/agents-metadata-tooling/agents-metadata.html
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=ai.agent_testing_center.htm&type=5
