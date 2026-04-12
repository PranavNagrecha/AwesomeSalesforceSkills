---
name: headless-commerce-api
description: "Use this skill when building custom headless storefronts that call Salesforce Commerce API (SCAPI) — including Shopper API authentication with SLAS OAuth2 JWT tokens, integrating Commerce SDK React hooks, wiring Shopper Basket/Checkout APIs, and handling SCAPI-specific load-shedding and caching behavior. NOT for standard LWR storefront configuration, declarative Experience Builder layouts, legacy OCAPI integrations, or architecture-level headless decisions — use admin/headless-commerce-architecture for pattern selection."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
triggers:
  - "how to authenticate a headless storefront against Salesforce Commerce API using SLAS"
  - "SCAPI returning 503 under load but no hard rate limit configured"
  - "Commerce SDK React hooks not refreshing JWT token on expiry"
  - "how to call Shopper Baskets API from a custom React storefront"
  - "OCAPI session-based hook patterns failing after migrating to SCAPI"
  - "object-level vs response-level caching in headless Commerce storefront"
tags:
  - headless-commerce
  - SCAPI
  - SLAS
  - shopper-api
  - commerce-sdk-react
  - B2C-commerce
  - headless-storefront
  - OAuth2
inputs:
  - Commerce Cloud instance hostname and organization ID
  - Client ID registered in SLAS (Shopper Login and API Access Service)
  - Site ID and locale for the target storefront
  - Whether the session is guest, registered shopper, or agent-on-behalf-of-shopper
  - Frontend framework in use (React/Next.js, Angular, or custom fetch layer)
outputs:
  - SLAS OAuth2 token acquisition and refresh flow implementation
  - Shopper API request wiring (browse, basket, checkout) with correct auth headers
  - Commerce SDK React hook integration for authenticated and guest sessions
  - Load-shedding resilience pattern (retry with back-off on HTTP 503)
  - Caching strategy guidance scoped to SCAPI object-level expectations
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Headless Commerce API (SCAPI)

Use this skill when building or debugging custom headless storefronts that communicate with the Salesforce Commerce API (SCAPI). It covers SLAS-based OAuth2 JWT token acquisition, Shopper API integration, Commerce SDK React hook patterns, SCAPI load-shedding behavior, and correct caching architecture. This skill does not cover declarative storefront configuration, OCAPI integrations, or the architectural decision of whether to go headless.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm SCAPI is enabled, not OCAPI.** SCAPI is the mandatory replacement for OCAPI for all new headless storefronts. If existing code references OCAPI endpoints (`/dw/shop/v*`) or OCAPI hook classes, this skill does not apply — OCAPI session and hook patterns are categorically different from SCAPI and cannot be mixed.
- **Identify the shopper session type.** SLAS issues different token types for guest shoppers (`client_credentials` grant with PKCE), registered shoppers (authorization code grant with PKCE), and agent-on-behalf-of-shopper flows. The token acquisition flow and refresh behavior differ for each. Confirm which session type the storefront requires before writing any auth code.
- **Confirm the SLAS client ID and redirect URI are registered.** SLAS client IDs are registered per-site in Account Manager. The redirect URI used in the PKCE flow must exactly match the registered value — a mismatch silently fails authorization, returning an `invalid_client` error.
- **Check which API group is needed.** SCAPI splits into Shopper APIs (customer-facing: product catalog, search, basket, checkout, orders) and Admin APIs (back-office: inventory, pricing, catalog management). Guest and registered shoppers call Shopper APIs only. Admin API calls require a separate Client Credentials grant, not a SLAS shopper token.
- **Understand load-shedding behavior.** SCAPI implements load-shedding at 90% server capacity rather than enforcing uniform hard rate limits. When server load crosses the 90% threshold, SCAPI returns HTTP 503 with a `Retry-After` header. Client code that does not handle 503 will silently drop requests during peak traffic.

---

## Core Concepts

### SCAPI vs. OCAPI: A Complete Break, Not a Migration Path

Salesforce Commerce API (SCAPI) is not a versioned upgrade of the legacy Open Commerce API (OCAPI). It is a parallel, purpose-built REST API surface with fundamentally different authentication, endpoint structure, and operational characteristics:

- **Authentication:** OCAPI uses Account Manager session cookies and registered hook classes in Business Manager. SCAPI uses SLAS — a dedicated OAuth2 service that issues short-lived JWT access tokens and long-lived refresh tokens. There are no sessions, no cookies, and no hook invocations.
- **Endpoint structure:** OCAPI exposes `/dw/shop/v*` and `/dw/data/v*` namespaces. SCAPI exposes `https://<short-code>.api.commercecloud.salesforce.com/customer/shopper-customers/v1/...` and related namespaces under the `api.commercecloud.salesforce.com` root domain.
- **Extensibility:** OCAPI extended behavior via registered hook scripts. SCAPI extensibility lives in the calling application layer or via Commerce Cloud extensibility APIs — OCAPI hook classes are not ported to SCAPI.

