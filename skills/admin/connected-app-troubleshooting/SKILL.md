---
name: connected-app-troubleshooting
description: "Troubleshooting Connected App OAuth flows — IP relaxation vs IP restriction, refresh token policy traps (default kills the connection on first refresh), session-revocation semantics, the OAuth error-code catalog (`invalid_grant`, `invalid_client_id`, `unsupported_grant_type`), per-user vs admin-pre-approved flows, and the user-policy check (Connected App must be assigned to the user via profile / permset). Covers the Login History debug trail. NOT for designing the OAuth flow itself — use integration/oauth-flows-and-connected-apps. NOT for a SAML / SSO login failure — use security/sso-saml-troubleshooting. Trigger keywords: 'invalid_grant', 'OAUTH_APP_BLOCKED', 'redirect_uri_mismatch', 'LoginHistory Status', 'LoginSubType', 'OauthRefreshToken', 'ForwardedForIp', 'SetupAuditTrail connected app', 'refreshTokenPolicy zero', 'isSecretRequiredForRefreshToken', 'works once then fails', 'diagnosis record'."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "connected app refresh token revoked first use"
  - "oauth invalid_grant connected app salesforce"
  - "connected app ip relaxation security policy"
  - "connected app user profile permission set assignment"
  - "connected app login history debug oauth flow"
  - "connected app session revocation api token"
  - "integration worked yesterday and now returns invalid_grant"
  - "which login history status means the connected app blocked the user"
  - "trace an oauth error string back to the connected app setting that caused it"
  - "prove which setup change broke the integration authentication"
  - "reproduce a connected app oauth failure safely in a sandbox"
  - "client only shows a generic oauth error and I need the salesforce side evidence"
tags:
  - connected-app
  - oauth
  - refresh-token
  - ip-relaxation
  - login-history
  - session-revocation
inputs:
  - "OAuth error code or symptom (silent failure, invalid_grant, popup-blocked, etc.)"
  - "Flow being used: Web Server, JWT Bearer, User Agent, Username-Password, Device, Refresh Token"
  - "User context: known user, integration user, anonymous Community user"
  - "Whether the Connected App is admin-pre-approved or self-authorized"
outputs:
  - "Diagnosis: which step in the OAuth dance is failing"
  - "Fix: settings change, user assignment, IP relaxation, refresh-token policy"
  - "Verification path via Login History"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Connected App Troubleshooting

OAuth via Connected Apps has a consistent set of failure modes
that admins hit repeatedly: refresh tokens silently revoked,
users not assigned to the app, IP restrictions blocking the
caller, callback URL mismatches, and the error catalog being
opaque ("invalid_grant" can mean five different things).

This skill is the diagnostic playbook. It assumes a Connected App
exists and an OAuth flow is failing; the input is the error
symptom, the output is the next action.

What this skill is NOT. Designing the OAuth architecture (which
flow to pick, JWT setup, certificate management) is
`integration/oauth-flows-and-connected-apps`, and authoring the app
file itself is `admin/connected-apps-and-auth`. SAML / SSO debugging
is `security/sso-saml-troubleshooting`. This skill is for the
"OAuth-via-Connected-App is failing; what now" moment.

---

## Before Starting

- **Capture the error code verbatim.** `invalid_grant` vs
  `invalid_client_id` vs `unsupported_grant_type` mean different
  things.
- **Identify the flow.** Web Server, JWT Bearer, User Agent,
  Device, Refresh Token, Username-Password (deprecated for
  most uses).
- **Identify the user.** Known interactive user, dedicated
  integration user, Connected App pre-approved user.
- **Pull Login History.** Setup → Login History filtered by the
  user / time window. The Salesforce side captures every login
  attempt with status code; many failures show here even when the
  client only sees a generic OAuth error.

---

## Questions to Ask Before Configuring

