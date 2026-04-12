# LLM Anti-Patterns — Headless Commerce Architecture

Common mistakes AI coding assistants make when generating or advising on Headless Commerce Architecture.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Conflating SCAPI/Composable Storefront with Headless Experience Cloud CMS

**What the LLM generates:** Architecture guidance that mixes B2C Commerce Cloud headless patterns with Experience Cloud headless CMS patterns. For example: recommending a "headless Salesforce storefront" that uses LWR Experience Sites as the frontend layer, Connected App OAuth for authentication, and Apex REST endpoints to serve product catalog data. Or describing SLAS as equivalent to Community user authentication.

**Why it happens:** LLMs are trained on large volumes of Salesforce documentation that covers both Experience Cloud headless delivery and Commerce Cloud headless architecture. Both are described as "headless Salesforce" in many sources. The LLM conflates the two stacks because the general concept (API-first, decoupled frontend) is the same, even though the implementation stacks are entirely different platforms with different auth models, hosting layers, and API surfaces.

**Correct pattern:**

```
B2C Commerce Cloud Headless:
  Frontend: PWA Kit (Composable Storefront) on Managed Runtime
  Auth:     SLAS (Shopper Login and API Access Service) — issues JWT tokens
  API:      SCAPI (api.commercecloud.salesforce.com)
  Hosting:  Managed Runtime (MRT) CDN + serverless functions

Experience Cloud Headless CMS:
  Frontend: Custom SPA / framework consuming Experience Site APIs
  Auth:     Guest user or authenticated Community user (Salesforce Identity)
  API:      Experience Cloud APIs, Apex REST, Connect API
  Hosting:  External CDN + app server
```

These are separate stacks with no shared components. A Commerce Cloud storefront does NOT use Experience Site infrastructure, and an Experience Cloud headless site does NOT use SLAS or SCAPI.

**Detection hint:** Any response that mentions "Experience Site", "Community user", "Connected App" for storefront auth, or "Apex REST" for product catalog data in a Commerce Cloud headless architecture context is exhibiting this anti-pattern.

---

## Anti-Pattern 2: Treating SCAPI as Optional or Equivalent to OCAPI for New Headless Work

**What the LLM generates:** Architecture recommendations that describe OCAPI as a valid alternative to SCAPI for a new headless storefront, or suggest a "hybrid" approach mixing OCAPI session authentication with SCAPI product APIs.

**Why it happens:** LLMs trained on older Salesforce Commerce Cloud documentation see extensive OCAPI coverage and treat it as a peer option to SCAPI. The deprecation trajectory of OCAPI for new headless work is not consistently represented in training data.

**Correct pattern:**

```
New headless storefronts: use SCAPI exclusively.
OCAPI is in maintenance mode for new headless implementations.
OCAPI session authentication (session cookies, hook classes) has NO equivalent in SCAPI.
Mixing OCAPI auth with SCAPI product APIs is not a supported configuration.
```

**Detection hint:** Any reference to `/dw/shop/v*` OCAPI endpoints, OCAPI hook class registration, or OCAPI session cookies in a new headless storefront architecture is incorrect.

---

## Anti-Pattern 3: Placing Shopper-Specific Personalization in the SSR Cache

**What the LLM generates:** Architecture designs that include shopper-specific promotions, purchase-history-based recommendations, or real-time basket state in the server-rendered (SSR) page response, without flagging that this content makes the response uncacheable at the web tier.

**Why it happens:** LLMs optimize for "completeness" in the initial page load without accounting for the caching constraint. The naive answer to "show the shopper their personalized promotions on the PDP" is to include the promotions in the SSR render — which is technically correct but architecturally expensive.

**Correct pattern:**

```
SSR renders (cacheable):
  - Product data (name, images, base price, description)
  - Locale-correct catalog content
  - Page structure and navigation shell

Client-side fetch post-hydration (not cached):
  - Shopper-specific promotions
  - Recommendations based on purchase history
  - Basket state and item count
  - Saved address / payment instruments
```

