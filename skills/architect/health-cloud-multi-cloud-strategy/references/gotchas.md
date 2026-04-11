# Gotchas — Health Cloud Multi-Cloud Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Experience Cloud for Health Cloud PSL Must Be Assigned Before the Site Goes Live — Not After

**What happens:** When an Experience Cloud site for Health Cloud is activated and external users are provisioned, the Health Cloud for Experience Cloud permission set license is not automatically applied to portal user profiles. Administrators who activate the site and then create portal users find that the site loads (the Experience Cloud framework works) but all Health Cloud-specific components — Care Plan viewer, CareProgramEnrollee FlexCards, and OmniScript-based intake forms — throw "Insufficient Privileges" errors for external users.

**When it occurs:** This catches teams in UAT when real portal users (not internal admins testing with the "View Site as" tool) attempt to access Health Cloud records. The "View Site as" tool in Experience Builder runs under the administrator's internal session and bypasses the PSL requirement. This means the site appears fully functional in Experience Builder preview but breaks for every actual external user.

**How to avoid:** Add PSL assignment verification to the go-live checklist explicitly: confirm that the Health Cloud for Experience Cloud PSL is assigned to the portal profile (or to each portal user individually) before any UAT with external test users. Use a SOQL query against PermissionSetLicenseAssign to confirm assignment counts match expected portal user counts. Never rely on the Experience Builder preview as evidence that external users will have access.

---

## Gotcha 2: PersonAccount Enablement Is Irreversible and Must Precede Health Cloud Installation in Brownfield Orgs

**What happens:** Health Cloud's patient data model is built on PersonAccount (an Account record that acts as an individual person rather than a business). If a customer's existing Salesforce org already has Account and Contact records in the standard B2B relationship model, enabling PersonAccount for Health Cloud requires a data migration. Once PersonAccount is enabled, it cannot be disabled — Salesforce Support will not reverse it. This means any existing Contacts that were not converted to PersonAccount before enabling the feature become orphaned from the new data model.

**When it occurs:** This catches brownfield implementations — orgs where the customer already uses Salesforce for non-healthcare workflows (sales pipeline, service cases for a commercial division). The commercial team's Contact records are often in standard Account-Contact relationships. Enabling PersonAccount for Health Cloud activates a separate Contact record type (PersonContact) and changes how the API handles Account-Contact relationships throughout the entire org.

**How to avoid:** Before enabling PersonAccount, conduct a full audit of all existing Account and Contact records and all Apex, Flow, and integration code that references Contact. Develop a migration plan that converts relevant Contacts to PersonAccount format. Validate in a full-copy sandbox first. If the existing org cannot be migrated cleanly, evaluate whether Health Cloud should be deployed in a new dedicated org rather than the existing brownfield org.

---

## Gotcha 3: OmniStudio DataRaptor Errors on Health Cloud Objects Are Not Permission Errors — They Are Empty Results

**What happens:** When a user is missing the Health Cloud Platform PSL (but has the base Health Cloud PSL and the OmniStudio User PSL), DataRaptor Extract steps that query Health Cloud-specific objects (EpisodeOfCare, CarePlan, ClinicalEncounter, CareProgramEnrollee) return zero records rather than throwing a permission exception. The OmniScript UI displays a step with no data populated, or a "No records found" message. Debugging is difficult because the same user CAN see those records on a standard record page — the base Health Cloud PSL grants read visibility in standard UI, but not CRUD through the OmniStudio runtime execution context.

**When it occurs:** This surfaces when OmniStudio is rolled out to a new user group that was set up before OmniStudio was added to the implementation scope, so PSL assignments were done in two batches and the Health Cloud Platform PSL was overlooked in the second batch. It also occurs when a new care coordinator is onboarded and the provisioning runbook does not list all three required PSLs.

**How to avoid:** Create a single permission set group that bundles all three PSLs (Health Cloud, Health Cloud Platform, OmniStudio User) and assign the group rather than the three PSLs individually. This eliminates the partial-assignment failure mode. Document the three-PSL requirement prominently in the user provisioning runbook and in the org's internal architecture documentation.

---

## Gotcha 4: Marketing Cloud Health Cloud Connect Sync Errors Surface in Marketing Cloud — Not in Salesforce Setup Logs

**What happens:** When the Marketing Cloud Health Cloud Connect integration is misconfigured (wrong Connected App credentials, expired OAuth token, or missing field mapping), the Salesforce Health Cloud org does not log any errors in Setup > Debug Logs or in the standard Event Log. The failure is logged only in Marketing Cloud's Synchronization Dashboard (within the Connected App configuration in Marketing Cloud Setup). Teams that only monitor Salesforce-side logs will conclude the sync is working when it is silently failing.

**When it occurs:** This catches teams immediately after go-live when Marketing Cloud journeys that depend on Health Cloud data (care program enrollment triggers, appointment reminders) never fire. The Salesforce org appears healthy. The issue is diagnosed only when someone checks the Marketing Cloud Synchronization Dashboard and sees failed sync runs.

**How to avoid:** Include Marketing Cloud Synchronization Dashboard monitoring in the post-go-live runbook. Set up Marketing Cloud's built-in sync failure email alerts to notify the integration operations team. Test the end-to-end sync in a connected sandbox environment — not just unit-test the Salesforce side — before go-live. Confirm that the Connected App in the Health Cloud org and the corresponding credentials in Marketing Cloud Setup are using the same client ID and secret.

---

## Gotcha 5: Sharing Sets for Experience Cloud Portal Users Do Not Reach All Health Cloud Object Relationships

**What happens:** Sharing Sets are the standard mechanism for giving Experience Cloud portal users (external users) access to Salesforce records they "own" via a lookup field. For Health Cloud portal sites, architects design Sharing Sets based on the assumption that all relevant patient records are reachable from the patient's PersonAccount. In practice, several Health Cloud objects — including CarePlanTemplate, some ClinicalEncounter relationship objects, and ConsumptionSchedule records — are not directly related to PersonAccount via a simple lookup and therefore cannot be reached by Sharing Sets alone.

**When it occurs:** This surfaces in UAT when patients using the portal can see their CareProgramEnrollee and active CarePlan records (which are reachable via Sharing Sets) but cannot access supplementary clinical documents or template-based care plan content that the implementation team expected them to see.

**How to avoid:** During the portal access model design phase, map every object that portal users must access and trace the relationship path back to PersonAccount. For any object that is not directly reachable via a lookup from PersonAccount, evaluate: (1) Apex managed sharing (programmatic sharing via the share object), (2) a criteria-based sharing rule on the object, or (3) a Guest User-accessible custom object wrapper. Do not finalize the portal security model without testing every object in the access matrix with an actual external Community user — not an internal admin using "View Site as."
