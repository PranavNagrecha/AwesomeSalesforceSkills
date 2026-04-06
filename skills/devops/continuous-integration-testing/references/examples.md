# Examples — Continuous Integration Testing

## Example 1: GitHub Actions Pipeline with RunLocalTests and Coverage Gate

**Context:** A team uses GitHub Actions to deploy Apex and metadata to a production org. They want every push to `main` to validate the deployment, run all local tests, and block the merge if coverage drops below 80%.

**Problem:** Without an explicit coverage gate, Salesforce only enforces 75% org-wide during deployment. The team's standard is 80%, and developers have been merging code that passes deployment but degrades coverage over time.

**Solution:**

```yaml
# .github/workflows/deploy.yml
name: Validate and Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install SF CLI
        run: npm install -g @salesforce/cli

      - name: Authenticate
        run: |
          echo "${{ secrets.SFDX_AUTH_URL }}" > auth.txt
          sf org login sfdx-url --sfdx-url-file auth.txt --alias prod

      - name: Validate deployment with tests
        run: |
          sf project deploy validate \
            --source-dir force-app \
            --test-level RunLocalTests \
            --target-org prod \
            --wait 60 \
            --coverage-formatters json \
            --results-dir ./test-results

      - name: Enforce 80% coverage threshold
        run: |
          python3 scripts/check_coverage.py \
            --results-dir ./test-results \
            --min-coverage 80

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: ./test-results/
```

**Why it works:** The pipeline separates validation from deployment, captures results as artifacts, and runs a custom script to enforce the team's 80% threshold rather than relying on Salesforce's built-in 75% gate. The `if: always()` on artifact upload ensures results are available even when the build fails.

---

## Example 2: Fast PR Validation with RunSpecifiedTests

**Context:** A large enterprise org has 2,000+ test classes. Running `RunLocalTests` takes 90 minutes. Developers want fast feedback on pull requests without waiting for the full suite.

**Problem:** Running `RunLocalTests` on every PR makes the feedback loop too slow. Developers start ignoring CI results or pushing without waiting for the build.

**Solution:**

```bash
#!/bin/bash
# scripts/pr-validate.sh
# Determine changed Apex classes and find their matching test classes

CHANGED_CLASSES=$(git diff --name-only origin/main...HEAD \
  | grep 'force-app.*\.cls$' \
  | sed 's|.*/||; s|\.cls||')

TEST_CLASSES=""
for CLASS in $CHANGED_CLASSES; do
  # Convention: MyClass -> MyClassTest
  TEST_NAME="${CLASS}Test"
  if [ -f "force-app/main/default/classes/${TEST_NAME}.cls" ]; then
    TEST_CLASSES="${TEST_CLASSES},${TEST_NAME}"
  fi
done

# Remove leading comma
TEST_CLASSES="${TEST_CLASSES#,}"

if [ -z "$TEST_CLASSES" ]; then
  echo "No matching test classes found for changed Apex. Skipping tests."
  exit 0
fi

echo "Running tests: $TEST_CLASSES"

sf project deploy validate \
  --source-dir force-app \
  --test-level RunSpecifiedTests \
  --tests "$TEST_CLASSES" \
  --target-org ci-sandbox \
  --wait 30
```

**Why it works:** The script maps changed classes to test classes using a naming convention, then uses `RunSpecifiedTests` to run only the relevant tests. PR builds complete in 3-5 minutes instead of 90. The full `RunLocalTests` suite still runs on merge to `main` as a safety net. Note that `RunSpecifiedTests` enforces 75% per-class coverage on every component in the deployment package, which is actually stricter than the org-wide check from `RunLocalTests`.

---

## Example 3: Working Around the 0% Coverage Bug

**Context:** A pipeline uses `sf apex run test` for sandbox validation (not a deployment). The team needs coverage data to track trends over time.

**Problem:** The pipeline runs `sf apex run test --code-coverage --wait 30 --result-format json` but coverage percentages in the output are all 0%, even though every test passes.

**Solution:**

```bash
#!/bin/bash
# Run tests asynchronously and capture the run ID
RUN_OUTPUT=$(sf apex run test \
  --test-level RunLocalTests \
  --result-format json \
  --wait 30 \
  --target-org sandbox)

# Extract test run ID
RUN_ID=$(echo "$RUN_OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('result', {}).get('summary', {}).get('testRunId', ''))
")

if [ -z "$RUN_ID" ]; then
  echo "ERROR: Could not extract test run ID"
  exit 1
fi

echo "Test run complete. Retrieving coverage for run $RUN_ID..."

# Retrieve coverage separately — this avoids the 0% bug
sf apex get test \
  --test-run-id "$RUN_ID" \
  --code-coverage \
  --result-format json \
  --output-dir ./coverage-results

echo "Coverage results written to ./coverage-results/"
```

**Why it works:** The 0% coverage bug occurs because the platform has not finished aggregating coverage data by the time the initial `--wait` returns. By separating the test execution from the coverage retrieval, the `sf apex get test` call reads the fully aggregated data. This two-step pattern is the documented workaround.

---

## Anti-Pattern: Using RunAllTestsInOrg in CI

**What practitioners do:** Set `--test-level RunAllTestsInOrg` in the CI pipeline to "be thorough" and catch everything.

**What goes wrong:** Managed package tests execute alongside local tests. A failing test in a managed package you did not write and cannot fix blocks your deployment. The build becomes flaky for reasons entirely outside your control, eroding trust in the CI pipeline.

**Correct approach:** Use `RunLocalTests` for production deployments. This runs all tests authored in your org and skips managed package tests. If you genuinely need to verify managed package compatibility (e.g., before a major release), run `RunAllTestsInOrg` as a separate, non-blocking job that reports results without gating the deployment.
