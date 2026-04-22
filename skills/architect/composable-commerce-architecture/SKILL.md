---
name: composable-commerce-architecture
description: "Composable commerce on Salesforce: headless API layer, micro-frontends, BFF pattern, CDN strategy, third-party composability over B2C/B2B Commerce. NOT for the standard B2C Storefront UX (use b2c-commerce-storefront-setup). NOT for Salesforce Order Management basics (use salesforce-order-management-setup)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Performance
  - Reliability
tags:
  - composable-commerce
  - headless
  - bff
  - micro-frontend
  - mach
  - commerce-cloud
  - cdn
triggers:
  - "how do i design composable headless commerce on salesforce"
  - "salesforce commerce cloud headless storefront architecture"
  - "bff backend for frontend in salesforce commerce"
  - "micro frontend storefront with salesforce commerce apis"
  - "cdn strategy for headless commerce storefront"
  - "replacing salesforce storefront with next.js mach"
inputs:
  - Commerce Cloud edition (B2C / B2B / B2B2C) and planned scope
  - Storefront technology choice (Next.js, Remix, SvelteKit, Hydrogen-like)
  - Integration surface (OMS, PIM, CMS, search, payments)
  - Traffic profile (peak-to-average ratio, geography, seasonality)
outputs:
  - API-layer topology (Commerce APIs, BFF, SCAPI coverage)
  - Storefront repo structure and deployment target
  - CDN, caching, and personalization strategy
  - Migration/decomposition plan from monolith storefront
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Composable Commerce Architecture

Activate when architecting a headless / composable commerce implementation on Salesforce Commerce Cloud (B2C or B2B): bespoke storefronts, micro-frontends, BFF middleware, multi-brand/multi-region front-ends over shared Commerce APIs. Composable commerce trades the shipped storefront for flexibility and frontend ownership — it is a deliberate architectural choice, not a default.

## Before Starting

- **Confirm the composable choice is warranted.** Composable commerce adds complexity: you now own a frontend codebase, a BFF, CDN config, caching, and observability. If the business can live with the shipped storefront, do that first.
- **Inventory the Commerce APIs in scope.** Salesforce Commerce API (SCAPI) covers catalog, cart, checkout, promotions, customer. Gaps (custom flows) become BFF-only features.
- **Understand the caching contract.** Composable sites live or die by cache strategy. Decide what is page-cached (catalog, PLP), what is edge-computed (personalization), what is origin-only (cart, checkout).

## Core Concepts

### Headless vs composable

Headless = decoupled frontend over one backend. Composable = best-of-breed assembly: Commerce Cloud for transactions, Contentful/Amplience for CMS, Algolia/Coveo for search, ShipStation for fulfillment. The integration layer (BFF) is what makes it composable.

### Backend-for-Frontend (BFF)

A thin service layer between the storefront and Commerce Cloud APIs. Aggregates calls, translates responses for the frontend, hosts business logic the frontend should not have (pricing rules, promo eligibility). Typically Node.js or serverless functions.

### MACH stack positioning

MACH = Microservices, API-first, Cloud-native, Headless. Salesforce Commerce Cloud with SCAPI fits MACH; pair with Next.js / Remix for the frontend. Cloud-native = the frontend lives in Vercel / Netlify / Cloudflare Pages, not in Commerce Cloud hosting.

### Edge rendering and CDN

Catalog pages are rendered at the edge (ISR / SSG), cached in CDN. Authenticated cart and checkout are origin-rendered. Personalization is edge-computed from a user cookie or header.

## Common Patterns

### Pattern: Next.js storefront with SCAPI + BFF

Next.js app on Vercel, reads from a Node BFF deployed on Vercel functions or a separate container. BFF authenticates to SCAPI via Client Credentials, applies markups, serves aggregated responses. CDN caches PLP/PDP at edge with ISR revalidation.

### Pattern: Multi-brand single Commerce Cloud

Brands share catalog/inventory but have distinct storefronts. BFF routes per brand. Brand config in Commerce Cloud site preferences; frontend derives brand from hostname.

### Pattern: Decompose monolith storefront incrementally

Phase 1: keep existing storefront; add headless for one PDP experiment. Phase 2: entire PLP+PDP composable; checkout stays on shipped. Phase 3: full composable including checkout. Gives learning at each phase.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard B2C UX needs | Shipped storefront | Lowest TCO |
| Brand-specific UX with perf requirements | Composable + Next.js | Frontend ownership |
| Multi-region with localization needs | Composable + edge rendering | Latency control |
| Short timeline, generic UX | Stay with shipped | Composable takes 6-9 months minimum |
| Team lacks frontend engineering | Don't go composable | Ops burden ≠ shipped |

## Recommended Workflow

1. Validate the composable decision vs shipped storefront with a capability gap analysis.
2. Draft the component architecture: storefront, BFF, CDN, PIM, CMS, search, payments.
3. Map every customer-facing flow to SCAPI endpoints; identify gaps that need custom Apex + custom APIs.
4. Select the frontend framework and deployment target; prototype a PDP to validate latency budget.
5. Build the BFF with a contract between frontend and Commerce Cloud; version the contract from day one.
6. Define caching strategy per route; instrument observability.
7. Rollout incrementally: A/B test the composable experience against the shipped storefront.

## Review Checklist

- [ ] Capability gap analysis shows composable is warranted
- [ ] BFF contract versioned and documented
- [ ] Caching strategy defined per route (edge / origin)
- [ ] Personalization approach clear (cookie / header / edge function)
- [ ] PCI scope minimized (checkout on hosted payment or tokenized)
- [ ] Observability: RUM, BFF logs, Commerce Cloud API metrics joined
- [ ] Rollback plan to shipped storefront documented

## Salesforce-Specific Gotchas

1. **SCAPI rate limits are per-client, not per-user.** A busy BFF can exhaust rate limits and throttle every user; design token rotation and per-endpoint budgets.
2. **Session affinity for cart lives with Commerce Cloud.** Composable frontends must pass the cart token consistently; losing it = empty cart.
3. **B2B promotions and pricing often require Apex extension points.** Plan the custom API surface alongside the frontend.

## Output Artifacts

| Artifact | Description |
|---|---|
| Capability gap analysis | Composable justification |
| BFF service contract | Endpoint catalog, schemas, versioning |
| Caching strategy doc | Per-route cache, CDN config, invalidation |
| Decomposition roadmap | Phased cutover with rollback |

## Related Skills

- `architect/multi-cloud-architecture` — adjacent cloud composition
- `integration/integration-pattern-selection` — BFF integration choice
- `security/oauth-and-jwt-patterns` — BFF auth to SCAPI
