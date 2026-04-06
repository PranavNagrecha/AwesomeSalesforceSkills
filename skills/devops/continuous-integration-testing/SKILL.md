---
name: continuous-integration-testing
description: "Use when configuring Apex test execution in CI/CD pipelines, choosing test levels for deployments, parsing test results, or troubleshooting code coverage in automated builds. Triggers: 'RunLocalTests', 'RunSpecifiedTests', 'sf project deploy', 'code coverage CI', 'JUnit test results'. NOT for Apex test class design patterns, test data factory architecture, or LWC Jest testing."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I run Apex tests in a CI pipeline"
  - "what test level should I use for deployment"
  - "my CI build shows 0% code coverage even though tests pass"
  - "how to get JUnit XML output from sf apex run test"
  - "RunLocalTests vs RunSpecifiedTests for managed packages"
tags:
  - continuous-integration-testing
  - ci-cd
  - apex-testing
  - code-coverage
  - sf-cli
  - deployment-validation
inputs:
  - "deployment pipeline tool (GitHub Actions, GitLab CI, Jenkins, Azure DevOps, Bitbucket Pipelines)"
  - "test level requirement (RunLocalTests, RunSpecifiedTests, RunAllTestsInOrg, NoTestRun)"
  - "whether the deployment includes managed package components"
  - "target org alias or authentication method"
outputs:
  - "CI pipeline configuration with correct test flags and coverage enforcement"
  - "test result parsing strategy producing JUnit XML or equivalent"
  - "coverage enforcement script that gates deployment on org-wide and per-class thresholds"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Continuous Integration Testing

Use this skill when Apex tests must run as part of an automated CI/CD pipeline rather than manually through the Developer Console or Setup UI. The objective is a pipeline configuration that executes the right test level, collects accurate coverage numbers, produces machine-readable results, and fails the build when coverage or test outcomes do not meet deployment thresholds.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which CI platform is in use?** The `sf` CLI commands are the same everywhere, but authentication (JWT, web login, auth URL) and artifact handling differ across GitHub Actions, GitLab CI, Jenkins, and others.
- **Does the target org contain managed packages?** Managed package tests inflate failure risk under `RunAllTestsInOrg` and are skipped under `RunLocalTests`. The wrong choice causes either false failures or silently skipped coverage.
- **What is the minimum coverage gate?** Salesforce enforces 75% org-wide for production deployments, but many teams enforce higher thresholds (80-85%) or per-class minimums that Salesforce does not natively enforce.

---

## Core Concepts

### Test Levels Control What Runs

The `sf project deploy start` and `sf apex run test` commands accept a `--test-level` flag with four values:

- **NoTestRun** -- skip tests entirely. Only valid for non-production targets or metadata-only changes.
- **RunSpecifiedTests** -- run only the named test classes. Salesforce enforces 75% coverage per class and per trigger in the deployment package, which is stricter than org-wide.
- **RunLocalTests** -- run all tests in the org except managed package tests. Coverage is calculated org-wide at 75%.
- **RunAllTestsInOrg** -- run everything including managed package tests. Rarely appropriate in CI because managed package test failures block your deployment.

The critical nuance: `RunSpecifiedTests` applies coverage requirements per-component in the package, not org-wide. A single under-covered class in your changeset will fail deployment even if the org is at 90% overall.

### Coverage Collection Is Not Coverage Enforcement

The `--code-coverage` flag on `sf apex run test` instructs the platform to collect coverage data and include it in the result payload. It does not enforce any threshold. Your pipeline script must parse the coverage result and fail the build if coverage is below the team standard. Salesforce only enforces the 75% threshold during actual deployment, not during standalone test runs.

### JUnit Output for CI Report Ingestion

Most CI platforms can parse JUnit XML to display test results in their UI. Use `--result-format junit` on `sf apex run test` to produce this format. The output file can be declared as a test artifact in GitHub Actions, GitLab CI, or Jenkins to get per-test pass/fail reporting in the build dashboard.

### Asynchronous Test Execution and Polling

By default, `sf apex run test` with `--synchronous` runs tests in a single synchronous request, which is limited to a smaller set of tests. Without `--synchronous`, tests run asynchronously and the CLI polls for completion when `--wait` is specified. A known platform behavior: combining `--code-coverage` with `--wait` on asynchronous runs can return 0% coverage. The workaround is to let the run complete, then retrieve results separately with `sf apex get test --test-run-id <id> --code-coverage`.

---

## Common Patterns

### Pattern: Two-Stage Deploy with Validation Then Quick-Deploy

**When to use:** Production deployments where you want a CI validation gate before the actual deployment window.

**How it works:**

1. Run `sf project deploy validate --test-level RunLocalTests --target-org prod` during CI. This runs all local tests and validates coverage without actually deploying.
2. Capture the validation ID from the output.
3. During the deployment window, run `sf project deploy quick --job-id <validation-id> --target-org prod` to deploy without re-running tests.

**Why not the alternative:** Running `sf project deploy start` directly means tests and deployment happen atomically. If CI validates in the morning and deployment is approved in the afternoon, validation-then-quick-deploy avoids re-running the full test suite.

### Pattern: RunSpecifiedTests with Explicit Coverage Gate

**When to use:** Large orgs where `RunLocalTests` takes too long (30+ minutes) and the team wants fast CI feedback.

**How it works:**

