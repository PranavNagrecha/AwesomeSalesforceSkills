# LLM Anti-Patterns — Agentforce Observability

Common mistakes AI coding assistants make when generating or advising on Agentforce Observability.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Querying Session Data via Standard SOQL

**What the LLM generates:** Instructions to run SOQL like `SELECT Id FROM AgentConversationSession` in Developer Console or Apex.

**Why it happens:** LLMs default to SOQL for all Salesforce data queries. They are not aware that session trace objects live in Data Cloud, not the standard org.

**Correct pattern:**
```
// WRONG: standard SOQL against a non-existent object
SELECT Id, SessionStatus FROM AgentConversationSession LIMIT 10

// CORRECT: Data Cloud SQL against the canonical Session Tracing DMO
SELECT Id, AgentName
FROM AIAgentSession
LIMIT 10
```

The canonical DMOs are `AIAgentSession`, `AIAgentSessionParticipant`, `AIAgentInteraction`, `AIAgentInteractionMessage`, and `AIAgentInteractionStep`. Any `AgentConversation*` name is fabricated.

**Detection hint:** Any suggestion to query `AgentConversationSession`/`AgentConversationSessionUtterance` (fabricated), or to query the real `AIAgent*` DMOs via SOQL or from Apex.

---

## Anti-Pattern 2: Building Standard Salesforce Reports for Agent Metrics

**What the LLM generates:** Instructions to create a standard Salesforce report using the Reports tab, selecting `AgentConversationSession` as the report type.

**Why it happens:** LLMs know that Salesforce has a Reports tab and that analytics is often done there. They are not aware that session trace objects are not in the main org's report object universe.

**Correct pattern:** Build agent performance dashboards in **Tableau Next** (Agent Analytics) using a dataset sourced from the Session Tracing DMOs — not CRM Analytics, and not the standard Reports tab, which cannot access Data Cloud objects. Access requires the Tableau Next Limited Consumer / Platform Analyst permission set plus Data Cloud User and API Enabled.

**Detection hint:** Any mention of "create a new report" or "use the Reports tab" for Agentforce session data.

---

## Anti-Pattern 3: Using the Legacy Dashboard for Long-Term Monitoring

**What the LLM generates:** Instructions to navigate to the Agentforce Analytics dashboard in Setup for session monitoring, without noting its retirement date.

**Why it happens:** The legacy dashboard existed before GA and may appear in training data as the canonical monitoring solution.

**Correct pattern:** The legacy Agentforce Analytics dashboard retired May 31, 2026 (a past retirement). New monitoring should be built on Tableau Next / Agent Analytics over the Session Tracing DMOs, not the legacy dashboard.

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

---

## Anti-Pattern 6: Treating Observability as Analytics-Only

**What the LLM generates:** Advice that Agentforce Observability equals deflection/escalation dashboards, with no mention of Agent Optimization or Agent Health Monitoring.

**Why it happens:** The analytics pillar is the most visible, so LLMs collapse the whole product into "session metrics."

**Correct pattern:** Observability has three pillars — **Agent Analytics** (effectiveness metrics), **Agent Optimization** (unresolved-interaction and knowledge-gap analysis over the reasoning chain, gated by the Access Agentforce Optimization permission set), and **Agent Health Monitoring** (near-real-time silent-failure signals on deployed agents). For "why is my agent failing?" reach for Optimization, not just an Analytics chart.

**Detection hint:** Any recommendation that stops at deflection/escalation dashboards for a diagnosis-of-quality question.

---

## Anti-Pattern 7: Inventing a REST Endpoint for Session Export

**What the LLM generates:** A made-up API path or a claim that you can bulk-export all sessions programmatically as JSON.

**Why it happens:** LLMs pattern-match to generic REST and assume an unrestricted export exists.

**Correct pattern:** The only documented programmatic trace export is the **Beta** OTel API — `GET /services/data/v66.0/einstein/audit/otel/{session-id}` — which is **single-session only**, returns OTLP v1.0 `ResourceSpans`, authenticates via OAuth 2.0 through an **External Client App**, and only covers sessions started in the **previous 72 hours**. Do not promise bulk historical export.

**Detection hint:** Any session-export endpoint that isn't the `einstein/audit/otel/{session-id}` path, or any claim of bulk/multi-session export.
