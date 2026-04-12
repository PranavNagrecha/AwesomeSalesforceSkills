---
name: headless-commerce-architecture
description: "Use this skill when designing or evaluating a headless B2C Commerce storefront architecture — covering the Composable Storefront (PWA Kit on Managed Runtime), SCAPI-first API design, frontend framework selection, latency budgets, and caching strategy. NOT for standard SFRA storefronts, Experience Cloud headless CMS delivery, B2B Commerce architecture, or SCAPI implementation-level coding (use apex/headless-commerce-api for that)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Security
  - Scalability
triggers:
  - "should we use Composable Storefront or SFRA for our new Commerce Cloud implementation"
  - "PWA Kit deployment to Managed Runtime vs self-hosted infrastructure decision"
  - "how to design the caching layer for a headless B2C Commerce storefront using SCAPI"
  - "what is the canonical Salesforce headless commerce stack and how does it fit together"
  - "performance architecture for headless storefront under peak holiday traffic with SCAPI timeouts"
tags:
  - commerce-cloud
  - headless
  - PWA-kit
  - SCAPI
  - Composable-Storefront
  - Managed-Runtime
  - B2C-commerce
  - architecture
inputs:
  - "Business requirement: new storefront build vs. migration from SFRA"
  - "Traffic profile and peak concurrency expectations"
  - "Frontend team's framework experience (React/Next.js vs. other)"
  - "Custom UX requirements (static site generation, ISR, fully custom design system)"
  - "Existing Commerce Cloud org configuration (SCAPI enabled, SLAS client IDs registered)"
  - "Integration surface (third-party search, reviews, payments, CMS)"
outputs:
  - Headless architecture decision record (stack selection and rationale)
  - Composable Storefront deployment topology with Managed Runtime configuration guidance
  - SCAPI endpoint grouping and latency budget table
  - Cache-key design and TTL strategy for web-tier and object-level caching
  - SLAS auth model selection (guest, registered, agent-on-behalf-of-shopper)
  - Frontend framework selection recommendation with tradeoff documentation
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Headless Commerce Architecture

Use this skill when making or reviewing architecture decisions for a headless B2C Commerce Cloud storefront. It covers the canonical Composable Storefront stack (PWA Kit on Managed Runtime consuming SCAPI), frontend framework selection, SCAPI latency constraints, web-tier caching design, and the SLAS auth model that governs all Shopper API access. This skill does not cover SCAPI implementation-level coding — for that, use `apex/headless-commerce-api`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the storefront type.** Headless B2C Commerce (Composable Storefront / PWA Kit + SCAPI) is architecturally distinct from SFRA (Server-Side Rendering in Business Manager sandbox), Experience Cloud headless CMS delivery, and B2B Commerce. Mixing up these stacks is the single most common LLM error in this domain — verify which platform is in scope before any architecture guidance.
- **Establish SCAPI availability.** PWA Kit and Composable Storefront consume SCAPI exclusively. Confirm the Commerce Cloud instance has SCAPI enabled, the org has SLAS configured, and a SLAS client ID is registered in Account Manager for the target site. SFRA-only orgs cannot directly serve a Composable Storefront without SCAPI enablement.
- **Know the Shopper API hard timeout.** SCAPI enforces a hard 10-second timeout on Shopper API requests. Any architecture that relies on server-side composition or page assembly that chains multiple SCAPI calls synchronously will breach this budget under normal conditions. Latency budgets must account for this constraint at design time.
- **Understand Managed Runtime vs. self-hosting tradeoffs.** Managed Runtime (MRT) is Salesforce's managed hosting layer for PWA Kit — it provides CDN integration, serverless function routing, and automatic scaling without infrastructure management. Self-hosting PWA Kit bypasses MRT but requires the team to own CDN configuration, Node.js infrastructure, and deployment pipelines. Most architectures should start from MRT unless specific requirements (e.g., on-premise data residency) preclude it.

---

## Core Concepts

### The Canonical Headless Stack: Composable Storefront on Managed Runtime

The canonical Salesforce headless B2C Commerce architecture consists of three tiers:

1. **PWA Kit (Composable Storefront)** — the React-based frontend framework published and maintained by Salesforce. It provides the application shell, routing, server-side rendering (SSR) via React SSR, and a pre-built component library for common commerce pages (PDP, PLP, cart, checkout). Teams extend or replace components as needed. PWA Kit is the only officially supported way to deploy a headless storefront on Managed Runtime.

2. **Managed Runtime (MRT)** — Salesforce's cloud hosting service for PWA Kit deployments. MRT handles serverless function execution (for SSR), a multi-region CDN, automated deployment pipelines via the Retail React App CLI, and runtime environment variable management. Web-tier caching of server-rendered responses occurs at the MRT/CDN layer.

3. **Salesforce Commerce API (SCAPI)** — the exclusive backend API consumed by the frontend. SCAPI is organized into Shopper APIs (browse, basket, checkout, orders, customers) and Admin APIs (catalog management, inventory, pricing). The frontend exclusively calls Shopper APIs. Admin API calls originate from back-office tooling, not from storefront code.

Any component substituted into this stack (custom React build tool, self-hosted Node.js, third-party CDN) carries corresponding operational responsibility. The canonical stack is the lowest-risk path for teams new to Composable Storefront.

### SCAPI Latency Constraints and the 10-Second Shopper API Timeout

SCAPI enforces a hard 10-second timeout on Shopper API requests. If a Shopper API call does not complete within 10 seconds, SCAPI returns HTTP 504. This is not a configurable limit — it is platform-enforced for all tenants.

This constraint has direct architectural implications:

- **Server-side data composition** (assembling a page by calling multiple SCAPI endpoints in sequence on the server) is viable only when the total request chain completes well under 10 seconds. For product detail pages, this typically means no more than 2–3 sequential SCAPI calls (product detail + recommendations + promotions). Sequential chains of 4+ calls will breach the budget under real network conditions.
- **Parallel SCAPI calls** via `Promise.all` or equivalent reduce the wall-clock time but increase backend concurrency per page render. Load-test the parallel call pattern at expected peak concurrency before treating it as the standard pattern.
- **Cache-first architecture** is the primary mitigation. Product catalog data (PDPs, PLPs, search results) must be cached at the web tier (MRT CDN) and at the object level within the SSR layer. A cache hit on a product page eliminates all SCAPI calls for that render, making the 10-second timeout irrelevant for the majority of traffic.

### Web-Tier Caching: TTL Caps and Cache-Key Design

The MRT CDN layer caches server-rendered responses. Web-tier cache TTLs for SCAPI-backed responses are capped at 86400 seconds (24 hours) — this is the platform maximum. TTLs above this value are silently clamped to 86400.

Cache-key design is a first-class architectural decision because:

- **Under-keying** (using only the URL path as the cache key) causes cache collisions for locale-specific, currency-specific, or price-book-specific content. A PDP cached for `en-US/USD` will incorrectly be served to `fr-FR/EUR` shoppers unless locale and currency are part of the cache key.
- **Over-keying** (including session-specific or user-specific headers in the cache key) defeats the purpose of the web-tier cache — every user gets a cache miss and the SCAPI timeout risk returns.
- **Recommended cache-key components** for product pages: site ID, locale, currency, product ID. For search results: site ID, locale, currency, encoded query string, page number, sort order.

Personalized content (promotions for a specific shopper, saved addresses, order history) must never be cached at the web tier. Personalized data is fetched client-side after the page shell is served from cache.

### SLAS Authentication Architecture

The Shopper Login and API Access Service (SLAS) is the OAuth2 authorization server for all SCAPI Shopper API access. SLAS is architecturally distinct from Salesforce Identity (connected apps, OAuth flows on the Salesforce org). It is a dedicated service within the Commerce Cloud infrastructure.

SLAS issues short-lived JWT access tokens (default 30-minute expiry) and long-lived refresh tokens. All Shopper API requests require a valid SLAS JWT in the `Authorization: Bearer` header. There are no sessions, no cookies, and no OCAPI-style hook invocations in a SCAPI architecture.