1. Determine which test classes cover the changed Apex classes. Many teams maintain a mapping file or naming convention (`MyClass` -> `MyClassTest`).
2. Run `sf project deploy start --test-level RunSpecifiedTests --tests MyClassTest,MyServiceTest --target-org target`.
3. Parse the deployment result for per-class coverage. Fail the build if any component in the package is below 75%.

**Why not the alternative:** `RunLocalTests` in a large org can take over an hour. `RunSpecifiedTests` gives targeted feedback in minutes but requires the team to maintain accurate test-to-class mappings.

### Pattern: Standalone Test Run with Separate Coverage Retrieval

**When to use:** When the pipeline needs test results and coverage data but is not performing a deployment (e.g., a PR validation build against a sandbox).

**How it works:**

1. Run `sf apex run test --test-level RunLocalTests --result-format junit --output-dir ./test-results --wait 30 --target-org sandbox`.
2. Run `sf apex get test --test-run-id <id> --code-coverage --result-format json` to retrieve coverage separately.
3. Parse the JSON coverage output and enforce the team threshold.

**Why not the alternative:** Combining `--code-coverage` with `--wait` on the initial run can return 0% coverage due to a known CLI behavior. Separating the retrieval step avoids this.

---

## Decision Guidance

| Situation | Recommended Test Level | Reason |
|---|---|---|
| Production deployment, no managed packages | RunLocalTests | Covers all local code, enforces 75% org-wide |
| Production deployment, managed packages present | RunLocalTests | Avoids failures from managed package tests you cannot control |
| Fast PR validation, known test mapping | RunSpecifiedTests | Minutes instead of hours; per-class 75% is still enforced |
| Sandbox validation, exploratory | RunLocalTests | Broad coverage check without deployment risk |
| Metadata-only change (labels, layouts) | NoTestRun | No Apex involved; tests add no value |
| Full regression before release | RunAllTestsInOrg | Only when you explicitly want to verify managed package compatibility |

---

## Recommended Workflow

Step-by-step instructions for configuring CI testing in a Salesforce pipeline:

1. **Authenticate the CI runner** -- configure JWT-based or auth-URL-based authentication so the pipeline can connect to the target org without interactive login. Store the connected app consumer key and server key as CI secrets.
2. **Choose the test level** -- use the decision table above. Default to `RunLocalTests` for production, `RunSpecifiedTests` for PR builds when test mappings exist, and `NoTestRun` for metadata-only changesets.
3. **Configure the deploy or test command** -- use `sf project deploy validate` for production validation or `sf apex run test` for sandbox-only test runs. Always include `--wait` with a timeout (e.g., `--wait 60`) so the pipeline blocks until tests finish.
4. **Capture results in JUnit format** -- add `--result-format junit --output-dir ./test-results` and publish the output directory as a CI artifact. Most CI platforms auto-detect JUnit XML.
5. **Retrieve coverage separately if needed** -- if using `sf apex run test` with `--code-coverage`, verify coverage numbers are non-zero. If they report 0%, fall back to `sf apex get test --test-run-id <id> --code-coverage` as a second step.
6. **Enforce coverage thresholds in script** -- parse the coverage JSON and fail the build if org-wide or per-class coverage falls below the team-defined minimum. Do not rely solely on Salesforce's 75% deployment gate.
7. **Report results** -- publish JUnit artifacts, log coverage percentages, and surface failures clearly in the CI dashboard.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] CI pipeline authenticates to the target org without interactive prompts
- [ ] Test level is explicitly set (not relying on default behavior)
- [ ] `--wait` timeout is long enough for the org's full test suite
- [ ] JUnit XML output is collected and published as a CI artifact
- [ ] Coverage enforcement script parses actual coverage and gates the build
- [ ] The 0% coverage bug workaround is in place if using async test runs with `--code-coverage`
- [ ] Pipeline fails fast on test failures before attempting deployment

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`--code-coverage` with `--wait` returns 0%** -- when running asynchronous tests, combining these flags can result in coverage data showing 0% even when tests pass. The platform has not finished aggregating coverage by the time the CLI reads the result. Fix: retrieve coverage separately using `sf apex get test --test-run-id <id> --code-coverage`.
2. **RunSpecifiedTests enforces per-class coverage, not org-wide** -- unlike `RunLocalTests`, which applies the 75% threshold org-wide, `RunSpecifiedTests` requires 75% coverage on every individual class and trigger in the deployment package. A single under-covered class blocks the entire deployment.
3. **Parallel test execution is opt-in per class** -- by default, Salesforce runs test classes serially in a test run. The `@isTest(isParallel=true)` annotation opts a class into parallel execution, which can reduce total run time but introduces risk if tests share mutable state through `SeeAllData` or poorly isolated setup.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CI pipeline configuration | YAML or Jenkinsfile with correct sf CLI commands, test levels, and coverage gates |
| JUnit XML test results | Machine-readable test output for CI dashboard integration |
| Coverage enforcement script | Shell or Python script that parses coverage JSON and exits non-zero below threshold |

---

## Related Skills

- test-class-standards -- use when the problem is test design quality (assertions, isolation, data factories) rather than CI pipeline configuration
- sf-cli-and-sfdx-essentials -- use for general sf CLI setup, authentication, and project structure questions beyond testing
- batch-job-scheduling-and-monitoring -- relevant when CI tests exercise batch Apex and need async test patterns