Any code that imports OCAPI patterns (session IDs, hook registration, `dw.*` namespace classes) must be rewritten from scratch for SCAPI, not adapted.

### SLAS: Shopper Login and API Access Service

SLAS is the OAuth2 authorization server that issues and manages JWT tokens for SCAPI Shopper API access. SLAS is separate from Salesforce Identity (connected apps, OAuth flows in the Salesforce org). It is a dedicated service running in the Commerce Cloud infrastructure.

SLAS supports three relevant grant types for storefront work:

1. **Guest shopper (PKCE without login):** Calls `POST /shopper/auth/v1/organizations/{orgId}/oauth2/token` with `grant_type=client_credentials` and a PKCE challenge. Returns a guest access token and a refresh token. No shopper credentials are required.
2. **Registered shopper (PKCE with login):** Two-step — first exchange credentials for an authorization code via the SLAS authorize endpoint, then exchange the code for tokens via the token endpoint with `grant_type=authorization_code`. Returns a shopper-specific access token bound to the customer identity.
3. **Token refresh:** `POST .../oauth2/token` with `grant_type=refresh_token` and the stored refresh token. Access tokens expire in 30 minutes by default; refresh tokens are long-lived but bounded by SLAS configuration.

All Shopper API requests include the access token as a Bearer token in the `Authorization` header. There is no cookie or session ID.

### Shopper APIs: Functional Split by Buyer Journey Stage

SCAPI Shopper APIs cover the full buyer journey and are organized by domain:

- **Shopper Products / Search (`shopper-products`, `shopper-search`):** Product detail pages, search results, recommendations.
- **Shopper Baskets (`shopper-baskets`):** Cart creation, item add/remove, coupon application, shipment assignment.
- **Shopper Orders (`shopper-orders`):** Order placement from a basket; order history for registered shoppers.
- **Shopper Customers (`shopper-customers`):** Registration, address book, payment instruments.
- **Shopper Experience (`shopper-experience`):** Page Designer content for headless storefronts.

Each API family has its own base path and versioning. The basket created for a guest shopper is bound to the guest token's subject claim. When the shopper logs in, the basket must be explicitly merged using the `shopper-baskets` merge endpoint — basket IDs do not automatically transfer between guest and registered tokens.

### Commerce SDK React: Hook-Based Integration Layer

Commerce SDK React is the official frontend integration library for SCAPI. It provides a set of `react-query`-backed hooks that handle token acquisition, request serialization, response normalization, and automatic background token refresh. Using Commerce SDK React instead of raw `fetch` calls eliminates the most common SCAPI integration bugs:

- The SDK automatically calls the SLAS refresh endpoint before an access token expires — application code does not implement refresh logic manually.
- Hooks expose typed response objects aligned to the SCAPI contract, reducing field-mapping errors.
- The SDK handles the PKCE flow internally, including code verifier generation and secure storage.

The entry point is `CommerceApiProvider`, which accepts the Commerce Cloud configuration (client ID, org ID, site ID, locale, short code) and wraps the component tree. Individual hooks like `useShopperSearch`, `useShopperBaskets`, and `useShopperOrders` are consumed within that provider context.

### Load-Shedding at 90% Capacity

SCAPI does not publish per-client rate limits in the traditional sense. Instead, it implements server-side load-shedding: when aggregate server capacity crosses 90% utilization, SCAPI begins returning HTTP 503 responses with a `Retry-After` header indicating the number of seconds to wait before retrying. This behavior differs from rate limiting in two important ways:

1. **It is not deterministic from the client's perspective.** A client making 10 requests per second might never see a 503 at 3:00 AM and see them for every request at peak shopping hours.
2. **The `Retry-After` value must be respected.** Ignoring `Retry-After` and immediately retrying compounds server load, increasing the probability of continued 503s. Clients must implement exponential back-off seeded from the `Retry-After` value.

Caching is the primary mitigation. Product catalog data (PDPs, search results) should be cached at the object level — individual product objects with their own TTLs — not at the full response level. Response-level caching caches the entire search results page as a blob; if one product updates, the entire cache entry must be invalidated. Object-level caching allows granular invalidation and higher cache-hit rates, reducing the number of live SCAPI calls during peak load.

---

## Common Patterns

### Pattern: Guest Shopper Session Initialization with SLAS PKCE

**When to use:** A visitor arrives at the headless storefront without an existing session. Before any personalized API call (basket creation, recommendations), a guest access token must be acquired.

