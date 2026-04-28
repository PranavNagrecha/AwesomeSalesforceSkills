---
name: agent-rate-limit-strategy
description: "Control LLM spend and Apex governor exposure for high-traffic Agentforce agents via per-user token budgets and graceful fallback. NOT for API rate-limiting of REST endpoints."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Operational Excellence
triggers:
  - "agent token budget blown"
  - "one user drives the whole agent quota"
  - "graceful fallback when agent is over limit"
  - "rate-limit agentforce per user"
tags:
  - agentforce
  - rate-limiting
  - cost
  - platform-events
inputs:
  - "Traffic forecast"
  - "per-tenant/per-user quotas"
  - "fallback UX"
outputs:
  - "Rate-limit policy CMDT"
  - "fallback messaging"
  - "observability dashboard"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Agent Rate Limit Strategy

Agentforce exposes internal LLM quotas indirectly — you hit them as platform 503s with no forward signal. This skill builds a client-side budget gate in front of the agent: per-user token ledger, CMDT-driven thresholds, and a graceful fallback when the budget is exhausted.

## Recommended Workflow

1. Define budget: tokens/user/hour, tokens/tenant/day. Persist in `Agent_Rate_Limit__mdt` per-persona.
2. In the channel entry point (LWC wrapper or Connect API), call a `BudgetService.checkAndConsume(userId, estTokens)` before dispatching to the agent.
3. Log consumption via Platform Event `Agent_Token_Consumed__e` — the subscriber rolls into a `User_Token_Ledger__c` aggregate.
4. When the budget is exhausted, render the fallback UX (human handoff / retry-after message) instead of calling the agent.
5. Dashboard: p50/p95 consumption per persona, budget exhaustion count, tokens/turn — page SRE when exhaustion >1%.

## Key Considerations

- Estimate tokens conservatively from input length (`chars/4`) before the call; reconcile after.
- Ledger is eventually consistent — use the Platform Event pattern, not synchronous DML.
- Fallback UX must be pre-approved; a generic 'try again later' erodes trust.

## Worked Examples (see `references/examples.md`)

- *Budget service sketch* — 100 Service reps use agent summarization; one rep loops a bad input 500x.
- *Graceful fallback* — Budget exhausted mid-conversation.

## Common Gotchas (see `references/gotchas.md`)

- **Estimating tokens from chars misses long RAG context** — Estimate says 500 tokens; reality is 5000 after grounding.
- **Platform Event volume limits** — High-traffic agent saturates your 24h PE quota.
- **Ledger bucket skew** — Timezone boundary resets at midnight UTC, users see it mid-afternoon locally.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Trusting Agentforce to rate-limit for you — it only fails loudly on hard limits.
- Hard-coded tokens/minute without per-persona CMDT — cannot respond to traffic shifts.
- Synchronous ledger DML per turn — blows DML limits.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
