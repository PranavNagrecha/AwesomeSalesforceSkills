# Well-Architected Notes — Consent Data Model Health

## Relevant Pillars

- **Security** — The consent hierarchy is the HIPAA authorization audit trail. Every architectural decision must preserve the integrity, completeness, and immutability of that trail. ConsentGiverId must resolve to the correct Individual. AuthorizationFormText records must be append-only to prevent retroactive audit corruption. The consent model must be explicitly decoupled from the sharing model — neither system compensates for gaps in the other.
- **Reliability** — The CareProgramEnrollee activation gate is a critical reliability control. If it is absent or misconfigured, patients can be enrolled without documented HIPAA authorization, creating regulatory exposure. The gate must be included in deployment packages and verified after every org refresh. Consent status checks in clinical workflows must filter on both status and DataUsePurpose to avoid false-positive clearances.
- **Performance** — AuthorizationFormConsent records grow at patient scale. SOQL queries traversing the full hierarchy (AuthorizationFormConsent → AuthorizationFormText → AuthorizationFormDataUse → DataUsePurpose) must use selective filters on indexed fields. `ConsentGiverId` is indexed by default. Avoid cross-object formula fields on AuthorizationFormConsent that trigger recalculation at enrollment time.
- **Scalability** — For large patient populations, consent records should be archived when the associated care episode is closed. Big Object archival or external storage should be planned for organizations with multi-million patient populations to prevent consent query degradation over time.
- **Operational Excellence** — Consent hierarchy configuration (DataUsePurpose, AuthorizationForm, AuthorizationFormText, AuthorizationFormDataUse) should be managed as metadata and deployed through change management pipelines — not created manually in production. This ensures environment parity and enables regression testing of the consent gate.

## Architectural Tradeoffs

**Append-only text versioning vs. in-place update:**
Append-only is the architecturally correct choice for HIPAA compliance but requires the intake flow to always reference the current AuthorizationFormText ID. A form registry pattern (a Custom Metadata or Custom Setting that maps a logical form name to the current AuthorizationFormText ID) prevents hardcoded record IDs in flows and allows form version transitions without flow updates.

**Native Flow gate vs. Apex trigger gate:**
A before-save Record-Triggered Flow is easier to deploy and modify without code deployment but has a higher governor limit risk at scale if the consent query is not designed carefully. An Apex before-save trigger provides more control and testability but adds code maintenance overhead. For high-volume orgs (10k+ enrollments/day), Apex with a bulkified query pattern is preferred.

**Consent recordkeeping vs. sharing rule design:**
These must be designed in tandem but remain independent in implementation. The consent hierarchy answers "did the patient authorize this use?" The sharing model answers "can this user see this record?" Both questions must have affirmative answers before clinical data is accessed. Treating them as the same system is the most common architectural error in Health Cloud implementations.

## Anti-Patterns

1. **Consent-as-access-control** — Designing the system so that creating an AuthorizationFormConsent record is the only step needed to grant a care team member access to PHI. This is wrong architecturally: the consent object has no relationship to the sharing model. The result is either all care team members can see all patient records regardless of consent (if OWD is public), or no care team member can see anything (if OWD is private) — neither of which is correct. Always design sharing rules as a separate, parallel track.

2. **Single global consent form** — Creating one AuthorizationForm and one AuthorizationFormText used for all patients and all purposes, with no DataUsePurpose granularity. This collapses the hierarchy and makes it impossible to verify consent for a specific use (e.g., Research vs. Treatment) without reading the free-text form body. HIPAA authorization requires specificity of purpose; the data model must reflect that.

3. **Skipping the CareProgramEnrollee gate** — Assuming the consent records are only needed for audit purposes and that the enrollment process can proceed independently. This leaves the system in a state where enrollment can occur without documented authorization, which is a HIPAA violation risk. The gate is not optional.

## Official Sources Used

- Health Cloud Consent Management Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.health_cloud_developer.meta/health_cloud_developer/
- AuthorizationFormConsent Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_authorizationformconsent.htm
- Health Cloud Object Reference (AuthorizationForm) — https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/hco_object_authorization_form_consent.htm
- Consent Management for Health Cloud (Help) — https://help.salesforce.com/s/articleView?id=ind.hc_consent_management.htm
- Optimizing Health Cloud Consent Management (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/health-cloud-consent-management
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
