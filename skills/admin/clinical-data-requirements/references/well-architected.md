# Well-Architected Notes — Clinical Data Requirements

## Relevant Pillars

- **Operational Excellence** — The FHIR-Aligned Clinical Data Model activation is a prerequisite that must be tracked in every Health Cloud implementation's readiness checklist. CodeableConcept truncation policy must be documented and operationally maintained as source systems add new coding variants. Legacy EHR object migration is an ongoing operational concern that affects reporting and analytics.
- **Security** — Clinical data objects contain PHI. All FHIR R4-aligned objects require appropriate OWD settings and Health Cloud permission set licences (UNVERIFIED (2026-10-03): a `HealthCloudICM` permission set is not named in the guide); community users need the FHIR R4 for Experience Cloud Sites permission set. FHIR Healthcare API endpoints require specific OAuth scopes and cannot be called with standard REST API credentials.
- **Reliability** — Middleware translation layers are critical path for all FHIR integrations. Middleware failures silently drop clinical data unless error monitoring and retry logic are implemented. FHIR bundle request size limits must be designed into the integration for reliable bulk processing (UNVERIFIED (2026-10-03): the figures of 30 entries and 10 read or search operations per bundle are not in the Health Cloud developer guide; confirm them in the Healthcare API guide).

## Architectural Tradeoffs

**Native FHIR R4 Objects vs. Custom Clinical Objects:** FHIR R4-aligned standard objects provide platform-native integration with Health Cloud clinical UI components, FHIR API endpoints, and future Salesforce investment. Custom clinical objects offer more schema flexibility but require custom FHIR mapping, custom UI, and manual maintenance as standards evolve. For any use case where FHIR R4-aligned objects exist, they should be the default choice.

**Direct FHIR API Storage vs. SObject API Storage:** The FHIR Healthcare API provides FHIR-native operations but with bundle size limits. The standard SObject API provides more granular control and higher throughput for bulk operations. Most implementations combine both: FHIR API for real-time clinical data transactions, SObject API for bulk data loads and reporting queries.

## Anti-Patterns

1. **Assuming Salesforce is a fully conformant FHIR server** — Salesforce's FHIR R4 implementation deliberately deviates from the spec (complex type flattening, CodeableConcept cap, cardinality differences). Direct FHIR bundle persistence without middleware translation will fail or silently lose data.
2. **Writing FHIR Patient demographics to Account fields** — Demographics map to child objects (PersonName, ContactPointPhone, ContactPointAddress). Writing to Account fields bypasses the Health Cloud data model.
3. **Using legacy HC24__ EHR objects for new integrations**: new customers since Spring '23 cannot create records in packaged EHR objects that have standard counterparts, and future development targets the FHIR R4-aligned model. All new integrations should target the standard objects.

## Official Sources Used

Read for the 2026-10-03 pass (fetched with plain `curl`; line numbers cite the `pdftotext -layout` extraction):

- Agentforce Health Developer Guide (Health Cloud developer guide), Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/health_cloud_dev_guide.pdf (clinical data model intro and HL7 v2.3 statement L8320-8338; org pref activation, object lists, added fields, and Spring '23 legacy note L8345-8410; HealthCondition fields L15119-15320; legacy `HC24__` object names L24863-24892; Considerations for Integration, CodeSetBundle flattening, and HumanName L75600-75700; Condition mapping L76778-76790; HL7 v2.3 messages and segments L82428-82530)
- Metadata API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (IndustriesSettings type definition L119169-119200; Health Cloud fields including `enableClinicalDataModel` L119538-119645)

Listed by the original author and not re-read in this pass (help.salesforce.com and architect.salesforce.com do not serve article content to plain HTTP clients; the atlas pages were superseded by the PDF above):

- Life Sciences Cloud Developer Guide, Clinical Data Model and FHIR v4.0 Mapping: https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/hco_dev_fhir_mapping.htm
- Life Sciences Cloud Developer Guide, Store HL7 v2.3 Messages: https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/hco_dev_hl7.htm
- FHIR R4 Support Settings Setup: https://help.salesforce.com/s/articleView?id=ind.hc_fhir_r4_support_settings.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
