---
name: github-actions-for-salesforce
description: "Use this skill to set up, review, or troubleshoot GitHub Actions CI/CD pipelines for Salesforce using SFDX JWT Bearer Flow authentication, Apex test gates, and branch-conditional deployments. Trigger keywords: github actions, CI pipeline, jwt auth, sfdx ci, workflow yaml, github secrets, apex coverage threshold. NOT for other CI tools such as Jenkins, Copado, Bitbucket Pipelines, or Azure DevOps."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "how do I set up GitHub Actions to deploy to Salesforce automatically on merge to main"
  - "my Salesforce CI pipeline is failing with authentication or JWT errors in GitHub Actions"
  - "how do I run Apex tests with a code coverage threshold gate in a GitHub Actions workflow"
  - "I need to audit an existing GitHub Actions Salesforce pipeline for security or best-practice gaps"
  - "GitHub Actions deploy step fails with INVALID_SESSION_ID or expired certificate"
tags:
  - github-actions
  - ci-cd
  - jwt-bearer-flow
  - sfdx
  - apex-testing
  - secrets-management
inputs:
  - GitHub repository with Salesforce DX project structure (sfdx-project.json present)
  - Connected App configured in target Salesforce org with OAuth JWT Bearer Flow enabled
  - Server private key (server.key) and consumer key (client_id) for JWT authentication
  - Target org username or login URL
  - Branch naming convention for environment promotion (e.g., feature/* → sandbox, main → production)
outputs:
  - GitHub Actions workflow YAML (.github/workflows/deploy.yml) ready to commit
  - Guidance on securely storing CONSUMER_KEY and SERVER_KEY in GitHub Secrets
  - Apex test run command with --code-coverage and threshold enforcement
  - Review findings or troubleshooting diagnosis for an existing pipeline
dependencies:
  - devops/scratch-org-management
  - apex/sf-cli-and-sfdx-essentials
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# GitHub Actions for Salesforce

This skill activates when a practitioner needs to build, review, or fix a GitHub Actions CI/CD pipeline that deploys Salesforce metadata and runs Apex tests using the Salesforce CLI and JWT Bearer Flow authentication. It covers all three operating modes: initial setup from scratch, pipeline audit/review, and live troubleshooting of CI failures.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Connected App status:** Is a Connected App already configured in the target org with a self-signed certificate uploaded and OAuth JWT Bearer Flow enabled? If not, that must be done first — GitHub Actions cannot authenticate without it.
- **Org type:** Is the target a sandbox, production, or scratch org? Sandbox uses `--instance-url https://test.salesforce.com`; production uses the default login URL. Scratch orgs require Dev Hub authentication first and are daily-limited.
- **Branch strategy:** Which branches correspond to which environments? The workflow's `if:` conditions must match the team's actual branching model (e.g., `main` → production, `develop` → full sandbox).
- **Most common wrong assumption:** Teams often store the raw `server.key` content directly in a GitHub Secret and then try to reference it as a file path. GitHub Secrets are environment variables, not files. The key content must be written to a temp file at runtime before `sf org login jwt` can reference it.
- **Platform limits:** Scratch org daily allocation limits (6 for Developer Edition, 40+ for Enterprise) apply to CI pipelines. If every PR spins up a scratch org, limits exhaust quickly in active repos.

---

## Core Concepts

### JWT Bearer Flow Authentication

The Salesforce CLI's `sf org login jwt` command authenticates a CI runner non-interactively using a private key and a Connected App. Per the Salesforce DX Developer Guide, the flow works as follows:

1. A self-signed X.509 certificate is generated (`openssl req -x509 -nodes -sha256 -days 365 -newkey rsa:2048 -keyout server.key -out server.crt`).
2. The `.crt` file is uploaded to a Connected App in Salesforce (Setup > App Manager > Edit > Upload Certificate).
3. The `server.key` is stored as a GitHub Secret (e.g., `SF_JWT_SERVER_KEY`). The consumer key (client ID) from the Connected App is stored as a second secret (`SF_CONSUMER_KEY`).
4. In the workflow, the key content is written to a temporary file and passed via `--jwt-key-file`. The `--username` flag must match the pre-authorized user on the Connected App.

The certificate has a finite lifespan (default 365 days with the OpenSSL command above). Expiry is the most common source of sudden, unexplained CI auth failures.

### `sf` CLI vs. Legacy `sfdx` Commands

As of Spring '25, Salesforce has unified the CLI under `sf` (Salesforce CLI v2). The legacy `sfdx force:*` namespace still works but is deprecated. All new pipelines should use `sf project deploy start` (not `sfdx force:source:deploy`) and `sf apex run test` (not `sfdx force:apex:test:run`). Mixing old and new command namespaces in a single workflow causes confusing output and will break when the deprecated commands are removed.

### GitHub Secrets and Environment Variables

GitHub Secrets are available to workflow steps as environment variables. They are masked in logs. The correct pattern for injecting a multi-line secret (like a private key) is:

```yaml
- name: Write JWT key to file
  run: echo "$SF_JWT_SERVER_KEY" > /tmp/server.key
  env:
    SF_JWT_SERVER_KEY: ${{ secrets.SF_JWT_SERVER_KEY }}
```

Do not commit `server.key` to the repository. Do not use GitHub Variables (unencrypted) for any credential. Repository-level secrets are available to all workflows; use Environment secrets (under Settings > Environments) if you need per-environment credential isolation.

### Apex Test Gating with Coverage Thresholds

The `sf apex run test` command supports `--code-coverage` to collect per-class coverage. Deployment via `sf project deploy start` enforces the platform's 75% org-wide threshold at the time of deploy if you use `--test-level RunLocalTests` or `RunAllTestsInOrg`. For finer control in CI — fail the build before deployment if a specific threshold is not met — run tests separately first, parse the JSON results, and use a shell check to fail the step.

---

## Common Patterns

### Mode 1: Set Up GitHub Actions from Scratch

**When to use:** No `.github/workflows/` directory exists yet, or the existing workflow is a placeholder. Team wants push-to-deploy with Apex test gating.

**How it works:**

Step 1 — Generate and upload the JWT cert (done once, outside CI):
```bash
openssl req -x509 -nodes -sha256 -days 365 -newkey rsa:2048 \
  -keyout server.key -out server.crt \
  -subj "/C=US/ST=CA/L=SF/O=MyOrg/CN=ci-service"
```
Upload `server.crt` to the Connected App in Salesforce. Store `server.key` content and the Connected App consumer key in GitHub Secrets.

Step 2 — Create `.github/workflows/deploy.yml`. The minimal structure:

```yaml
name: Salesforce CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Salesforce CLI
        run: npm install --global @salesforce/cli@latest

      - name: Write JWT server key
        run: echo "$SF_JWT_SERVER_KEY" > /tmp/server.key
        env:
          SF_JWT_SERVER_KEY: ${{ secrets.SF_JWT_SERVER_KEY }}

      - name: Authenticate to target org
        run: |
          sf org login jwt \
            --client-id "$SF_CONSUMER_KEY" \
            --jwt-key-file /tmp/server.key \
            --username "$SF_USERNAME" \
            --alias target-org \
            --set-default
        env:
          SF_CONSUMER_KEY: ${{ secrets.SF_CONSUMER_KEY }}
          SF_USERNAME: ${{ secrets.SF_USERNAME }}

      - name: Run Apex tests with coverage
        run: |
          sf apex run test \
            --target-org target-org \
            --test-level RunLocalTests \
            --code-coverage \
            --result-format json \
            --output-dir test-results \
            --wait 20

      - name: Enforce 75% coverage threshold
        run: |
          COVERAGE=$(python3 -c "
          import json, sys
          with open('test-results/test-result.json') as f:
              data = json.load(f)
          pct = data.get('summary', {}).get('orgWideCoverage', '0%').replace('%','')
          print(pct)
          ")
          echo "Org-wide coverage: ${COVERAGE}%"
          python3 -c "assert float('${COVERAGE}') >= 75, 'Coverage below 75%'"

      - name: Deploy to target org (main branch only)
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: |
          sf project deploy start \
            --target-org target-org \
            --source-dir force-app \
            --test-level NoTestRun \
            --wait 30

      - name: Remove JWT key file
        if: always()
        run: rm -f /tmp/server.key
```

**Why not a simpler approach:** Using `sfdx auth:jwt:grant` (old namespace) or hard-coding credentials as plain text environment variables violates the Connected App isolation model and creates credential-in-log risks.

### Mode 2: Reviewing/Auditing an Existing Pipeline

**When to use:** A pipeline exists but the team suspects it has security gaps, uses deprecated commands, or has flaky test failures.

**How it works:**

Check for these items in order:

1. **Auth method** — Is `sf org login jwt` used (correct) or `sf org login web`/`sfdx auth:sfdxurl:store` (wrong for CI)?
2. **Secrets hygiene** — Are credentials referenced via `${{ secrets.X }}`? Are any credentials echoed to stdout in `run:` blocks without masking?
3. **CLI version** — Is `sfdx force:*` (deprecated) or `sf` (current) used?
4. **Test level** — Is `RunLocalTests` or `RunAllTestsInOrg` specified, or is `--test-level` omitted (defaults to `NoTestRun`, which skips coverage)?
5. **Branch conditions** — Does the `if:` guard on the deploy step correctly target only the intended branch and event type?
6. **Key cleanup** — Is there an `if: always()` step to delete the temporary `server.key` file even when earlier steps fail?
7. **Certificate expiry** — When was the certificate generated? Check the Connected App in Setup for the expiry date.

### Mode 3: Troubleshooting CI Failures

**When to use:** A previously working pipeline starts failing.

**Common failure patterns and fixes:**

| Symptom | Root Cause | Fix |
|---|---|---|
| `INVALID_SESSION_ID` or `expired access/refresh token` | JWT cert expired (365-day default) | Regenerate cert, re-upload to Connected App, update secret |
| `No org found for alias target-org` | Auth step failed silently; later steps reference unregistered alias | Add `--set-default` to login step; check `sf org list` in a debug step |
| `Deploy failed: Test coverage of classes is 0%` | `--test-level NoTestRun` used on production deploy | Use `RunLocalTests` or pre-validate coverage in a separate step |
| `ECONNREFUSED` or timeout on `sf apex run test` | Scratch org Daily limit hit or org was deleted | Switch to sandbox-based testing; check scratch org limits in Dev Hub |
| `Error: Can't set default org` | Username not authorized on Connected App | Verify pre-authorized users in the Connected App's OAuth Policies section |

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Pull request validation only (no deploy) | `sf project deploy validate` with `--dry-run` | Validates metadata and runs tests without committing to the org; idempotent |
| Deploy on merge to main (production) | `sf project deploy start` with `--test-level RunLocalTests` | Enforces platform 75% threshold at deploy time; no double-test overhead |
| Feature branch with ephemeral scratch org | Create scratch org, run tests, delete org | Org-per-PR isolation; be mindful of daily scratch org limits |
| Sandbox promotion (develop → staging) | `sf project deploy start` with `--target-org sandbox-alias` and JWT auth per environment | Use separate GitHub Environment secrets per environment for credential isolation |
| Rollback after failed production deploy | Trigger a revert PR and re-run the pipeline | Salesforce does not support automated rollback via CLI; rollback is a new deploy |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking the pipeline complete:

- [ ] `server.key` is stored in GitHub Secrets, never committed to the repository
- [ ] JWT certificate uploaded to Connected App and not expired (check expiry date in Setup)
- [ ] `--test-level` is explicitly set; never rely on the default `NoTestRun` for sandbox or production deploys
- [ ] Deploy step has a branch/event `if:` guard; PR runs validate only, not deploy
- [ ] `if: always()` cleanup step removes `/tmp/server.key` after every run
- [ ] CLI version is `sf` (v2), not deprecated `sfdx force:*` commands
- [ ] Separate GitHub Environments (with environment secrets) used for sandbox vs. production credentials
- [ ] Apex test results are captured in `--output-dir` and uploaded as workflow artifacts for audit

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Scratch org daily limits exhaust silently** — Developer Edition Dev Hub allows only 6 scratch orgs per day across all users and CI runs. If your `on: pull_request` trigger fires frequently, you will hit this limit mid-day. The error (`LIMIT_EXCEEDED: You have reached the daily scratch org creation limit`) appears in the auth/create step and is easy to misread as a credential error. Prevention: use scratch orgs only for isolated unit tests; use a persistent sandbox for integration tests in high-activity repos.

2. **JWT certificate expiry has no warning** — Salesforce does not send any notification when a JWT certificate uploaded to a Connected App is nearing expiry. The pipeline simply starts returning `INVALID_SESSION_ID` on the renewal date. Prevention: set a calendar reminder or GitHub Actions scheduled job to alert 30 days before the cert's 365-day (or configured) lifespan ends. Rotate the cert and update GitHub Secrets before expiry.

3. **Parallel jobs writing to the same alias conflict** — When a workflow has multiple jobs running in parallel (e.g., unit-tests job and integration-tests job both run `sf org login jwt --alias target-org`), they share the `~/.sf/` credential store on the runner. The second login overwrites the first alias entry. Fix: use unique aliases per job (`--alias target-org-${{ github.run_id }}-unit`) or use matrix strategy with per-job environment isolation.

4. **`NoTestRun` is the silent default for `sf project deploy start`** — If `--test-level` is omitted from a deploy command targeting a production org, the CLI defaults to `RunSpecifiedTests` or `NoTestRun` depending on context, and Salesforce enforces 75% at the platform level only if tests are actually run. Omitting the flag on a sandbox deploy means zero tests run and zero coverage is checked. Always specify `--test-level` explicitly.

5. **Connected App "Pre-authorize users" must be configured** — JWT authentication silently fails if the org's Connected App does not have the authenticating user listed under "Manage Connected Apps > OAuth Policies > Pre-authorize users" (Permitted Users: Admin approved users are pre-authorized). Adding the user to the profile or permission set assigned to the Connected App is not sufficient — the explicit pre-authorization step is required.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `.github/workflows/deploy.yml` | Complete GitHub Actions workflow YAML with JWT auth, test gate, branch-conditional deploy, and cleanup |
| `test-results/` directory | JSON and JUnit XML Apex test output produced by `sf apex run test --output-dir` |
| Pipeline audit findings | Ordered list of security and best-practice gaps found in an existing workflow file |
| Troubleshooting diagnosis | Root cause and fix for a specific CI failure symptom |

---

## Related Skills

- `devops/scratch-org-management` — Use when the pipeline needs per-PR ephemeral scratch org creation, limits management, or automated deletion after the job completes
- `apex/sf-cli-and-sfdx-essentials` — Use for `sf` CLI command reference, auth patterns, and metadata deploy/retrieve CLI details
- `devops/devops-center-pipeline` — Alternative to GitHub Actions for teams that want a Salesforce-native UI-driven pipeline without writing YAML
