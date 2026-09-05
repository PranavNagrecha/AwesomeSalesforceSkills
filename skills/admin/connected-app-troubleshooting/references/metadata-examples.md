# Metadata Examples — Connected App Troubleshooting

This is the working half of the skill: the runbook table, the evidence queries, the policy excerpt
to compare a live app against, the sandbox reproduction, and the diagnosis record the checker lints.

It deliberately does **not** contain a whole `connectedApp-meta.xml`. Authoring the full file — and
the connected app vs External Client App decision that precedes it — belongs to
`admin/connected-apps-and-auth`. The operations that follow a fix (revocation, key and secret
rotation, the periodic review) belong to `admin/integration-admin-connected-apps`.

**About the error strings.** Every OAuth token-endpoint `error` value in the table below carries an
UNVERIFIED marker. The REST API Developer Guide's status-code table documents the HTTP layer — 401
is "The session ID or OAuth token used has expired or is invalid. The response body contains the
message and errorCode", 403 is "The request has been refused. Verify that the logged-in user has
appropriate permissions" — but the token endpoint's `error` / `error_description` vocabulary is not
in any guide in this skill's source set. Match on the *behaviour* columns, which are grounded, and
treat the error string as a hint.

---

## 1. The runbook: symptom → error → evidence → policy field → fix

Walk this top to bottom. Stop at the first row whose **evidence** column matches what § 2 actually
returned, not the first row whose error string looks familiar.