**Detection hint:** Any architecture that includes shopper ID, basket ID, promotion personalization, or customer-segment-specific pricing in the SSR response without flagging it as a caching constraint is exhibiting this anti-pattern.

---

## Anti-Pattern 4: Ignoring or Mishandling the SCAPI 10-Second Shopper API Timeout

**What the LLM generates:** SSR page assembly designs that chain 4+ sequential SCAPI calls without a latency budget analysis, or retry logic that retries on HTTP 504 (which indicates the timeout was already exceeded — retrying a 504 is almost certain to 504 again if the underlying condition is load).

**Why it happens:** LLMs default to sequential `await` call patterns because they are simpler to generate. The 10-second hard timeout is a non-obvious platform constraint that is not always prominently documented in SCAPI reference material.

**Correct pattern:**

```javascript
// WRONG: Sequential SCAPI calls — will exceed 10-second budget under load
const product = await fetchProduct(productId);
const recommendations = await fetchRecommendations(productId);
const promotions = await fetchPromotions(productId);
const content = await fetchPageContent(productId);

// CORRECT: Parallel SCAPI calls with individual timeouts
const [product, recommendations, promotions] = await Promise.allSettled([
  withTimeout(fetchProduct(productId), 4000),
  withTimeout(fetchRecommendations(productId), 4000),
  withTimeout(fetchPromotions(productId), 4000),
]);
// Handle settled results — render page with available data, omit timed-out sections
```

**Detection hint:** Any SSR data-fetching pattern that uses sequential `await` for 3+ SCAPI calls without a latency budget justification is exhibiting this anti-pattern.

---

## Anti-Pattern 5: Recommending Self-Hosted PWA Kit as the Default Without Operational Justification

**What the LLM generates:** Architecture guidance that describes self-hosted PWA Kit (running on Kubernetes, EC2, or a custom CDN) as the default or equivalent-to-MRT option, without noting that self-hosting transfers all infrastructure, CDN configuration, scaling, and deployment pipeline responsibility to the implementation team.

**Why it happens:** LLMs trained on general cloud architecture patterns default to "deploy on your own infrastructure" as an implicit pattern. MRT as the preferred managed hosting layer for PWA Kit is a Salesforce-specific recommendation that may be underrepresented in training data relative to general cloud deployment patterns.

**Correct pattern:**

```
Default architecture: PWA Kit on Managed Runtime (MRT)
  - Salesforce-managed CDN, serverless functions, automated deployments
  - No infrastructure provisioning or CDN configuration required
  - Multi-region by default

Self-hosted PWA Kit: only when specific requirements preclude MRT
  - On-premise data residency requirements
  - Existing enterprise CDN contract that cannot be bypassed
  - Custom edge compute requirements not supported by MRT
  In all cases: document the operational responsibilities transferred to the team.
```

**Detection hint:** Any architecture that defaults to self-hosted Node.js, Kubernetes, or a custom CDN for PWA Kit without documenting a specific reason why MRT is not suitable is likely exhibiting this anti-pattern.

---

## Anti-Pattern 6: Using URL-Path-Only Cache Keys for Multi-Locale Storefronts

**What the LLM generates:** CDN or MRT caching configuration that sets the cache key to the URL path alone, without including locale and currency dimensions. Often presented as "standard CDN caching" without commerce-specific adaptation.

**Why it happens:** URL-path-only cache keys are the default in most CDN documentation. The locale/currency cross-contamination risk is specific to multi-locale commerce storefronts and is not a general CDN concern.

**Correct pattern:**

```
Minimum cache-key components for commerce pages:
  - site-id
  - locale (e.g., en-US, en-GB, fr-FR)
  - currency (e.g., USD, GBP, EUR)
  - content-specific identifier (product ID, search query, category ID)

Never include in cache key:
  - shopper ID or basket ID
  - session token or JWT
  - request-specific headers that vary per user
```

**Detection hint:** Any caching configuration that uses URL path as the sole cache key dimension for a multi-locale Commerce Cloud storefront is exhibiting this anti-pattern.
