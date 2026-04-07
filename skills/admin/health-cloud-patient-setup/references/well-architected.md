# Well-Architected Notes — Health Cloud Patient Setup

## Relevant Pillars

### Security

Patient data is Protected Health Information (PHI) under HIPAA. The patient setup process must establish correct access controls from the start:

- Health Cloud permission sets (HealthCloudFoundation, HealthCloudSocialDeterminants, HealthCloudMHSUD) must be assigned to user profiles based on clinical role, not granted broadly.
- Field-level security on clinical fields (diagnoses, medications, mental health data) must be configured so that only authorized roles can view or edit sensitive data.
- Person Account records that represent patients must have sharing settings reviewed: overly permissive OWD settings (e.g., Public Read/Write on Account) expose PHI to all internal users.
- Audit trail must be enabled and regularly reviewed for access to clinical records.

### Reliability

Person Account enablement is an irreversible, org-wide change. Any reliability failure during this step — partial configuration, missed record type assignment, or broken page layout assignment — results in patient records that lack Health Cloud components. Reliability best practices:

- Perform all configuration in sandbox with full regression testing before production enablement.
- Use change sets or metadata API deployments to migrate record type and page layout configurations, not manual clicks in production.
- Validate with a post-deployment smoke test using a test patient record.
- Document the exact sequence of configuration steps so the process can be reproduced in disaster recovery scenarios.

### Operational Excellence

Patient setup establishes the foundation for all downstream Health Cloud work (care plans, clinical programs, interoperability). Operational excellence requires:

- Clear documentation of which record types exist, which profiles have access, and which permission sets are required.
- Configuration managed via metadata (record types, page layouts, custom settings) so it can be version-controlled and peer-reviewed.
- Health Cloud Settings configurations (care team roles, Patient Card fields) exported and documented — these are not automatically captured by standard change sets.
- Post-setup runbook that clinical administrators can execute without developer assistance to add new care team roles or update Patient Card fields.

## Architectural Tradeoffs

**Person Accounts vs. Custom Patient Object:** Health Cloud requires Person Accounts for its clinical components. Some organizations resist enabling Person Accounts because of the irreversibility and impact on existing B2B Account/Contact architecture. The only correct path for Health Cloud is Person Accounts — custom patient objects forfeit the entire Health Cloud clinical UI layer. The tradeoff is accepting the irreversible org change in exchange for the full Health Cloud feature set.

**FHIR Clinical Objects vs. Custom Fields:** Storing clinical data in Health Cloud clinical objects (EhrPatientMedication, PatientHealthCondition) requires understanding a more complex data model and integration pattern. The benefit is that all Health Cloud components — Patient Card, Timeline, Care Gap Detection, Population Health — natively read from these objects. Custom fields on Account are simpler to create but invisible to every Health Cloud clinical component.

**Managed Package Page Layouts vs. Custom Layouts:** Health Cloud ships with patient page layouts. Organizations can clone and customize these layouts, but heavily customized layouts diverge from the managed package and require ongoing maintenance during Health Cloud upgrades. The tradeoff is customization flexibility vs. upgrade compatibility.

## Anti-Patterns

1. **Enabling Person Accounts in Production Without Sandbox Testing** — Person Account enablement changes the org-wide Account/Contact model permanently. Enabling in production without sandbox regression testing risks breaking existing Account/Contact automation, integrations, and reports with no rollback path. Always test in sandbox first, run full regression, and get explicit sign-off from integration partners before enabling in production.

2. **Storing Clinical Data in Custom Account Fields** — Building a shadow clinical data model with custom Account or Contact fields instead of using Health Cloud clinical objects (EhrPatientMedication, PatientHealthCondition, etc.) creates technical debt that is invisible to every Health Cloud clinical component. Care Plans, the Patient Card, the Timeline, and Population Health analytics all depend on the standard Health Cloud object model. Custom field workarounds prevent adoption of these capabilities and compound maintenance costs with each Health Cloud release.

3. **Skipping Permission Set Configuration After Record Type Setup** — Creating the patient record type and page layout without assigning Health Cloud permission sets to clinical user profiles results in users who can see the patient record but cannot interact with clinical components (care teams, care plans, clinical data). Permission set assignment is a required post-setup step that is frequently overlooked when implementations focus on the record type creation and miss the access layer.

## Official Sources Used

- Health Cloud Administration Guide — https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/
- Health Cloud Administration: Set Up Person Accounts for Health Cloud Members and Patients — https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/admin_set_up_person_accounts.htm
- Health Cloud Administration: Customize Medical Data on the Patient Card Component — https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/admin_customize_patient_card.htm
- Health Cloud Administration: Create Roles for Care Team Members — https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/admin_care_team_roles.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Object Reference: Account — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_account.htm