| # | Symptom | Error text (client side) | LoginHistory evidence to look for | Policy field to inspect (`ConnectedApp` XML path) | Fix | `root-cause` |
|---|---|---|---|---|---|---|
| 1 | Never worked. Consent screen appears, then the callback errors. | `redirect_uri_mismatch` — UNVERIFIED (2026-09-04): string not in this skill's source set | Often **no row at all** — the exchange fails before a session is created | `oauthConfig/callbackUrl` — "Required. The endpoint that Salesforce calls back to your connected app during OAuth. It's the OAuth `redirect_uri`." | Add the client's exact URI, one per line. Character-exact (gotcha 4). | `callback-url` |
| 2 | Never worked. User authenticates, lands back with an app-blocked error. | `OAUTH_APP_BLOCKED` — UNVERIFIED (2026-09-04) | A row for the user with a failure `Status`; `LoginSubType` = `OauthWebServer` | `oauthConfig/isAdminApproved` plus `permissionSetName` / `profileName` — "If set to `true`, only users with the appropriate profile or permission set can access the app." | Add the user's permission set to `permissionSetName` (one name per line) and redeploy. | `pre-authorization` |
| 3 | Never worked. Client-credentials integration returns nothing usable. | `unsupported_grant_type` — UNVERIFIED (2026-09-04) | No row, or `LoginSubType` absent for `OauthClientCredentials` | `oauthConfig/isClientCredentialEnabled` and `oauthClientCredentialUser` — the execution user "must have the API Only permission" | Enable the flag and name the execution user; the two are a pair. | `flow-not-enabled` |
| 4 | Worked once. Every renewal fails. Certificate is current. | `invalid_grant` — UNVERIFIED (2026-09-04) | `LoginSubType` = `OauthRefreshToken` with a failure `Status`, while the earlier `OauthWebServer` row is Success | `oauthPolicy/refreshTokenPolicy` — `zero` means "The refresh token is invalid immediately. The user can use the current session (access token) already issued, but can't obtain a new session when the access token expires." | Set an explicit lifetime or inactivity window; re-authorize so a token is issued under the new policy. | `refresh-token-policy` |
| 5 | Worked once. Renewal fails, and the client never stored a secret. | `invalid_client` / `invalid_client_credentials` — UNVERIFIED (2026-09-04) | Same split as row 4: initial grant Success, `OauthRefreshToken` failing | `oauthConfig/isSecretRequiredForRefreshToken` (default `true`) read **against** `isConsumerSecretOptional` | These are two independent switches (gotcha 14). Either give the client the secret, or set `isSecretRequiredForRefreshToken` to `false` for a genuine public client. | `secret-required-asymmetry` |
| 6 | Ran for months. Every renewal now fails; two client replicas share one stored token. | `invalid_grant` — UNVERIFIED (2026-09-04) | Repeated `OauthRefreshToken` failures starting at one timestamp | `oauthConfig/isRefreshTokenRotationEnabled` — "If a user tries to use a previous refresh token that's been invalidated, the current refresh token and its associated access tokens get deleted." | Make one process own the token, or turn rotation off. See `admin/connected-apps-and-auth` for the field's full semantics. | `refresh-token-rotation` |
| 7 | Works from the office, fails from cloud infrastructure. | `IP_RESTRICTED` / `restricted_ip` — UNVERIFIED (2026-09-04) | A failure row whose `SourceIp` is the caller's **first proxy**, not its origin (gotcha 12) | `oauthPolicy/ipRelaxation` — `ENFORCE` (default) "Enforces the IP restrictions configured for the org, such as the IP ranges assigned to a user profile" | Decide by flow, not by strictness. Add `ipRanges` if the caller can enumerate them; the four-value semantics are in `admin/connected-apps-and-auth`. | `ip-restriction` |
| 8 | Worked yesterday. Nothing was deployed. | `invalid_grant`, or a generic 401 | `SetupAuditTrail` rows in the window **before** the first failure | Whatever the audit row names — usually `oauthPolicy` | Revert or re-approve the change. The lag is real: a refresh policy is evaluated at the next refresh, so the change predates the symptom (see `admin/integration-admin-connected-apps`). | `policy-change` |
| 9 | Integration user only. Other users fine. | `inactive_user` — UNVERIFIED (2026-09-04) | A failure row on the user, or **no row at all** if the user is frozen before authentication | None — this is a User record, not the app | Reactivate or unfreeze; if the permission set that pre-authorizes the app has a dated `PermissionSetAssignment`, see `admin/integration-admin-connected-apps`. | `user-state` |
| 10 | All flows for one app fail; other apps on the same org are fine. | `OAUTH_APP_BLOCKED` — UNVERIFIED (2026-09-04) | Failure rows across multiple users and multiple `LoginSubType` values | None in the XML — the block lives in Connected Apps OAuth Usage | Unblock, or migrate to an approved app (gotcha 6). | `app-blocked` |
| 11 | Authentication succeeds; the *API call* is refused. | HTTP 403, or 401 on a later call | `Status` = Success. The failure is not a login failure at all | `oauthConfig/scopes` | REST API: 403 is "The request has been refused. Verify that the logged-in user has appropriate permissions." Fix the scope or the user's object permissions, not the app policy. | `post-auth-authorization` |

Row 11 exists because it is the most common misdiagnosis: a Success row in `LoginHistory` next to a
failing integration means the OAuth dance completed and the problem is downstream.

---

## 2. The evidence query set

Run all three before changing anything. Record each result — including "0 rows" — in the diagnosis
record. Filterability constraints are grounded in the Object Reference and explained in gotchas
11 and 13.

### 2a. Every login attempt for the integration user, last 24 hours

`UserId` and `LoginTime` are both on the filterable list. `Status`, `LoginSubType`, `Application`
and `SourceIp` are not — they are selected and read, never filtered.

```sql
SELECT LoginTime, Status, LoginType, LoginSubType, Application,
       SourceIp, ApiType, ApiVersion, TlsProtocol, AuthenticationServiceId
FROM LoginHistory
WHERE UserId = '005XXXXXXXXXXXXXXX'
  AND LoginTime = LAST_N_DAYS:1
ORDER BY LoginTime DESC
```

Read it this way:

- **A Success row with `LoginSubType` = `OauthWebServer` and no later `OauthRefreshToken` row** — the
  initial authorization worked and the client has not attempted a renewal yet. Nothing is proven.
- **`OauthWebServer` Success followed by `OauthRefreshToken` failures** — runbook rows 4, 5 or 6.
  The renewal half is broken; the app's `oauthConfig` for the initial exchange is not the suspect.
