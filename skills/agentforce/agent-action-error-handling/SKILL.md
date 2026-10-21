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
  - "return a typed error from an Agentforce Apex action instead of throwing"
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
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-21
---

# Agent Action Error Handling

Agentforce agents receive the return value of an Invocable action as-is and feed it back into the LLM loop. An unhandled exception becomes a Flow or framework error — the agent cannot reason about it, often re-invokes the action with the same inputs, and occasionally confabulates success. This skill defines a Response type that always returns (status, reason_code, user_message) so the subagent instructions can route deterministically.

> **Terminology.** Salesforce renamed agent *topics* to *subagents* in April 2026.
> Nothing about behaviour changed, and the API surface kept the old word —
> `GenAiPlugin` is still the metadata type behind a subagent, and `GenAiFunction`
> is still the action. This skill says *subagent instructions* for what older
> docs and your org's metadata call *topic instructions*.
>
> UNVERIFIED (2026-10-21): the April 2026 rename date is not in the corpus, and
> the Winter '27 guides pull both ways — api_meta 264 L80307-80308 still defines
> `GenAiPlugin` as "an agent topic", while pkg2_dev 264 L16999-17000 says
> `GenAiPlannerBundle` "defines the agent's actions and subagents". `GenAiFunction`
> "Represents an agent action" (api_meta 264 L78861-78862).

## The Platform Rule Everything Follows From

An `@InvocableMethod` must return one result per input, **in the same order,
even if errors occur** — "the Inputs and Outputs must match on both the size and
the order" (apexdev 264 L5510-5512), and "The execution of the invocable method
must run and return the same number of results as inputs received even if errors
occur", wrapping failures "in an Apex object that reports failures" (L5372-5373).

So an error is not an exception you throw. It is a **value you return in the
slot belonging to the failing request**. A thrown exception breaks the contract
for the whole batch, not just the request that failed (UNVERIFIED (2026-10-21):
the whole-batch consequence is not stated in the corpus).

Two further platform rules shape the class: "The invocable method must be static
and public or global, and its class must be an outer class", and "Only one method
in a class can have the InvocableMethod annotation" (apexdev 264 L5475-5476). One
action is one verb — see `templates/agentforce/AgentActionSkeleton.cls`.

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

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Can this action be invoked with many requests at once — from a flow, a batch, or a bulk agent run?" | Outputs must match inputs in size and order (apexdev 264 L5510-5512); per-row DML hits the 150-statement limit (L19757) and `LimitException` can't be caught (L40116-40123) — Gotchas 1, 2 | A two-phase, bulk-safe design with a pre-sized output list |
| "For each failure, can the user fix it, and would the same inputs succeed on a retry?" | `status` and `retryable` are independent axes; a single boolean makes the planner retry terminal errors (Gotcha 10) | A reason-code table with locus of control and retryability per code |
| "Does the action write data, and is there a stable key a retry could reuse?" | A retried mutation without idempotency is a duplicate write (Gotcha 11) | An External Id upsert key, or a decision to mark mutating failures terminal |
| "Could any error text reach the user — for example a validation rule message that quotes field values?" | `getMessage()` in `userMessage` leaks internals and PII into the transcript (Gotcha 6) | Authored `userMessage` copy per reason code, with raw errors only in the log |
| "Which errors will the code branch on, and by what — status code or message text?" | `Database.Error.getStatusCode()` returns a `StatusCode` (apexref 262 L148710-148719); message text is not a contract (Gotcha 7) | A classification keyed on `StatusCode` / `getDmlType` and HTTP status |
| "Is any of this code copied from an `@AuraEnabled` controller?" | `AuraHandledException` has no planner contract (Gotcha 3). UNVERIFIED (2026-10-21): not in the corpus | A grep result showing no `AuraHandledException` in invocable classes |
| "What should the agent say when the action returns nothing, and when it must not call again?" | An empty result reads as success unless instructions say otherwise (Gotcha 8) | One instruction per outcome class, including explicit "do not call again" lines |

A proper configuration adds what a bare try/catch skips: an error contract the planner can branch on, bulk-safety that keeps the error path reachable, and instructions that stop retry loops.

## Recommended Workflow

1. Design the Response class with the four fields above. Register every
   `reasonCode` in `Agent_Reason_Code__mdt` so Apex, subagent instructions, and
   dashboards share one contract.
2. Structure the method in two phases — validate and collect, then one bulkified
   `Database.<dml>(records, false, AccessLevel.USER_MODE)` — and assign results
   back by index into a pre-sized output list. Per-row DML hits the 150 DML
   statement limit (apexdev 264 L19757) under bulk invocation and raises a
   `System.LimitException`, which "can't be caught" — catch and finally blocks
   "aren't executed" (L40116-40123).
