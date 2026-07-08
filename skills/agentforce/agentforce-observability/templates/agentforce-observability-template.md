# Agentforce Observability — Monitoring Setup Template

Use this template when setting up or reviewing Agentforce agent monitoring.

## Agent Being Monitored

- **Agent name:** ___
- **Agent ID:** ___
- **Agent type:** (ASA / Employee Agent / Default Agent / SDR) — coverage varies: ASA & Employee get Analytics + Optimization; Default = Optimization only; SDR = Analytics only
- **Target environment:** (production / full sandbox)
- **Data Cloud provisioned:** Yes / No
- **Setup toggles enabled (Einstein Audit, Analytics, and Monitoring Setup):** Session Tracing and Data Model ___ / Agentforce Optimization ___
- **Access provisioned:** Tableau Next Limited Consumer or Platform Analyst ___ / Data Cloud User ___ / API Enabled ___ / Access Agentforce Optimization ___

## Baseline Metrics (First Week After Go-Live)

Run these queries and record baseline values:

| Metric | Query Run Date | Value |
|---|---|---|
| Total sessions (last 7 days) | | |
| Deflection rate (last 7 days) | | |
| Escalation rate (last 7 days) | | |
| Avg response latency (ms) | | |
| Top 3 topics by session volume | | |

## Monitoring Dashboard Components

Built in Tableau Next (Agent Analytics), sourced from the Session Tracing DMOs:

| Component | Visualization | Data Source (DMO) | Refresh |
|---|---|---|---|
| Daily session count | Bar chart by status | AIAgentSession | Daily |
| Rolling deflection rate | KPI + trend line | AIAgentSession | Daily |
| Topic distribution | Pie chart | Agent Analytics (topic effectiveness) | Weekly |
| Avg latency by agent | Table | AIAgentInteraction / AIAgentInteractionMessage | Daily |

## Alert Thresholds

| Metric | Warning Threshold | Critical Threshold | Notification Target |
|---|---|---|---|
| Deflection rate | Below ___% | Below ___% | |
| Avg latency | Above ___ ms | Above ___ ms | |
| Escalation rate | Above ___% | Above ___% | |

## Legacy Dashboard Migration Status (if applicable)

The legacy Agentforce Analytics dashboard retired May 31, 2026.

- [ ] Identified all monitoring workflows using the legacy Agentforce Analytics dashboard
- [ ] Recreated in Tableau Next (Agent Analytics) over the Session Tracing DMOs
- [ ] Legacy dashboard references removed from runbooks

## External Telemetry Export (optional, OTel API — Beta)

- [ ] External Client App configured for OAuth 2.0
- [ ] Target sink confirmed OTLP-capable (Splunk / Datadog / New Relic)
- [ ] Aware of Beta limits: single session per request, 72-hour window

## Utterance Analysis Access Control

- [ ] Access to session utterance queries restricted to authorized roles
- [ ] Data Cloud retention policy reviewed and documented
- [ ] Historical query window confirmed: retention period = ___ days

## Notes

(Record any issues with Data Cloud provisioning, query performance, or monitoring gaps)
