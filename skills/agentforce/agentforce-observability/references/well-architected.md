# Well-Architected Notes — Agentforce Observability

## Relevant Pillars

- **Operational Excellence** — Observability is the foundation of operational excellence for agentic systems. Without session trace data and deflection metrics, teams cannot distinguish between an agent that is performing well and one that is failing silently. Structured monitoring with alerting on deflection rate and latency thresholds enables proactive management rather than reactive firefighting.
- **Reliability** — An agent that is monitored can be made reliable. Unmonitored agents degrade in quality over time as business processes change and the agent's training data becomes stale. Observability creates the feedback loop needed to maintain reliable agent behavior.
- **Security** — Utterance logs may contain PII or sensitive customer data. Data Cloud retention policies must align with data governance requirements. Access to session trace data should be restricted to authorized roles.

## Architectural Tradeoffs

**Real-time vs. batch monitoring:** Data Cloud session trace data is available with a short latency (typically minutes) but is not real-time. For immediate escalation detection, consider using Agentforce event callbacks or Platform Events from the agent's action layer rather than querying Data Cloud.

**Raw utterance access vs. aggregated metrics:** Raw utterance queries provide the deepest diagnostic capability but raise data governance concerns and are subject to retention policy limits. Design monitoring to use aggregated metrics for ongoing operations and raw utterance access as an exception for specific troubleshooting, with appropriate access controls.

## Anti-Patterns

1. **Building monitoring dashboards in the standard Salesforce report builder** — Session trace objects are in Data Cloud. Standard reports will not find them. Build in CRM Analytics.
2. **Relying on the legacy Agentforce Analytics dashboard** — It retires May 31, 2026. Any monitoring workflow built on it will break.
3. **Querying utterance text without data governance controls** — Utterance logs may contain sensitive customer information. Access should be restricted and queries should be subject to the same controls as PII access.

## Official Sources Used

- Salesforce Help — Agentforce Observability — https://help.salesforce.com/s/articleView?id=sf.agentforce_observability.htm
- Salesforce Help — Agent Analytics Data Cloud Objects — https://help.salesforce.com/s/articleView?id=sf.agentforce_analytics_data_objects.htm
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce-dev-guide.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
