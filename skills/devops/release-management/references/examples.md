# Examples — Release Management

## Example 1: Validation Deploy + Quick Deploy for a Large Org

**Scenario:** A financial services org with 800 Apex classes and a 45-minute test suite needs to deploy 12 components to production on Saturday night.

**Problem:** Running a full test suite during a Saturday-night deployment window is risky. If tests fail at 1am, the team is debugging live on production.

**Solution:**
1. On Wednesday: run `sf project deploy validate --source-dir force-app --test-level RunLocalTests --wait 120` against production. Save the returned deploy ID.
2. On Saturday night: run `sf project deploy quick --job-id 0Af...savedId`. This skips the test run and deploys the pre-validated package in minutes.
3. If the quick deploy fails (expired ID because production was modified after validation): fall back to `sf project deploy start --test-level RunLocalTests --wait 120`.

**Why it works:** The validation deploy is a full rehearsal without committing changes. Quick Deploy consumes the 10-day validated deploy ID. The rehearsal window allows defect resolution before deployment night.

---

## Example 2: Rollback After a Defective Apex Trigger Deployment

**Scenario:** A retail org deploys a new version of `AccountTrigger`. Within 20 minutes, support reports all new Account creates are failing — a null pointer in the new trigger code.

**Problem:** The deployment succeeded but the trigger has a runtime defect. Every Account creation is broken.

**Solution:**
1. The team retrieves the pre-deployment backup taken 30 minutes before go-live: `sf project retrieve start --manifest pre-release-backup.xml`.
2. Redeploys the backup: `sf project deploy start --manifest pre-release-backup.xml --test-level RunSpecifiedTests --tests AccountTriggerTest`.
3. Within 10 minutes, the prior trigger version is restored.

**Why it works:** The pre-release backup was taken as part of the release workflow. Without it, the team would reconstruct the prior Apex code from Git history, increasing rollback time from 10 minutes to 60+ minutes.
