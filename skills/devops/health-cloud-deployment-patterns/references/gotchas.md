# Gotchas — Health Cloud Deployment Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in Health Cloud deployments.

## Gotcha 1: CarePlanProcessorCallback Registration Is Not Captured in Any Deployable Artifact

**What happens:** After deploying the `CarePlanProcessorCallback` Apex class to a new org, the Care Plan wizard either silently skips post-processing or throws errors. Checking Installed Packages, permission sets, and class deployment all look correct. The missing step is the callback registration in Health Cloud Setup, which writes to a Custom Metadata record in the `HealthCloudGA` namespace and is therefore not retrievable via `sf project retrieve`.

**When it occurs:** Every deployment to a new org and every sandbox refresh. The class is deployed correctly but the Setup registration must be performed manually every time. Teams that rely solely on CI/CD pipelines without an accompanying post-deploy runbook will miss this step on every environment rebuild.

**How to avoid:** Add "Register CarePlanProcessorCallback in Setup > Health Cloud Setup > Care Plan Settings" as a mandatory, non-skippable step in your deployment runbook. Consider adding a post-deploy validation that queries the underlying Custom Metadata record to confirm registration: `SELECT Id, HealthCloudGA__ClassName__c FROM HealthCloudGA__CarePlanProcessorSetting__mdt`.

---

## Gotcha 2: Care Plan Templates Silently Malform When Created via Direct DML

**What happens:** An Apex script or data migration tool inserts records directly into `HealthCloudGA__CarePlanTemplate__c` and its child objects. The records appear in SOQL queries and the org's data, but the Care Plan wizard does not display them or produces errors when they are selected. The template entries and goals are either missing associations or have incorrect field values that the wizard requires.

**When it occurs:** Any time a developer or data migration engineer treats `CarePlanTemplate__c` like a standard custom object and bypasses the `HealthCloud.CreateCarePlanTemplate` invocable action. This often happens during sandbox seeding, data migration from legacy systems, or when a developer assumes standard DML will work because the object exists and they have field-level access.

**How to avoid:** Always use the `HealthCloud.CreateCarePlanTemplate` invocable action to create care plan templates, either through the Setup UI (Health Cloud > Care Plan Templates) or through an Apex invocable action call. Never insert into `CarePlanTemplate__c` directly, even in anonymous Apex. Add this to your pre-deploy checklist as a validation step: check that care plan templates in the target org respond correctly in the Care Plan wizard, not just that the records exist in SOQL.

---

## Gotcha 3: Permission Set License Must Be Assigned Before the Permission Set or Runtime Errors Are Silent

**What happens:** A user receives a permission set that grants access to Health Cloud objects. The permission set deploys without error. The user logs in and navigates to a Health Cloud list view or record page and receives "insufficient privileges" with no further explanation. The permission set is correctly assigned and the field/object permissions are visible in Setup — but the user still cannot access the records.

**When it occurs:** The user does not have a Health Cloud Permission Set License (PSL) assigned. PSL assignment is a prerequisite for the permission set to function at runtime, but it is a separate operation from permission set assignment. A user can have the permission set without the PSL, and the system does not warn you at assignment time. This is especially common after sandbox refreshes (PSLs are wiped) and after onboarding new users who receive permission sets from a group assignment but whose PSL was not included in the group provisioning script.

**How to avoid:** Always verify PSL assignment before assigning Health Cloud permission sets to users. Include PSL verification in your post-deploy validation. If using Salesforce Flow or a setup script to assign permission sets in bulk, add a step that also assigns the PSL. Query `UserPackageLicense` with the appropriate `PackageLicense.NamespacePrefix = 'HealthCloudGA'` filter to audit who has the PSL.

---

## Gotcha 4: Sandbox Refresh Wipes HealthCloudGA Package and All Configuration State

**What happens:** After a full sandbox refresh from production, the sandbox appears to have all org-specific metadata (custom objects, flows, Apex classes are all present), but every Health Cloud feature is broken. Care plan templates are gone. The Care Plan wizard fails. Several users have "insufficient privileges" errors. The managed package shows as not installed in Setup > Installed Packages.

**When it occurs:** Full sandbox refreshes do not preserve managed package installations. The sandbox is rebuilt from a production org snapshot that includes the data and org-specific metadata, but the managed package installation, PSL assignments, and Health Cloud Setup configuration (including CarePlanProcessorCallback registration) must be reinstated after every refresh. This is a Salesforce sandbox architecture behavior — sandbox refresh preserves what is in your org's metadata, not what was installed from AppExchange.

**How to avoid:** Maintain a post-refresh setup script or runbook that covers: (1) reinstall HealthCloudGA and all feature packages at the same version as production, (2) reassign PSLs to test users, (3) re-register CarePlanProcessorCallback in Care Plan Settings, (4) recreate care plan templates via invocable actions, (5) verify Shield Encryption policies are active. Treat sandbox refresh as equivalent to a greenfield deployment for all package-dependent configuration.

---

## Gotcha 5: Shield Encryption Does Not Retroactively Encrypt Existing Records

**What happens:** A team configures Shield Platform Encryption policies after importing a test dataset that contains mock PHI. They discover that the test records are not encrypted — querying the encrypted fields via the API or data export returns plaintext values. The encryption policy only applies to records written after the policy was activated.

**When it occurs:** Whenever Shield Platform Encryption is configured after data is already in the org. This is common during UAT when teams import test data to configure and verify the encryption setup, not realizing that the verification data itself is stored unencrypted.

**How to avoid:** Activate Shield Platform Encryption and confirm all encryption policies are live before any PHI (or PHI-shaped test data) is imported into the org. If data is already present, the remediation options are: delete and re-import the data after encryption is active, or engage Salesforce Support for a bulk encryption operation (not available as a self-service feature). Document this sequencing requirement in your go-live runbook as a hard dependency: "Encryption policy active" must precede "data import begins."

---

## Gotcha 6: Scratch Org Support for Health Cloud Is Limited and Requires Explicit Feature Declaration

**What happens:** A developer creates a scratch org without declaring Health Cloud features in the scratch org definition file. The HealthCloudGA namespace is not available, and metadata that references Health Cloud objects or fields fails to deploy to the scratch org. Even when the package is installed post-creation, some Health Cloud Setup features (including Care Plan Settings) may not render correctly in scratch orgs.

**When it occurs:** Development teams that use scratch orgs for standard Salesforce development try to apply the same workflow to Health Cloud. Health Cloud scratch org support is more limited than full sandbox support — some configuration UI sections do not appear, and some invocable actions behave differently.

**How to avoid:** Use developer sandboxes or full sandboxes (not scratch orgs) as the primary Health Cloud development environment. If scratch orgs are required for CI testing, declare all required Health Cloud features in `project-scratch-def.json` and install the HealthCloudGA package immediately after org creation. Document which aspects of Health Cloud Setup are not available in scratch orgs and plan for those to be validated only in sandbox environments.
