# Well-Architected Notes — Referral Management Health Cloud

## Relevant Pillars

- **Security** — ClinicalServiceRequest records contain PHI (patient identity, clinical service type, provider information). Access must be restricted via the HealthCloudICM permission set and OWD settings. Do not make referral records world-readable. Referral data exchanged with external providers must transit through HIPAA-compliant channels only.
- **Operational Excellence** — Provider search index (CareProviderSearchableField) requires scheduled DPE job maintenance. Index staleness directly degrades care coordinator efficiency. Monitoring DPE job success/failure is a required operational control.
- **Reliability** — Referral status automation (Flows) must handle all status transition paths including error/declined paths. Unhandled Flow failures can leave referrals in an intermediate status with no follow-up action.
- **Performance** — The CareProviderSearchableField index is denormalized specifically for search performance. Bypassing it with direct SOQL queries on provider Account records will not scale to large provider networks.

## Architectural Tradeoffs

**ClinicalServiceRequest vs. Custom Object:** Using the standard ClinicalServiceRequest object aligns with FHIR R4 and Salesforce's Health Cloud data model roadmap. Custom objects require custom FHIR mapping if interoperability is needed and lose native Health Cloud UI integration. The tradeoff: ClinicalServiceRequest requires HealthCloudICM license assignment overhead; custom objects offer more schema flexibility but at the cost of platform alignment.

**Real-Time vs. Batch Provider Search Index:** The DPE-based CareProviderSearchableField approach is optimized for search performance at scale but introduces index latency. For orgs with very small provider networks, a direct SOQL-based provider lookup component might be acceptable. For any network over ~500 providers, the denormalized index approach is required for acceptable search performance.

## Anti-Patterns

1. **Using FSC Referral Management configuration for Health Cloud clinical referrals** — FSC Referral Management uses a different object model (Lead/Opportunity fields, Einstein scoring) designed for financial advisor-client referrals. Applying FSC Referral documentation to a Health Cloud org produces misconfiguration or no-ops. Always start from the Health Cloud Administration Guide.
2. **Skipping the DPE job and querying provider Accounts directly** — Direct SOQL queries against Account/Contact for provider search bypasses the optimized CareProviderSearchableField index, will not perform at scale, and does not benefit from the Health Cloud provider search UI components designed to work with this index.
3. **Creating custom Referral__c objects instead of using ClinicalServiceRequest** — Custom objects require all FHIR mapping to be built manually if the org ever needs interoperability. ClinicalServiceRequest is the FHIR R4-aligned standard; Salesforce's future Health Cloud features will target this object, not custom alternatives.

## Official Sources Used

- Health Cloud Administration Guide — Configure Referral Management: https://help.salesforce.com/s/articleView?id=ind.hc_referral_management.htm
- Health Cloud Developer Guide — Provider Network Management Data Model: https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/hco_object_care_provider.htm
- ClinicalServiceRequest Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_clinicalservicerequest.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
