# Examples — Pipeline Secrets Management

Every secret value in this file is `[REDACTED]`. The pipeline shape is deliberately minimal
— job structure and matrix design belong to `devops/github-actions-for-salesforce` and
`devops/gitlab-ci-for-salesforce`.

## Example 1: Replacing an auth-URL deploy with the JWT bearer flow

**Context:** A GitHub Actions workflow deploying to production, inherited from a proof of
concept. It authenticated with an SFDX auth URL held in a repository secret.

**Problem:** An SFDX authorization URL contains all the information needed to authorize the
org, so the secret was a portable production credential — usable from anywhere by anyone who
could read it. It had also been copied into a runbook and a support ticket, because it looked
like configuration rather than a key.

**Solution:** A JWT bearer flow with a per-environment external client app and integration user.
The private key never leaves the secret store except as a temporary file that is removed
whether the job succeeds or fails.

```yaml
name: Deploy to production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production          # required reviewers; scopes the secrets to this job
    steps:
      - uses: actions/checkout@v4

      - name: Install Salesforce CLI
        run: npm install --global @salesforce/cli@2   # pinned major; see anti-pattern 5

      - name: Authenticate
        env:
          SF_JWT_KEY:   ${{ secrets.SF_JWT_KEY_PROD }}      # base64 PEM  — [REDACTED]
          SF_CLIENT_ID: ${{ secrets.SF_CLIENT_ID_PROD }}    # consumer key — [REDACTED]
          SF_USERNAME:  ${{ vars.SF_USERNAME_PROD }}        # not a secret
        run: |
          set -euo pipefail          # note: no `set -x` in a step that touches the key
          umask 077
          KEYFILE="$(mktemp)"
          trap 'rm -f "$KEYFILE"' EXIT
          printf '%s' "$SF_JWT_KEY" | base64 -d > "$KEYFILE"
          sf org login jwt \
            --client-id "$SF_CLIENT_ID" \
            --jwt-key-file "$KEYFILE" \
            --username "$SF_USERNAME" \
            --alias prod

      - name: Confirm the session without printing a credential
        run: |
          sf org display --target-org prod --json \
            | python3 -c "import json,sys; r=json.load(sys.stdin)['result']; \
                          print('connected as', r['username'])"

      - name: Validate before deploying
        run: |
          sf project deploy validate \
            --target-org prod \
            --source-dir force-app \
            --test-level RunLocalTests \
            --wait 60

      - name: Deploy
        run: |
          sf project deploy start \
            --target-org prod \
            --source-dir force-app \
            --test-level RunLocalTests \
            --wait 60
```

**Why it works:** the long-lived artefact is now a private key that stays in the secret
store, paired with a certificate on an external client app that you can replace to revoke access.
The decrypted key exists on the runner only inside one step, `umask 077` keeps it
unreadable to other users on a shared runner, and `trap ... EXIT` removes it even when the
deploy fails — which is exactly when a naive `rm` at the end of the script never runs.

**The step that is missing on purpose:** there is no `sf org auth show-sfdx-auth-url` or
`sf org auth show-access-token` anywhere, and nothing sets `SF_TEMP_SHOW_SECRETS`. Standard
commands such as `sf org display` now hide secrets; the `show-*` commands exist to print them,
and with `--json` they skip the confirmation prompt — which is how they would run in CI. A
"just checking the connection" step built on them is how orgs leak.

**Why `RunLocalTests`:** it is the documented default for production deployments containing
Apex classes or triggers, and it runs every test in the org except those from installed
managed and unlocked packages. Choosing `NoTestRun` to make the pipeline faster is not
available for production, and `RunAllTestsInOrg` adds managed-package tests you do not own
and cannot fix.

---

## Example 2: Rotating without a window where nothing works

The rotation workflow and its ordering live in `rotation-runbook.md`. The one check worth
copying into any pipeline that handles keys is the shape test, which proves a decoded secret
is a PEM private key without printing it:

```bash
head -1 "$KEYFILE" | grep -q 'BEGIN .*PRIVATE KEY' \
  && echo "PEM header present" \
  || { echo "not a PEM private key"; exit 1; }
```

**What rotation does not fix:** if the old key ever leaked, rotating is the response, not
the prevention. Run the checker on every pull request and enable the CI provider's secret
scanning so a `force://` URL or a PEM block cannot reach the remote in the first place — and
treat any leak as compromise, because rewriting repository history revokes nothing.