**How it works:**
1. Generate a cryptographically random PKCE code verifier (43–128 URL-safe Base64 characters: `[A-Za-z0-9\-._~]`).
2. Compute the PKCE code challenge as `BASE64URL(SHA-256(code_verifier))`.
3. Call the SLAS guest token endpoint: `POST /shopper/auth/v1/organizations/{orgId}/oauth2/token` with `grant_type=client_credentials`, the PKCE challenge, client ID, and channel ID (site ID).
4. Store the returned access token in memory only (not `localStorage`). Store the refresh token in a `httpOnly` cookie or equivalent secure storage.
5. Attach the access token as `Authorization: Bearer <token>` on all subsequent Shopper API requests.
6. Trigger token refresh proactively when the access token is within 60 seconds of expiry — do not wait for a 401.

**Why not the alternative:** Storing session cookies (OCAPI-style) exposes the session to CSRF attacks and does not work with SCAPI's stateless JWT model. Relying on 401 responses to trigger refresh adds visible latency on every expiry boundary.

### Pattern: Guest-to-Registered Basket Merge on Login

**When to use:** A shopper builds a basket as a guest, then logs in. The guest basket and registered shopper basket must be merged so the shopper sees their pre-login cart items.

**How it works:**
1. Acquire a registered shopper token via the SLAS authorization code PKCE flow (preserve the guest basket ID before discarding the guest token).
2. Call `POST /checkout/shopper-baskets/v1/organizations/{orgId}/baskets/actions/merge` with the registered shopper token.
3. Include the guest basket ID in the request body as `basketId`. Specify the merge strategy (`merge` to combine items, `replace` to overwrite the registered basket with guest items).
4. Discard the guest basket reference from client-side state. The guest token can be discarded after the merge completes.

**Why not the alternative:** Attempting to access the guest basket ID with the registered shopper token returns 403 — baskets are bound to the subject claim of the token that created them. Directly assigning the guest basket to the registered account is not a supported API operation.

### Pattern: Resilient SCAPI Calls with Load-Shedding Retry

**When to use:** Any production SCAPI integration that must handle peak traffic periods gracefully without surfacing false unavailability to shoppers.

**How it works:**
1. Wrap SCAPI fetch calls in a retry loop with a configurable maximum retry count (3 is recommended for most endpoints; search may warrant fewer).
2. On receiving HTTP 503, read the `Retry-After` response header value (in seconds).
3. Wait for `Retry-After` seconds plus a small random jitter (0–500 ms) to prevent thundering-herd retry storms.
4. Retry the original request with the same valid token (503 does not invalidate tokens).
5. After exhausting retries, surface a user-facing degraded state (for example, "search temporarily unavailable — please try again shortly") rather than throwing an unhandled exception.

