# Gotchas — Agentforce Multi-Turn Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Sources: Agentforce Developer Guide pages under `developer.salesforce.com/docs/ai/agentforce/guide/` (Agent Script reference and patterns, testing pages) and "Quickstart Your Einstein Generative AI Solution" (Generative AI guide, Spring '26 PDF), read on 2026-10-03. The guide's April 2026 note says agent topics are now called subagents with no change in functionality.

## Gotcha 1: Variables Are Agent-Wide, So Stale Values Follow the User Into Other Subagents

**What happens:** Earlier versions of this skill said variables captured in subagent A disappear when the conversation enters subagent B unless scoped cross-subagent. The Agent Script reference says the opposite: "You define all variables in the variables block, and all subagents in the agent can access the variables." The real failure is the inverse. A `case_id` set while troubleshooting is still populated when the user moves to billing, and a billing action that takes an optional case reference picks it up.

**When it occurs:** When authors assume subagent exit clears state, or when two subagents reuse a generic variable name.

**How to avoid:** Give each variable a name and description that says who owns it. Reset owned variables explicitly when their subagent finishes (`set @variables.case_id = ""`). Use `available when` conditions so actions only appear when their inputs are meant to be set.

**Source:** Agentforce Developer Guide, Agent Script Reference: Variables (Custom and Linked); Agent Script Pattern: Using Variables Effectively.

---

## Gotcha 2: How Much History the Model Sees Depends on the Agent Type

**What happens:** Ten turns in, an employee agent ignores a fact from turn 2. For Agentforce (Default), the Generative AI guide says conversation history applies to the current session only and messages from up to the most recent six turns are used as context. For Agent Script agents, the system-variables page says the LLM remembers the entire conversation history, yet the same guide positions variables as the way to "reliably store information about the agent's current state, rather than relying on LLM context memory".

**When it occurs:** Any design that relies on the model to recall an earlier answer instead of storing it.

**How to avoid:** Store every fact that later turns depend on in a variable at the moment it is given. For Agentforce (Default), assume anything older than six turns is gone.

**Source:** Generative AI guide, Agents Limits (six turns for Agentforce (Default)); Agentforce Developer Guide, Agent Script Reference: System Variables and Get Started with Agent Script.

---

## Gotcha 3: A Refresh or a Second Tab Starts a New Agentforce (Default) Session

**What happens:** A user refreshes the browser tab, or opens the agent in a second tab, and the agent has no memory of the conversation. Agentforce (Default) sessions are specific to a browser tab; a new session starts on refresh or in another tab.

**When it occurs:** Long employee-agent tasks where the user navigates away and back, or works in two tabs.

**How to avoid:** Document this in user-facing help. For work that must survive, write durable state to platform data (Case, custom object) and design the agent to read it back.

**Source:** Generative AI guide, Considerations for Agent Conversations.

---

## Gotcha 4: A User Correction Does Not Invalidate Downstream Variables

**What happens:** The user says "actually, change the order number to A7843". The agent updates `order_number`, but `item_id`, resolved from the old order, is now stale.

**When it occurs:** Correction patterns that update one variable without resetting the variables derived from it.

**How to avoid:** Write the dependency map as part of the design. When `order_number` changes, reset `item_id` and `return_reason` in the same instruction block, then re-run the lookup action. Variables are mutable only when declared `mutable`, so mark derived values mutable and give the source values clear descriptions.

**Source:** Agentforce Developer Guide, Agent Script Reference: Variables (the `mutable` property); design guidance carried from earlier revisions.

---

## Gotcha 5: Session End Wipes Variables

**What happens:** The user leaves and comes back; the agent has forgotten everything and the user starts over. Variables live for the session only.

**When it occurs:** Long-running tasks (returns, complex tickets) that outlast a session. UNVERIFIED (2026-10-03): session timeout values are not stated in any source read for this revision.

**How to avoid:** Persist critical state to a platform record on each significant turn, and rehydrate from it when the user returns.

**Source:** Agentforce Developer Guide, Agent Script Reference: Variables ("remember information across conversation turns ... throughout the session").

---

## Gotcha 6: Asking One Question Per Turn When One Reply Could Fill Several Slots

**What happens:** The agent asks three clarifying questions in a row and the user abandons.

**When it occurs:** When each ambiguity is handled as its own turn.

**How to avoid:** Ask for related facts together and let one tool call set several variables. Agent Script's slot filling uses `@utils.setVariables` with `...` values, and the guide's example sets `first_name` and `last_name` from one user reply. Ask one question at a time only when the second depends on the first answer.

**Source:** Agentforce Developer Guide, Agent Script Pattern: Using Variables Effectively ("Let the LLM set variables with user-entered information (slot filling)") and Agent Script Reference: Utils (`setVariables`).

---

## Gotcha 7: Slot Filling Only Works for Inputs the LLM Calls

**What happens:** A chained action expects the LLM to fill an input from the conversation and receives nothing. The guide states slot filling works for top-level action inputs, which the LLM calls, but not for chained action inputs, which run deterministically.

