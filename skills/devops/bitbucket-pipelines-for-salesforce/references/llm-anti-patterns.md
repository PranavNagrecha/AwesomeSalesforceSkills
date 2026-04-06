# LLM Anti-Patterns — Bitbucket Pipelines for Salesforce

Common mistakes AI coding assistants make when generating or advising on Bitbucket Pipelines CI/CD for Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Storing Salesforce Credentials in bitbucket-pipelines.yml

**What the LLM generates:** Pipeline YAML with plaintext consumer keys, server keys, or SFDX auth URLs directly in the `bitbucket-pipelines.yml` file instead of using Bitbucket Repository Variables.

**Why it happens:** LLMs generate complete, runnable examples and fill in credential placeholders with realistic values. The distinction between pipeline YAML (committed to Git) and repository variables (encrypted, not in source) is not always clear in training data.

**Correct pattern:**

```yaml
# bitbucket-pipelines.yml — credentials from secured repository variables only
pipelines:
  branches:
    main:
      - step:
          name: Deploy to Production
          script:
            - echo "$SF_SERVER_KEY" > server.key
            - sf org login jwt --client-id "$SF_CONSUMER_KEY" --jwt-key-file server.key --username "$SF_USERNAME" --instance-url https://login.salesforce.com
            - sf project deploy start --target-org "$SF_USERNAME" --test-level RunLocalTests
          after-script:
            - rm -f server.key

# SF_CONSUMER_KEY, SF_SERVER_KEY, SF_USERNAME stored as
# Bitbucket Repository Variables (Settings > Pipelines > Repository variables > Secured)
```

**Detection hint:** Flag `bitbucket-pipelines.yml` files containing literal private keys, consumer keys, or base64-encoded credentials. Regex: `-----BEGIN`, `3MVG`, or `force://` in YAML content.

---

## Anti-Pattern 2: Using Deprecated sfdx CLI Commands

**What the LLM generates:** Pipeline steps using `sfdx force:source:deploy`, `sfdx force:auth:jwt:grant`, or `sfdx force:apex:test:run` instead of current `sf` CLI commands.

**Why it happens:** The `sfdx` CLI was the primary tool for years and dominates training data. Salesforce unified the CLI under the `sf` namespace.

**Correct pattern:**

```yaml
# Current sf CLI commands:
- sf org login jwt --client-id $KEY --jwt-key-file server.key --username $USER
- sf project deploy start --target-org prod --test-level RunLocalTests
- sf apex run test --target-org prod --code-coverage

# Deprecated (do not use):
# sfdx force:auth:jwt:grant
# sfdx force:source:deploy
# sfdx force:apex:test:run
```

**Detection hint:** Flag pipeline YAML containing `sfdx force:` commands. Regex: `sfdx\s+force:` in script blocks.

---

## Anti-Pattern 3: Using login.salesforce.com for Sandbox Deployments

**What the LLM generates:** `--instance-url https://login.salesforce.com` for all environments, including sandbox deployments where the correct URL is `https://test.salesforce.com`.

**Why it happens:** Training data predominantly shows production login URLs. LLMs do not always parameterize the instance URL based on the target environment.

**Correct pattern:**

```yaml
pipelines:
  branches:
    develop:
      - step:
          name: Deploy to Sandbox
          script:
            - sf org login jwt --instance-url https://test.salesforce.com ...
    main:
      - step:
          name: Deploy to Production
          script:
            - sf org login jwt --instance-url https://login.salesforce.com ...

# Better: use deployment variables
# SF_INSTANCE_URL = https://test.salesforce.com (staging deployment)
# SF_INSTANCE_URL = https://login.salesforce.com (production deployment)
```

**Detection hint:** Flag sandbox deployment steps using `login.salesforce.com`. Check for hardcoded instance URLs that should be parameterized per environment.

---

## Anti-Pattern 4: Missing Apex Test Coverage Gate

**What the LLM generates:** A pipeline that deploys to production without running Apex tests or verifying the 75% code coverage threshold required by Salesforce for production deployments.

**Why it happens:** Basic pipeline examples focus on the deploy step. Test execution and coverage validation add steps that tutorials often skip.

**Correct pattern:**

```yaml
- step:
    name: Validate and Deploy
    script:
      - sf org login jwt --client-id "$SF_CONSUMER_KEY" --jwt-key-file server.key --username "$SF_USERNAME" --instance-url https://login.salesforce.com
      # Validate (dry run with tests):
      - sf project deploy start --target-org "$SF_USERNAME" --test-level RunLocalTests --dry-run
      # Deploy:
      - sf project deploy start --target-org "$SF_USERNAME" --test-level RunLocalTests
```

**Detection hint:** Flag pipelines deploying to production without `--test-level RunLocalTests` or `--test-level RunSpecifiedTests`. Look for missing test execution in production deployment steps.

---

## Anti-Pattern 5: Not Cleaning Up the JWT Server Key File

**What the LLM generates:** Pipeline that writes the JWT server key to a file but never removes it after use, leaving the private key on the CI build agent's filesystem.

**Why it happens:** LLMs focus on making the pipeline work without security cleanup. The `after-script` block in Bitbucket Pipelines (which runs regardless of step success/failure) is not always included.

**Correct pattern:**

```yaml
- step:
    name: Deploy
    script:
      - echo "$SF_SERVER_KEY_BASE64" | base64 --decode > server.key
      - sf org login jwt --client-id "$SF_CONSUMER_KEY" --jwt-key-file server.key --username "$SF_USERNAME"
      - sf project deploy start --target-org "$SF_USERNAME" --test-level RunLocalTests
    after-script:
      # Always clean up, even if deployment fails
      - rm -f server.key
      - sf org logout --target-org "$SF_USERNAME" --no-prompt || true
```

**Detection hint:** Flag pipelines that write `server.key` without a corresponding `rm -f server.key` in `after-script`. Check for `server.key` not in `.gitignore`.