3. Classify by locus of control, branching on `Database.Error.getStatusCode()`
   (returns `StatusCode`, apexref 262 L148710-148719) or the HTTP status code —
   never on message text, which is localised and reworded between releases. Log the raw exception to
   `templates/apex/ApplicationLogger.cls`; never put `getMessage()` in
   `userMessage`.
4. Write one test per reason code asserting the code, the `retryable` flag, and
   that no raw platform error text reached `userMessage`. Coverage percentage is
   not the signal; assertions-per-reason-code is. Then run
   `python3 skills/agentforce/agent-action-error-handling/scripts/check_agent_action_error_handling.py --manifest-dir force-app`.
5. Add one subagent instruction per outcome class, including an explicit *"do not
   call the action again"* for terminal codes — the planner's default on an
   unsatisfied goal is to retry.
6. Run the Testing Center scenarios (Agentforce-enabled scratch orgs have the
   Testing Center, pkg2_dev 264 L17017) that exercise each branch and confirm
   the agent's wording matches the instruction for each code. UNVERIFIED
   (2026-10-21): the `sf agent test run` command name is not in the corpus; the
   DX MCP server lists a `run_agent_test` tool (sfdx_dev 264 L13395-13396).

## Key Considerations

- `userMessage` is user-visible and lands in a stored transcript. Validation-rule
  error text can interpolate field values, so `getMessage()` is a PII channel as
  well as an implementation-detail leak (UNVERIFIED (2026-10-21): the corpus
  defines `ValidationRule.errorMessage` only as a message of 255 characters or
  less, api_meta 264 L47780-47781, and says nothing of field interpolation).
- Distinguishing `NOT_FOUND` from `NO_ACCESS` helps internal users and leaks
  record existence on a guest channel. Decide per channel.
- `retryable = true` on a mutating action requires idempotency (a caller-supplied
  key upserted on an External Id). Otherwise a retried timeout is a duplicate
  write.
- The `@InvocableMethod` and `@InvocableVariable` `description` values are read
  by the planner to decide whether to call the action, and pre-fill the
  instruction fields in Agentforce Builder — they are functional, not
  documentation. UNVERIFIED (2026-10-21): the planner and Builder behaviour is
  from the Agentforce workshop, not the corpus; the corpus says the method
  description "appears as the action description in Flow Builder" (apexdev 264
  L5460) and `GenAiFunction.description` explains "the general purpose and domain
  of the action" (api_meta 264 L78897-78900).
- Watch the `SYSTEM_ERROR/UNKNOWN` **ratio** in production. It is the direct
  measure of classification debt; a jump after a release means an upstream
  contract changed.

## Worked Examples (see `references/examples.md`)

- *Typed Response envelope for a Case-update action* — Agentforce service agent closes Cases on user request.
- *Stable reason_code enum across releases* — A new DML error type appears after a managed-package install.

## Common Gotchas (see `references/gotchas.md`)

- **Throwing AuraHandledException from an Invocable** — The agent receives an opaque framework message and loops (UNVERIFIED (2026-10-21): not in the corpus).
- **Governor-limit exceptions pre-empt your catch** — LimitException (uncatchable, apexdev 264 L40116-40123) kills the transaction — agent sees raw Flow failure.
- **Empty list returned when input list is empty** — Agent receives an empty array and hallucinates a success message.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Rethrowing exceptions from an @InvocableMethod — the LLM cannot reason about framework errors.
- Putting `ex.getMessage()` directly into user_message — leaks internals and breaks deterministic subagent routing.
- Using boolean `success` instead of a reason_code enum — the agent cannot distinguish retryable from terminal failures.

## Official Sources Used

- apexdev 264 L5372-5373, L5475-5476, L5510-5512 — one result per input even if errors occur; static public/global in an outer class; one invocable method per class; size-and-order rule
- apexdev 264 L40116-40123 and L19757 — `LimitException` can't be caught; 150 DML statements per transaction
- InvocableMethod Annotation (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm
- Create Custom Actions Using Apex InvocableMethod — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-invocablemethod.html
- Agentforce Actions — https://developer.salesforce.com/docs/ai/agentforce/guide/get-started-actions.html
- Agentforce Metadata Types — https://developer.salesforce.com/docs/ai/agentforce/references/agents-metadata-tooling/agents-metadata.html
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=ai.agent_testing_center.htm&type=5
