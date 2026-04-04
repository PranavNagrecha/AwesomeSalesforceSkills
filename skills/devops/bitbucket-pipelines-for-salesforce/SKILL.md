---
name: bitbucket-pipelines-for-salesforce
description: "Use this skill to set up, review, or troubleshoot Bitbucket Pipelines CI/CD workflows for Salesforce using SFDX JWT Bearer Flow or SFDP URL authentication, Apex test gates, branch-based deployment strategies, and Bitbucket repository variables for secret management. Trigger keywords: bitbucket pipelines, bitbucket CI, atlassian pipe, salesforce-deploy pipe, bitbucket-pipelines.yml, bitbucket repository variables. NOT for GitHub Actions (use github-actions-for-salesforce), Jenkins, Copado, Azure DevOps, or any non-Bitbucket CI platform."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
  - Reliability
triggers:
  - "how do I set up Bitbucket Pipelines to deploy Salesforce metadata automatically when I push to main"
  - "my Bitbucket Pipelines Salesforce CI job is failing with authentication or JWT errors"
  - "how do I run Apex tests with a coverage threshold gate in Bitbucket Pipelines for Salesforce"
  - "I need to review an existing bitbucket-pipelines.yml for security gaps or best-practice issues"
  - "how do I store Salesforce credentials securely in Bitbucket repository variables for CI"
  - "the atlassian/salesforce-deploy pipe fails with INVALID_SESSION_ID or connection errors"
tags:
  - bitbucket-pipelines
  - ci-cd
  - jwt-bearer-flow
  - sfdx
  - apex-testing
  - secrets-management
