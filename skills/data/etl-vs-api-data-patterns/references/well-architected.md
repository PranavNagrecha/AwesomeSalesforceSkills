# Well-Architected Notes — ETL vs API Data Patterns

## Relevant Pillars

### Reliability
Matching the integration pattern to the use case (batch ETL for volume/governance, API for real-time) directly affects reliability. Using REST API for bulk ETL introduces daily limit exhaustion failure modes that do not exist with Bulk API 2.0 or ETL tools.

### Performance Efficiency
Bulk API 2.0 processes records in batches with significantly higher throughput than row-by-row REST API calls. Selecting the right interface (Bulk vs REST) for the data volume is a performance efficiency decision.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Right-Sizing | ETL tools for bulk volume; API-led for real-time; do not over-engineer real-time for batch use cases |
| Appropriate Tooling | Official Salesforce Architects guidance: MuleSoft for application integration, Informatica for data integration |
| Limit Awareness | All bulk ETL must use Bulk API 2.0 to avoid exhausting the REST API daily limit |

## Cross-Skill References

- `data/data-migration-planning` — Use for one-time data migration tool selection (not ongoing ETL)
- `integration/middleware-integration-patterns` — Use for iPaaS vendor comparison and middleware selection
- `integration/change-data-capture-integration` — Use for CDC-based incremental replication patterns as an alternative to full batch ETL

## Official Sources Used

- Salesforce Architects — Leveraging MuleSoft and Informatica: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-informatica-mulesoft
- Salesforce Architects — Data Integration Decision Guide: https://architect.salesforce.com/docs/architect/decision-guides/guide/data-integration
- Salesforce Architects — Integration Patterns: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Bulk API 2.0 Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
