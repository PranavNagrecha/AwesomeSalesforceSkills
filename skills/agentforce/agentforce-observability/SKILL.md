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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Agentforce Observability

Use this skill when monitoring Agentforce agent sessions in production, analyzing conversation logs stored in Data Cloud, measuring agent effectiveness (deflection rate, escalation rate, avg response latency), or diagnosing specific agent behavior issues by examining session trace data. Agentforce Observability reached GA in November 2025.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Data Cloud (Data 360) is provisioned and connected to the org. Agentforce session data is stored in Data Cloud — it is not queryable from standard SOQL in the main org.
- Identify the agent(s) you are monitoring. Session data is queryable by agent ID or agent name.
- Note: the legacy Agentforce Analytics dashboard (the one pre-GA) retires May 31, 2026. Any org still using it should migrate to the Data Cloud query approach before that date.
- Be aware that session trace objects in Data Cloud use a distinct query surface (Data Cloud SQL or CRM Analytics datasets), not standard SOQL.

---

## Core Concepts

### Session Trace Data Model in Data Cloud

Agentforce conversation data is stored in Data Cloud as a set of linked session trace objects. The primary objects are:

| Object | Purpose |
|---|---|
| `AgentConversationSession` | One record per agent session. Contains agent ID, session start/end times, session status (Completed, Escalated, Abandoned), and participant info. |
| `AgentConversationSessionUtterance` | One record per message turn. Links to the session and contains the utterance text, response text, and response latency. |
| `AgentConversationSessionTopic` | One record per topic classification event in the session. Links to the session and records which topic was selected and its confidence score. |

Key metrics computable from these objects:
- **Deflection rate:** Sessions with status = Completed (agent resolved without human) ÷ total sessions
- **Escalation rate:** Sessions with status = Escalated ÷ total sessions
- **Avg agent latency:** Average of response latency across all utterances
- **Sessions by topic:** Count of `AgentConversationSessionTopic` grouped by topic name

### Utterance Analysis

The `AgentConversationSessionUtterance` object contains the full text of each user message and the agent's response. This is the primary tool for diagnosing why an agent is misrouting, giving poor responses, or failing to resolve issues. When a session escalated unexpectedly, retrieve the utterance trace for that session to see the exact conversation flow.

### Legacy Dashboard vs Data Cloud Queries

Before GA (November 2025), Agentforce analytics were available via a built-in dashboard in the Agentforce app. This dashboard retires May 31, 2026. The replacement is Data Cloud SQL queries and CRM Analytics datasets built on the session trace objects listed above. Any reporting built on the legacy dashboard needs to be migrated.

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
FROM AgentConversationSession
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
FROM AgentConversationSessionUtterance u
LEFT JOIN AgentConversationSessionTopic t
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
FROM AgentConversationSessionUtterance u
JOIN AgentConversationSession s ON u.SessionId = s.Id
WHERE s.SessionStartDateTime >= DATEADD(day, -7, GETDATE())
GROUP BY AgentName
ORDER BY avg_latency_ms DESC
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Overall deflection rate trend | Query `AgentConversationSession` grouped by day | Aggregation is faster on session object than utterance |
| Diagnosing a specific bad session | Query utterance trace with session ID | Full turn-by-turn view with topic classification |
| Topic performance comparison | Query `AgentConversationSessionTopic` grouped by topic | Shows which topics are handling sessions well |
| Building an ops dashboard | CRM Analytics dataset on session trace objects | Better visualization than raw SQL queries |
| Legacy dashboard migration (before May 2026) | Recreate dashboard metrics in CRM Analytics or CRMA | Legacy dashboard retiring May 31, 2026 |

---

## Recommended Workflow

Step-by-step instructions for setting up Agentforce observability:

1. **Confirm Data Cloud is provisioned and session trace objects exist.** Run a simple count query in Data Cloud SQL: `SELECT COUNT(*) FROM AgentConversationSession WHERE AgentName = '<your-agent>'`. If this fails, check Data Cloud provisioning and Agentforce Data Cloud connector setup.
2. **Establish baseline metrics.** Run deflection rate and session count queries for the last 30 days. Record baseline values to compare against future periods.
3. **Set up a CRM Analytics dataset** on the session trace objects. This enables building dashboard components without running raw SQL queries each time.
4. **Build a monitoring dashboard** with: sessions per day, deflection rate trend, escalation rate trend, avg latency per agent, top topics by volume.
5. **Enable utterance analysis for high-value sessions.** Use session ID filtering to pull full conversation traces for escalated sessions or sessions flagged by QA.
6. **Set up alert thresholds.** If deflection rate drops below the target threshold or avg latency exceeds an SLA threshold, trigger a Salesforce Flow-based notification to the Agentforce admin team.
7. **Migrate any legacy dashboard components** (if the org was using the pre-GA dashboard) to CRM Analytics before May 31, 2026.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Data Cloud provisioned and `AgentConversationSession` object is queryable
- [ ] Baseline deflection rate, escalation rate, and session count established
- [ ] Monitoring dashboard built in CRM Analytics with key agent KPIs
- [ ] Utterance trace query tested and returning expected session data
- [ ] Legacy dashboard migration plan in place (if applicable, deadline: May 31, 2026)
- [ ] Alert thresholds configured for deflection rate and latency SLAs

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Session data is in Data Cloud, not the main org** — You cannot use standard SOQL to query Agentforce session traces. You must use Data Cloud SQL or CRM Analytics. Developers used to querying everything via SOQL will hit a wall here.
2. **Legacy Analytics dashboard retires May 31, 2026** — Any operational process that relies on the pre-GA Agentforce dashboard will break on that date. Migration to Data Cloud-based reporting must be completed before then.
3. **Utterance text may be subject to data retention policies** — Depending on the org's Data Cloud retention configuration, utterance text may be purged after a set period. Set up aggregated reporting as the long-term record, not raw utterance queries.

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
