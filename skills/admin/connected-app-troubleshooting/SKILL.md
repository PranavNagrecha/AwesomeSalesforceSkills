---
name: connected-app-troubleshooting
description: "Troubleshooting Connected App OAuth flows — IP relaxation vs IP restriction, refresh token policy traps (default kills the connection on first refresh), session-revocation semantics, the OAuth error-code catalog (`invalid_grant`, `invalid_client_id`, `unsupported_grant_type`), per-user vs admin-pre-approved flows, and the user-policy check (Connected App must be assigned to the user via profile / permset). Covers the Login History debug trail and the test-once-with-real-credentials sanity check before integrations go live. NOT for designing the OAuth flow itself (use security/oauth-flows-and-connected-apps), NOT for SAML troubleshooting (use admin/sso-saml-troubleshooting)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
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
`security/oauth-flows-and-connected-apps`. SAML / SSO debugging is
`admin/sso-saml-troubleshooting`. This skill is for the
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

## Core Concepts

### The OAuth error catalog

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

The default in older orgs was "Immediately expire refresh token"
or a short-window equivalent — the integration works for one
access-token lifetime, then dies on first refresh. This is the
single most-common silent OAuth failure for server-to-server
integrations.

**Right answer for server-to-server:** "Refresh token is valid
until revoked." Pair with credential-rotation discipline.

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

1. **Capture the OAuth error code** verbatim from the client.
2. **Pull Login History** for the user + time window. Failures often show clearer causes there.
3. **Match against the error catalog.** Most issues fit a known shape.
4. **Apply the fix** in the Connected App settings or user / profile assignment.
5. **Test with a fresh credential** (don't rely on the cached one that may be in a bad state).
6. **Verify in Login History** that the test attempt now shows Success.

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

1. **Default Refresh Token Policy in older orgs is "Immediately expire"** — works for one access-token lifetime, then dies. (See `references/gotchas.md` § 1.)
2. **`invalid_grant` is overloaded** — five different causes; check Login History to disambiguate. (See `references/gotchas.md` § 2.)
3. **User assignment to Connected App is required for "Admin pre-approved" mode.** Profile or permset entry. (See `references/gotchas.md` § 3.)
4. **`redirect_uri` mismatch is character-exact** — trailing slashes matter. (See `references/gotchas.md` § 4.)
5. **JWT `sub` claim must be the user's Username, not Email.** (See `references/gotchas.md` § 5.)
6. **Connected App admin-block** is a separate setting from disabling OAuth. (See `references/gotchas.md` § 6.)
7. **IP Relaxation interacts with the user's profile IP range** — both must permit the caller. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Error → Cause → Fix mapping | Translated explanation for the specific OAuth error |
| Connected App settings change | Refresh Token Policy, IP Relaxation, Permitted Users, Callback URL |
| User assignment update | Profile / permset Connected App Access entry |
| Verification via Login History | Confirms the test post-fix shows Success |

---

## Related Skills

- `security/oauth-flows-and-connected-apps` — designing the OAuth architecture; this skill is the troubleshooting half.
- `admin/sso-saml-troubleshooting` — SAML-specific debugging (different runtime).
- `apex/jwt-bearer-flow` — JWT-specific setup including certificate management.
- `admin/external-credentials-setup` — modern External Credentials (post-Named-Credential migration) interact with OAuth flows.
