# Headless Commerce Architecture — Architecture Decision Record

Use this template when documenting architecture decisions for a new or migrated headless B2C Commerce Cloud storefront.

---

## Project Context

**Project name:**
<!-- Name of the storefront or commerce implementation -->

**Commerce Cloud org type:**
<!-- B2C Commerce Cloud (Composable Storefront eligible) / B2B Commerce / Other -->

**SCAPI enabled on this org:**
<!-- Yes / No / Unknown — if No, stop: SCAPI must be enabled before Composable Storefront work begins -->

**Storefront type (new build vs. migration):**
<!-- New build | Migration from SFRA | Migration from custom OCAPI headless | Other -->

**Date:**
<!-- YYYY-MM-DD -->

**Author:**
<!-- Name and role -->

---

## 1. Storefront Stack Decision

### Decision

**Selected stack:**
<!-- Composable Storefront (PWA Kit on MRT) | SFRA | Custom React on custom hosting | Other -->

**Rationale:**
<!-- 2-4 sentences explaining why this stack was selected. Reference the team's frontend skills, business UX requirements, and migration constraints. -->

### Alternative Considered

**Alternative:**
<!-- What was the primary alternative? e.g., SFRA, fully custom React app -->

**Why not selected:**
<!-- 1-3 sentences. Be specific. -->

### SFRA vs. Composable Storefront Checklist

| Factor | Assessment |
|---|---|
| Frontend team has React/Next.js experience | Yes / No |
| Custom design system required (not Retail React App) | Yes / No |
| Managed Runtime acceptable for hosting | Yes / No |
| Third-party integrations primarily API-based | Yes / No |
| Business requires SFRA cartridge parity before go-live | Yes / No |
| Timeline allows Composable Storefront ramp-up | Yes / No |

---

## 2. Hosting Decision

### Decision

**Hosting target:**
<!-- Managed Runtime (MRT) | Self-hosted Node.js | Other -->

**Rationale:**
<!-- Why this hosting option? If not MRT, document the specific requirement that precludes MRT. -->

### Managed Runtime Configuration

*(Complete if MRT is selected)*

**PWA Kit version:**
<!-- e.g., 3.x -->

**MRT environment count:**
<!-- Development / Staging / Production -->

**CDN regions:**
<!-- Salesforce-managed multi-region (default) | Custom CDN layered on top -->

---

## 3. SLAS Authentication Model

### Session Types Required

| Session Type | Required? | Notes |
|---|---|---|
| Guest shopper (anonymous browsing) | Yes / No | SLAS `client_credentials` + PKCE |
| Registered shopper (account login) | Yes / No | Auth code + PKCE |
| Agent on behalf of shopper | Yes / No | Service console use cases only |

### SLAS Client ID Registration

**SLAS client ID registered:**
<!-- Yes / No — must be registered via SLAS management in Account Manager, not Setup connected apps -->

**Site ID:**

**Short code:**

**Redirect URI registered:**
<!-- Must match exactly what the frontend sends -->

### Token Storage Strategy

**Access token storage:**
<!-- In-memory (JavaScript variable) — REQUIRED. localStorage and sessionStorage are NOT acceptable. -->

**Refresh token storage:**
<!-- httpOnly cookie (recommended) -->

**Token refresh trigger:**
<!-- Proactive (refresh before expiry, recommended) | Reactive (on 401) -->

### Guest-to-Registered Basket Merge

**Basket merge implemented in login flow:**
<!-- Yes / No / Not applicable -->

**Merge strategy:**
<!-- `merge` (combine items) | `replace` (overwrite registered basket with guest items) -->

**Guest basket ID preserved through auth flow:**
<!-- Describe how the guest basket ID is stored and passed to the merge call after token exchange -->

---

## 4. SCAPI Endpoint Map and Latency Budget

**SCAPI hard timeout:** 10 seconds (HTTP 504). All SSR latency budgets must stay well below this.

| Page Type | SSR SCAPI Endpoints | Client-Side SCAPI Endpoints | Estimated SSR Latency |
|---|---|---|---|
| Product Detail Page (PDP) | | | |
| Product List Page (PLP) | | | |
| Search Results | | | |
| Cart / Basket | | | |
| Checkout | | | |
| Order Confirmation | | | |

**SSR call pattern:**
<!-- Sequential awaits | Promise.all parallel | Mixed -->

**Individual call timeout:**
<!-- Recommended: 4 seconds per call. Describe graceful degradation on timeout. -->

---

## 5. Caching Architecture

**Maximum TTL in use:** _______ seconds (must not exceed 86400 / 24 hours)

| Page Type | Cache TTL (seconds) | Cache Key Components | Personalized Content (client-side only) |
|---|---|---|---|
| Product Detail Page | | site-id, locale, currency, product-id | |
| Product List Page | | site-id, locale, currency, category-id | |
| Search Results | | site-id, locale, currency, query, page, sort | |
| Cart | 0 (not cached) | n/a | All content is shopper-specific |
| Checkout | 0 (not cached) | n/a | All content is shopper-specific |
| Home Page | | site-id, locale | |

**Locale dimension in all cache keys:** Yes / No

**Currency dimension in all cache keys:** Yes / No

**Cache invalidation strategy:**
<!-- How do catalog changes in Business Manager trigger cache invalidation in MRT? -->

---

## 6. Integration Points

| Integration | Type | Integration Point | Auth Method | Notes |
|---|---|---|---|---|
| Salesforce CRM (if applicable) | Salesforce org API | Server-side proxy | Connected App OAuth (separate from SLAS) | |
| Third-party search (if applicable) | Third-party API | Client-side or SSR | API key | |
| CMS (if applicable) | Third-party API | SSR or client-side | Delivery token | |
| Payment provider | Third-party API | Client-side | Public key only in browser | |

---

## 7. Well-Architected Review

### Performance

- [ ] SCAPI 10-second hard timeout acknowledged in SSR latency budget
- [ ] SSR-required SCAPI calls use parallel fetch with individual timeouts
- [ ] Web-tier cache-hit rate target defined: _______%
- [ ] Personalized content deferred to client-side

### Security

- [ ] SLAS PKCE enforced — no client secret in browser-side code
- [ ] Access tokens stored in memory only
- [ ] Refresh tokens in httpOnly cookies
- [ ] No credentials or secrets in frontend bundle

### Adaptability

- [ ] Third-party integrations at clear API boundaries
- [ ] PWA Kit component library replaceability confirmed
- [ ] Migration path from SFRA documented (if applicable)

### Reliability

- [ ] SCAPI HTTP 503 load-shedding handled with retry + back-off
- [ ] Graceful degradation defined for SCAPI timeout scenarios
- [ ] Cache-first architecture reduces live SCAPI dependency during peak

---

## 8. Open Risks and Decisions Deferred

| Risk / Open Item | Owner | Target Resolution Date |
|---|---|---|
| | | |

---

## 9. Sign-Off

| Role | Name | Date |
|---|---|---|
| Commerce Cloud Technical Lead | | |
| Frontend Architect | | |
| Security Review | | |
