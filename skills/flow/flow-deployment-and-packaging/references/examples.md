# Examples — Flow Deployment And Packaging

Concrete, copy-pasteable examples for the most common deployment scenarios. Every command targets the `sf` (v2) CLI, not the deprecated `sfdx` (v1).

---

## Example 1: Validate-then-quick-deploy a single flow to production

**Context:** A record-triggered flow `Opportunity_Stage_Notification.flow-meta.xml` has been authored in a UAT sandbox, source-controlled, code-reviewed, and is ready for production.

**Problem:** Running `sf project deploy start` directly during the cutover window means tests run inside the maintenance window. A 60-minute Apex test suite turns a 5-minute change into a 65-minute downtime risk.

**Solution:**

```bash
# Step 1 — Validate, hours before the cutover (no production change yet).
sf project deploy validate \
  --source-dir force-app/main/default/flows/Opportunity_Stage_Notification.flow-meta.xml \
  --target-org prod \
  --test-level RunLocalTests \
  --wait 90 \
  --verbose
```

Expected output (truncated, JSON shape from `--json`):

```json
{
  "status": 0,
  "result": {
    "id": "0Af5g00000EnQqWCAV",
    "validatedDeployRequestId": "0Af5g00000EnQqWCAV",
    "status": "Succeeded",
    "checkOnly": true,
    "numberComponentsTotal": 1,
    "numberComponentsDeployed": 1,
    "numberComponentErrors": 0,
    "numberTestsTotal": 247,
    "numberTestsCompleted": 247,
    "numberTestErrors": 0,
    "createdBy": "0055g00000EXMPL",
    "createdDate": "2026-04-27T14:02:11.000Z"
  }
}
```

```bash
# Step 2 — During the cutover window, quick-deploy using the validation Id.
sf project deploy quick \
  --job-id 0Af5g00000EnQqWCAV \
  --target-org prod \
  --wait 30
```

Quick-deploy completes in under 60 seconds for a single-flow change because no tests re-run.

**Why it works:** `validate` is a `checkOnly` deploy — it compiles, runs tests, but does not commit. `quick` reuses the cached test results and only commits the metadata, as long as it runs within 10 days of the validation.

---

## Example 2: Failure mode — Flow Version Conflict

**Context:** A developer extracted `Lead_Routing.flow-meta.xml` on Monday, made changes, and tries to deploy on Friday. Meanwhile, an admin clicked "Save As New Version" on the same flow in production via Flow Builder on Wednesday.

**Problem:** Deploying the developer's version would silently overwrite the admin's Wednesday changes.

**Failure output:**

```bash
$ sf project deploy start --source-dir force-app/main/default/flows/Lead_Routing.flow-meta.xml --target-org prod

Status: Failed | 0/1 Components | 0/0 Tests
=== Component Failures
PROJECT PATH                                                       ERRORS
─────────────────────────────────────────────────────────────────  ────────────────────────────────────────────────
force-app/main/default/flows/Lead_Routing.flow-meta.xml            cannot deploy a Flow that has been edited in
                                                                   the Flow Builder UI since the source was last
                                                                   retrieved. Re-retrieve and merge.
```

**Solution:**

```bash
# Re-retrieve the current production version.
sf project retrieve start \
  --metadata Flow:Lead_Routing \
  --target-org prod \
  --output-dir /tmp/prod-current

# Diff the production XML against your developer branch.
diff /tmp/prod-current/main/default/flows/Lead_Routing.flow-meta.xml \
     force-app/main/default/flows/Lead_Routing.flow-meta.xml

# Manually merge the admin's Wednesday changes into the developer branch.
# Re-retrieve sets a fresh baseline.

# Re-deploy.
sf project deploy start \
  --source-dir force-app/main/default/flows/Lead_Routing.flow-meta.xml \
  --target-org prod \
  --test-level RunLocalTests
```

**Why it matters:** Flow Version Conflict is Salesforce protecting you from silent loss of admin changes. The fix is always: retrieve fresh, diff, merge, re-deploy. Never use `--ignore-errors` to bypass.

