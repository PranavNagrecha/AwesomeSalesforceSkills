# Well-Architected Notes — Shield Event Log Retention

## Relevant Pillars

- **Security** — right retention for the right events; evidence survives long enough for audit.
- **Operational Excellence** — a query runbook converts retention from compliance theater to operational value.
- **Reliability** — tiered storage absorbs SIEM outages and supports legal hold.

## Architectural Tradeoffs

- **Hot-only vs tiered storage:** hot-only is simpler but cost-prohibitive at scale; tiered requires pipeline complexity but is the only economical path for multi-year retention.
- **In-SIEM vs Big Object archive:** SIEM is standard-practice; Big Objects keep auditors in Salesforce but need custom tooling.
- **Stream vs batch:** streaming enables real-time detection but costs more; batch is sufficient for audit.

## Anti-Patterns

1. Keeping every event at hot tier.
2. Enabling Shield Event Monitoring with no archive pipeline.
3. Leaving retention at defaults in a regulated industry.

## Official Sources Used

- Salesforce Shield Event Monitoring — https://help.salesforce.com/s/articleView?id=sf.real_time_event_monitoring_overview.htm
- Event Log File reference — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_event_log_file.htm
- Big Objects — https://developer.salesforce.com/docs/atlas.en-us.bigobjects.meta/bigobjects/big_object_intro.htm
- Salesforce Well-Architected Security — https://architect.salesforce.com/docs/architect/well-architected/trusted/secure
