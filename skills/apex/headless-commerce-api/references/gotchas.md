# Gotchas — Headless Commerce API (SCAPI)

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SLAS and Account Manager Are Completely Separate Services

**What happens:** SLAS returns `invalid_client` or `unauthorized_client` when called with a client ID that was registered in Salesforce Account Manager for OCAPI. The error message does not indicate the root cause — it looks identical to a misconfigured redirect URI or an expired client secret.

**When it occurs:** Any time a developer reuses an OCAPI client ID against SLAS endpoints, or when a Commerce Cloud org has both OCAPI and SCAPI integrations and the wrong client ID is used for the SCAPI flow. Account Manager client IDs are valid only for OCAPI and Account Manager OAuth2 — they have no standing with SLAS.

**How to avoid:** Register a dedicated SLAS client ID through the SLAS management interface (separate from Account Manager). Confirm the client ID is associated with the correct site ID (channel ID) and that the redirect URI registered in SLAS matches exactly — including trailing slashes and protocol — what the frontend sends in the PKCE flow.

---

## Gotcha 2: HTTP 503 Is Load-Shedding, Not a Standard Rate-Limit Error

**What happens:** Under high load, SCAPI returns HTTP 503 with a `Retry-After` header instead of 429. Client code that handles 429 for rate limits but not 503 will treat the load-shedding response as a server error, surfacing a false "service unavailable" state to all shoppers simultaneously at peak traffic.

**When it occurs:** When aggregate SCAPI server capacity exceeds 90% utilization — typically during flash sales, holiday peaks, or heavy concurrent catalog crawls. The 503 is server-side and non-deterministic from the client's perspective: the same request rate that works at 2:00 AM triggers 503s at noon on a sale day.

**How to avoid:** Implement a retry wrapper on all SCAPI calls that specifically handles 503 by reading the `Retry-After` header value and waiting that many seconds (plus random jitter of 0–500 ms) before retrying. Cap retries at 3. Do not handle 503 the same as 429 — they have different semantics. Reduce the frequency of live SCAPI calls through aggressive object-level product caching to lower the baseline load.

---

## Gotcha 3: Response-Level Caching Causes Stale Data and Expensive Cache Invalidation

**What happens:** Caching an entire SCAPI search or product listing response as a single cache blob under a query-string key means that any change to any product in the results requires invalidating the entire cache entry. At scale, this produces two bad outcomes: either cache TTLs must be very short (causing high SCAPI call volume and more 503 exposure) or TTLs are long and product data becomes stale.

**When it occurs:** When caching is implemented at the HTTP response level — for example, caching `GET /shopper-search/v1/...?q=shoes` as a single key — rather than at the level of individual product objects returned in the response. It worsens when product catalogs are updated frequently (price changes, inventory changes, product availability).

**How to avoid:** Cache individual product objects under their product ID as the primary cache key, with locale and price book ID as secondary dimensions. When a product is updated, invalidate only its specific cache entry. The search result set itself can be cached briefly (1–5 minutes) as a list of product IDs without caching the full product payloads — the IDs are used to look up the already-cached product objects.

---

## Gotcha 4: Guest Basket IDs Are Bound to the Guest Token Subject Claim

**What happens:** When a guest shopper logs in, calling the Shopper Baskets API with the registered shopper token and the guest basket ID returns 403 `forbidden`. The registered token cannot access a basket that was created under a different token's subject claim, even if both tokens are for the same Commerce Cloud site.

**When it occurs:** Any time a guest shopper adds items to a cart and then authenticates — a flow that occurs constantly in production. Without the basket merge call, the shopper loses their pre-login cart silently (no error is shown at the basket creation step — the error surfaces only when the registered shopper tries to retrieve or modify the guest basket).

**How to avoid:** Before discarding the guest token and switching to the registered shopper token, call `POST /checkout/shopper-baskets/v1/organizations/{orgId}/baskets/actions/merge` with the registered shopper token and the guest basket ID in the request body. This is the only supported mechanism to transfer basket contents. Store the guest basket ID in client state (not tied to the guest token) so it survives the authentication redirect.

---

## Gotcha 5: PKCE Code Verifier Outside 43–128 Characters Fails SLAS Validation Silently

**What happens:** SLAS returns HTTP 400 `invalid_request` when the PKCE code verifier sent in the token request is shorter than 43 characters or longer than 128 characters, or contains characters outside the RFC 7636 URL-safe Base64 alphabet (`[A-Za-z0-9\-._~]`). Some popular PKCE libraries generate verifiers of 32 or 40 characters — values that are accepted by many OAuth2 servers but rejected by SLAS.

**When it occurs:** When developers use a generic PKCE library without verifying that its output conforms to SLAS's strict RFC 7636 enforcement. The 400 error does not indicate that the verifier length is the problem; it just says `invalid_request`, which looks similar to a missing-parameter error.

**How to avoid:** Always generate the PKCE code verifier with a length of 43–128 characters using only the URL-safe Base64 character set. Test the verifier generation against SLAS directly before integrating it into the full auth flow. If using `crypto.randomBytes()` in Node.js, generate at least 64 bytes and encode them as base64url — this reliably produces a 86-character verifier well within the valid range.
