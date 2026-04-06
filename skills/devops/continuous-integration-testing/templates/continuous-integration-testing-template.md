# Continuous Integration Testing — Work Template

Use this template when configuring or troubleshooting Apex test execution in a CI/CD pipeline.

## Scope

**Skill:** `continuous-integration-testing`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer these before proceeding:

- **CI platform:** (GitHub Actions / GitLab CI / Jenkins / Azure DevOps / Bitbucket Pipelines / other)
- **Target org type:** (production / sandbox / scratch org)
- **Authentication method:** (JWT / auth URL / web login / other)
- **Managed packages present?** (yes / no — affects test level choice)
- **Approximate number of local test classes:** (affects sync vs async decision)
- **Team coverage threshold:** (Salesforce minimum is 75%; many teams enforce 80-85%)

## Test Level Decision

Based on context above, select the test level:

| Scenario | Test Level | Rationale |
|---|---|---|
| Production deploy, no managed packages | `RunLocalTests` | |
| Production deploy, managed packages present | `RunLocalTests` | |
| Fast PR validation, test mapping exists | `RunSpecifiedTests` | |
| Sandbox validation | `RunLocalTests` | |
| Metadata-only (no Apex) | `NoTestRun` | |
| Managed package compatibility check | `RunAllTestsInOrg` | Non-blocking job only |

**Selected test level:** ___________________

**Justification:** ___________________

## Pipeline Configuration

### Authentication Step

```bash
# Replace with actual secret references for your CI platform
sf org login sfdx-url --sfdx-url-file <(echo "$SFDX_AUTH_URL") --alias target
```

### Test Execution Step

```bash
# For deployment validation:
sf project deploy validate \
  --source-dir force-app \
  --test-level __TEST_LEVEL__ \
  --target-org target \
  --wait 60

# For standalone test run (sandbox):
sf apex run test \
  --test-level __TEST_LEVEL__ \
  --result-format junit \
  --output-dir ./test-results \
  --wait 60 \
  --target-org target
```

### Coverage Retrieval (if needed)

```bash
# Use if async run returns 0% coverage
sf apex get test \
  --test-run-id __RUN_ID__ \
  --code-coverage \
  --result-format json \
  --output-dir ./coverage-results
```

### Coverage Enforcement

```bash
# Parse coverage JSON and enforce team threshold
# Exit non-zero if below minimum
python3 scripts/check_coverage.py \
  --results-dir ./coverage-results \
  --min-coverage __THRESHOLD__
```

## Checklist

- [ ] CI pipeline authenticates to the target org without interactive prompts
- [ ] Test level is explicitly set with `--test-level`
- [ ] `--wait` timeout is sufficient for the org's test suite
- [ ] JUnit XML output is collected with `--result-format junit`
- [ ] Test results are published as CI artifacts
- [ ] Coverage enforcement script gates the build above team threshold
- [ ] 0% coverage bug workaround is in place if using async runs with `--code-coverage`
- [ ] No hardcoded credentials in pipeline configuration
- [ ] Pipeline fails on test failures before attempting deployment
- [ ] Legacy `sfdx force:*` commands are not used (use `sf` CLI v2)

## Notes

Record any deviations from the standard pattern and why:

-
