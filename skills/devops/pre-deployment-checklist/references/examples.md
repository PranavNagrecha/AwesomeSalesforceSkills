# Examples -- Pre-Deployment Checklist

## Example 1: Validate-Then-Quick-Deploy for a Standard Release

**Context:** A team has completed a sprint delivering three new Apex classes, two LWC components, one Flow, and associated permission set changes. The release is scheduled for Saturday morning. They have 48 hours of lead time.

**Problem:** Without a validation deploy, the team has to run the full test suite during the production window. In their org (2,400 Apex classes), `RunLocalTests` takes 90 minutes. If tests fail, the window is blown and the release must wait another week.

**Solution:**

```bash
# Thursday: run validation deploy during business hours (safe — writes nothing)
sf project deploy validate \
  --manifest manifest/package.xml \
  --target-org production \
  --test-level RunLocalTests \
  --wait 120

# Capture the validated deploy request ID from output
# Example output: "Deploy ID: 0Af5g00000XXXXX — Validated successfully"

# Saturday morning: quick deploy using the validated ID
sf project deploy quick \
  --job-id 0Af5g00000XXXXX \
  --target-org production
```

**Why it works:** The validation deploy runs all tests on Thursday when there is no time pressure. The quick deploy on Saturday completes in under 5 minutes because tests are skipped. If the validation fails on Thursday, the team has a full business day to fix and re-validate.

---

## Example 2: Pre-Release Backup and Rollback

**Context:** A deployment introduces a new trigger on the Account object and modifies an existing validation rule. After deploying, the team discovers the trigger has an unexpected interaction with a managed package, causing errors on Account save.

**Problem:** Without a backup, the team must manually reconstruct the prior state of the validation rule and remove the trigger, which takes time and is error-prone under pressure.

**Solution:**

```bash
# Before deploying: retrieve current production state of everything being deployed
sf project retrieve start \
  --manifest manifest/package.xml \
  --target-org production \
  --output-dir backups/2026-04-05/

# Deploy the new changes
sf project deploy start \
  --manifest manifest/package.xml \
  --target-org production \
  --test-level RunLocalTests

# After discovering the issue: rollback by redeploying the backup
sf project deploy start \
  --source-dir backups/2026-04-05/ \
  --target-org production \
  --test-level RunLocalTests
```

**Why it works:** The backup contains the exact metadata state that was in production before the deploy. Redeploying it restores production to its prior state without requiring any code changes or source control archaeology.

---

## Example 3: Dependency Gap Detection Before Deploy

**Context:** A developer adds a new custom field `Account.Risk_Score__c` and a validation rule that references it. The validation rule is included in the `package.xml`, but the custom field is accidentally omitted.

**Problem:** The deploy fails in production with: `Error: Field Account.Risk_Score__c does not exist`. The team has already opened the production window and now must scramble.

**Solution:**

```sql
-- Query MetadataComponentDependency in target org to find missing references
SELECT MetadataComponentName, MetadataComponentType,
       RefMetadataComponentName, RefMetadataComponentType
FROM MetadataComponentDependency
WHERE MetadataComponentName = 'Account_Risk_Validation'
  AND MetadataComponentType = 'ValidationRule'
```

Cross-reference the results against the `package.xml` manifest. Any `RefMetadataComponentName` that is not already in the target org and not in the manifest is a gap that must be added.

**Why it works:** Running this check before the deploy attempt catches the gap without wasting a validation cycle or opening the production window prematurely.

---

## Anti-Pattern: Skipping Validation Deploy to Save Time

**What practitioners do:** Deploy directly to production with `sf project deploy start` during the release window, skipping the validation step entirely. They reason that tests passed in staging, so they will pass in production.

**What goes wrong:** Production has different data volumes, sharing rules, installed packages, and org-wide defaults. Tests that pass in a partial-copy sandbox fail in production due to SOQL query limits, sharing visibility differences, or managed package trigger interactions. The team discovers this during the production window, extending the outage.

**Correct approach:** Always run a validation deploy (`checkOnly: true` / `sf project deploy validate`) against production before the release window. This is safe (writes nothing) and reveals production-specific test failures with zero risk. Use the resulting quick-deploy ID during the actual window.
