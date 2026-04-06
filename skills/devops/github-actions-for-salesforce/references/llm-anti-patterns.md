# LLM Anti-Patterns — GitHub Actions for Salesforce

Common mistakes AI coding assistants make when generating or advising on GitHub Actions CI/CD for Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Storing JWT Private Key as a Plain GitHub Secret String

**What the LLM generates:** Workflow YAML that reads the server key directly from a secret as text (`echo "${{ secrets.SERVER_KEY }}" > server.key`) without base64 encoding/decoding, which corrupts multi-line PEM keys because GitHub secrets strip newlines.

**Why it happens:** Single-line secrets work fine. Multi-line PEM private keys lose their line breaks when stored directly as GitHub secrets. LLMs do not consistently handle this encoding requirement.

**Correct pattern:**

```yaml
# Encode the key before storing as a secret:
# base64 -i server.key | pbcopy  (macOS)
# base64 server.key               (Linux — copy output to GitHub secret)

# In the workflow, decode the key:
- name: Create server key file
  run: echo "${{ secrets.SERVER_KEY_BASE64 }}" | base64 --decode > server.key

# Clean up after use:
- name: Cleanup
  if: always()
  run: rm -f server.key
```

**Detection hint:** Flag workflows that write `${{ secrets.SERVER_KEY }}` directly to a file without base64 decoding. Multi-line PEM keys require encoding/decoding.

---

## Anti-Pattern 2: Using Deprecated sfdx CLI Commands in Workflow Steps

**What the LLM generates:** Workflow steps with `sfdx force:auth:jwt:grant`, `sfdx force:source:deploy`, or `sfdx force:apex:test:run` instead of the current `sf` CLI equivalents.

**Why it happens:** The `sfdx` namespace has years more training data than the unified `sf` CLI. LLMs default to the older commands.

**Correct pattern:**

```yaml
# Current sf CLI commands:
- run: sf org login jwt --client-id ${{ secrets.CONSUMER_KEY }} --jwt-key-file server.key --username ${{ secrets.SF_USERNAME }} --instance-url https://login.salesforce.com
- run: sf project deploy start --target-org ${{ secrets.SF_USERNAME }} --test-level RunLocalTests
- run: sf apex run test --target-org ${{ secrets.SF_USERNAME }} --code-coverage --result-format human

# Deprecated equivalents (do not use):
# sfdx force:auth:jwt:grant --clientid ... --jwtkeyfile ... --username ...
# sfdx force:source:deploy -u ... -l RunLocalTests
# sfdx force:apex:test:run -u ... --codecoverage
```

**Detection hint:** Flag workflow YAML containing `sfdx force:` commands. Regex: `sfdx\s+force:`.

---

## Anti-Pattern 3: Hardcoding test.salesforce.com vs login.salesforce.com

**What the LLM generates:** `--instance-url https://login.salesforce.com` for all deployment targets, including sandbox environments that require `https://test.salesforce.com`.

**Why it happens:** Production login URL dominates training examples. LLMs do not parameterize the instance URL per environment.

**Correct pattern:**

```yaml
# Use environment-specific secrets or variables:
jobs:
  deploy-sandbox:
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - run: sf org login jwt --instance-url https://test.salesforce.com ...

  deploy-production:
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - run: sf org login jwt --instance-url https://login.salesforce.com ...

# Or use a single parameterized secret:
# SF_INSTANCE_URL (set per GitHub environment)
- run: sf org login jwt --instance-url ${{ vars.SF_INSTANCE_URL }} ...
```

**Detection hint:** Flag sandbox deployment jobs using `login.salesforce.com`. Check for hardcoded instance URLs that should vary by environment.

---

## Anti-Pattern 4: Missing Validate-Only Step Before Production Deploy

**What the LLM generates:** A workflow that deploys directly to production on push/merge without a separate validation step, missing the opportunity to catch errors without committing changes.

**Why it happens:** Validation adds an extra workflow step. LLMs optimize for brevity and produce single-step deploy workflows.

**Correct pattern:**

```yaml
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install SF CLI
        run: npm install -g @salesforce/cli
      - name: Auth
        run: |
          echo "${{ secrets.SERVER_KEY_BASE64 }}" | base64 --decode > server.key
          sf org login jwt --client-id ${{ secrets.CONSUMER_KEY }} --jwt-key-file server.key --username ${{ secrets.SF_USERNAME }} --instance-url https://login.salesforce.com
      - name: Validate (dry run)
        run: sf project deploy start --target-org ${{ secrets.SF_USERNAME }} --test-level RunLocalTests --dry-run
      - name: Cleanup
        if: always()
        run: rm -f server.key

  deploy:
    needs: validate
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      # ... same auth steps ...
      - name: Deploy
        run: sf project deploy start --target-org ${{ secrets.SF_USERNAME }} --test-level RunLocalTests
```

**Detection hint:** Flag production deployment workflows that do not include a `--dry-run` validation step or a separate validation job before the deploy job.

---

## Anti-Pattern 5: Not Pinning the Salesforce CLI Version

**What the LLM generates:** `npm install -g @salesforce/cli` without a version pin, meaning the workflow installs the latest CLI version on every run. A breaking change in the CLI can silently break the pipeline.

**Why it happens:** Tutorials use `npm install -g @salesforce/cli` for simplicity. Version pinning is a CI best practice not always demonstrated in Salesforce-specific training data.

**Correct pattern:**

```yaml
# Pin the CLI version for reproducible builds:
- name: Install SF CLI
  run: npm install -g @salesforce/cli@2.49.6

# Or use the official Salesforce CLI GitHub Action:
- name: Install SF CLI
  uses: salesforcecli/setup-sf-cli@v1
  with:
    version: '2.49.6'

# Periodically update the pinned version in a dedicated PR.
```

**Detection hint:** Flag `npm install -g @salesforce/cli` without a version number. Also flag `npm install -g sfdx-cli` (deprecated package name).
