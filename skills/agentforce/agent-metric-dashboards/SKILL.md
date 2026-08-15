---
name: agent-metric-dashboards
description: "Build the executive KPI dashboard for Agentforce: adoption, deflection, latency, cost, quality — KPI definitions, data sources, CRM Analytics lenses, alert thresholds. NOT for the platform's own session tracing, Agent Analytics and health monitoring — use agentforce/agentforce-observability. NOT for scoring agent answer quality offline — use agentforce/agentforce-eval-harness."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Agent Metric Dashboards

The five agent KPIs: sessions and turns per session, deflection, latency
percentiles, reasoning intensity (the observable cost driver), and quality. This
skill wires each to a **real** source and lays out the single-pane dashboard an
executive reviewer can read without being misled.

## The Prerequisite That Gates Everything

Agentforce Session Tracing must be enabled — Setup → Einstein Audit, Analytics,
and Monitoring Setup → Agentforce Session Tracing plus the Session Tracing Data
Model — **before** the conversations you want to measure. Analytics appear only
for conversations occurring after setup; there is no backfill. Readers need the
Data Cloud User permission set or the dashboard is empty for them.

This makes dashboard enablement a row on the go-live checklist
(`agentforce/agent-deployment-checklist`), not an analytics backlog item.

## Where The Numbers Actually Come From

| KPI | Source | Notes |
|---|---|---|
| Sessions | `AIAgentSession` (Data Cloud DMO) | Also reported directly by Agentforce Observability |
| Turns per session | `AIAgentInteraction` ÷ `AIAgentSession` | Turn-by-turn detail |
| Deflected sessions, average latency | Agentforce Observability | Reported as first-class insights |
| Escalation rate | Action data on `AIAgentInteraction` | Sessions whose action sequence includes the transfer action |
| Action failure rate | `AIAgentInteractionStep` | Group by action; sort by rate, not volume |
| Quality, feedback | Session-tracing metric scores and feedback signals | Calibrate against human labels quarterly |

There is no standard `Conversation__c` and no queryable per-token cost. A spec
that names them is a data-engineering project, not a dashboard.

## Adoption Signals

Every production agent from activation onward; monthly executive review. Tracing
must be on from day zero, so this skill is consumed before launch rather than
after the first week.

## Recommended Workflow

1. Enable Session Tracing and the Session Tracing Data Model before activation;
   assign Data Cloud User to every intended reader and verify with a real one.
2. Build the volume and efficiency tiles from `AIAgentSession` and
   `AIAgentInteraction`: sessions, turns per session, LLM calls per turn, p50 and
   p95 latency. Split agent latency from action latency — different owners,
   different fixes.
3. Make deflection causal or rename it. Randomise a holdout arm at the routing
   layer and report `(rate_control − rate_treatment) / rate_control` with both
   arm sizes; where no holdout is possible, label the tile "Escalation rate (no
   control arm)".
4. Pair every proxy with its confound **on the same tile**: deflection with
   72-hour repeat-contact rate, CSAT with `n` and response rate, aggregate with
   the per-subagent breakdown sorted by rate (*subagent* is the April 2026
   rename of *topic*; the metadata names did not change).
5. Report cost as drivers (sessions × turns/session × LLM-calls/turn) and take
   absolute cost from Salesforce consumption reporting. Reconcile monthly; never
   compute a currency figure from org data alone.
6. Annotate every trend with agent version activations, prompt template
   activations, and model version changes — model versions move without a
   deployment on your side.
7. Derive alert thresholds from four weeks of observed distribution, give each
   one a named owner, and review at four weeks: did it fire, was every firing
   actionable.

## Key Considerations

- Deflection **rises when the agent gets worse** — a user who abandons looks
  identical to one who was helped. It is never a solo KPI.
- Mean latency hides the tail that drives abandonment. Report p50 and p95.
- A quality score whose agreement with human judgement is unmeasured is an
  unmonitored dependency of every decision made from it.
- The OTel export (`GET /services/data/v66.0/einstein/audit/otel/{session-id}`)
  is one session per call, limited to the previous 72 hours, and Beta. Sample
  rather than exporting everything, and alert on exporter *lag*.

## Worked Examples (see `references/examples.md`)

- *Deflection with baseline* — Service org with 40% pre-agent escalation rate.
- *Tokens/conversation trend* — Costs spike after a subagent-instruction rewrite.

## Common Gotchas (see `references/gotchas.md`)

- **CSAT response bias** — Only frustrated users answer the survey — CSAT looks terrible.
- **Deflection = 'user gave up'** — No escalation because user closed the browser in frustration.
- **Cost metric without model version** — Cost/conversation changes overnight due to model upgrade.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Single-number CSAT with no context.
- Deflection without a baseline — reports vanity metrics.
- LLM-as-judge never calibrated — grades itself.

## Official Sources Used

- About Agentforce Session Tracing — https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_about.htm&type=5
- Set Up Agentforce Session Tracing — https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_setup.htm&type=5
- Data Model for Agentforce Session Tracing — https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_data_model.htm&type=5
- Export Agentforce Session Tracing Data (OTel API) — https://developer.salesforce.com/docs/ai/agentforce/guide/otel-api.html
- Data Model and Calculated Fields for Agent Analytics — https://help.salesforce.com/s/articleView?id=ai.generative_ai_agent_analytics_data_model.htm&type=5