Ask these before changing a single Connected App field. A failing OAuth flow has one true cause and
four plausible ones; every question below eliminates a branch of the decision table using evidence
that already exists in the org.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Paste the response body, not your summary of it." | The token endpoint's `error` string and the HTTP status are different signals. REST API documents 401 as "The session ID or OAuth token used has expired or is invalid", and 403 as a refusal to check permissions against | The row of the runbook table to start on, and whether this is an auth failure or a post-auth authorization failure |
| "Which grant is failing — the first authorization, or a later refresh?" | `LoginSubType` separates `OauthWebServer` from `OauthRefreshToken`, so Salesforce already recorded which half broke | Whether to inspect `oauthConfig` (initial exchange) or `oauthPolicy` (renewal) — they are different fields |
| "Did this ever work, and when did it last succeed?" | A working-then-broken integration points at a policy change or a token lifetime, not at configuration; a never-worked one points at pre-authorization or callback URL | The `SetupAuditTrail` window to search and whether a `LoginHistory` success row exists to compare against |
| "Who is the authenticating user, by Id?" | `UserId` is one of only twelve filterable `LoginHistory` fields, so it is the anchor of every evidence query | A query that compiles, instead of one rejected on `WHERE Application` or `WHERE Status` |
| "Can the caller enumerate its egress IPs, and does anything proxy the request?" | `ipRelaxation` `ENFORCE` is evaluated against the org's IP restrictions, and `SourceIp` records the first proxy rather than the origin | Whether the IP branch is even testable from Salesforce-side evidence (gotcha 12) |
| "Who will run the verification query, and do they hold Customize Application?" | `OauthToken` shows an under-privileged caller only their own rows, so a clean result can be an artefact of the reviewer's permissions | A named runner for the evidence step, so an empty result means something |
| "Is there a sandbox with the same policy values, and has My Domain been deployed in it?" | The reproduction is only valid if the login host and the policy block match; callback URLs are host-specific | A safe place to test the fix before touching the production app |

What a proper configuration adds over just doing it: the fix is attached to a written diagnosis
record — symptom, verbatim error, the evidence rows that ruled the other causes out, and a
root-cause category — so the next person who sees `invalid_grant` on this app does not restart the
same five-branch search from zero.

---

## Core Concepts

### The OAuth error catalog

UNVERIFIED (2026-09-04): the token-endpoint `error` strings below are not
documented in this skill's source set — the REST API Developer Guide covers
the HTTP layer (401 as an expired or invalid session/OAuth token, 403 as a
refusal to check permissions against) but not the OAuth vocabulary. Treat each
string as a hint and confirm the diagnosis with the evidence columns in
`references/metadata-examples.md` § 1, which are grounded.

| Error code | Common cause | Fix |
|---|---|---|
| `invalid_grant` | Refresh token revoked / expired / not issued for this client | Verify Refresh Token Policy on the Connected App; re-authorize the user |
| `invalid_client_id` | Wrong Consumer Key | Check the Consumer Key matches the Connected App in the right org |
| `invalid_client_credentials` | Wrong Consumer Secret | Reset / fetch the secret in Setup |
| `unsupported_grant_type` | Connected App's "Permitted Users" or "OAuth Policies" don't permit this flow | Edit the Connected App; ensure the flow's grant type is enabled |
| `redirect_uri_mismatch` | Callback URL in app doesn't match the request's redirect_uri | Update the Connected App's callback URL list |
| `inactive_user` | User is deactivated | Activate the user OR use a different user |
| `IP_RESTRICTED` | Connected App's IP relaxation = "Enforce IP restrictions" + caller IP not on user's profile login range | Either: relax to "Relax IP restrictions for activated devices", OR add IP to user's profile range |
| `error=login_required` (silent) | Session expired but Connected App is configured for SSO bypass | User must re-authenticate; auto-refresh isn't applicable |
| `OAUTH_APP_BLOCKED` | Setup → Connected Apps Usage → admin blocked the app | Unblock or pick a different app |

### Refresh Token Policy: the silent-killer setting

On the Connected App, `Refresh Token Policy` has four values:

| Value | Behavior |
|---|---|
| **Refresh token is valid until revoked** | Token works indefinitely until explicitly revoked. |
| **Immediately expire refresh token** | Refresh token expires after one use. |
| **Expire refresh token if not used for N days** | Sliding window; inactive refresh tokens expire. |
| **Expire refresh token after N days** | Hard expiry from issuance. |

In metadata the field is `refreshTokenPolicy` on
`ConnectedAppOauthPolicy`, it is Required, and its documented
values are `zero`, `infinite`, `specific_lifetime:number:HOURS|DAYS|MONTHS`
and `specific_inactivity:number:HOURS|DAYS|MONTHS`
(Metadata API Developer Guide, `ConnectedAppOauthPolicy`).

Correction to the row above, grounded: `infinite` is the documented
default — "the refresh token is used indefinitely, unless revoked by
the user or Salesforce admin. Default setting." The Setup UI in an
older org may have presented a different pre-selected option.
UNVERIFIED (2026-09-04): the claim that older orgs defaulted to
"Immediately expire" is not in the Metadata API guide, which
documents `infinite` as the default; treat it as a field observation
and read the deployed value rather than assuming either default.

