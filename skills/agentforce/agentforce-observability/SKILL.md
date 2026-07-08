---
name: agentforce-observability
description: "Use when monitoring Agentforce agent sessions, analyzing conversation logs, measuring deflection rates, or diagnosing agent performance issues. Triggers: 'agentforce session analytics', 'how to query agent conversation data', 'monitor agentforce agent effectiveness', 'agent deflection rate', 'utterance analysis agentforce'. NOT for Einstein Trust Layer audit logging (use einstein-trust-layer), NOT for agent topic design or guardrails (use agent-topic-design or agentforce-guardrails), NOT for LLM prompt debugging (this skill covers session metrics and conversation trace, not prompt engineering)."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I see what users are saying to my Agentforce agent"
  - "how do I measure whether my agent is deflecting cases effectively"
  - "where can I find the conversation logs for my Agentforce sessions"
  - "how do I analyze utterances and agent responses in Data Cloud"
  - "my agent keeps escalating to a human — where do I find the trace data to diagnose why"
  - "what Data Cloud objects store Agentforce session data"
  - "set up Agentforce Observability with Tableau Next analytics"
  - "export an Agentforce session trace to Splunk, Datadog, or New Relic"
  - "enable Agent Optimization to find agent knowledge gaps"
tags:
  - agentforce
  - observability
  - session-analytics
  - data-cloud
  - agent-performance
  - conversation-logs
inputs:
  - "Agentforce agent name or agent ID being monitored"
  - "Date range for session analysis"
  - "Specific metric of interest: deflection rate, session count, avg latency, escalation rate"
outputs:
  - "SOQL/SQL queries against Data Cloud session trace objects"
  - "Dashboard or report configuration for key agent performance metrics"
  - "Interpretation of session trace data to diagnose specific agent issues"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-07
---

# Agentforce Observability

Use this skill when monitoring Agentforce agent sessions in production, analyzing conversation logs stored in Data Cloud, measuring agent effectiveness (deflection rate, escalation rate, avg response latency), or diagnosing specific agent behavior issues by examining session trace data.

Agentforce Observability is a product built on the **Session Tracing Data Model** with three capability pillars: **Agent Analytics** (topic-level effectiveness metrics, surfaced through Tableau Next), **Agent Optimization** (unresolved-interaction and knowledge-gap analysis over the reasoning chain), and **Agent Health Monitoring** (near-real-time uptime/reliability signals on deployed agents). There is no single unified maturity label: Agent Analytics and Agent Optimization reached GA (Nov 2025), Agent Health Monitoring is a Spring '26 addition, and the programmatic OTel session-export API is documented as Beta. Confirm the current status of each pillar against the official docs before you rely on it.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Data Cloud (Data 360) is provisioned and connected to the org. Agentforce session data is stored in Data Cloud — it is not queryable from standard SOQL in the main org.
- Identify the agent(s) you are monitoring. Session data is queryable by agent ID or agent name.
- Enable the feature toggles in **Setup → Einstein Audit, Analytics, and Monitoring Setup**: turn on **Agentforce Session Tracing and Data Model** and **Agentforce Optimization**. Do not enable legacy Analytics versions from this page — they are superseded by the Session Tracing Data Model.
- Provision analytics access through **Tableau Next**, not CRM Analytics: assign the **Tableau Next Limited Consumer** or **Tableau Next Platform Analyst** permission set to analytics users, plus a **Data Cloud User** permission set, and set **API Enabled** on their profile. (Agent Optimization access uses the **Access Agentforce Optimization** permission set.)
- Note: the legacy Agentforce Analytics dashboard (the pre-GA one) retired **May 31, 2026** — as of this skill's date that deadline has passed, so any workflow still pointing at it is already broken and must move to the Session Tracing Data Model + Tableau Next approach.
- Be aware that session trace objects in Data Cloud use a distinct query surface (Data Cloud SQL or Tableau Next datasets), not standard SOQL.

---

## Core Concepts

### Session Trace Data Model in Data Cloud

Agentforce conversation data is stored in Data Cloud as a set of linked Data Model Objects (DMOs) under the **Data Model for Agentforce Session Tracing**. The canonical DMOs are:

| DMO | Purpose |
|---|---|
| `AIAgentSession` | One record per agent session — session-level details (agent, start/end, status, session ID that ties everything together). |
| `AIAgentSessionParticipant` | Who was associated with the session (for example the Contact, Lead, or Account). |
| `AIAgentInteraction` | Turn-by-turn interaction details for the session. |
| `AIAgentInteractionMessage` | The individual messages within an interaction (user utterance and agent response text). |
| `AIAgentInteractionStep` | The reasoning-chain steps behind an interaction — reasoning-engine executions, action invocations, and prompt/gateway inputs and outputs. |

> **DMO naming — read before running the queries below.** Earlier drafts of this skill used placeholder names (`AIAgentSession`, `…Utterance`, `…Topic`) that do **not** exist. The names above are the canonical Session Tracing DMOs. The SQL examples in this skill are illustrative of the query *shape* — confirm exact object and field/attribute names against the official "Data Model for Agentforce Session Tracing" reference (the ERD there lists every attribute) before running them in a real org.

Key metrics computable from these objects:
- **Deflection rate:** Sessions with a resolved/completed status (agent resolved without human) ÷ total sessions
- **Escalation rate:** Sessions with an escalated status ÷ total sessions
- **Avg agent latency:** Average response latency across interactions
- **Sessions by topic:** Topic-level effectiveness is surfaced primarily through **Agent Analytics** in Tableau Next rather than a standalone raw topic DMO

### Utterance Analysis

The `AIAgentInteractionMessage` DMO contains the full text of each user message and the agent's response; `AIAgentInteractionStep` holds the reasoning steps behind each turn. This is the primary raw material for diagnosing why an agent is misrouting, giving poor responses, or failing to resolve issues. When a session escalated unexpectedly, retrieve the interaction/message trace for that session to see the exact conversation flow.

### The Three Pillars

- **Agent Analytics** — topic-level effectiveness across your agents: agent topics, average feedback, and metrics such as **escalation rate, deflection rate, and abandoned sessions**. Consumed through Tableau Next.
- **Agent Optimization** — go a layer deeper: dig into unresolved interactions, identify knowledge gaps, and inspect the agent's reasoning chain (user utterances, LLM calls, tool/action invocations, guardrail checks, response timing) session by session. This is a distinct pillar from Analytics, gated behind the **Access Agentforce Optimization** permission set.
- **Agent Health Monitoring** — near-real-time uptime, reliability, and responsiveness signals across your deployed agent fleet, so silent failures surface as actionable trust signals rather than going unnoticed until users complain.

### Coverage by Agent Type and Data Refresh Cadence

Observability coverage is **not uniform across agent types**:

| Agent type | Agent Analytics | Agent Optimization |
|---|---|---|
| Agentforce Service Agent (ASA) | Yes | Yes |
| Employee Agent | Yes | Yes |
| Default Agent | — | Yes |
| SDR Agent | Yes | — |

Data does not all land at the same time — set monitoring expectations accordingly:

| Data type | Approximate refresh latency |
|---|---|
| Session tracing data | ~30 minutes |
| Agent analytics | ~45–60 minutes |
| Moments / quality scores | Daily |
| Tags | Weekly |

### Legacy Dashboard vs the Session Tracing Data Model

