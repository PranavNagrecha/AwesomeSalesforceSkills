# Examples: Change Set Deployment

## Example 1: Validate-First + Quick Deploy for a Production Release

**Scenario:** A team needs to deploy a new custom object with fields, a flow, two Apex classes, and a permission set from a full-copy sandbox to production. The release window is Saturday midnight and the team wants the shortest possible window.

**Problem:** A deploy that includes Apex runs local tests by default in production. In a large org that can take a long time, and a failure mid-window is an incident.

**Solution:**

```text
Outbound change set "REL-2026-10 Service Tier" (source: UAT full sandbox)
  CustomObject     Service_Tier__c
  CustomField      Service_Tier__c.Tier_Level__c
  CustomField      Service_Tier__c.Effective_Date__c
  Flow             Service_Tier_Assignment
  ApexClass        ServiceTierService
  ApexClass        ServiceTierServiceTest
  PermissionSet    Service_Tier_Manager

Validation in production (Tuesday, business hours)
  Test level: Run specified tests -> ServiceTierServiceTest
  Pass condition: every deployed class and trigger >= 75% from that test

Release night (Saturday)
  Setup > Deployment Status > validated change set > Quick Deploy
  Then: activate Service_Tier_Assignment, assign Service_Tier_Manager
```

1. In the source sandbox, build the outbound change set with the components above. Decide whether the flow should arrive active (production setting) or be activated afterward.
2. Run **View/Add Dependencies**, then audit the list. Confirm page layouts, field sets, and validation rules that reference the new fields are included.
3. Upload to production.
4. During business hours, open the inbound change set in production and click **Validate** with **Run specified tests** listing `ServiceTierServiceTest`. Every deployed class must reach 75% from that test.
5. On Saturday, open Deployment Status, find the validated change set, and click **Quick Deploy**.
6. After the deploy, activate the flow if it arrived inactive and assign the permission set.

**Why it works:** Validation runs the test logic during low-risk hours. The Metadata API guide describes quick deploy of a recent validation on the Deployment Status page, valid for 10 days. The flow activation step is explicit because production deploys flows inactive by default.

---

## Example 2: Dependency Resolution for a Page Layout + Custom Field Change Set

**Scenario:** A developer adds `Account.Service_Tier__c` to the Account page layout and uploads a change set containing only the layout. Validation fails with a missing-field error. UNVERIFIED (2026-10-03): the exact error text varies by release; it names the missing field.

**Problem:** The layout references `Service_Tier__c`, but the field was not in the change set and does not exist in the target.

**Solution:**

```text
New outbound change set (the uploaded one cannot be edited in the target)
  Layout        Account-Account Layout
  CustomField   Account.Service_Tier__c      <- the missing dependency
  FieldSet      Account.Service_Summary      <- only if it references the field
```

1. In the source org, create a new outbound change set (or edit the original outbound change set before re-uploading).
2. Add **Custom Field > Account > Service_Tier__c**.
3. Add any field set or compact layout that references the new field.
4. Upload and validate again.

**Why it works:** The layout names the field API name. The deploy can't write a layout that points at a field the target schema does not have. Shipping both together satisfies the dependency in one deployment.

---

## Example 3: Auditing a Change Set That Contains Profiles

**Scenario:** An inherited change set built by a departing consultant includes the custom `Sales Manager` and `Service Agent` profiles alongside feature metadata. A senior admin must decide whether to deploy it as-is.

**Problem:** Profile settings for the components in the change set will change. On top of that, the Metadata API always includes user permissions, login IP ranges, and login hours in a profile, so production-only values in those sections can be replaced with sandbox values.

**Solution:**

```bash
# Pull the production baseline of the two profiles together with the feature object,
# so the retrieved .profile files contain the same scoped sections the deploy will carry.
sf project retrieve start --target-org prod \
  --metadata "Profile:Sales Manager" "Profile:Service Agent" \
  "CustomObject:Service_Tier__c" \
  --output-dir baseline/prod
```

1. List every Profile component in the change set.
2. Retrieve the production baseline as above and compare the user permissions, `loginIpRanges`, and `loginHours` sections with the source profiles.
3. If the delta is one object or field permission, create a permission set that grants it, remove the profiles from the change set, and re-upload.
4. If the profile deploy cannot be avoided, copy the production-only values into the source profile first, then re-upload and re-validate.

**Why it works:** The review targets the sections that actually move. A targeted permission set replaces a broad profile deploy, which is the safer default.

A package.xml mirror of a change set, for retrieving and diffing the target before upload, is in [metadata-examples.md](metadata-examples.md).

---

## Anti-Pattern: Skipping Validation to Save Time

**What practitioners do:** Under time pressure, they skip Validate and click Deploy, reasoning that the change was tested in a sandbox.

**What goes wrong:** If any test fails, the production deployment rolls back completely, and the window time is already spent. Tests also run serially in change set deployments, so the run is slower than the Developer Console suggests.

**Correct approach:** Always validate before the release window, then quick deploy. A failed validation is a finding; a failed production deploy is an incident.