**Why not the alternative:** Treating 503 as a permanent error causes false product-unavailable states during normal peak periods. Retrying immediately without respecting `Retry-After` aggravates server load and increases the likelihood of continued 503s for all clients.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New headless storefront from scratch | Use SCAPI + SLAS; do not start with OCAPI | OCAPI is deprecated for new headless work; SCAPI is the mandatory path |
| Existing OCAPI integration needs updating | Full rewrite of auth and API call layer to SCAPI; no partial migration | OCAPI session cookies and hook patterns have no SCAPI equivalent |
| React/Next.js frontend | Use Commerce SDK React hooks (`CommerceApiProvider` + typed hooks) | SDK handles token refresh, PKCE, and response normalization automatically |
| Angular or non-React frontend | Call SCAPI REST directly; implement SLAS PKCE and token refresh manually | Commerce SDK React is React-specific; no official Angular SDK as of Spring '25 |
| High-traffic product catalog page | Cache product objects at the object level with per-object TTLs | Response-level caching requires full invalidation on any product update; object-level is more granular |
| HTTP 503 received during API call | Respect `Retry-After` header; retry with exponential back-off plus jitter | Immediate retry compounds server load during load-shedding events |
| Guest shopper adding to cart | Acquire guest SLAS token first; then create basket with Shopper Baskets API | Unauthenticated basket creation is not supported — all basket calls require a valid SLAS token |
| Shopper logs in after building guest basket | Use basket merge endpoint with registered token before discarding guest basket | Guest basket IDs are bound to the guest token subject; they cannot be re-used with a different token |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm SCAPI readiness** — Verify the Commerce Cloud instance has SCAPI enabled and that a SLAS client ID is registered in Account Manager for the target site. Confirm the redirect URI is registered exactly as the frontend will send it. Collect the org ID, site ID, short code, and locale before writing any code.
2. **Design the auth layer first** — Map the required session types (guest, registered, or agent-on-behalf-of-shopper). For each type, document the SLAS grant flow, where tokens are stored, and how refresh is triggered. Do not proceed to API wiring until the auth design is fully specified and reviewed.
3. **Choose and configure the integration layer** — For React/Next.js: install Commerce SDK React, configure `CommerceApiProvider`, and wire the typed hooks. For other frameworks: implement the SLAS PKCE flow manually and write a thin fetch wrapper that injects `Authorization: Bearer <token>` and handles 401 by triggering refresh.
4. **Wire Shopper APIs by buyer journey stage** — Implement product and search APIs first (stateless, no basket required), then basket creation and item management, then checkout and order APIs. Test each stage with a guest token before implementing the registered shopper flow.
5. **Implement load-shedding resilience** — Add a retry wrapper around all SCAPI calls. On HTTP 503, read `Retry-After`, wait the indicated duration plus jitter, then retry. Cap retries at 3. Surface graceful degradation messages to the user after max retries are exhausted.
6. **Design and implement the caching layer** — Cache product objects individually with per-object TTLs, not full page or query responses. Use cache keys scoped to product ID, locale, and price book ID. Implement cache invalidation hooks for product update events from the Commerce Cloud catalog.
7. **Validate end-to-end** — Run through a complete guest purchase flow: token acquisition, product browse, basket creation, item add, checkout, order placement. Then run the registered shopper variant including basket merge. Verify token refresh works by testing with a forced token expiry.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All API calls use SCAPI endpoints (`api.commercecloud.salesforce.com`), not OCAPI (`/dw/shop/v*`) endpoints
- [ ] SLAS tokens are acquired via PKCE — no client secret is sent from browser-side code
- [ ] Access tokens are stored in memory only (never `localStorage`); refresh tokens are in `httpOnly` cookies or equivalent secure storage
- [ ] Token refresh is triggered proactively before expiry, not reactively on 401
- [ ] Guest-to-registered basket merge is implemented before the guest basket reference is discarded
- [ ] All SCAPI calls have a retry wrapper that respects the `Retry-After` header on HTTP 503
- [ ] Caching is implemented at the object level (per product, per TTL) — not at the full search-response level
- [ ] No OCAPI session, hook, or `dw.*` namespace patterns remain in the codebase

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **SLAS and Account Manager Are Not Interchangeable** — SLAS (`https://<short-code>.api.commercecloud.salesforce.com/shopper/auth/v1/...`) is a separate OAuth2 service from Salesforce Account Manager. A client ID registered in Account Manager for OCAPI does not work with SLAS. SLAS client IDs must be registered specifically through the SLAS management interface. Using an Account Manager client ID against SLAS endpoints returns `invalid_client` with no further detail.
2. **HTTP 503 Is Load-Shedding, Not a Rate Limit Error** — Unlike typical REST APIs that return 429 for rate limiting, SCAPI returns 503 when server load exceeds 90% capacity. Client code that treats 503 as a permanent server error will silently fail for all shoppers during peak periods. The `Retry-After` header is authoritative — retry after exactly that duration plus jitter.
3. **Response-Level Caching Causes Stale and Expensive Cache Invalidation** — Caching a full search response as a single blob means any product update requires invalidating the entire query result. At scale this produces either stale product data (long TTLs) or cache thrashing (short TTLs). SCAPI responses are designed for object-level caching: cache each product under its product ID key with its own TTL.
4. **Guest Basket IDs Are Token-Bound** — When a guest shopper logs in, their guest basket cannot be accessed with the registered shopper token. The basket was created under the guest token's subject claim. Calling the basket endpoint with the registered token returns 403. The basket merge endpoint is the only supported transfer mechanism.
5. **PKCE Code Verifier Length Is Strictly Validated by SLAS** — SLAS enforces RFC 7636 strictly: the code verifier must be 43–128 characters of URL-safe Base64 (`[A-Za-z0-9\-._~]`). A verifier outside this range returns a 400 `invalid_request` error. Some PKCE libraries default to shorter values that pass other OAuth2 providers but fail SLAS validation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| SLAS token acquisition module | PKCE-based guest and registered shopper token flows with proactive refresh logic |
| Commerce SDK React provider setup | `CommerceApiProvider` configuration and hook wiring for product, basket, and checkout |
| SCAPI fetch wrapper | Lightweight fetch layer with Bearer token injection, 503 retry, and exponential back-off for non-React frontends |
| Object-level cache design | Cache key schema and TTL strategy for SCAPI product and search responses |
| Basket merge implementation | Guest-to-registered basket merge call with session state cleanup |

---

## Related Skills

- admin/headless-commerce-architecture — architecture-level pattern selection for headless vs. hybrid storefronts; use before SCAPI development begins to confirm the storefront model
- apex/callouts-and-http-integrations — HTTP callout patterns and error handling; relevant for non-SDK SCAPI integrations
- apex/commerce-extension-points — Apex-based Commerce Cloud extension points for server-side pricing and inventory hooks in LWR stores
- security/api-security-and-rate-limiting — broader API security patterns including OAuth2 token storage and scope minimization