- **No rows at all** — the request never produced a session. Runbook rows 1 or 3, or the caller is
  not reaching this org (check the login host, § 4).
- **`SourceIp`** is the first proxy to reach Salesforce for a proxied client, and the documented
  alternative is empty for OAuth logins (gotcha 12). Do not treat it as the caller's egress address.

### 2b. Which grants exist for the app

Run as a user holding Customize Application — "Users with the Customize Application permission see
all tokens for all users in the org. Otherwise, you see only your own tokens." An empty result from
anyone else is not evidence.

```sql
SELECT AppName, UserId, LastUsedDate, UseCount
FROM OauthToken
WHERE AppName = 'Billing Sync JWT'
ORDER BY LastUsedDate DESC
```

- **No row for the user** — the authorization never completed. Combine with 2a: no `LoginHistory`
  row either means the request never arrived; a failure row means it arrived and was rejected.
- **A row with a stale `LastUsedDate` and a non-zero `UseCount`** — the grant was established and
  used, and then stopped being exchanged. That timestamp is the start of the `SetupAuditTrail`
  window in 2c.
- Row-count ceilings and the `Id`-is-always-null constraint on this object are covered by
  `admin/integration-admin-connected-apps`; for a single-app diagnosis the filter on `AppName`
  keeps you well under them.

### 2c. What changed in Setup before the first failure

Only `Action` and `DelegateUser` carry the `Filter` property on this object; `Section` and `Display`
are `Nillable, Sort` only, so they are read off the rows rather than filtered (gotcha 13). The
object holds changes "for at least the last 180 days".

```sql
SELECT CreatedDate, CreatedBy.Name, CreatedByContext, DelegateUser,
       Action, Section, Display
FROM SetupAuditTrail
WHERE CreatedDate >= 2026-08-20T00:00:00Z
ORDER BY CreatedDate DESC
LIMIT 500
```

Then scan the returned `Section` and `Display` values for the app's label. `Display` is "the full
description of changes made in Setup", `Action` is "the category of the change made in Setup", and
`DelegateUser` is "the Login-As user who executed the action in Setup" — a non-blank `DelegateUser`
means the change was made by someone logged in as another user, which changes who you ask about it.

Start the window **before** the first observed failure, not at it. A refresh-token policy takes
effect at the next refresh, so the change and the symptom can be a full session apart.

---

## 3. The `oauthPolicy` / `oauthConfig` excerpt to compare against

Retrieve the live app and diff these fields. This is an **excerpt** for comparison during a
diagnosis, not a deployable app definition — the full file, with `contactEmail`, `label`,
`callbackUrl` and the rest, is in `admin/connected-apps-and-auth`
(`references/metadata-examples.md` § 1).

`force-app/main/default/connectedApps/Billing_Sync_JWT.connectedApp-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ConnectedApp xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- EXCERPT for diagnosis. Required fields (contactEmail, label,
         oauthConfig/callbackUrl) are omitted here and are mandatory in the
         real file. Author the full file from admin/connected-apps-and-auth. -->
    <label>Billing Sync JWT</label>
    <contactEmail>platform-integrations@example.com</contactEmail>
    <oauthConfig>
        <callbackUrl>https://example.com/oauth/callback</callbackUrl>
        <!-- Runbook row 2: isAdminApproved without a grantee authorizes nobody. -->
        <isAdminApproved>true</isAdminApproved>
        <!-- Runbook row 5: these two are independent switches. -->
        <isConsumerSecretOptional>false</isConsumerSecretOptional>
        <isSecretRequiredForRefreshToken>true</isSecretRequiredForRefreshToken>
        <!-- Runbook row 6: replaying an old token deletes the current grant. -->
        <isRefreshTokenRotationEnabled>false</isRefreshTokenRotationEnabled>
        <scopes>Api</scopes>
        <scopes>RefreshToken</scopes>
    </oauthConfig>
    <oauthPolicy>
        <!-- Runbook row 7. ENFORCE is the documented default. -->
        <ipRelaxation>ENFORCE</ipRelaxation>
        <!-- Runbook row 4. `zero` is the "works once then dies" value. -->
        <refreshTokenPolicy>specific_inactivity:7:DAYS</refreshTokenPolicy>
    </oauthPolicy>
    <!-- Runbook row 2's other half. One permission set name per line. -->
    <permissionSetName>Billing_Sync_Integration</permissionSetName>
</ConnectedApp>
```

