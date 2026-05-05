# Examples — Connected App Troubleshooting

## Example 1 — Server-to-server integration dies on day 2

**Symptom.** Heroku worker authenticates Monday via Web Server
flow; success. Tuesday morning, every API call fails with
`invalid_grant`.

**Diagnosis.** Login History (Setup → Login History, filter by the
integration user) shows Monday's logins as Success. Tuesday's
shows "Failed: invalid_grant". The Connected App's Refresh Token
Policy is "Immediately expire refresh token after first use" —
default in older orgs.

**Fix.** Setup → Apps → Connected Apps → edit the app → OAuth
Policies → Refresh Token Policy = "Refresh token is valid until
revoked." Re-authorize the integration user (initial consent
flow). The new refresh token is captured under the new policy.

**Verification.** Wait 24 hours; verify Login History shows
continued Success.

---

## Example 2 — `invalid_client_id` on a freshly-deployed app

**Symptom.** New Connected App deployed via metadata to
production. Integration starts; first call returns
`invalid_client_id`.

**Diagnosis.** Consumer Key in the integration config doesn't
match the new Connected App's actual key. Metadata deploy creates
a new Connected App record with a new key; the integration was
configured with the sandbox's key.

**Fix.** Setup → Apps → Connected Apps → click the app → click
Manage Consumer Details → copy the Consumer Key. Update the
integration's config. Restart.

---

## Example 3 — Cloud Lambda hits IP restriction

**Symptom.** AWS Lambda calling Salesforce REST API gets
`IP_RESTRICTED`. Each invocation comes from a different AWS IP.

**Diagnosis.** Connected App IP Relaxation = "Enforce IP
restrictions". Integration user's profile has a tight IP range
that doesn't include AWS's IP pool.

**Fix.** Two reasonable approaches:

- **Connected App level:** IP Relaxation = "Relax IP restrictions".
  Compensate by tightening the integration user's permissions
  (only what's needed) and rotating the credential.
- **Profile level:** Add AWS Lambda's IP ranges to the user's
  Login IP Range. Practical only for Lambdas in fixed VPCs with
  known NAT IPs; Lambda's default outbound IPs are too dynamic.

For most cloud integrations, "Relax IP restrictions" + tight user
permissions is the right trade.

---

## Example 4 — JWT Bearer first-call success, all subsequent fail

**Symptom.** JWT Bearer flow integration works for one call;
subsequent calls (with regenerated JWTs) fail with `invalid_grant`.

**Diagnosis.** Refresh tokens aren't part of JWT Bearer flow —
each call signs a fresh JWT. The "subsequent calls fail" pattern
points at:

- **Certificate expired** — check expiry date.
- **Wrong certificate** — Connected App keyed to certA, client
  signing with certB.
- **`sub` claim mismatch** — must be the user's Username, not
  Email.
- **`aud` claim wrong** — must be `https://login.salesforce.com`
  (or test login URL for sandbox).

Test with a fresh JWT generated manually using a known-good cert
to isolate variables.

---

## Example 5 — User can't approve a Connected App

**Symptom.** User tries to authorize a Connected App via Web
Server flow; gets a Salesforce login screen, signs in, and
returns to the integration with a "OAUTH_APP_BLOCKED" error.

**Diagnosis.** Connected App's Permitted Users = "Admin approved
users are pre-authorized" + the user is not assigned via profile
or permission set.

**Fix.** Setup → Permission Sets (or Profiles) → edit the user's
permset → "Connected App Access" → check the Connected App.
Re-attempt the OAuth flow.

---

## Anti-Pattern: Hardcoding credentials in the integration

**What it looks like.** Integration code with
`consumer_key`/`consumer_secret`/`refresh_token` hardcoded.

**What goes wrong.** Credentials in source control. Rotation
requires code change + deploy. If the secret leaks, you can't
rotate it without immediate redeploy.

**Correct.** Named Credentials (Salesforce-side) or environment
variables / secret store (client-side). Rotation is a config
change.
