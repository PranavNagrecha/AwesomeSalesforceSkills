---
name: agent-metric-dashboards
description: "Observability for Agentforce: adoption, deflection, latency, cost, quality. NOT for agent evaluation/testing (see agentforce-eval-harness) or raw platform-event monitoring."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Performance
triggers:
  - "what is my agent deflection rate"
  - "how much does each agent conversation cost"
  - "agent latency p95"
  - "agentforce roi dashboard"
tags:
  - agentforce
  - observability
  - dashboards
  - metrics
inputs:
  - "Conversation log access"
  - "CSAT or quality signal"
outputs:
  - "Einstein Analytics / CRM Analytics dashboard"
  - "weekly rollup email"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Agent Metric Dashboards

The five agent KPIs: turns/conversation, deflection rate, mean latency, tokens/conversation (cost proxy), and quality score. This skill wires each KPI to a source and lays out the single-pane dashboard the executive reviewer needs.

## Adoption Signals

Every production agent after the first week; monthly executive review.

## Recommended Workflow

1. Source adoption + turns from `Conversation__c` (or equivalent). Deflection = conversations ending without a `Case` escalation divided by total conversations.
2. Source latency from `Conversation_Turn__c.duration_ms__c`. Source tokens from the PE ledger.
3. Source quality from a post-conversation survey (CSAT) or LLM-as-judge score over a sampled cohort.
4. Build a CRM Analytics lens per KPI with the prior 8 weeks; assemble into a single dashboard.
5. Weekly email digest: current vs. prior week for each KPI; page on >10% deflection drop or >20% latency spike.

## Key Considerations

- Deflection is only meaningful vs. a baseline from before agent deployment.
- LLM-as-judge must be calibrated against human labels quarterly.
- Cost proxy (tokens) drifts when the model changes; track separately from raw latency.

## Worked Examples (see `references/examples.md`)

- *Deflection with baseline* — Service org with 40% pre-agent escalation rate.
- *Tokens/conversation trend* — Costs spike after a topic-instruction rewrite.

## Common Gotchas (see `references/gotchas.md`)

- **CSAT response bias** — Only frustrated users answer the survey — CSAT looks terrible.
- **Deflection = 'user gave up'** — No escalation because user closed the browser in frustration.
- **Cost metric without model version** — Cost/conversation changes overnight due to model upgrade.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Single-number CSAT with no context.
- Deflection without a baseline — reports vanity metrics.
- LLM-as-judge never calibrated — grades itself.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