The three session types and their architectural implications:

| Session Type | Grant Flow | Storefront Impact |
|---|---|---|
| Guest shopper | `client_credentials` + PKCE | Required for all anonymous browsing — even product catalog calls require a token |
| Registered shopper | Authorization code + PKCE | Token bound to customer identity; basket data is shopper-specific |
| Agent on behalf of shopper | SLAS agent grant | Only needed for service rep console use cases; not for standard storefront |

A critical architectural constraint: **guest basket IDs are bound to the guest token's subject claim**. When a shopper logs in, their cart cannot be accessed with the registered shopper token until a basket merge API call transfers the contents. This merge step must be designed into the cart and login flow.

---

## Common Patterns

### Pattern: Cache-First Page Architecture with Client-Side Personalization

**When to use:** Any product page (PDP, PLP, search results, category page) that serves the same content to all shoppers of the same locale and currency.

**How it works:**
1. Server-side render the product page shell using SCAPI product/search data. Set a web-tier TTL appropriate to catalog update frequency (typically 300–3600 seconds for most product pages; lower for promotions with near-term expiry).
2. Design the cache key to include site ID, locale, currency, and the content-specific identifier (product ID, search query, category ID). Exclude all session or user data from the cache key.
3. Serve the cached shell immediately. The page is complete and indexable without JavaScript — this is critical for SEO.
4. On the client side, after hydration, fetch personalized data (promotions for the current shopper, basket state, wishlist) from SCAPI using the SLAS JWT stored in memory. Inject personalized content into the already-rendered shell.

**Why not the alternative:** Full server-side assembly with personalization (including shopper-specific promotions in the SSR render) makes the page uncacheable at the web tier. Every page request becomes a live SCAPI call, and the 10-second timeout risk applies to all traffic at all times — including peak load.

### Pattern: SCAPI Parallel Fetch with Latency Budget Enforcement

**When to use:** A page requires data from multiple SCAPI endpoints (e.g., product detail + product recommendations + active promotions) and the data can be fetched independently.

**How it works:**
1. Identify which SCAPI endpoints are required for the server-side-rendered (above-the-fold) content vs. which can be deferred to client-side hydration.
2. Issue SSR-required calls in parallel using `Promise.all`. Set a per-call timeout (recommended: 4 seconds for individual calls, 7 seconds for the parallel group) so the page can render with partial data rather than timing out entirely.
3. On timeout or error, render the page with graceful degradation (e.g., no recommendations shown, promotions omitted) rather than returning a 500 or blank page.
4. Defer non-critical SCAPI calls (reviews, cross-sell recommendations, personalized content) to client-side hydration so they do not contribute to the SSR latency budget.

**Why not the alternative:** Sequential SCAPI calls for a 4-endpoint page will typically consume 2–6 seconds of the 10-second budget on network alone, leaving no margin for SCAPI processing time or temporary load-shedding events.

### Pattern: Storefront Stack Selection Decision (SFRA vs. Composable Storefront)

**When to use:** A new Commerce Cloud implementation or a storefront migration where the team must choose between SFRA and Composable Storefront.

**Decision framework:**

| Factor | Composable Storefront (PWA Kit) | SFRA |
|---|---|---|
| Frontend team skills | Strong React/Next.js experience | Salesforce ISML/server-side templating experience |
| Customization depth | Full UI/UX control; any React component | Constrained by ISML templates; plugin architecture |
| SEO requirements | SSR included; full control over markup | SSR included via Business Manager sandbox |
| Third-party integrations | Clean API boundary; any NPM package | Integration via SFRA cartridge system |
| Infrastructure ownership | Managed Runtime (Salesforce-managed) or self-hosted | Business Manager sandbox (Salesforce-managed) |
| Maintenance trajectory | Active investment from Salesforce | Maintenance mode; no new feature investment from Salesforce |

