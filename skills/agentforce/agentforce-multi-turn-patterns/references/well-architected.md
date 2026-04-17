# Well-Architected Notes — Agentforce Multi-Turn Patterns

## Relevant Pillars

- **Reliability** — Multi-turn agents fail silently when context truncates, when a variable is stale after correction, or when an escalation loses context. Explicit session-variable state + cascade resets + bounded escalation are the load-bearing structures that keep conversations recoverable under edge cases.
- **User Experience** — The difference between an agent users return to and one they abandon is almost entirely multi-turn design. Asking one question per ambiguity, batching clarifications, and preserving identity across topics are what make conversations feel competent.
- **Security** — Session variables may hold PII (account IDs, phone numbers, addresses). Scope discipline prevents PII from leaking cross-topic. Escalation handoff payloads must redact PII before logging.

## Architectural Tradeoffs

### Session variables vs platform data

| Approach | Pro | Con |
|---|---|---|
| Session variables | Fast, in-memory, no DML | Lost on session timeout |
| Platform data (`Agent_Conversation__c`) | Durable across sessions | DML per significant turn; storage cost |

Rule of thumb: session variables are the default; promote to platform data only for:
- Long-running workflows (returns, multi-day tickets)
- Resumable conversations (user abandons + returns)
- Regulatory audit trails

### Synchronous clarification vs assume-and-verify

| Approach | Pro | Con |
|---|---|---|
| Synchronous clarifying question | Unambiguous; user feels heard | Adds turns; abandon rate rises with turn count |
| Assume-and-verify | Fewer turns; feels snappy | Wrong assumption feels pushy or presumptuous |

Rule: if the plausible-assumption success rate is > 90%, use assume-and-verify with confirmation. Below 90%, ask.

### Topic granularity

Topics too narrow: agent loses conversation coherence when user drifts slightly.
Topics too broad: one topic ends up owning disparate workflows and its description can't discriminate well from neighbors.

Rule: topic per coherent user-intent family (e.g., "Returns", "Billing", "Technical Support"), not per specific task (e.g., "Return_Shirt" is too narrow).

## Anti-Patterns

1. **LLM context as memory** — Relying on the rolling turn history to remember early facts. Facts fall off as context fills. Fix: explicit session variables.

2. **Monolithic `session.context` blob** — One JSON string holding everything. Loses type safety, can't scope-reset individual facts. Fix: one variable per atomic fact.

3. **Infinite clarification loops** — Re-asking indefinitely when user input remains unparseable. Fix: two-strike rule with escalation.

4. **Context-free escalation** — Transferring to a human with just the latest message. Forces the human to restart from zero. Fix: escalation payload with full transcript + redacted session state.

5. **Per-topic identity verification** — Asking for account verification at every topic boundary. Users feel the agent doesn't trust them. Fix: cross-topic identity with expiry.

## Official Sources Used

- Salesforce Help — Agentforce Topics and Conversations: https://help.salesforce.com/s/articleView?id=sf.copilot_topics.htm
- Salesforce Help — Session Variables for Agents: https://help.salesforce.com/s/articleView?id=sf.copilot_variables.htm
- Salesforce Developer — Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/
- Salesforce Architects — Well-Architected Framework: https://architect.salesforce.com/design/architecture-framework/well-architected
