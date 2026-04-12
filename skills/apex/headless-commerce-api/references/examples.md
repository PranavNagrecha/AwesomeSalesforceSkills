# Examples — Headless Commerce API (SCAPI)

## Example 1: Guest Token Acquisition via SLAS PKCE in JavaScript

**Context:** A Next.js storefront needs to initialize a guest shopping session before calling any Shopper API. The application has no existing session for the visitor.

**Problem:** Without a valid SLAS access token, all Shopper API calls return 401. Developers migrating from OCAPI try to call the old Account Manager session endpoint or reuse an Account Manager client ID, neither of which works with SCAPI. Some developers attempt to store the access token in `localStorage` for convenience, creating an XSS exposure vector.

**Solution:**

```javascript
// guestSession.js — SLAS PKCE guest token flow (no client secret sent from browser)
import crypto from 'crypto';

const SLAS_BASE = `https://${process.env.SHORT_CODE}.api.commercecloud.salesforce.com`;
const ORG_ID    = process.env.ORG_ID;
const CLIENT_ID = process.env.SLAS_CLIENT_ID;
const SITE_ID   = process.env.SITE_ID;

function generateCodeVerifier() {
  // RFC 7636: 43–128 URL-safe Base64 chars [A-Za-z0-9\-._~]
  // SLAS strictly enforces this range — values shorter than 43 chars return 400
  return crypto
    .randomBytes(64)
    .toString('base64url')
    .slice(0, 96); // 96 chars — well within the 43–128 required range
}

async function computeCodeChallenge(verifier) {
  const hash = crypto.createHash('sha256').update(verifier).digest();
  return hash.toString('base64url');
}

export async function acquireGuestToken() {
  const codeVerifier  = generateCodeVerifier();
  const codeChallenge = await computeCodeChallenge(codeVerifier);

  const params = new URLSearchParams({
    grant_type:     'client_credentials',
    client_id:      CLIENT_ID,
    channel_id:     SITE_ID,
    code_challenge: codeChallenge,
  });

  const response = await fetch(
    `${SLAS_BASE}/shopper/auth/v1/organizations/${ORG_ID}/oauth2/token`,
    {
      method:  'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body:    params.toString(),
    }
  );

  if (!response.ok) {
    const err = await response.json();
    throw new Error(`SLAS guest token failed: ${err.error} — ${err.error_description}`);
  }

  const { access_token, refresh_token, expires_in } = await response.json();
  // access_token: store in memory only — never localStorage
  // refresh_token: set as httpOnly cookie server-side to prevent JS access
  return { access_token, refresh_token, expires_in };
}
```

**Why it works:** The PKCE code verifier is generated within the 43–128 character range that SLAS strictly validates. The access token is returned to the caller for in-memory use only; the refresh token is handled by the server layer as an `httpOnly` cookie, preventing JavaScript from reading it in the event of an XSS attack. No client secret is transmitted from the browser, which is correct for public clients.

---

## Example 2: Resilient SCAPI Fetch Wrapper for Load-Shedding (HTTP 503)

**Context:** A high-traffic B2C storefront calls `shopper-search` frequently during peak periods. During flash sale events, SCAPI begins returning HTTP 503 responses with a `Retry-After` header as server load exceeds 90% capacity.

**Problem:** Developers unfamiliar with SCAPI's load-shedding model treat 503 as a permanent error — either throwing immediately or retrying without delay. Throwing immediately surfaces a false "product unavailable" page to all shoppers during a live sale. Retrying without reading `Retry-After` compounds server load across thousands of concurrent clients, worsening the 503 event.

**Solution:**

```javascript
// scapiClient.js — fetch wrapper with load-shedding retry logic
const MAX_RETRIES = 3;

