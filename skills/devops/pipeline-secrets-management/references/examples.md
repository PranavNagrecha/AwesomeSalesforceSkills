# Examples — Pipeline Secrets Management

Every secret value in this file is `[REDACTED]`. The pipeline shape is deliberately minimal
— job structure and matrix design belong to `devops/github-actions-for-salesforce` and
`devops/gitlab-ci-for-salesforce`.

## Example 1: Replacing an auth-URL deploy with the JWT bearer flow

**Context:** A GitHub Actions workflow deploying to production, inherited from a proof of
concept. It authenticated with an SFDX auth URL held in a repository secret.

**Problem:** The auth URL embeds a refresh token, so the secret was a permanent, portable
production credential — usable from anywhere by anyone who could read it, with nothing to
expire and no way to revoke it short of resetting the user. It had also been copied into a
runbook and a support ticket, because it looked like configuration rather than a key.

**Solution:** A JWT bearer flow with a per-environment connected app and integration user.
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
store, paired with a certificate on a connected app that you can replace to revoke access.
The decrypted key exists on the runner only inside one step, `umask 077` keeps it
unreadable to other users on a shared runner, and `trap ... EXIT` removes it even when the
deploy fails — which is exactly when a naive `rm` at the end of the script never runs.

**The step that is missing on purpose:** there is no `sf org display --verbose` anywhere.
`--verbose` prints the SFDX auth URL, and it prints it as ordinary output that the
provider's secret masking does not cover, because the CLI derived the value rather than
receiving it as a declared secret. A "just checking the connection" step is how orgs leak.

**Why `RunLocalTests`:** it is the documented default for production deployments containing
Apex classes or triggers, and it runs every test in the org except those from installed
managed and unlocked packages. Choosing `NoTestRun` to make the pipeline faster is not
available for production, and `RunAllTestsInOrg` adds managed-package tests you do not own
and cannot fix.

---

## Example 2: Scheduled rotation, ordered so a failure is recoverable

**Context:** The certificate on the production connected app was self-signed with a long
validity, created once by someone who had since left. Nothing tracked it.

**Problem:** A JWT certificate produces no gradual signal. The pipeline works, and then on
one specific morning every deployment fails with an authentication error, on a date nobody
had in a calendar. The first attempt at a fix made it worse — the new certificate was
uploaded before the new key was proven, which broke deploys with no way back.

**Solution:** Rotate on a schedule rather than on expiry, and order the steps so the old
credential still works until the new one is proven.

```yaml
name: Rotate Salesforce JWT credentials
on:
  schedule:
    - cron: '0 3 1 */3 *'      # quarterly, well inside any certificate validity
  workflow_dispatch:

jobs:
  rotate:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Generate a new key pair
        run: |
          set -euo pipefail
          umask 077
          openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 \
            -keyout new.key -out new.crt \
            -subj "/CN=ci-prod-$(date +%Y%m%d)"
          # new.key is never echoed and never leaves this runner in plaintext

      - name: Upload the new certificate to the connected app
        run: |
          echo "Upload new.crt to the connected app's digital signature field."
          echo "Do NOT remove the existing certificate yet."

      - name: Prove the new key works BEFORE retiring the old one
        env:
          SF_CLIENT_ID: ${{ secrets.SF_CLIENT_ID_PROD }}    # [REDACTED]
          SF_USERNAME:  ${{ vars.SF_USERNAME_PROD }}
        run: |
          set -euo pipefail
          sf org login jwt \
            --client-id "$SF_CLIENT_ID" \
            --jwt-key-file new.key \
            --username "$SF_USERNAME" \
            --alias rotation-check
          sf org display --target-org rotation-check --json > /dev/null
          echo "new key authenticates"

      - name: Publish the new key to the secret store
        env:
          GH_TOKEN: ${{ secrets.GH_ADMIN_TOKEN }}           # [REDACTED]
        run: |
          base64 -w0 new.key | gh secret set SF_JWT_KEY_PROD --env production
          rm -f new.key new.crt

      - name: Retire the old certificate
        run: echo "Only now remove the previous certificate from the connected app."
```

**Why it works:** the ordering is the whole design. Upload, prove, publish, retire — at
every point before the last step the previous credential is still valid, so a failure is a
retry rather than an outage. Rotating quarterly means the expiry date stops being the thing
that triggers the work, which is what turns this from an incident into a routine job.

**Diagnosing a failure at the "prove" step without printing anything:** JWT authentication
fails for a small number of reasons, and none of them require the key in a log. The consumer
key does not belong to the app holding the certificate; the integration user is not
pre-authorised for the app; or the uploaded certificate is not the pair of this key. Check
the shape of the decoded value, not its content:

```bash
head -1 new.key | grep -q 'BEGIN .*PRIVATE KEY' \
  && echo "PEM header present" \
  || { echo "not a PEM private key"; exit 1; }
```

**What rotation does not fix:** if the old key ever leaked, rotating is the response, not
the prevention. Add push protection and a local hook so a `force://` URL or a PEM block
cannot reach the remote in the first place — and treat any leak as compromise, because
rewriting git history revokes nothing.
