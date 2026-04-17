# Gotchas — CSP and Trusted URLs

## Gotcha 1: Wildcard subdomains

**What happens:** https://*.corp.com trusts unintended hosts.

**When it occurs:** Lazy allow-listing.

**How to avoid:** Trust the exact host you need.


---

## Gotcha 2: LWR vs. LEX confusion

**What happens:** Same URL added for wrong context silently fails.

**When it occurs:** Cross-environment feature.

**How to avoid:** Add Trusted URL per each context where the UI runs.


---

## Gotcha 3: CDN churn

**What happens:** Script URL changes version and the allow-list breaks.

**When it occurs:** Pinning a major version URL.

**How to avoid:** Use versioned URL patterns; monitor CSP violations in production.

