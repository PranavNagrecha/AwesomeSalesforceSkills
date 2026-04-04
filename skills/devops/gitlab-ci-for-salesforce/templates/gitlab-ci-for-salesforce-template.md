# GitLab CI for Salesforce — Work Template

Use this template when building, reviewing, or troubleshooting a GitLab CI/CD pipeline for Salesforce.

## Scope

**Skill:** `gitlab-ci-for-salesforce`

**Request summary:** (fill in what the user asked for — e.g., "set up a new pipeline", "fix failing auth job", "review existing .gitlab-ci.yml")

**Mode:** (circle one)
- Mode 1: New pipeline setup from scratch
- Mode 2: Review / audit existing pipeline
- Mode 3: Troubleshoot a failing pipeline

---

## Context Gathered

Answer these before proceeding:

- **Connected App configured?** Yes / No / Unknown
  - Certificate uploaded? Yes / No
  - Pre-authorized users set? Yes / No
- **Org type(s):** sandbox / developer sandbox / production
  - Sandbox login URL: `https://test.salesforce.com`
  - Production login URL: `https://login.salesforce.com`
- **GitLab runner type:** Docker executor / Shell executor / GitLab shared runners
- **Branch strategy:**
  - Feature branches → (environment)
  - `develop` → (environment)
  - `main` → production
- **GitLab CI/CD variables configured?**
  - `SF_JWT_SERVER_KEY_*` — masked, base64-encoded: Yes / No
  - `SF_CONSUMER_KEY_*` — masked: Yes / No
  - `SF_USERNAME_*` — masked: Yes / No
  - Production variables also Protected: Yes / No
- **Known failure symptom (Mode 3 only):** (fill in error message)

---

## Approach

Which mode applies and why:

- **Mode 1 (new pipeline):** No `.gitlab-ci.yml` exists or it is a placeholder
- **Mode 2 (review):** Pipeline exists; check security, deprecated syntax, test level
- **Mode 3 (troubleshoot):** Specific failure — match symptom to root cause table in SKILL.md

Pattern selection reasoning: (fill in)

---

## Pipeline Structure (Mode 1)

Fill in the target pipeline configuration:

```yaml
# .gitlab-ci.yml skeleton — fill in variable names and branch names
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

# Feature / MR: validate only
validate-metadata:
  stage: validate
  script:
    - echo "$SF_JWT_SERVER_KEY_DEV" | base64 -d > /tmp/server.key
    - sf org login jwt
        --client-id "$SF_CONSUMER_KEY_DEV"
        --jwt-key-file /tmp/server.key
        --username "$SF_USERNAME_DEV"
        --instance-url "$SF_INSTANCE_URL_SANDBOX"
        --alias dev-org --set-default
    - sf project deploy validate
        --target-org dev-org
        --source-dir force-app
        --test-level RunLocalTests
        --wait 30
  after_script:
    - rm -f /tmp/server.key
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH =~ /^feature\//'

# Develop: Apex test gate
apex-tests:
  stage: test
  script:
    - echo "$SF_JWT_SERVER_KEY_DEV" | base64 -d > /tmp/server.key
    - sf org login jwt
        --client-id "$SF_CONSUMER_KEY_DEV"
        --jwt-key-file /tmp/server.key
        --username "$SF_USERNAME_DEV"
        --instance-url "$SF_INSTANCE_URL_SANDBOX"
        --alias sandbox-org --set-default
    - sf apex run test
        --target-org sandbox-org
        --test-level RunLocalTests
        --code-coverage
        --result-format json
        --output-dir test-results
        --wait 20
    - |
      python3 -c "
      import json
      with open('test-results/test-result.json') as f:
          data = json.load(f)
      pct = data.get('summary', {}).get('orgWideCoverage', '0%').replace('%','')
      assert float(pct) >= 75, f'Coverage {pct}% below 75% threshold'
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

# Develop: deploy to sandbox
deploy-sandbox:
  stage: deploy
  script:
    - echo "$SF_JWT_SERVER_KEY_DEV" | base64 -d > /tmp/server.key
    - sf org login jwt
        --client-id "$SF_CONSUMER_KEY_DEV"
        --jwt-key-file /tmp/server.key
        --username "$SF_USERNAME_DEV"
        --instance-url "$SF_INSTANCE_URL_SANDBOX"
        --alias sandbox-org --set-default
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

# Main: deploy to production (manual gate)
deploy-production:
  stage: deploy
  script:
    - echo "$SF_JWT_SERVER_KEY_PROD" | base64 -d > /tmp/server.key
    - sf org login jwt
        --client-id "$SF_CONSUMER_KEY_PROD"
        --jwt-key-file /tmp/server.key
        --username "$SF_USERNAME_PROD"
        --instance-url "$SF_INSTANCE_URL_PROD"
        --alias prod-org --set-default
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

---

## GitLab CI/CD Variables Checklist

| Variable Name | Masked | Protected | Notes |
|---|---|---|---|
| `SF_JWT_SERVER_KEY_DEV` | Yes | No | base64 -w 0 server.key |
| `SF_CONSUMER_KEY_DEV` | Yes | No | Connected App consumer key |
| `SF_USERNAME_DEV` | Yes | No | Pre-authorized CI username |
| `SF_JWT_SERVER_KEY_PROD` | Yes | Yes | Protected — main branch only |
| `SF_CONSUMER_KEY_PROD` | Yes | Yes | Protected |
| `SF_USERNAME_PROD` | Yes | Yes | Protected |

---

## Review Checklist (Mode 2)

Copy the checklist from SKILL.md and mark each item:

- [ ] `server.key` stored as base64-encoded masked GitLab CI/CD variable (not raw PEM)
- [ ] Production credential variables are masked AND protected
- [ ] JWT certificate not expired (verify in Salesforce Setup > App Manager > Connected App)
- [ ] `--test-level` explicitly specified on every `sf project deploy start` call
- [ ] Production deploy job uses `when: manual`
- [ ] `after_script:` removes `/tmp/server.key` on every job that writes it
- [ ] `sf` CLI v2 commands used (not deprecated `sfdx force:*`)
- [ ] `rules:` syntax used (not deprecated `only:`/`except:`)
- [ ] Apex test results in `artifacts: paths:` for audit retention
- [ ] Separate variables per environment (not one shared credential)
- [ ] Docker executor on runner (not shell executor)
- [ ] `environment:` declared on deploy jobs for GitLab Environments tracking

---

## Troubleshooting Reference (Mode 3)

| Symptom | Root Cause | Fix |
|---|---|---|
| `INVALID_SESSION_ID` | JWT cert expired | Regenerate cert, re-upload to Connected App, update masked variable |
| `No org found for alias` | Auth step failed; alias not registered | Add `--set-default`; add `sf org list` debug step |
| `Deploy failed: Test coverage 0%` | NoTestRun on production | Use RunLocalTests; add separate test job |
| `ENOTFOUND login.salesforce.com` | Wrong instance URL for sandbox | Use `https://test.salesforce.com` for sandboxes |
| Job never triggers on branch push | `rules:` mismatch or protected variable restriction | Check branch name; verify variable protection settings |
| `masked variable value rejected` | Multi-line PEM value in variable | Base64-encode the key value before storing |
| `user is not pre-authorized` | Connected App pre-authorization missing | Set pre-authorized user under Manage Connected Apps > Pre-Authorize Users |

---

## Notes

Record any deviations from standard patterns and the reason:

- (e.g., "shell executor used because Docker not available on self-hosted runner — added `sf` CLI version check in before_script:")
- (e.g., "base64 decoding omitted because private key was uploaded without masking — flagged as security gap for team to rotate")
