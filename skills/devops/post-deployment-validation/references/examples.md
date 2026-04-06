# Examples — Post Deployment Validation

## Example 1: Validate-Then-Quick-Deploy to Production

**Context:** A team has a release package containing 3 Apex classes, 2 Lightning Web Components, and 5 custom fields ready for production. The production org has a 30-minute maintenance window on Saturday morning.

**Problem:** Running a full deploy with RunLocalTests during the window takes 45 minutes — longer than the window allows. If the deploy runs over, users arrive to a partially deployed org.

**Solution:**

```bash
# Step 1: Validate on Thursday (runs tests, does NOT commit)
sf project deploy start \
  --manifest manifest/package.xml \
  --target-org production \
  --dry-run \
  --test-level RunLocalTests \
  --wait 60

# Step 2: Capture the validation ID from the output
# Deploy ID: 0Af7g00000XXXXX

# Step 3: On Saturday, quick deploy (skips tests, commits immediately)
sf project deploy quick \
  --job-id 0Af7g00000XXXXX \
  --target-org production

# Step 4: Monitor the quick deploy (returns a NEW deploy ID)
sf project deploy report --job-id 0Af7g00000YYYYY

# Step 5: Verify landing
sf project retrieve start \
  --metadata "ApexClass:OrderProcessor,ApexClass:OrderValidator,ApexClass:OrderService" \
  --target-org production
```

**Why it works:** The validation runs the full test suite days in advance. The quick deploy during the maintenance window only commits the already-validated metadata, completing in minutes instead of 45 minutes. The 10-day validation window gives the team flexibility to schedule the actual commit.

---

## Example 2: Post-Deployment Smoke Test Using Metadata API Status

**Context:** A deployment just completed against a staging org. The team needs to confirm it succeeded before promoting the same package to production.

**Problem:** The deployment status shows "Succeeded" but two Apex tests that were passing before the deployment are now failing. The team needs to determine whether these are regressions introduced by the deployment or pre-existing flaky tests.

**Solution:**

```bash
# Pull the detailed deployment report with test coverage
sf project deploy report \
  --job-id 0Af7g00000ZZZZZ \
  --coverage-formatters json \
  --results-dir ./deploy-results

# Review the JSON output for failing tests
# deploy-results/coverage/coverage.json contains per-class detail

# Compare against the pre-deployment test run baseline
# If the same tests were failing before the deploy, they are pre-existing
sf apex run test \
  --class-names "FailingTestClass1,FailingTestClass2" \
  --target-org staging \
  --result-format json \
  --output-dir ./rerun-results

# Retrieve a key component to confirm it landed
sf project retrieve start \
  --metadata "CustomField:Account.NewField__c" \
  --target-org staging
```

**Why it works:** Comparing the deployment test results against a fresh re-run of the failing tests isolates whether the deployment caused the failure. If the tests fail again on re-run without any new deployment, they are pre-existing. If they pass on re-run, the deployment may have introduced a transient state issue that self-resolved (e.g., test data ordering).

---

## Anti-Pattern: Deploying to Production Without a Prior Validation

**What practitioners do:** Skip the validation deploy step entirely and run `sf project deploy start` directly against production with `--test-level RunLocalTests`. They treat the single deploy as both validation and commit.

**What goes wrong:** If a test fails mid-deploy, the deployment rolls back, but the org may have already been in a partially deployed state for the duration of the test run (which can take 30+ minutes for large orgs). Users accessing the org during this window may see inconsistent behavior. There is no way to "resume" a failed deploy — you must fix the issue and start over, re-running all tests from scratch.

**Correct approach:** Always run a validation deploy first (`--dry-run`). Review the test results. If everything passes, use quick deploy to commit in seconds. This separates the risky test-execution phase from the commit phase, minimizing the window of exposure.
