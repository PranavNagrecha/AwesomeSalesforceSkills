---
name: agentforce-cost-optimization
description: "Use when Agentforce run costs are climbing, you need to forecast scale, or you want to reduce tokens per conversation without hurting quality. Covers topic design impact on cost, prompt/template reuse, grounding size discipline, caching, and model-tier selection. Triggers: 'agentforce cost', 'tokens per conversation too high', 'reduce agentforce runs spend', 'forecast agentforce scale cost', 'einstein trust layer tokens'. NOT for general LLM pricing strategy outside Salesforce."
category: agentforce
salesforce-version: "Spring '26+"
well-architected-pillars:
  - Performance
  - Operational Excellence
  - Reliability
triggers:
  - "reduce agentforce token spend"
  - "cost per agent conversation forecast"
  - "agentforce trust layer token count"
  - "why are agentforce runs expensive"
  - "model tier selection agentforce"
tags:
  - agentforce
  - cost-optimization
  - tokens
  - grounding
  - model-tier
inputs:
  - "current token usage per conversation"
  - "topic and prompt template inventory"
  - "grounding source sizes"
outputs:
  - "cost-per-conversation model"
  - "token-reduction plan"
  - "model-tier recommendation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Agentforce Cost Optimization

Agentforce cost looks like "we'll just pay per run" right up until volume meets reality. A customer-service agent handling 200,000 conversations/month can consume 10× the tokens of a well-tuned version of the same agent — same quality, same topics, different token discipline. The cost drivers are predictable: topic instruction length, prompt template verbosity, grounding payload size, tool-call round-trips, and model tier. None of these are free to change, but they all respond to focused work.

The job is to measure first, then optimize the top three contributors. Most orgs find that topic instructions and grounding dominate — often 60-80% of tokens per conversation. Once those are disciplined, the remaining optimizations (template reuse, model-tier selection) become viable.

---

## Before Starting

- Pull 7 days of Agentforce runs; compute average and p95 token counts per conversation.
- Inventory topics, prompt templates, and grounding sources.
- Confirm model tier currently in use and any rate-limit headroom.
- Confirm business tolerance for quality-vs-cost tradeoffs.

## Core Concepts

### What Tokens Are You Paying For?

Every conversation pays for:

1. **System prompt** — the framework-level Agentforce prompt.
2. **Topic instructions** — active topic's instructions injected verbatim.
3. **Prompt template** — any custom template rendered per turn.
4. **Grounding** — retrieved content from Data Cloud, Knowledge, or explicit variables.
5. **Conversation history** — full turn history on each call.
6. **Tool output** — action results returned into context.

### The 80/20 Rule

For most agents, topic instructions + grounding = 60-80% of token spend. Conversation history grows linearly in long sessions. Tool output is lumpy but occasionally large (SOQL result sets dumped raw into context).

### Reducing Topic Instruction Tokens

- Delete department-name preamble ("As a customer service agent working for Acme Insurance...").
- Collapse redundant examples; 2 good examples outperform 10 mediocre ones.
- Externalize static policy ("always use formal English") into the system prompt instead of per-topic.

### Reducing Grounding Tokens

- Retrieve k=3, not k=10, unless evaluation shows quality improves.
- Chunk sizes: 300-500 tokens usually beats 1000-2000.
- Reranker before final injection when using Data Cloud retrievers.
- Strip boilerplate (legal footers, headers) from Knowledge articles before indexing.

### Conversation History Discipline

Long sessions inflate every turn's token count. Patterns:
- Summarize older turns ("Summary of first 5 turns: …") rather than sending verbatim.
- Archive turns beyond a threshold; keep only the last N in active context.

### Model Tier Selection

Not every action needs the most capable model. Use tiered routing:
- Classification / intent detection → smaller model.
- Reasoning / final response → larger model.
- Tool-calling / structured output → mid-tier is often enough.

### Caching Opportunities

- Topic instructions are stable across conversations — framework should cache; you don't need to change anything unless your template is dynamic.
- Grounding retrieval can cache per query; watch freshness needs.

---

## Common Patterns

### Pattern 1: Topic Instruction Audit And Trim

Per-topic, measure instruction token count. Target 150-300 tokens per topic instruction. Trim anything above 500 without a compelling reason.

### Pattern 2: k-3 Retriever With Reranker

Retrieve 10 candidates; rerank; inject top 3. Cuts grounding tokens 70% vs retrieve-10-inject-10.

### Pattern 3: Conversation Summarization Trigger

After N turns or M tokens of history, replace older turns with a one-line summary.

### Pattern 4: Tiered Model Routing

Route classification / intent steps to a smaller model; reasoning/response to the capable model.

### Pattern 5: Tool Output Projection

When a tool returns a large payload (e.g. SOQL result), project the fields the agent actually needs instead of dumping the full response.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Token usage high, unknown contributor | Instrument and measure first | Avoid guessing |
| Topic instructions > 500 tokens | Trim (Pattern 1) | Biggest win |
| Grounding k ≥ 5 without evaluation | Reduce k + rerank (Pattern 2) | Second biggest win |
| Long conversations | Summarize (Pattern 3) | Linear savings per turn |
| Classification step using largest model | Switch to smaller tier (Pattern 4) | Cheap wins |
| Tool returns wide records | Project fields (Pattern 5) | Eliminates silent waste |

## Well-Architected Pillar Mapping

- **Performance** — smaller contexts are lower latency, which compounds at scale.
- **Operational Excellence** — cost model + monitoring turns cost from surprise to dial.
- **Reliability** — tight contexts reduce distraction and improve routing quality.

## Review Checklist

- [ ] Per-conversation token metrics collected and dashboarded.
- [ ] Top 3 token contributors identified per agent.
- [ ] Topic instruction length audited.
- [ ] Grounding k and chunk size justified.
- [ ] Long-conversation strategy exists.
- [ ] Model tier routing considered.
- [ ] Tool output projection in place.

## Recommended Workflow

1. Measure — 7 days of run data broken down by token source.
2. Identify top 3 contributors.
3. Optimize topic instructions first.
4. Optimize grounding second.
5. Add conversation summarization if sessions are long.
6. Apply tier routing where quality allows.
7. Re-measure; document cost savings.

---

## Salesforce-Specific Gotchas

1. Trust Layer adds tokens — masking, citation, guardrails all add context weight.
2. Grounding sources can include large boilerplate (Knowledge article footers); index selectively.
3. Tool output is counted even if the agent ignores it.
4. Managed topics may have opaque instruction length; audit via runtime logs.
5. Switching model tier changes quality — do not do this without A/B evaluation.

## Proactive Triggers

- Topic instruction > 500 tokens → Flag High.
- Retriever k ≥ 10 without reranker → Flag High.
- Average conversation > 20 turns with no summarization → Flag Medium.
- Classification step on flagship model → Flag Medium.
- Token growth > 15%/month without volume growth → Flag High.

## Output Artifacts

| Artifact | Description |
|---|---|
| Cost model | Tokens per conversation by contributor |
| Optimization plan | Prioritized trim list with expected savings |
| Tier routing design | Step → model mapping |

## Related Skills

- `agentforce/agent-topic-design` — topic structure quality.
- `agentforce/prompt-builder-templates` — prompt template hygiene.
- `agentforce/data-cloud-grounding-for-agentforce` — grounding retrieval.
- `agentforce/agentforce-observability` — measurement infrastructure.