inputs:
  - Bitbucket repository with Salesforce DX project structure (sfdx-project.json present)
  - Connected App configured in target Salesforce org with OAuth JWT Bearer Flow enabled
  - Server private key (server.key) and consumer key (client_id) for JWT authentication, OR an SFDP URL stored as a Bitbucket repository variable
  - Target org username and login URL (test.salesforce.com for sandbox, login.salesforce.com for production)
  - Branch naming convention for environment promotion (e.g., feature/* → developer sandbox, develop → full sandbox, main → production)
outputs:
  - bitbucket-pipelines.yml ready to commit with branch-conditional deploy, JWT auth, Apex test gate, and cleanup steps
  - Guidance on securely storing CONSUMER_KEY, SERVER_KEY, or SFDP_URL in Bitbucket repository variables
  - Apex test run command with --code-coverage and threshold enforcement
  - Review findings or troubleshooting diagnosis for an existing pipeline
dependencies:
  - apex/sf-cli-and-sfdx-essentials
  - devops/scratch-org-management
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Bitbucket Pipelines for Salesforce

This skill activates when a practitioner needs to build, review, or fix a Bitbucket Pipelines CI/CD workflow that deploys Salesforce metadata and runs Apex tests using the Salesforce CLI. It covers all three operating modes: initial setup from scratch, pipeline audit and review, and live troubleshooting of CI failures. It is scoped exclusively to Bitbucket Cloud pipelines using `bitbucket-pipelines.yml`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Connected App status:** Is a Connected App already configured in the target org with a self-signed certificate uploaded and OAuth JWT Bearer Flow enabled? If not, that must be done first — Bitbucket Pipelines cannot authenticate non-interactively without it. Alternatively, if SFDP URL auth is used, confirm the SFDP URL secret is stored in Bitbucket repository variables.
- **Org type:** Is the target a sandbox, developer sandbox, or production org? Sandbox authentication requires `--instance-url https://test.salesforce.com`. Production uses the default login URL. Using the wrong instance URL is the most common auth setup error.
- **Branch strategy:** Which branches correspond to which environments? The `branches:` section in `bitbucket-pipelines.yml` must precisely match the team's branching model. Misconfigured branch matchers cause deployments to the wrong environment.
- **Most common wrong assumption:** Practitioners often try to use `sfdx auth:sfdxurl:store` (old namespace) or store the SFDP URL as a plain text variable instead of a secured (masked) Bitbucket repository variable. Masked variables are never echoed in logs; plain variables are. Always use secured variables for credentials.
- **Platform limits:** Bitbucket Pipelines has a monthly free minute allowance (50 minutes for free plans). Enterprise teams should use self-hosted runners or Atlassian Cloud plans to avoid build queue throttling. Salesforce scratch org daily allocation limits (6 for Developer Edition Dev Hub) also apply if scratch orgs are used per PR.

---

## Core Concepts

### JWT Bearer Flow Authentication in Bitbucket

The Salesforce CLI's `sf org login jwt` command authenticates non-interactively using a private RSA key and a Connected App. Per the Salesforce DX Developer Guide, the flow requires:

1. Generate a self-signed X.509 certificate:
   ```bash
   openssl req -x509 -nodes -sha256 -days 365 -newkey rsa:2048 \
     -keyout server.key -out server.crt \
     -subj "/C=US/ST=CA/L=SF/O=MyOrg/CN=ci-service"
   ```
2. Upload `server.crt` to the Connected App in Salesforce (Setup > App Manager > Edit > Upload Certificate).
3. Store the content of `server.key` in a **secured** (masked) Bitbucket repository variable (e.g., `SF_JWT_SERVER_KEY`). Store the Connected App consumer key in a second secured variable (e.g., `SF_CONSUMER_KEY`).
4. In the pipeline YAML, write the key content to a temporary file before calling `sf org login jwt --jwt-key-file`.

The certificate has a finite lifespan (365 days by default). Expiry is the most common cause of sudden, unexplained CI auth failures. There is no platform notification when a cert nears expiry.

### `sf` CLI vs. Legacy `sfdx` Commands

As of Spring '25, Salesforce has unified the CLI under `sf` (Salesforce CLI v2). The legacy `sfdx force:*` namespace still works but is deprecated. All new pipelines must use `sf project deploy start` (not `sfdx force:source:deploy`) and `sf apex run test` (not `sfdx force:apex:test:run`). Mixing old and new namespaces in a single pipeline causes ambiguous output and will break when deprecated commands are removed.

### Bitbucket Repository Variables for Secrets

Bitbucket repository variables come in two types:
- **Secured (masked):** Values are never printed in build logs. Use for all credentials, private keys, SFDP URLs, and consumer keys.
- **Unsecured:** Values appear in logs. Use only for non-sensitive configuration (e.g., a target org username that is not itself a secret).

Variables are injected as environment variables into every pipeline step. Reference them with `$VARIABLE_NAME` in YAML scripts. Never echo a secured variable in a `run:` step without intentional masking — even with masking, this is poor hygiene.

### `bitbucket-pipelines.yml` Branch Pipeline Structure

Bitbucket Pipelines uses a declarative YAML structure. The key sections for Salesforce CI are:

- `image:` — the Docker image for the build container (e.g., `node:20` for npm-based CLI installs)
- `pipelines.branches:` — triggers per branch name or glob pattern
- `step:` — a single unit of work; multiple steps in a `parallel:` block run concurrently
- `after-script:` — runs after the step regardless of success or failure; use for cleanup (equivalent to GitHub Actions `if: always()`)

---

## Common Patterns

### Mode 1: Set Up Bitbucket Pipelines from Scratch

**When to use:** No `bitbucket-pipelines.yml` exists yet, or it is a placeholder. Team wants branch-based push-to-deploy with Apex test gating.

**How it works:**

Step 1 — Generate and upload the JWT cert (done once, outside CI):
```bash
openssl req -x509 -nodes -sha256 -days 365 -newkey rsa:2048 \
  -keyout server.key -out server.crt \
  -subj "/C=US/ST=CA/L=SF/O=MyOrg/CN=ci-service"
```
Upload `server.crt` to the Connected App. Store `server.key` content and the consumer key as secured Bitbucket repository variables. Delete `server.key` locally after uploading.

Step 2 — Create `bitbucket-pipelines.yml` in the repository root:

```yaml
image: node:20

pipelines:
  branches:
    # Feature branches: validate only (no deploy)
    'feature/**':
      - step:
          name: Validate Salesforce Metadata
          script:
            - npm install --global @salesforce/cli@latest
            - echo "$SF_JWT_SERVER_KEY" > /tmp/server.key
            - sf org login jwt
                --client-id "$SF_CONSUMER_KEY"
                --jwt-key-file /tmp/server.key
                --username "$SF_USERNAME"
                --instance-url "$SF_INSTANCE_URL"
                --alias target-org
                --set-default
            - sf project deploy validate
                --target-org target-org
                --source-dir force-app
                --test-level RunLocalTests
                --wait 30
          after-script:
            - rm -f /tmp/server.key

    # Develop branch: deploy to full sandbox
    develop:
      - step:
          name: Run Apex Tests
          script:
            - npm install --global @salesforce/cli@latest
            - echo "$SF_JWT_SERVER_KEY_SANDBOX" > /tmp/server.key
            - sf org login jwt
                --client-id "$SF_CONSUMER_KEY_SANDBOX"
                --jwt-key-file /tmp/server.key
                --username "$SF_USERNAME_SANDBOX"
                --instance-url "https://test.salesforce.com"
                --alias sandbox-org
                --set-default
            - sf apex run test
                --target-org sandbox-org
                --test-level RunLocalTests
                --code-coverage
                --result-format json
                --output-dir test-results
                --wait 20
            - python3 -c "
                import json, sys
                with open('test-results/test-result.json') as f:
                    data = json.load(f)
                pct = data.get('summary', {}).get('orgWideCoverage', '0%').replace('%','')
                assert float(pct) >= 75, f'Coverage {pct}% is below 75% threshold'
                print(f'Coverage OK: {pct}%')
              "
          after-script:
            - rm -f /tmp/server.key
      - step:
          name: Deploy to Sandbox
          script:
            - npm install --global @salesforce/cli@latest
            - echo "$SF_JWT_SERVER_KEY_SANDBOX" > /tmp/server.key
            - sf org login jwt
                --client-id "$SF_CONSUMER_KEY_SANDBOX"
                --jwt-key-file /tmp/server.key
                --username "$SF_USERNAME_SANDBOX"
                --instance-url "https://test.salesforce.com"
                --alias sandbox-org
                --set-default
            - sf project deploy start
                --target-org sandbox-org
                --source-dir force-app
                --test-level NoTestRun
                --wait 30
          after-script:
            - rm -f /tmp/server.key

    # Main branch: deploy to production
    main:
      - step:
          name: Deploy to Production
          deployment: Production
          script:
            - npm install --global @salesforce/cli@latest
            - echo "$SF_JWT_SERVER_KEY_PROD" > /tmp/server.key
            - sf org login jwt
                --client-id "$SF_CONSUMER_KEY_PROD"
                --jwt-key-file /tmp/server.key
                --username "$SF_USERNAME_PROD"
                --instance-url "https://login.salesforce.com"
                --alias prod-org
                --set-default
            - sf project deploy start
                --target-org prod-org
                --source-dir force-app
                --test-level RunLocalTests
                --wait 60
          after-script:
            - rm -f /tmp/server.key
```

**Why not the simpler approach:** Using `sfdx auth:sfdxurl:store` or storing the SFDP URL as an unsecured variable exposes credentials in build logs and violates the Connected App isolation model.

### Mode 2: Reviewing/Auditing an Existing Pipeline

**When to use:** A `bitbucket-pipelines.yml` exists but the team suspects security gaps, deprecated commands, or flaky test failures.

**How it works:**

Check for these items in order:

1. **Auth method** — Is `sf org login jwt` used (correct) or `sf org login web`/`sfdx auth:sfdxurl:store` (wrong for CI)?
2. **Variable security** — Are all credentials referenced from secured (masked) Bitbucket repository variables? Are any credentials echoed to stdout?
3. **CLI namespace** — Is `sfdx force:*` (deprecated) used instead of `sf`?
4. **Test level** — Is `--test-level` explicitly set? Omitting it means zero tests run on sandbox deploys.
5. **Branch matchers** — Do branch patterns match the team's actual branching model? Glob patterns like `feature/**` must be quoted in YAML.
6. **`after-script:` cleanup** — Is `rm -f /tmp/server.key` in `after-script:` (runs on failure too), not just in the main `script:` block?
7. **Certificate expiry** — When was the JWT certificate generated? Check the Connected App in Setup for the expiry date. Certs default to 365-day lifespans.
8. **Per-environment credentials** — Are separate secured variables used per environment (sandbox vs. production), not one shared secret?

### Mode 3: Troubleshooting CI Failures

**When to use:** A previously working pipeline starts failing.

| Symptom | Root Cause | Fix |
|---|---|---|
| `INVALID_SESSION_ID` or `expired access/refresh token` | JWT cert expired (365-day default) | Regenerate cert, re-upload to Connected App, update Bitbucket secured variable |
| `No org found for alias target-org` | Auth step failed silently; later steps reference unregistered alias | Add `--set-default` to login step; add `sf org list` in a debug step |
| `Deploy failed: Test coverage of classes is 0%` | `--test-level NoTestRun` used on production deploy | Use `RunLocalTests` for production; run separate test step first |
| `Error: ENOTFOUND login.salesforce.com` or connection timeout | Wrong `--instance-url` for org type | Use `https://test.salesforce.com` for sandbox, `https://login.salesforce.com` for production |
| `LIMIT_EXCEEDED: scratch org creation limit` | Daily scratch org allocation exhausted | Switch to sandbox-based testing; check limits in Dev Hub |
| `Error: Can't set default org` / `user not authorized` | Connected App OAuth Policies missing pre-authorization | Verify pre-authorized users in Connected App > OAuth Policies |
| Pipeline build step not triggered | Branch pattern not matching | Quote glob patterns in YAML; test with Bitbucket's pipeline YAML validator |

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Pull request validation only (no deploy) | `sf project deploy validate` with `--dry-run` | Validates metadata and runs tests without committing to the org; idempotent |
| Deploy on merge to main (production) | `sf project deploy start` with `--test-level RunLocalTests` | Enforces platform 75% threshold at deploy time |
| Feature branch with ephemeral scratch org | Create scratch org per step, run tests, delete on `after-script:` | Org-per-PR isolation; watch daily limits |
| Sandbox promotion (develop → staging) | `sf project deploy start` targeting sandbox alias with separate secured variable set | Use separate Bitbucket Deployment environments per environment for credential isolation |
| Rollback after failed production deploy | Trigger a revert branch and re-run the pipeline | Salesforce does not support automated rollback via CLI; rollback is a new deployment |
| JWT vs. SFDP URL auth | JWT Bearer Flow preferred | SFDP URL embeds a refresh token that can expire; JWT cert expiry is predictable and rotatable |

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

- [ ] `server.key` content stored in a secured (masked) Bitbucket repository variable — never committed to the repo
- [ ] JWT certificate uploaded to Connected App and not expired (check expiry date in Setup)
- [ ] `--test-level` is explicitly specified on every `sf project deploy start` call
- [ ] Production deploy step uses `RunLocalTests`; sandbox can use `NoTestRun` only if a separate test step precedes it
- [ ] `after-script:` block removes `/tmp/server.key` so cleanup runs even on step failure
- [ ] CLI version uses `sf` (v2) commands, not deprecated `sfdx force:*`
- [ ] Separate secured variables used per environment (sandbox vs. production) — not a single shared credential
- [ ] Branch patterns in `pipelines.branches:` are quoted and match the team's actual branch naming convention
- [ ] `deployment:` labels on production steps enable Bitbucket Deployment environment tracking
- [ ] Apex test results written to `--output-dir` for artifact retention and audit

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`after-script:` is the only way to guarantee cleanup on failure** — Unlike the main `script:` block, `after-script:` runs regardless of whether earlier steps succeed or fail. If `rm -f /tmp/server.key` is placed only in `script:`, a deploy failure leaves the key file on the runner for the rest of that build's lifetime. Always place key file deletion in `after-script:`.

2. **JWT certificate expiry has no built-in notification** — Salesforce does not send any warning when a JWT certificate on a Connected App is nearing expiry. The pipeline returns `INVALID_SESSION_ID` on the expiry date with no advance notice. Prevention: record the cert generation date in a team calendar or README; set a reminder 30 days before the 365-day lifespan ends; rotate before expiry.

3. **`--test-level NoTestRun` silently skips all tests on sandbox deploys** — When `--test-level` is omitted from `sf project deploy start`, Salesforce defaults to `NoTestRun` for sandbox targets. Zero tests run and zero coverage is checked. Teams discover this only when a later production deploy fails the 75% threshold. Always specify `--test-level` explicitly.

4. **Bitbucket YAML branch glob patterns must be quoted** — `feature/**` without quotes is valid YAML but some Bitbucket Pipeline parsers treat `*` as a YAML alias anchor character and silently misparse the pattern, resulting in the step never triggering. Always quote branch patterns: `'feature/**'`.

5. **Connected App OAuth pre-authorization is separate from profile assignment** — Adding a user to the profile or permission set assigned to the Connected App is not sufficient for JWT auth. The Connected App's OAuth Policies must have "Permitted Users: Admin approved users are pre-authorized" and the specific user (or their profile) must be listed in the "Manage Connected Apps > Pre-Authorize Users" section. Skipping this step produces a silent auth failure.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `bitbucket-pipelines.yml` | Complete Bitbucket Pipelines YAML with JWT auth, test gate, branch-conditional deploy, and cleanup |
| `test-results/` directory | JSON and JUnit XML Apex test output produced by `sf apex run test --output-dir` |
| Pipeline audit findings | Ordered list of security and best-practice gaps found in an existing pipeline YAML |
| Troubleshooting diagnosis | Root cause and fix for a specific CI failure symptom |

---

## Related Skills

- `devops/github-actions-for-salesforce` — Use when the team's source control is GitHub, not Bitbucket
- `apex/sf-cli-and-sfdx-essentials` — Use for `sf` CLI command reference, auth patterns, and metadata deploy/retrieve details
- `devops/scratch-org-management` — Use when the pipeline needs per-PR ephemeral scratch org creation, limit management, or automated deletion
- `devops/devops-center-pipeline` — Alternative for teams that want a Salesforce-native UI-driven pipeline without writing YAML
