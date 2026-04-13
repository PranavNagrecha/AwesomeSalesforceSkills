# Examples — Deployment Risk Assessment

## Example 1: Permissions Release Deployed Without Pre-Retrieve Backup

**Context:** A team needs to deploy an updated PermissionSet that adds field-level security access to a financial data object. The release is done via SFDX CLI deploy directly to production. The team has validated in a Full sandbox but did not capture the current production PermissionSet XML before opening the deployment window.

**Problem:** The deployment succeeds but the PermissionSet inadvertently grants access to a field that was previously restricted due to a profile-level override the team did not know existed. Within 30 minutes the team identifies the error and decides to roll back. There is no pre-retrieve backup of the prior PermissionSet XML. The team must reconstruct the prior XML from memory and from a partial sandbox capture that does not reflect production reality. The rollback takes 4 hours instead of 15 minutes.

**Solution:**

```bash
# Before opening ANY production deployment window, capture the current state of
# all components that will be overwritten. This is the rollback artifact.

# Retrieve the specific PermissionSet that will be modified
sf project retrieve start \
  --metadata "PermissionSet:Financial_Data_Viewer" \
  --target-org production \
  --output-dir .rollback-backup/$(date +%Y-%m-%d)

# Confirm the retrieved XML matches what is actually in production
# Store the backup path in the release runbook with the timestamp
echo "Backup captured at .rollback-backup/$(date +%Y-%m-%d)" >> release-runbook.md
```

**Why it works:** The pre-retrieve backup creates a deployable artifact of the exact prior state. If rollback is needed, the team re-deploys the backed-up XML in the same way the forward deployment was done — no reconstruction required and no dependence on sandbox state.

---

## Example 2: HIGH-Risk Flow Deployed Without a Feature Flag Gate

**Context:** An operations team deploys a new version of a Record-Triggered Flow on the Opportunity object. The flow runs on every Opportunity update and changes how close date validation works. The change was validated in a sandbox but the sandbox data volume is 1% of production. No feature flag was used.

**Problem:** In production, the flow fires on a bulk import of 50,000 Opportunity records. The new close date validation logic throws an unhandled exception at scale, causing the import job to fail and leaving 30,000 records in an intermediate state. Rolling back requires re-deploying the prior Flow version (which the team has in source control) but the 30,000 partially processed records require manual data cleanup regardless.

**Solution:**

```xml
<!-- Deploy the new flow logic behind a Custom Permission gate.
     The flow checks the permission before executing the new validation path. -->

<!-- In the Flow: add a Decision element at the start -->
<!-- Condition: $Permission.Enable_New_Close_Date_Validation == true -->
<!-- If false: take the existing path (old behavior) -->
<!-- If true: take the new validation path -->

<!-- Custom Permission XML (deploy alongside the Flow) -->
<?xml version="1.0" encoding="UTF-8"?>
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Enables the new close date validation logic in the Opportunity flow</description>
    <isLicensed>false</isLicensed>
    <label>Enable New Close Date Validation</label>
</CustomPermission>
```

**Why it works:** The flow is deployed to production in the off state. Activation (granting the Custom Permission to a PermissionSet) is a separate, low-risk metadata update. If the new logic causes problems in production, rollback is a single Custom Metadata update to disable the permission — no flow re-deployment required, and the change takes effect immediately without a deployment window.

---

## Anti-Pattern: Treating "Roll Back If Needed" as a Rollback Plan

**What practitioners do:** Include a line in the release notes that says "If issues are found, we will roll back" without specifying observable trigger conditions, who has authority to make the call, or what the rollback procedure is.

**What goes wrong:** During the production incident, three things fail simultaneously: the team cannot agree on whether the symptoms are bad enough to trigger rollback (no agreed threshold), the person who knows the rollback procedure is not reachable (no alternate named), and the rollback itself takes longer than expected because the procedure was never rehearsed. The outage extends from 30 minutes to 3 hours.

**Correct approach:** Before the window opens, document: (1) the exact observable conditions that trigger a rollback call, for example error rate in the Apex debug log exceeds 5% on the affected object type; (2) the named individual with rollback authority and their named alternate; (3) the exact CLI command or UI steps to execute rollback with the estimated execution time; (4) the post-rollback smoke test to confirm the prior behavior is restored.