`zero` is the value that produces the classic "works once, then
dies" report: "The refresh token is invalid immediately. The user
can use the current session (access token) already issued, but
can't obtain a new session when the access token expires." The
failure therefore surfaces one access-token lifetime *after* the
change that caused it — which is why the `SetupAuditTrail` search
window has to start before the first failure, not at it.

**Right answer for server-to-server:** an explicit value you chose.
`infinite` only when a revocation runbook exists;
`specific_inactivity:` when the integration has a predictable
cadence. The policy-vs-kill-switch distinction and the revoke
procedure belong to `admin/integration-admin-connected-apps`.

### IP Relaxation

| Setting | Behavior |
|---|---|
| **Enforce IP restrictions** | Apply user's profile IP range; calls from outside fail with `IP_RESTRICTED`. |
| **Relax IP restrictions for activated devices** | First use prompts a device-verification email; subsequent calls from the verified device skip IP check. |
| **Relax IP restrictions** | Skip IP check for this Connected App. |

For server-to-server integrations from cloud infrastructure (AWS,
Azure, etc.) where the IP set is large or rotating, "Relax IP
restrictions" plus a tightly-scoped integration user is the
standard pattern.

### User assignment to the Connected App

The user authenticating via the Connected App must be authorized to
use it. Two models:

- **All users may self-authorize.** Anyone with API access can use
  the app; the user sees a consent screen on first use.
- **Admin-pre-approved users only.** The app must be assigned to
  the user via a profile or permission set's
  "Connected App Access" entries. Without assignment, the user
  gets `OAUTH_APP_BLOCKED` or similar.

Server-to-server integrations should use admin-pre-approved + a
dedicated integration user. The integration user has only the
permsets needed; the Connected App is assigned to those permsets
specifically.

### Login History as the diagnostic source

Setup → Login History (or `LoginHistory` SOQL):

- **`Status`** column tells you "Success" / "Failed: User not
  assigned to Connected App" / "Failed: Restricted IP" / "Invalid
  Password" / etc.
- **`SourceIp`** verifies the caller's IP.
- **`Application`** confirms the Connected App in use.
- **`AuthenticationServiceId`** identifies the auth method.

`Status` is the fastest discriminator, because it "[d]isplays the
status of the attempted login. Status is either success or a reason
for failure" — a sentence the Object Reference does not expand into
a value list, so read the strings your org actually emits rather
than matching against a remembered catalog.

`LoginSubType` is the field that names the grant: `OauthWebServer`,
`OauthRefreshToken`, `OauthClientCredentials`, `OauthUserAgent`,
`OauthTokenExchange`, `OAuthDevice`, `OauthUsernamePassword` and the
hybrid variants. It tells you which half of the dance failed before
you open a single Setup page.

Neither is filterable. `LoginHistory` publishes a closed list of
twelve filterable fields, and `Status`, `LoginSubType` and
`SourceIp` are outside it (gotcha 11). Anchor every evidence query
on `UserId` and `LoginTime`, then read the rest off the returned
rows. The ready-made queries are in `references/metadata-examples.md`.

Failures often show in Login History with a clearer cause than
the client receives. Always check Login History before guessing.

---

## Common Patterns

### Pattern A — JWT Bearer Flow setup that "works once, then dies"

**Symptom.** First call succeeds; subsequent calls fail with
`invalid_grant`.

**Cause.** Refresh Token Policy isn't relevant for JWT Bearer
(JWT itself is the credential, no refresh token), but the
**JWT signature** validation may fail if:

- Certificate expired.
- Wrong certificate referenced (Connected App keyed to one cert,
  client signing with another).
- Username mismatch (`sub` claim must be the username, exactly).

**Right answer.** Check certificate expiry. Match the certificate
in the Connected App's `Use digital signatures` setting against
the cert the client signs with. Test with a fresh JWT generated
manually to isolate variables.

### Pattern B — Server-to-server integration's refresh token dies on day 2

**Symptom.** Web Server flow integration works on Monday; fails
Tuesday with `invalid_grant`.

**Cause.** Refresh Token Policy is "Immediately expire refresh
token" (default in older orgs) or a short window.

**Right answer.** Set Refresh Token Policy = "Refresh token is
valid until revoked." Re-authorize the integration user (initial
authorization captures a new refresh token under the new policy).

### Pattern C — User can't access the Connected App

**Symptom.** User OAuth flow fails with `OAUTH_APP_BLOCKED` or a
silent fall-through.

**Diagnosis.** Setup → Apps → Connected Apps → click the app →
"OAuth Policies" → "Permitted Users":

