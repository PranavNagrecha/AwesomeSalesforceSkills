# Gotchas — Connected App Troubleshooting

Non-obvious Connected App behaviors.

---

## Gotcha 1: Default Refresh Token Policy in older orgs is "Immediately expire"

**What happens.** Integration works for one access-token
lifetime, then dies on first refresh.

**How to avoid.** Set Refresh Token Policy = "Refresh token is
valid until revoked" for server-to-server integrations. Pair
with credential-rotation discipline.

---

## Gotcha 2: `invalid_grant` is overloaded — five different causes

**What happens.** Single error code maps to: refresh token
expired, refresh token revoked, refresh token never issued
(missing scope), wrong user, certificate expired (JWT).

**How to avoid.** Always check Login History to disambiguate.
The `Status` column there often shows clearer cause.

---

## Gotcha 3: User assignment for "Admin approved" mode is non-obvious

**What happens.** Connected App's "Permitted Users" = "Admin
approved users are pre-authorized". User OAuth flow fails with
`OAUTH_APP_BLOCKED`. Admin sees no error setting up the app.

**How to avoid.** Profile or Permission Set must include the
Connected App in its "Connected App Access" entries. Document
this as part of the rollout checklist.

---

## Gotcha 4: `redirect_uri` mismatch is character-exact

**What happens.** Connected App's Callback URL is
`https://app.example.com/oauth/callback` but client sends
`https://app.example.com/oauth/callback/`. Trailing slash
mismatch fails with `redirect_uri_mismatch`.

**How to avoid.** Match the callback URL exactly. Add multiple
URLs to the Connected App's Callback URL list (one per line) if
the client may send variants.

---

## Gotcha 5: JWT `sub` claim must be the Username, not Email

**What happens.** Client constructs JWT with `sub = user@example.com`
(the user's Email). JWT Bearer flow fails with `invalid_grant`.
Username might be `user@example.com.acmesandbox` (Salesforce
appended the org suffix).

**How to avoid.** Use the User.Username field, exactly as it
appears in Setup → Users.

---

## Gotcha 6: Connected App admin-block is separate from disabling OAuth

**What happens.** Admin sets the Connected App to "Block"
status while reviewing access. The app itself is still defined
and configured; OAuth flows fail with `OAUTH_APP_BLOCKED`.

**How to avoid.** Setup → Apps → Connected Apps OAuth Usage —
check if the app is blocked. Unblock if appropriate.

---

## Gotcha 7: IP Relaxation interacts with the user's profile IP range

**What happens.** Connected App is "Relax IP restrictions" but
the user's profile has a tight Login IP Range. Both must permit
the caller; the union doesn't apply, the user's profile does.

**How to avoid.** Verify both layers. For server-to-server
integrations, the integration user's profile should NOT have a
restrictive IP range that conflicts with the Connected App's
Relax setting.

---

## Gotcha 8: Resetting the Consumer Secret breaks every active session

**What happens.** Admin resets the Connected App's Consumer
Secret in Setup. Every integration using that app fails until
the new secret is propagated.

**How to avoid.** Treat secret resets as planned changes.
Coordinate with every integration using the app; rotate
secrets via a credential manager that propagates atomically.

---

## Gotcha 9: Connected App metadata deploys with sandbox-shaped Consumer Key

**What happens.** Connected App deployed via metadata; the
deployed Connected App has a NEW Consumer Key (the sandbox key
isn't preserved). Integration was configured with sandbox key.

**How to avoid.** After Connected App deploy to a new env,
fetch the Consumer Key from Setup and update the integration's
config. The key is environment-specific.

---

## Gotcha 10: `Username-Password` flow is deprecated for most uses

**What happens.** New integration uses Username-Password OAuth
flow; admin gets a warning email about deprecation.

**How to avoid.** Use JWT Bearer (server-to-server) or Web
Server flow (interactive) instead. Username-Password only for
legacy systems being actively migrated; not for new code.
