---
name: agentforce-multi-turn-patterns
description: "Design Agentforce conversations that span multiple turns without losing context: session variable scoping, conversation memory, clarifying-question patterns, topic-to-topic handoff, and the right abstractions for accumulating state across turns. NOT for single-turn agent actions (use agent-actions). NOT for channel-specific conversation UX (use agent-channel-deployment)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Agentforce Multi-Turn Conversation Patterns

## When to use this skill

Activate when:

- You're designing an agent that needs to remember what the user said in a prior turn (order number, account context, preferences).
- The agent has more than one topic and conversations routinely cross topic boundaries mid-session.
- You're seeing "the agent forgot what I just said" or "it asked me the same question twice" in test transcripts.
- You need to decide between storing state in session variables vs a scratch Data Cloud record vs a conversation log object.
- You're modeling a guided task (multi-step form fill, troubleshooting tree, return authorization) in Agentforce.

Do NOT use this skill for:
- Single-turn transactional actions (use `skills/agentforce/agent-actions`).
- Channel-specific rendering (use `skills/agentforce/agent-channel-deployment`).
- Initial agent bootstrapping (use `skills/agentforce/agentforce-agent-creation`).

## Core concept — conversation state lives in three places

Agentforce keeps conversation state in three distinct stores. Design fails when authors conflate them.

| Store | Scope | Persistence | When to use |
|---|---|---|---|
| **LLM context window** | Current turn (+ recent turns) | Ephemeral — falls off as conversation grows | Implicit; handled by the model |
| **Session variables** | Current conversation session | Until session ends (timeout or user closes) | Facts the user states that future turns need |
| **Platform data** (Account, Case, custom objects, Data Cloud) | Forever | Durable | Facts that outlive the session — user preferences, transaction logs |

Rules:
- Never rely on the LLM context window alone to remember multi-turn facts. The window truncates silently.
- Never use session variables for data that must outlive the conversation.
- Never write platform data on every turn when a session variable would do.

## Recommended Workflow

1. **Inventory the turn-to-turn facts.** List every piece of information the agent must know in turn N that was given in turn N-1 or earlier. This is your session-variable schema.
2. **Decide the scope of each fact.** Within-topic-only, cross-topic, cross-session? Each scope maps to a different store.
3. **Design topics around user intent shifts, not UI screens.** A topic boundary should match a meaningful change in what the user is trying to accomplish.
4. **Plan clarifying-question triggers.** For every ambiguous input class, decide: can the agent proceed with a plausible assumption and verify, or does it need to ask?
5. **Wire the topic-to-topic handoff.** When a topic exits, which session variables survive? Which are reset?
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

### Pattern 2 — Cross-topic memory

User switches from Support (Case topic) to Sales (Upgrade topic) mid-session.

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
- The `verifiedAccountId` session variable has **cross-topic scope**.
- The Support topic's internal variables (`caseId`, `resolutionStatus`) are **topic-scoped** and don't survive the topic exit.
- Declaring scope explicitly at variable-creation time prevents information leaks.

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
- Hand-off preserves the full conversation transcript for the human agent.
- Session variables accumulated to this point are passed to the human via the hand-off payload.
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
- **Security** — session variables may hold PII. Scope discipline prevents PII from leaking across topics; platform-data writes must respect FLS.

## Gotchas

See `references/gotchas.md`.

## Testing

Multi-turn conversations need **transcript-level evals**, not single-turn unit tests. See `skills/agentforce/agentforce-eval-harness` for the harness + fixture format. Minimum coverage:

- Happy path for each topic (linear flow, all variables captured correctly).
- Topic switch mid-conversation (state handoff correct).
- Ambiguity requiring clarification.
- Two-strike escalation.
- User correction mid-flow ("actually, change that to...").

## Official Sources Used

- Salesforce Help — Agentforce Topics and Conversations: https://help.salesforce.com/s/articleView?id=sf.copilot_topics.htm
- Salesforce Help — Session Variables for Agents: https://help.salesforce.com/s/articleView?id=sf.copilot_variables.htm
- Salesforce Architects — Conversational AI Patterns: https://architect.salesforce.com/
- Salesforce Developer — Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/
