# Gotchas — Org Edition and Feature Licensing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Feature Availability Can Change Between Releases Without Notice

Salesforce moves features between edition tiers and add-on bundles with each seasonal release. A feature that required an add-on in Winter '25 may be included in a base edition in Spring '25, or vice versa. Cached edition comparison tables (including those trained into LLMs) can be out of date by 6–12+ months.

**Fix:** Always verify current feature availability from the Salesforce edition comparison page at https://www.salesforce.com/editions-pricing/overview/ for the current release, not from documentation that was accurate at a prior release.

---

## Gotcha 2: Permission Set Licenses Must Be Assigned Per User Even When Org License Is Active

Add-on features provisioned as Permission Set Licenses (PSLs) are assigned at the org level (enabling the feature for the org) and separately at the user level (enabling the feature for a specific user). An org may have an active Einstein or Agentforce PSL, but if it has not been assigned to a specific user, that user cannot access the feature — and the error is often a generic "feature not available" message rather than a clear "license not assigned" error.

**Fix:** When a feature works for one user but not another: check Setup > Users > [User] > Permission Set License Assignments. Assign the relevant PSL to the affected user.

---

## Gotcha 3: Developer Edition Is Enterprise-Equivalent But Not a Free Production Tier

Many developers and ISV partners build on Developer Edition orgs and assume the feature set matches what customers have. Developer Edition has Enterprise-equivalent features for development purposes — but customers on Professional or Essentials editions will not have access to Apex triggers, full sandbox environments, or other Enterprise features that work fine in the developer's DE org.

**Fix:** When designing for a customer, always build and test against an org edition that matches the customer's edition, not a Developer Edition. Use edition-appropriate scratch org definitions in sfdx if testing across editions.

---

## Gotcha 4: Sandbox Type Availability Is Edition-Dependent

Full Sandboxes are not available in Professional Edition. Partial Copy Sandboxes are not available in Professional Edition. Many implementation teams assume "we have sandboxes" without realizing that Professional Edition only includes Developer Sandboxes — which do not support full data copies or production-volume testing.

This often surfaces during UAT when the customer cannot create a Full Sandbox for production data testing and learns they need an Enterprise Edition upgrade or a Full Sandbox add-on purchase.

**Fix:** Confirm sandbox type requirements early in project scoping. If production-data testing is a requirement, confirm the org edition and sandbox type availability before signing off on the implementation approach.

---

## Gotcha 5: Some Features Are On by Default in Newer Orgs but Off in Older Orgs

Salesforce enables some new features by default in new orgs provisioned after a certain release, but does not auto-enable them in existing orgs provisioned before that release. An existing Enterprise org provisioned in 2019 may be missing a feature that a new Enterprise org provisioned today has enabled — not because of edition differences, but because of org provisioning date and auto-enablement timing.

**Fix:** If a feature is available in the org's edition but cannot be found in Setup: check Salesforce Release Notes for the feature to find whether it was auto-enabled for new orgs only, and look for the manual enable toggle in Setup. Contact Salesforce Support if the enable option is missing entirely from Setup.
