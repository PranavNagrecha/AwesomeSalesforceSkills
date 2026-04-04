# LLM Anti-Patterns — GitLab CI for Salesforce

Common mistakes AI coding assistants make when generating or advising on GitLab CI pipelines for Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using GitHub Actions Syntax in `.gitlab-ci.yml`

**What the LLM generates:** A `.gitlab-ci.yml` that includes GitHub Actions constructs such as `uses: actions/checkout@v4`, `with:`, `env:` under a step block, or `if: github.ref == 'refs/heads/main'`. Some LLMs blend the two syntaxes when asked for "CI/CD for Salesforce" without a platform-specific prompt.

**Why it happens:** GitHub Actions is more prevalent in training data than GitLab CI. LLMs trained on both formats frequently blend the two syntaxes, especially when the prompt says "CI" without specifying "GitLab CI" explicitly. The two platforms share conceptual overlap (jobs, stages, steps) but have entirely different YAML schemas.

**Correct pattern:**

```yaml
# GitLab CI — correct structure
deploy-production:
  stage: deploy
  script:
    - echo "$SF_JWT_SERVER_KEY_PROD" | base64 -d > /tmp/server.key
    - sf org login jwt --client-id "$SF_CONSUMER_KEY_PROD" ...
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: manual
```

GitLab CI uses `script:` (not `run:`), `rules:` (not `if:` at the job level), and `before_script:` / `after_script:` instead of `if: always()` cleanup steps. There are no `uses:` reusable actions — use Docker images or shell scripts.

**Detection hint:** Scan the generated YAML for `uses:`, `with:`, `if: github.`, `actions/checkout`, or `env:` under a step-level key. Any of these indicates GitHub Actions syntax bleed.

---

## Anti-Pattern 2: Storing Raw Private Key as GitLab CI Variable Without Base64 Encoding

**What the LLM generates:** Instructions like "create a GitLab CI variable named `SF_JWT_SERVER_KEY` and paste the contents of `server.key` as the value." The LLM then writes `echo "$SF_JWT_SERVER_KEY" > /tmp/server.key` in the job script, which would appear correct — except the variable cannot actually be masked because it contains newlines and special characters.

**Why it happens:** This pattern works correctly in GitHub Actions, where secrets have no masking restriction on multi-line values. LLMs trained on GitHub Actions CI patterns apply the same approach to GitLab without accounting for GitLab's variable masking constraints. The result is a working but unmasked variable — a security gap.

**Correct pattern:**

```bash
# Developer machine — encode once
base64 -w 0 server.key
# Copy single-line output into GitLab variable (can now be masked)
```

```yaml
# .gitlab-ci.yml — decode at runtime
script:
  - echo "$SF_JWT_SERVER_KEY" | base64 -d > /tmp/server.key
  - sf org login jwt --jwt-key-file /tmp/server.key ...
after_script:
  - rm -f /tmp/server.key
```

**Detection hint:** Look for `echo "$SF_JWT_SERVER_KEY" > /tmp/server.key` without a `| base64 -d` pipe. If the variable value in the instructions is presented as a raw multi-line PEM block starting with `-----BEGIN RSA PRIVATE KEY-----`, the encoding step is missing.

---

## Anti-Pattern 3: Using `only:` / `except:` Instead of `rules:` for Branch Conditions

**What the LLM generates:** Branch conditions using the deprecated `only:` syntax:

```yaml
deploy-production:
  only:
    - main
```

or with regex:

```yaml
deploy-feature:
  only:
    - /^feature\/.*/
```

**Why it happens:** `only:` was the original GitLab CI branch-filtering mechanism and is still valid syntax, so it appears heavily in pre-2020 GitLab CI examples in training data. LLMs default to familiar patterns even when newer alternatives exist.

**Correct pattern:**

```yaml
deploy-production:
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: manual

validate-feature:
  rules:
    - if: '$CI_COMMIT_BRANCH =~ /^feature\//'
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```

`rules:` supports `when:`, `allow_failure:`, `variables:`, and `$CI_PIPELINE_SOURCE` conditions that `only:` does not. GitLab's own documentation recommends migrating from `only:` to `rules:`.