Before GA (November 2025), Agentforce analytics were available via a built-in pre-GA dashboard. That legacy dashboard **retired May 31, 2026** (now a past event on Salesforce's retirements list). The replacement is the Session Tracing Data Model queried via Data Cloud SQL, with Tableau Next as the consumption/visualization layer. Any reporting still built on the legacy dashboard is already broken and must be migrated.

---

## Common Patterns

### Measuring Agent Deflection Rate

**When to use:** Regular operational monitoring of whether the agent is resolving sessions without human intervention.

**How it works (Data Cloud SQL):**
```sql
SELECT
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN SessionStatus = 'Completed' THEN 1 ELSE 0 END) AS deflected_sessions,
    ROUND(
        SUM(CASE WHEN SessionStatus = 'Completed' THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100,
        1
    ) AS deflection_rate_pct
FROM AIAgentSession
WHERE AgentName = 'My_Service_Agent'
  AND SessionStartDateTime >= DATEADD(day, -30, GETDATE())
```

**Why it works:** `SessionStatus = 'Completed'` indicates the agent fully resolved the session. Escalated and Abandoned sessions are not deflected.

### Diagnosing a Specific Escalated Session

**When to use:** A user or supervisor reports a specific session where the agent failed and they want to understand what happened.

**How it works (Data Cloud SQL):**
```sql
SELECT
    u.SessionId,
    u.SequenceNumber,
    u.UtteranceText,
    u.ResponseText,
    u.ResponseLatencyMs,
    t.TopicName,
    t.TopicConfidenceScore
FROM AIAgentInteractionMessage u
LEFT JOIN AIAgentInteractionStep t
    ON u.SessionId = t.SessionId
    AND u.SequenceNumber = t.UtteranceSequenceNumber
WHERE u.SessionId = '5MR...<session-id>'
ORDER BY u.SequenceNumber ASC
```

**Why it works:** This gives the full turn-by-turn conversation with topic classification at each turn — the raw material for diagnosing misrouting or poor response quality.

### Monitoring Average Response Latency

**When to use:** SLA monitoring for agent response times.

**How it works:**
```sql
SELECT
    AgentName,
    AVG(ResponseLatencyMs) AS avg_latency_ms,
    MAX(ResponseLatencyMs) AS p100_latency_ms,
    COUNT(*) AS utterance_count
FROM AIAgentInteractionMessage u
JOIN AIAgentSession s ON u.SessionId = s.Id
WHERE s.SessionStartDateTime >= DATEADD(day, -7, GETDATE())
GROUP BY AgentName
ORDER BY avg_latency_ms DESC
```

### Exporting a Session Trace to a Third-Party Tool (OTel API, Beta)

**When to use:** You want a full session trace in an external observability platform (Splunk, Datadog, New Relic — any tool that ingests OpenTelemetry) instead of, or alongside, Tableau Next.

**How it works:** A programmatic export API returns a single session as OpenTelemetry-formatted spans:

```http
GET /services/data/v66.0/einstein/audit/otel/{session-id}
```

- **Status: Beta.** Do not treat it as GA-stable.
- **Auth:** OAuth 2.0 via an **External Client App (ECA)**.
- **Output:** OTel `ResourceSpans` conforming to **OTLP (OpenTelemetry Protocol) v1.0**. The payload is pre-joined — all turns, messages, LLM calls, action executions, metric scores, and feedback signals for the session, with no additional SQL needed.
- **Limits:** **single-session only** (one session ID per request; no bulk queries yet), and the session's `StartTimestamp` must fall within the **previous 72 hours**. Standard Connect API rate limits apply.

**Why it works:** OTLP is the vendor-neutral wire format, so any OTLP-capable sink can ingest the spans directly. This is a materially different path from the Tableau Next / Flow-alert workflow — use it when your org already standardizes agent telemetry alongside other services in an external APM, not for in-org dashboards.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Overall deflection rate trend | Agent Analytics in Tableau Next, or query `AIAgentSession` grouped by day | Analytics gives escalation/deflection/abandonment out of the box; raw SQL for custom cuts |
| Diagnosing a specific bad session | Query the interaction/message/step trace with session ID | Full turn-by-turn view with reasoning steps |
| Finding knowledge gaps / unresolved interactions | Agent Optimization | Purpose-built pillar for reasoning-chain and knowledge-gap analysis |
| Watching for silent failures on live agents | Agent Health Monitoring | Near-real-time reliability signals, not batch analytics |
| Building an ops dashboard | Tableau Next dataset on the Session Tracing DMOs | Tableau Next is the current consumption layer (not CRM Analytics) |
| Piping traces into Splunk/Datadog/New Relic | OTel export API (Beta) | Vendor-neutral OTLP spans for external APM ingestion |

---

## Recommended Workflow

Step-by-step instructions for setting up Agentforce observability:

1. **Enable the feature and grant access.** In **Setup → Einstein Audit, Analytics, and Monitoring Setup**, turn on **Agentforce Session Tracing and Data Model** and **Agentforce Optimization**. Assign the **Tableau Next Limited Consumer** / **Tableau Next Platform Analyst** and **Data Cloud User** permission sets (and **Access Agentforce Optimization** for Optimization users), and confirm **API Enabled** on the profile.
2. **Confirm the Session Tracing DMOs are populating.** Run a simple count in Data Cloud SQL: `SELECT COUNT(*) FROM AIAgentSession` (allow ~30 minutes for session tracing data to land). If empty, check Data Cloud provisioning and the Agentforce Data Cloud connector.
3. **Establish baseline metrics.** Review escalation/deflection/abandonment in Agent Analytics (Tableau Next), or run baseline deflection and session-count queries for the last 30 days, and record them for comparison. Remember analytics lags session tracing by ~45–60 minutes.
4. **Build a monitoring view in Tableau Next** with: sessions per day, deflection-rate trend, escalation-rate trend, avg latency per agent, top topics by volume.
5. **Turn on Agent Optimization** to surface unresolved interactions and knowledge gaps, and use session-ID filtering to pull full interaction/step traces for escalated or QA-flagged sessions.
6. **Set up alert thresholds and external export.** If deflection rate drops below target or avg latency exceeds an SLA, trigger a Salesforce Flow-based notification to the Agentforce admin team, and lean on **Agent Health Monitoring** for near-real-time silent-failure signals. Optionally wire the **OTel export API (Beta)** into an external APM (Splunk/Datadog/New Relic) via an External Client App if your org standardizes agent telemetry outside Salesforce — remember its 72-hour, single-session limits.
7. **Retire any legacy dashboard dependency.** The pre-GA Agentforce Analytics dashboard retired May 31, 2026; migrate anything still pointing at it to the Session Tracing DMOs + Tableau Next.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Session Tracing and Optimization enabled in Einstein Audit, Analytics, and Monitoring Setup
- [ ] Tableau Next + Data Cloud User permission sets (and Access Agentforce Optimization) assigned; API Enabled set
- [ ] Data Cloud provisioned and `AIAgentSession` DMO is queryable and populating
- [ ] Baseline deflection rate, escalation rate, and session count established (accounting for refresh SLAs)
- [ ] Monitoring dashboard built in Tableau Next with key agent KPIs
- [ ] Interaction/message/step trace query tested and returning expected session data
- [ ] Agent-type coverage confirmed (some agent types get Analytics or Optimization only)
- [ ] Any legacy dashboard dependency removed (retired May 31, 2026)
- [ ] Alert thresholds configured for deflection rate and latency SLAs
- [ ] OTel export path validated if used (ECA/OAuth, 72-hour single-session window)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Session data is in Data Cloud, not the main org** — You cannot use standard SOQL to query Agentforce session traces. You must use Data Cloud SQL, or consume through Tableau Next. Developers used to querying everything via SOQL will hit a wall here.
2. **The DMO names are `AIAgent*`, not `AgentConversation*`** — The canonical Session Tracing DMOs are `AIAgentSession`, `AIAgentSessionParticipant`, `AIAgentInteraction`, `AIAgentInteractionMessage`, and `AIAgentInteractionStep`. Any `AgentConversationSession…` name is fabricated and will error. Confirm attributes against the official Data Model for Agentforce Session Tracing reference.
3. **Analytics runs on Tableau Next, not CRM Analytics** — Access requires the Tableau Next Limited Consumer / Platform Analyst permission set plus Data Cloud User and API Enabled. Provisioning CRM Analytics will not surface these agents' metrics.
4. **Coverage and refresh are not uniform** — Some agent types get Analytics only, some Optimization only (see the coverage table). And data lands on different clocks: session tracing ~30 min, analytics ~45–60 min, quality/moments daily, tags weekly. Don't diagnose a "missing metric" that simply hasn't refreshed yet.
5. **Legacy Analytics dashboard retired May 31, 2026** — Any operational process that still relies on the pre-GA Agentforce dashboard is already broken. Migrate to the Session Tracing DMOs + Tableau Next.
6. **Utterance text may be subject to data retention policies** — Depending on the org's Data Cloud retention configuration, message text may be purged after a set period. Set up aggregated reporting as the long-term record, not raw message queries.
7. **The OTel export API is Beta and narrow** — Single session per request, only sessions started in the previous 72 hours, OAuth via an External Client App. It is not a bulk historical export.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Deflection rate query | Data Cloud SQL query to compute session deflection rate over a date range |
| Session trace query | Data Cloud SQL query to retrieve full utterance trace for a specific session ID |
| Monitoring dashboard spec | List of dashboard components with their query sources and refresh cadences |

---

## Related Skills

- agentforce-guardrails — configuring topic scope and escalation triggers that affect session outcomes
- agent-topic-design — designing topics that reduce misrouting (which shows up in observability data)
- einstein-trust-layer — Trust Layer audit logging (distinct from session observability)
