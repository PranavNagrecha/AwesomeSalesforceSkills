# Well-Architected Notes — Clinical Data Requirements

## Relevant Pillars

- **Operational Excellence** — The FHIR-Aligned Clinical Data Model activation is a prerequisite that must be tracked in every Health Cloud implementation's readiness checklist. CodeableConcept truncation policy must be documented and operationally maintained as source systems add new coding variants. Legacy EHR object migration is an ongoing operational concern that affects reporting and analytics.
- **Security** — Clinical data objects contain PHI. All FHIR R4-aligned objects require appropriate OWD settings and the HealthCloudICM permission set. FHIR Healthcare API endpoints require specific OAuth scopes and cannot be called with standard REST API credentials.
- **Reliability** — Middleware translation layers are critical path for all FHIR integrations. Middleware failures silently drop clinical data unless error monitoring and retry logic are implemented. FHIR bundle request size limits (30 entries per bundle, 10 read/search per bundle) must be designed into the integration for reliable bulk data processing.

## Architectural Tradeoffs

**Native FHIR R4 Objects vs. Custom Clinical Objects:** FHIR R4-aligned standard objects provide platform-native integration with Health Cloud clinical UI components, FHIR API endpoints, and future Salesforce investment. Custom clinical objects offer more schema flexibility but require custom FHIR mapping, custom UI, and manual maintenance as standards evolve. For any use case where FHIR R4-aligned objects exist, they should be the default choice.

**Direct FHIR API Storage vs. SObject API Storage:** The FHIR Healthcare API provides FHIR-native operations but with bundle size limits. The standard SObject API provides more granular control and higher throughput for bulk operations. Most implementations combine both: FHIR API for real-time clinical data transactions, SObject API for bulk data loads and reporting queries.

## Anti-Patterns

1. **Assuming Salesforce is a fully conformant FHIR server** — Salesforce's FHIR R4 implementation deliberately deviates from the spec (complex type flattening, CodeableConcept cap, cardinality differences). Direct FHIR bundle persistence without middleware translation will fail or silently lose data.
2. **Writing FHIR Patient demographics to Account fields** — Demographics map to child objects (PersonName, ContactPointPhone, ContactPointAddress). Writing to Account fields bypasses the Health Cloud data model.
3. **Using legacy HC24__ EHR objects for new integrations** — These objects are write-locked in new orgs and receive no future investment. All new integrations should target FHIR R4-aligned standard objects.

## Official Sources Used

- Life Sciences Cloud Developer Guide — Clinical Data Model and FHIR v4.0 Mapping: https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/hco_dev_fhir_mapping.htm
- Life Sciences Cloud Developer Guide — Store HL7 v2.3 Messages: https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/hco_dev_hl7.htm
- FHIR R4 Support Settings Setup: https://help.salesforce.com/s/articleView?id=ind.hc_fhir_r4_support_settings.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
