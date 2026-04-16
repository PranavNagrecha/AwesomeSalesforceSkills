# Well-Architected Notes — Data Storytelling Design

## Relevant Pillars

### Operational Excellence
Dashboards that communicate clearly reduce the time executives spend interpreting data and increase the quality and speed of decisions. The Z-pattern and text widget narrative approach are operationally efficient design patterns.

### Trustworthy AI
When using Smart Data Discovery narrative API to generate machine-produced insight text, the Trustworthy AI pillar requires that the narrative is accurate, explainable, and does not misrepresent trends. Machine-generated narratives should be reviewed by a human before being surfaced to executive audiences.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| User Experience | Apply Z-pattern layout and text widget narrative to reduce cognitive load |
| Efficiency | Pre-compute insights; do not require executives to calculate answers mentally |
| Consistency | Use the same color thresholds and layout patterns across all dashboard pages |

## Cross-Skill References

- `admin/analytics-dashboard-design` — Use for chart type selection and SAQL step configuration — the technical layer below storytelling
- `admin/analytics-kpi-definition` — Use to define KPI formulas and metric logic before designing narrative around them
- `agentforce/einstein-discovery-development` — Use for Einstein Discovery story creation and narrative REST API integration

## Official Sources Used

- CRM Analytics Design Trailhead — Principles of Good Design: https://trailhead.salesforce.com/content/learn/modules/analytics-app-design/principles-good-design
- CRM Analytics App Structuring and Design Concepts: https://trailhead.salesforce.com/content/learn/modules/analytics-app-design/structure-your-app
- Salesforce Well-Architected Overview: https://architect.salesforce.com/well-architected/overview
