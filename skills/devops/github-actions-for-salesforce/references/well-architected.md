# Well-Architected Notes — GitHub Actions for Salesforce

## Relevant Pillars

- **Security** — The JWT Bearer Flow is the only supported non-interactive authentication method for CI pipelines per the Salesforce DX Developer Guide. Storing credentials in GitHub Secrets (not repository files or plain environment variables), scoping Connected App permissions to the minimum required, using per-environment credentials, and cleaning up temp key files enforces the principle of least privilege and secrets isolation. An improperly secured pipeline can expose org credentials to any contributor with `run:` access.

- **Operational Excellence** — A well-designed GitHub Actions pipeline is the operational backbone of a Salesforce development team. It enforces code coverage thresholds automatically, catches metadata conflicts before merge, makes deployment steps repeatable and auditable, and produces structured test result artifacts. Without it, teams rely on manual validation steps that are inconsistently applied. Key operational practices: explicit `--test-level`, branch guards on deploy steps, `if: always()` cleanup, and test result artifact uploads.

- **Reliability** — The pipeline must produce consistent results across runs. Reliability risks include flaky tests that fail intermittently (causing false negatives), scratch org daily limit exhaustion causing mid-day outages, and JWT cert expiry causing sudden unrecoverable failures. Reliability patterns: persistent sandboxes for integration tests, cert expiry monitoring, unique alias naming for parallel jobs, and timeout flags (`--wait N`) on all deploy and test commands.

## Architectural Tradeoffs

**GitHub Actions vs. Salesforce DevOps Center:** GitHub Actions gives full YAML control, integrates with any external tool, and works with any branching strategy. DevOps Center provides a Salesforce-native UI, is suitable for admin-led teams, and handles work item tracking natively — but it does not expose raw YAML, limits custom logic, and requires the DevOps Center managed package. GitHub Actions is the right choice for developer-led teams with complex pipelines; DevOps Center is better for low-code teams that want source control benefits without CI/CD investment.

**Scratch orgs vs. sandboxes for CI testing:** Scratch orgs provide complete isolation per run and can be seeded with known data, making them ideal for deterministic unit tests. However, they incur daily allocation limits, require Dev Hub, and add 2-5 minutes of provisioning time per job. Sandboxes are persistent, have no daily creation limit, but require manual refresh scheduling and shared state between runs can cause flaky tests. Recommended hybrid: scratch orgs for unit/component tests in PR jobs, persistent sandboxes for integration and end-to-end validation.

**Single workflow file vs. reusable workflows:** A single `deploy.yml` is simple to manage for small teams. As the repo grows, extract shared steps (auth, test, deploy) into reusable workflow files (`/.github/workflows/reusable-auth.yml`) and call them with `uses:`. This avoids copy-paste drift across multiple pipelines and makes credential rotation a single-file change.

## Anti-Patterns

1. **Storing `server.key` in the repository** — Even in a private repo, the private key in git history is a persistent credential leak. Any future fork, contributor, or access incident exposes the key. Always use GitHub Secrets and write the key to a temp file at runtime. Rotate immediately if the key was ever committed.

2. **Using `sfdx force:*` deprecated commands in new pipelines** — The legacy command namespace produces deprecation warnings that obscure real errors, uses different flag names than `sf` v2, and will be removed in a future CLI version. All new pipelines must use `sf` CLI v2 commands (`sf org login jwt`, `sf project deploy start`, `sf apex run test`).

3. **Omitting `--test-level` from deploy commands** — Relying on platform defaults leads to untested sandbox deploys that fail silently on coverage. Every deploy command must specify `--test-level` explicitly. This is especially critical for sandbox environments where the platform does not enforce coverage at deploy time.

4. **Single global credential for all environments** — Using the same Connected App and consumer key for sandbox, staging, and production means a compromised sandbox credential can be used against production. Use separate Connected Apps (or at minimum separate pre-authorized users with the same Connected App) per environment, stored in GitHub Environment secrets.

## Official Sources Used

- Salesforce DX Developer Guide — JWT-Based Flow: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_jwt_flow.htm
- Salesforce DX Developer Guide — GitHub Actions CI: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_ci_github.htm
- Salesforce CLI Command Reference: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide (Introduction): https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce Well-Architected: Operational Excellence: https://architect.salesforce.com/well-architected/operational-excellence
- Salesforce Well-Architected: Security: https://architect.salesforce.com/well-architected/security
