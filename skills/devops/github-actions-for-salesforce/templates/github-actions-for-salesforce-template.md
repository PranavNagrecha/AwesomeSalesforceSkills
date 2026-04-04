# GitHub Actions for Salesforce — Work Template

Use this template when setting up, reviewing, or troubleshooting a GitHub Actions CI/CD pipeline for Salesforce.

## Scope

**Skill:** `github-actions-for-salesforce`

**Request summary:** (fill in what the user asked for — e.g., "Set up a new pipeline", "Audit existing workflow", "Fix auth failure")

---

## Context Gathered

Answer these before generating any workflow YAML or diagnosis:

- **Connected App status:** [ Already configured with JWT | Needs to be created ]
- **Org type(s):** [ Sandbox | Production | Scratch org | Dev Hub ]
- **Sandbox login URL:** [ https://test.salesforce.com | custom domain: ________ ]
- **Branch strategy:** [ main → production | develop → sandbox | feature/* → scratch org | other: ________ ]
- **Existing pipeline:** [ None — starting from scratch | Exists — location: ________ ]
- **CI failure symptom (if troubleshooting):** [ INVALID_SESSION_ID | No org found for alias | Coverage below 75% | Timeout | Other: ________ ]

---

## Approach

Which mode applies?

- [ ] **Mode 1: Set up from scratch** — No `.github/workflows/deploy.yml` exists
- [ ] **Mode 2: Audit existing pipeline** — Review for security/best-practice gaps
- [ ] **Mode 3: Troubleshoot failure** — Diagnose a specific error in a running pipeline

---

## GitHub Actions Workflow Template

Copy this block and fill in the `[PLACEHOLDER]` values. Remove sections that do not apply.

```yaml
# .github/workflows/deploy.yml
# Generated from: github-actions-for-salesforce skill template
name: Salesforce CI/CD

on:
  push:
    branches:
      - [BRANCH_NAME_FOR_DEPLOY]        # e.g., main
  pull_request:
    branches:
      - [BRANCH_NAME_FOR_PR_VALIDATE]   # e.g., main, develop

jobs:
  validate-and-deploy:
    runs-on: ubuntu-latest
    steps:
      # ── Checkout ──────────────────────────────────────────────────────
      - uses: actions/checkout@v4

      # ── Install Salesforce CLI (sf v2) ────────────────────────────────
      - name: Install Salesforce CLI
        run: npm install --global @salesforce/cli@latest

      # ── Write JWT server key from GitHub Secret to temp file ──────────
      # GitHub Secrets are env vars, not files. Write to /tmp at runtime.
      - name: Write JWT server key
        run: echo "$SF_JWT_SERVER_KEY" > /tmp/server.key
        env:
          SF_JWT_SERVER_KEY: ${{ secrets.[SF_JWT_SERVER_KEY_SECRET_NAME] }}
          # Replace [SF_JWT_SERVER_KEY_SECRET_NAME] with your actual secret name
          # e.g., secrets.SF_JWT_SERVER_KEY

      # ── Authenticate to Salesforce org via JWT Bearer Flow ────────────
      # Requires: Connected App with JWT enabled + pre-authorized user
      - name: Authenticate to Salesforce
        run: |
          sf org login jwt \
            --client-id "$SF_CONSUMER_KEY" \
            --jwt-key-file /tmp/server.key \
            --username "$SF_USERNAME" \
            --instance-url "[INSTANCE_URL]" \
            --alias target-org \
            --set-default
          # [INSTANCE_URL]: https://test.salesforce.com  (sandbox)
          # [INSTANCE_URL]: https://login.salesforce.com (production)
          # [INSTANCE_URL]: https://[mydomain].my.salesforce.com (custom domain)
        env:
          SF_CONSUMER_KEY: ${{ secrets.[SF_CONSUMER_KEY_SECRET_NAME] }}
          SF_USERNAME: ${{ secrets.[SF_USERNAME_SECRET_NAME] }}
          # Replace placeholders with your actual secret names

      # ── Run Apex tests with coverage collection ───────────────────────
      - name: Run Apex tests
        run: |
          sf apex run test \
            --target-org target-org \
            --test-level RunLocalTests \
            --code-coverage \
            --result-format json \
            --output-dir test-results \
            --wait [TEST_TIMEOUT_MINUTES]
            # [TEST_TIMEOUT_MINUTES]: e.g., 20

      # ── Enforce coverage threshold ────────────────────────────────────
      - name: Enforce [COVERAGE_THRESHOLD]% coverage
        run: |
          python3 - <<'EOF'
          import json, sys
          with open("test-results/test-result.json") as f:
              data = json.load(f)
          raw = data.get("summary", {}).get("orgWideCoverage", "0%")
          pct = float(raw.replace("%", ""))
          threshold = [COVERAGE_THRESHOLD]  # Replace with number, e.g. 75
          print(f"Org-wide coverage: {pct}%  (required: {threshold}%)")
          if pct < threshold:
              print(f"FAIL: coverage {pct}% is below required {threshold}%")
              sys.exit(1)
          EOF
          # [COVERAGE_THRESHOLD]: Minimum: 75 (Salesforce platform requirement)

      # ── Deploy (branch-conditional — only runs on target branch push) ─
      - name: Deploy to Salesforce
        if: github.ref == 'refs/heads/[BRANCH_NAME_FOR_DEPLOY]' && github.event_name == 'push'
        run: |
          sf project deploy start \
            --target-org target-org \
            --source-dir [SOURCE_DIR] \
            --test-level [DEPLOY_TEST_LEVEL] \
            --wait [DEPLOY_TIMEOUT_MINUTES]
            # [SOURCE_DIR]: e.g., force-app
            # [DEPLOY_TEST_LEVEL]: RunLocalTests | NoTestRun (if pre-validated above)
            # [DEPLOY_TIMEOUT_MINUTES]: e.g., 30

      # ── Cleanup — always runs, even if earlier steps fail ─────────────
      - name: Remove JWT key file
        if: always()
        run: rm -f /tmp/server.key

      # ── Upload test results as workflow artifact for audit ─────────────
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: apex-test-results-${{ github.run_id }}
          path: test-results/
```

---

## GitHub Secrets Checklist

Set these under: Repository Settings > Secrets and variables > Actions > New repository secret

| Secret Name | Value | Notes |
|---|---|---|
| `SF_JWT_SERVER_KEY` | Full content of `server.key` file | Multi-line PEM content; paste as-is |
| `SF_CONSUMER_KEY` | Consumer Key from Connected App | Found in Setup > App Manager > View |
| `SF_USERNAME` | Username of the pre-authorized CI user | e.g., `ci-user@myorg.com` |

For multiple environments, use GitHub Environments and environment-scoped secrets instead of repository secrets.

---

## Connected App Setup Checklist

Complete these steps in the target Salesforce org before running the pipeline:

- [ ] Setup > App Manager > New Connected App
- [ ] Enable OAuth Settings; add scopes: `api`, `web`, `refresh_token`
- [ ] Enable "Use digital signatures"; upload `server.crt` (public certificate)
- [ ] Save, then: Setup > App Manager > [App] > Manage > Edit Policies
- [ ] Set "Permitted Users" to "Admin approved users are pre-authorized"
- [ ] Add the CI user's profile or a dedicated Permission Set to the authorized list

---

## Review Checklist

- [ ] `server.key` is in GitHub Secrets — never committed to the repository
- [ ] JWT certificate expiry date is documented and a reminder is set
- [ ] `--test-level` is explicit on all deploy commands
- [ ] Deploy step has branch + event-type `if:` guard
- [ ] `if: always()` cleanup step removes `/tmp/server.key`
- [ ] All `sfdx force:*` references replaced with `sf` CLI v2 commands
- [ ] Separate secrets per environment (sandbox vs. production)
- [ ] Test results uploaded as artifact for audit trail

---

## Notes

Record any deviations from the standard pattern and why.
