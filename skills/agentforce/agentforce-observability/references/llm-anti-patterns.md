# LLM Anti-Patterns — Agentforce Observability

Common mistakes AI coding assistants make when generating or advising on Agentforce Observability.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Querying Session Data via Standard SOQL

**What the LLM generates:** Instructions to run SOQL like `SELECT Id FROM AgentConversationSession` in Developer Console or Apex.

**Why it happens:** LLMs default to SOQL for all Salesforce data queries. They are not aware that session trace objects live in Data Cloud, not the standard org.

**Correct pattern:**
```
// WRONG: standard SOQL
SELECT Id, SessionStatus FROM AgentConversationSession LIMIT 10

// CORRECT: Data Cloud SQL query in Data Cloud Query Builder
SELECT Id, SessionStatus, AgentName
FROM AgentConversationSession
WHERE SessionStartDateTime >= DATEADD(day, -30, GETDATE())
LIMIT 10
```

**Detection hint:** Any suggestion to query `AgentConversationSession` or `AgentConversationSessionUtterance` via SOQL or from Apex.

---

## Anti-Pattern 2: Building Standard Salesforce Reports for Agent Metrics

**What the LLM generates:** Instructions to create a standard Salesforce report using the Reports tab, selecting `AgentConversationSession` as the report type.

**Why it happens:** LLMs know that Salesforce has a Reports tab and that analytics is often done there. They are not aware that session trace objects are not in the main org's report object universe.

**Correct pattern:** Build agent performance dashboards in CRM Analytics (Tableau CRM) using a dataset sourced from Data Cloud session trace objects. The standard Reports tab cannot access Data Cloud objects.

**Detection hint:** Any mention of "create a new report" or "use the Reports tab" for Agentforce session data.

---

## Anti-Pattern 3: Using the Legacy Dashboard for Long-Term Monitoring

**What the LLM generates:** Instructions to navigate to the Agentforce Analytics dashboard in Setup for session monitoring, without noting its retirement date.

**Why it happens:** The legacy dashboard existed before GA and may appear in training data as the canonical monitoring solution.

**Correct pattern:** The legacy Agentforce Analytics dashboard retires May 31, 2026. New monitoring should be built on CRM Analytics datasets from Data Cloud session trace objects, not the legacy dashboard.

**Detection hint:** Any recommendation to use the "Agentforce Analytics" setup page without noting the May 2026 retirement.

---

## Anti-Pattern 4: Conflating Session Observability with Einstein Trust Layer Logging

**What the LLM generates:** Advice to check the Einstein Trust Layer audit log to see what users said to the agent.

**Why it happens:** Both involve logging Agentforce activity. LLMs conflate the two distinct logging surfaces.

**Correct pattern:** Einstein Trust Layer logs cover LLM prompt/response pairs and data masking events for compliance purposes. Session observability (utterances, session status, topic classification) is the user-facing conversation layer stored in Data Cloud. Use session trace objects for agent performance monitoring, Trust Layer logs for compliance and security auditing.

**Detection hint:** Any mention of "Trust Layer" in the context of measuring agent deflection rate or viewing conversation utterances.

---

## Anti-Pattern 5: Assuming Utterance Text Is Always Available for Historical Queries

**What the LLM generates:** Code or queries that rely on utterance text being available for all historical sessions indefinitely.

**Why it happens:** LLMs assume all stored data is always queryable. They do not model data retention policies.

**Correct pattern:** Utterance text in Data Cloud is subject to retention policies. Build aggregated metrics (deflection rate, session count, topic distribution) as the durable operational record. Use raw utterance queries only for recent sessions within the retention window.

**Detection hint:** Any query or report design that assumes utterance text from 90+ days ago is available without checking the Data Cloud retention policy configuration.
