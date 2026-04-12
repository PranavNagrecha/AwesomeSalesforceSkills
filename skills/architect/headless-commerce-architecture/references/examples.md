# Examples — Headless Commerce Architecture

## Example 1: Phased Migration from SFRA to Composable Storefront

**Context:** A mid-market retailer runs a high-traffic SFRA storefront with 20+ custom cartridges. The business wants to move to a headless architecture for UX flexibility and faster frontend iteration, but cannot afford a full-cutover rewrite.

**Problem:** A single-phase full migration requires parity feature work across 20+ cartridges while keeping the live SFRA storefront stable. Any gap in feature parity delays go-live indefinitely, and the team cannot staff two parallel development tracks for an extended period.

**Solution:**

Architecture approach:
1. Launch Composable Storefront (PWA Kit on MRT) for a single high-traffic category (e.g., new arrivals) where SFRA cartridge dependencies are minimal.
2. Route traffic to Composable Storefront via the CDN URL split for that category path — all other paths continue to serve from SFRA.
3. Both storefronts call the same SCAPI endpoints — no backend changes required. SLAS client IDs are registered once and shared.
4. Iterate on the Composable Storefront category in production, gathering performance and UX data.
5. Migrate additional categories incrementally as the Composable Storefront reaches feature parity for each.

Cache-key configuration for the split:
```
# MRT routing configuration (conceptual — actual config in package.json app.sites)
category/new-arrivals/* → Composable Storefront (MRT)
category/*              → SFRA (existing CDN)
```

**Why it works:** The phased approach isolates risk to a single category while building team capability on Composable Storefront under real traffic conditions. Because both storefronts call the same SCAPI backend, there is no data-layer divergence between the split paths. The team can course-correct on the Composable Storefront build without risking the rest of the catalog.

---

## Example 2: Cache-First PDP Architecture Surviving Black Friday Traffic

**Context:** A global apparel retailer operates a Composable Storefront with product detail pages that receive 50,000+ concurrent visitors during peak sale events. Previous architecture cached full SSR responses using only the URL path as the cache key.

**Problem:** During a peak event targeting a specific locale (UK), the cache served US-locale pages to UK shoppers because both locales shared the same URL path. Additionally, some product pages were not cacheable because SSR included shopper-specific promotions, causing all traffic to hit SCAPI live. During the peak event, SCAPI returned 504 on approximately 8% of requests due to the 10-second hard timeout being breached.

**Solution:**

Architecture changes:
1. **Separate SSR content from personalized content.** Product page SSR renders: product data, locale-correct pricing, catalog images, page structure. Personalized promotions, wishlist state, and recommendations are removed from SSR and fetched client-side post-hydration.
2. **Redesign cache key.** Cache key components: `{site-id}:{locale}:{currency}:{product-id}`. URL-only keying is replaced. Shoppers in different locales now receive independent cache entries.
3. **Set TTLs appropriate to catalog change frequency.** Core product data: 1800 seconds (30 minutes). Promotional pricing (sale events): 300 seconds (5 minutes). The 86400-second cap is never approached for frequently-changing sale content.
4. **Parallel SCAPI calls with per-call timeout.** SSR calls product detail and top recommendations in parallel via `Promise.all`. Individual call timeout: 4 seconds. If recommendations timeout, the page renders without the recommendations section rather than failing.

Result:
- Cache hit rate on PDP pages during the next peak event: approximately 94%, vs. less than 30% previously.
- SCAPI 504 errors: reduced to less than 0.1% of requests (only uncached first-hits and explicit cache misses).
- No locale cross-contamination.

**Why it works:** Cache-first architecture with correct cache-key design eliminates the vast majority of SCAPI calls during peak load. The 10-second timeout becomes a non-issue for cached content. Personalization moved client-side removes the constraint that made SSR responses uncacheable.

---

## Anti-Pattern: Using Experience Cloud Headless Patterns for Commerce Cloud Storefronts

**What practitioners do:** Teams familiar with Experience Cloud headless CMS delivery (LWR sites with guest user APIs, Community auth, Apex REST endpoints serving content) attempt to apply the same architecture to a B2C Commerce Cloud headless storefront. Specifically: using connected app OAuth (Salesforce org identity) for authentication, routing Commerce data through Apex REST controllers, and treating the Experience Site as the hosting layer.

**What goes wrong:**
- Commerce Cloud product data is not available through Apex REST or Experience Cloud APIs. Commerce Cloud and the Salesforce org operate as separate platforms with separate data stores.
- Connected app OAuth (Salesforce org) tokens are rejected by SCAPI endpoints — SCAPI requires SLAS JWT tokens, which are issued by an entirely separate OAuth2 service.
- Hosting a Commerce Cloud storefront on an Experience Site is not a supported architecture. PWA Kit is the storefront layer; MRT is the hosting layer.
- Teams waste weeks designing an auth and API topology that will not work before discovering the platform separation.

**Correct approach:** Treat B2C Commerce Cloud as a separate platform from the Salesforce org. The headless storefront is PWA Kit hosted on MRT. Authentication is SLAS. The API surface is SCAPI. The Salesforce org (with its connected apps, Apex, Experience Cloud) is a separate integration target for back-office and CRM data — not the storefront backend.
