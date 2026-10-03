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

Read for this revision (2026-10-03):

- Analytics Dashboard JSON Developer Guide (Summer '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_json.pdf. Widget `type` list, text and number widget parameters, bindings in the apex step example, `gridLayouts` and `selectors`, `mobileDisabled`, saql step example, apex step limitations.
- Analytics Platform Setup Guide (Spring '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_admin_guide_setup.pdf. Lens and Dashboard Limits (default table rows, 4 MB JSON, components per dashboard); CRM Analytics on Mobile Devices.
- Einstein Discovery REST API Developer Guide (Spring '26), local corpus: `knowledge/imports/bi-dev-guide-rest-sdd.md`. Narrative Resource (`POST /smartdatadiscovery/narrative`, API 51.0).
- CRM Analytics REST API Developer Guide (Summer '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_rest.pdf. Overview pointer to the smartdatadiscovery API.
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. WaveDashboard (unsupported `.wdash` modifications, step-removal deployment failure, suffix, `application`), WaveApplication, WaveDataset.
- Tableau Help, Stories: https://help.tableau.com/current/pro/desktop/en-us/stories.htm
- Tableau Help, Create a Story: https://help.tableau.com/current/pro/desktop/en-us/story_create.htm
- Tableau Help, Tableau Pulse Release Notes: https://help.tableau.com/current/online/en-us/pulse_intro.htm

Listed in the original version and not re-read:

- CRM Analytics Design Trailhead, Principles of Good Design: https://trailhead.salesforce.com/content/learn/modules/analytics-app-design/principles-good-design (HTTP 404 on 2026-10-03).
- CRM Analytics App Structuring and Design Concepts: https://trailhead.salesforce.com/content/learn/modules/analytics-app-design/structure-your-app (HTTP 404 on 2026-10-03).
- Salesforce Well-Architected Overview: https://architect.salesforce.com/well-architected/overview
