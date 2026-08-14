---
name: postman-for-salesforce
description: "Use when designing or auditing **Postman collections** that exercise Salesforce APIs — collection structure, OAuth authentication (Web Server, JWT bearer, Username-Password, Client Credentials), pre-request scripts that refresh access tokens, environment variables for sandbox vs prod, request chaining via collection variables, response visualizers, and the official Salesforce Postman collection from the Developer Hub. Triggers: 'set up postman for salesforce', 'postman oauth pre-request script', 'postman jwt bearer salesforce', 'postman environment variables instance url access token', 'salesforce postman collection import', 'postman chained requests bulk api job', 'postman session id refresh script'. NOT for general OAuth-flow design (use `integration/oauth-flows-and-connected-apps`), Apex callouts from inside Salesforce (use `apex/callouts-and-http-integrations`), API performance load testing (use `devops/performance-testing-salesforce`), or running `sf` CLI commands (use `devops/salesforce-cli-automation`)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "how do I set up Postman to call Salesforce REST APIs across sandbox and prod"
  - "Postman pre-request script keeps printing the old access token"
  - "JWT bearer flow Postman script returns invalid_grant from Salesforce"
  - "how do I import the official Salesforce Postman collection"
  - "Postman environment variables for instance url and access token"
  - "chain a Bulk API 2.0 ingest job request in Postman with the upload step"
  - "Postman collection runner against Salesforce Bulk API"
tags:
  - postman
  - api-testing
  - oauth
  - jwt-bearer
  - rest-api
  - bulk-api
  - collection-runner
  - environment-variables
  - pre-request-script
inputs:
  - "auth flow chosen — Web Server (3-legged OAuth), JWT bearer (server-to-server), Username-Password (deprecated), or Client Credentials (Spring '23+)"
  - "target environments — production, named sandboxes, scratch orgs — and how Postman environments map to each"
  - "API surfaces in scope — Data API REST, Tooling API, Bulk API 2.0, Connect API, Pub/Sub gRPC (limited Postman support)"
  - "team distribution model — shared Postman workspace, exported `.postman_collection.json` in source control, or both"
  - "credential storage policy — Postman Vault, environment secrets, or external secret manager"
outputs:
  - "Postman environment(s) per org with `instanceUrl`, `accessToken`, `apiVersion`, and auth-flow-specific secrets"
  - "Pre-request script that refreshes `accessToken` when expired (per-flow shape)"
  - "Collection skeleton matching the team's API surfaces, with sample requests and tests"
  - "Chained-request examples (Bulk API 2.0 job lifecycle, composite REST graph)"
  - "Setup runbook (environment import, secret population, first-request smoke test)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-10
runtime_orphan: true
---

# Postman for Salesforce

Activate when a developer or platform team is **building or auditing a Postman setup that exercises Salesforce APIs** — typically: importing the official Salesforce Postman collection, designing per-environment auth, writing a pre-request script that refreshes the access token, chaining a multi-step Bulk API ingest, or hardening a shared collection against credential leakage. The skill produces a concrete environment shape, an OAuth pre-request script for the chosen flow, and a collection structure that scales from one developer to a shared team workspace.