Composable Storefront is the strategic path for new implementations. SFRA remains the practical choice for teams with existing ISML investment or those who cannot staff React frontend engineers.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New B2C Commerce storefront, React team available | Composable Storefront (PWA Kit) on Managed Runtime, SCAPI | Strategic platform direction; MRT reduces operational burden |
| New B2C Commerce storefront, no React expertise | SFRA with plan to migrate when team capability builds | SFRA is stable; a headless migration with under-skilled team increases risk |
| Migrating from SFRA to Composable Storefront | Phased migration: Composable Storefront for new categories first, SFRA for existing until parity | Full-cutover migrations introduce high risk; phased reduces blast radius |
| Headless with custom design system (not Retail React App) | Use PWA Kit as the SSR and routing layer; replace component library with custom | PWA Kit's MRT integration is the value; the component library is replaceable |
| Heavy third-party integrations (search, CMS, reviews) | Wire integrations client-side or via server-side proxy on PWA Kit | SCAPI is not a middleware bus; third-party APIs should not be chained through SCAPI |
| High-traffic peak events (Black Friday, flash sales) | Cache-first architecture with web-tier TTLs; personalization client-side only | Eliminates SCAPI calls for catalog pages under load; critical for surviving 10-second timeout risk |
| Personalized promotions on product pages | Fetch promotions client-side after hydration; never include in SSR cache key | Personalized content in SSR makes the page uncacheable; negates web-tier cache entirely |
| Custom frontend framework (Angular, Vue, non-React) | Call SCAPI REST directly; do not use PWA Kit or Commerce SDK React | PWA Kit and Commerce SDK React are React-specific; non-React stacks must implement SLAS PKCE manually |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm the platform scope** — Verify this is a B2C Commerce Cloud headless architecture decision, not Experience Cloud CMS, B2B Commerce, or SFRA configuration. Collect: Commerce Cloud org type, SCAPI enablement status, existing storefront technology (if any), and business requirements driving the headless decision.
2. **Select the storefront stack** — Use the SFRA vs. Composable Storefront decision framework. If Composable Storefront is selected, confirm Managed Runtime is the hosting target unless specific data residency or infrastructure requirements mandate self-hosting. Document the stack decision and rationale in an architecture decision record.
3. **Design the SLAS authentication model** — Identify which shopper session types the storefront requires (guest, registered, agent). Document the token acquisition flow for each type, token storage strategy (access token in memory, refresh token in httpOnly cookie), and the basket merge flow for guest-to-registered transitions.
4. **Define the SCAPI endpoint map and latency budget** — List all SCAPI endpoints the storefront will call per page type (PDP, PLP, cart, checkout). Classify each call as SSR-required (must complete before HTML is sent) or client-side (can be deferred post-hydration). Verify the SSR-required call group fits within a 7-second parallel budget, leaving margin below the hard 10-second SCAPI timeout.
5. **Design the caching architecture** — For each page type, specify: (a) web-tier TTL in seconds (cap at 86400); (b) cache-key components (at minimum: site ID, locale, currency, content identifier); (c) which content is personalized and must be fetched client-side after hydration. Confirm no session or user-specific data is included in web-tier cache keys.
6. **Validate against Well-Architected pillars** — Check Performance (latency budget, cache-hit ratio targets), Security (SLAS token storage, PKCE enforcement, no secrets in frontend bundles), and Adaptability (integration points, component replaceability, migration path from SFRA if applicable).
7. **Produce and review the architecture deliverables** — Deliver: stack decision record, SLAS auth model document, SCAPI endpoint map with latency budget, cache-key design table, and any open risk items. Review with the Commerce Cloud technical lead before development begins.

---

## Review Checklist

Run through these before marking architecture work in this area complete:

