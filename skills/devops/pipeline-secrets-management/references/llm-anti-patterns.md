# LLM Anti-Patterns — Pipeline Secrets Management

Scope: how a CI job gets an authenticated Salesforce session without leaving a credential
behind. Pipeline structure and job design belong to `devops/github-actions-for-salesforce`
and `devops/gitlab-ci-for-salesforce`; this file is only about the credential.

All secret values below are `[REDACTED]`. Never print a real one, in a skill or a log.

## Anti-Pattern 1: Authorising with an SFDX auth URL

The generated default, because it is one line and works immediately. The Salesforce DX
Developer Guide does document `sf org login sfdx-url` for CI, and describes the URL as
containing all the information needed to authorize the org. That is the problem: the value
alone is the credential, so anyone who can read it can authorize the org from anywhere, and
nothing about it is tied to a certificate you can swap.

**Wrong** — a permanent org credential in an environment variable:

```yaml
- name: Authenticate
  env:
    SFDX_AUTH_URL: ${{ secrets.SFDX_AUTH_URL }}   # force://[REDACTED]
  run: |
    echo "$SFDX_AUTH_URL" > auth.txt
    sf org login sfdx-url --sfdx-url-file auth.txt --alias prod
    # auth.txt is still in the workspace, and the workspace is often archived
```

**Right** — the JWT bearer flow, where the long-lived artefact is a private key you control
and can revoke by replacing one certificate on the app:

```yaml
- name: Authenticate to production
  env:
    SF_JWT_KEY:   ${{ secrets.SF_JWT_KEY_PROD }}      # base64 PEM, [REDACTED]
    SF_CLIENT_ID: ${{ secrets.SF_CLIENT_ID_PROD }}    # consumer key, [REDACTED]
    SF_USERNAME:  ${{ vars.SF_USERNAME_PROD }}        # not a secret
  run: |
    set -euo pipefail
    umask 077
    KEYFILE="$(mktemp)"
    trap 'rm -f "$KEYFILE"' EXIT              # removed even if the step fails
    printf '%s' "$SF_JWT_KEY" | base64 -d > "$KEYFILE"
    sf org login jwt \
      --client-id "$SF_CLIENT_ID" \
      --jwt-key-file "$KEYFILE" \
      --username "$SF_USERNAME" \
      --alias prod
```

The `trap ... EXIT` matters more than it looks: without it a failing deploy leaves the
decrypted private key on the runner's disk, and self-hosted runners are reused.

Source: Authorize an Org Using the JWT Flow — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_jwt_flow.htm

## Anti-Pattern 2: Printing credentials to "check the connection"

Older material says `sf org display --verbose` shows the auth URL, so assistants either add it
as a debug step or reach for its replacement. Current CLI behaviour: `sf org display` and
`sf org list` hide secrets, and the dedicated `sf org auth show-access-token`,
`show-sfdx-auth-url`, and `show-user-password` commands print them. With `--json` or
`--no-prompt` they skip the confirmation prompt, which is exactly how they would run in CI;
`SF_TEMP_SHOW_SECRETS=true` brings the old `sf org display` output back. CI logs are far more
widely readable than the secret store, and provider masking only covers declared secrets.

❌ `sf org auth show-access-token --target-org prod --json` or `SF_TEMP_SHOW_SECRETS=true` in a pipeline step.
✅ Assert connectivity without printing a credential:

```yaml
- name: Verify authentication
  run: |
    sf org display --target-org prod --json \
      | python3 -c "import json,sys; d=json.load(sys.stdin)['result']; \
                    print('connected as', d['username'], 'to', d['instanceUrl'])"
```

If a human genuinely needs a token, that is a local action on their own machine, never a
pipeline step. Treat any generated workflow containing `org auth show-` as a finding.

## Anti-Pattern 3: One Connected App and one integration user for every environment

Assistants consolidate because the setup work is tedious and identical. The result is that
the credential which deploys to a scratch org is the credential that deploys to production —
so a compromised PR-validation runner is a production compromise, and revoking anything
takes every pipeline down at once.

❌ `SF_CLIENT_ID` and `SF_JWT_KEY` as two repository-wide secrets used by all jobs.
✅ One app, one certificate and one integration user per environment, with the production
pair scoped to a protected environment so a fork or a feature branch cannot reach it:

```yaml
jobs:
  deploy-prod:
    environment: production        # required reviewers; secrets scoped to this environment
    steps:
      - name: Authenticate
        env:
          SF_JWT_KEY:   ${{ secrets.SF_JWT_KEY_PROD }}      # [REDACTED]
          SF_CLIENT_ID: ${{ secrets.SF_CLIENT_ID_PROD }}    # [REDACTED]
        run: ...
```

Give the integration user a permission set with only what the pipeline needs. "System
Administrator because it was quicker" turns a leaked key into an org takeover rather than a
deployment.

## Anti-Pattern 4: Exposing secrets to a fork-triggered workflow

The failure that is invisible in review, because the YAML looks normal. A workflow that runs
on `pull_request_target`, or a `pull_request` workflow that checks out the PR head and then
runs code from it, executes an outside contributor's script with the repository's secrets in
scope. The exfiltration is one line in a build script.

❌ `on: pull_request_target` on a job that checks out `github.event.pull_request.head.sha`
and runs project scripts.
✅ Validation from an untrusted branch runs with **no** org credential at all — lint, static
analysis and unit-testable logic only — and anything needing an org runs after merge, or in
a manually approved environment. If a validation deploy must run pre-merge, gate it behind a
protected environment with required reviewers so a human authorises the credential's use.

## Anti-Pattern 5: Treating the JWT certificate as install-and-forget

The private key does not expire, but the certificate paired with it does. Because the
pipeline works right up until the moment it does not, there is no gradual signal — the
failure lands as a broken release on the day of the release.

❌ Generate a self-signed certificate with a multi-year validity, upload it, move on.
✅ Two independent controls. Track the certificate's expiry date and alert with enough lead
time to run the swap, and put the rotation itself on a schedule rather than on the expiry.
Rotation means proving the new key before the old one stops working. `rotation-runbook.md`
does that with a second ("idle") app per environment: upload the new certificate there, log
in with it, switch the CI secrets, then retire the old certificate. A failed rotation is then
a retry instead of an outage, without assuming an app can hold two certificates at once.

## Anti-Pattern 6: Echoing the failure

When authentication fails, generated debugging prints the inputs. `set -x` in the auth step
expands the whole command including the key path and any inline value; `cat "$KEYFILE"`
prints the private key into a log that is retained and searchable.

❌ `set -x` in a step that handles the key, or `echo "$SF_JWT_KEY"` to "check it decoded".
✅ Keep `set -x` out of any step touching the secret, and diagnose from the shape of the
value rather than the value:

```yaml
- name: Diagnose key format without printing it
  run: |
    printf '%s' "$SF_JWT_KEY" | base64 -d > "$KEYFILE"
    head -1 "$KEYFILE" | grep -q 'BEGIN .*PRIVATE KEY' \
      && echo "key decoded, PEM header present" \
      || { echo "key did not decode to a PEM private key"; exit 1; }
```

Most JWT auth failures are one of three things, none of which need the key printed: the
consumer key does not match the app, the integration user is not pre-authorised for the
app, or the certificate on the app is not the pair of this key. A fourth is environmental: an
org that requires high assurance sessions blocks headless JWT login entirely.

## Anti-Pattern 7: No detection, so a leak is found by the person who exploits it

Prevention is the only control most generated pipelines have, and prevention fails. Nothing
in the repo notices a committed `force://` URL, a `.ecaGlblOauth` file or a PEM block, so the
window between a leak and its discovery is unbounded.

❌ Rely on review to catch a credential in a diff.
✅ Turn on the provider's secret scanning with push protection, and add a local hook that
refuses the commit before it reaches the remote — the pattern is distinctive enough to match
cheaply:

```bash
#!/usr/bin/env bash
# .githooks/pre-commit — block obvious Salesforce credential material
if git diff --cached -U0 | grep -qE '(force://|BEGIN [A-Z ]*PRIVATE KEY)'; then
  echo "refusing commit: looks like an sfdx auth URL or a private key" >&2
  exit 1
fi
if git diff --cached --name-only | grep -qE '(^|/)\.sfdx/|(^|/)\.sf/'; then
  echo "refusing commit: local CLI state directory (belongs in .gitignore)" >&2
  exit 1
fi
```

Treat a leak as compromise, not as a mistake to delete. Rewriting history does not revoke
anything — the response is to replace the certificate and rotate the key, then clean up.