How to read it:

- `oauthConfig` governs the **initial** exchange; `oauthPolicy` governs the **renewal**. Step 2a's
  `LoginSubType` tells you which one to look at, so you are not diffing eleven fields.
- `permissionSetName` and `profileName` both carry the same precondition: "To use this field, the
  `isAdminApproved` field on the `ConnectedAppOauthConfig` subtype must be set to `true`." Deploying
  an empty `<permissionSetName></permissionSetName>` removes every assignment — a diagnosis that
  ends in "redeploy the app from a trimmed source file" can create runbook row 2.
- `refreshTokenPolicy` and `ipRelaxation` are both **Required** on `ConnectedAppOauthPolicy`. An app
  whose retrieved file has no `<oauthPolicy>` block at all is running on defaults nobody chose.
- `consumerSecret` will not be in the retrieved file: "When set, the value isn't returned in
  Metadata API requests." Its absence is not a finding.

### package.xml for the retrieve

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Billing_Sync_JWT</members>
        <name>ConnectedApp</name>
    </types>
    <version>64.0</version>
</Package>
```

### Retrieve, lint, deploy

```bash
# Pull the app as it actually is in the org that is failing.
sf project retrieve start -o prod -x manifest/package.xml

# Lint the policy combinations and the diagnosis record together.
python3 scripts/check_connected_app_troubleshooting.py \
    --manifest-dir force-app/main/default

# Validate the fix without committing it, then deploy.
sf project deploy start -o prod -x manifest/package.xml --dry-run
sf project deploy start -o prod -x manifest/package.xml
```

### Verification step

After the fix and a fresh authorization, re-run 2a and require a Success row for the grant that was
failing — not just any Success row:

```sql
SELECT LoginTime, Status, LoginSubType, Application
FROM LoginHistory
WHERE UserId = '005XXXXXXXXXXXXXXX'
  AND LoginTime = LAST_N_DAYS:1
