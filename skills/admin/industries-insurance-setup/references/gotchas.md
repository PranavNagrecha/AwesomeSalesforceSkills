# Gotchas — Industries Insurance Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Insurance Settings Toggles Are Permanently Irreversible

**What happens:** Enabling "Many-to-Many Policy Relationships" or "Multiple Producers Per Policy" in Setup > Insurance Settings permanently alters the org's underlying data model and junction object behavior. There is no UI toggle to reverse these settings, and Salesforce Support will not reverse them post-activation because the underlying schema changes cannot be safely undone once policy or participant data exists.

**When it occurs:** During initial org setup or when an admin is exploring Insurance Settings without a documented decision. Often discovered too late when a project is mid-delivery and the team realizes the wrong setting combination was chosen.

**How to avoid:** Treat each Insurance Settings toggle as an architectural decision, not an admin configuration. Document the participant model (how many named insureds per policy? how many producers?) before opening Insurance Settings. Have the decision reviewed and approved by the solution architect before saving. Run these decisions past the client explicitly — they have business and regulatory implications.

---

## Gotcha 2: FSC Insurance Permission Set License Is Not Included in the Base FSC License

**What happens:** Users with a full Financial Services Cloud license cannot see InsurancePolicy, InsurancePolicyCoverage, Claim, or other insurance objects, and Insurance Settings does not appear in Setup. This looks exactly like a permission or profile configuration problem, causing teams to spend hours debugging field-level security and permission sets before discovering the root cause.

**When it occurs:** When an org is provisioned with standard FSC and insurance features are assumed to be included. Also occurs when new users are added and only given the base FSC permission set license without the additional FSC Insurance permission set license.

**How to avoid:** Before any insurance configuration work, navigate to Setup > Company Information > Permission Set Licenses and confirm the FSC Insurance PSL row shows available licenses. If the row is absent, contact your Salesforce AE — it requires a separate order. Assign the PSL explicitly to each user who needs insurance object access.

---

## Gotcha 3: Managed-Package vs Native-Core Platform Path Produces Different Namespace Behavior

**What happens:** The Digital Insurance Platform is in a mid-transition from a managed package to native Salesforce core (target October 2025). On managed-package orgs, OmniStudio components like `insOsGridProductSelection` and the `InsProductService` Apex class carry managed-package namespace prefixes. On native-core orgs, these references are different. OmniScript Remote Action elements configured with the wrong class reference silently fail or throw a "Class not found" error at runtime.

**When it occurs:** When documentation, training materials, or AI-generated configuration steps mix managed-package and native-core references. Also occurs when an org migrates from managed package to native core mid-project.

**How to avoid:** At project start, confirm whether the org is on the managed-package or native-core path by checking Setup > Installed Packages for the Digital Insurance Platform package. Document the path. Use only the setup guides appropriate for that path. When Salesforce releases native-core GA guidance, plan a formal cutover rather than mixing references.

---

## Gotcha 4: Connect API Issue Policy Endpoint Requires a Complete Coverage Payload — Partial Payloads Silently Omit Coverage Records

**What happens:** When calling `POST /connect/insurance/policy-administration/policies`, if the coverage input array is incomplete or malformed, the endpoint creates the `InsurancePolicy` record successfully but silently skips creating some or all `InsurancePolicyCoverage` child records. The HTTP response is 200/201 with a policy ID, giving the impression that issuance succeeded. The missing coverage records are only discovered later when users open the policy record or when billing/renewals break.

**When it occurs:** During OmniScript development when the coverage inputs passed from the product selection step are not fully mapped. Also during testing when simplified payloads are used to "just get the policy created."

**How to avoid:** After every test policy issuance, immediately query `InsurancePolicyCoverage` records for the new policy and verify the expected count and coverage types. Add an assertion step to the OmniScript or Integration Procedure that validates coverage record creation before showing a success confirmation. Never treat a 200 response from the issue-policy endpoint as sufficient proof of complete issuance.

---

## Gotcha 5: InsurancePolicyParticipant Role Picklist Changes Affect All Existing Participant Records

**What happens:** The `InsurancePolicyParticipant.Role` field is a picklist. Removing or deactivating a picklist value does not null out existing records with that value — they retain the old value in the database but the field displays blank in the UI and the value fails validation rules that reference the picklist. This is standard Salesforce picklist behavior but is particularly dangerous here because participant role drives downstream automation, OmniScript branching, and Connect API behavior.

**When it occurs:** When the initial participant model is set up with a placeholder role like "Agent" and then the team later standardizes on "Producer." Deactivating "Agent" picklist value breaks all existing InsurancePolicyParticipant records with Role = Agent.

**How to avoid:** Finalize the Role picklist values as part of the Insurance Settings / participant model decision before creating any participant records. If a rename is required, use a Replace Picklist Values bulk operation (Setup > Object Manager > InsurancePolicyParticipant > Fields > Role > Replace) rather than deactivating the old value. Test all OmniScript branching and automation after any picklist change.
