# Well-Architected Notes — FHIR Integration Patterns

## Relevant Pillars

- **Security** — FHIR integrations carry PHI. OAuth tokens with the `healthcare` scope must be rotated and stored securely. CDS Hook service endpoints (MuleSoft) must authenticate callers (EHR) to prevent unauthorized clinical alert queries. All FHIR data in transit must use TLS.
- **Reliability** — Middleware translation layers are critical path for FHIR integrations. Middleware failures mean clinical data from EHR does not reach Salesforce. Dead letter queues, retry logic, and operational alerting on middleware pipeline health are required for HIPAA-compliant clinical data flows.
- **Performance** — FHIR bundle limits (30 entries) constrain bulk data throughput. For high-volume EHR event streams, the middleware must implement efficient batching and fan-out. The standard SObject Bulk API is more efficient for bulk historical data loads than FHIR Healthcare API bundles.

## Architectural Tradeoffs

**MuleSoft vs. Custom Middleware:** MuleSoft Accelerator for Healthcare provides pre-built assets for Epic/Cerner and HL7 v2 to FHIR R4 conversion, significantly reducing integration development time. Custom middleware (custom FHIR translators, Node.js/Python services) provides more flexibility but requires full FHIR R4 mapping implementation from scratch. For major EHR vendors, MuleSoft Accelerator assets provide the most reliable starting point.

**Real-Time vs. Batch FHIR Sync:** Real-time event-driven FHIR sync (via EHR webhook → MuleSoft → Salesforce) provides immediate data currency but creates a dependency on EHR availability. Batch FHIR sync (scheduled FHIR search queries) is more resilient to EHR downtime but introduces data latency. Most implementations use both: real-time for critical events (admissions, discharges, new orders) and batch for historical data and overnight reconciliation.

## Anti-Patterns

1. **Assuming Salesforce is a native CDS Hooks service** — there is no native CDS Hook endpoint. MuleSoft is required as middleware.
2. **Sending raw FHIR bundles without middleware translation** — Salesforce is not a 1:1 FHIR server. Complex types must be flattened; CodeableConcept cardinalities differ; mandatory fields differ. Translation is always required.
3. **Using legacy HC24__ EHR objects for new integrations** — write-locked in Spring '23+ orgs. Always target FHIR R4-aligned standard objects.

## Official Sources Used

- Health Cloud Developer Guide — Mapping FHIR v4.0 to Salesforce Standard Objects: https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/hco_dev_fhir_mapping.htm
- MuleSoft Direct Integration Apps — Healthcare FHIR Patterns: https://docs.mulesoft.com/healthcare-accelerator/
- FHIR R4 Support for Better Interoperability (Release Notes): https://help.salesforce.com/s/articleView?id=release-notes.rn_ind_hc_fhir_r4.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
