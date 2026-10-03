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
  - "build an Agentforce dashboard for adoption and deflection"
  - "query agent session data in Data Cloud"
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
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Agent Metric Dashboards

The five agent KPIs: sessions and turns per session, deflection, latency
percentiles, reasoning intensity (the observable cost driver), and quality. This
skill wires each to a **real** source and lays out the single-pane dashboard an
executive reviewer can read without being misled.

## The Prerequisite That Gates Everything

Agentforce Session Tracing must be enabled (Setup, Einstein Audit, Analytics,
and Monitoring Setup, Agentforce Session Tracing) **before** the conversations you
want to measure. UNVERIFIED (2026-10-03): the earlier statements, sourced to Help
articles that do not fetch, that analytics never backfill and that readers need
the "Data Cloud User" permission set; plan as if both are true. Agent Analytics
runs on Data Cloud, consumes credits, and is not available on Data Cloud One
companion orgs (Generative AI guide, Agentforce Analytics).

This makes dashboard enablement a row on the go-live checklist
(`agentforce/agent-deployment-checklist`), not an analytics backlog item.

## Questions to Ask Before Configuring

Ask these before building a tile. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "When was session tracing turned on, and is it on in every org that matters?" | The dashboard has no history before tracing (Gotcha 1) | A data start date and a go-live checklist row | A trend nobody misreads as a launch date |
| "Is there a control arm, or only a before-and-after?" | Deflection without a holdout measures the world (Gotchas 3, 4, 5) | A holdout design or an honest tile label | Causal claims only where they are earned |
| "What does cost mean here: tokens, credits or currency?" | Token counts are queryable from the usage DMO; currency is not (Gotcha 7) | Driver tiles plus a monthly reconciliation with consumption reporting | A cost view that is true and actionable |
| "Who reads the dashboard, and do they have Data Cloud access and folder access?" | Readers without access see nothing (Gotcha 2) | A permission set group and a shared folder | A dashboard that works for its audience on day one |
| "Which events must annotate the trends?" | Model and version changes move metrics silently (Gotcha 8) | Agent activations, prompt activations, model changes as series | Step changes explained at a glance |
| "Who owns each alert, and how was its threshold chosen?" | Untuned alerts get muted (Gotcha 12) | An owner and a distribution-based threshold per alert | Alerts that are still read in month four |

## Where The Numbers Actually Come From

| KPI | Source (DMO label, object API name) | Notes |
|---|---|---|
| Sessions | AI Agent Session, `ssot__AiAgentSession__dlm` | Also in the standard Total Session report |
| Turns per session | AI Agent Interaction, `ssot__AiAgentInteraction__dlm` ÷ sessions | `ssot__TopicApiName__c` gives the subagent per turn |
| Deflected and escalated sessions | `ssot__AiAgentSessionEndType__c` on the session (resolved, escalated, deflected, other) | Also the standard Deflection Session report |
| Average latency | Standard Latency report | Compute p50 and p95 from interaction timestamps yourself |
| Action failure rate, LLM calls per turn | AI Agent Interaction Step, `ssot__AiAgentInteractionStep__dlm` | Step types UserInputStep, LLMExecutionStep, FunctionStep; group by action, sort by rate |
| Tokens | Ai Agent Generative Ai Usage, `AiAgentGenerativeAiUsage_std__dlm` (Spring '26 and later) | Token counts per request; no currency |
| Quality, feedback | Session-tracing metric scores and feedback signals | Calibrate against human labels quarterly |

There is no standard `Conversation__c`. A spec that names it is a data-engineering
project, not a dashboard. Token counts are queryable from the usage DMO; a
currency rate is not in org data (this corrects the earlier "no queryable
per-token cost"). Object and field names come from the Data Cloud DMO reference;
`references/metadata-examples.md` has a deployable calculated insight and the
driver queries.

## Adoption Signals

Every production agent from activation onward; monthly executive review. Tracing
must be on from day zero, so this skill is consumed before launch rather than
after the first week.

## Recommended Workflow

1. Enable Session Tracing and the Session Tracing Data Model before activation;
   assign Data Cloud User to every intended reader and verify with a real one.
2. Build the volume and efficiency tiles from `ssot__AiAgentSession__dlm`,
   `ssot__AiAgentInteraction__dlm` and `ssot__AiAgentInteractionStep__dlm`:
   sessions, turns per session, LLM calls per turn, p50 and p95 latency. Deploy
   the daily session counts as a calculated insight (`references/metadata-examples.md`). Split agent latency from action latency, different owners,
   different fixes.
3. Make deflection causal or rename it. Randomise a holdout arm at the routing
   layer and report `(rate_control − rate_treatment) / rate_control` with both
   arm sizes; where no holdout is possible, label the tile "Escalation rate (no
   control arm)".
4. Pair every proxy with its confound **on the same tile**: deflection with
   72-hour repeat-contact rate, CSAT with `n` and response rate, aggregate with
   the per-subagent breakdown sorted by rate (*subagent* is the April 2026
   rename of *topic*; the metadata names did not change).
5. Report cost as drivers (sessions × turns/session × LLM-calls/turn, plus tokens
   from `AiAgentGenerativeAiUsage_std__dlm`) and take absolute cost from
   Salesforce consumption reporting (Digital Wallet). Reconcile monthly; never
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

See `references/well-architected.md` for the sources read for this revision.
