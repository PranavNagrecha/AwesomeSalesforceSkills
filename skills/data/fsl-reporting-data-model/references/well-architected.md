# Well-Architected Notes — FSL Reporting Data Model

## Relevant Pillars

- **Reliability** — Travel time and actual duration data is only as reliable as FSL Mobile adoption. Reporting built on these fields without verifying mobile adoption produces systematically misleading KPIs. Document data quality dependencies explicitly in all FSL dashboards.
- **Performance** — FTF rate calculation via cross-filter reports is expensive at scale. Moving FTF calculation to write-time (Flow + custom field) versus read-time (report filter) significantly improves report load performance in large orgs.
- **Operational Excellence** — Dashboards should include data quality indicators: "% of Completed appointments with ActualTravelTime populated" surfaces mobile adoption gaps directly to operations leadership.

## Architectural Tradeoffs

**Native report cross-filters vs. custom FTF field:** Cross-filter FTF reports require no custom development but are slow at scale and provide no real-time visibility on in-flight records. A Flow + custom checkbox field requires development effort but delivers real-time FTF visibility, fast reports, and the ability to report FTF trend over time.

**CRM Analytics vs. native Reports:** Native Salesforce Reports are sufficient for basic FSL operational metrics (completion rate, utilization by resource, on-time arrival). CRM Analytics (Field Service Intelligence) provides pre-built FSL dashboards with predictive analytics but requires a separate license. For orgs without FSI, native reports plus Flow-calculated metrics cover most operational reporting needs.

## Anti-Patterns

1. **Reporting on ServiceReport for job performance data** — ServiceReport is a customer-facing PDF object. Operational data lives on ServiceAppointment and WorkOrder.
2. **Building travel time KPIs without verifying mobile check-in adoption** — Null travel time data creates misleading averages. Always validate mobile adoption before committing to travel time as a KPI.
3. **Assuming a native FTF field exists** — It doesn't. Planning FTF reporting without a custom field development budget means no real-time FTF metric.

## Official Sources Used

- Report on Field Service (help.salesforce.com) — https://help.salesforce.com/s/articleView?id=sf.fs_reports.htm
- ServiceAppointment Object (Field Service Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_data_model_service_appointment.htm
- Field Service Analytics (help.salesforce.com) — https://help.salesforce.com/s/articleView?id=sf.fs_analytics.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
