# LLM Anti-Patterns — Composable Commerce Architecture

Common mistakes AI coding assistants make when architecting headless / composable commerce on Salesforce.

## Anti-Pattern 1: Skipping the BFF and calling SCAPI from the browser

**What the LLM generates:** Frontend fetches SCAPI directly using a client-side token; "saves a hop."

**Why it happens:** The model treats SCAPI as just another REST API and forgets it is designed for a thin trusted intermediary.

**Correct pattern:**

```
All SCAPI calls go through the BFF. BFF holds the Client-Credentials
grant, applies server-only logic (pricing, promo eligibility, catalog
filtering), and returns a frontend-shaped DTO. The browser never sees
a SCAPI token or raw SCAPI payload.
```

**Detection hint:** Frontend code imports a `@salesforce/commerce-sdk` directly; SCAPI endpoints appear in browser network tab.

---

## Anti-Pattern 2: Caching authenticated pages at the CDN edge

**What the LLM generates:** CDN config caches every route aggressively, including cart and account pages; "for perf."

**Why it happens:** The model applies blanket CDN rules without distinguishing public from authenticated.

**Correct pattern:**

```
Public pages (PLP, PDP, content) = edge-cached with ISR. Authenticated
pages (cart, checkout, account) = origin-only, no-store. Personalized
content = edge function reads cookie/header and fetches BFF variant.
Route-level cache policy, not blanket.
```

**Detection hint:** CDN config has a global max-age that includes `/cart` and `/account`.

---

## Anti-Pattern 3: Copy-pasting the shipped storefront's checkout into the composable app

**What the LLM generates:** Rewrites the checkout in React, re-implements tax/payment/shipping calculations client-side.

**Why it happens:** The model reads the SFRA checkout code and ports it. It does not realize SCAPI checkout endpoints exist and PCI scope balloons if you self-host payment forms.

**Correct pattern:**

```
Use SCAPI checkout endpoints or a hosted payment page. Do NOT touch
raw card data in the composable frontend unless the team has a
dedicated PCI-DSS compliance program. Tokenize at the payment
processor, pass tokens to Commerce Cloud.
```

**Detection hint:** React component renders a raw credit card form; no mention of hosted payment page or tokenization service.

---

## Anti-Pattern 4: Shared BFF for multiple brands with no tenancy model

**What the LLM generates:** One BFF serves brand-A and brand-B from the same deployment; brand is a header.

**Why it happens:** The model optimizes for infra simplicity and forgets that brand config, markups, and catalog scopes need routing.

**Correct pattern:**

```
BFF is brand-aware: derives brand from hostname, loads brand-specific
config (catalog scope, price book, markup), applies per-brand rate
limiting. A compromised token for brand-A must not fetch brand-B data.
Prefer a single deployment with brand context over N brand copies.
```

**Detection hint:** BFF handler reads a `brand` query param with no validation and uses it directly in SCAPI calls.

---

## Anti-Pattern 5: No rollback plan from composable back to shipped

**What the LLM generates:** Full cutover from SFRA to composable on a single release day; "we can always redeploy the old version."

**Why it happens:** The model underestimates how much state drifts after cutover: cart tokens, session cookies, promotion assignments.

**Correct pattern:**

```
Rollback plan documented BEFORE cutover. Options include route-level
fallback (composable for PLP, shipped for checkout) and a feature
flag to divert traffic. Cart/session state must survive rollback or
you orphan in-flight orders.
```

**Detection hint:** Project plan has "Go live" with no rollback entry and no feature-flag gating.
