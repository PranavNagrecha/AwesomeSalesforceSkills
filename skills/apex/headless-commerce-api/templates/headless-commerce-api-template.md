# Headless Commerce API (SCAPI) — Work Template

Use this template when working on SCAPI headless storefront development tasks.

## Scope

**Skill:** `headless-commerce-api`

**Request summary:** (fill in what the user asked for — e.g., "implement SLAS guest token acquisition for Next.js storefront," "add basket merge on login," "debug 503 retry handling")

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here before writing any code.

- **API in use:** [ ] SCAPI (`api.commercecloud.salesforce.com`) — NOT OCAPI (`/dw/shop/v*`)
- **SLAS client ID confirmed registered:** [ ] Yes — Client ID: _____________
- **Redirect URI registered in SLAS:** (exact value) _____________
- **Site / Org / Short Code:**
  - Org ID: _____________
  - Site ID: _____________
  - Short code: _____________
  - Locale: _____________
- **Session type required:** [ ] Guest only  [ ] Registered shopper  [ ] Agent-on-behalf-of-shopper  [ ] All three
- **Frontend framework:** [ ] React / Next.js (use Commerce SDK React)  [ ] Angular / Vue / other (implement SLAS manually)
- **Known constraints / prior issues:** _____________

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] **Guest SLAS PKCE token acquisition** — visitor has no session; need to acquire guest access token before any Shopper API call
- [ ] **Registered shopper auth + basket merge** — shopper logs in; must merge guest basket before discarding guest token
- [ ] **Commerce SDK React hook integration** — React/Next.js frontend; use `CommerceApiProvider` + typed hooks
- [ ] **Manual SCAPI REST integration** — non-React frontend; implement SLAS PKCE and token refresh manually
- [ ] **Load-shedding retry wrapper** — production traffic; add `Retry-After`-aware retry logic to all SCAPI calls
- [ ] **Object-level product caching** — high traffic; cache individual product objects, not full search responses

## SLAS Configuration Checklist

Before writing auth code:

- [ ] Confirmed client ID is registered in SLAS (not Account Manager)
- [ ] Confirmed redirect URI matches exactly (including protocol, trailing slash)
- [ ] Confirmed site ID (channel ID) is correct for the target store
- [ ] Confirmed the required grant type (client_credentials for guest; authorization_code for registered shopper)
- [ ] PKCE code verifier will be 43–128 URL-safe Base64 characters (`[A-Za-z0-9\-._~]`)

## API Wiring Checklist

- [ ] All SCAPI endpoints use `https://{shortCode}.api.commercecloud.salesforce.com/...` — no OCAPI paths
- [ ] Every Shopper API request includes `Authorization: Bearer <access_token>` header
- [ ] Access tokens stored in memory only (never `localStorage`)
- [ ] Refresh tokens stored in `httpOnly` cookies or equivalent secure server-side storage
- [ ] Token refresh triggered proactively (60 seconds before expiry) — not reactively on 401

## Basket Lifecycle Checklist (if basket work is in scope)

- [ ] Guest token acquired before basket creation
- [ ] Guest basket ID preserved in client state before the login redirect begins
- [ ] Basket merge endpoint called with registered token + guest basket ID after login
- [ ] Guest basket reference cleared from client state after successful merge
- [ ] Merge strategy confirmed: `merge` (combine items) or `replace` (overwrite with guest items)

## Resilience Checklist

- [ ] All SCAPI calls wrapped in a retry handler
- [ ] HTTP 503 handled by reading `Retry-After` header value (seconds) before retrying
- [ ] Random jitter (0–500 ms) added to `Retry-After` wait to prevent thundering herd
- [ ] Maximum retry count capped (recommended: 3)
- [ ] After max retries exhausted, graceful degradation message shown to shopper (not an unhandled exception)
- [ ] HTTP 401 triggers token refresh + single retry — not the same retry loop as 503

## Caching Checklist (if caching is in scope)

- [ ] Product objects cached individually under `productId:locale:priceBook` key
- [ ] Full search responses NOT cached as a single blob under the query URL
- [ ] Search result ID lists cached briefly (1–5 minutes) separately from product payloads
- [ ] Cache invalidation strategy documented for product updates
- [ ] Basket, order, and session endpoints explicitly excluded from caching

## Review Checklist

- [ ] No OCAPI endpoint URLs or session cookie patterns in the codebase
- [ ] No `client_secret` sent from browser-side SLAS token requests
- [ ] PKCE code verifier is 43–128 characters of URL-safe Base64
- [ ] Guest-to-registered basket merge implemented when login flow is present
- [ ] Retry wrapper respects `Retry-After` on HTTP 503 — not an immediate retry
- [ ] Caching is at object level, not response level
- [ ] Commerce SDK React used for React/Next.js integration (not manual SLAS from scratch)

## Notes

Record any deviations from the standard pattern and the reason for the deviation.

(example: "Angular frontend requires manual SLAS implementation — Commerce SDK React is React-specific")