This skill is not for choosing the OAuth flow itself (that's `integration/oauth-flows-and-connected-apps`), generating Apex callouts (`apex/callouts-and-http-integrations`), running performance tests (`devops/performance-testing-salesforce`), or building external integrations (`integration/rest-api-patterns`). It assumes Postman is the chosen client; auditing whether Postman is the right tool versus `sf api request rest` or curl is out of scope.

---

## Before Starting

Gather this context before opening Postman:

- **OAuth flow choice.** The pre-request script body is entirely flow-dependent. Web Server flow needs an authorization code round-trip; JWT bearer needs a private key and a digital cert assertion; Username-Password (deprecated for new Connected Apps but still in use) needs username, password+token, client id, client secret; Client Credentials (Spring '23+) needs a Connected App configured for the flow with an execution user. Pick before scripting.
- **Environment-per-org or environment-per-team.** A Postman environment holds variables. The most stable pattern is one environment per Salesforce org (DevSandbox, UAT, Prod) so switching orgs is a single dropdown change. Avoid one-environment-with-an-org-toggle — pre-request scripts get unreadable.
- **Secret storage policy.** Postman Vault stores secrets locally, never sync'd to the cloud. Environment "secret" type variables are sync'd if the workspace is shared. For shared team workspaces, use Vault for per-developer client secrets and a placeholder in the environment so the collection imports cleanly for new joiners.
- **Collection ownership model.** Personal collection synced to your account; team collection in a shared workspace; or exported `.postman_collection.json` in source control. The third option is the only auditable one — diff the JSON in PRs and treat the collection as code.
- **API version pinning.** Set `apiVersion` as an environment variable (e.g. `v59.0`) and reference `{{apiVersion}}` in every URL. Hard-coded versions across hundreds of requests are the most common reason Postman setups rot.

---

## Core Concepts

### Environment shape

The minimum environment for Salesforce work:

| Variable | Purpose | Example |
|---|---|---|
| `instanceUrl` | Org-specific base URL after auth | `https://mycompany.my.salesforce.com` |
| `accessToken` | Current OAuth access token (set by pre-request script) | `00D...!ARQAQ...` |
| `apiVersion` | API version for `/services/data/{{apiVersion}}/...` | `v59.0` |
| `loginUrl` | OAuth endpoint (prod or sandbox) | `https://login.salesforce.com` or `https://test.salesforce.com` |
| `clientId` | Connected App consumer key | `3MVG9...` |
| `clientSecret` | Consumer secret (Vault) | (secret) |
| `username` | Service-account username (JWT/Pwd flows) | `integration@example.com.dev` |
| (flow-specific) | `password+token`, `jwtPrivateKey`, etc. | varies |

`instanceUrl` is set by the pre-request script after a successful auth — never hard-coded, because sandbox orgs have unstable subdomains and JWT bearer responses tell you the actual `instance_url`.

### Pre-request script — JWT bearer flow

JWT bearer is the right choice for unattended Postman runs (collection runner, scheduled monitor, CI smoke test). The script signs a JWT with a private key, exchanges it for an access token, and updates the environment.

```javascript
// JWT bearer pre-request script (one of several reference shapes).
// Requires: jsrsasign loaded via pm.sendRequest from a CDN, or Postman's
// built-in CryptoJS for HS256-only flows. Salesforce JWT bearer requires RS256.

const cachedToken = pm.environment.get("accessToken");
const cachedExp = parseInt(pm.environment.get("accessTokenExpiry") || "0", 10);
if (cachedToken && Date.now() < cachedExp - 60000) {
  return; // still valid, skip refresh
}

const jsrsasign = "https://kjur.github.io/jsrsasign/jsrsasign-all-min.js";
pm.sendRequest({ url: jsrsasign, method: "GET" }, (err, res) => {
  eval(res.text());
  const header = { alg: "RS256", typ: "JWT" };
  const claim = {
    iss: pm.environment.get("clientId"),
    sub: pm.environment.get("username"),
    aud: pm.environment.get("loginUrl"),
    exp: Math.floor(Date.now() / 1000) + 180,
  };
  const jwt = KJUR.jws.JWS.sign("RS256", JSON.stringify(header), JSON.stringify(claim), pm.environment.get("jwtPrivateKey"));

  pm.sendRequest({
    url: `${pm.environment.get("loginUrl")}/services/oauth2/token`,
    method: "POST",
    header: { "Content-Type": "application/x-www-form-urlencoded" },
    body: { mode: "urlencoded", urlencoded: [
      { key: "grant_type", value: "urn:ietf:params:oauth:grant-type:jwt-bearer" },
      { key: "assertion", value: jwt },
    ]},
  }, (e, r) => {
    const data = r.json();
    pm.environment.set("accessToken", data.access_token);
    pm.environment.set("instanceUrl", data.instance_url);
    pm.environment.set("accessTokenExpiry", String(Date.now() + 60 * 60 * 1000)); // assume 1h
  });
});
```

Important details:

- **Cache the token by expiry.** Salesforce returns no `expires_in` in the JWT bearer response, so the script computes its own expiry (Salesforce's default access-token TTL is 2h for most setups; assume 1h to be safe).
- **The private key must include the `\n` line breaks** — Postman's environment editor strips them by default. Either store the key as a base64-encoded blob and decode in the script, or paste with literal `\n` and replace inside the script: `key.replace(/\\n/g, "\n")`.
- **`loginUrl` is the audience (`aud`)**, not `https://login.salesforce.com/services/oauth2/token`. Setting `aud` to the token endpoint is a common mistake that returns `invalid_grant`.

### Pre-request script — Web Server flow

For developer-machine usage where browser interaction is acceptable, Postman's built-in OAuth 2.0 helper handles the authorization code round-trip. Configure on the collection: Authorization → Type → OAuth 2.0 → Get New Access Token. Postman opens a browser, the user logs in, and the token returns to Postman. The token is stored in the collection's auth (or per-environment if templated as `{{accessToken}}`).

The Web Server flow has two gotchas in Postman:

1. **Callback URL must match exactly.** Postman's default `https://oauth.pstmn.io/v1/callback` works only if the Connected App lists it. For long-running team setups, register `https://oauth.pstmn.io/v1/callback` plus a localhost variant (`http://localhost:8000/callback`) and document which to use.
2. **`audience` parameter is required for sandbox.** Some sandbox orgs reject the token request unless the `audience` matches the org's My Domain. Postman's OAuth helper exposes `Audience` under "Advanced Options."

### Pre-request script — Client Credentials (Spring '23+)

For unattended server-to-server use without a JWT private key infrastructure, the Client Credentials flow is the simplest. The Connected App must be configured with "Enable Client Credentials Flow" and an explicit "Run As" execution user.

```javascript
const cachedToken = pm.environment.get("accessToken");
const cachedExp = parseInt(pm.environment.get("accessTokenExpiry") || "0", 10);
if (cachedToken && Date.now() < cachedExp - 60000) return;

pm.sendRequest({
  url: `${pm.environment.get("loginUrl")}/services/oauth2/token`,
  method: "POST",
  header: { "Content-Type": "application/x-www-form-urlencoded" },
  body: { mode: "urlencoded", urlencoded: [
    { key: "grant_type", value: "client_credentials" },
    { key: "client_id", value: pm.environment.get("clientId") },
    { key: "client_secret", value: pm.environment.get("clientSecret") },
  ]},
}, (err, res) => {
  const data = res.json();
  pm.environment.set("accessToken", data.access_token);
  pm.environment.set("instanceUrl", data.instance_url);
  pm.environment.set("accessTokenExpiry", String(Date.now() + 30 * 60 * 1000));
});
```

The execution-user model is the differentiator: every API call made with this token runs *as the configured execution user*, not as the service principal that "owns" the token. Permission audits should follow that user, not the Connected App.

### Request chaining and the collection runner

Postman tests can stash response data into environment or collection variables for the next request:

```javascript
// In the "Tests" tab of a Bulk API 2.0 "Create Job" request:
pm.test("job created", () => pm.expect(pm.response.code).to.eql(200));
const job = pm.response.json();
pm.collectionVariables.set("bulkJobId", job.id);
pm.collectionVariables.set("bulkContentUrl", job.contentUrl);
```

The next request in the collection (`Upload Job Data`) references `{{bulkJobId}}` in its URL and sends the CSV as the body. The collection runner executes the requests in order, threading state.

`pm.collectionVariables` are scoped to the collection and survive across runs; `pm.variables` are run-scoped and reset between runs. For a multi-step flow that needs to be re-runnable, use collection variables.

### Postman Vault and shared workspaces

When a team shares a Postman workspace, every "secret" environment variable is sync'd to all members. For per-developer credentials (client secrets, JWT private keys), this is wrong: each developer should hold their own.

Postman Vault is the local-only, per-user secret store. Reference vault secrets in the collection with `{{vault:KEY_NAME}}`. The collection commits the *reference* (which is safe to share); each developer populates their own vault on first use. Document the required vault keys in the collection's README request.

---

## Common Patterns

### Pattern 1 — Token-refresh pre-request script with caching

**When to use:** Any Postman collection that hits Salesforce, regardless of flow.

**How it works:** Pre-request script reads cached `accessToken` + `accessTokenExpiry` from environment. If unexpired, returns. Otherwise refreshes per the chosen flow and updates both. Subsequent requests in the same Postman session reuse the cached token until it nears expiry.

**Why not the alternative:** Re-authenticating on every request triples API call latency for any non-trivial collection run, and burns the org's daily login limit (limit varies by edition; Spring '25 baseline is 5,000 successful logins per 24h per user).

### Pattern 2 — Bulk API 2.0 ingest job lifecycle

**When to use:** Loading a CSV into Salesforce via Bulk API 2.0 from Postman, often for ad-hoc data fixes or initial smoke tests.

**How it works:** Five chained requests in the collection:

1. `POST /services/data/{{apiVersion}}/jobs/ingest` — body specifies `object`, `operation`, `contentType=CSV`. Test stashes `id` and `contentUrl`.
2. `PUT {{bulkContentUrl}}` (or the relative path) — body is the CSV. `Content-Type: text/csv`.
3. `PATCH /services/data/{{apiVersion}}/jobs/ingest/{{bulkJobId}}` body `{"state": "UploadComplete"}`.
4. `GET /services/data/{{apiVersion}}/jobs/ingest/{{bulkJobId}}` — poll for `state` ∈ `JobComplete` / `Failed` / `Aborted`.
5. `GET /services/data/{{apiVersion}}/jobs/ingest/{{bulkJobId}}/successfulResults` (and `/failedResults`) — pull row-level outcomes.

The collection runner with a delay setting handles step 4's polling.

**Why not the alternative:** `sf data import bulk` is more ergonomic for one-shots, but Postman's per-request visibility is unbeatable when debugging why a specific job leg fails (auth, malformed CSV, FLS error on a row).

### Pattern 3 — Composite REST graph

**When to use:** Need to insert an Account, Contact, and Opportunity in a single transactional call.

**How it works:** `POST /services/data/{{apiVersion}}/composite/graph/` with a body that lists the three sub-requests, each with a `referenceId`. Subsequent sub-requests reference predecessor outputs via `@{ref.body.id}` syntax. The whole graph commits or rolls back as one transaction.

```json
{
  "graphs": [{
    "graphId": "g1",
    "compositeRequest": [
      {"method": "POST", "url": "/services/data/v59.0/sobjects/Account", "referenceId": "AccRef", "body": {"Name": "Acme"}},
      {"method": "POST", "url": "/services/data/v59.0/sobjects/Contact", "referenceId": "ConRef", "body": {"LastName": "Doe", "AccountId": "@{AccRef.id}"}}
    ]
  }]
}
```

**Why not the alternative:** Three separate Postman requests with chained collection variables work but aren't atomic — a failure on the third leaves the first two committed. Composite graph is one round trip and one transaction.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One developer, ad-hoc API exploration | Personal workspace + Web Server OAuth helper | Browser flow is fastest for iterative dev |
| Team-shared collection in source control | Export `.postman_collection.json`, diff in PRs, Vault for secrets | Auditable; new joiners populate Vault on import |
| Unattended runs (CI smoke, scheduled monitor) | JWT bearer or Client Credentials with cached token | No browser; deterministic; cache avoids login-limit churn |
| Cross-org work (sandbox + prod) | One environment per org, dropdown switch | Pre-request script stays simple |
| Bulk data load from CSV | Bulk API 2.0 chained collection | Per-request visibility for debugging |
| Multi-record transactional insert | Composite Graph (single request) | Atomic semantics |
| Streaming/Pub/Sub work | Skip Postman; use a gRPC client | Postman gRPC is limited and Salesforce Pub/Sub auth is non-trivial |
| Audit log of who hit what API | Salesforce-side Login History + Event Monitoring | Postman has no shared-history server |
| Need to re-run a collection deterministically | `pm.collectionVariables` + collection runner with delay | Variables survive across runs; delay paces async polls |

---

## Recommended Workflow

1. Choose the OAuth flow per the requirements (interactive vs unattended, server-side credentials available, browser allowed). Document the choice in the collection README.
2. Configure the Connected App in Salesforce: scopes (`api`, `refresh_token`, `openid` as needed), callback URL (Web Server only), policy "Admin approved users are pre-authorized," IP restrictions if applicable.
3. Wire auth into the collection, never into individual requests:
   - Create the environment shape — `instanceUrl`, `accessToken`, `apiVersion`, `loginUrl`, `clientId`, `clientSecret` (Vault), and flow-specific keys (`username`, `jwtPrivateKey`, etc.).
   - Write the pre-request script for the chosen flow at the **collection level** (not per-request). It runs before every request and refreshes the token only when needed.
4. Build the collection structure and make every request assert something:
   - Folder per API surface (Data, Tooling, Bulk, Connect), folder per workflow (Bulk Job Lifecycle, Composite Graph). Each request uses `{{instanceUrl}}/services/data/{{apiVersion}}/...`.
   - For each request, write at least one `pm.test` assertion (status code, key field present). Without tests, a successful 200 hides response-body bugs.
5. Make the collection reproducible on someone else's machine:
   - Document the environment-variable population steps in a "00 — Setup" markdown request at the top of the collection (Postman supports markdown in request descriptions).
   - Export the collection JSON and commit to source control. Document the export ritual (Postman's auto-sync vs manual export) so the source-controlled copy doesn't drift.
6. Run the full collection via the collection runner against a sandbox before merging changes. The runner enforces ordering and surfaces broken chains.
7. For shared workspaces, audit Vault usage on every onboarding — a developer who imports the collection without populating Vault sees broken auth, not "missing secret" errors.

---

## Review Checklist

Run through these before merging Postman setup changes:

- [ ] Pre-request script lives at collection level, not duplicated per request
- [ ] `accessToken` is cached with an `accessTokenExpiry` and the script skips refresh when valid
- [ ] All URLs reference `{{instanceUrl}}` and `{{apiVersion}}` — no hard-coded subdomains or version numbers
- [ ] Per-developer secrets (client secret, JWT private key, username password+token) live in Postman Vault, not synced environment variables
- [ ] Collection JSON is exported and committed to source control with a documented export ritual
- [ ] Each request has at least one `pm.test` assertion
- [ ] Multi-step flows use `pm.collectionVariables` (re-runnable), not `pm.variables` (run-scoped)
- [ ] `loginUrl` is parameterized per environment (prod vs sandbox)
- [ ] Connected App callback URL matches what Postman's OAuth helper sends (`https://oauth.pstmn.io/v1/callback` by default)
- [ ] Setup runbook is in a markdown request at the top of the collection
- [ ] Bulk API 2.0 chained flows handle the `JobComplete` / `Failed` / `Aborted` terminal states explicitly

---

## Salesforce-Specific Gotchas

Non-obvious behaviors that bite Postman users hitting Salesforce:

1. **`instance_url` from the OAuth response is authoritative; don't hard-code it.** Sandbox subdomains can change after refresh; My Domain rebrands change the pod-prefixed URL. Hard-coded `https://na123.my.salesforce.com` works until it doesn't.
2. **Salesforce's daily login-attempt limit is per-user, not per-IP.** A pre-request script that refreshes on every request burns through 5,000 logins/day fast. Token caching with expiry is mandatory, not optional.
3. **JWT bearer's `aud` claim must be the login URL, not the token endpoint.** `aud: https://login.salesforce.com` works; `aud: https://login.salesforce.com/services/oauth2/token` returns `invalid_grant: audience` with no further detail.
4. **Connected App "IP Relaxation" defaults to `Enforce IP restrictions` if profile-level IP ranges exist.** If Postman runs from a developer's home IP that the user's profile doesn't permit, JWT bearer returns `invalid_grant` and Web Server bounces back to login. The fix is "Relax IP restrictions" on the Connected App, not a per-user trusted-IP edit.
5. **Postman's `{{variable}}` substitution does NOT happen inside JSON bodies for *array values* in the visual editor.** The text editor handles them correctly. Switching from Body → JSON visual to Body → Raw JSON resolves substitution issues that look like collection-runner bugs.
6. **The Bulk API 2.0 "upload" step is a `PUT` to `{{contentUrl}}`, not `POST`.** Using `POST` returns a 400 with a generic "expected PUT" error. The path is *relative* in the response — Postman concatenates `{{instanceUrl}}{{bulkContentUrl}}`.
7. **`Content-Type: application/json; charset=UTF-8` works; bare `application/json` works; `application/json;charset=utf-8` (no space, lowercase) sometimes returns 415 from older API versions.** Stick to the canonical form with the space and uppercase UTF-8.
8. **Postman's collection-level "Authorization" tab applies after the pre-request script.** If the pre-request script sets `accessToken` and the collection's Auth is also "Bearer Token: `{{accessToken}}`," both run — but the collection-level Auth wins. Centralize on one or the other; mixing produces confusing 401s when one path is mutated.
9. **Vault secrets are local-only and **not** included in the collection export.** A collection committed to source control with `{{vault:CLIENT_SECRET}}` references in the auth header runs on the developer's machine but breaks in CI without a different secret-injection mechanism.
10. **`response.json()` throws when the body isn't JSON, including on Salesforce's HTML error pages from auth misconfiguration.** Wrap parses in try/catch in test scripts; the actual error message lives in the HTML body, not in the JSON exception.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Postman environment(s) | One per Salesforce org; covers `instanceUrl`, `accessToken`, `apiVersion`, `loginUrl`, flow-specific secrets |
| Pre-request script | Flow-specific token refresh with cache-by-expiry; lives at collection level |
| Collection JSON | Exported `.postman_collection.json` checked into source control |
| Setup runbook | Markdown request at the top of the collection: vault keys to populate, env import order, smoke-test request |
| Chained-request example(s) | At minimum the Bulk API 2.0 lifecycle and one composite REST graph |

---

## Related Skills

- integration/oauth-flows-and-connected-apps — for choosing among Web Server, JWT bearer, Username-Password, Client Credentials before building the Postman script
- integration/named-credentials-setup — when the long-term home for the same calls is Salesforce-side via a Named Credential, not Postman
- integration/rest-api-patterns — for general Salesforce REST API usage; Postman is the test client, this skill the design surface
- integration/bulk-api-2-patterns — for the underlying Bulk API 2.0 design covered by Pattern 2
- integration/composite-api-patterns — for the underlying composite-REST design covered by Pattern 3
- devops/salesforce-cli-automation — when the right answer is `sf api request rest` instead of Postman
