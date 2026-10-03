# Well-Architected Notes: ETL vs API Data Patterns

## Relevant Pillars

### Reliability
Matching the pattern to the requirement keeps a pipeline inside its limits. A batch pipeline needs a control table with restart values, an upsert key, and a path for failed and unprocessed records. An event pipeline needs retries on the caller side, because Remote Call-In is synchronous request-reply.

### Performance Efficiency
Bulk API 2.0 moves a whole delta in one job. Single-record REST writes multiply requests. Sorting child rows by parent reduces lock failures in Bulk API 2.0's parallel-only processing.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Right-Sizing | Composite or sObject Collections under 2,000 records; Bulk API 2.0 above; APIs or events for per-record latency |
| Appropriate Tooling | MuleSoft for application connectivity, Informatica for data management, both when the architecture needs both (Salesforce Architects "Better Together") |
| Limit Awareness | Budget daily API requests, 150,000,000 ingest records, and 15,000 batches across every tool |

## Cross-Skill References

- `data/data-migration-planning`: one-time migration tool selection
- `integration/middleware-integration-patterns`: iPaaS vendor comparison
- `integration/change-data-capture-integration`: CDC-based replication when Salesforce is the master

## Official Sources Used

- Salesforce Architects, "Leveraging MuleSoft and Informatica: Better Together" (fetched 2026-10-03): https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-informatica-mulesoft
- Salesforce Architects, "Data Integration with Salesforce" decision guide (fetched 2026-10-03; the older URL https://architect.salesforce.com/docs/architect/decision-guides/guide/data-integration serves the same guide): https://architect.salesforce.com/decision-guides/data-integration
- Integration Patterns and Practices, Summer '26 (262): Pattern Selection Guide, "Batch Data Synchronization," "Remote Call-In." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/integration_patterns_and_practices.pdf
- Bulk API 2.0 and Bulk API Developer Guide, Summer '26 (262): introduction, "Understanding Bulk API 2.0 Ingest," "Step 5: Bulk Upsert," Create a Job and Create a Query Job request bodies, failed and unprocessed result resources. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_asynch.pdf
- Salesforce Developer Limits and Allocations Quick Reference, Summer '26 (262): "API Request Limits and Allocations," "Bulk API and Bulk API 2.0 Limits and Allocations." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- REST API Developer Guide, Summer '26 (262): "sObject Collections," upsert by external ID. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- Metadata API Developer Guide, Summer '26 (262): CustomField `externalId`, `unique`, `caseSensitive`. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- MuleSoft Documentation, "Batch Processing" (Mule 4, fetched 2026-10-03): https://docs.mulesoft.com/mule-runtime/latest/batch-processing-concept

### Earlier references kept from version 1.0.0 (checked 2026-10-03: atlas pages return a script shell, help.salesforce.com returns an app shell, and Well-Architected guide pages redirect to the home page, so no claim in this skill rests on these links)

- Salesforce Architects, Integration Patterns page: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Bulk API 2.0 Developer Guide (atlas page): https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
