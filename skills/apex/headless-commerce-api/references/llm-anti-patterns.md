# LLM Anti-Patterns — Headless Commerce API (SCAPI)

Common mistakes AI coding assistants make when generating or advising on SCAPI-based headless Commerce development. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Applying OCAPI Session Authentication to SCAPI Endpoints

**What the LLM generates:** Code that sets an `x-dw-client-id` header or uses Business Manager OCAPI session authentication for SCAPI endpoint calls.

**Why it happens:** OCAPI was the dominant B2C Commerce API for many years and far more training data exists for it than SCAPI. LLMs default to OCAPI patterns when asked about "B2C Commerce API authentication."

**Correct pattern:**

```javascript
// WRONG — OCAPI client ID header on a SCAPI endpoint:
headers: { 'x-dw-client-id': 'your-ocapi-client-id' }

// CORRECT — SLAS Bearer token for SCAPI:
const slasClient = new ShopperLogin({ ...config });
const { access_token } = await slasClient.getAccessToken({ ... });
headers: { 'Authorization': `Bearer ${access_token}` }
```

SCAPI requires a SLAS-issued Bearer token. The `x-dw-client-id` header is OCAPI-specific and has no effect on SCAPI endpoints.

**Detection hint:** If generated SCAPI code includes `x-dw-client-id`, HMAC authentication, or references Business Manager > OCAPI Settings for credential setup, flag as wrong auth model.

---

## Anti-Pattern 2: Using Response-Level Caching Instead of Object-Level Caching

**What the LLM generates:** Advice to "cache the full API response" at the CDN or reverse proxy layer for all SCAPI product/basket calls, treating every response as cacheable.

**Why it happens:** Response-level caching is a default recommendation for REST APIs. LLMs do not know that SCAPI enforces object-level caching (per-product, per-category) and that basket/checkout endpoints are never cacheable.

**Correct pattern:**

```
Object-level caching (correct for SCAPI):
  - Product records: cache keyed by productId + locale + currency
  - Category/navigation trees: cache keyed by categoryId + locale
  - Price books: cache keyed by priceBookId + currency

Never cache (shopper-specific, mutable):
  - /baskets (basket contents change per add/remove)
  - /orders (POST is non-idempotent)
  - /sessions (session tokens are ephemeral)
```

Apply HTTP cache headers (`Cache-Control: max-age`) at the object granularity — not across all SCAPI responses uniformly.

**Detection hint:** If the LLM recommends a blanket CDN cache rule for all SCAPI endpoints or sets `Cache-Control: max-age` on basket/order endpoints, flag as incorrect caching scope.

---

## Anti-Pattern 3: Ignoring SCAPI Load-Shedding (HTTP 503 at 90% Capacity)

**What the LLM generates:** A simple retry-on-error wrapper that treats HTTP 503 from SCAPI as a transient server error, retrying immediately with exponential backoff.

**Why it happens:** 503 is normally a transient error signal in most APIs. LLMs apply standard resilience patterns without knowing that SCAPI 503s at high load are load-shedding events designed to shed additional traffic — aggressive retries worsen the problem.

**Correct pattern:**

```javascript
// WRONG — immediate retry on 503:
if (response.status === 503) await sleep(1000 * attempt);

// CORRECT — honor Retry-After header, use circuit breaker:
if (response.status === 503) {
  const retryAfter = parseInt(response.headers['retry-after'] || '5', 10);
  // Respect the server's backoff signal; use circuit breaker to stop retries
  await sleep(retryAfter * 1000);
  circuitBreaker.recordFailure();
  if (circuitBreaker.isOpen()) throw new Error('SCAPI circuit open');
}
```

SCAPI implements load-shedding at 90% server capacity. Respecting `Retry-After` and using a circuit breaker prevents thundering herd during capacity events.

**Detection hint:** If the LLM generates a retry loop on 503 without reading `Retry-After` or a circuit breaker, flag as load-shedding-unaware retry logic.

---

## Anti-Pattern 4: Building a Custom Auth Flow Instead of Using Commerce SDK React

**What the LLM generates:** Custom `fetch`-based SLAS authentication code from scratch, manually constructing PKCE parameters, token exchange URLs, and refresh logic.

**Why it happens:** LLMs generate self-contained code and don't always surface official SDK usage. Manually implementing OAuth2 PKCE from scratch is a common training-data pattern.

**Correct pattern:**

```javascript
// WRONG — custom PKCE + SLAS token exchange from scratch:
const codeVerifier = generateCodeVerifier();
const codeChallenge = await generateCodeChallenge(codeVerifier);
const authUrl = `https://${shortCode}.api.commercecloud.salesforce.com/...`;
// ... 50 lines of manual OAuth2 PKCE code

