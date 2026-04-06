# Gotchas — Continuous Integration Testing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `--code-coverage` with `--wait` Returns 0% on Async Runs

**What happens:** When running `sf apex run test --code-coverage --wait 30` without `--synchronous`, the CLI reports 0% code coverage for all classes even though tests pass. The test results show as passing, but every coverage line reads 0/0.

**When it occurs:** This happens on asynchronous test runs (the default when `--synchronous` is omitted). The platform queues coverage aggregation as a background task that has not completed by the time the CLI polls the final result. Synchronous runs are not affected but are limited to a smaller number of test classes.

**How to avoid:** Use a two-step approach: run tests with `--wait` to get pass/fail, then retrieve coverage separately with `sf apex get test --test-run-id <id> --code-coverage`. Alternatively, for deployments, use `sf project deploy validate` which handles coverage collection internally as part of the deployment validation flow.

---

## Gotcha 2: RunSpecifiedTests Enforces Per-Class 75%, Not Org-Wide

**What happens:** A deployment with `--test-level RunSpecifiedTests` fails with a coverage error even though the org has 90% overall coverage. The error message says a specific class in the deployment package has only 60% coverage.

**When it occurs:** `RunSpecifiedTests` applies the 75% code coverage requirement individually to every Apex class and trigger included in the deployment package. This is stricter than `RunLocalTests`, which only checks the 75% threshold against the entire org's aggregate coverage. A class that was previously "carried" by high coverage elsewhere now must meet the threshold on its own.

**How to avoid:** When using `RunSpecifiedTests`, ensure every class in the deployment changeset has at least 75% coverage from the specified test classes. Run coverage checks locally before pushing to CI. If a utility class has low coverage, either add targeted tests or switch to `RunLocalTests` for that deployment.

---

## Gotcha 3: `@isTest(isParallel=true)` Can Cause Intermittent Failures

**What happens:** Tests that pass individually start failing intermittently when run as part of a CI suite. Errors include `UNABLE_TO_LOCK_ROW`, unexpected DML failures, or assertion failures on data counts.

**When it occurs:** When test classes annotated with `@isTest(isParallel=true)` share mutable org state -- custom settings, custom metadata records created with `SeeAllData=true`, or platform objects with unique constraints. Parallel execution means multiple tests modify the same records simultaneously.

**How to avoid:** Only apply `isParallel=true` to test classes that are fully isolated -- they create all their own data, do not use `SeeAllData=true`, and do not rely on unique field values that could collide. For CI pipelines, if intermittent failures appear, check whether parallel-annotated tests are the cause by temporarily removing the annotation and verifying stability.

---

## Gotcha 4: Deployment Validation IDs Expire After 10 Days

**What happens:** A team validates a deployment on Monday using `sf project deploy validate`, captures the validation ID, then tries to run `sf project deploy quick --job-id <id>` the following Monday. The quick deploy fails with an invalid or expired job ID error.

**When it occurs:** Salesforce deployment validation results expire after 10 days (240 hours). Any quick-deploy attempt after that window requires a fresh validation. This catches teams with long approval cycles or release windows that span more than a week.

**How to avoid:** Design the CI pipeline so validation happens close to the deployment window -- ideally within the same day. If approvals take longer, re-validate before quick-deploying. Store the validation timestamp alongside the job ID so the pipeline can detect expiration proactively.

---

## Gotcha 5: `--synchronous` Flag Limits Test Class Count

**What happens:** A CI pipeline uses `--synchronous` to avoid the 0% coverage bug, but starts failing when the number of test classes exceeds the platform limit for synchronous execution.

**When it occurs:** Synchronous test execution is designed for smaller test suites. When the number of test classes or total test methods exceeds the synchronous limit, the platform either rejects the request or silently switches to asynchronous execution, reintroducing the coverage reporting issue.

**How to avoid:** Use `--synchronous` only for small, targeted test runs (e.g., `RunSpecifiedTests` with a handful of classes). For `RunLocalTests` or large suites, use the asynchronous path with the two-step coverage retrieval workaround.
