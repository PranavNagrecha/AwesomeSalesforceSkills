# Gotchas: Agentforce Agent Handoff

Gotchas 1 to 5 are carried from the earlier version and now say what an official source supports. Gotchas 6 to 12 are platform mechanics with a cited source.

## Gotcha 1: Escalation needs a fallback queue, and presence can strand users

**What happens:** The agent says it is connecting the customer, and nothing happens. The conversation waits with no person available.

**When it occurs:** No fallback queue exists for the channel, or the queue has nobody available and there is no time-based fallback.

**How to avoid:** Create an Omni-Channel fallback queue that supports the Messaging Session object for each channel, and design what happens when no rep is available (callback, case, opening-hours message).

**Source:** Agentforce Developer Guide, Multi-Surface Example: Build and Deploy an Enhanced Chat Agent: "A fallback queue is required so that conversations can escalate to a human service rep." UNVERIFIED (2026-10-03): the earlier claim that Omni-Channel parks a conversation "without telling the user"; the user-facing behaviour depends on the routing configuration.

---

## Gotcha 2: Routing by case owner and routing by queue behave differently

**What happens:** Cases created at handoff skip capacity rules, or land with one person who is off shift.

**When it occurs:** The handoff action assigns an owner directly instead of using a queue.

**How to avoid:** Route through a queue when Omni-Channel capacity and presence should apply. Assign an owner only for a deliberate named handoff.

**Source:** UNVERIFIED (2026-10-03): no source read compares owner assignment with queue routing for agent handoffs. Keep the decision explicit in the design.

---

## Gotcha 3: Raw transcript dumps make the handoff slower, not faster

**What happens:** The rep receives thirty turns of transcript in the case description and asks the customer to start again.

**When it occurs:** The context package is the whole conversation.

**How to avoid:** Write a short structured summary (intent, what was tried, why the handoff fired) and link the full transcript. The example in `references/metadata-examples.md` uses three labelled lines and a fixed reason vocabulary.

**Source:** Generative AI guide (Spring '26), Agent Topic: Escalation: add actions that "gather information and create or update a record" so that the rep does not have to. UNVERIFIED (2026-10-03): the claim that reps skip long transcripts is a design observation, not a documented fact.

---

## Gotcha 4: Handing to another agent starts a different agent, not a continuation

**What happens:** The receiving agent ignores the instructions and context the first subagent had.

**When it occurs:** A team expects agent-to-agent delegation to carry the previous subagent's instructions.

**How to avoid:** Pass what the receiver needs explicitly (variables, a summary) and design the receiver to stand alone. A connected subagent is a complete, independent agent with its own expertise and identity.

**Source:** Agentforce Developer Guide, Agent Script Blocks: "A connected subagent represents a complete, independent agent with its own distinct expertise and identity."

---

## Gotcha 5: Hand-back is not automatic

**What happens:** After the rep resolves the issue, the team expects the agent to pick the conversation back up, and it does not.

**When it occurs:** Hand-back is assumed rather than designed.

**How to avoid:** Design hand-back explicitly: what triggers it, what context returns, and what the customer sees. Within one agent, a transition to another subagent does not return either: control passes one way, and you must add an explicit transition back.

**Source:** Agentforce Developer Guide, Agent Script Reference: Utils ("Transitions are one way. There's no return of control to the calling subagent"). UNVERIFIED (2026-10-03): how a session resumes after a human takes over; no source read documents agent resumption after escalation.

---

## Gotcha 6: Only the standard Escalation topic can route to service reps in the legacy builder

**What happens:** A team builds a custom "Talk to a Human" topic, and it never transfers anyone.

**When it occurs:** Escalation is modelled as an ordinary custom topic.

**How to avoid:** Customize the standard Escalation topic's classification description and instructions instead. It routes through the associated outbound Omni-Channel flow, which only that topic can invoke. As configured initially, it escalates only when the customer asks for a person; widen it to your policy.

**Source:** Generative AI guide, Agent Topic: Escalation ("No other standard topics can route conversations to live service representatives, and Create a Custom Topic can't be configured to do so"; "this topic escalates conversations only when customers ask to speak to a human, but rules regarding escalation are customizable").

---

## Gotcha 7: `@utils.escalate` needs a connection block, and `escalate` is reserved

**What happens:** An Agent Script agent calls escalate and nothing routes, or the script fails because a subagent is named `escalate`.

**When it occurs:** The connection block is missing, or the reserved word is used as a name.

**How to avoid:** Declare a `connection messaging` block with `outbound_route_type` and `outbound_route_name` that point at an active Omni-Channel flow. Name subagents and actions anything but `escalate`.

**Source:** Agentforce Developer Guide, Agent Script Reference: Utils ("To use utils.escalate, you need an active Omni-Channel connection ... defined in a connection messaging block with outbound_route_type and outbound_route_name values"; "escalate is a reserved keyword").

---

## Gotcha 8: Standard actions on the Escalation topic leak data

**What happens:** An external customer reaches broad data through a standard action attached to the Escalation topic.

**When it occurs:** Standard actions are added to Escalation for convenience, for example to look up records before transfer.

**How to avoid:** Use custom actions with a narrow field list on the Escalation topic.

**Source:** Generative AI guide, Agent Topic: Escalation: "Avoid associating standard actions with the Escalation topic. Standard actions have broad data access not intended for external use cases. Define custom actions instead."

---

## Gotcha 9: Without a fallback route, an unavailable primary route ends the handoff

**What happens:** The primary escalation path is unavailable and the customer is left in the agent conversation.

**When it occurs:** Only one escalation route is configured.

**How to avoid:** Configure a fallback escalation behaviour. In Metadata API 65.0 and later, `Bot.defaultOutboundFlow` "specifies a fallback escalation behavior if the primary agent escalation behavior is not available."

**Source:** Metadata API Developer Guide (API 67.0), Bot, `defaultOutboundFlow`.

---

## Gotcha 10: Human handoff over enhanced Messaging needs a Service Agent

**What happens:** An internal-style agent is designed for a customer messaging channel with human escalation, and it cannot be connected.

**When it occurs:** The agent type is chosen before the channel.

**How to avoid:** Use Agentforce Service Agent for enhanced Messaging and Bring Your Own Channel, which is where Omni-Channel escalation applies.

**Source:** Generative AI guide, Considerations for Agents: "Currently, only Agentforce Service Agent can connect to enhanced Messaging channels and Bring Your Own Channel."

---

## Gotcha 11: Deactivating an agent is not a handoff

**What happens:** An admin deactivates the agent to stop a bad behaviour; every open conversation receives the system error message and nobody is routed anywhere.

**When it occurs:** Deactivation is used as an emergency "send everyone to humans" switch.

**How to avoid:** Plan an emergency route that changes the channel's routing target or escalation behaviour instead of deactivating the agent.

**Source:** Generative AI guide, Activate or Deactivate Your Agent: "Deactivating an agent interrupts any ongoing user conversations. Users aren't notified that an agent is deactivated. The agent sends the system error message as a response to any messages."

---

## Gotcha 12: A subagent transition restarts the target subagent

**What happens:** After a detour to a verification subagent, the agent repeats questions the customer already answered in the original subagent.

**When it occurs:** A design transitions away and back, expecting the original subagent to resume mid-step.

**How to avoid:** Store progress in variables before transitioning, and branch on them at the start of the subagent you return to.

**Source:** Agentforce Developer Guide, Agent Script Reference: Utils: "When transitioning back to a subagent, the flow starts at the beginning of the subagent, not where it last left off."
