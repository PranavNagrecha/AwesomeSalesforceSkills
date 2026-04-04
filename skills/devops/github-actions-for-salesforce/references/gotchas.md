# Gotchas — GitHub Actions for Salesforce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: JWT Certificate Expiry Has No Platform Warning

**What happens:** The self-signed X.509 certificate uploaded to the Connected App has a finite validity period (default 365 days when generated with the OpenSSL command in the official Salesforce DX Developer Guide). When the certificate expires, `sf org login jwt` returns `INVALID_SESSION_ID` or `invalid_grant: JWT has expired` with no indication that the cause is certificate expiry rather than a credential error. Teams spend hours checking GitHub Secrets, Connected App settings, and user permissions before discovering the certificate date.

**When it occurs:** Exactly 365 days (or whatever `-days N` was specified) after the certificate was generated. Because the cert is uploaded once and never touched again, the expiry date is easy to forget. Pipelines that have been working reliably for months suddenly fail with no code changes.

**How to avoid:**
- Record the certificate expiry date in the repository's CODEOWNERS or a `docs/ci-cert-expiry.txt` file at the time of initial setup.
- Add a scheduled GitHub Actions job that runs weekly and checks the days remaining on the certificate:
  ```yaml
  - name: Check cert expiry
    run: |
      echo "$SF_JWT_SERVER_KEY" > /tmp/server.key
      openssl rsa -in /tmp/server.key -check -noout
      # Use openssl to decode the cert expiry from the Connected App's .crt if stored separately
      rm -f /tmp/server.key
  ```
- Set a personal calendar reminder 30 days before expiry. Rotate: regenerate key pair, upload new `.crt` to Connected App, update GitHub Secret with new `server.key` content.

---

## Gotcha 2: Scratch Org Daily Allocation Limits Block CI Mid-Day

**What happens:** On push-per-PR pipelines that create a scratch org for each run, Developer Edition Dev Hub orgs allow only 6 scratch org creates per 24-hour rolling window. When the limit is hit, `sf org create scratch` fails with `LIMIT_EXCEEDED: You have reached the daily scratch org creation limit.` This error appears to look like an auth or configuration failure in CI log output and is often misdiagnosed.

**When it occurs:** Any active feature team running more than 6 open PRs or re-runs per day. This is a hard Salesforce platform limit per Dev Hub org, not a GitHub Actions limit. Enterprise Edition Dev Hub has higher allocations (40+ active, 200+ daily depending on contract) but Developer Edition is capped at 6.

**How to avoid:**
- Use persistent sandboxes (not scratch orgs) for integration test jobs. Reserve scratch orgs for unit-test isolation jobs and limit one scratch org per feature branch (not per commit).
- Use `--duration-days 1` to minimize active org accumulation and add an `if: always()` delete step so orgs are released immediately after the job.
- Query remaining allocation before creating: `sf limits api display --target-org DevHub | grep DailyScratchOrgs` and fail fast with a meaningful error if the limit is near.
- Track active scratch org count in Dev Hub via `sf org list --json` in a monitoring job.

---

## Gotcha 3: Parallel Jobs Overwrite Each Other's Authenticated Alias

**What happens:** When a GitHub Actions workflow has multiple jobs that run concurrently on the same runner pool and each calls `sf org login jwt --alias target-org`, they write to the shared `~/.sf/` config directory on whatever runner they land on. If two jobs happen to land on the same hosted runner (unlikely with GitHub-hosted runners since each job gets a fresh VM, but common with self-hosted runners), the second login overwrites the alias and the first job's subsequent commands get `No org found for alias target-org`.

**When it occurs:** Self-hosted runner pools where multiple jobs run on the same machine concurrently. Also occurs when a single job has multiple steps that authenticate to different orgs with the same alias name — the second `sf org login jwt --alias target-org` replaces the first.

**How to avoid:**
- Use unique aliases per job or per run: `--alias target-org-${{ github.run_id }}-${{ github.job }}`.
- On self-hosted runners, set `SFDX_USE_GENERIC_UNIX_KEYCHAIN=true` and use per-job working directories to isolate `~/.sf/` state.
- For GitHub-hosted runners, no action is needed — each job gets a fresh ephemeral VM with an empty credential store.

---

## Gotcha 4: `--test-level` Defaults to `NoTestRun` on Sandbox Deploys

**What happens:** When `--test-level` is omitted from `sf project deploy start` targeting a sandbox org, the Salesforce platform defaults to `NoTestRun`. This means zero Apex tests execute and zero coverage is collected during the deploy. The deploy succeeds, masking broken or untested code. Practitioners assume their tests passed when they were never run.

**When it occurs:** Any deploy command to a sandbox that omits `--test-level`. Production orgs enforce a platform-level minimum of 75% org-wide coverage at deploy time, but sandboxes do not enforce coverage. The gap between sandbox behavior and production behavior leads to "works in sandbox, fails in prod" deployment failures.

**How to avoid:** Always specify `--test-level` explicitly in every deploy step. For sandbox validation: `--test-level RunLocalTests`. For production via CI: run `sf apex run test` as a separate step first, enforce coverage in a shell check, then deploy with `--test-level RunLocalTests` or `NoTestRun` (coverage was already validated).

---

## Gotcha 5: Connected App "Pre-Authorize Users" Is a Separate Step from Profile Assignment

**What happens:** A practitioner creates a Connected App, enables JWT Bearer Flow, assigns the Connected App to the CI user's profile or permission set, and then `sf org login jwt` returns `user is not admin approved to access this application`. The profile/permission set assignment allows the user to see the Connected App in the UI but does not grant JWT Bearer Flow access. JWT requires explicit pre-authorization.

**When it occurs:** Initial setup of a new Connected App, or when a new CI user is added without going through the full JWT setup checklist.

**How to avoid:** In Setup > App Manager > [Connected App] > Manage > Edit Policies, set "Permitted Users" to "Admin approved users are pre-authorized". Then add the CI user's profile or a dedicated permission set to the "Profiles" or "Permission Sets" list in the same Manage page. Both steps are required. Verify by checking `sf org display --target-org target-org` returns the expected username after auth.
