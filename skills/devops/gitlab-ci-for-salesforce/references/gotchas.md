# Gotchas — GitLab CI for Salesforce

Non-obvious Salesforce platform behaviors and GitLab CI quirks that cause real production problems in this domain.

## Gotcha 1: GitLab Masked Variables Reject Multi-Line Values — Private Keys Cannot Be Stored Unencoded

**What happens:** When you try to create a GitLab CI/CD variable containing the raw contents of `server.key` (a PEM-format private key) with the "Masked" toggle enabled, GitLab rejects the save with an error like "Variable value is not valid — masked variables must not contain multi-line values or special characters." The masking system requires single-line values with no `$`, `[`, `]`, or newline characters. A standard RSA private key fails all of these conditions.

**When it occurs:** Any time a practitioner follows documentation or tutorials that say "store your private key as a GitLab CI variable" without specifying base64 encoding. This is a GitLab-specific constraint that does not exist in GitHub Actions (which uses a different secrets mechanism).

**How to avoid:** Base64-encode the private key before storing it, then decode it in the job script:

```bash
# On developer machine — encode and copy output into the GitLab variable
base64 -w 0 server.key
# -w 0 produces a single line (no line wraps) which GitLab can mask

# In .gitlab-ci.yml job script — decode before use
echo "$SF_JWT_SERVER_KEY" | base64 -d > /tmp/server.key
```

The base64-encoded single-line value passes GitLab's masking validation. The decoded temp file is consumed by `sf org login jwt --jwt-key-file /tmp/server.key` at runtime and deleted in `after_script:`.

---

## Gotcha 2: JWT Certificate Expiry Has No Platform Notification

**What happens:** Salesforce sends no email, warning, or platform alert when a JWT certificate uploaded to a Connected App is approaching or has passed its expiry date. On the expiry date, every CI job that uses `sf org login jwt` returns `INVALID_SESSION_ID` with no contextual message about certificate expiry. The error looks identical to a wrong password or misconfigured Connected App, causing teams to debug the wrong thing.

**When it occurs:** 365 days (or whatever `-days N` was used with OpenSSL) after the certificate was generated and uploaded. Active pipelines that have been running correctly for months will fail suddenly overnight with no code changes.

**How to avoid:**
- When generating the cert, record the expiry date immediately: `openssl x509 -in server.crt -noout -dates`
- Set a team calendar reminder 30 days before the expiry date
- Use `-days 730` to generate a two-year cert and reduce rotation frequency
- Add a scheduled GitLab CI job to check cert expiry programmatically (parse `notAfter` from the cert and fail if within 30 days)
- When `INVALID_SESSION_ID` appears with no code changes, check cert expiry first before investigating credentials

---

## Gotcha 3: `only:` and `except:` Branch Pattern Matching Is Unreliable — Use `rules:` Instead

**What happens:** The older GitLab CI `only:` syntax with regex branch patterns behaves inconsistently. For example, `only: [/^feature\/.*/]` is supposed to match branches like `feature/my-work` but in some GitLab versions or runner configurations it matches against the full ref string (`refs/heads/feature/my-work`) rather than the branch name alone, causing the pattern to fail silently. Jobs either never trigger or trigger when they should not. Additionally, `only:` does not support the `merge_request_event` pipeline source distinction, making it impossible to correctly differentiate MR pipelines from push pipelines.

**When it occurs:** When a `.gitlab-ci.yml` uses `only: branches` or `only: [/regex/]` instead of `rules:`. This is especially problematic in repos that mix MR-triggered and push-triggered pipelines for the same branch.

**How to avoid:** Migrate all branch conditions to the `rules:` syntax, which reliably matches against `$CI_COMMIT_BRANCH` and `$CI_PIPELINE_SOURCE`:

```yaml
# Old — unreliable
only:
  - /^feature\/.*/

# Correct — use rules:
rules:
  - if: '$CI_COMMIT_BRANCH =~ /^feature\//'
  - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```

The `rules:` syntax also supports `when: manual`, `allow_failure:`, and variable-based conditions — none of which `only:` supports.

---

## Gotcha 4: Production Variables Marked "Protected" Are Invisible to Non-Protected Branch Jobs

**What happens:** A GitLab CI/CD variable marked as "Protected" is only injected into jobs running on protected branches (typically `main` and `production`). If a developer tests the production deploy job from a feature branch or `develop`, the job fails with `sf org login jwt: client-id is required` or a similar error — not because the variable is wrong, but because it is not injected at all. The job sees the variable name as empty.

**When it occurs:** When a practitioner marks production credentials as "Protected" (correct for security) but then tries to test or debug the production job from a non-protected branch. Also occurs when a new branch is not added to the protected branches list in GitLab's repository settings.

**How to avoid:** This is expected and correct behavior — protected variables are a security feature, not a bug. The correct response is to confirm the intent:
- Production secrets should be Protected + Masked
- Test the production deploy job only from protected branches
- For pipeline debugging, create a separate test job with a dummy variable to verify job structure without real credentials
- Document in the team runbook that only `main` can trigger the real production deploy (the `when: manual` gate reinforces this)

---

## Gotcha 5: Connected App Pre-Authorization Is Required and Separate from Profile/Permission Set Assignment

**What happens:** A practitioner creates a Connected App, assigns it to a profile, assigns the profile to the CI service user, uploads a certificate, and sets "Permitted Users: Admin approved users are pre-authorized." The JWT auth still returns `user is not pre-authorized` or a similar error.

**When it occurs:** The "Admin approved users are pre-authorized" setting in the Connected App's OAuth Policies requires that the specific user (or their profile) be explicitly listed under "Manage Connected Apps > Pre-Authorize Users" (the separate "Pre-Authorize Users" action in App Manager). Assigning the Connected App to a profile via the profile's "Connected App Access" does NOT automatically pre-authorize the user for JWT. These are two separate configuration steps that Salesforce documentation does not make obviously distinct.

**How to avoid:**
1. In Setup > App Manager, find the Connected App
2. Click the dropdown arrow next to the app name > "Manage"
3. Click "Edit Policies" — verify "Permitted Users" is set to "Admin approved users are pre-authorized"
4. Return to the Manage page and look for a "Pre-Authorize Users" related list or button
5. Add the CI service user's profile or the specific user to the pre-authorized list
6. Save. Test JWT auth again.

If `sf org login jwt` still fails after pre-authorization, confirm the `--username` flag matches exactly the username in the target org (case-sensitive) and the `--instance-url` matches the org type.
