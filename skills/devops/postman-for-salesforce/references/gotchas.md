# Gotchas — Postman for Salesforce

Non-obvious Salesforce platform behaviors that bite Postman users. The list focuses on issues that cost real debugging time.

## Gotcha 1: `instance_url` from OAuth is authoritative — never hard-code the org subdomain

**What happens:** A request returns `INVALID_SESSION_ID` even though the access token was just refreshed seconds ago. The token is valid; the URL it's hitting is wrong because the org's `My Domain` has a different subdomain than what's hard-coded.

**When it occurs:** Sandbox refresh, My Domain rebrand, or pod migration changes the subdomain. Hard-coded `https://orgname.my.salesforce.com` (or worse, the legacy `na123.my.salesforce.com` pattern) silently rots.

**How to avoid:** Always set `instanceUrl` from `data.instance_url` in the OAuth response inside the pre-request script. Reference `{{instanceUrl}}` in every request URL. Never paste the subdomain into the collection.

---

## Gotcha 2: Per-user 5,000-logins/24h limit is exhausted by per-request token refresh

**What happens:** Around 4 PM, every request fails with `INVALID_LOGIN: Your daily logins have been used up`. The team rotates to a different integration user; that user is exhausted by 9 AM the next day. Production smoke tests fail.

**When it occurs:** Pre-request script re-authenticates on every request without caching. A 150-request collection run = 150 logins. Four runs per day = 600 logins. Five developers per project = 3,000 logins. Add ad-hoc work and the limit is hit fast.

**How to avoid:** Cache the access token with an explicit `accessTokenExpiry` (use 1h to be safe; Salesforce default is typically 2h but the Connected App can override). Skip the refresh when `cachedExp - 60000 > Date.now()`. One token covers one developer's day.

---

## Gotcha 3: JWT bearer `aud` must be the login URL, not the token endpoint

**What happens:** JWT bearer returns `invalid_grant: audience` with no further detail. Token never issues.

**When it occurs:** Confusing the token-exchange endpoint URL with the JWT audience claim. The URL the request POSTs to is `https://login.salesforce.com/services/oauth2/token`; the `aud` claim inside the JWT is `https://login.salesforce.com` (no path).

**How to avoid:** In the JWT claim object, `aud: pm.environment.get("loginUrl")` where `loginUrl` is `https://login.salesforce.com` (or `https://test.salesforce.com` for sandbox). The token-exchange URL is built from `loginUrl + '/services/oauth2/token'`.

---

## Gotcha 4: Connected App "IP Relaxation" defaults to enforcing profile IP ranges

**What happens:** JWT bearer or Web Server returns `invalid_grant` from a developer's home IP, but works from the office VPN. Web Server flow seems to "loop back to login" instead of issuing the token.

**When it occurs:** The user's profile has Login IP Ranges configured, and the Connected App is set to "Enforce IP restrictions." Postman's outbound IP isn't in the profile range.

**How to avoid:** On the Connected App, set "IP Relaxation" to "Relax IP restrictions" (the right answer for Connected Apps that authenticate users outside the office). Editing the user's profile's IP ranges as a workaround opens a wider security hole and should be avoided.

---

## Gotcha 5: Bulk API 2.0 upload step is `PUT`, not `POST`

**What happens:** Step 2 of the Bulk API 2.0 chain returns 400 with a generic "expected PUT" error message. The job stays in `Open` state and never makes progress.

**When it occurs:** Defaulting to `POST` because steps 1 and 3 are POST/PATCH. Step 2 (the actual CSV upload) is `PUT`.

**How to avoid:** Verify each request method against the Bulk API 2.0 reference. Memorize the lifecycle: POST job → PUT CSV → PATCH UploadComplete → GET poll → GET results. The CSV upload is the only PUT.

---

## Gotcha 6: Postman's JSON visual editor doesn't substitute `{{variable}}` inside arrays

**What happens:** A POST body with `"ids": ["{{accountId}}", "{{contactId}}"]` in the visual JSON editor sends the literal string `"{{accountId}}"` instead of the substituted Id. The receiving endpoint returns a malformed-Id error.

**When it occurs:** Building a request body in the visual JSON editor (Body → JSON, the structured form). Postman's substitution pre-processes the raw text body but the visual editor stores values as a structured tree where the variable token isn't recognized.

**How to avoid:** Use the raw JSON body editor (Body → Raw → JSON). Substitution works correctly there. If you must use the visual editor, only put variables in scalar fields, never inside arrays or nested objects.

---

## Gotcha 7: Postman Vault secrets are local-only and not exported with the collection

**What happens:** A collection that runs cleanly on a developer's laptop fails in CI (or for a teammate who imported the JSON) with `invalid_grant: invalid client credentials`. The collection JSON references `{{vault:CLIENT_SECRET}}`; CI's Postman doesn't have that vault key populated.

**When it occurs:** Forgetting that Vault is per-user, per-machine. Newman (the Postman CLI for CI) has its own credential mechanism (env vars passed via `-e`/`--env-var`), which doesn't read Postman Vault.

**How to avoid:** Document required Vault keys in the collection's setup runbook. For CI, use Newman's `--env-var` flag to inject secrets from the CI's secret store: `newman run mycoll.json -e env.json --env-var "CLIENT_SECRET=$CI_CLIENT_SECRET"`. Don't try to "fix" the local-only nature of Vault — that's the feature.

---

## Gotcha 8: Salesforce HTML error pages break `response.json()` in test scripts

**What happens:** A test script does `const data = pm.response.json();` and the run fails with `JSONError: Unexpected token < in JSON at position 0`. The actual error (auth misconfiguration, IP block, login URL wrong) is in the HTML body that the script ignored.

**When it occurs:** Auth failures often return HTML login pages instead of JSON. Network-level redirects (proxies, IP blocks) return HTML.

**How to avoid:** Wrap parses in try/catch and inspect `pm.response.text()` on failure: `try { data = pm.response.json(); } catch (e) { console.error("non-JSON response:", pm.response.text().substring(0, 500)); throw e; }`. Logging the first 500 characters of HTML usually reveals the real issue.

---

## Gotcha 9: Collection-level Authorization tab clobbers the pre-request-set token

**What happens:** A pre-request script that successfully refreshes `accessToken` is followed by a request that sends a stale token. Spelunking shows the collection-level Authorization tab is set to "Bearer Token: `{{accessToken}}`" — which evaluates *after* the pre-request script… but caches the value at request creation time on some Postman versions, leading to a stale read.

**When it occurs:** Mixing two auth-injection mechanisms (pre-request script setting headers manually + collection-level Auth tab). The two paths fight each other.

**How to avoid:** Pick one. The cleanest is collection-level Authorization → Bearer Token → `{{accessToken}}` and let the pre-request script update only the variable. Don't manually set the `Authorization` header in the pre-request script. That keeps the data flow one-directional.

---

## Gotcha 10: Client Credentials flow runs as the Connected App's "Run As" user, not the principal

**What happens:** A Postman request authenticated via Client Credentials creates records owned by a user the team didn't expect. CRUD/FLS audits look at the wrong user. Sharing rules apply differently than the dev expected.

**When it occurs:** Confusing the Connected App's identity (its consumer key / secret) with the user identity the API calls execute as. Client Credentials Flow requires the Connected App to specify a "Run As" execution user; that user is who the calls run as.

**How to avoid:** Document the "Run As" user in the collection's setup runbook. Audit that user's profile and permission sets — they govern what every Client-Credentials-authenticated request can do. If you need different operations to run as different users, you need different Connected Apps (or a different flow like JWT bearer that lets the `sub` claim choose the user per call).
