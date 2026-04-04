# Examples — GitLab CI for Salesforce

## Example 1: Three-Stage Branch-Based Pipeline (Feature → Sandbox → Production)

**Context:** A mid-size Salesforce ISV team manages a Salesforce DX project in GitLab. They have three persistent environments: a developer sandbox (for feature branch merge request validation), a full sandbox (for integration testing on `develop`), and production (deployed manually on `main` merge). They want branch pushes and merge requests to trigger the correct action per environment automatically.

**Problem:** Without branch conditions, every push to every branch would trigger the same deploy job, risking feature-in-progress metadata reaching production. The team also has no Apex test gate, meaning a deploy can reach production with coverage below the Salesforce-enforced 75% threshold.

**Solution:**

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

# MR / feature branches: validate only
validate-metadata:
  stage: validate
  script:
    - echo "$SF_JWT_SERVER_KEY_DEV" | base64 -d > /tmp/server.key
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
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH =~ /^feature\//'

# Develop: run Apex tests with coverage gate
apex-tests:
  stage: test
  script:
    - echo "$SF_JWT_SERVER_KEY_DEV" | base64 -d > /tmp/server.key
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

# Develop: deploy to sandbox after tests pass
deploy-sandbox:
  stage: deploy
  script:
    - echo "$SF_JWT_SERVER_KEY_DEV" | base64 -d > /tmp/server.key
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

# Main: deploy to production with manual gate
deploy-production:
  stage: deploy
  script:
    - echo "$SF_JWT_SERVER_KEY_PROD" | base64 -d > /tmp/server.key
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

**GitLab CI/CD variables to configure (Settings > CI/CD > Variables):**

| Variable | Masked | Protected | Description |
|---|---|---|---|
| `SF_JWT_SERVER_KEY_DEV` | Yes | No | `base64 -w 0 server.key` output for dev Connected App |
| `SF_CONSUMER_KEY_DEV` | Yes | No | Consumer key of dev sandbox Connected App |
| `SF_USERNAME_DEV` | Yes | No | Pre-authorized username in dev/sandbox org |
| `SF_JWT_SERVER_KEY_PROD` | Yes | Yes | `base64 -w 0 server.key` output for prod Connected App |
| `SF_CONSUMER_KEY_PROD` | Yes | Yes | Consumer key of production Connected App |
| `SF_USERNAME_PROD` | Yes | Yes | Pre-authorized username in production org |

**Why it works:** `rules:` conditions ensure merge request and feature branch pipelines validate only (no deploy). The `develop` push triggers the test job first; `deploy-sandbox` uses `needs: [apex-tests]` so it only runs after the test job passes. The `main` push triggers the production job only with an explicit `when: manual` click in GitLab — preventing accidental automated production deploys. Base64-encoded key values satisfy GitLab's variable masking requirements for multi-line content containing newlines.

---

## Example 2: Fixing a Broken Pipeline — JWT Certificate Expired Mid-Sprint

**Context:** A team's GitLab CI Salesforce pipeline had been running cleanly for 11 months. One morning, every pipeline job fails at the `sf org login jwt` step with the error `INVALID_SESSION_ID`. No code changes were made overnight.

**Problem:** The JWT certificate uploaded to the Connected App was generated with `openssl ... -days 365` 11 months earlier and has now expired. Salesforce returns `INVALID_SESSION_ID` for every JWT authentication attempt once the cert expires. The failure message is identical to a credential misconfiguration, making the root cause non-obvious to someone who has not seen cert expiry before.

**Solution:**

Step 1 — Verify the cert is expired (on a developer machine):
```bash
# Decode the stored variable locally to inspect the cert
echo "$SF_JWT_SERVER_KEY_DEV" | base64 -d > /tmp/check.key
# Or if you have the original .crt file:
openssl x509 -in server.crt -noout -dates
# notAfter=Apr 03 12:00:00 2025 GMT  ← compare to today's date
```

Step 2 — Regenerate the certificate with an extended lifespan:
```bash
openssl req -x509 -nodes -sha256 -days 730 -newkey rsa:2048 \
  -keyout server.key -out server.crt \
  -subj "/C=US/ST=CA/L=SF/O=MyOrg/CN=ci-service"
```
Using `-days 730` extends the rotation cycle to two years.

Step 3 — Upload `server.crt` to Salesforce:
- Setup > App Manager > find the Connected App > Edit
- Under OAuth Policies > Certificate > Upload the new `.crt` file > Save

Step 4 — Update the GitLab CI/CD variable:
```bash
# Encode the new key for GitLab variable storage
base64 -w 0 server.key
# Copy output; update SF_JWT_SERVER_KEY_DEV and SF_JWT_SERVER_KEY_PROD
# in Settings > CI/CD > Variables (overwrite existing value)
```

Step 5 — Delete local key files:
```bash
rm server.key server.crt
```

Step 6 — Record the new expiry date in the team calendar with a 30-day advance reminder.

**Why it works:** The Connected App now trusts the new certificate, and the base64-encoded GitLab variable contains the matching private key. Extending to 730 days reduces rotation frequency from annually to biennially. Documenting the expiry date prevents a repeat of the same silent failure.

---

## Anti-Pattern: Using SFDP URL Auth Instead of JWT

**What practitioners do:** To avoid JWT Connected App setup complexity, some teams generate an SFDP URL via `sf org display --verbose --target-org <alias>` and store the `force://...` URL as a GitLab CI/CD variable named `SFDX_AUTH_URL`.

**What goes wrong:**
- The SFDP URL contains an embedded OAuth refresh token. If the GitLab CI/CD variable is accidentally logged, shared, or exposed in a merge request pipeline (which runs in a less-trusted context by default), that token grants full org access.
- SFDP URL tokens can expire when the underlying session policy changes, causing intermittent auth failures that are harder to diagnose than JWT cert expiry.
- SFDP URLs cannot be masked in GitLab CI/CD variables because they contain characters (`://`, `?`, `=`) that GitLab's masking system rejects. Storing the URL unmasked means it can appear in job logs.

**Correct approach:**
- Use JWT Bearer Flow as documented in this skill. JWT generates a new short-lived access token on every run — no refresh token is embedded in any variable.
- Per the Salesforce DX Developer Guide, JWT Bearer Flow is the explicitly recommended authentication method for CI/CD pipelines.
- If SFDP URL auth is unavoidable as a short-term workaround: base64-encode the URL, mark the variable as masked, and never echo it in a script block.
