# Rotation Runbook — JWT credentials for a CI environment

Goal: replace the private key and certificate a pipeline uses for one org without any moment where the pipeline has no working credential. Every secret value is `[REDACTED]`.

The design uses two apps per environment ("blue" and "green") so the new certificate is proven on an app the pipeline is not yet using. That avoids relying on an app holding two certificates at once, which this runbook does not assume.

## Steps

| # | Step | Proof before moving on |
|---|---|---|
| 1 | Generate a new key pair on a locked-down runner (`umask 077`); the private key never leaves it in plaintext | `head -1 new.key` matches `BEGIN .*PRIVATE KEY` |
| 2 | Create (or reuse) the idle app for this environment — external client app, or connected app for a scratch/sandbox-creating Dev Hub — with JWT Bearer Flow, the `api`, `web`, `refresh_token, offline_access` scopes, and admin-approved pre-authorization for the integration user only | App shows the new certificate uploaded |
| 3 | Log in with the idle app's consumer key and the new key | `sf org login jwt` succeeds; `sf org display --json` returns the integration username |
| 4 | Publish the new key and the idle app's consumer key to the CI secret store, replacing the old values | Next scheduled pipeline run authenticates |
| 5 | Remove the old certificate from the previously active app, or disable that app for the integration user | A login with the old key now fails |
| 6 | Record the new certificate's expiry date and the date of the next rotation | Calendar entry exists |

## Workflow skeleton (GitHub Actions)

```yaml
name: Rotate Salesforce JWT credentials (production)
on:
  schedule:
    - cron: '0 3 1 */3 *'          # quarterly, well inside a 365-day certificate
  workflow_dispatch:
jobs:
  rotate:
    runs-on: ubuntu-latest
    environment: production         # required reviewers
    steps:
      - name: Generate key pair
        run: |
          set -euo pipefail
          umask 077
          openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 \
            -keyout new.key -out new.crt -subj "/CN=ci-prod-$(date +%Y%m%d)"
      - name: Upload new.crt to the idle app (manual gate)
        run: echo "Upload new.crt to the idle app for production, then approve the next step."
      - name: Prove the new key on the idle app
        env:
          SF_CLIENT_ID_IDLE: ${{ secrets.SF_CLIENT_ID_PROD_IDLE }}   # [REDACTED]
          SF_USERNAME:       ${{ vars.SF_USERNAME_PROD }}
        run: |
          set -euo pipefail
          sf org login jwt --client-id "$SF_CLIENT_ID_IDLE" --jwt-key-file new.key \
            --username "$SF_USERNAME" --alias rotation-check
          sf org display --target-org rotation-check --json \
            | python3 -c "import json,sys; print('ok as', json.load(sys.stdin)['result']['username'])"
      - name: Publish and clean up
        env:
          GH_TOKEN: ${{ secrets.GH_ADMIN_TOKEN }}                     # [REDACTED]
        run: |
          set -euo pipefail
          base64 -w0 new.key | gh secret set SF_JWT_KEY_PROD --env production
          rm -f new.key new.crt
```

## Diagnosing a failed proof (step 3) without printing anything

- The consumer key belongs to a different app from the one holding the uploaded certificate.
- The integration user is not pre-authorized for the app (profile or permission set not selected under the app's policies).
- The org requires high assurance sessions for this user, which blocks headless JWT login.
- The certificate uploaded is not the pair of the key used.

Each of these is checked by looking at Setup or at the file header, never by echoing the key or the token.
