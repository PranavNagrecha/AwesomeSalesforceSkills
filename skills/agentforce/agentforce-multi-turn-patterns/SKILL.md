---
name: agentforce-multi-turn-patterns
description: "Design Agentforce conversations that span multiple turns without losing context: session variable scoping, conversation memory, clarifying-question patterns, topic-to-topic (now subagent) handoff, and the right abstractions for accumulating state across turns. NOT for deciding the topic boundaries themselves or out-of-scope behavior — use agentforce/agent-topic-design. NOT for single-turn agent actions and their input/output contracts — use agentforce/agent-actions."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
  - Security
tags:
  - agentforce
  - multi-turn
  - conversation-state
  - topics
  - session-variables
  - clarifying-questions
triggers:
  - "agentforce multi-turn conversation"
  - "agent session variable state"
  - "ask clarifying question agent"
  - "topic to topic handoff"
  - "conversation memory agentforce"
  - "agent remembers previous turn"
  - "keep my agentforce agent from asking for the order number again two turns later"
inputs:
  - Conversation design goals (what info must accumulate across turns)
  - Topic catalog for the agent
  - Expected turn count before task completion
  - Escalation criteria (when to hand off to human)
outputs:
  - Session-variable schema with scopes documented
  - Topic design with entry/exit conditions per topic
  - Clarifying-question patterns per ambiguous input class
  - Hand-off criteria and escalation flow
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Agentforce Multi-Turn Conversation Patterns

> **Terminology.** This skill leads with *subagent* because that is the current
> product term — beginning in April 2026, agent topics are called subagents,
> with no change to functionality. It deliberately keeps *topic* in metadata and
> API names, in transcript examples that name a configured entity, and in search
> keywords — those did not change, and readers arriving with the older
> vocabulary still need to find this skill.

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Which facts must the agent still know several turns later, and which must be exact? | Agent Script variables "let agents deterministically remember information across conversation turns"; the guide recommends them over LLM context memory for state. | A variable list with type, default, and description for each fact. | Exact values (order numbers, dates) survive long conversations instead of being paraphrased. |
| Is this an Agent Script agent or an Agentforce (Default) employee agent? | Agentforce (Default) uses only the most recent six turns as context, and its sessions are tied to one browser tab; Agent Script agents keep variables for the session. | The agent type and channel, which decides where state can live. | The memory design matches the runtime instead of assuming one that does not apply. |
| Which values come from the channel rather than the user? | Linked variables read sources such as `@MessagingSession.Id` or `@MessagingEndUser.ContactId`; they cannot have defaults and cannot be set by the agent. | A list of channel-sourced values and their source namespace. | Identity and session context are read from the channel, not re-asked. |
| What resets when the user corrects an earlier answer or switches subagent? | Variables are agent-wide (all subagents can access them), and transitions are one way, so stale values follow the user unless they are reset. | A dependency map: which variables to clear when another changes. | Corrections cascade cleanly and do not produce records built from mixed answers. |
| When does the conversation leave the agent, and what goes with it? | `@utils.escalate` needs an active Omni-Channel connection with outbound route settings; `@utils.end_session` ends the conversation immediately. | Escalation triggers, the route, and the context to collect first. | Handoffs reach a person who can see what the agent already learned. |
| How will multi-turn behavior be tested? | `AiEvaluationDefinition` test cases accept `conversationHistory` inputs, so an utterance can be tested in the middle of a conversation. | A set of transcripts with expected subagents and actions per turn. | Prompt or script changes are checked against real multi-turn paths before release. |

## Core concept — conversation state lives in three places

Agentforce keeps conversation state in three distinct stores. Design fails when authors conflate them.

| Store | Scope | Persistence | When to use |
|---|---|---|---|
| **LLM context window** | Conversation history (Agentforce (Default): the most recent six turns, per the Generative AI guide; Agent Script: the guide says the LLM remembers the entire conversation history) | Not deterministic; the model interprets it | Implicit; handled by the model |
| **Session variables** (Agent Script `variables` block) | Agent-wide: every subagent can read and set them | Until the session ends | Facts the user states that future turns need, action outputs used in conditions |
| **Platform data** (Account, Case, custom objects, Data Cloud) | Forever | Durable | Facts that outlive the session — user preferences, transaction logs |

