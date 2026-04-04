---
name: gitlab-ci-for-salesforce
description: "Use this skill to set up, review, or troubleshoot GitLab CI/CD pipelines for Salesforce using SFDX JWT Bearer Flow authentication, Docker executor runners, Apex test gates, branch-based deployment jobs, and GitLab CI/CD variables for secret management. Trigger keywords: gitlab-ci.yml, gitlab runner, gitlab ci salesforce, gitlab ci sfdx, gitlab pipeline deploy salesforce, gitlab ci jwt auth. NOT for GitHub Actions (use github-actions-for-salesforce), Bitbucket Pipelines (use bitbucket-pipelines-for-salesforce), Jenkins, Copado, Azure DevOps, or any non-GitLab CI platform."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
  - Reliability
triggers:
  - "how do I set up GitLab CI to automatically deploy Salesforce metadata when I push to the main branch"
  - "my GitLab CI Salesforce pipeline is failing with JWT authentication errors or INVALID_SESSION_ID"
  - "how do I configure a GitLab runner with Docker executor to run Salesforce CLI commands"
  - "I need to add an Apex test coverage threshold gate to my .gitlab-ci.yml for Salesforce"
  - "how do I store Salesforce Connected App credentials securely in GitLab CI/CD variables"
  - "my gitlab-ci.yml deploy job fails to authenticate to the Salesforce org with sf org login jwt"
  - "how do I set up branch-based Salesforce deployment stages in GitLab CI for sandbox and production"
tags:
  - gitlab-ci
  - ci-cd
  - jwt-bearer-flow
  - sfdx
  - apex-testing
  - secrets-management
  - docker-executor
