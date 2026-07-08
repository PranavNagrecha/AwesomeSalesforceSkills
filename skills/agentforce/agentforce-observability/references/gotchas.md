# Gotchas — Agentforce Observability

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Session Data Lives in Data Cloud, Not the Main Org

**What happens:** Admins and developers attempt to build reports in standard Salesforce report builder or run SOQL queries for session data — and find nothing. The `AIAgentSession` DMOs live in Data Cloud, not the standard org database. (They are also easy to misname — the canonical DMOs are `AIAgentSession`, `AIAgentSessionParticipant`, `AIAgentInteraction`, `AIAgentInteractionMessage`, `AIAgentInteractionStep`; `AgentConversation*` names do not exist.)

**When it occurs:** Any attempt to build standard reports or run Developer Console SOQL against session trace objects.

**How to avoid:** Always use Data Cloud SQL / the Data Cloud Query Builder, or consume through Tableau Next (Agent Analytics), to access session trace data. Document this clearly in any runbook or monitoring setup guide.

---

## Gotcha 2: Legacy Analytics Dashboard Retired May 31, 2026

**What happens:** The Agentforce Analytics dashboard that shipped with the pre-GA version stopped working on May 31, 2026 (now a past retirement). Any automated report, stakeholder notification, or operational process still referencing it fails or produces no data.

**When it occurs:** Orgs that were early adopters of Agentforce and built monitoring workflows around the legacy dashboard before the GA observability feature shipped in November 2025.

**How to avoid:** Audit all monitoring workflows for lingering references to the legacy dashboard and recreate them as Tableau Next datasets/Agent Analytics sourced from the Session Tracing DMOs.

---

## Gotcha 3: Utterance Text May Be Subject to Data Cloud Retention Policies

**What happens:** An admin queries for utterance text from sessions 90+ days ago and finds the text fields are null or the records do not exist, even though session-level metadata is still present.

**When it occurs:** When Data Cloud retention policies are configured to purge detailed utterance content after a set number of days for privacy compliance.

**How to avoid:** Do not rely on raw utterance text for long-term analytics. Build aggregated metrics (deflection rate, topic distribution, latency percentiles) as the operational record. Store utterance content in a separate retention-controlled location if conversation replay capability is required for compliance.