Rules:
- Never rely on the LLM context window alone to remember multi-turn facts. Agentforce (Default) keeps only six turns, and even where history is kept, the model interprets it rather than storing exact values.
- Never use session variables for data that must outlive the conversation.
- Never write platform data on every turn when a session variable would do.

## Recommended Workflow

1. **Inventory the turn-to-turn facts.** List every piece of information the agent must know in turn N that was given in turn N-1 or earlier. This is your session-variable schema.
2. **Decide the scope of each fact.** Cross-subagent (any Agent Script variable is agent-wide), within one subagent (an agent-wide variable you reset on exit), or cross-session (platform data)? Write the result as a `variables` block; a complete example is in `references/metadata-examples.md`.
3. **Design subagents around user intent shifts, not UI screens.** A subagent boundary should match a meaningful change in what the user is trying to accomplish.
4. **Plan clarifying-question triggers.** For every ambiguous input class, decide: can the agent proceed with a plausible assumption and verify, or does it need to ask?
5. **Wire the subagent-to-subagent handoff.** When a subagent exits, which session variables survive? Which are reset?
6. **Plan escalation.** After how many failed turns does the agent hand off to a human? Which signals count as "failed"?
7. **Build an eval set of 10+ multi-turn transcripts** covering happy paths, ambiguity, and escalation. Run before every prompt change (see `agentforce-eval-harness`).

## Key patterns

### Pattern 1 — Accumulating form fill

User task: file a return request. Agent must collect: order number, item, reason, refund method.

```
Turn 1:
  User: "I want to return my order."
  Agent intent: Start_Return topic.
  Action: ask "What's your order number?"

Turn 2:
  User: "Order #A7842."
  Agent sets: session.orderNumber = 'A7842'.
  Action: look up order → ask "Which item?"

Turn 3:
  User: "The blue scarf."
  Agent sets: session.itemId = <matched-item-id>.
  Action: ask "What's the reason?"
```

Key design:
- Each turn stores exactly one fact in a session variable.
- The next turn's prompt incorporates all accumulated facts: "To confirm, you're returning item X from order Y for reason Z."
- If the user changes their mind mid-flow ("wait, actually it was the red scarf"), the agent updates the variable and re-asks the downstream question.

### Pattern 2 — Cross-subagent memory

User switches from Support (Case subagent) to Sales (Upgrade subagent) mid-session.

```
Turn 1-3: Support topic resolves billing question.
  session.verifiedAccountId = '001xxx' (set by Support topic)

Turn 4:
  User: "Also, I want to upgrade to the premium plan."
  Agent: Upgrade topic begins.

Turn 5:
  Agent: instead of asking "which account?", uses session.verifiedAccountId
  directly. No re-verification.
```

Key design:
- In Agent Script every variable is defined once in the `variables` block, and all subagents can access it ("Variables (Custom and Linked)", Agentforce Developer Guide). `verified_account_id` is therefore visible to the Upgrade subagent without extra setup.
- There is no subagent-private variable scope. Earlier versions of this skill said Support's internal variables are subagent-scoped and vanish on exit; they do not. If `case_id` must not influence the Upgrade subagent, reset it explicitly (`set @variables.case_id = ""`) when Support finishes.
- Name and describe each variable so its owner and lifetime are obvious, because any subagent can change a `mutable` variable.

### Pattern 3 — Clarifying question with fallback

User input is ambiguous. Agent decides: ask or assume-and-verify.

```
User: "Cancel my subscription."

Path A — Ask:
  Agent (if user has ≥ 2 active subscriptions):
    "You have two active subscriptions — Pro ($49/mo) and Enterprise ($199/mo). Which one?"

Path B — Assume-and-verify:
  Agent (if user has 1 active subscription):
    "I see your Pro subscription ($49/mo, renews March 15). Proceed with cancellation?"
```

