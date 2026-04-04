# Bitbucket Pipelines for Salesforce — Work Template

Use this template when building, reviewing, or troubleshooting a Bitbucket Pipelines CI/CD workflow for Salesforce.

## Scope

**Skill:** `bitbucket-pipelines-for-salesforce`

**Request summary:** (fill in what the user asked for — e.g., "set up a new pipeline", "debug auth failure", "audit existing YAML")

**Operating mode:**
- [ ] Mode 1 — Set up a new pipeline from scratch
- [ ] Mode 2 — Review/audit an existing `bitbucket-pipelines.yml`
- [ ] Mode 3 — Troubleshoot a CI failure

---

## Context Gathered

Answer these before proceeding (from SKILL.md "Before Starting"):

- **Connected App status:** Is a Connected App already configured in the target org with JWT Bearer Flow enabled and a certificate uploaded? Yes / No / Unknown
- **Auth method:** JWT Bearer Flow (server.key + consumer key) or SFDP URL?
- **Org type for each environment:**
  - Feature/validate target: sandbox / developer sandbox / scratch org
  - Integration target: full sandbox / partial sandbox
  - Production target: production org
- **Instance URLs:**
  - Sandbox: `https://test.salesforce.com`
  - Production: `https://login.salesforce.com`
- **Branch naming convention:**
  - Feature branches: `feature/**` (or: ____________)
  - Integration branch: `develop` (or: ____________)
  - Production branch: `main` (or: ____________)
- **Bitbucket variables already configured:** List names (not values): ____________
- **Current failure symptom (Mode 3):** ____________

---

## Approach

Which pattern from SKILL.md applies? (mark one)

- [ ] Mode 1: Scaffold new `bitbucket-pipelines.yml` with branch-conditional stages
- [ ] Mode 2: Audit checklist review of existing YAML
- [ ] Mode 3: Symptom-based root cause diagnosis using the troubleshooting table

Reason for choice: ____________

---

## `bitbucket-pipelines.yml` Scaffold

Fill in the placeholder values and commit this file to the repository root.

```yaml
# bitbucket-pipelines.yml
# Generated from: bitbucket-pipelines-for-salesforce skill template
image: node:20

pipelines:
  branches:
    # --- FEATURE BRANCHES: validate only, no deploy ---
    'feature/**':
      - step:
          name: Validate Salesforce Metadata
          script:
            - npm install --global @salesforce/cli@latest
            - echo "$SF_JWT_SERVER_KEY_DEV" > /tmp/server.key
            - sf org login jwt
                --client-id "$SF_CONSUMER_KEY_DEV"
                --jwt-key-file /tmp/server.key
                --username "$SF_USERNAME_DEV"
                --instance-url "$SF_INSTANCE_URL_DEV"
                --alias dev-org
                --set-default
            - sf project deploy validate
                --target-org dev-org
                --source-dir force-app
                --test-level RunLocalTests
                --wait 30
          after-script:
            - rm -f /tmp/server.key

    # --- DEVELOP BRANCH: test then deploy to full sandbox ---
    develop:
      - step:
          name: Apex Test Gate
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
                import json
                with open('test-results/test-result.json') as f:
                    d = json.load(f)
                pct = d.get('summary', {}).get('orgWideCoverage', '0%').replace('%','')
                assert float(pct) >= 75, f'Coverage {pct}% is below 75% minimum'
                print(f'Coverage OK: {pct}%')
              "
          after-script:
            - rm -f /tmp/server.key
      - step:
          name: Deploy to Full Sandbox
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

    # --- MAIN BRANCH: deploy to production ---
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

---

## Bitbucket Repository Variables to Configure

Set these in Bitbucket: Repository Settings > Repository variables. Mark all as **Secured (masked)**.

| Variable Name | Value | Secured? |
|---|---|---|
| `SF_JWT_SERVER_KEY_DEV` | Contents of `server.key` for dev sandbox | Yes |
| `SF_CONSUMER_KEY_DEV` | Consumer key from dev sandbox Connected App | Yes |
| `SF_USERNAME_DEV` | Pre-authorized username in dev sandbox | No (not a secret) |
| `SF_INSTANCE_URL_DEV` | `https://test.salesforce.com` | No |
| `SF_JWT_SERVER_KEY_SANDBOX` | Contents of `server.key` for full sandbox | Yes |
| `SF_CONSUMER_KEY_SANDBOX` | Consumer key from full sandbox Connected App | Yes |
| `SF_USERNAME_SANDBOX` | Pre-authorized username in full sandbox | No |
| `SF_JWT_SERVER_KEY_PROD` | Contents of `server.key` for production | Yes |
| `SF_CONSUMER_KEY_PROD` | Consumer key from production Connected App | Yes |
| `SF_USERNAME_PROD` | Pre-authorized username in production | No |

---

## Audit Checklist (Mode 2)

Use when reviewing an existing `bitbucket-pipelines.yml`:

- [ ] `sf org login jwt` used for auth (not `sfdx auth:sfdxurl:store` or `sf org login web`)
- [ ] All credentials referenced from secured (masked) Bitbucket repository variables
- [ ] No credentials echoed to stdout in `script:` blocks
- [ ] `sf` (v2) commands used — no deprecated `sfdx force:*` commands
- [ ] `--test-level` explicitly set on every `sf project deploy start` invocation
- [ ] Production deploy uses `RunLocalTests` (not `NoTestRun`)
- [ ] `after-script:` block removes `/tmp/server.key` (not only in `script:`)
- [ ] Branch patterns containing `*` are wrapped in single quotes
- [ ] Separate Connected Apps and separate variable sets for sandbox vs. production
- [ ] JWT certificate expiry date is known and rotation reminder is set
- [ ] `deployment:` label on production step for Bitbucket Deployment environment tracking
- [ ] `sfdx-project.json` exists in the repository root

---

## Troubleshooting Quick Reference (Mode 3)

| Symptom | Likely Cause | First Action |
|---|---|---|
| `INVALID_SESSION_ID` | JWT cert expired | Regenerate cert, re-upload to Connected App, update secured variable |
| `No org found for alias` | Auth step failed silently | Add `sf org list` debug step; check `--set-default` flag |
| `Coverage of classes is 0%` | `NoTestRun` on production | Change to `RunLocalTests` for production deploy |
| `ENOTFOUND login.salesforce.com` | Wrong `--instance-url` | Use `https://test.salesforce.com` for sandbox |
| `user not authorized` / `IP not allowed` | Missing pre-authorization on Connected App | Add user profile to Connected App > Manage > Profiles |
| Branch step never triggers | Unquoted glob pattern | Wrap branch pattern in single quotes |
| `LIMIT_EXCEEDED: scratch org` | Daily scratch org limit hit | Switch to persistent sandbox for CI |

---

## Notes

Record any deviations from the standard pattern and why:

____________
