# Examples — GitHub Actions for Salesforce

## Example 1: Full Pipeline — PR Validate + Main Branch Deploy with JWT Auth

**Context:** A team maintains a Salesforce DX project in GitHub. They want pull requests to automatically validate metadata and run Apex tests against a sandbox, but only deploy to production when a PR merges to `main`.

**Problem:** Without a CI pipeline, developers rely on manual deploys via VS Code or Workbench. Changes that fail Apex tests get pushed to production, causing org-wide coverage drops below 75% and triggering a Salesforce deployment block.

**Solution:**

```yaml
# .github/workflows/deploy.yml
name: Salesforce CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Salesforce CLI
        run: npm install --global @salesforce/cli@latest

      # Write JWT key from secret to a temp file
      - name: Write JWT server key
        run: echo "$SF_JWT_SERVER_KEY" > /tmp/server.key
        env:
          SF_JWT_SERVER_KEY: ${{ secrets.SF_JWT_SERVER_KEY }}

      # Authenticate to sandbox (PR) or production (push to main)
      - name: Authenticate to Salesforce
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            TARGET_URL="https://test.salesforce.com"
            TARGET_USER="${{ secrets.SF_SANDBOX_USERNAME }}"
            TARGET_KEY="${{ secrets.SF_SANDBOX_CONSUMER_KEY }}"
          else
            TARGET_URL="https://login.salesforce.com"
            TARGET_USER="${{ secrets.SF_PROD_USERNAME }}"
            TARGET_KEY="${{ secrets.SF_PROD_CONSUMER_KEY }}"
          fi
          sf org login jwt \
            --client-id "$TARGET_KEY" \
            --jwt-key-file /tmp/server.key \
            --username "$TARGET_USER" \
            --instance-url "$TARGET_URL" \
            --alias target-org \
            --set-default

      # Run Apex tests and collect JSON results
      - name: Run Apex tests
        run: |
          sf apex run test \
            --target-org target-org \
            --test-level RunLocalTests \
            --code-coverage \
            --result-format json \
            --output-dir test-results \
            --wait 20

      # Parse coverage and fail if below threshold
      - name: Enforce coverage threshold (75%)
        run: |
          python3 - <<'EOF'
          import json, sys
          with open("test-results/test-result.json") as f:
              data = json.load(f)
          raw = data.get("summary", {}).get("orgWideCoverage", "0%")
          pct = float(raw.replace("%", ""))
          print(f"Org-wide coverage: {pct}%")
          if pct < 75:
              print(f"FAIL: coverage {pct}% is below required 75%")
              sys.exit(1)
          EOF

      # Deploy ONLY when pushing to main (not on PRs)
      - name: Deploy to production
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: |
          sf project deploy start \
            --target-org target-org \
            --source-dir force-app \
            --test-level RunLocalTests \
            --wait 30

      # Always clean up the key file regardless of prior step outcome
      - name: Remove JWT key
        if: always()
        run: rm -f /tmp/server.key

      # Publish test results as a workflow artifact for audit
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: apex-test-results
          path: test-results/
```

**Why it works:** The `if: github.event_name == 'push'` guard on the deploy step ensures PRs only run validation. The `if: always()` on key cleanup guarantees the secret is removed from the runner even when earlier steps fail. Separate Consumer Key secrets per environment (`SF_SANDBOX_CONSUMER_KEY` vs. `SF_PROD_CONSUMER_KEY`) ensure that a compromised sandbox credential cannot be used to deploy to production.

---

## Example 2: Auditing an Existing Pipeline with Deprecated `sfdx` Commands

**Context:** A pipeline was written 18 months ago and uses the legacy `sfdx force:source:deploy` and `sfdx auth:jwt:grant` command namespace. The team asks whether the pipeline is still compliant.

**Problem:** The legacy `sfdx force:*` commands are deprecated as of Salesforce CLI v2 (Spring '24+). They still function but emit deprecation warnings that pollute CI logs, and Salesforce has announced they will be removed. The old `sfdx auth:jwt:grant` also uses a different flag set (`--clientid` vs. `--client-id`) that does not accept the new `--instance-url` flag correctly.

**Existing pipeline (problematic):**

```yaml
- name: Authenticate
  run: |
    sfdx auth:jwt:grant \
      --clientid ${{ secrets.CONSUMER_KEY }} \
      --jwtkeyfile server.key \
      --username ${{ secrets.SF_USERNAME }} \
      --setdefaultdevhubusername

- name: Deploy
  run: sfdx force:source:deploy -p force-app -u ${{ secrets.SF_USERNAME }} -l RunLocalTests
```

**Corrected pipeline using `sf` CLI v2:**

```yaml
- name: Write JWT key
  run: echo "$SF_JWT_SERVER_KEY" > /tmp/server.key
  env:
    SF_JWT_SERVER_KEY: ${{ secrets.SF_JWT_SERVER_KEY }}

- name: Authenticate
  run: |
    sf org login jwt \
      --client-id "${{ secrets.CONSUMER_KEY }}" \
      --jwt-key-file /tmp/server.key \
      --username "${{ secrets.SF_USERNAME }}" \
      --alias target-org \
      --set-default

- name: Deploy
  run: |
    sf project deploy start \
      --target-org target-org \
      --source-dir force-app \
      --test-level RunLocalTests \
      --wait 30

- name: Remove JWT key
  if: always()
  run: rm -f /tmp/server.key
```

**Why it works:** The `sf` CLI v2 uses a consistent `--flag-name` format across all commands. `sf org login jwt` replaces `sfdx auth:jwt:grant` with the same JWT mechanism but updated flag names and improved error messages. `sf project deploy start` replaces `sfdx force:source:deploy` and returns structured JSON output that can be parsed by downstream steps.

---

## Anti-Pattern: Storing `server.key` in the Repository

**What practitioners do:** To avoid setting up GitHub Secrets, some teams commit `server.key` directly into the repository (sometimes inside a `.ci/` folder) and reference it by file path in the workflow.

**What goes wrong:** The private key is exposed in the repository's git history permanently. Anyone with read access to the repo — including future contributors, forks, and any tool that clones the repo — has the private key. They can use it to authenticate as the pre-authorized CI user to the target Salesforce org, potentially extracting all data or deploying malicious metadata.

**Correct approach:** Store the private key content in a GitHub Secret (`SF_JWT_SERVER_KEY`). Write it to a temp file at runtime, use it for auth, and delete it in an `if: always()` cleanup step. Never add `server.key` to `.gitignore` and consider it protected — if it was ever committed, rotate the certificate immediately (generate a new key pair, upload the new certificate to the Connected App, revoke the old one).