---

## Example 3: Flow + Subflow + Apex bundled deploy

**Context:** A new screen flow `Lead_Qualification.flow-meta.xml` references a new subflow `Sub_Score_Lead.flow-meta.xml`, which in turn calls a new invocable Apex class `LeadScorer.cls`.

**Problem:** Deploying any one of the three alone fails — the subflow needs the Apex class, the parent needs the subflow.

**Solution:** include all three in one deploy bundle.

```bash
sf project deploy start \
  --source-dir force-app/main/default/flows/Lead_Qualification.flow-meta.xml \
  --source-dir force-app/main/default/flows/Sub_Score_Lead.flow-meta.xml \
  --source-dir force-app/main/default/classes/LeadScorer.cls \
  --source-dir force-app/main/default/classes/LeadScorer.cls-meta.xml \
  --source-dir force-app/main/default/classes/LeadScorerTest.cls \
  --source-dir force-app/main/default/classes/LeadScorerTest.cls-meta.xml \
  --target-org uat \
  --test-level RunSpecifiedTests \
  --tests LeadScorerTest \
  --wait 30
```

Salesforce computes the dependency order: Apex compiled first, subflow second, parent flow third.

**Why it works:** the Metadata API processes each component, and dependencies are resolved within a single transaction.

---

## Example 4: Deploy as Draft, activate manually in cutover window

**Context:** A high-risk flow change to `Order_Approval.flow-meta.xml`. Ops wants to deploy at 2pm but only flip activation at 11pm during the maintenance window.

**Solution:**

Step 1 — Edit the source XML to set `<status>Draft</status>`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <processType>AutoLaunchedFlow</processType>
    <status>Draft</status>
    <interviewLabel>Order Approval {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Order Approval</label>
    ...
</Flow>
```

Step 2 — Deploy at 2pm:

```bash
sf project deploy start \
  --source-dir force-app/main/default/flows/Order_Approval.flow-meta.xml \
  --target-org prod \
  --test-level RunLocalTests
```

Step 3 — At 11pm, activate the new draft via Tooling API:

```bash
# Find the new draft VersionNumber.
sf data query \
  --query "SELECT Id, VersionNumber, Status FROM Flow WHERE DeveloperName = 'Order_Approval' ORDER BY VersionNumber DESC" \
  --use-tooling-api \
  --target-org prod

# Suppose the new draft is VersionNumber 12.
# Find the FlowDefinition Id.
sf data query \
  --query "SELECT Id, ActiveVersion.VersionNumber FROM FlowDefinition WHERE DeveloperName = 'Order_Approval'" \
  --use-tooling-api \
  --target-org prod

# Activate via PATCH.
sf data update record \
  --sobject FlowDefinition \
  --record-id 3005g000000EXMPL \
  --values "ActiveVersionNumber=12" \
  --use-tooling-api \
  --target-org prod
```

**Why it works:** activation is a separate operation from deployment. The draft sits inert until promoted.

---

## Example 5: Rollback by re-activating a prior version

**Context:** Version 12 of `Order_Approval` was activated last night and is causing data corruption at 7am the next morning. Need to revert to version 11 immediately.

**Solution:**

```bash
# Confirm version 11 still exists in the org (it does — Salesforce never deletes versions).
sf data query \
  --query "SELECT Id, VersionNumber, Status FROM Flow WHERE DeveloperName = 'Order_Approval' ORDER BY VersionNumber DESC" \
  --use-tooling-api \
  --target-org prod

# Re-activate version 11.
sf data update record \
  --sobject FlowDefinition \
  --record-id 3005g000000EXMPL \
  --values "ActiveVersionNumber=11" \
  --use-tooling-api \
  --target-org prod
```

Version 12 becomes Obsolete (still in the org, not deleted). Version 11 becomes Active. Live traffic flips immediately — no deploy required.

**Why it works:** rollback by re-activation is a metadata-only operation, no XML deploy needed. This is the fastest possible recovery path — sub-minute.

---

## Example 6: Unlocked Package definition for a reusable subflow library

**Context:** Your team maintains a library of 8 reusable subflows that ship to 12 internal orgs. Source-deploy to each org is unmanageable. Time to graduate to 2GP.

**Solution:**

`sfdx-project.json`:

```json
{
  "packageDirectories": [
    {
      "path": "force-app",
      "default": true,
      "package": "ACME Internal Flow Library",
      "versionName": "ver 1.4",
      "versionNumber": "1.4.0.NEXT",
      "definitionFile": "config/project-scratch-def.json",
      "dependencies": []
    }
  ],
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "62.0",
  "packageAliases": {
    "ACME Internal Flow Library": "0Ho5g0000004EXMPL"
  }
}
```

`config/project-scratch-def.json`:

```json
{
  "orgName": "ACME Flow Library Dev",
  "edition": "Enterprise",
  "features": ["EnableSetPasswordInApi"],
  "settings": {
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    }
  }
}
```

Build a new package version:

```bash
sf package version create \
  --package "ACME Internal Flow Library" \
  --installation-key-bypass \
  --wait 30 \
  --code-coverage