- [ ] Architecture explicitly names Composable Storefront + PWA Kit + SCAPI as the canonical stack (not a custom combination without explicit rationale)
- [ ] SLAS is identified as the auth system (not Salesforce org OAuth, not Community auth, not OCAPI session cookies)
- [ ] SCAPI 10-second Shopper API hard timeout is acknowledged in the latency budget design
- [ ] Web-tier cache TTLs are at or below 86400 seconds (24 hours)
- [ ] Cache keys include locale and currency — no under-keying that would serve wrong-locale content
- [ ] Personalized content (shopper-specific promotions, basket state, saved addresses) is fetched client-side, not included in server-rendered cached responses
- [ ] Guest-to-registered basket merge is identified in the login flow design
- [ ] No OCAPI patterns (`/dw/shop/v*`, session cookies, hook classes) are referenced in the architecture

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **SCAPI Hard 10-Second Shopper API Timeout (HTTP 504)** — SCAPI enforces a non-configurable 10-second timeout on all Shopper API requests. Any SSR path that chains SCAPI calls sequentially or waits on slow upstream enrichment steps will return HTTP 504 to the browser, rendering the page blank. Latency budget design and aggressive web-tier caching are the only mitigations — the timeout cannot be extended.
2. **Web-Tier Cache TTL Hard Cap at 86400 Seconds** — MRT CDN enforces a maximum cache TTL of 86400 seconds (24 hours). TTL values set above this limit are silently clamped. Architecture documents that specify longer TTLs (e.g., 7-day catalog caches) will not behave as designed. If content genuinely needs cache lifetimes above 24 hours, an explicit cache invalidation strategy must be designed instead.
3. **SLAS Is Not Salesforce Identity** — SLAS is a separate OAuth2 service from the Salesforce org's connected app OAuth infrastructure. A client ID registered as a connected app in the Salesforce org does not work with SLAS. SLAS client IDs are registered through the SLAS management interface in Account Manager. Architectures that conflate the two OAuth systems will fail silently — SLAS returns `invalid_client` with no further diagnostic detail pointing to this misunderstanding.
4. **Guest Basket IDs Are Token-Bound — Merge Is Not Automatic** — Guest baskets are created under the guest token's subject claim. When a shopper authenticates, the registered shopper token cannot access the guest basket — calls return 403. The basket merge endpoint (`POST .../baskets/actions/merge`) is the only supported mechanism. If the login flow does not call the merge endpoint before discarding the guest basket reference, the shopper's pre-login cart items are silently lost.
5. **Under-Keying the Web-Tier Cache Causes Locale and Currency Cross-Contamination** — A common architecture oversight is using only the URL path as the cache key for product pages. If the same URL path serves multiple locales (e.g., via `Accept-Language` headers or session cookies), shoppers in different locales receive each other's cached page. Cache keys must include locale, currency, and any other dimension that affects page content. Over-keying on user-specific data is equally harmful — it makes every request a cache miss.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Stack decision record | Composable Storefront vs. SFRA decision with rationale, team capability assessment, and migration path if applicable |
| SLAS auth model document | Session type map (guest/registered/agent), token acquisition flows, token storage strategy, basket merge design |
| SCAPI endpoint map | Per-page-type list of SCAPI calls, classified as SSR-required or client-side, with latency budget per call group |
| Cache-key design table | Per-page-type cache-key components, TTL values (≤ 86400s), and personalized-content exclusion list |
| Architecture decision record | Formal ADR capturing stack, hosting, auth, caching, and integration decisions with open risks |

---

## Related Skills

- apex/headless-commerce-api — implementation-level SCAPI coding: SLAS token acquisition code, Shopper API wiring, Commerce SDK React hooks, load-shedding retry patterns; use this after architecture is decided
- admin/b2c-commerce-store-setup — Business Manager configuration for Commerce Cloud sites; use for SFRA storefronts or back-office setup prerequisites
- architect/headless-vs-standard-experience — headless architecture decisions for Experience Cloud (not Commerce Cloud); use when evaluating Experience Site headless CMS delivery, not storefront commerce

## Official Sources Used

- B2C Commerce API — Headless Commerce with Salesforce Commerce API: https://developer.salesforce.com/docs/commerce/commerce-api/guide/headless-commerce.html
- B2C Commerce API — Load Shedding and Rate Limiting: https://developer.salesforce.com/docs/commerce/commerce-api/guide/load-shedding.html
- SLAS (Shopper Login and API Access Service) Overview: https://developer.salesforce.com/docs/commerce/commerce-api/guide/slas.html
- Commerce SDK React: https://developer.salesforce.com/docs/commerce/commerce-api/guide/commerce-sdk-react.html
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
