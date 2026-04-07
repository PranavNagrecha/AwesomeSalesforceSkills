# LLM Anti-Patterns — Headless Experience Cloud

Common mistakes AI coding assistants make when generating or advising on Salesforce CMS headless delivery integrations. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing CMS Connect with the Headless Delivery API

**What the LLM generates:** When asked "how do I deliver Salesforce CMS content to a React app," the LLM instructs the developer to configure a CMS Connect source (Setup > CMS Connect) and set up an external CMS adapter. Alternatively, when asked to pull WordPress content into an Experience Builder page, the LLM points at the Connect REST API delivery endpoint.

**Why it happens:** Both features appear under "CMS" and "Experience Cloud" in training data. The LLM does not reliably distinguish the direction of content flow (inbound vs outbound) and conflates the two feature names.

**Correct pattern:**

```
Headless delivery API → SF CMS content going OUT to an external frontend
CMS Connect → External CMS content (WordPress, Contentful) coming IN to Experience Builder pages

For React/mobile/static apps consuming Salesforce-authored content:
  GET /services/data/{version}/connect/cms/delivery/channels/{channelId}/contents

For Experience Builder pages showing 3rd-party CMS content:
  Setup > CMS Connect source configuration
```

**Detection hint:** If the LLM response mentions "CMS Connect source" or "external CMS adapter" in the context of delivering SF CMS content to a React app, the response is wrong. If the response references the `/connect/cms/delivery/` endpoint in the context of pulling WordPress into Experience Builder, the response is wrong.

---

## Anti-Pattern 2: Not Setting Up CORS for the External Frontend

**What the LLM generates:** A complete React fetch example that calls the delivery endpoint — with no mention of CORS setup. The LLM treats CORS as an optional note or omits it entirely.

**Why it happens:** LLMs optimistically generate code that looks syntactically correct and complete. CORS is a server-side configuration step in Salesforce Setup, not a code change — so it falls outside the code generation frame and gets omitted.

**Correct pattern:**

```
Before writing any frontend fetch code:
1. Setup > Security > CORS
2. Add the frontend origin (e.g., https://www.mysite.com)
3. Add http://localhost:{port} for local development
4. No wildcard (*) — each origin must be listed explicitly

Without this, all browser fetch calls to the delivery endpoint will fail
with a CORS preflight error before Salesforce ever receives the request.
```

**Detection hint:** Any code example that calls `fetch('https://{org}.my.salesforce.com/services/data/.../connect/cms/delivery/...')` from a browser context without a corresponding CORS configuration step is missing a critical requirement.

---

## Anti-Pattern 3: Missing OAuth Scope for Authenticated Channels

**What the LLM generates:** A connected app configuration with only the `openid` scope, or with `full` (overly permissive). The LLM either under-scopes (access token lacks permission to call the delivery API) or over-scopes (violates least-privilege).

**Why it happens:** LLMs default to common OAuth scope patterns from generic examples. The correct minimum scope for the CMS delivery API on authenticated channels (`api` or `chatter_api`) is not prominently featured in most training examples.

**Correct pattern:**

```
Connected App OAuth Scopes for authenticated CMS channel access:
  Minimum: api
  Alternative minimum: chatter_api
  Add: refresh_token, offline_access (if long-lived token refresh is needed)
  Do NOT use: full (unnecessary privilege)
  Do NOT use: openid alone (insufficient for delivery API calls)
```

**Detection hint:** If the LLM recommends `full` scope without a rationale, or recommends `openid` only, the scope configuration is wrong. Flag any connected app configuration that does not mention `api` or `chatter_api` for an authenticated channel integration.

---

## Anti-Pattern 4: Treating Channel ID as Static or Guessing Its Value

**What the LLM generates:** Code with a hardcoded channel ID in the source (often a placeholder that looks like a real ID, e.g., `0apXx0000000001AAA`), with no instruction to retrieve the actual ID from the org. Some LLM responses state the channel ID can be found in "the Experience Cloud site URL" or "the CMS Setup page" — neither of which is accurate.

**Why it happens:** Channel IDs are org-specific record IDs that the LLM cannot know. Rather than producing broken code with an obvious placeholder, the LLM sometimes invents a plausible-looking value or points to a UI location that does not show the ID.

**Correct pattern:**

```
To retrieve the channel ID:
  GET /services/data/v62.0/connect/cms/delivery/channels

Use Workbench, Salesforce CLI, or Postman with org credentials.
The response includes channelId for each configured channel.

Store the retrieved value as an environment variable:
  REACT_APP_CMS_CHANNEL_ID=0apXx0000004C3KIAU  (example; your value will differ)

Channel IDs differ between production, sandboxes, and scratch orgs.
Never hardcode them in source code.
```

**Detection hint:** Any code that uses a hardcoded string as the channel ID path segment without an instruction to retrieve it from the org is wrong. Look for patterns like `/channels/0ap.../contents` with no mention of API retrieval or environment variables.

---

## Anti-Pattern 5: Fetching All Content Without Pagination

**What the LLM generates:** A fetch call with no `pageSize` or `page` parameters, or a while-loop that iterates through all pages to collect every content item into a single in-memory array before returning anything to the UI.

**Why it happens:** LLMs often generate the simplest code that retrieves "all" items, modeling the pattern on in-memory collections. Pagination is added as an afterthought or omitted from examples that are focused on demonstrating the API call structure.

**Correct pattern:**

```javascript
// Paginate using nextPageUrl from the response
async function fetchContentPage(channelId, contentType, pageSize = 10, page = 1) {
  const url = new URL(`${SF_INSTANCE}/services/data/${API_VERSION}/connect/cms/delivery/channels/${channelId}/contents`);
  url.searchParams.set('contentTypeName', contentType);
  url.searchParams.set('pageSize', String(pageSize));
  url.searchParams.set('page', String(page));

  const response = await fetch(url.toString());
  const data = await response.json();

  return {
    items: data.items ?? [],
    nextPageUrl: data.nextPageUrl ?? null,
    totalCount: data.total ?? 0,
  };
}
// Call iteratively using nextPageUrl; do not fetch all pages in one call for display use cases
```

**Detection hint:** Any fetch example that does not pass `pageSize` to the delivery endpoint, or that collects all items from all pages before returning, is not production-safe. Flag implementations that ignore `nextPageUrl` in the response.

---

## Anti-Pattern 6: Omitting Token Refresh for Authenticated Channels

**What the LLM generates:** OAuth token acquisition code (client credentials or web server flow) that obtains an access token and stores it indefinitely, with no expiry handling or refresh logic.

**Why it happens:** OAuth examples in training data frequently show only the happy-path token acquisition. Refresh token handling is often treated as an "advanced" topic and omitted from basic examples.

**Correct pattern:**

```
Access tokens from Salesforce OAuth expire after ~2 hours by default.
On a 401 response from the delivery API:
  1. Use the refresh_token grant to obtain a new access_token
  2. Retry the original request with the new token
  3. If refresh also fails (expired refresh token), redirect to re-authentication

Connected App must include refresh_token and offline_access scopes for long-lived sessions.
```

**Detection hint:** Any authenticated channel integration that does not handle the 401 response case and does not show token refresh logic is incomplete. Look for missing `refresh_token` grant handling or missing expiry-based proactive refresh.
