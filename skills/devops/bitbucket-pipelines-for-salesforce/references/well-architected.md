# Well-Architected Notes — Bitbucket Pipelines for Salesforce

## Relevant Pillars

### Operational Excellence

Bitbucket Pipelines is the primary enabler of Operational Excellence for Salesforce DX projects hosted in Bitbucket. The Well-Architected framework's Operational Excellence pillar calls for automating deployment processes, eliminating manual steps, and ensuring repeatable, auditable change delivery. A well-structured `bitbucket-pipelines.yml` with branch-based promotion, test gating, and `deployment:` labels achieves all three:

- **Automation:** Every push to `feature/**`, `develop`, or `main` triggers the correct action (validate, deploy to sandbox, or deploy to production) without human intervention.
- **Repeatability:** The same YAML-defined sequence runs identically on every execution; no developer-local environment variation.
- **Auditability:** Bitbucket Deployment environments record every production deployment with the committer, timestamp, and build log URL — fulfilling change management audit requirements.

### Security

Per the Salesforce Well-Architected Security pillar, credentials must never be embedded in source code and all non-interactive authentication should use the JWT Bearer Flow with a Connected App. Bitbucket Pipelines implements this through:

- **Secured (masked) repository variables:** Private key contents and consumer keys stored as masked variables are never printed in build logs, even when accidentally echoed.
- **JWT Bearer Flow:** The private key is written to a temp file per-run and deleted in `after-script:`. No long-lived session token is stored at rest.
- **Per-environment credential isolation:** Separate Connected Apps and separate Bitbucket variable sets per environment ensure a compromised sandbox credential cannot authenticate to production.
- **Least privilege:** The Connected App's OAuth Policies use "Admin approved users are pre-authorized" — only explicitly listed users can authenticate via JWT, not any user in the org.

### Reliability

The Reliability pillar requires that deployments are predictable and that failures do not leave systems in an inconsistent state. Key reliability patterns for Bitbucket Pipelines Salesforce CI:

- **Validate before deploy:** `sf project deploy validate` on feature branches detects metadata or test failures before they reach a shared sandbox or production.
- **Explicit test levels:** Always specifying `--test-level` prevents silent skipping of Apex tests, which would allow untested code to reach production.
- **`after-script:` cleanup:** Ensures the build environment is left clean (no dangling key files) regardless of step outcome.
- **Certificate rotation reminders:** Tracking cert expiry prevents the sudden `INVALID_SESSION_ID` failures that bring pipelines down without code changes.

---

## Architectural Tradeoffs

### JWT Bearer Flow vs. SFDP URL Authentication

JWT Bearer Flow is the architecturally preferred method for CI/CD per the Salesforce DX Developer Guide. It generates a new access token on each run using a static private key — no session or refresh token is stored at rest. SFDP URL authentication embeds a refresh token that can be revoked, expired, or rotated without warning, causing intermittent pipeline failures. For any pipeline running more than weekly, use JWT Bearer Flow.

### Bitbucket Pipelines vs. Atlassian `salesforce-deploy` Pipe

Atlassian publishes an `atlassian/salesforce-deploy` pipe that wraps SFDX commands. While convenient for initial setup, the pipe abstracts away CLI flags and version pinning, making it harder to audit exactly which CLI version and which commands run. For teams that need predictable, auditable, upgrade-controlled pipelines, installing `@salesforce/cli@latest` directly and invoking `sf` commands explicitly is preferable. Use the pipe only for prototyping or when the team explicitly accepts the abstraction tradeoff.

### Ephemeral Scratch Orgs vs. Persistent Sandbox for CI

Using a scratch org per PR provides complete environment isolation but consumes daily scratch org allocations (6 for Developer Edition Dev Hub, more for Enterprise). For active repositories with many daily PRs, persistent sandbox-based testing is more reliable. Scratch orgs are architecturally appropriate for ISV development where feature isolation is critical; persistent sandboxes are appropriate for org-development teams with predictable daily PR volumes.

---

## Anti-Patterns

1. **Hardcoding org usernames and instance URLs directly in `bitbucket-pipelines.yml`** — Committing usernames and `https://test.salesforce.com` vs. `https://login.salesforce.com` flags directly in the YAML couples the pipeline to a specific environment configuration. When the org username changes (e.g., after a sandbox refresh) or the team adds a new environment, the YAML must be edited. Instead, externalize all org-specific values into Bitbucket repository variables (`SF_USERNAME`, `SF_INSTANCE_URL`) so the YAML only references variable names and environment-specific values are set at the repository level.

2. **Using a single Connected App and shared credentials across all environments** — Sharing one Connected App (and one set of secrets) between sandbox and production means a compromised CI credential grants production access. This violates the Security pillar's principle of environment isolation. Each environment (dev sandbox, full sandbox, production) should have its own Connected App, its own certificate, and its own set of Bitbucket secured variables.

3. **Relying on the `atlassian/salesforce-deploy` pipe without pinning its version** — Using `atlassian/salesforce-deploy:0` (floating major version) means a non-breaking change to the pipe's minor version can silently change behavior in production deployments. Pin to a specific pipe version (e.g., `atlassian/salesforce-deploy:0.5.0`) and treat pipe version upgrades as a deliberate, tested change.

---

## Official Sources Used

- Salesforce DX Developer Guide (SFDX Introduction) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce DX Developer Guide (JWT Bearer Flow for CI) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_jwt_flow.htm
- Salesforce CLI Command Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Bitbucket Pipelines Get Started Guide — https://support.atlassian.com/bitbucket-cloud/docs/get-started-with-bitbucket-pipelines/
- Bitbucket Repository Variables Documentation — https://support.atlassian.com/bitbucket-cloud/docs/variables-and-secrets/
