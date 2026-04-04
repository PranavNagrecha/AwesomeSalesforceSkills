# Examples — Bitbucket Pipelines for Salesforce

## Example 1: Branch-Based Promotion Pipeline (Feature → Sandbox → Production)

**Context:** A mid-size ISV team manages a Salesforce DX project in Bitbucket. They have three persistent environments: a developer sandbox (for feature branch validation), a full sandbox (for integration testing on `develop`), and production (deployed on `main` merge). They want branch pushes to trigger the correct action for each environment automatically.

**Problem:** Without branch conditions, every push deploys to the same org regardless of branch. Teams either deploy feature work to production or manually trigger deploys — both introduce risk. The team also has no Apex test gate, meaning a deploy can reach production with coverage below 75%.

**Solution:**

```yaml
# bitbucket-pipelines.yml
image: node:20

pipelines:
  branches:
    # Feature branches: validate only, no deploy
    'feature/**':
      - step:
          name: Validate Metadata (Dry Run)
          script:
            - npm install --global @salesforce/cli@latest
            - echo "$SF_JWT_SERVER_KEY_DEV" > /tmp/server.key
            - sf org login jwt
                --client-id "$SF_CONSUMER_KEY_DEV"
                --jwt-key-file /tmp/server.key
                --username "$SF_USERNAME_DEV"
                --instance-url "https://test.salesforce.com"
                --alias dev-org --set-default
            - sf project deploy validate
                --target-org dev-org
                --source-dir force-app
                --test-level RunLocalTests
                --wait 30
          after-script:
            - rm -f /tmp/server.key

    # Develop branch: test then deploy to full sandbox
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
                --alias sandbox-org --set-default
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
                assert float(pct) >= 75, f'Coverage {pct}% below 75% threshold'
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
                --alias sandbox-org --set-default
            - sf project deploy start
                --target-org sandbox-org
                --source-dir force-app
                --test-level NoTestRun
                --wait 30
          after-script:
            - rm -f /tmp/server.key

    # Main branch: deploy to production with full test run
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
                --alias prod-org --set-default
            - sf project deploy start
                --target-org prod-org
                --source-dir force-app
                --test-level RunLocalTests
                --wait 60
          after-script:
            - rm -f /tmp/server.key
```

**Bitbucket repository variables to configure (all secured/masked):**
- `SF_JWT_SERVER_KEY_DEV` — contents of `server.key` for dev sandbox Connected App
- `SF_CONSUMER_KEY_DEV` — consumer key of dev sandbox Connected App
- `SF_USERNAME_DEV` — pre-authorized username in dev sandbox
- `SF_JWT_SERVER_KEY_SANDBOX`, `SF_CONSUMER_KEY_SANDBOX`, `SF_USERNAME_SANDBOX` — full sandbox equivalents
- `SF_JWT_SERVER_KEY_PROD`, `SF_CONSUMER_KEY_PROD`, `SF_USERNAME_PROD` — production equivalents

**Why it works:** Branch-specific `pipelines.branches:` sections ensure feature branch pushes only validate (no deploy), `develop` pushes deploy to the sandbox, and `main` merges deploy to production. Separate secured variables per environment ensure a compromised dev credential cannot authenticate to production. The `after-script:` block guarantees key file deletion even if the deploy step fails.

---

## Example 2: Fixing a Broken Pipeline — JWT Certificate Expired Mid-Sprint

**Context:** A team's Bitbucket Pipelines Salesforce CI had been running cleanly for 11 months. One morning, every pipeline step fails at the `sf org login jwt` step with the error `INVALID_SESSION_ID`. No code changes were made the night before.

**Problem:** The JWT certificate uploaded to the Connected App was generated with `openssl ... -days 365` eleven months earlier and has expired. Salesforce returns `INVALID_SESSION_ID` for every JWT authentication attempt once the cert expires. The pipeline failure message looks identical to a credential misconfiguration, making the root cause non-obvious.

**Solution:**

Step 1 — Regenerate the certificate on a developer machine:
```bash
openssl req -x509 -nodes -sha256 -days 730 -newkey rsa:2048 \
  -keyout server.key -out server.crt \
  -subj "/C=US/ST=CA/L=SF/O=MyOrg/CN=ci-service"
```
(Using `-days 730` gives a 2-year lifespan — longer rotation cycle.)

Step 2 — Upload `server.crt` to Salesforce:
- Setup > App Manager > find the Connected App > Edit
- Under "OAuth Policies" > "Certificate" > Upload new `.crt` file
- Save the Connected App

Step 3 — Update Bitbucket repository variable:
- Repository Settings > Repository variables
- Find `SF_JWT_SERVER_KEY_PROD` (and sandbox equivalents)
- Replace the value with the contents of the new `server.key`
- Keep the variable secured (masked)

Step 4 — Delete the local `server.key` file after uploading:
```bash
rm server.key
```

Step 5 — Record the new expiry date in the team's calendar with a 30-day advance reminder.

**Why it works:** The Connected App now trusts the new certificate, and the Bitbucket variable contains the matching private key. Extending the cert to 730 days reduces rotation frequency. Documenting the expiry prevents a repeat of the same silent failure. This procedure applies equally to sandbox and production Connected Apps — each environment has its own Connected App and must be rotated independently.

---

## Anti-Pattern: Storing the SFDP URL as an Unsecured Bitbucket Variable

**What practitioners do:** To avoid the complexity of JWT setup, some teams generate an SFDP URL via `sf org display --verbose --target-org <alias>` and store the resulting `force://...` URL as an unsecured (non-masked) Bitbucket repository variable named `SFDX_AUTH_URL`.

**What goes wrong:** Unsecured Bitbucket repository variables appear in plain text in build logs whenever the variable is referenced with `echo $SFDX_AUTH_URL` or in debug output. Any team member with repository read access can view build logs and retrieve the SFDP URL, which contains an embedded refresh token granting full org access. Additionally, SFDP URLs can expire when the underlying session or refresh token expires, causing intermittent auth failures that are harder to debug than JWT cert expiry.

**Correct approach:**
- If using SFDP URL auth: store it in a **secured (masked)** Bitbucket repository variable and never `echo` it in a script. Prefer `sf org login sfdx-url --sfdx-url-file <file>` by writing the URL to a temp file rather than passing it inline.
- Preferred: Use JWT Bearer Flow instead. JWT authentication does not embed a live session token — it generates a new one on every run — so there is no refresh token to steal or expire unexpectedly. Per the Salesforce DX Developer Guide, JWT Bearer Flow is the recommended authentication method for CI/CD pipelines.
