# Well-Architected Notes — Health Cloud Deployment Patterns

## Relevant Pillars

- **Security** — HIPAA compliance is the dominant security concern. A signed BAA with Salesforce is a contractual prerequisite for PHI storage. Shield Platform Encryption must be configured on clinical fields before any PHI is imported. Debug log access must be restricted in production to prevent PHI exposure in log output. Integration users and connected apps must be reviewed for minimal privilege and PHI data access scope. Every deployment runbook must include a security checklist that addresses these controls explicitly.

- **Reliability** — Health Cloud deployments have multiple manual post-deploy steps (CarePlanProcessorCallback registration, care plan template creation, PSL assignment) that are outside the control of standard CI/CD pipelines. Reliability depends on explicit, tested runbooks that cover these steps. Sandbox refresh scenarios must be treated as equivalent to fresh deployments for reliability testing. Post-deploy validation steps (Care Plan wizard smoke test, PSL audit, encryption policy verification) are reliability gates, not optional nice-to-haves.

- **Operational Excellence** — The strict managed package installation sequence, the invisible nature of post-deploy configuration steps, and the limitations of care plan template metadata all create operational risk if the deployment process is not thoroughly documented and rehearsed. Runbooks must be kept current with each Health Cloud version upgrade, as package versions change and new post-deploy steps may be introduced. Teams should automate what can be automated (package installs, metadata deploy) and document what cannot (callback registration, template creation) with enough specificity that any team member can execute the steps without prior context.

## Architectural Tradeoffs

**Managed Package vs. Unlocked Package for Org-Specific Customizations**

Health Cloud org-specific customizations (custom Apex, flows, custom objects, LWC) can be delivered via change sets or unlocked packages. Unlocked packages support version pinning, dependency declaration, and automated install via `sf package install`, making them the preferred choice for teams with CI/CD pipelines. Change sets are acceptable for simple one-off configuration, but they have no dependency management and cannot declare their relationship to the HealthCloudGA package version — meaning deployments are more error-prone.

The tradeoff: unlocked packages require more upfront investment in package architecture but significantly reduce deployment risk for ongoing development. Change sets are lower friction for initial delivery but accumulate technical debt that complicates future Health Cloud version upgrades.

**Full Sandbox vs. Scratch Org for Health Cloud Development**

Scratch orgs offer faster provisioning and better isolation for standard Salesforce development. However, Health Cloud scratch org support is more limited: some Care Plan Setup UI sections do not render, and certain invocable actions behave differently. Full sandboxes, while slower to provision and shared, provide the most accurate reflection of production Health Cloud behavior.

The tradeoff: scratch orgs are appropriate for unit-testable Apex and LWC components that do not depend on Health Cloud Setup configuration. Full sandboxes are required for any end-to-end Care Plan template, callback registration, or HIPAA configuration testing.

## Anti-Patterns

1. **Treating Health Cloud Deployment as a Standard Metadata Deploy** — Assuming `sf project deploy start` is sufficient to deploy Health Cloud, without accounting for managed package installation order, PSL assignment, callback registration, and care plan template creation. This produces a partially functional org with no clear error messages indicating what is missing. The correct approach is the sequential package-then-metadata-then-post-deploy-checklist pattern documented in this skill.

2. **Configuring Shield Encryption After PHI Import** — Enabling Shield Platform Encryption after data is already in the org and assuming existing records are now protected. Encryption policies apply only to new writes; existing records remain plaintext until deleted and re-imported or until Salesforce Support performs a bulk encryption operation. The correct approach is to activate encryption policies before any PHI is imported.

3. **Omitting Post-Deploy Runbook Steps from CI/CD Pipeline Validation** — Building a CI/CD pipeline that validates the metadata deploy but does not check whether the CarePlanProcessorCallback is registered, PSLs are assigned, and care plan templates exist. The pipeline passes green but the org is in a broken state. The correct approach is to include post-deploy smoke tests (Care Plan wizard test, PSL audit query, encrypted field verification) as pipeline gates, even if those tests are run manually.

## Official Sources Used

- Health Cloud Administration Guide: Install Health Cloud Packages — https://help.salesforce.com/s/articleView?id=sf.admin_install_package.htm
- Health Cloud Administration Guide: Create a Care Plan Template — https://help.salesforce.com/s/articleView?id=sf.admin_care_template_config.htm
- Health Cloud Administration Guide: Assign Permission Sets — https://help.salesforce.com/s/articleView?id=sf.admin_permissionset_licenses_assign.htm
- Health Cloud Custom Metadata Types — https://help.salesforce.com/s/articleView?id=sf.hc_mdt_overview.htm
- Health Cloud Managed Package Data Model — https://help.salesforce.com/s/articleView?id=sf.hc_managed_package_data_model.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Shield Platform Encryption Implementation Guide — https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/security_pe_overview.htm
- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/well-architected/trusted/
