# Well-Architected Notes — Agentforce Multi-Turn Patterns

## Relevant Pillars

- **Reliability** — Multi-turn agents fail silently when context truncates, when a variable is stale after correction, or when an escalation loses context. Explicit session-variable state + cascade resets + bounded escalation are the load-bearing structures that keep conversations recoverable under edge cases.
- **User Experience** — The difference between an agent users return to and one they abandon is almost entirely multi-turn design. Asking one question per ambiguity, batching clarifications, and preserving identity across subagents (called topics before April 2026) are what make conversations feel competent.
- **Security** — Session variables may hold PII (account IDs, phone numbers, addresses). Because variables are agent-wide, explicit resets and `filter_from_agent` on sensitive action outputs prevent PII from leaking across subagents. Escalation handoff payloads must redact PII before logging.

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

### Subagent granularity

Subagents too narrow: agent loses conversation coherence when user drifts slightly.
Subagents too broad: one subagent ends up owning disparate workflows and its description can't discriminate well from neighbors.

Rule: subagent per coherent user-intent family (e.g., "Returns", "Billing", "Technical Support"), not per specific task (e.g., "Return_Shirt" is too narrow).

## Anti-Patterns

1. **LLM context as memory** — Relying on the rolling turn history to remember early facts. Facts fall off as context fills. Fix: explicit session variables.

2. **Monolithic `session.context` blob** — One JSON string holding everything. Loses type safety, can't reset individual facts. Fix: one variable per atomic fact.

3. **Infinite clarification loops** — Re-asking indefinitely when user input remains unparseable. Fix: two-strike rule with escalation.

4. **Context-free escalation** — Transferring to a human with just the latest message. Forces the human to restart from zero. Fix: escalation payload with full transcript + redacted session state.

5. **Per-subagent identity verification** — Asking for account verification at every subagent boundary. Users feel the agent doesn't trust them. Fix: cross-subagent identity with expiry.

## Official Sources Used

Read for the 2026-10-03 revision:

- Agentforce Developer Guide, Agent Script Reference: Variables (Custom and Linked): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-variables.html. Supports agent-wide variables, types (including the deprecated `id`), linked variable sources, and `visibility`.
- Agentforce Developer Guide, Agent Script Reference: System Variables: https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-variables-system.html. Supports `user_input`, conversation history memory, `current_modality`, and the ten-file `uploaded_files` window.
- Agentforce Developer Guide, Agent Script Pattern: Using Variables Effectively: https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-patterns-variables.html. Supports slot filling and its limit to top-level action inputs.
- Agentforce Developer Guide, Agent Script Reference: Utils: https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-utils.html. Supports one-way transitions, `setVariables`, `escalate`, and `end_session`.
- Agentforce Developer Guide, Agent Script Pattern: Subagent Transitions: https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-patterns-transitions.html
- Agentforce Developer Guide, Agent Script Reference: Actions: https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-actions.html. Supports session-long memory of action outputs and `filter_from_agent`.
- Agentforce Developer Guide, Agent Script Blocks (`reset_to_initial_node`, connection block): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-blocks.html
- Agentforce Developer Guide, Agent Script Reference: Conditional Expressions: https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-expressions.html
- Agentforce Developer Guide, Build Tests in Metadata API (`conversationHistory`, context variables): https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-build-tests.html
- Quickstart Your Einstein Generative AI Solution (Generative AI guide, Spring '26), Agents Limits and Considerations for Agent Conversations: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf
- Metadata API Developer Guide (Spring '26), AiAuthoringBundle and AiEvaluationDefinition: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

Carried from earlier revisions (not re-read on 2026-10-03):

- Salesforce Help — Agentforce Topics and Conversations: https://help.salesforce.com/s/articleView?id=sf.copilot_topics.htm
- Salesforce Help — Session Variables for Agents: https://help.salesforce.com/s/articleView?id=sf.copilot_variables.htm
- Salesforce Developer — Agentforce Developer Guide (older einstein/genai path): https://developer.salesforce.com/docs/einstein/genai/guide/
- Salesforce Architects — Well-Architected Framework: https://architect.salesforce.com/design/architecture-framework/well-architected