Key design:
- The assume-and-verify path is always paired with a confirmation step — never act on an assumption without explicit user acknowledgment.
- If the user hesitates or says "wait" / "no", the agent backs up to the ambiguity and asks.

### Pattern 4 — Failure-bounded escalation

```
Turn 1: User asks a question the agent doesn't understand. Agent asks for clarification.
Turn 2: User rephrases. Agent still doesn't understand.
Turn 3: Agent says "Let me connect you with a specialist." Hands off to a human queue.
```

Key design:
- Two-strike rule: two consecutive non-understanding turns trigger hand-off.
- Hand-off uses `@utils.escalate`, which needs an active Omni-Channel connection defined in the agent's connection block with `outbound_route_type` and `outbound_route_name` (Agent Script Reference: Utils).
- Hand-off preserves the full conversation transcript for the human agent, and session variables accumulated to this point are passed to the human via the hand-off payload. UNVERIFIED (2026-10-03): what the receiving rep sees depends on the Omni-Channel flow; no source read for this revision describes the payload.
- The agent does NOT keep probing after escalation — the human owns the interaction.

## Bulk safety

Agent conversations are inherently one-user-one-conversation. Bulk safety here is about:
- **Concurrent conversations from the same user** — two browser tabs, two devices. Use `UserId + sessionId` keys, never `UserId` alone.
- **Agent-to-tool fan-out** — a single turn may invoke multiple Apex or Flow actions. Each action must be bulk-safe independently (see `skills/agentforce/custom-agent-actions-apex`).
- **Session-variable-array growth** — if a session accumulates a list (e.g., items the user wants to buy), bound the list size. A 10,000-element list will exceed LLM context budgets.

## Error handling

- **Tool failure (Apex action throws):** the agent should detect the failure, inform the user in natural language ("I had trouble looking that up"), and offer alternatives (retry, escalate, skip).
- **LLM refusal:** the agent declines to answer (policy). Ensure the refusal is graceful and offers an alternative — see `agentforce-refusal-patterns` if added to the library.
- **Ambiguous input after N turns:** escalate to human.
- **Session timeout:** save critical state to platform data BEFORE the timeout; when the user returns, rehydrate.

## Well-Architected mapping

- **Reliability** — explicit state stores + bounded list sizes prevent context-window overflow failures. Two-strike escalation prevents infinite clarification loops.
- **User Experience** — the quality of multi-turn conversations is the difference between an agent users trust and one they avoid. Clarifying vs assume-and-verify must be tuned per task.
- **Security** — session variables may hold PII. Scope discipline prevents PII from leaking across subagents; platform-data writes must respect FLS.

## Gotchas

See `references/gotchas.md`.

## Testing

Multi-turn conversations need **transcript-level evals**, not single-turn unit tests. See `skills/agentforce/agentforce-eval-harness` for the harness + fixture format. Salesforce's own test definition (`AiEvaluationDefinition`) supports this directly: a test case can include `conversationHistory` entries (role, message, subagent for agent turns, index) before the utterance under test, and context variables are immutable after the session starts except `EndUserLanguage` (Agentforce Developer Guide, Build Tests in Metadata API). Minimum coverage:

- Happy path for each subagent (linear flow, all variables captured correctly).
- Subagent switch mid-conversation (state handoff correct).
- Ambiguity requiring clarification.
- Two-strike escalation.
- User correction mid-flow ("actually, change that to...").

## Official Sources Used

- Salesforce Help — Agentforce Topics and Conversations: https://help.salesforce.com/s/articleView?id=sf.copilot_topics.htm
- Salesforce Help — Session Variables for Agents: https://help.salesforce.com/s/articleView?id=sf.copilot_variables.htm
- Salesforce Architects — Conversational AI Patterns: https://architect.salesforce.com/
- Salesforce Developer — Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/
- Agentforce Developer Guide, Agent Script Reference: Variables (Custom and Linked): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-variables.html
- Agentforce Developer Guide, Agent Script Reference: Utils: https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-utils.html
- Agentforce Developer Guide, Build Tests in Metadata API: https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-build-tests.html
- Full list with the claim each source supports: `references/well-architected.md`
