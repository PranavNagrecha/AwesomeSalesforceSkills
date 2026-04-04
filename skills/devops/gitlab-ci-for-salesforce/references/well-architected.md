# Well-Architected Notes — GitLab CI for Salesforce

## Relevant Pillars

- **Security** — The most critical pillar for CI/CD pipelines. All Salesforce org credentials (private key, consumer key, username) must be stored as masked and protected GitLab CI/CD variables — never committed to the repository or echoed in job logs. JWT Bearer Flow is the only recommended non-interactive auth method per the Salesforce DX Developer Guide; it avoids storing live refresh tokens. Production credentials must be additionally marked "Protected" to restrict access to protected branches only.

- **Operational Excellence** — The pipeline codifies the deployment process as auditable, repeatable automation. Using `stages:` with explicit ordering, `needs:` DAG dependencies, `when: manual` gates on production, and `environment:` declarations creates a deployment workflow that is visible, traceable, and reviewable in GitLab's Environments and Pipeline views. `artifacts:` on test jobs ensures Apex test results are retained for post-job audit even after the runner container is torn down.

- **Reliability** — An `after_script:` block on every job that writes a temporary key file guarantees cleanup runs even if the main `script:` block fails mid-way. Explicit `--wait` flags on `sf project deploy start` and `sf apex run test` prevent jobs from returning a false success while operations are still pending. The `needs:` DAG ensures the deploy job cannot run if the test job fails — preventing a coverage-below-threshold deployment from reaching the org.

## Architectural Tradeoffs

**Docker executor vs. shell executor:** Docker executor (recommended) provides a clean container per job with no stale CLI state, reproducible Node.js version, and full isolation between jobs. Shell executor reuses the runner host's environment, which can have leftover `~/.sf/` credential state from previous jobs, inconsistent CLI versions, and race conditions when parallel jobs share the same org alias. The tradeoff is that Docker executor requires a Docker-capable runner and image pull time. For Salesforce CI, the isolation benefit of Docker executor outweighs the setup cost.

**Shared runners vs. self-managed runners:** GitLab SaaS shared runners have compute minute quotas (400 minutes/month on the free tier). Salesforce metadata deploys and Apex test runs are slow — a single deploy job can consume 20–30 minutes. Teams with frequent CI activity should use self-managed runners on their own infrastructure to avoid quota exhaustion. The tradeoff is runner maintenance overhead.

**JWT Bearer Flow vs. SFDP URL auth:** JWT Bearer Flow generates a new short-lived access token on every CI run; the stored credential is only a private key, not a live session token. SFDP URL embeds an OAuth refresh token with an unpredictable session lifetime that can be invalidated by org policy changes. For CI/CD, JWT is the correct choice per the Salesforce DX Developer Guide.

**`when: manual` on production:** Requiring a manual approval click before production deploy is the standard safeguard against accidental automated pushes. The tradeoff is a human bottleneck in the deployment flow. Teams that want full automation should implement a pre-production integration environment and a strict branch protection model (no direct pushes to `main`) rather than removing the manual gate.

## Anti-Patterns

1. **Storing raw private key content as a GitLab CI variable** — GitLab's masking system rejects multi-line values, so the variable cannot be masked. An unmasked private key can appear in job logs. The correct pattern is to base64-encode the key (`base64 -w 0 server.key`), store the single-line encoded value as a masked variable, and decode it in the job script (`base64 -d`).

2. **Relying on `only:`/`except:` for branch-conditional deploy logic** — The older `only:` syntax has documented matching inconsistencies, does not support `$CI_PIPELINE_SOURCE` conditions, and cannot express `when: manual` or complex conditional logic. Pipelines using `only:` will produce unexpected behavior when merge request pipelines coexist with push pipelines. Always use `rules:`.

3. **Omitting `--test-level` from `sf project deploy start`** — When `--test-level` is absent on a sandbox deploy, Salesforce defaults to `NoTestRun`, meaning zero Apex tests run and zero coverage is checked. Teams discover this only when a later production deploy fails the 75% threshold. Always specify `--test-level` explicitly on every deploy command.

## Official Sources Used

- Salesforce DX Developer Guide (JWT Bearer Flow for CI) — JWT authentication flow, Connected App setup requirements, non-interactive auth for CI/CD pipelines
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_ci_jwt.htm

- Salesforce DX Developer Guide (SFDX Introduction) — SFDX project structure, sfdx-project.json, source format overview
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm

- Salesforce CLI Command Reference — `sf org login jwt`, `sf project deploy start`, `sf project deploy validate`, `sf apex run test` command syntax and flags
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm

- Metadata API Developer Guide — Deployment behavior, test levels (RunLocalTests, RunAllTestsInOrg, NoTestRun), 75% coverage enforcement
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm

- Salesforce Well-Architected Overview — Operational Excellence, Security, and Reliability pillar guidance
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