**Detection hint:** Grep the generated YAML for `only:` or `except:` at the job level (not nested inside `rules:`). Any occurrence of these top-level keys is the anti-pattern.

---

## Anti-Pattern 4: Omitting `--test-level` from `sf project deploy start` on Sandbox Deploys

**What the LLM generates:** A deploy job that calls `sf project deploy start --target-org sandbox-org --source-dir force-app --wait 30` without an explicit `--test-level` flag, with the implicit assumption that tests will run.

**Why it happens:** LLMs often conflate production and sandbox deploy behavior. In production orgs, Salesforce enforces test execution. For sandbox orgs, the default is `NoTestRun` — no tests run unless explicitly specified. This silent default is one of the most commonly missed Salesforce CI configuration issues.

**Correct pattern:**

```yaml
# Sandbox deploy — explicit test level
- sf project deploy start
    --target-org sandbox-org
    --source-dir force-app
    --test-level NoTestRun
    --wait 30

# Production deploy — RunLocalTests enforces 75% threshold
- sf project deploy start
    --target-org prod-org
    --source-dir force-app
    --test-level RunLocalTests
    --wait 60
```

Run a separate `sf apex run test` job with `--code-coverage` before the sandbox deploy to enforce a coverage gate independently of the deploy command.

**Detection hint:** Look for `sf project deploy start` calls that lack a `--test-level` flag. Also look for sandbox deploy jobs that do not have a preceding dedicated test job in the pipeline stages.

---

## Anti-Pattern 5: Missing `after_script:` Cleanup for Temporary Key Files

**What the LLM generates:** A job script that writes `server.key` to `/tmp/server.key` in the `script:` block and deletes it at the end of `script:`:

```yaml
script:
  - echo "$SF_JWT_SERVER_KEY" | base64 -d > /tmp/server.key
  - sf org login jwt --jwt-key-file /tmp/server.key ...
  - sf project deploy start ...
  - rm -f /tmp/server.key  # WRONG — not reached if deploy fails
```

**Why it happens:** LLMs model sequential cleanup as "run cleanup at the end of the sequence." They do not account for early job failure: if `sf project deploy start` fails, the `rm` command is never reached and the key file persists on the runner container for the remainder of its lifecycle.

**Correct pattern:**

```yaml
script:
  - echo "$SF_JWT_SERVER_KEY" | base64 -d > /tmp/server.key
  - sf org login jwt --jwt-key-file /tmp/server.key ...
  - sf project deploy start ...
  # No rm in script block
after_script:
  - rm -f /tmp/server.key  # always runs, even on failure
```

`after_script:` runs after every job execution, including failed jobs. This is the GitLab CI equivalent of GitHub Actions' `if: always()` cleanup step.

**Detection hint:** Search for `rm -f /tmp/server.key` (or any key file deletion) appearing inside `script:` rather than `after_script:`. If `after_script:` is absent from any job that writes a temp credential file, the anti-pattern is present.

---

## Anti-Pattern 6: Hardcoding `--instance-url https://login.salesforce.com` for Sandbox Orgs

**What the LLM generates:** A pipeline that uses `--instance-url https://login.salesforce.com` (the production login URL) for every `sf org login jwt` call, including sandbox and developer sandbox jobs.

**Why it happens:** `login.salesforce.com` is the most commonly cited Salesforce login URL in general documentation. LLMs default to the production URL without checking whether the target org is a sandbox, or assume it works universally.

**Correct pattern:**

```yaml
variables:
  SF_INSTANCE_URL_SANDBOX: "https://test.salesforce.com"
  SF_INSTANCE_URL_PROD: "https://login.salesforce.com"

# Sandbox job
- sf org login jwt --instance-url "$SF_INSTANCE_URL_SANDBOX" ...

# Production job
- sf org login jwt --instance-url "$SF_INSTANCE_URL_PROD" ...
```

Sandboxes and developer sandboxes always authenticate via `https://test.salesforce.com`. Using `login.salesforce.com` for a sandbox auth attempt fails because production authentication endpoints cannot resolve sandbox org usernames.

**Detection hint:** Look for `--instance-url https://login.salesforce.com` in sandbox or feature branch job scripts. Check whether the pipeline differentiates instance URLs by environment or hardcodes a single production URL across all jobs.
