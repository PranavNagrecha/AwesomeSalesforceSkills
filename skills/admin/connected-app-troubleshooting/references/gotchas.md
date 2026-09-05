# Gotchas — Connected App Troubleshooting

Non-obvious Connected App behaviors.

---

## Gotcha 1: `refreshTokenPolicy` `zero` lets the current session finish, so the failure arrives late

**What happens.** Integration works for one access-token
lifetime, then dies on first refresh. The Metadata API guide
defines the value exactly: `zero` — "The refresh token is invalid
immediately. The user can use the current session (access token)
already issued, but can't obtain a new session when the access
token expires." The grant is dead the moment it is issued, and the
client keeps working until the access token runs out.

UNVERIFIED (2026-09-04): the older claim that this was the default
in older orgs is not supported by the Metadata API guide, which
documents `infinite` as the default ("the refresh token is used
indefinitely, unless revoked by the user or Salesforce admin.
Default setting"). Read the deployed `refreshTokenPolicy` value
rather than assuming any default.

**When it occurs.** On the second working day of a new
integration, and after any policy edit — never at the moment of
the change, because the currently-issued access token is
unaffected. The audit-trail entry therefore precedes the first
failure, which is why the `SetupAuditTrail` window in
`references/metadata-examples.md` § 2c starts before the symptom.

**How to avoid.** Set an explicit value rather than inheriting one:
`specific_inactivity:<n>:HOURS|DAYS|MONTHS` for a use-it-or-lose-it
window, `specific_lifetime:<n>:...` for a hard ceiling, `infinite`
only where a revocation runbook exists. Re-authorize after the
change so a token is issued under the new policy.

---

## Gotcha 2: `invalid_grant` is overloaded — five different causes

**What happens.** Single error code maps to: refresh token
expired, refresh token revoked, refresh token never issued
(missing scope), wrong user, certificate expired (JWT).

**When it occurs.** On every report that arrives as a bare error
string with no timeline. The five causes split cleanly once you
know whether the failing grant is the first authorization or a
renewal — see `LoginSubType` in `references/metadata-examples.md`
§ 2a.

**How to avoid.** Always check Login History to disambiguate.
The `Status` column there often shows clearer cause.

---

## Gotcha 3: User assignment for "Admin approved" mode is non-obvious

**What happens.** Connected App's "Permitted Users" = "Admin
approved users are pre-authorized". User OAuth flow fails with
`OAUTH_APP_BLOCKED`. Admin sees no error setting up the app.

**When it occurs.** At first use by a real user, never during
setup, and again after any deploy from a source file that trimmed
the access elements — an empty `permissionSetName` removes every
assignment.

**How to avoid.** Profile or Permission Set must include the
Connected App in its "Connected App Access" entries. Document
this as part of the rollout checklist.

---

## Gotcha 4: `redirect_uri` mismatch is character-exact

**What happens.** Connected App's Callback URL is
`https://app.example.com/oauth/callback` but client sends
`https://app.example.com/oauth/callback/`. Trailing slash
mismatch fails with `redirect_uri_mismatch`.

**When it occurs.** On a first integration, and on any change of
login host — a My Domain deploy or a move between sandbox and
production changes the URI the client redirects from.

**How to avoid.** Match the callback URL exactly. Add multiple
URLs to the Connected App's Callback URL list (one per line) if
the client may send variants.

---

## Gotcha 5: JWT `sub` claim must be the Username, not Email

**What happens.** Client constructs JWT with `sub = user@example.com`
(the user's Email). JWT Bearer flow fails with `invalid_grant`.
Username might be `user@example.com.acmesandbox` (Salesforce
appended the org suffix).

**When it occurs.** Most often on the first sandbox test after a
production integration was working, because the sandbox copy
changes the Username and not the Email.

**How to avoid.** Use the User.Username field, exactly as it
appears in Setup → Users.

---

## Gotcha 6: Connected App admin-block is separate from disabling OAuth

**What happens.** Admin sets the Connected App to "Block"
status while reviewing access. The app itself is still defined
and configured; OAuth flows fail with `OAUTH_APP_BLOCKED`.

**When it occurs.** Across every user and every grant type at
once — which is the discriminator against a per-user
pre-authorization problem, where only some users fail.

**How to avoid.** Setup → Apps → Connected Apps OAuth Usage —
check if the app is blocked. Unblock if appropriate.

---

## Gotcha 7: IP Relaxation interacts with the user's profile IP range

**What happens.** Connected App is "Relax IP restrictions" but
the user's profile has a tight Login IP Range. Both must permit
the caller; the union doesn't apply, the user's profile does.

**When it occurs.** After the connected app is loosened but the
integration user's profile is not, so the change looks applied and
nothing improves.

**How to avoid.** Verify both layers. For server-to-server
integrations, the integration user's profile should NOT have a
restrictive IP range that conflicts with the Connected App's
Relax setting.

---

## Gotcha 8: Resetting the Consumer Secret breaks every active session

**What happens.** Admin resets the Connected App's Consumer
Secret in Setup. Every integration using that app fails until
the new secret is propagated.

**When it occurs.** Immediately and org-wide, unlike a policy
change — a useful way to tell the two apart when the timeline is
ambiguous.

**How to avoid.** Treat secret resets as planned changes.
Coordinate with every integration using the app; rotate
secrets via a credential manager that propagates atomically.

---

## Gotcha 9: Connected App metadata deploys with sandbox-shaped Consumer Key

**What happens.** Connected App deployed via metadata; the
deployed Connected App has a NEW Consumer Key (the sandbox key
isn't preserved). Integration was configured with sandbox key.

**When it occurs.** On the first call after a promotion to a new
environment, before any user has authenticated — so `LoginHistory`
is usually empty, which is itself the tell.

**How to avoid.** After Connected App deploy to a new env,
fetch the Consumer Key from Setup and update the integration's
config. The key is environment-specific.

---

## Gotcha 10: `Username-Password` flow is deprecated for most uses

**What happens.** New integration uses Username-Password OAuth
flow; admin gets a warning email about deprecation.

**When it occurs.** On new builds copied from older
documentation. `LoginHistory` records these as `LoginSubType` =
`OauthUsernamePassword`, a fast way to find them across an org.

**How to avoid.** Use JWT Bearer (server-to-server) or Web
Server flow (interactive) instead. Username-Password only for
legacy systems being actively migrated; not for new code.

---

## Gotcha 11: The one field that names the failing grant reads as filterable and is not

**What happens.** `LoginSubType` is the field that separates `OauthWebServer` from
`OauthRefreshToken`, `OauthClientCredentials`, `OauthUserAgent`, `OauthTokenExchange`, `OAuthDevice`
and `OauthUsernamePassword` — which is exactly the "did the first authorization fail, or the
renewal?" question the whole diagnosis turns on. Its own field row lists `Filter, Group, Nillable,
Restricted picklist, Sort`, so an agent reading the field table writes
`WHERE LoginSubType = 'OauthRefreshToken'` and the query is rejected. The Usage section of the same
object publishes a closed list — "Not all fields are filterable. You can only filter on the
following fields: `AuthenticationServiceId`, `CipherSuite`, `CountryIso`, `Id`, `LoginTime`,
`LoginType`, `LoginUrl`, `NetworkId`, `OptionsIsGet`, `OptionsIsPost`, `TlsProtocol`, `UserId`" —
and `LoginSubType` is not on it. Neither is `SourceIp`, whose field row also advertises `Filter`.

**When it occurs.** On the first attempt to build a targeted evidence query, and again in any
generated monitoring report, because the two halves of the documentation disagree and the field
table is the half most readers reach first.

**How to avoid.** Treat the Usage list as authoritative and the per-field `Filter` property as
unreliable on this object. Anchor on `UserId` and `LoginTime`, select `LoginSubType` and read it off
the returned rows, and sort or group by it in the client. `Application`, `Status` and comma-bearing
`LoginType` values are a related trap covered by `admin/integration-admin-connected-apps` gotcha 7.

---

## Gotcha 12: For an OAuth failure, the documented way to see past a proxy does not exist

**What happens.** An IP-restriction diagnosis needs the caller's real egress address. `SourceIp` is
"the IP address of the incoming client request that first reaches Salesforce during a login", and
the Object Reference immediately qualifies it: "For clients that redirect through one or more HTTP
proxies, this field stores the IP address of the first proxy to reach Salesforce. To better identify
the origin IP for these cases, check the `ForwardedForIp` field instead." That instruction does not
apply here. `ForwardedForIp` "isn't populated for logins completed via OAuth flows or single sign-on
(SSO)" — the one flow this skill exists for is the documented exception. `SourceIp` also "doesn't
support the LIKE comparison operator", so subnet-shaped matching is out even client-side-adjacent.

**When it occurs.** Every time an `ipRelaxation` `ENFORCE` failure is investigated for a caller
behind a load balancer, API gateway or CDN — which is most cloud-hosted integrations. The recorded
address looks authoritative, gets added to a profile's Login IP Range, and the failure continues
because the address belonged to a proxy that rotates.

**How to avoid.** Do not treat `SourceIp` as the caller's egress address for an OAuth login. Get the
egress ranges from the caller's own infrastructure, then confirm the fix by re-running the login and
watching for a Success row — not by matching addresses. If the caller cannot enumerate its ranges,
the IP branch is not diagnosable from Salesforce evidence and the design question belongs to
`admin/connected-apps-and-auth`.

---

## Gotcha 13: The two `SetupAuditTrail` columns that say what changed cannot anchor a `WHERE` clause

**What happens.** The obvious "what changed on this connected app" query filters on the section or
the description — `WHERE Section = 'Connected Apps'`, or a `LIKE` against `Display`. Neither field
supports it. On `SetupAuditTrail`, `Section` carries `Nillable, Sort` and `Display` carries
`Nillable, Sort`; only `Action` (`Filter, Sort`), `DelegateUser` (`Filter, Nillable, Sort`) and
`CreatedByContext` (`Filter, Group, Nillable, Sort`) are filterable. So the query that would narrow
180 days of Setup history down to one app is the query the object refuses to run.

**When it occurs.** In the "worked yesterday, nothing was deployed" branch — runbook row 8 — which is
the branch where the audit trail is the only evidence that exists. The failed query gets quietly
replaced by a guess about what someone might have changed.

**How to avoid.** Filter on `CreatedDate` for a window that starts before the first observed failure,
take a bounded page (`ORDER BY CreatedDate DESC LIMIT 500`), and scan `Section` and `Display` in the
returned rows for the app's label. Widen by date, never by predicate. Two related constraints:
`Display` is truncated to nothing useful if you select it without `Action` for context, and the
aggregate restriction on this object is covered by `admin/integration-admin-connected-apps`.

---

## Gotcha 14: "Secret required" is two independent switches, so an app can pass its first exchange and fail every refresh

**What happens.** A public client — a mobile app, a single-page app, a worker that was never given a
secret — completes the initial authorization and then fails on every renewal. The refresh token
policy is fine and the certificate is current, so the search goes to the wrong place. Two separate
`oauthConfig` booleans govern two separate requests. `isConsumerSecretOptional` "instructs the web
server flow not to require the `client_secret` parameter in the access token request" — the
*initial* exchange. `isSecretRequiredForRefreshToken` is a different field with its own default:
"If set to `true` (default), the app's client secret is required in the authorization request of a
refresh token and hybrid refresh token flow." Setting the first one and not the second produces an
app that works exactly once.

**When it occurs.** Whenever an app is configured for a public client by flipping the one setting
whose name mentions the secret being optional. The symptom is indistinguishable from a
refresh-token-policy failure until you look at which of the two requests carried a secret.

**How to avoid.** Set both deliberately and read them as a pair, in that order, when a "works once"
report arrives and `refreshTokenPolicy` turns out to be reasonable. The guide's own note is worth
keeping: for apps that cannot protect a secret "we recommend against selecting this option" on
`isSecretRequiredForRefreshToken`, and it "recommend[s] the user agent flow as a more secure option
than web server flow without the secret" — so the real fix is sometimes a different grant, which is
`integration/oauth-flows-and-connected-apps`.
