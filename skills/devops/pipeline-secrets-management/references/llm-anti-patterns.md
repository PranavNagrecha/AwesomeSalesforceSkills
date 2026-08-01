# LLM Anti-Patterns — Pipeline Secrets Management

Scope: how a CI job gets an authenticated Salesforce session without leaving a credential
behind. Pipeline structure and job design belong to `devops/github-actions-for-salesforce`
and `devops/gitlab-ci-for-salesforce`; this file is only about the credential.

All secret values below are `[REDACTED]`. Never print a real one, in a skill or a log.

## Anti-Pattern 1: Authorising with an SFDX auth URL

The generated default, because it is one line and works immediately. A `force://` auth URL
embeds a **refresh token**. Anyone who can read the value can mint access tokens for that
org indefinitely, from anywhere, with no further interaction. It is not a password — it is
strictly worse than a password, because it does not expire on a schedule anybody watches.

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
and can revoke by replacing one certificate:

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

## Anti-Pattern 2: Running `sf org display --verbose` to "check the connection"

The single most effective way to leak an org. `--verbose` prints the **Sfdx Auth Url**, and
CI logs are far more widely readable than the secret store — visible to anyone with repo
read on many providers, retained for months, and frequently forwarded into chat. The masking
that hides `${{ secrets.* }}` does not apply, because this value was never a declared
secret; the CLI derived it.

❌ `sf org display --target-org prod --verbose` as a debug step.
✅ Assert connectivity without printing a credential:

```yaml
- name: Verify authentication
  run: |
    sf org display --target-org prod --json \
      | python3 -c "import json,sys; d=json.load(sys.stdin)['result']; \
                    print('connected as', d['username'], 'to', d['instanceUrl'])"
```

If a human genuinely needs `--verbose`, that is a local action on their own machine, never a
pipeline step. Treat any generated workflow containing `--verbose` as a finding.

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
Rotation means: generate a new key pair, upload the new certificate to the connected app,
update the CI secret, confirm a real login with the new key, and only then remove the old
certificate. Doing it in that order means a failed rotation is recoverable instead of an
outage.

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
consumer key does not match the connected app, the integration user is not pre-authorised
for the app, or the certificate on the app is not the pair of this key.

## Anti-Pattern 7: No detection, so a leak is found by the person who exploits it

Prevention is the only control most generated pipelines have, and prevention fails. Nothing
in the repo notices a committed `force://` URL, a `.sfdx/` directory or a PEM block, so the
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
  echo "refusing commit: CLI auth state directory" >&2
  exit 1
fi
```

Treat a leak as compromise, not as a mistake to delete. Rewriting history does not revoke
anything — the response is to replace the certificate and rotate the key, then clean up.
