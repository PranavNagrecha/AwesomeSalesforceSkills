# Examples — Agentforce Observability

## Example 1: Building a Weekly Deflection Rate Report

**Context:** A customer service team deployed an Agentforce agent to handle tier-1 service requests. The VP of Service wants a weekly report showing how often the agent resolves cases without human escalation.

**Problem:** There is no out-of-the-box weekly deflection report that emails to stakeholders. The legacy dashboard shows a current snapshot but no trend.

**Solution:**

1. Create a CRM Analytics dataset sourced from `AgentConversationSession` in Data Cloud.
2. Build a CRMA dashboard with a bar chart of daily session counts colored by status (Completed vs Escalated vs Abandoned).
3. Add a KPI tile showing rolling 7-day deflection rate computed from the dataset.
4. Schedule the dashboard for email delivery to stakeholders every Monday at 8 AM.

Key query for the deflection rate KPI:
```sql
SELECT
    DATE_TRUNC('week', SessionStartDateTime) AS week,
    ROUND(
        SUM(CASE WHEN SessionStatus = 'Completed' THEN 1.0 ELSE 0.0 END)
        / COUNT(*) * 100, 1
    ) AS deflection_pct
FROM AgentConversationSession
WHERE AgentName = 'Service_Agent'
GROUP BY 1
ORDER BY 1 DESC
```

**Why it works:** The session status field directly indicates the resolution outcome. Grouping by week and computing the ratio gives a trended deflection rate that stakeholders can act on.

---

## Example 2: Diagnosing Why an Agent Keeps Escalating on Billing Questions

**Context:** The service team notices that sessions containing billing-related questions escalate to a human agent at a much higher rate than other topics. They want to understand why.

**Problem:** The legacy dashboard does not show topic-level breakdowns, and they cannot see the actual conversation content.

**Solution:**

Step 1 — Find sessions that escalated while discussing billing:
```sql
SELECT s.Id, s.SessionStartDateTime, s.SessionStatus, t.TopicName
FROM AgentConversationSession s
JOIN AgentConversationSessionTopic t ON s.Id = t.SessionId
WHERE s.AgentName = 'Service_Agent'
  AND s.SessionStatus = 'Escalated'
  AND t.TopicName = 'Billing_Inquiry'
  AND s.SessionStartDateTime >= DATEADD(day, -14, GETDATE())
ORDER BY s.SessionStartDateTime DESC
LIMIT 20
```

Step 2 — Pull the utterance trace for the most recent escalated billing session:
```sql
SELECT SequenceNumber, UtteranceText, ResponseText, ResponseLatencyMs
FROM AgentConversationSessionUtterance
WHERE SessionId = '5MRxx...'
ORDER BY SequenceNumber ASC
```

Step 3 — Review the utterance trace. In this case, the agent is not handling refund-related questions because the Billing_Inquiry topic scope does not include refund processing.

**Why it works:** The utterance trace reveals the exact conversation turn where the agent failed to provide a useful response, leading to escalation. The team can then update the topic scope or add an action to handle refund queries.

---

## Anti-Pattern: Using Standard SOQL to Query Session Data

**What practitioners do:** Try to run SOQL queries from Developer Console or Apex to find `AgentConversationSession` records.

**What goes wrong:** The session trace objects live in Data Cloud (Data 360), not in the standard Salesforce org database. Standard SOQL returns "Object type AgentConversationSession is not supported in queries" or simply finds no records.

**Correct approach:** Use Data Cloud SQL via the Data Cloud Query Builder, CRM Analytics datasets, or the Data Cloud Einstein Analytics connector. Never attempt to query session trace objects via standard SOQL.
