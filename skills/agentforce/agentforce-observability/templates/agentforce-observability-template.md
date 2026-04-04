# Agentforce Observability — Monitoring Setup Template

Use this template when setting up or reviewing Agentforce agent monitoring.

## Agent Being Monitored

- **Agent name:** ___
- **Agent ID:** ___
- **Target environment:** (production / full sandbox)
- **Data Cloud provisioned:** Yes / No

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

| Component | Visualization | Data Source | Refresh |
|---|---|---|---|
| Daily session count | Bar chart by status | AgentConversationSession | Daily |
| Rolling deflection rate | KPI + trend line | AgentConversationSession | Daily |
| Topic distribution | Pie chart | AgentConversationSessionTopic | Weekly |
| Avg latency by agent | Table | AgentConversationSessionUtterance | Daily |

## Alert Thresholds

| Metric | Warning Threshold | Critical Threshold | Notification Target |
|---|---|---|---|
| Deflection rate | Below ___% | Below ___% | |
| Avg latency | Above ___ ms | Above ___ ms | |
| Escalation rate | Above ___% | Above ___% | |

## Legacy Dashboard Migration Status (if applicable)

- [ ] Identified all monitoring workflows using legacy Agentforce Analytics dashboard
- [ ] Recreated in CRM Analytics before May 31, 2026
- [ ] Legacy dashboard references removed from runbooks

## Utterance Analysis Access Control

- [ ] Access to session utterance queries restricted to authorized roles
- [ ] Data Cloud retention policy reviewed and documented
- [ ] Historical query window confirmed: retention period = ___ days

## Notes

(Record any issues with Data Cloud provisioning, query performance, or monitoring gaps)
