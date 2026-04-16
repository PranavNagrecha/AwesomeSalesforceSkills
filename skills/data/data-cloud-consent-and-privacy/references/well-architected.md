# Well-Architected Notes — Data Cloud Consent and Privacy

## Relevant Pillars

- **Security** — Consent records must be treated as sensitive data with appropriate access controls. The `ssot__ContactPointConsent__dlm` DMO should be restricted to roles that manage consent. Consent status must not be overridden or ignored in activation workflows.
- **Reliability** — Deletion requests take up to 90 days to process. Downstream cascade deletion must be tracked and monitored. A gap between Data Cloud erasure and downstream system erasure creates a compliance exposure window.
- **Operational Excellence** — Consent filter requirements must be codified in segment review checklists. Retention policy configuration must be part of the data onboarding runbook. DSAR processing must be tracked with SLA monitoring.

## Architectural Tradeoffs

**Platform-Enforced vs. Application-Enforced Consent:** Data Cloud does not enforce consent at the platform level — it must be enforced in segment definitions. This gives flexibility but requires discipline. Organizations that rely solely on consent record creation without segment filter enforcement will have compliance gaps.

**Streaming Consent vs. Batch Consent Updates:** If consent records are ingested via streaming Ingestion API, there is a ~3-minute propagation delay plus pipeline lag before the consent record affects segment membership. For urgent opt-out processing (e.g., real-time web form), implement consent enforcement at the activation system level as a failsafe in addition to Data Cloud consent filtering.

**Data Use Purpose Granularity:** Coarse-grained purposes (e.g., "Marketing") create compliance risk when separate channels (email, SMS, push) have different consent requirements. Fine-grained purposes (e.g., "Marketing Email", "Marketing SMS") are more precise but require more consent records per individual.

## Anti-Patterns

1. **Segments Without Consent Filters** — Building any marketing or activation segment without an explicit `ssot__ContactPointConsent__dlm` OptIn filter is a GDPR/CCPA compliance violation. Platform does not enforce consent automatically.

2. **Relying Solely on Data Cloud Deletion for GDPR Compliance** — Data Cloud deletion propagates across the unified profile but does not reach external systems. Treating Privacy Center submission as the complete GDPR deletion workflow ignores all downstream systems seeded with activated data.

3. **Configuring Retention Policies After Data Ingestion** — Retention policies are not retroactive. Configuring a 1-year retention policy after 3 years of data has been ingested does not purge the excess data automatically.

## Official Sources Used

- Consent Management for Data Cloud — https://help.salesforce.com/s/articleView?id=consent_management_c360_audiences.htm
- Contact Point Consent DMO — https://developer.salesforce.com/docs/atlas.en-us.c360dm.meta/c360dm/c360dm-contact-point-consent-dmo.htm
- Data Subject Rights — Data Cloud — https://help.salesforce.com/s/articleView?id=xcloud.data_subject_rights.htm
- Use the Consent API with Data 360 — https://developer.salesforce.com/docs/atlas.en-us.resources_consent.meta/resources_consent/resources_consent_cdp_params.htm
- Data Retention Policies — https://help.salesforce.com/s/articleView?id=xcloud.data_retention_policies.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
