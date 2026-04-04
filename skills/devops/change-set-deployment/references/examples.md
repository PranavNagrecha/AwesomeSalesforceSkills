# Examples — Change Set Deployment

## Example 1: Validate-First + Quick Deploy for a Production Release

**Scenario:** A team needs to deploy a new custom object with fields, a Flow, two Apex classes, and a permission set from a full-copy sandbox to production. The production release window is Saturday midnight and the team wants to minimize downtime.

**Problem:** Deploying Apex to production triggers a full test run by default, which can take 30–90 minutes for large orgs. Running the deploy live during the window is risky if any test fails mid-run.

**Solution:**

1. In the source sandbox, build the outbound change set. Include: the custom object, all custom fields, the Flow (check whether it should arrive active or inactive), both Apex classes, their test classes, and the permission set.
2. Use "Add Dependencies" then manually audit the component list — confirm page layouts, field sets, and validation rules referencing the new fields are included.
3. Upload to production.
4. During business hours (not in the release window): open the inbound change set in production and click **Validate**. Choose **Run specified tests** and list both test classes. Confirm validation passes and code coverage is above 75%.
5. On Saturday: open Deployment Status, find the validated change set, and click **Quick Deploy**. Because tests were already run, quick deploy completes in minutes — typically under 5 minutes for a change set of this size.
6. Post-deploy: activate the Flow manually (Setup > Flows > find the Flow > Activate). Assign the permission set to the relevant users or public group.

**Why it works:** Validation runs all test logic during low-risk business hours. Quick Deploy (available for 10 days after a passing validation) applies the metadata without re-running tests, compressing the production window to near-zero. The Flow activation step is explicit and deliberate rather than automatic. Per Salesforce documentation, a change set validated with at least the required test coverage qualifies for Quick Deploy (see: help.salesforce.com — Deploy a Change Set).

---

## Example 2: Dependency Resolution for a Page Layout + Custom Field Change Set

**Scenario:** A developer adds a new custom field `Account.Service_Tier__c` to the Account page layout and creates an outbound change set with just the page layout. Validation fails with: `No such column 'Service_Tier__c' on entity 'Account'`.

**Problem:** The page layout metadata references `Service_Tier__c` but the custom field itself was not added to the change set. The target org has no record of this field. The platform cannot deploy a layout that references a field it cannot resolve.

**Solution:**

1. Return to the source org's outbound change set (it is now locked as an inbound in the target — create a new outbound change set or edit the existing one before upload).
2. Add **Custom Field > Account > Service_Tier__c** to the change set.
3. Also add the **Field Set** if any field set on Account references the new field, and the **Compact Layout** if applicable.
4. Re-upload to the target org.
5. Re-validate. Confirm the error is gone.

**Why it works:** Change sets enforce complete dependency resolution at deploy time. The layout XML explicitly names the field API name; if the field does not exist in the org's schema, the deploy cannot write the layout. Adding the field to the same change set ensures both components land together atomically. Per the Salesforce Metadata API Developer Guide, component dependencies must be satisfied in the target org or within the same deployment for the deploy to succeed.

---

## Example 3: Auditing a Change Set for Profile Overwrite Risk

**Scenario:** An inherited change set built by a departing consultant includes `Admin` and `Standard User` profiles alongside the feature metadata. A senior admin needs to decide whether to deploy it as-is.

**Problem:** Profile metadata in a change set is a full-replace operation. If the source sandbox Admin profile has fewer custom app assignments or different field-level security settings than the production Admin profile (which has been customized over years), deploying it will silently remove those production-only customizations.

**Solution:**

1. Download the change set component list and identify all Profile metadata types included.
2. Compare source and target profile XML using the Metadata API retrieve or Salesforce CLI (`sf project retrieve start --metadata Profile:Admin`) to get the production baseline.
3. Decision: if the delta is just one FLS setting or one object permission, create a permission set that grants the same access and add it instead of the profile. Remove the profiles from the change set.
4. If the profile deploy truly cannot be avoided, merge the production-specific sections back into the source profile, re-add to the change set, re-upload, and re-validate.

**Why it works:** Profiles are one of the metadata types with the highest overwrite risk in change sets because the UI does not show you a diff. Replacing a profile deploy with a targeted permission set deploy is the safest pattern. Per Salesforce Help (Change Sets Best Practices), avoid deploying full profiles when more granular options exist.

---

## Anti-Pattern: Skipping Validation to Save Time

**What practitioners do:** Under time pressure, skip Validate and click Deploy directly — reasoning that "we tested this in sandbox, it will be fine."

**What goes wrong:** If any test fails, Salesforce rolls back the entire deployment — but the time is already spent. Worse, if the failure involves an Apex compilation error, the deploy may leave a partial state in the Deployment Status log that misleads the next attempt. In large orgs, a failed production deploy with a full test run may consume 30–60 minutes before rolling back.

**Correct approach:** Always validate before the production release window. Use the 10-day quick deploy window as the deployment vehicle. Validation failures are learning opportunities; deploy failures are production incidents.