**When it occurs:** When an action is moved from a reasoning tool into an action chain without changing how its inputs are supplied.

**How to avoid:** For chained actions, pass inputs from variables or from the previous action's outputs. Capture user-provided values into variables first.

**Source:** Agentforce Developer Guide, Agent Script Pattern: Using Variables Effectively.

---

## Gotcha 8: Escalation Needs an Omni-Channel Connection, and Context Does Not Travel by Itself

**What happens:** The agent decides to escalate and nothing happens, or the rep receives only the last message. `@utils.escalate` requires an active Omni-Channel connection defined in a connection messaging block with `outbound_route_type` and `outbound_route_name` values.

**When it occurs:** Agents built and tested before the messaging channel and Omni-Channel flow exist, or escalation designs that never specify what context the rep sees.

**How to avoid:** Configure the connection and route before testing escalation. Write the context the rep needs (variables, case number, reason) to the record the Omni-Channel flow routes. UNVERIFIED (2026-10-03): what transcript the rep sees depends on the channel and flow; no source read for this revision describes it.

**Source:** Agentforce Developer Guide, Agent Script Reference: Utils (`utils.escalate`).

---

## Gotcha 9: Overlapping Subagent Descriptions Cause Routing Instability

**What happens:** The user says "cancel"; sometimes it routes to Cancel_Subscription, sometimes to Cancel_Order.

**When it occurs:** Subagent and transition descriptions that are not discriminating. The agent chooses transitions from their descriptions and names.

**How to avoid:** Make descriptions mutually exclusive and specific. Name transition tools with a `go_to_` prefix. Where the choice is a business rule, use a deterministic conditional transition instead of LLM choice. If ambiguity is unavoidable, have the router ask which one the user means.

**Source:** Agentforce Developer Guide, Agent Script Pattern: Subagent Transitions (best practices) and Agent Router.

---

## Gotcha 10: There Is No Usable `id` Variable Type

**What happens:** Earlier versions of this skill advised typing record references as `Id` instead of `String`. In Agent Script, `id` is deprecated for both custom and linked variables: "Use string to store a Salesforce record ID." Action input and output types follow the same rule.

**When it occurs:** Variable blocks written from Apex habits.

**How to avoid:** Declare record IDs as `string` and validate the format in the action that consumes them. Use `date` for dates, `number` for numbers, and `list[type]` for lists.

**Source:** Agentforce Developer Guide, Agent Script Reference: Variables (types table) and Agent Script Reference: Actions (input and output types).

---

## Gotcha 11: Exact Values Should Not Be Reconstructed From History

**What happens:** An address or phone number stated early is later reproduced slightly wrong. Relying on the model's reading of history gives paraphrase, not storage. UNVERIFIED (2026-10-03): earlier versions of this skill attributed this to a built-in turn-history summarization feature; no source read for this revision describes one.

**When it occurs:** Designs that read exact values back out of the conversation instead of out of variables.

**How to avoid:** Capture exact values into variables when they are stated, and show them back from the variable (`{!@variables.customer_email}`) when confirming.

**Source:** Agentforce Developer Guide, Agent Script Reference: Variables (referencing variables in reasoning instructions).

---

## Gotcha 12: `reset_to_initial_node` Turns Every Turn Into a Fresh Start

**What happens:** A multi-turn flow keeps jumping back to the router. In the agent's config `runtime` sub-block, `reset_to_initial_node: True` makes each new customer turn restart at the `start_agent` block instead of resuming where the previous turn left off.

**When it occurs:** When a setting meant for stateless, one-shot Q&A agents is copied into a conversational agent.

**How to avoid:** Leave `reset_to_initial_node` off (the default) for multi-turn flows, as the guide recommends.

**Source:** Agentforce Developer Guide, Agent Script Blocks (Runtime Sub-Block).

---

## Gotcha 13: Transitions Are One Way, and a Return Starts From the Top

**What happens:** After a detour to an identity subagent, the user lands at the beginning of the original subagent and is asked the first question again. When a transitioned-to subagent completes, control does not return to the caller, and transitioning back starts the subagent from the beginning.

**When it occurs:** Detours (verification, FAQ) inserted into the middle of a multi-step flow, or A-to-B-to-A designs that can loop.

**How to avoid:** Branch at the top of the subagent on which variables are still empty (or on a progress variable) so a return resumes at the right place. Check that no pair of subagents can transition to each other indefinitely.

**Source:** Agentforce Developer Guide, Agent Script Reference: Utils (`transition to`) and Agent Script Pattern: Subagent Transitions ("Avoid transition loops").

---

## Gotcha 14: Action Outputs Stay in Context for the Whole Session

**What happens:** A lookup action returns a customer's date of birth for verification, and the agent mentions it again five turns later. By default, the agent remembers an action's output information for the entire session.

**When it occurs:** Actions that return sensitive or bulky data the conversation does not need after the current step.

**How to avoid:** Set `filter_from_agent: True` on outputs the model should not keep in context, and store only what later turns need in variables.

**Source:** Agentforce Developer Guide, Agent Script Reference: Actions (output parameters, `filter_from_agent`).
