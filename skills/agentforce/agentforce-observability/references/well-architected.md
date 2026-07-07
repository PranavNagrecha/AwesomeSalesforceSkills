# Well-Architected Notes — Agentforce Observability

## Relevant Pillars

- **Operational Excellence** — Observability is the foundation of operational excellence for agentic systems. Without session trace data and deflection metrics, teams cannot distinguish between an agent that is performing well and one that is failing silently. Structured monitoring with alerting on deflection rate and latency thresholds enables proactive management rather than reactive firefighting.
- **Reliability** — An agent that is monitored can be made reliable. Unmonitored agents degrade in quality over time as business processes change and the agent's training data becomes stale. Observability creates the feedback loop needed to maintain reliable agent behavior.
- **Security** — Utterance logs may contain PII or sensitive customer data. Data Cloud retention policies must align with data governance requirements. Access to session trace data should be restricted to authorized roles.

## Architectural Tradeoffs

**Real-time vs. batch monitoring:** Data Cloud session trace data is available with a short latency (session tracing ~30 min, analytics ~45–60 min, quality/moments daily, tags weekly) but is not real-time. For near-real-time silent-failure detection use **Agent Health Monitoring**; for immediate escalation reactions consider Agentforce event callbacks or Platform Events from the agent's action layer rather than querying Data Cloud.

**In-org analytics vs. external APM:** Tableau Next (Agent Analytics) and Agent Optimization keep the feedback loop inside Salesforce. The **Beta OTel export API** instead pushes a session's spans (OTLP v1.0) into an external tool like Splunk, Datadog, or New Relic — useful when agent telemetry must sit alongside the rest of your services, at the cost of a Beta surface with single-session/72-hour limits.

**Raw utterance access vs. aggregated metrics:** Raw utterance queries provide the deepest diagnostic capability but raise data governance concerns and are subject to retention policy limits. Design monitoring to use aggregated metrics for ongoing operations and raw utterance access as an exception for specific troubleshooting, with appropriate access controls.

## Anti-Patterns

1. **Building monitoring dashboards in the standard Salesforce report builder** — Session trace DMOs are in Data Cloud. Standard reports will not find them. Build in Tableau Next (Agent Analytics), not CRM Analytics.
2. **Relying on the legacy Agentforce Analytics dashboard** — It retired May 31, 2026. Any monitoring workflow still built on it is already broken.
3. **Querying utterance text without data governance controls** — Utterance logs may contain sensitive customer information. Access should be restricted and queries should be subject to the same controls as PII access.

## Official Sources Used

- Salesforce Help — Learn About Agentforce Observability — https://help.salesforce.com/s/articleView?id=005226932&language=en_US&type=1
- Salesforce Help — Agentforce Observability Setup and Access — https://help.salesforce.com/s/articleView?id=005237036&language=en_US&type=1
- Salesforce Help — Data Model for Agentforce Session Tracing — https://help.salesforce.com/s/articleView?language=en_US&id=ai.generative_ai_session_trace_data_model.htm&type=5
- Salesforce Help — About Agentforce Session Tracing — https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_about.htm&language=en_US&type=5
- Salesforce Developers — Agentforce Session Trace OTel API (Beta) — https://developer.salesforce.com/docs/ai/agentforce/guide/otel-api.html
- Salesforce Help — Product and Feature Retirements (Legacy Agentforce Analytics) — https://help.salesforce.com/s/articleView?id=005132112&language=en_US&type=1
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
