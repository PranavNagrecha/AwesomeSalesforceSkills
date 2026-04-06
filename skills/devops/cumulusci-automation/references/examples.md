# Examples — CumulusCI Automation

## Example 1: Adding a Custom Configuration Step to the Standard dev_org Flow

**Context:** A nonprofit Salesforce project uses CumulusCI for local development. The standard `dev_org` flow deploys the main package metadata and runs permset assignments, but the team also needs to deploy a set of custom sharing rules and load a small reference dataset after the standard flow completes. The developer does not want to duplicate the standard flow's steps.

**Problem:** Without extending `dev_org`, the developer either skips the custom setup entirely (making every new dev org incomplete) or manually runs extra commands after `cci flow run dev_org`, which is error-prone and undocumented.

**Solution:**

```yaml
# cumulusci.yml

tasks:
  deploy_sharing_rules:
    description: Deploy sharing rules metadata after base org setup
    class_path: cumulusci.tasks.salesforce.Deploy
    options:
      path: unpackaged/config/sharing
      unmanaged: True

  load_reference_data:
    description: Load Picklist and RecordType reference datasets
    class_path: cumulusci.tasks.bulkdata.LoadData
    options:
      mapping: datasets/reference/mapping.yml
      sql_path: datasets/reference/data.sql

flows:
  dev_org:
    steps:
      # Standard dev_org steps 1-3 remain untouched; insert after step 3
      3.1:
        task: deploy_sharing_rules
      3.2:
        task: load_reference_data
        options:
          ignore_row_errors: True   # step-level override for dev environments only
```

Run the extended flow:

```bash
cci flow run dev_org --org dev
```

Verify the merged step order before running:

```bash
cci flow info dev_org
```

**Why it works:** CumulusCI merges the `dev_org` extension with the standard library flow at runtime. Steps numbered 3.1 and 3.2 sort between step 3 and step 4 of the standard flow. The standard steps are never duplicated; they are inherited automatically. When CumulusCI upgrades the standard `dev_org` flow, the inherited steps update automatically.

---

## Example 2: Running Robot Framework Acceptance Tests in a CI Flow

**Context:** A consulting partner team delivers a managed package. Acceptance tests are written in Robot Framework with Selenium. The team wants Robot tests to run automatically on every feature branch push using CumulusCI and GitHub Actions.

**Problem:** Without CumulusCI wiring, the Robot suite requires manual credential management (org URL, session token) and browser driver setup. Running Robot independently of CumulusCI means duplicating auth logic and losing the automatic org lifecycle management (create, deploy, test, delete).

**Solution:**

```yaml
# cumulusci.yml

tasks:
  robot:
    options:
      suites: robot/tests/acceptance
      output_dir: robot_results
      browser: headlesschrome

flows:
  ci_acceptance:
    description: Deploy and run Robot acceptance tests
    steps:
      1:
        flow: dev_org           # provision and deploy against a scratch org
      2:
        task: robot             # CCI injects org credentials automatically
```

GitHub Actions workflow:

```yaml
# .github/workflows/acceptance.yml
name: Acceptance Tests
on:
  push:
    branches-ignore: [main]

jobs:
  acceptance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install CumulusCI and browser drivers
        run: |
          pip install cumulusci
          pip install robotframework-browser
          rfbrowser init

      - name: Authenticate Dev Hub (JWT)
        run: |
          printf '%s' "${{ secrets.DEVHUB_JWT_KEY }}" > /tmp/server.key
          chmod 600 /tmp/server.key
          sf org login jwt \
            --client-id "${{ secrets.DEVHUB_CLIENT_ID }}" \
            --jwt-key-file /tmp/server.key \
            --username "${{ secrets.DEVHUB_USERNAME }}" \
            --alias DevHub \
            --set-default-dev-hub
          rm /tmp/server.key

      - name: Run acceptance tests
        run: cci flow run ci_acceptance --org feature

      - name: Upload Robot results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: robot-results
          path: robot_results/
```

**Why it works:** CumulusCI's `robot` task automatically sets `${LOGIN_URL}`, `${SESSION_ID}`, and `${ORG_ID}` as Robot variables, so test suites do not need to handle authentication. The task also manages ChromeDriver/browser setup when `browser: headlesschrome` is set. Wrapping everything in a `ci_acceptance` flow ensures the org is provisioned and torn down consistently.

---

## Anti-Pattern: Hardcoding SFDX Auth URLs in CI Instead of JWT

**What practitioners do:** Store a full SFDX auth URL (from `sf org display --verbose`) as a CI secret and use it to authenticate CumulusCI in pipelines.

```bash
# Wrong approach — do not do this
echo "$SFDX_AUTH_URL" > auth.txt
sf org login sfdx-url --sfdx-url-file auth.txt --alias DevHub --set-default-dev-hub
```

**What goes wrong:** SFDX auth URLs embed a refresh token tied to a specific user's OAuth session. The token expires silently when the session is revoked or the Connected App policy changes, is tied to a personal user account (not a service account), and if leaked grants persistent org access until manually revoked.

**Correct approach:** Configure a Connected App with a certificate, store only the private key as a CI secret, and authenticate via `sf org login jwt`. The JWT private key can be rotated by uploading a new certificate to the Connected App and updating the CI secret — no interactive re-auth required.

```bash
printf '%s' "$DEVHUB_JWT_KEY" > /tmp/server.key
chmod 600 /tmp/server.key
sf org login jwt \
  --client-id "$DEVHUB_CLIENT_ID" \
  --jwt-key-file /tmp/server.key \
  --username "$DEVHUB_USERNAME" \
  --alias DevHub \
  --set-default-dev-hub
rm /tmp/server.key
```