- `All users may self-authorize` — user gets consent prompt.
- `Admin approved users are pre-authorized` — user must be
  assigned via profile or permset.

For "Admin approved" model: Setup → Profiles or Permission Sets →
edit the user's profile/permset → "Connected App Access" → enable
the app.

### Pattern D — Cloud-hosted integration hits IP restriction

**Symptom.** Integration on AWS Lambda / Heroku fails with
`IP_RESTRICTED` from a different IP each time.

**Cause.** Connected App IP Relaxation = "Enforce IP restrictions"
+ user's profile has a tight IP range that doesn't match the
cloud IP pool.

**Right answer.** Connected App IP Relaxation = "Relax IP
restrictions" (cloud IPs are too dynamic for IP-range pinning).
Compensate by tightening the integration user's permission scope
and rotating credentials regularly.

### Pattern E — Connected App admin-blocked for security review

**Symptom.** All flows for the app fail with
`OAUTH_APP_BLOCKED`.

**Cause.** Setup → Connected Apps OAuth Usage → admin set the app
to "Block" while reviewing or revoking access.

**Fix.** Unblock the app, OR (if the block was intentional)
migrate the integration to a different Connected App that's been
approved.

---

## Decision Guidance

| Symptom | Diagnosis | Fix |
|---|---|---|
| `invalid_grant` after first day | Refresh token policy too aggressive | Set to "Valid until revoked" |
| `invalid_grant` immediately on first call | Refresh token never issued (wrong scope, wrong user) | Add `refresh_token` scope; re-auth |
| `invalid_client_id` | Wrong Consumer Key | Verify against Connected App |
| `IP_RESTRICTED` from cloud infra | Tight IP enforcement | Relax IP restrictions |
| `OAUTH_APP_BLOCKED` | User not assigned OR app admin-blocked | Profile / permset assignment OR unblock |
| `redirect_uri_mismatch` | Callback URL not in app's list | Add the URL to the app |
| Silent failure / popup blocked | OAuth Web Server flow + popup blocker | Test in incognito; or use device flow |
| `unsupported_grant_type` | Flow not enabled in Connected App's OAuth Policies | Edit app; enable the grant type |
| Inactive user error | Integration user deactivated | Reactivate or migrate to new user |
| First call works, every subsequent call fails | Refresh token policy = "Immediately expire" | Set to "Valid until revoked" |

---

## Recommended Workflow

1. **Open a diagnosis record and paste the raw failure into it.** Copy the YAML skeleton from
   `templates/connected-app-diagnosis-record.yaml`. Fill `symptom`, `error` (verbatim response body,
   secrets replaced with `[REDACTED]`), `app`, `user-id` and `first-failure`. An error you have
   paraphrased is an error you have already started guessing about.
2. **Run the evidence query set in `references/metadata-examples.md` § 2 and record every result.**
   `LoginHistory` for the user over the failure window, `OauthToken` for the app, `SetupAuditTrail`
   for recent Setup changes. Each `evidence` entry needs both a `query` and a `result` — including
   "0 rows", which is itself a finding. Run the `OauthToken` query as a user holding Customize
   Application, or the empty result proves nothing.
3. **Walk the runbook table in `references/metadata-examples.md` § 1 top to bottom.** It goes
   symptom → error string → the `LoginHistory` `Status` / `LoginSubType` to look for → the exact
   `ConnectedApp` XML path to inspect → the fix. Stop at the first row whose evidence column matches
   what step 2 actually returned; assign the matching `root-cause` category.
4. **Inspect the deployed policy, not the Setup screen.** Retrieve the app and compare its
   `oauthConfig` / `oauthPolicy` against the annotated excerpt in
   `references/metadata-examples.md` § 3. `admin/connected-apps-and-auth` owns the full file; this
   step only reads the four fields the runbook named.
5. **Reproduce in a sandbox before changing production** using the procedure in
   `references/metadata-examples.md` § 4 — matching policy block, the sandbox login host, and the
   sandbox-suffixed username. Skip this only when the diagnosis is a user assignment, which is
   reversible in one click.
6. **Apply the fix, re-authorize from a clean state, and re-run the same queries from step 2.**
   Paste the post-fix rows into `verified-by`. A refresh-policy fix is not verified until a
   `LoginSubType = OauthRefreshToken` row returns Success, because the initial authorization would
   have succeeded either way.
7. **Lint the record and the metadata.**
   `python3 scripts/check_connected_app_troubleshooting.py --manifest-dir force-app/main/default`
   fails on an incomplete diagnosis record and on the three policy combinations that produce the
   classic failures. Commit the record next to the change.

