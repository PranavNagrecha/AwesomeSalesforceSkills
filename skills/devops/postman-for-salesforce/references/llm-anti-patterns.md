# LLM Anti-Patterns — Postman for Salesforce

Common mistakes AI coding assistants make when generating or advising on Postman setups for Salesforce.

## Anti-Pattern 1: Generating a pre-request script that re-authenticates on every request

**What the LLM generates:** A script that unconditionally calls `/services/oauth2/token`, sets `accessToken`, and runs as the pre-request hook. No cache check, no expiry tracking. The user pastes it in and "it works" — until the per-user login limit is hit.

**Why it happens:** Training data emphasizes the *mechanics* of OAuth (how to build the request) without the operational concern (how to avoid burning the org's login budget). The happy-path example always works in isolation.

**Correct pattern:**

```javascript
// CORRECT — cache by expiry, only refresh when nearing expiration
const cached = pm.environment.get("accessToken");
const exp = parseInt(pm.environment.get("accessTokenExpiry") || "0", 10);
if (cached && Date.now() < exp - 60000) return;
// ... refresh and set both accessToken AND accessTokenExpiry
```

**Detection hint:** Look for any pre-request script that calls `pm.sendRequest` against `/services/oauth2/token` without a preceding `pm.environment.get("accessTokenExpiry")` check. The script must set `accessTokenExpiry` after the refresh.

---

## Anti-Pattern 2: Setting JWT `aud` claim to the token endpoint URL

**What the LLM generates:** A JWT claim object with `aud: "https://login.salesforce.com/services/oauth2/token"`. The token request returns `invalid_grant: audience` and the LLM proposes other unrelated fixes (regenerate the cert, rotate the consumer secret, check IP).

**Why it happens:** Many OAuth flows use the token endpoint URL as the audience. Salesforce JWT bearer is the exception — `aud` is the login URL itself, no path. Training data conflates the two patterns.

**Correct pattern:**

```javascript
// CORRECT — aud is the login URL, no path
const claim = {
  iss: pm.environment.get("clientId"),
  sub: pm.environment.get("username"),
  aud: pm.environment.get("loginUrl"),  // "https://login.salesforce.com" or "https://test.salesforce.com"
  exp: Math.floor(Date.now() / 1000) + 180,
};
```

**Detection hint:** Grep the script for `aud` and check whether the value contains `/services/oauth2/token`. If yes, it's wrong. The right value ends at the host (with optional `:port`), no path.

---

## Anti-Pattern 3: Hard-coding `instanceUrl` and `apiVersion` in every request

**What the LLM generates:** Request URLs like `https://mycompany.my.salesforce.com/services/data/v55.0/sobjects/Account`. No environment variables, no parameterization. When asked "make this work for sandbox too," the LLM duplicates the collection.

**Why it happens:** Concrete URLs are how Salesforce REST API examples appear in docs. The LLM mimics the literal form. Training data examples don't typically demonstrate environment-variable substitution.

**Correct pattern:**

```
{{instanceUrl}}/services/data/{{apiVersion}}/sobjects/Account
```

`instanceUrl` is set by the pre-request script from `data.instance_url` in the OAuth response. `apiVersion` is an environment-level variable.

**Detection hint:** Any URL in the collection JSON containing a literal `https://` followed by `.salesforce.com` or `.force.com` is a bug. Any URL containing `/services/data/v\d+\.\d+/` (literal version) without `{{apiVersion}}` is a bug.

---

## Anti-Pattern 4: Putting per-developer secrets in synced environment variables

**What the LLM generates:** Instructions to populate the JWT private key or client secret as a `Default Value` (synced) instead of a `Current Value` (local) on a shared environment, or guidance to "check 'Secret' on the variable" without flagging that "secret" environment variables are still synced if the workspace is shared.

**Why it happens:** Postman's Vault is a relatively recent feature; older training data doesn't reference it consistently. The "secret type" environment variable feels like the right primitive but doesn't address shared-workspace exposure.

**Correct pattern:** Use Postman Vault for per-developer secrets, referenced via `{{vault:KEY_NAME}}`. Document the required vault keys in the collection's setup runbook. Synced environment variables are for shared-config items only (loginUrl, apiVersion).

**Detection hint:** If the LLM's setup instructions populate a `clientSecret`, `jwtPrivateKey`, or `password` value in the environment editor without mentioning Vault, flag it. The setup should always say "populate this in your Postman Vault as KEY_NAME" for per-developer credentials.

---

## Anti-Pattern 5: Threading state across requests with `pm.variables` (run-scoped) instead of `pm.collectionVariables`

**What the LLM generates:** A multi-step Bulk API 2.0 chain that uses `pm.variables.set("bulkJobId", ...)` and references `{{bulkJobId}}` in the next request. The first run works; the second run fails because `pm.variables` reset between runs.

**Why it happens:** `pm.variables`, `pm.environment.variables`, and `pm.collectionVariables` are all valid scopes; the LLM picks one based on training-data frequency rather than scope semantics. Training data examples often use `pm.environment` even when collection-scope is more appropriate.

**Correct pattern:** For state that should survive across runs *but is collection-specific* (not environment-specific), use `pm.collectionVariables.set(...)`. For state that should reset every run, use `pm.variables.set(...)` (rare in practice).

**Detection hint:** In a multi-step chain, look at the test script's variable-set call. If the chained value (job Id, content URL) is set on `pm.variables` rather than `pm.collectionVariables`, the chain breaks on re-run.

---

## Anti-Pattern 6: Using `POST` for the Bulk API 2.0 upload step

**What the LLM generates:** The LLM produces a chain where step 2 (CSV upload) is `POST` because step 1 was POST and "all the writes look like POST." The job stays in `Open` state and never progresses; the LLM proposes other unrelated fixes.

**Why it happens:** REST API mental model defaults to POST for "send data." Bulk API 2.0's two-stage create-then-upload pattern uses PUT for the upload. Training data underweights API-specific lifecycle quirks.

**Correct pattern:**

```
POST   /jobs/ingest                           # create job (step 1)
PUT    {{bulkContentUrl}}                     # upload CSV (step 2)
PATCH  /jobs/ingest/{{bulkJobId}}             # mark UploadComplete (step 3)
GET    /jobs/ingest/{{bulkJobId}}             # poll status (step 4)
GET    /jobs/ingest/{{bulkJobId}}/results     # pull results (step 5)
```

**Detection hint:** Any Bulk API 2.0 chain where the upload step uses a method other than `PUT` is a bug.
