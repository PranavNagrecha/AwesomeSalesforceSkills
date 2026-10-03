# Examples: Release Management

## Example 1: Validation Deploy + Quick Deploy for a Large Org

**Scenario:** A financial services org with 800 Apex classes and a 45-minute test suite needs to deploy 12 components to production on Saturday night.

**Problem:** Running the full test suite inside a Saturday-night window is risky. If tests fail at 1am, the team debugs live on production.

**Solution:**

```bash
# Wednesday: rehearse against production; record the 0Af job ID in the release plan
sf project deploy validate \
  --manifest manifest/package.xml \
  --test-level RunLocalTests \
  --target-org prod \
  --wait 120

# Saturday night: deploy the validated set without re-running tests
sf project deploy quick --job-id 0AfXXXXXXXXXXXXXXX --target-org prod --wait 30

# The quick deploy prints a NEW deploy ID; monitor that one
sf project deploy report --job-id <quickDeployId> --target-org prod
```

If the quick deploy is rejected (for example the validation is more than 10 days old), fall back to a full deploy with `sf project deploy start --manifest manifest/package.xml --test-level RunLocalTests --target-org prod --wait 120`.

**Why it works:** The validation is a full rehearsal that commits nothing. Quick deploy consumes the validated job ID within its 10-day window. The rehearsal leaves days to resolve defects.

---

## Example 2: Rollback After a Defective Apex Trigger Deployment

**Scenario:** A retail org deploys a new version of `AccountTrigger`. Within 20 minutes, support reports all new Account creates are failing with a null pointer in the new trigger code.

**Problem:** The deployment succeeded but the trigger has a runtime defect. Every Account creation is broken.

**Solution:**

```bash
# BEFORE the release (part of the go/no-go checklist): archive the production version
# in Metadata API format. The CLI writes backups/2026-10-03/unpackaged.zip by default.
sf project retrieve start \
  --manifest manifest/package.xml \
  --target-org prod \
  --target-metadata-dir backups/2026-10-03 \
  --single-package

# DURING the incident: redeploy the archived zip, never a fresh retrieve
sf project deploy start \
  --metadata-dir backups/2026-10-03/unpackaged.zip \
  --single-package \
  --test-level RunSpecifiedTests \
  --tests AccountTriggerTest \
  --target-org prod \
  --wait 60
```

The prior trigger version is restored once the deploy finishes. `RunSpecifiedTests` requires the listed tests to cover each deployed class and trigger at 75% or more.

**Why it works:** The backup was retrieved before the release, so it holds the old trigger. A retrieve run during the incident would fetch the defective version that is now in production. Without the archive, the team rebuilds the old code from git history under pressure. The `--single-package` flag on both commands keeps `package.xml` at the root of the zip, which is the layout the deploy expects when the same flag is passed.

A complete release folder (sfdx-project.json, package.xml, backup and deploy commands, and the FlowSettings file) is in [metadata-examples.md](metadata-examples.md).