export async function scapiFetch(url, options = {}) {
  let lastError;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const response = await fetch(url, options);

    if (response.ok) return response;

    if (response.status === 503) {
      // SCAPI load-shedding — not a rate-limit (429). Retry-After is authoritative.
      const retryAfterSec = parseInt(response.headers.get('Retry-After') ?? '2', 10);
      const jitterMs      = Math.random() * 500; // 0–500 ms jitter prevents thundering herd
      const waitMs        = retryAfterSec * 1000 + jitterMs;

      if (attempt < MAX_RETRIES) {
        await new Promise((resolve) => setTimeout(resolve, waitMs));
        continue; // retry — 503 does NOT invalidate the JWT
      }

      lastError        = new Error(`SCAPI unavailable after ${MAX_RETRIES} retries`);
      lastError.status = 503;
      break;
    }

    // Non-503 errors (400, 401, 404, etc.) — surface immediately; retrying won't help
    const body   = await response.json().catch(() => ({}));
    const err    = new Error(`SCAPI ${response.status}: ${body.title ?? response.statusText}`);
    err.status   = response.status;
    throw err;
  }

  throw lastError;
}
```

**Why it works:** The wrapper reads `Retry-After` from the SCAPI response header — the authoritative wait time provided by the server — and adds randomized jitter to prevent synchronized retry storms across concurrent clients. Only 503 triggers retries; other status codes surface immediately because they indicate a request problem that retrying will not resolve. The existing JWT access token remains valid across 503s — no re-authentication is needed.

---

## Example 3: Commerce SDK React Provider and Hook Setup for Shopper Search

**Context:** A Next.js storefront uses Commerce SDK React to manage Shopper API calls without manually implementing PKCE, token refresh, or response deserialization.

**Problem:** Developers sometimes configure `CommerceApiProvider` at the page level instead of the application root. This destroys and re-initializes the internal `react-query` client and SLAS token state on every route change, causing unnecessary token re-acquisitions and flash-of-loading states on navigation.

**Solution:**

```jsx
// _app.jsx — configure CommerceApiProvider once at the application root
import { CommerceApiProvider } from '@salesforce/commerce-sdk-react';

const commerceConfig = {
  clientId:       process.env.NEXT_PUBLIC_SLAS_CLIENT_ID,
  organizationId: process.env.NEXT_PUBLIC_ORG_ID,
  shortCode:      process.env.NEXT_PUBLIC_SHORT_CODE,
  siteId:         process.env.NEXT_PUBLIC_SITE_ID,
  locale:         'en-US',
  currency:       'USD',
};

export default function App({ Component, pageProps }) {
  return (
    <CommerceApiProvider config={commerceConfig}>
      <Component {...pageProps} />
    </CommerceApiProvider>
  );
}
```

```jsx
// SearchResults.jsx — consuming a typed Shopper Search hook within provider context
import { useShopperSearch } from '@salesforce/commerce-sdk-react';

export function SearchResults({ query }) {
  const { data, isLoading, error } = useShopperSearch().useProductSearch({
    parameters: { q: query, limit: 24, locale: 'en-US' },
  });

  if (isLoading)           return <p>Loading...</p>;
  if (error?.status === 503) return <p>Search temporarily unavailable. Please try again shortly.</p>;
  if (error)               return <p>An error occurred.</p>;

  return (
    <ul>
      {data?.hits?.map((product) => (
        <li key={product.productId}>{product.productName}</li>
      ))}
    </ul>
  );
}
```

**Why it works:** Placing `CommerceApiProvider` at the `_app.jsx` root means the provider — and its internal `react-query` client, SLAS token state, and proactive token refresh timers — persists across all route changes. The SDK handles PKCE code verifier generation, token storage, and background refresh internally. The `error.status === 503` check enables graceful UI degradation during load-shedding events without crashing the component or misleading the shopper with a permanent error state.

---

## Anti-Pattern: Applying OCAPI Session Cookie Logic to SCAPI

**What practitioners do:** Developers copy OCAPI-era integration code that acquires a `dwsid` session cookie from Account Manager and passes it as a `Cookie` header on subsequent calls to what they expect to be SCAPI endpoints.

**What goes wrong:** SCAPI endpoints are fully stateless and do not recognize `dwsid` session cookies. Every request returns 401 `invalid_token`. Critically, this error message is identical to the error returned for an expired JWT, so developers waste significant time debugging token expiry scenarios and refreshing tokens before realizing the auth mechanism itself is wrong.

**Correct approach:** Discard all OCAPI session cookie handling entirely. SCAPI requires a JWT access token acquired from SLAS via PKCE, passed as `Authorization: Bearer <token>` on every request. There are no sessions to maintain, no cookie headers to set, and no Account Manager session endpoints to call.
