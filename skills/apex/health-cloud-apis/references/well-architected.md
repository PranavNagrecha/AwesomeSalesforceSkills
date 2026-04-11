# Well-Architected Notes — Health Cloud APIs

## Relevant Pillars

- **Security** — FHIR Healthcare API requires the `healthcare` OAuth scope. Clinical SObjects require the HealthCloudICM permission set for all API users including integration users. FHIR responses contain PHI — OAuth tokens with `healthcare` scope must be stored securely and rotated regularly.
- **Performance** — FHIR bundle limits (30 entries, 10 reads) require chunking design for bulk operations. The standard SObject API has higher throughput for internal operations. Use the appropriate API layer for the performance requirements of the integration.
- **Reliability** — FHIR bundle HTTP 424 errors are dependency cascades from a single root failure. Error handling must implement dependency tracing, not just per-entry error counting. Retry logic must fix the root cause before retrying dependent entries.

## Architectural Tradeoffs

**FHIR Healthcare API vs. Standard SObject API:** FHIR Healthcare API provides FHIR R4-conformant responses required for external FHIR client interoperability but has lower throughput limits (30 entries/bundle). Standard SObject API has higher throughput and simpler error handling but returns non-FHIR response formats. For internal integrations and analytics, standard SObject API is preferred. For EHR/payer FHIR interoperability, FHIR Healthcare API is required.

**Bundle Transactions vs. Individual Calls:** FHIR bundles are atomic when using `type: "transaction"` — all entries succeed or all fail. This is valuable for creating related clinical records (CarePlan + Goals + Tasks) atomically. However, bundle failures cascade via 424. For independent clinical record operations, individual API calls may be simpler to debug and retry.

## Anti-Patterns

1. **Using the standard SObject endpoint for FHIR operations** — FHIR bundles sent to the standard SObject endpoint will fail or silently lose FHIR-specific fields. Always use the FHIR-specific endpoint for FHIR operations.
2. **Assuming standard API batch limits apply to FHIR bundles** — FHIR bundles are limited to 30 entries, not 200. Integrations built without chunking will fail at production data volumes.
3. **Not handling HTTP 424 dependency errors specifically** — Generic error handling that treats 424 like other 4xx errors will misdiagnose bundle failures. Always implement 424 dependency tracing.

## Official Sources Used

- Salesforce Healthcare API Get Started Guide: https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/hco_dev_healthcare_api.htm
- Health Cloud Developer Guide — Clinical Data Model: https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/
- Health Cloud Business APIs REST Reference: https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/hco_dev_api.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
