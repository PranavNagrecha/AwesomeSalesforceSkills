# Well-Architected Notes — Headless Commerce Architecture

## Relevant Pillars

- **Performance** — The primary constraint on headless Commerce Cloud architecture. SCAPI enforces a hard 10-second Shopper API timeout (HTTP 504) with no tenant override. Web-tier cache TTLs are capped at 86400 seconds. Latency budget design and cache-first page architecture are not optional optimizations — they are required for production viability under peak load. Every architecture decision (SSR vs. client-side fetch, sequential vs. parallel SCAPI calls, cache-key design) must be evaluated against the performance pillar first.

- **Adaptability** — Composable Storefront's value proposition is component-level replaceability. The architecture should expose clear seams where third-party services (search, CMS, review platforms, payment providers) integrate without coupling into the core SCAPI data flow. PWA Kit's extensibility model allows replacing the Retail React App component library with a custom design system without changing the SSR/routing layer. Architectural decisions that tightly couple custom business logic to PWA Kit internals reduce long-term adaptability.

- **Security** — SLAS PKCE is the mandatory auth pattern for all Shopper API access. No client secret should exist in browser-side code — PKCE eliminates this requirement for public clients. Access tokens must be stored in memory only (not `localStorage` or `sessionStorage`). Refresh tokens must be stored in `httpOnly` cookies. Any architecture that puts credentials or tokens in client-accessible browser storage violates the security pillar.

- **Reliability** — SCAPI load-shedding at 90% server capacity returns HTTP 503 with a `Retry-After` header. Architectures that do not implement retry logic with back-off will surface false product-unavailable states to shoppers during normal peak traffic. Cache-first architecture reduces live SCAPI dependency and is the primary reliability mechanism — a high cache-hit rate means the storefront continues to serve catalog pages even during extended SCAPI 503 events.

- **Operational Excellence** — Managed Runtime (MRT) provides automated deployment pipelines, multi-region CDN, and serverless scaling without infrastructure management overhead. Choosing MRT over self-hosted PWA Kit reduces operational surface area significantly. Architecture should treat MRT as the default hosting path and document explicit rationale for any deviation.

---

## Architectural Tradeoffs

**SSR depth vs. cacheability:** Deeper server-side rendering (assembling more personalized content in the SSR response) improves perceived page completeness on initial load but makes the page uncacheable at the web tier. Shallow SSR (product shell only, personalization deferred to client) maximizes cache hit rates and reduces SCAPI dependency. The tradeoff point: SSR should include everything that does not vary by shopper identity (product data, locale-correct pricing, page structure) and exclude everything that does (promotions, basket state, recommendations requiring purchase history).

**Composable Storefront (PWA Kit) vs. fully custom React app:** PWA Kit on MRT provides MRT integration, deployment tooling, and the Commerce SDK React pre-wired. A fully custom React application gives more architectural freedom but requires the team to implement SLAS PKCE, token management, Commerce SDK React integration (or full raw-fetch implementation), and deployment/CDN infrastructure from scratch. For most implementations, PWA Kit is the lower-risk path. The custom path is warranted only when PWA Kit's conventions conflict with specific requirements that cannot be addressed through its extensibility model.

**SCAPI parallel calls vs. sequential calls in SSR:** Parallel calls reduce wall-clock SSR latency but increase backend concurrency per page render. Under moderate traffic, parallel calls are strictly beneficial. At very high concurrency (thousands of simultaneous SSR renders), parallel calls amplify SCAPI load. Cache-first architecture mitigates this because most requests are cache hits and generate no SCAPI calls — parallel vs. sequential is a meaningful decision only for uncached first-hit renders.

---

## Anti-Patterns

1. **Full SSR with personalization in every response** — Including shopper-specific promotions, recommendations based on purchase history, or real-time inventory availability in the SSR render makes every page response unique per shopper, defeating web-tier caching entirely. Under peak load, every page request becomes a live SCAPI call sequence, exposing all traffic to the 10-second timeout risk simultaneously. Correct pattern: SSR serves the catalog shell (same for all shoppers of a given locale/currency), personalization is fetched client-side after hydration.

2. **Using Salesforce org OAuth / connected app client IDs with SCAPI** — SCAPI and SLAS are not part of the Salesforce org's OAuth infrastructure. Connected app credentials, named credentials, and Salesforce Identity OAuth flows do not grant access to SCAPI endpoints. Architecture that routes Commerce data through the Salesforce org (e.g., Apex callouts to SCAPI) introduces unnecessary latency, requires manual token management, and bypasses Commerce SDK React's built-in auth handling. Correct pattern: the PWA Kit frontend calls SCAPI directly using SLAS JWT tokens; the Salesforce org is a separate integration target for CRM data only.

3. **URL-path-only cache keys for multi-locale storefronts** — Caching product pages with only the URL path as the cache key causes locale and currency cross-contamination when different locales share URL paths. Correct pattern: cache key always includes site ID, locale, and currency at minimum.

---

## Official Sources Used

- B2C Commerce API — Headless Commerce with Salesforce Commerce API: https://developer.salesforce.com/docs/commerce/commerce-api/guide/headless-commerce.html
- B2C Commerce API — Load Shedding and Rate Limiting: https://developer.salesforce.com/docs/commerce/commerce-api/guide/load-shedding.html
- SLAS (Shopper Login and API Access Service) Overview: https://developer.salesforce.com/docs/commerce/commerce-api/guide/slas.html
- Commerce SDK React: https://developer.salesforce.com/docs/commerce/commerce-api/guide/commerce-sdk-react.html
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
