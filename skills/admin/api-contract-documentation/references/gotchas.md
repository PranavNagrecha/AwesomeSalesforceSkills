# Gotchas — API Contract Documentation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: API Rate Limits Are Not a Fixed Published Number

**What happens:** Teams document a specific numeric daily API limit (e.g., "50,000 calls/day") sourced from general knowledge or old documentation. The actual limit depends on org edition, licenses, and Salesforce adjustments.

**Impact:** Documentation becomes stale or incorrect, leading consumer teams to design integrations around wrong limits.

**How to avoid:** Always retrieve the actual limit dynamically from `GET /services/data/vXX.0/limits` and reference the Salesforce Developer Limits Quick Reference cheatsheet. Never document a hardcoded number without sourcing it from the org's actual `/limits` response.

---

## Gotcha 2: OpenAPI Beta Does Not Cover Custom Apex REST Endpoints

**What happens:** Teams use the Salesforce sObjects OpenAPI beta endpoint to generate documentation and assume it covers all their APIs, including custom `@RestResource` Apex classes.

**Impact:** Custom Apex REST endpoints remain undocumented because the beta generator only covers sObjects CRUD endpoints.

**How to avoid:** The OpenAPI beta covers standard sObjects REST API only. All custom Apex REST endpoints must be hand-authored in OpenAPI 3.0 or another specification format.

---

## Gotcha 3: REQUEST_LIMIT_EXCEEDED (403) and HTTP 429 Have Different Recovery Paths

**What happens:** Integrations treat HTTP 403 REQUEST_LIMIT_EXCEEDED identically to HTTP 429 transient rate throttling, implementing the same exponential backoff retry.

**Impact:** Immediate retry on 403 fails repeatedly because the daily limit is not a transient state — it will not recover until the 24-hour rolling window resets.

**How to avoid:** HTTP 403 REQUEST_LIMIT_EXCEEDED requires waiting for the 24-hour window to reset (check the Sforce-Limit-Info header to estimate reset timing). HTTP 429 is transient throttling that responds to exponential backoff. Document these as separate error conditions with separate recovery procedures.