---

## Review Checklist

- [ ] Error code captured exactly from the client.
- [ ] Login History checked for the user / time window.
- [ ] Connected App Refresh Token Policy is "Valid until revoked" for server-to-server.
- [ ] User is assigned to the Connected App via profile or permset.
- [ ] Callback URL list includes every URL the client uses.
- [ ] IP Relaxation matches the integration's IP source (relax for cloud, enforce for on-prem).
- [ ] Cert (for JWT Bearer) is current and matches client.
- [ ] Test post-fix verifies Success in Login History.

---

## Salesforce-Specific Gotchas

1. **`refreshTokenPolicy` `zero` works for one access-token lifetime, then dies** — and the documented default is `infinite`, not "immediately expire". (See `references/gotchas.md` § 1.)
2. **`invalid_grant` is overloaded** — five different causes; check Login History to disambiguate. (See `references/gotchas.md` § 2.)
3. **User assignment to Connected App is required for "Admin pre-approved" mode.** Profile or permset entry. (See `references/gotchas.md` § 3.)
4. **`redirect_uri` mismatch is character-exact** — trailing slashes matter. (See `references/gotchas.md` § 4.)
5. **JWT `sub` claim must be the user's Username, not Email.** (See `references/gotchas.md` § 5.)
6. **Connected App admin-block** is a separate setting from disabling OAuth. (See `references/gotchas.md` § 6.)
7. **IP Relaxation interacts with the user's profile IP range** — both must permit the caller. (See `references/gotchas.md` § 7.)
8. **`LoginSubType` names the failing grant but cannot anchor a `WHERE` clause** — it is outside the twelve filterable fields. (See `references/gotchas.md` § 11.)
9. **`ForwardedForIp` is never populated for an OAuth login**, so the documented way to see past a proxy does not exist for this flow. (See `references/gotchas.md` § 12.)
10. **`SetupAuditTrail.Section` and `Display` are not filterable** — the "who changed the policy" query has to filter on `Action`. (See `references/gotchas.md` § 13.)
11. **Secret-required is two independent switches**, so an app can pass its first token exchange and fail every refresh. (See `references/gotchas.md` § 14.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Error → Cause → Fix mapping | Translated explanation for the specific OAuth error |
| Connected App settings change | Refresh Token Policy, IP Relaxation, Permitted Users, Callback URL |
| User assignment update | Profile / permset Connected App Access entry |
| Verification via Login History | Confirms the test post-fix shows Success |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are running a live diagnosis — the symptom-to-fix runbook table, the three evidence queries, the `oauthPolicy` excerpt to compare against, the sandbox reproduction procedure, and the diagnosis-record shape all live here |
| `references/gotchas.md` | An evidence query returned an answer you don't trust, a fix didn't take, or the failure timestamp doesn't line up with the change that caused it |
| `references/examples.md` | You want the worked narratives end to end, including a completed diagnosis record |
| `references/well-architected.md` | You need the Security / Reliability framing for a post-incident write-up, or the official source behind a claim here |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated OAuth triage advice before acting on it |
| `templates/connected-app-troubleshooting-template.md` | At the start of a triage, to capture the symptom, flow, user and evidence in one place |
| `templates/connected-app-diagnosis-record.yaml` | The record you fill during the triage and commit alongside the fix — linted by the checker |
| `scripts/check_connected_app_troubleshooting.py` | Before deploying a policy fix, and again once the diagnosis record is written |

---

## Related Skills

- `integration/oauth-flows-and-connected-apps` — choosing and designing the OAuth grant flow; this skill is the troubleshooting half.
- `admin/connected-apps-and-auth` — authoring the full `connectedApp` / External Client App / Named Credential file, and the artefact decision.
- `admin/integration-admin-connected-apps` — the operations half: hardening, revocation, key and secret rotation, monitoring, and the periodic review.
- `security/oauth-token-management` — token lifecycle and revocation semantics beyond a single failing flow.
- `security/login-forensics` — when the question is "who logged in and from where", not "why did this grant fail".
- `security/sso-saml-troubleshooting` — SAML-specific debugging (different runtime, different evidence).
- `apex/apex-jwt-bearer-flow` — JWT-specific setup including certificate management.
- `integration/named-credentials-setup` — External Credentials and Named Credentials, which interact with these OAuth flows.
- `admin/org-setup-and-configuration` — My Domain, trusted IP ranges and session settings, which the login host and the IP branch both depend on.