// CORRECT — Commerce SDK React / SCAPI SDK handles auth:
import { ShopperLogin } from 'commerce-sdk-isomorphic';
const slasClient = new ShopperLogin({
  parameters: { clientId, organizationId, siteId, shortCode },
});
const { access_token } = await slasClient.getAccessToken({ ... });
```

Commerce SDK React (react-query hooks) is the Salesforce-recommended frontend integration layer. Use it instead of manually implementing SLAS.

**Detection hint:** If generated code implements PKCE manually or constructs SLAS token exchange URLs by hand, flag as "use Commerce SDK React instead."

---

## Anti-Pattern 5: Constructing SCAPI URLs with OCAPI URL Pattern

**What the LLM generates:** API call URLs in the format `https://{instance}.demandware.net/s/{site}/dw/shop/v24_5/products/{id}` (OCAPI pattern) for a SCAPI integration.

**Why it happens:** OCAPI URLs dominate older B2C Commerce documentation and training data. LLMs conflate the two API systems and use OCAPI URL patterns when writing SCAPI integration code.

**Correct pattern:**

```
OCAPI (legacy — do not use for new integrations):
  https://{instance}.demandware.net/s/{siteId}/dw/shop/v24_5/products/{productId}

SCAPI (correct for new integrations):
  https://{shortCode}.api.commercecloud.salesforce.com/product/shopper-products/v1/
    organizations/{organizationId}/products/{productId}?siteId={siteId}
```

SCAPI uses the `{shortCode}.api.commercecloud.salesforce.com` base URL with organization-scoped paths. Find `shortCode` and `organizationId` in Business Manager > Administration > Salesforce Commerce API Settings.

**Detection hint:** If generated SCAPI code contains `demandware.net` or `/dw/shop/v` URL fragments, flag as OCAPI URL pattern used for SCAPI endpoint.

---

## Anti-Pattern 6: Skipping Guest-to-Registered Basket Merge After Login

**What the LLM generates:** A login completion handler that acquires a registered shopper token and immediately redirects to the account or cart page, without calling the basket merge endpoint for the pre-login guest basket.

**Why it happens:** The basket merge requirement is unique to SCAPI's token-binding model and absent from general OAuth2 and e-commerce integration patterns in training data. LLMs generate standard "acquire token, redirect" login flows without knowing that SCAPI binds basket ownership to the subject claim of the token that created the basket — making the guest basket inaccessible to the new registered token without explicit merge.

**Correct pattern:**

```javascript
// WRONG — login without basket merge:
const { access_token } = await acquireRegisteredToken(credentials);
redirectToCart(); // Guest cart is silently inaccessible — shopper sees empty cart

// CORRECT — merge guest basket before redirect:
const { access_token } = await acquireRegisteredToken(credentials);
if (guestBasketId) {
  await fetch(`${SCAPI_BASE}/checkout/shopper-baskets/v1/organizations/${orgId}/baskets/actions/merge`, {
    method:  'POST',
    headers: { Authorization: `Bearer ${access_token}`, 'Content-Type': 'application/json' },
    body:    JSON.stringify({ basketId: guestBasketId, mergeStrategy: 'merge' }),
  });
}
redirectToCart(); // Cart contents preserved
```

**Detection hint:** Flag any login completion handler (post-SLAS token exchange) that does not include a call to the `baskets/actions/merge` endpoint when a guest basket ID is in session state. The guest basket ID must be preserved through the authentication redirect — flag any code where the guest basket ID could be lost before the merge completes.

---

## Anti-Pattern 7: Using PKCE Code Verifier Values Outside the SLAS 43–128 Character Range

**What the LLM generates:** A PKCE code verifier generated with fewer than 43 characters — for example, using `crypto.randomBytes(32).toString('base64url')` which produces a ~43-character value that may be padded below the required minimum, or `crypto.randomBytes(16).toString('hex')` which produces exactly 32 characters.

**Why it happens:** PKCE is a widely-used OAuth2 extension and most OAuth2 providers accept code verifiers of various lengths. LLMs generate PKCE examples based on the most common training patterns, which typically use 32-byte random values. SLAS enforces RFC 7636 strictly, requiring 43–128 characters — a validation constraint absent from most other OAuth2 server implementations in training data.

**Correct pattern:**

```javascript
// WRONG — 32-byte hex produces only 64 chars but base64 padding may vary:
const codeVerifier = crypto.randomBytes(32).toString('hex'); // 64 chars hex — MAY be OK but fragile

// WRONG — 16-byte base64url: only 22 chars, far below 43 minimum:
const codeVerifier = crypto.randomBytes(16).toString('base64url'); // 22 chars — SLAS rejects

// CORRECT — 64 bytes base64url: 86 chars, safely within 43–128:
const codeVerifier = crypto.randomBytes(64).toString('base64url'); // 86 chars — SLAS accepts
```

**Detection hint:** Flag any PKCE code verifier generation that uses fewer than 48 source bytes (which produces fewer than 64 base64url characters). The safe pattern is `crypto.randomBytes(64).toString('base64url')` which reliably produces 86 characters well within the valid range.
