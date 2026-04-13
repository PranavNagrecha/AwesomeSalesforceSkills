# Gotchas — FSC Deployment Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Person Account Enablement Cannot Be Automated and Is Irreversible

**What happens:** When a CI/CD pipeline attempts to deploy FSC household record types, Relationship Group metadata, or Financial Account layouts to an org where Person Accounts have not been enabled, the deployment fails with a metadata entity reference error. The error message identifies the failing component (e.g., `RecordType:Account.Household`) but does not state that the root cause is a missing org-level configuration.

**When it occurs:** Any time a managed-package FSC or Core FSC metadata package is deployed to a net-new sandbox, scratch org (without `"isPersonAccountEnabled": true` in the scratch org definition), or any org where the Person Accounts feature has not been manually enabled.

**How to avoid:** Gate every FSC deployment pipeline on a pre-flight Person Account check. Add a step before any metadata deployment that queries `SELECT Id, DeveloperName FROM RecordType WHERE SObjectType = 'Account' AND DeveloperName = 'PersonAccount'` against the target org. If the query returns zero rows, halt the pipeline and surface an actionable error message: "Person Accounts must be enabled in Setup before FSC metadata can be deployed." For scratch orgs, add `"features": ["PersonAccounts"]` and `"settings": {"personAccountSettings": {"enablePersonAccounts": true}}` to the scratch org definition file. For persistent sandboxes and production, Person Account enablement requires a manual Setup toggle and is not reversible — plan org provisioning accordingly.

---

## Gotcha 2: IndustriesSettings Does Not Backfill CDS Share-Table Rows for Existing Records

**What happens:** Deploying `IndustriesSettings` metadata to activate Compliant Data Sharing succeeds with no errors. Participant Role assignments made after the deployment correctly populate the share table (`FinancialAccountShare` or equivalent). But Financial Account records that existed in the org before CDS was activated have no share-table entries, even if Participant Roles were assigned to those records before activation. Relationship Managers lose visibility to pre-existing client accounts.

**When it occurs:** Any time CDS is activated via a metadata deployment on an org that already contains Financial Account records. This is the most common scenario in production promotions, where the sandbox already had test data when CDS was first enabled, and the pattern was never caught because sandbox data volume was low enough that all records were re-created after CDS was turned on.

**How to avoid:** After every `IndustriesSettings` deployment that activates CDS, explicitly run a sharing recalculation. In managed-package FSC, execute the `FinServ.FinancialAccountShareRecalcBatch` Apex batch. In platform-native Core FSC, use the Sharing Settings recalculation mechanism for the Financial Account object. Add a post-deploy validation step to the pipeline that queries the share table and confirms rows exist for a known set of test records before marking the deployment complete.

---

## Gotcha 3: Namespace Mismatch Between Managed-Package and Core FSC Is Not Flagged at Deploy Time

**What happens:** The sf CLI and Metadata API do not warn when a metadata component's API name uses a namespace (`FinServ__`) that does not exist in the target org. The deployment fails with a generic "Component not found" or "Invalid fullName" error for each affected component. Because the errors appear at the component level rather than the system level, practitioners typically diagnose this as a missing dependency, wrong API version, or missing installed package — not as a namespace model incompatibility.

**When it occurs:** When a deployment package built for a managed-package FSC org is applied to a platform-native Core FSC org, or vice versa. Common triggers: org refresh that changes the FSC model, multi-org pipeline where different stages use different FSC models, or a new developer org provisioned with Core FSC while the team's pipeline was built against managed-package FSC.

**How to avoid:** Run a namespace audit before the first deployment to any new target org. Script a scan of all metadata XML in the package for `FinServ__` occurrences (see `scripts/check_fsc_deployment_patterns.py`). If the audit finds `FinServ__` API names but the target is a platform-native Core FSC org (confirmed by querying for `FinancialAccount` as a standard object type), a rewrite is required before deployment. Document which FSC model each org in the pipeline uses and enforce this as a pipeline prerequisite check.

---

## Gotcha 4: Participant Role Custom Metadata Deploys Successfully With Broken Cross-References

**What happens:** Participant Role custom metadata records reference Account record type developer names to map roles to record types. If the record type developer name in the custom metadata does not exactly match the developer name in the target org (e.g., because the record type was renamed during a migration, or because managed-package vs. platform-native naming differs), the custom metadata deploys without any error. At runtime, the CDS engine silently ignores Participant Role records whose record type references do not resolve — resulting in no share-table rows being written for that record type, and no access being granted to users via that role.

**When it occurs:** After a record type rename, after a namespace migration, or when deploying custom metadata built in one org to a target where record type developer names differ. The silence of the deploy tool makes this particularly dangerous — there is no deploy-time validation of custom metadata cross-references.

**How to avoid:** After deploying Participant Role custom metadata, query the target org for all Account record types and compare their developer names against the references in the deployed custom metadata records. Test each Participant Role by assigning it to a test Financial Account and confirming a share-table row is written for the expected user or group. Add this validation as a post-deploy automated check in the pipeline.

---

## Gotcha 5: OWD Changes Trigger a Platform-Level Sharing Recalculation That Can Take Hours in Large Orgs

**What happens:** Setting Account, Opportunity, or Financial Deal OWDs to Private as a prerequisite for CDS is correct, but in production orgs with millions of records, the platform-triggered sharing recalculation job can take several hours to complete. During this period, users may experience intermittent or incorrect record visibility. If the FSC metadata deployment proceeds during or before the recalculation completes, the share-table state is indeterminate and CDS validation results are unreliable.

**When it occurs:** In any org with significant data volume whenever OWD settings are tightened as part of the FSC CDS enablement sequence. Large financial services orgs with millions of Account records are most at risk.

**How to avoid:** Schedule OWD changes during a maintenance window. Monitor the sharing recalculation job via Setup > Sharing Settings or by querying the `BackgroundOperation` object. Do not proceed with the `IndustriesSettings` deployment or any CDS metadata deployment until the recalculation is confirmed complete. In the deployment runbook, add an explicit gate: "Wait for sharing recalculation to complete (monitor via Setup > Background Jobs) before proceeding to Phase 2."
