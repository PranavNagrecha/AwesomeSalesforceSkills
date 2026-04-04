# Well-Architected Notes — sf CLI and SFDX Essentials

## Relevant Pillars

- **Security** — Authentication method selection has direct security implications. JWT bearer token auth with certificate-based Connected Apps is more secure than storing passwords or tokens in environment variables. Private key files must never be committed to version control. The Connected App's OAuth policy (pre-authorized users) controls the blast radius of a compromised credential.

- **Reliability** — Scratch orgs are ephemeral by design (1–30 days). Teams that rely on scratch orgs for integration testing must rebuild them on demand. Source control must be the single source of truth — not the org itself. Validate-then-Quick-Deploy patterns improve production deploy reliability by separating test execution from deployment.

- **Operational Excellence** — The Salesforce DX workflow (scratch org → push → pull → deploy) automates and standardizes the developer feedback loop. Consistent use of aliases, default org config, and project structure prevents human errors in multi-environment workflows. Storing package.xml manifests in version control alongside the skill makes retrieval and deployment repeatable.

---

## Architectural Tradeoffs

**Web flow auth vs JWT auth:**
Web flow stores a durable refresh token on the local machine. JWT auth requires a Connected App with a certificate and produces only short-lived access tokens. Web flow is easier to set up for developers but cannot run in headless CI environments. JWT is required for pipelines but requires upfront certificate management.

**Source tracking (scratch org) vs manifest-driven (sandbox/production):**
Source tracking reduces cognitive load — the CLI knows what changed. But it only works on scratch orgs. For shared environments (sandboxes, production), explicit manifests are required. Teams that use both must clearly separate their tooling conventions to avoid accidentally deploying nothing (no-op push to sandbox) or deploying too much (overly broad manifest).

**Quick Deploy vs regular deploy:**
Quick Deploy skips Apex test re-execution by reusing a validated deployment. This reduces production deployment time substantially for orgs with large test suites. The tradeoff is that the validation window is 10 days — after that, the validation expires and must be re-run.

---

## Anti-Patterns

1. **Committing private key files or access tokens to the repository** — JWT auth requires a private key (`.key`, `.pem`). Teams sometimes commit these alongside the pipeline configuration "for convenience." A committed key gives any repository reader the ability to authenticate as the deploying user. Always store credentials in environment secrets (GitHub Actions secrets, Vault, etc.) and add key file patterns to `.gitignore`.

2. **Using scratch org push/pull for sandbox deployments** — Source tracking is not available on sandboxes. Developers accustomed to scratch org workflows sometimes omit the `--source-dir` or `--manifest` flag on sandbox deploys, causing zero-component deployments that succeed silently. Enforce explicit scope flags in sandbox and production deploy scripts.

3. **Never running `sf project deploy validate` before production deploys** — Deploying directly to production without a prior validation skips the opportunity to catch test failures in a zero-impact way. The validate-then-quick-deploy pattern separates test execution from the actual deployment window, reducing production risk.

---

## Official Sources Used

- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm — Source-driven development, scratch org lifecycle, project structure
- Salesforce CLI Command Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm — Command flags, output formats, and pipeline automation options
- Salesforce Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm — Retrieve/deploy behavior, source tracking, package.xml structure, source format vs mdapi format
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — Architecture quality model, operational excellence guidance
