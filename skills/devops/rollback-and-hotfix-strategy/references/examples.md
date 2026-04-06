# Examples — Rollback And Hotfix Strategy

## Example 1: Full Rollback Using a Pre-Deploy Archive

**Context:** A team deployed a release containing 45 metadata components to production. Within an hour, users reported that several Lightning pages were broken and a critical validation rule was firing incorrectly on the Account object.

**Problem:** Without a pre-deploy archive, the team would need to manually identify the previous version of each of the 45 components from Git history, reconstruct a deployment package, and hope they did not miss anything. This process takes hours during an active production incident.

**Solution:**

```bash
# Before every production deployment, the CI pipeline captures the archive:
sf project retrieve start \
  --manifest deploy/package.xml \
  --target-org production \
  --output-dir rollback-archives/2026-04-04-release-v3.2/

# When the regression is discovered, deploy the archive back:
sf project deploy start \
  --manifest deploy/package.xml \
  --source-dir rollback-archives/2026-04-04-release-v3.2/ \
  --target-org production
```

**Why it works:** The archive contains the exact state of every component as it existed in production before the failed deployment. Re-deploying it restores that state without any manual reconstruction. The `package.xml` used for retrieval matches the deployment manifest, so every changed component is covered.

---

## Example 2: Quick Deploy Hotfix for a Single Apex Bug

**Context:** A production Apex trigger on Opportunity has a null pointer exception that fires on a specific record type. The fix is a single-line null check. The org has 2,400 Apex tests that take 75 minutes to run.

**Problem:** A standard deployment would require 75 minutes of test execution before the fix reaches production. Users are blocked from saving Opportunities during this time.

**Solution:**

```bash
# 1. Create hotfix branch from production tag
git checkout -b hotfix/opp-null-check v3.2-production
# (make the one-line fix in OpportunityTriggerHandler.cls)

# 2. Validate against production (runs all tests once)
sf project deploy validate \
  --source-dir force-app/main/default/classes/OpportunityTriggerHandler.cls \
  --test-level RunLocalTests \
  --target-org production

# Output: Job ID: 0Af5g00000EXAMPLE

# 3. Promote during the deployment window (skips tests, deploys in seconds)
sf project deploy quick \
  --job-id 0Af5g00000EXAMPLE \
  --target-org production

# 4. Merge hotfix back
git checkout main && git merge hotfix/opp-null-check
git checkout develop && git merge hotfix/opp-null-check
```

**Why it works:** The validate step runs all tests once and confirms the fix is clean. Quick deploy then promotes the validated package in seconds rather than re-running 75 minutes of tests. The hotfix branch ensures only the minimal change reaches production.

---

## Anti-Pattern: Rolling Forward Without Stabilizing Production First

**What practitioners do:** When a deployment causes a regression, the team immediately starts debugging and building a forward fix while production remains broken. They skip rollback because "we'll have the fix ready in an hour."

**What goes wrong:** The "one hour" fix takes three hours because the root cause is more complex than expected. During that time, users are experiencing errors, data integrity issues may be accumulating, and the team is under escalating pressure. If the forward fix itself has a bug, the situation worsens.

**Correct approach:** Roll back first to restore production stability, then investigate and fix at normal pace. The pre-deploy archive makes rollback a 5-minute operation. Once production is stable, the team can debug without time pressure, build the fix properly, validate it through the normal pipeline, and deploy it as a planned release. The only exception is when the rollback itself would cause more damage (e.g., a data migration that already ran), in which case a targeted hotfix with quick deploy is the safer path.
