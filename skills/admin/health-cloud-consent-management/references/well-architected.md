# Well-Architected Notes — Health Cloud Consent Management

## Relevant Pillars

- **Security** — AuthorizationFormConsent records contain PHI-adjacent data (which patients have authorized which uses of their PHI). These records must be protected with appropriate OWD and sharing rules. The consent record is part of the HIPAA audit trail and must be retained (no deletion).
- **Operational Excellence** — Consent form display depends on `AuthorizationForm.DefaultAuthFormTextId`, the fallback text when no language matches (there is no `IsDefault` field on `AuthorizationFormText`). The Data Protection and Privacy setting must be under change control, because turning it off purges stored consent forms. Operational processes must include consent hierarchy validation checks before enrollment goes live.
- **Reliability** — Enrollment workflows that gate CareProgramEnrollee activation on consent status must handle edge cases: consent withdrawn after enrollment, consent expired, patient unable to provide consent. Build error paths in all consent-linked Flows.

## Architectural Tradeoffs

**AuthorizationFormConsent vs. Custom Consent Object:** Using AuthorizationFormConsent aligns with the Health Cloud data model and platform reporting. Custom consent objects can be more flexible but require custom FHIR mapping if interoperability is needed and will not integrate with Health Cloud's enrollment and consent UI components.

**Centralized vs. Per-Program Consent:** Some organizations prefer one HIPAA authorization form per patient (covering all programs). Others require per-program consent. Per-program consent creates more AuthorizationFormConsent records and more complex enrollment gating logic, but provides finer-grained PHI use control. The choice should be driven by legal/compliance team guidance.

## Anti-Patterns

1. **Conflating AuthorizationFormConsent with ContactPointConsent** — These serve different regulatory purposes. AuthorizationFormConsent is HIPAA clinical authorization. ContactPointConsent is GDPR/CCPA marketing opt-out. Using marketing consent objects for HIPAA authorization creates a compliance gap.
2. **Deleting consent records on withdrawal**: the complete consent history must be kept. Withdrawal is recorded as `Status = Rejected` (there is no `Withdrawn` value), either as a new record or as an update with field history. Any data cleanup or archival process must explicitly protect AuthorizationFormConsent from deletion.
3. **Assuming consent tracking enforces access control** — AuthorizationFormConsent documents consent but does not enforce PHI access restrictions. Separate sharing rules and OWD settings must implement actual access control.

## Official Sources Used

Read for the 2026-10-03 pass (fetched with plain `curl`; line numbers cite the `pdftotext -layout` extraction):

- Object Reference for the Salesforce Platform, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (AuthorizationForm and `DefaultAuthFormTextId` L45946-46075; AuthorizationFormConsent required fields, source type values, `ConsentGiverId` targets, `Status` values, history L46076-46290; AuthorizationFormDataUse L46294-46405; AuthorizationFormText `Locale` and `LocaleSelection` L46410-46545; DataUsePurpose L95156-95240)
- Metadata API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (PartyDataModelSettings and the purge note L123939-123995; PrivacySettings authorization capture, custom sharing, locking and versioning L124598-124700; IndustriesSettings `enableAuthorizationCustomSharingPCU` L119541-119546; CustomField `trackHistory` L43675-43682)
- Salesforce Security Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf (Field Audit Trail policy objects including Authorization Form Consent L4833-4875)

Listed by the original author and not re-read in this pass (help.salesforce.com, the retired Trailhead page, and architect.salesforce.com did not serve readable content; the atlas object pages were superseded by the PDFs above):

- Consent Management for Health Cloud: https://help.salesforce.com/s/articleView?id=ind.hc_consent_management.htm
- Optimizing Health Cloud Consent Management (Trailhead): https://trailhead.salesforce.com/ (page retired; see host index for current equivalent)
- Privacy Consent Data Model: https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/hco_object_authorization_form_consent.htm
- AuthorizationFormConsent Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_authorizationformconsent.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
