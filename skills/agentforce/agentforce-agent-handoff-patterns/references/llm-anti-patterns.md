# LLM Anti-Patterns: Agentforce Agent Handoff

Mistakes AI assistants make when designing how an agent hands a conversation to a person, another agent or a workflow. Each entry gives the mistake, why an assistant makes it, and the correct move.

## Anti-Pattern 1: "Handoff On Error" With No Trigger Design

**What the LLM generates:** "When the agent encounters an error, escalate to a human."

**Why it happens:** Errors are the most visible trigger, so the assistant designs only for them.

**Correct pattern:** Design triggers across six categories: user-initiated, confidence, scope, policy, authorization and technical. Write each into the Escalation topic's classification description and instructions (legacy builder) or into the conditions around `@utils.escalate` (Agent Script). The standard Escalation topic escalates only when the customer asks for a person until you widen it (Generative AI guide, Agent Topic: Escalation).

## Anti-Pattern 2: Verbatim Transcript As Context

**What the LLM generates:** A handoff action that packs the entire turn history into the case description.

**Why it happens:** More context feels safer than less.

**Correct pattern:** A structured summary (intent, what was tried, handoff reason from a fixed vocabulary) plus a link to the transcript. The rep benefits from the summary; the link preserves the full history for audit. See `references/metadata-examples.md`, Example 1.

## Anti-Pattern 3: No Deflection Path

**What the LLM generates:** Handoff logic that assumes a person is always available.

**Why it happens:** The happy path dominates the design.

**Correct pattern:** A fallback queue that supports the Messaging Session object, a fallback escalation behaviour (`Bot.defaultOutboundFlow`, API 65.0 and later), and a next-best-action when nobody is available: a callback, a case, or opening hours. The Enhanced Chat example states that a fallback queue is required for escalation.

## Anti-Pattern 4: Silent Transfer

**What the LLM generates:** A handoff that fires with no message to the customer.

**Why it happens:** The transfer looks like a back-office step.

**Correct pattern:** Every handoff has an explicit user message, with the expected wait when it is known. In Agent Script, the `connection messaging` block carries an `escalation_message`; in the builder, the Enhanced Chat v2 settings take an escalation message alongside the escalation flow.

## Anti-Pattern 5: Missing Confidence-Based Escalation

**What the LLM generates:** Handoff triggers only on hard errors.

**Why it happens:** Confidence is harder to define than an exception.

**Correct pattern:** Retry, then escalate after a set number of unsuccessful attempts on the same intent, tracked in a variable. This prevents loops. Gate `@utils.escalate` with an `available when` condition when it should only appear in some states (for example business hours).

## Anti-Pattern 6: Building a Custom "Talk to a Human" Topic

**What the LLM generates:** Instructions to create a new custom topic named "Human Handoff" with an action that "transfers the chat".

**Why it happens:** Every other capability is a custom topic plus actions, so the assistant applies the same recipe.

**Correct pattern:** In the legacy builder, customize the standard Escalation topic; it is the only topic that can invoke the outbound Omni-Channel flow, and a custom topic cannot be configured to route to service reps. In Agent Script, use `@utils.escalate` with a `connection messaging` block.

## Anti-Pattern 7: Expecting a Subagent Transition to Return

**What the LLM generates:** "Transition to the Verification subagent, and when it finishes the agent continues where it left off in Order Management."

**Why it happens:** Assistants model transitions as function calls with a return.

**Correct pattern:** Transitions are one way. Add an explicit transition back, and store progress in variables, because returning starts the target subagent from its beginning (Agentforce Developer Guide, Utils reference).

## Anti-Pattern 8: Attaching Standard Actions to the Escalation Topic

**What the LLM generates:** "Add Get Record Details to the Escalation topic so the agent can look up the account before transferring."

**Why it happens:** Standard actions are ready-made and save build time.

**Correct pattern:** Use custom actions with a narrow field list. The Generative AI guide says standard actions have broad data access not intended for external use cases and should not be associated with the Escalation topic.

## Anti-Pattern 9: Deactivating the Agent as the Emergency Handoff

**What the LLM generates:** "If the agent misbehaves, deactivate it and conversations will go to your reps."

**Why it happens:** Deactivation sounds like a clean off switch.

**Correct pattern:** Deactivation interrupts open conversations, sends the system error message, and routes no one. Prepare an emergency routing change on the channel instead.
