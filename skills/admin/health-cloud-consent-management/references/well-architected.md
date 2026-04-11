# Well-Architected Notes — Health Cloud Consent Management

## Relevant Pillars

- **Security** — AuthorizationFormConsent records contain PHI-adjacent data (which patients have authorized which uses of their PHI). These records must be protected with appropriate OWD and sharing rules. The consent record is part of the HIPAA audit trail and must be retained (no deletion).
- **Operational Excellence** — Consent form display depends on a specific IsDefault flag on AuthorizationFormText. Missing this flag causes silent failure in enrollment workflows. Operational processes must include consent hierarchy validation checks before enrollment goes live.
- **Reliability** — Enrollment workflows that gate CareProgramEnrollee activation on consent status must handle edge cases: consent withdrawn after enrollment, consent expired, patient unable to provide consent. Build error paths in all consent-linked Flows.

## Architectural Tradeoffs

**AuthorizationFormConsent vs. Custom Consent Object:** Using AuthorizationFormConsent aligns with the Health Cloud data model and platform reporting. Custom consent objects can be more flexible but require custom FHIR mapping if interoperability is needed and will not integrate with Health Cloud's enrollment and consent UI components.

**Centralized vs. Per-Program Consent:** Some organizations prefer one HIPAA authorization form per patient (covering all programs). Others require per-program consent. Per-program consent creates more AuthorizationFormConsent records and more complex enrollment gating logic, but provides finer-grained PHI use control. The choice should be driven by legal/compliance team guidance.

## Anti-Patterns

1. **Conflating AuthorizationFormConsent with ContactPointConsent** — These serve different regulatory purposes. AuthorizationFormConsent is HIPAA clinical authorization. ContactPointConsent is GDPR/CCPA marketing opt-out. Using marketing consent objects for HIPAA authorization creates a compliance gap.
2. **Deleting consent records on withdrawal** — HIPAA requires retention of the complete consent history. Withdrawal means updating Status to a terminal value, not deleting the record. Any data cleanup or archival process must explicitly protect AuthorizationFormConsent from deletion.
3. **Assuming consent tracking enforces access control** — AuthorizationFormConsent documents consent but does not enforce PHI access restrictions. Separate sharing rules and OWD settings must implement actual access control.

## Official Sources Used

- Consent Management for Health Cloud: https://help.salesforce.com/s/articleView?id=ind.hc_consent_management.htm
- Optimizing Health Cloud Consent Management (Trailhead): https://trailhead.salesforce.com/content/learn/modules/health-cloud-consent-management
- Privacy Consent Data Model: https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/hco_object_authorization_form_consent.htm
- AuthorizationFormConsent Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_authorizationformconsent.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
