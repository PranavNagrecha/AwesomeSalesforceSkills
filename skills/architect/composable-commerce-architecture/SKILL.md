---
name: composable-commerce-architecture
description: "Composable commerce on Salesforce: headless API layer, micro-frontends, BFF pattern, CDN strategy, third-party composability over B2C/B2B Commerce. NOT for the supported PWA Kit on Managed Runtime composable storefront — use architect/headless-commerce-architecture. NOT for standard B2C storefront setup — use admin/b2c-commerce-store-setup."
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
  - "size the API and SLAS budget for a headless storefront BFF before peak season"
  - "plan a phased headless rollout that keeps checkout on SFRA"
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Composable Commerce Architecture

Activate when architecting a headless / composable commerce implementation on Salesforce Commerce Cloud (B2C or B2B): bespoke storefronts, micro-frontends, BFF middleware, multi-brand/multi-region front-ends over shared Commerce APIs. Composable commerce trades the shipped storefront for flexibility and frontend ownership — it is a deliberate architectural choice, not a default.

## Before Starting

- **Confirm the composable choice is warranted.** Composable commerce adds complexity: you now own a frontend codebase, a BFF, CDN config, caching, and observability. If the business can live with the shipped storefront, do that first.
- **Inventory the Commerce APIs in scope.** Salesforce Commerce API (SCAPI) covers catalog, cart, checkout, promotions, customer. A gap can become a SCAPI Custom API (B2C Commerce Script API code in a cartridge, served under `/custom/{apiName}/{apiVersion}/organizations/{organizationId}/...` and cacheable) or BFF logic. Choose per gap; do not default everything into the BFF.
- **Understand the caching contract.** Composable sites live or die by cache strategy. Decide what is page-cached (catalog, PLP), what is edge-computed (personalization), what is origin-only (cart, checkout).

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which platform serves each journey: B2C Commerce through SCAPI, or B2B/D2C Commerce on the core org?" | The two sides have different limit models: SLAS and load shedding versus the org's 24-hour API allocation (Gotchas 1, 5, 6) | A per-journey limit budget against the right pool | Capacity planning uses the numbers that will actually throttle |
| "How many uncached BFF calls reach the core org per session at peak, and how long can each run?" | Community licences add no API allocation; 20-second calls contend for 25 slots (Gotchas 1, 2, 3) | A calls-per-session ceiling and a client timeout below 20 seconds | One slow storefront route cannot take down every integration in the org |
| "What is the peak SLAS login and token-refresh rate per instance, including staging load tests?" | SLAS limits are per tenant: 24,000 RPM production, 500 RPM per non-production instance (Gotcha 5) | Token traffic sized per instance, refresh serialized per session | Load tests that fail for the right reason, and no 429 storm at launch |
| "Where is the shopper's identity verified, and which SLAS client type does each component use?" | A BFF must be a private client; a browser app a public client; client-supplied identity is an IDOR (Gotchas 4, 7) | A private client with Strict Client Auth for the BFF, a public client for browser code | The platform's access model survives the move to a custom frontend |
| "Which journeys stay on SFRA during a phased rollout, and which frontend serves the rest?" | Custom headless plus SFRA is "possible but not formally supported"; Hybrid Auth targets PWA Kit v3 (Gotcha 8) | A phasing plan that names who owns session bridging | The unsupported part of the design is a recorded decision, not a surprise |
| "What does each route do on SCAPI 503 or 429?" | Browse APIs shed load; checkout does not; SLAS returns `Retry-After` (Gotchas 5, 6) | A per-route degrade rule in the BFF | Peak traffic degrades to stale catalog instead of blank pages |

What proper configuration adds over "just building a Next.js storefront": a capacity model per limit pool, an identity model the platform still enforces, and a phasing plan that knows where formal support ends.

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

Next.js app on Vercel, reads from a Node BFF deployed on Vercel functions or a separate container. BFF is registered as a SLAS private client (guest tokens via `grant_type=client_credentials`, registered shoppers via the authorization-code flow), applies markups, and serves aggregated responses. CDN caches PLP/PDP at edge with ISR revalidation.

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
| Short timeline, generic UX | Stay with shipped | Composable adds a frontend, a BFF, and a CDN to build and run (UNVERIFIED (2026-10-03): the often-quoted "6-9 months minimum" is a practitioner estimate) |
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

Full detail and sources in `references/gotchas.md`. The short list:

1. Customer Community and Customer Community Login licences add zero calls to the org's API allocation.
2. Requests of 20 seconds or longer share 25 concurrent slots across the whole org.
3. SLAS rate limits are per instance (24,000 RPM production, 500 RPM per non-production instance), not per client. This corrects an earlier "per-client" statement in this skill.
4. Browse APIs shed load with HTTP 503; Shopper Baskets and Shopper Orders do not.
5. A BFF must be a SLAS private client; browser code must use a public client.
6. Custom headless plus SFRA is outside formal support; Hybrid Auth (B2C Commerce 25.3+) targets PWA Kit v3.
7. B2B promotion and pricing gaps may need extension code on the core org (UNVERIFIED (2026-10-03): extension points not re-checked for this revision).

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