inputs:
  - GitLab repository with Salesforce DX project structure (sfdx-project.json present)
  - Connected App configured in target Salesforce org with OAuth JWT Bearer Flow enabled and self-signed certificate uploaded
  - Server private key (server.key) and consumer key (client_id) for JWT authentication
  - Target org username and login URL (test.salesforce.com for sandbox, login.salesforce.com for production)
  - Branch naming convention for environment promotion (e.g., feature/* → developer sandbox, develop → full sandbox, main → production)
outputs:
  - .gitlab-ci.yml ready to commit with stage-based deploy, JWT auth, Apex test gate, and artifact retention
  - Guidance on securely storing SF_JWT_SERVER_KEY, SF_CONSUMER_KEY, and SF_USERNAME as masked GitLab CI/CD variables
  - Apex test run command with --code-coverage and threshold enforcement
  - Review findings or troubleshooting diagnosis for an existing GitLab pipeline
dependencies:
  - devops/github-actions-for-salesforce
  - devops/scratch-org-management
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# GitLab CI for Salesforce

This skill activates when a practitioner needs to build, review, or fix a GitLab CI/CD pipeline that deploys Salesforce metadata and runs Apex tests using the Salesforce CLI and JWT Bearer Flow authentication. It covers all three operating modes: initial setup from scratch, pipeline audit and review, and live troubleshooting of CI failures. It is scoped exclusively to GitLab CI using `.gitlab-ci.yml`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Connected App status:** Is a Connected App already configured in the target org with a self-signed certificate uploaded and OAuth JWT Bearer Flow enabled? If not, that must be done first — GitLab CI cannot authenticate non-interactively without it.
- **Runner type:** Is the GitLab runner using a Docker executor, shell executor, or GitLab's shared runners? Docker executor is strongly preferred for Salesforce CI because it provides a clean, isolated environment per job with a known Node.js/CLI version. Shell executors can have stale CLI state between runs.
- **Org type:** Is the target a sandbox, developer sandbox, or production org? Sandbox authentication requires `--instance-url https://test.salesforce.com`. Production uses the default login URL. Using the wrong instance URL is the most common auth setup error.
- **Branch strategy:** Which branches correspond to which environments? GitLab CI uses `rules:` or `only:`/`except:` conditions per job to control when each job runs. Misconfigured branch rules cause deployments to the wrong environment.
- **Most common wrong assumption:** Practitioners unfamiliar with GitLab CI often try to reuse GitHub Actions workflow syntax (`uses:`, `with:`) in `.gitlab-ci.yml`. GitLab CI has a completely different YAML schema: jobs, stages, `script:`, `rules:`, `variables:`, `artifacts:`, and `before_script:`. There are no reusable "actions" — use Docker images or shell scripts instead.
- **Platform limits:** GitLab SaaS shared runners have compute minute quotas (400 minutes/month on the free tier). Large Salesforce orgs with slow metadata deploys can exhaust this quickly. Self-managed runners on Docker avoid this constraint. Salesforce scratch org daily allocation limits (6 for Developer Edition Dev Hub) also apply if scratch orgs are used per merge request.

---

## Core Concepts

### JWT Bearer Flow Authentication in GitLab CI

The Salesforce CLI's `sf org login jwt` command authenticates non-interactively using a private RSA key and a Connected App. Per the Salesforce DX Developer Guide, the flow requires:

1. Generate a self-signed X.509 certificate:
   ```bash
   openssl req -x509 -nodes -sha256 -days 365 -newkey rsa:2048 \
     -keyout server.key -out server.crt \
     -subj "/C=US/ST=CA/L=SF/O=MyOrg/CN=ci-service"
   ```
2. Upload `server.crt` to the Connected App in Salesforce (Setup > App Manager > Edit > Upload Certificate).
3. Store the content of `server.key` in a **masked** GitLab CI/CD variable (e.g., `SF_JWT_SERVER_KEY`). Store the Connected App consumer key in a second masked variable (e.g., `SF_CONSUMER_KEY`).
4. In the pipeline job, write the key content to a temporary file before calling `sf org login jwt --jwt-key-file`.

The certificate has a finite lifespan (365 days by default with the OpenSSL command above). Expiry is the most common cause of sudden, unexplained CI auth failures. GitLab and Salesforce send no warning when a cert nears expiry.

### `sf` CLI vs. Legacy `sfdx` Commands

As of Spring '25, Salesforce has unified the CLI under `sf` (Salesforce CLI v2). The legacy `sfdx force:*` namespace still works but is deprecated. All new pipelines must use `sf project deploy start` (not `sfdx force:source:deploy`) and `sf apex run test` (not `sfdx force:apex:test:run`). Mixing old and new namespaces in a single pipeline produces ambiguous output and will break when deprecated commands are removed.

### GitLab CI/CD Variables for Secrets

GitLab CI/CD variables come in two sensitivity levels:
- **Masked variables:** Values are never printed in job logs. Required for all credentials, private keys, consumer keys, and usernames. Set in Settings > CI/CD > Variables with the "Masked" toggle enabled.
- **Protected variables:** Variables available only to protected branches (e.g., `main`, `production`). Use "Protected" in addition to "Masked" for production credentials to prevent feature branch jobs from accessing production secrets.
- **Unmasked variables:** Values appear in logs when echoed. Use only for non-sensitive configuration (e.g., a target login URL that is not itself a secret).

Variables are injected as environment variables into every job. Reference them with `$VARIABLE_NAME` in YAML scripts. Never use `echo $SF_JWT_SERVER_KEY` in a script block — masked variables are blocked from appearing in logs, but this is best-hygiene avoidance, not a security substitute.

### `.gitlab-ci.yml` Pipeline Structure

GitLab CI uses a declarative YAML file at the repository root. Key concepts for Salesforce CI:

- `stages:` — ordered list of stage names; jobs in the same stage run in parallel, stages run sequentially
- `image:` — the Docker image for the job container; specify globally or per-job
- `variables:` — job-level or global variable definitions; CI/CD variable values injected at runtime
- `script:` — the shell commands for the job; this is the equivalent of GitHub Actions `run:` steps
- `before_script:` — commands run before every job's `script:`; useful for installing the Salesforce CLI once globally
- `after_script:` — commands run after `script:` regardless of success or failure; use for cleanup (delete temp key files)
- `rules:` — conditional execution per job; replaces the older `only:`/`except:` syntax; supports branch, event, and variable conditions
- `artifacts:` — file patterns to retain after a job; use for Apex test result JSON files
- `environment:` — marks a job as a deployment to a named environment; enables GitLab Environments tracking and deployment history

---

## Common Patterns

### Mode 1: Set Up GitLab CI from Scratch

**When to use:** No `.gitlab-ci.yml` exists yet, or it is a placeholder. Team wants branch-based push-to-deploy with Apex test gating.

**How it works:**

Step 1 — Generate and upload the JWT cert (done once, outside CI):
```bash
openssl req -x509 -nodes -sha256 -days 365 -newkey rsa:2048 \
  -keyout server.key -out server.crt \
  -subj "/C=US/ST=CA/L=SF/O=MyOrg/CN=ci-service"
```
Upload `server.crt` to the Connected App. Store `server.key` content and the consumer key as masked GitLab CI/CD variables. Delete `server.key` locally after uploading.

Step 2 — Configure GitLab CI/CD variables in the project (Settings > CI/CD > Variables):
| Variable | Value | Masked | Protected |
|---|---|---|---|
| `SF_JWT_SERVER_KEY_DEV` | contents of server.key for dev org | Yes | No |
| `SF_CONSUMER_KEY_DEV` | Connected App consumer key for dev | Yes | No |
| `SF_USERNAME_DEV` | pre-authorized username in dev org | Yes | No |
| `SF_JWT_SERVER_KEY_PROD` | contents of server.key for prod | Yes | Yes |
| `SF_CONSUMER_KEY_PROD` | Connected App consumer key for prod | Yes | Yes |
| `SF_USERNAME_PROD` | pre-authorized username in production | Yes | Yes |

Step 3 — Create `.gitlab-ci.yml` at the repository root:

```yaml
# .gitlab-ci.yml
image: node:20

stages:
  - validate
  - test
  - deploy

variables:
  SF_INSTANCE_URL_SANDBOX: "https://test.salesforce.com"
  SF_INSTANCE_URL_PROD: "https://login.salesforce.com"

before_script:
  - npm install --global @salesforce/cli@latest --quiet

# ── Feature branches: metadata validation only ────────────────────────
validate-metadata:
  stage: validate
  script:
    - echo "$SF_JWT_SERVER_KEY_DEV" > /tmp/server.key
    - sf org login jwt
        --client-id "$SF_CONSUMER_KEY_DEV"
        --jwt-key-file /tmp/server.key
        --username "$SF_USERNAME_DEV"
        --instance-url "$SF_INSTANCE_URL_SANDBOX"
        --alias dev-org
        --set-default
    - sf project deploy validate
        --target-org dev-org
        --source-dir force-app
        --test-level RunLocalTests
        --wait 30
  after_script:
    - rm -f /tmp/server.key
  rules:
    - if: '$CI_COMMIT_BRANCH =~ /^feature\//'
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'

# ── Develop branch: run Apex tests ───────────────────────────────────
apex-tests:
  stage: test
  script:
    - echo "$SF_JWT_SERVER_KEY_DEV" > /tmp/server.key
    - sf org login jwt
        --client-id "$SF_CONSUMER_KEY_DEV"
        --jwt-key-file /tmp/server.key
        --username "$SF_USERNAME_DEV"
        --instance-url "$SF_INSTANCE_URL_SANDBOX"
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
  after_script:
    - rm -f /tmp/server.key
  artifacts:
    when: always
    paths:
      - test-results/
    expire_in: 7 days
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"'

# ── Develop branch: deploy to sandbox ────────────────────────────────
deploy-sandbox:
  stage: deploy
  script:
    - echo "$SF_JWT_SERVER_KEY_DEV" > /tmp/server.key
    - sf org login jwt
        --client-id "$SF_CONSUMER_KEY_DEV"
        --jwt-key-file /tmp/server.key
        --username "$SF_USERNAME_DEV"
        --instance-url "$SF_INSTANCE_URL_SANDBOX"
        --alias sandbox-org
        --set-default
    - sf project deploy start
        --target-org sandbox-org
        --source-dir force-app
        --test-level NoTestRun
        --wait 30
  after_script:
    - rm -f /tmp/server.key
  environment:
    name: sandbox
  needs:
    - apex-tests
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"'

# ── Main branch: deploy to production ────────────────────────────────
deploy-production:
  stage: deploy
  script:
    - echo "$SF_JWT_SERVER_KEY_PROD" > /tmp/server.key
    - sf org login jwt
        --client-id "$SF_CONSUMER_KEY_PROD"
        --jwt-key-file /tmp/server.key
        --username "$SF_USERNAME_PROD"
        --instance-url "$SF_INSTANCE_URL_PROD"
        --alias prod-org
        --set-default
    - sf project deploy start
        --target-org prod-org
        --source-dir force-app
        --test-level RunLocalTests
        --wait 60
  after_script:
    - rm -f /tmp/server.key
  environment:
    name: production
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: manual
```

**Why not a simpler approach:** Using `sf org login web` requires browser interaction, which is impossible in a non-interactive runner. Using SFDP URL auth stores a live refresh token in the variable; if leaked, it grants immediate org access with no expiry signal. JWT Bearer Flow generates a new short-lived access token per run and provides predictable cert-based expiry. The `when: manual` gate on the production job requires an explicit human approval click in GitLab before production deployment proceeds — preventing accidental pushes to production.

### Mode 2: Reviewing/Auditing an Existing Pipeline

**When to use:** A `.gitlab-ci.yml` exists but the team suspects security gaps, deprecated commands, or flaky failures.

**How it works:**

Check for these items in order:

1. **Auth method** — Is `sf org login jwt` used (correct) or `sf org login web`/`sfdx auth:sfdxurl:store` (wrong for CI)?
2. **Variable masking** — Are all credentials in masked GitLab CI/CD variables? Are production credentials also marked "Protected"? Are any variables echoed with `echo $VAR` in job scripts?
3. **CLI namespace** — Is `sfdx force:*` (deprecated) used instead of `sf`?
4. **Test level** — Is `--test-level` explicitly set on every `sf project deploy start` call?
5. **Rules vs. only/except** — Is the older `only:`/`except:` syntax used? Migrate to `rules:` for correctness and future compatibility. GitLab CI's `only:` has subtle matching quirks with branch patterns.
6. **`after_script:` cleanup** — Is `rm -f /tmp/server.key` in `after_script:` (runs on failure too), not just in the main `script:` block?
7. **Certificate expiry** — When was the JWT certificate generated? Check the Connected App in Setup for the expiry date.
8. **Per-environment credential isolation** — Are separate masked+protected variables used for production vs. sandbox? Are sandbox variables protected=false (allows feature branch jobs) and production variables protected=true (allows only protected branches)?
9. **`when: manual` on production** — Is the production deployment job gated with `when: manual`? Automated production deploys on every `main` push are a common configuration risk.
10. **Artifact retention** — Are Apex test result files captured in `artifacts: paths:` so they can be reviewed after a job completes?

### Mode 3: Troubleshooting CI Failures

**When to use:** A previously working pipeline starts failing.

| Symptom | Root Cause | Fix |
|---|---|---|
| `INVALID_SESSION_ID` or `expired access/refresh token` | JWT cert expired (365-day default) | Regenerate cert, re-upload to Connected App, update masked variable |
| `No org found for alias sandbox-org` | Auth step failed silently; later steps reference unregistered alias | Add `--set-default` to login step; add `sf org list` in a debug script |
| `Deploy failed: Test coverage of classes is 0%` | `--test-level NoTestRun` used on production deploy | Use `RunLocalTests` for production; run a separate test job first |
| `Error: ENOTFOUND login.salesforce.com` or connection timeout | Wrong `--instance-url` for org type | Use `https://test.salesforce.com` for sandbox, `https://login.salesforce.com` for production |
| `LIMIT_EXCEEDED: scratch org creation limit` | Daily scratch org allocation exhausted | Switch to sandbox-based testing; check limits in Dev Hub |
| `Error: Can't set default org` / `user not authorized` | Connected App OAuth pre-authorization not set | Verify pre-authorized users in Connected App > OAuth Policies |
| Job never triggers on `main` push | `rules:` branch condition or protected variable mismatch | Check branch name, variable protection level; use GitLab CI lint tool |
| `masked variable value rejected` | Variable value contains characters that cannot be masked (e.g., `$`, newlines) | Base64-encode the private key value; decode it in the job script before writing to file |

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Pull request / merge request validation only | `sf project deploy validate` — no source deploy | Validates metadata and runs tests without committing; idempotent; safe on MR events |
| Deploy on merge to develop (sandbox) | `sf project deploy start` with `--test-level NoTestRun` after a separate passing test job | Avoids double-running all tests; rely on the dedicated test job for coverage gate |
| Deploy on merge to main (production) | `sf project deploy start` with `--test-level RunLocalTests` and `when: manual` gate | Enforces 75% threshold; manual gate prevents accidental production deploy |
| Feature branch with ephemeral scratch org | Create scratch org in job, run tests, delete in `after_script:` | Org-per-branch isolation; watch daily limits (6/day for Developer Edition Dev Hub) |
| Base64-encoded private key | `echo "$SF_JWT_KEY_B64" | base64 -d > /tmp/server.key` | Avoids GitLab masking rejection for multi-line values with special characters |
| Rollback after failed production deploy | Revert branch and re-run the pipeline | Salesforce does not support automated rollback via CLI; rollback is a new deployment |
| JWT vs. SFDP URL auth | JWT Bearer Flow preferred | SFDP URL embeds a refresh token that can expire unpredictably; JWT cert expiry is predictable and rotatable |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Gather context** — Confirm whether a `.gitlab-ci.yml` exists, identify the target org type (sandbox/production), check whether a Connected App with JWT is already configured, and determine the team's branch naming convention.
2. **Check auth prerequisites** — Verify the Connected App exists with a valid non-expired certificate uploaded, the pre-authorized username is listed in the Connected App's OAuth Policies, and the masked GitLab CI/CD variables are set for each environment.
3. **Build or review the pipeline** — Apply the Mode 1 (setup), Mode 2 (review), or Mode 3 (troubleshoot) pattern from Common Patterns above based on what the practitioner needs. Ensure `rules:` conditions, stage ordering, `after_script:` cleanup, and `when: manual` on production are all correct.
4. **Validate the YAML locally** — Run `gitlab-ci-lint` or use the GitLab CI/CD > Editor lint tool to catch syntax errors before pushing. Check that masked variable names match exactly between the YAML and the project's CI/CD Variables settings.
5. **Run the skill's checker script** — `python3 scripts/check_gitlab_ci_for_salesforce.py --gitlab-ci-file .gitlab-ci.yml` to catch common structural issues.
6. **Review checklist** — Walk through the Review Checklist below before marking complete.
7. **Document deviations** — Record any non-standard patterns (e.g., shell executor instead of Docker, base64-encoded key) in the template notes section.

---

## Review Checklist

Run through these before marking the pipeline complete:

- [ ] `server.key` content stored in a masked GitLab CI/CD variable — never committed to the repository
- [ ] Production credential variables are both masked AND protected (restricted to protected branches)
- [ ] JWT certificate uploaded to Connected App and not expired (check expiry date in Salesforce Setup)
- [ ] `--test-level` is explicitly specified on every `sf project deploy start` call
- [ ] Production deploy job uses `when: manual` to prevent accidental automated pushes
- [ ] `after_script:` block removes `/tmp/server.key` so cleanup runs even on job failure
- [ ] CLI version uses `sf` (v2) commands, not deprecated `sfdx force:*`
- [ ] `rules:` syntax used (not deprecated `only:`/`except:`) with correct branch conditions
- [ ] Apex test results captured in `artifacts: paths:` for post-job review and audit
- [ ] Separate masked variables per environment (dev, sandbox, production) — not a single shared credential
- [ ] Docker executor used on runner (not shell executor) for clean per-job environment isolation
- [ ] `environment:` declared on deployment jobs to enable GitLab Environments tracking

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **GitLab masked variables reject multi-line values** — GitLab CI/CD variable masking fails silently if the variable value contains newlines or certain special characters (`$`, `[`, `]`). A private key (`server.key`) contains newlines, which prevents masking. Workaround: base64-encode the key before storing it in the variable (`base64 -w 0 server.key`) and decode it in the job script (`echo "$SF_JWT_KEY_B64" | base64 -d > /tmp/server.key`). GitLab documents this limitation in the CI/CD variable masking requirements.

2. **JWT certificate expiry has no built-in notification** — Salesforce does not send any warning when a JWT certificate on a Connected App is nearing expiry. The pipeline returns `INVALID_SESSION_ID` on the expiry date with no advance notice. Prevention: record the cert generation date in a team calendar; set a reminder 30 days before the 365-day lifespan ends; rotate before expiry. Extend the lifespan to 730 days with `-days 730` to reduce rotation frequency.

3. **`when: manual` jobs block dependent `needs:` jobs** — GitLab CI `needs:` creates a DAG dependency: if `deploy-production` needs `apex-tests`, the production job will wait for `apex-tests` to succeed. However, if `deploy-production` is also `when: manual`, GitLab requires a manual trigger first — the job stays in a "manual" (blocked) state even after all `needs:` dependencies pass. This is expected behavior, not a bug: the manual trigger requires explicit user action even when all upstream jobs succeed.

4. **`only:`/`except:` branch regex matches differently than expected** — The legacy `only: branches` with a regex like `only: [/^feature\//]` matches against the full ref path in some GitLab versions, not just the branch name. This causes feature branch jobs to unexpectedly skip or fire. Migrate to `rules: - if: '$CI_COMMIT_BRANCH =~ /^feature\//'` which reliably matches against the branch name only.

5. **Connected App OAuth pre-authorization is separate from profile assignment** — Adding the CI service user to the profile or permission set on the Connected App is not sufficient for JWT auth. The Connected App's OAuth Policies must have "Permitted Users: Admin approved users are pre-authorized" and the specific user (or their profile) must be listed under "Manage Connected Apps > Pre-Authorize Users". Skipping the pre-authorization step produces a cryptic auth failure that looks identical to a wrong credential.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `.gitlab-ci.yml` | Complete GitLab CI pipeline with stage-based JWT auth, Apex test gate, branch-conditional deploy, `when: manual` production gate, and `after_script:` cleanup |
| `test-results/` directory | JSON and JUnit XML Apex test output produced by `sf apex run test --output-dir`, retained as a GitLab job artifact |
| Pipeline audit findings | Ordered list of security and best-practice gaps found in an existing `.gitlab-ci.yml` |
| Troubleshooting diagnosis | Root cause and fix for a specific CI failure symptom |

---

## Related Skills

- `devops/github-actions-for-salesforce` — Use when the team's source control is GitHub, not GitLab
- `devops/bitbucket-pipelines-for-salesforce` — Use when the team's source control is Bitbucket
- `apex/sf-cli-and-sfdx-essentials` — Use for `sf` CLI command reference, auth patterns, and metadata deploy/retrieve details
- `devops/scratch-org-management` — Use when the pipeline needs per-merge-request ephemeral scratch org creation, limit management, or automated deletion
- `devops/devops-center-pipeline` — Alternative for teams that want a Salesforce-native UI-driven pipeline without writing YAML (GitHub-only constraint applies)
