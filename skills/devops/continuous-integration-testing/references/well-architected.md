# Well-Architected Notes — Continuous Integration Testing

## Relevant Pillars

- **Reliability** -- CI testing is the primary mechanism for catching regressions before they reach production. A well-configured test pipeline with appropriate test levels, coverage enforcement, and failure handling ensures that deployments do not introduce defects. Unreliable CI (flaky tests, ignored failures, missing coverage gates) directly undermines the reliability of the production org.

- **Operational Excellence** -- automated test execution removes manual toil from the deployment process. Consistent test levels, JUnit reporting, and coverage trend tracking give teams visibility into the health of their codebase without requiring individual developers to remember to run tests. Pipeline-as-code (YAML/Jenkinsfile checked into version control) makes the testing process auditable and repeatable.

- **Performance** -- test execution time directly affects developer productivity. Choosing `RunSpecifiedTests` for PR builds versus `RunLocalTests` for production deployments is a performance-conscious architectural decision. Parallel test execution via `@isTest(isParallel=true)` can reduce suite runtime but must be balanced against isolation requirements.

- **Security** -- CI pipelines handle org credentials (JWT keys, auth URLs, connected app secrets). Secure credential management is essential: secrets must be stored in the CI platform's secret store, never in source code. Service accounts used for CI should have minimum necessary permissions, and connected apps should be scoped to the deployment user profile.

## Architectural Tradeoffs

The central tradeoff in CI testing configuration is **speed versus coverage confidence**:

- `RunSpecifiedTests` is fast (minutes) but only validates the classes you name. If your test mapping is incomplete, regressions in untested code slip through. The per-class 75% enforcement is stricter, which catches some gaps but not cross-class interaction bugs.
- `RunLocalTests` is comprehensive (all local tests) but slow in large orgs (30-90+ minutes). It catches interaction bugs and enforces org-wide coverage but makes PR feedback loops painful.
- The two-stage pattern (fast PR validation with `RunSpecifiedTests`, full `RunLocalTests` on merge to main) balances both concerns but requires maintaining accurate test-to-class mappings.

A secondary tradeoff is **synchronous versus asynchronous execution**. Synchronous runs avoid the 0% coverage bug and are simpler to script, but are limited to smaller test suites. Asynchronous runs scale to any org size but require the two-step coverage retrieval workaround.

## Anti-Patterns

1. **No coverage enforcement beyond Salesforce's built-in 75%** -- relying solely on the platform's deployment gate means coverage can erode to exactly 75% over time. Teams that enforce higher thresholds (80-85%) with pipeline scripts maintain healthier codebases because the gate catches gradual degradation before it becomes a deployment blocker.

2. **RunAllTestsInOrg as the default test level** -- this runs managed package tests that the team cannot fix, creating flaky builds and eroding trust in the pipeline. Developers start ignoring CI failures or adding retry logic that masks real problems. Use `RunLocalTests` and reserve `RunAllTestsInOrg` for explicit compatibility checks.

3. **Ignoring test results and deploying anyway** -- some teams configure pipelines with `continue-on-error: true` or `|| true` after test commands to avoid blocking deployments. This defeats the purpose of CI entirely. If tests are too slow or flaky to be a reliable gate, fix the tests rather than bypassing the gate.

## Official Sources Used

- Apex Developer Guide — Testing Best Practices — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing.htm
- Metadata API Developer Guide — Deploy — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm
- Salesforce CLI Reference — Apex Commands — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_apex.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