ORDER BY LoginTime DESC
LIMIT 20
```

A `refresh-token-policy` fix is verified only by a Success row whose `LoginSubType` is
`OauthRefreshToken`. The initial `OauthWebServer` authorization would have succeeded under the
broken policy too, which is exactly why the original report said "it works, then it stops".

---

## 4. Sandbox reproduction procedure

Reproduce before changing production whenever the fix touches `oauthPolicy`, `ipRelaxation`, or
anything that could invalidate live grants. Skip it for a permission-set assignment, which is
reversible in one click.

1. **Deploy the same excerpt** from § 3 into the sandbox. If the sandbox app's `oauthPolicy` differs
   from production, you are reproducing a different bug.
2. **Point the client at the sandbox login host.** The Data Loader guide states the general shape:
   "The production and test authentication endpoints default to `login.salesforce.com` and
   `test.salesforce.com`. Salesforce recommends changing these to the My Domain URLs of your orgs."
   A JWT `aud` claim, an OAuth authorize URL and a callback URL are all host-specific — changing one
   and not the others produces a fresh, unrelated failure.
3. **Confirm My Domain is deployed in the sandbox** and use its URL rather than `test.salesforce.com`
   in every one of those three places. My Domain sequencing, and the fact that a deployed domain
   becomes the org's identity across integrations, is `admin/org-setup-and-configuration`.
4. **Use the sandbox-suffixed username.** UNVERIFIED (2026-09-04): the rule that a sandbox copy
   appends `.<sandboxName>` to every username is not stated in this skill's source set; read the
   actual value from Setup → Users in the sandbox rather than constructing it. It matters because a
   JWT `sub` claim must be the Username exactly (gotcha 5).
5. **Reproduce the failure first, then apply the fix.** A sandbox that does not reproduce the symptom
   has not validated anything. If it will not reproduce, the difference between the two orgs is
   itself the diagnosis — diff the two retrieved `oauthPolicy` blocks.
6. **Exercise the renewal, not just the first call.** For a refresh-policy or secret-asymmetry
   diagnosis, let the access token expire (or force a refresh) and confirm an `OauthRefreshToken`
   row appears in the sandbox's `LoginHistory`.

---

## 5. The diagnosis record

Fill this during the triage and commit it with the fix. The checker lints it: every field below is
required, `root-cause` must be one of the eleven categories from the § 1 table, every `evidence`
entry needs both a `query` and a `result`, and `verified-by` must be non-empty.

`force-app/main/default/connected-app-diagnosis-record.yaml`

```yaml
diagnosis:
  symptom: Billing Sync worker authenticated Monday, every call since Tuesday 09:14 returns 401
  error: |
    HTTP 400 from /services/oauth2/token
    {"error":"invalid_grant","error_description":"expired access/refresh token"}
    Consumer key: [REDACTED]
  app: Billing Sync JWT
  user-id: 005XXXXXXXXXXXXXXX
  first-failure: 2026-09-02T09:14:00Z
  flow: OAuth Web Server, then refresh
  root-cause: refresh-token-policy
  fix-applied: |
    oauthPolicy/refreshTokenPolicy changed from `zero` to
    `specific_inactivity:7:DAYS`; integration user re-authorized so a
    token is issued under the new policy.
  verified-by: |
    LoginHistory 2026-09-04T11:02Z — Status Success,
    LoginSubType OauthRefreshToken. Second refresh at 11:47Z also Success.
  evidence:
    - step: LoginHistory for the integration user, last 24h
      query: >
        SELECT LoginTime, Status, LoginSubType, Application, SourceIp
        FROM LoginHistory WHERE UserId = '005XXXXXXXXXXXXXXX'
        AND LoginTime = LAST_N_DAYS:1 ORDER BY LoginTime DESC
      result: >
        11 rows. One OauthWebServer Success on 2026-09-01T08:02Z.
        Ten OauthRefreshToken failures from 2026-09-02T09:14Z onward.
        Rules out rows 1, 2, 3 and 10 — the initial grant succeeded.
    - step: OauthToken rows for the app
      query: >
        SELECT AppName, UserId, LastUsedDate, UseCount FROM OauthToken
        WHERE AppName = 'Billing Sync JWT' ORDER BY LastUsedDate DESC
      result: >
        1 row, UseCount 1, LastUsedDate 2026-09-01T08:02Z. Run as
        integration-ops@example.com, who holds Customize Application.
        Grant exists and was used exactly once.
    - step: SetupAuditTrail from before the first failure
      query: >
        SELECT CreatedDate, CreatedBy.Name, DelegateUser, Action, Section,
        Display FROM SetupAuditTrail WHERE CreatedDate >= 2026-08-25T00:00:00Z
        ORDER BY CreatedDate DESC LIMIT 500
      result: >
        Row 2026-09-01T07:41Z, Section "Connected Apps", Display names
        Billing Sync JWT and a refresh token policy change. DelegateUser
        blank. Precedes the first failure by one access-token lifetime.
```

The `result` field is where the diagnosis actually happens. "11 rows" is data; "rules out rows 1, 2,
3 and 10" is the reasoning that makes the record worth committing.

---

## Related reading

| Question | Skill |
|---|---|
| I need to author or migrate the whole app file | `admin/connected-apps-and-auth` |
| The diagnosis is done; now revoke, rotate, or schedule the review | `admin/integration-admin-connected-apps` |
| Which grant flow should this integration use at all | `integration/oauth-flows-and-connected-apps` |
| The question is who logged in from where, across the org | `security/login-forensics` |
| The failure is SAML, not OAuth | `security/sso-saml-troubleshooting` |
