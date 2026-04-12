# Gotchas — Headless Commerce Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SCAPI Hard 10-Second Shopper API Timeout (HTTP 504)

**What happens:** SCAPI enforces a non-configurable 10-second timeout on Shopper API requests. When a Shopper API call (or the server-side rendering path that triggers it) does not return a response within 10 seconds, SCAPI returns HTTP 504. The browser receives a 504, and the page renders blank or as an error page.

**When it occurs:** Most commonly during server-side rendering paths that chain multiple SCAPI calls sequentially. A page that calls product detail (800 ms), then recommendations (900 ms), then promotions (700 ms), then content slots (600 ms) sequentially accumulates 3+ seconds of SCAPI call time before any processing or rendering begins — and that is under normal load. During load-shedding events or transient SCAPI slowdowns, individual call times can spike, pushing the sequential total above 10 seconds.

**How to avoid:**
- Cache product catalog pages at the web tier so that the majority of requests are served from cache without any SCAPI calls.
- Parallelize SSR-required SCAPI calls using `Promise.all` rather than sequential `await` chains.
- Set per-call timeouts (recommended: 4 seconds) on individual SCAPI calls so a slow endpoint causes graceful degradation (omit the section) rather than blocking the entire render past 10 seconds.
- Defer non-critical SCAPI calls (reviews, cross-sell recommendations) to client-side hydration so they do not count against the SSR latency budget.

---

## Gotcha 2: Web-Tier Cache TTL Hard Cap at 86400 Seconds

**What happens:** The MRT CDN layer enforces a maximum cache TTL of 86400 seconds (24 hours). Cache TTL values set above this limit are silently clamped to 86400 seconds. There is no error or warning — the configuration appears to accept any value, but the actual TTL in effect is 86400.

**When it occurs:** When architecture documents or PWA Kit cache configuration specify TTLs above 86400 seconds — for example, a 7-day TTL for "stable" catalog pages or a 30-day TTL for static product images served through MRT. The configuration is accepted silently but the effective TTL is 24 hours.

**How to avoid:**
- Document and enforce a maximum TTL of 86400 seconds in all caching architecture specifications.
- For content that genuinely benefits from longer cache lifetimes (e.g., product images, static brand assets), serve those assets from a separate CDN or object storage layer that is not subject to the MRT TTL cap.
- If content must stay fresh for longer than 24 hours without expiry-based refresh, design an explicit cache invalidation webhook from the Commerce Cloud catalog system rather than relying on TTL alone.

---

## Gotcha 3: SLAS Is a Separate OAuth2 Service from Salesforce Identity (Connected Apps)

**What happens:** SLAS (Shopper Login and API Access Service) is a dedicated OAuth2 server within the Commerce Cloud infrastructure. It is not the same as Salesforce Account Manager OAuth or the connected app OAuth2 flows used for Salesforce org API access. A client ID registered as a Salesforce connected app will not work with SLAS — SLAS returns `invalid_client` with no further detail.

**When it occurs:** Teams familiar with Salesforce org OAuth (for Experience Cloud, Apex REST, or Salesforce platform APIs) assume SLAS uses the same client IDs and registration process. They register a connected app in Setup, obtain a client ID and secret, and attempt to use it against SLAS token endpoints. The flow fails silently with `invalid_client`.

**How to avoid:**
- SLAS client IDs must be registered specifically through the SLAS management interface in Account Manager (not through Salesforce Setup connected apps).
- Architecture documentation must explicitly distinguish SLAS from Salesforce Identity. These are two separate auth systems serving two separate platforms (Commerce Cloud vs. Salesforce org).
- If the storefront also integrates with the Salesforce org (e.g., CRM data, service case creation), those integrations require a separate connected app credential — they cannot share the SLAS client ID.

---

## Gotcha 4: Guest Basket IDs Are Token-Bound — Merge Is Not Automatic on Login

**What happens:** Guest shopping baskets are created in Commerce Cloud under the subject claim of the guest SLAS token. When a shopper authenticates and receives a registered shopper token, calling the basket endpoint with the new token returns HTTP 403 — the registered token has a different subject claim and is not authorized to access the guest basket.

**When it occurs:** Login flows that obtain a registered shopper token and then attempt to resume the guest basket without an explicit merge call. This is a very common omission in initial implementation — the guest basket ID is in client state, the new token is obtained, and the cart page attempts to load the basket with the new token and receives a 403.

**How to avoid:**
- Design the login flow to call the basket merge endpoint (`POST .../baskets/actions/merge`) before discarding the guest basket reference or the guest token.
- Preserve the guest basket ID in client state through the entire SLAS authorization code flow so it is available to the merge call.
- Test the guest-to-registered basket merge explicitly as a required acceptance criterion — it is not exercised by standard unit testing of the auth flow alone.

---

## Gotcha 5: Cache Under-Keying Causes Locale and Currency Cross-Contamination

**What happens:** When the web-tier cache key is based only on the URL path (the default for many CDN configurations), shoppers in different locales or with different currency settings receive each other's cached product pages. A UK shopper browsing `example.com/en-GB/p/SKU123` may receive the cached US-locale version of that page if both locales share the same URL structure and the cache key does not include locale or currency.

**When it occurs:** Initial architecture that treats URL-path-only as a sufficient cache key, commonly inherited from SFRA configurations where URL paths were locale-specific by convention. Composable Storefront supports locales via URL prefix or header — the chosen approach must be reflected in the cache key design.

**How to avoid:**
- Always include locale, currency, and site ID in the web-tier cache key, regardless of whether they appear in the URL.
- For architectures that use `Accept-Language` or session-based locale detection (rather than URL-prefix locale), include the normalized locale value as an explicit Vary header or a custom cache-key component.
- Validate cache-key design by testing with two shoppers in different locales hitting the same URL and confirming they receive correctly-locale-specific pages.
