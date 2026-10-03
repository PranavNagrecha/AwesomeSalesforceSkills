# LLM Anti-Patterns — Composable Commerce Architecture

Common mistakes AI coding assistants make when architecting headless / composable commerce on Salesforce.

## Anti-Pattern 1: Putting a SLAS client secret in the browser, or banning browser calls outright

**What the LLM generates:** One of two wrong answers. Either the frontend calls SCAPI with a private client's ID and secret embedded in JavaScript ("it's just a config value"), or the design forbids any browser-to-SCAPI call and routes everything through a BFF "because SCAPI needs a trusted intermediary".

**Why it happens:** The model collapses two documented client types into one. SLAS defines private clients, for apps that can keep a secret, and public clients, for single-page and mobile apps that cannot. Salesforce's own PWA Kit runs as a public client in the browser.

**Correct pattern:**

```
Browser code that calls SCAPI  -> SLAS public client, authorization code + PKCE, no secret.
BFF / full-stack server        -> SLAS private client, secret held server-side,
                                  Strict Client Auth on (x-slas-client-auth header).
Server-only logic (pricing, promo eligibility, catalog filtering) stays in the BFF
or in a SCAPI Custom API, whichever client calls SCAPI.
```

Source: B2C Commerce Developer Guide, Public and Private SLAS Client Use Cases; SLAS Best Practices (read 2026-10-03).

**Detection hint:** A SLAS client secret in a frontend bundle or environment file shipped to the browser; or a design that rejects PWA Kit's documented public-client model without a stated reason.

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

---

## Anti-Pattern 6: Load-testing SLAS on staging and reading the 429s as a capacity verdict

**What the LLM generates:** A load-test plan that drives login and token refresh at production volume against a staging instance, then concludes the storefront "cannot handle peak".

**Why it happens:** The model assumes rate limits scale with the environment's hardware. SLAS limits are fixed per instance: 24,000 requests per minute on production and 500 per minute on each non-production instance.

**Correct pattern:** Load-test browse and BFF paths on staging with SLAS stubbed or throttled to stay under 500 RPM. Validate SLAS volume against the production allowance with the Customer Success Manager, who can discuss adjustments for known peaks. Serialize token refresh per session, because one refresh token can be exchanged only 3 times in 60 seconds.

**Detection hint:** A performance report whose failures are all HTTP 429 from `/shopper/auth/` on a non-production instance.