```

Install in a target org:

```bash
sf package install \
  --package "ACME Internal Flow Library@1.4.0-3" \
  --target-org internal-sales-prod \
  --wait 30 \
  --publish-wait 10
```

**Why it works:** Unlocked Packages give you versioned, upgradable distribution. Each install records a package lineage in the target org, and a new version upgrades in place — no manual diff-and-merge required.

---

## Anti-Pattern 1: Direct `--test-level NoTestRun` deploy to production

**What practitioners do:**

```bash
sf project deploy start \
  --source-dir force-app/main/default/flows/Order_Approval.flow-meta.xml \
  --target-org prod \
  --test-level NoTestRun
```

**What goes wrong:** Production deploys do not allow `NoTestRun` (Salesforce blocks it server-side). Even if it were allowed, you would skip every test — including tests for invocable Apex the flow calls. A regression in a downstream Apex method would surface only in live traffic.

**Correct approach:** always `RunLocalTests` (or `RunAllTestsInOrg` if managed-package interaction expected) for production. Only use `NoTestRun` in scratch orgs.

---

## Anti-Pattern 2: Editing the deployed flow in production via Flow Builder

**What practitioners do:** Deploy `Lead_Routing` to prod, then realize a label needs tweaking, and click "Edit" in Flow Builder in prod, save a new version, and activate it.

**What goes wrong:** the source-controlled version drifts from the production version. Next deploy from source either (a) fails with Flow Version Conflict (if Salesforce detects the drift) or (b) silently overwrites the admin's edit.

**Correct approach:** every change to a production flow goes through the source-control + deploy pipeline. The "Edit in Prod" button on Flow Builder is only for true emergencies, and the change must be back-ported to source-control immediately.

---

## Anti-Pattern 3: Forgetting to deploy FlowAccessPermission with the flow

**What practitioners do:** Deploy `Custom_Lead_Screen.flow-meta.xml` to prod, test in admin context (works), close the ticket. End-users hit "Insufficient privileges" the next morning.

**What goes wrong:** FlowAccessPermission entries on profiles / permission sets are separate metadata. They do not auto-travel with the flow.

**Correct approach:** include the relevant `Profile.profile-meta.xml` or `PermissionSet.permissionset-meta.xml` (with the FlowAccessPermission section) in the deploy bundle. Smoke-test by impersonating a non-admin user.

---

## Anti-Pattern 4: Using `--ignore-errors` on a flow deploy

**What practitioners do:**

```bash
sf project deploy start --source-dir force-app --target-org prod --ignore-errors
```

**What goes wrong:** partial-success deploys leave the target org in a half-migrated state. A parent flow may activate while its dependent subflow failed silently. Hard to diagnose, harder to roll back.

**Correct approach:** never `--ignore-errors` for prod. Fix every error before deploying. For non-critical metadata (e.g. a CustomReport that's optional), surgically exclude it from the deploy bundle rather than ignoring errors org-wide.
