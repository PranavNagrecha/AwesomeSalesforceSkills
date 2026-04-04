# Gotchas — Bitbucket Pipelines for Salesforce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `after-script:` Is the Only Reliable Cleanup Point — Not `script:`

**What happens:** When a step's `script:` block fails mid-execution (e.g., a deploy step times out or a test fails), Bitbucket halts the remaining `script:` lines. Any `rm -f /tmp/server.key` placed at the end of the `script:` block is never reached. The private key file remains on the ephemeral build runner for the duration of that build job, accessible to any subsequent steps in the same build.

**When it occurs:** Any time a build step fails before reaching the cleanup line — which is exactly when failures are most likely. The key file is most at risk when the deployment itself fails.

**How to avoid:** Always place private key file deletion in the `after-script:` block, not in `script:`. Bitbucket's `after-script:` runs unconditionally after the step, whether `script:` succeeded or failed — it is the `finally` equivalent for pipeline steps:

```yaml
- step:
    name: Deploy
    script:
      - echo "$SF_JWT_SERVER_KEY" > /tmp/server.key
      - sf org login jwt --jwt-key-file /tmp/server.key ...
      - sf project deploy start ...
    after-script:
      - rm -f /tmp/server.key   # runs even if script: fails
```

---

## Gotcha 2: YAML Branch Glob Patterns Fail Silently When Unquoted

**What happens:** Bitbucket Pipelines branch matchers support glob syntax (e.g., `feature/**`). When these patterns are written without quotes in the YAML, some YAML parsers interpret `*` as a YAML alias anchor or merge key marker. The pattern parses without an error but never matches any branch. The step silently never triggers — no failure message, no warning, just no builds on feature branches.

**When it occurs:** When branch patterns containing `*` or `**` are written without surrounding quotes in `bitbucket-pipelines.yml`, for example:
```yaml
# BROKEN — * is ambiguous in unquoted YAML context
pipelines:
  branches:
    feature/**:
      - step: ...
```

**How to avoid:** Always quote branch glob patterns with single quotes in Bitbucket Pipelines YAML:
```yaml
# CORRECT
pipelines:
  branches:
    'feature/**':
      - step: ...
    'hotfix/*':
      - step: ...
```
Use the Bitbucket Pipeline YAML validator (available in the Bitbucket repository UI under Pipelines > Edit) to check patterns before committing.

---

## Gotcha 3: Connected App Pre-Authorization Is a Separate Step From Profile Assignment

**What happens:** JWT Bearer Flow auth fails with `Authentication failure. IP address is not allowed` or `user not authorized` even though the authenticating user has the correct profile and the Connected App is enabled for that profile. The Salesforce CLI returns a generic auth error with no indication that the pre-authorization step is missing.

**When it occurs:** When the Connected App's OAuth Policies are set to "Admin approved users are pre-authorized" but the specific user (or the user's profile) has not been explicitly added to the pre-authorized list. Profile-level access to the Connected App through a permission set or profile is necessary but not sufficient — JWT Bearer Flow requires the explicit pre-authorization in the Connected App's "Manage Connected Apps" settings.

**How to avoid:**
1. In Setup, go to App Manager > find the Connected App > Manage.
2. Under "OAuth Policies", set "Permitted Users" to "Admin approved users are pre-authorized".
3. Scroll down to "Profiles" or "Permission Sets" and add the profile or permission set that the CI service user belongs to.
4. Verify with `sf org login jwt ... --username <ci-user>` from a local machine before relying on it in the pipeline.

---

## Gotcha 4: Wrong `--instance-url` Silently Routes to the Wrong Org Type

**What happens:** Using `--instance-url https://login.salesforce.com` when authenticating to a sandbox org (which requires `https://test.salesforce.com`) causes the JWT auth call to succeed against the production login endpoint but fail to find the sandbox user — or, worse, accidentally authenticate to a production org with sandbox credentials if the usernames match. Similarly, using `https://test.salesforce.com` for a production org causes a redirect loop and a timeout.

**When it occurs:** When a pipeline template from a sandbox setup is copy-pasted to a production step (or vice versa) without updating the `--instance-url` flag. This is especially common when teams promote a sandbox pipeline YAML to production via a branch merge without reviewing the instance URL.

**How to avoid:** Use environment-specific Bitbucket repository variables for the instance URL rather than hardcoding it:
```yaml
- sf org login jwt
    --client-id "$SF_CONSUMER_KEY"
    --jwt-key-file /tmp/server.key
    --username "$SF_USERNAME"
    --instance-url "$SF_INSTANCE_URL"   # set per environment
    --alias target-org --set-default
```
Set `SF_INSTANCE_URL` to `https://test.salesforce.com` for sandbox variables and `https://login.salesforce.com` for production variables in Bitbucket.

---

## Gotcha 5: `--test-level` Omission Silently Skips All Tests on Sandbox Deploys

**What happens:** When `--test-level` is omitted from `sf project deploy start` targeting a sandbox, Salesforce defaults to `NoTestRun`. Zero Apex tests execute and zero code coverage is measured. The deploy succeeds with a green build indicator. Teams discover the problem only when the same change is deployed to production, where the platform enforces 75% coverage — and fails.

**When it occurs:** When copying a minimal deploy command from documentation or blog posts that omit the `--test-level` flag, or when a team assumes that tests "just run" as part of every deploy.

**How to avoid:** Always specify `--test-level` explicitly in every deploy command. For sandbox deploys that follow a dedicated test step, `NoTestRun` is acceptable only if the preceding test step enforces the coverage threshold. For production deploys, always use `RunLocalTests`:
```bash
# Sandbox (tests run in prior step)
sf project deploy start --target-org sandbox-org --test-level NoTestRun --wait 30

# Production (tests run as part of deploy)
sf project deploy start --target-org prod-org --test-level RunLocalTests --wait 60
```
