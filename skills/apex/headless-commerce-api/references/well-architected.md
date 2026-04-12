# Well-Architected Notes — Headless Commerce API (SCAPI)

## Relevant Pillars

- **Security** — SCAPI's SLAS-based JWT model is purpose-built for public client authentication without secret exposure. Correct token storage (access tokens in memory, refresh tokens in `httpOnly` cookies) directly implements the Security pillar's requirements for credential protection. Using OCAPI session cookies instead of SLAS tokens violates this pillar by exposing session state to CSRF attacks. Scope minimization is also critical: SLAS tokens should request only the scopes required for the specific shopper action.

- **Performance** — Object-level caching of product data and search results directly reduces the number of live SCAPI calls, which is the primary mechanism for avoiding load-shedding 503s during peak traffic. Response-level caching is an anti-pattern that impairs cache-hit rates and forces all-or-nothing invalidation. Commerce SDK React's `react-query` layer provides built-in query deduplication and background refresh, which contributes to perceived performance for the shopper.

- **Reliability** — SCAPI's load-shedding behavior at 90% capacity means the API is operationally designed around the assumption that well-behaved clients implement retry logic with `Retry-After` respect. A storefront that does not implement retry is unreliable by design — it will surface false unavailability to shoppers at exactly the moments when traffic is highest. The basket merge pattern for guest-to-registered transitions is also a reliability concern: failing to implement it causes silent cart loss, which damages conversion.

- **Scalability** — SLAS token acquisition must scale with session volume. Guest token acquisition is cheap and stateless, but high-traffic storefronts should still cache tokens for the session duration rather than acquiring a new token per request. Token re-use across requests within the same session is the expected pattern. Commerce SDK React handles this via its internal token state management.

- **Operational Excellence** — Observability for SCAPI integrations requires tracking 503 frequency and `Retry-After` duration trends over time, not just error rates. A spike in 503s signals an approaching capacity event before it becomes a user-visible outage. Logging the SLAS token acquisition success and failure rates separately from API call failures helps isolate auth issues from availability issues.

---

## Architectural Tradeoffs

**SCAPI + Commerce SDK React vs. raw SCAPI REST calls**

Commerce SDK React provides significant benefits (automatic PKCE, token refresh, typed hooks, react-query deduplication) at the cost of coupling the integration layer to React. For React/Next.js storefronts, the SDK is the correct choice. For Angular, Vue, or custom framework storefronts, a raw SCAPI REST integration is necessary — this means manually implementing SLAS PKCE, refresh token rotation, and retry logic that the SDK would otherwise provide. The raw integration is more work but supports any frontend architecture.

**Object-level caching vs. no caching**

Forgoing a caching layer simplifies the implementation but makes the storefront fully dependent on SCAPI availability for every page render. During load-shedding events, uncached storefronts fail completely; cached storefronts degrade gracefully (serving stale-but-present product data while retrying in the background). The tradeoff is implementation complexity and cache invalidation correctness. For any production storefront with meaningful traffic, object-level caching is not optional — it is the primary reliability control.

**Guest token acquisition per-visit vs. session persistence**

Acquiring a new guest token on every visit keeps server state minimal but increases SLAS load. Persisting the refresh token across visits (via `httpOnly` cookie with a reasonable max-age) allows the storefront to silently re-acquire a fresh access token from the refresh token without a full PKCE round-trip. This is the recommended pattern for returning visitors — it reduces SLAS load and provides faster session initialization on re-visit.

---

## Anti-Patterns

1. **Using OCAPI patterns on a SCAPI endpoint** — Sending OCAPI `dwsid` session cookies or Account Manager client credentials to SCAPI endpoints produces 401 errors that look identical to expired-JWT errors, leading developers down a fruitless debugging path. OCAPI and SCAPI are architecturally incompatible; there is no incremental migration. Any OCAPI-origin auth code must be replaced entirely before calling SCAPI.

2. **Full response-level HTTP caching for product and search data** — Caching the raw SCAPI response body keyed on the full URL (including query parameters) creates an unmaintainable cache invalidation problem at scale. A single product price change requires invalidating every cached search query that included that product. This anti-pattern typically appears when developers apply generic HTTP caching middleware without understanding the SCAPI data model's composition of individually-identifiable objects.

3. **Ignoring Retry-After on HTTP 503** — Treating 503 as a fatal error or retrying immediately without reading `Retry-After` results in a storefront that amplifies SCAPI load-shedding events into full outages. SCAPI's 503 model is explicitly designed for well-behaved retry; ignoring it violates the operational contract between the client and the API and produces worse availability outcomes than any competitor's implementation during the same peak event.

---

## Official Sources Used

- B2C Commerce API — Why Use SCAPI: https://developer.salesforce.com/docs/commerce/commerce-api/guide/commerce-api-overview.html
- Headless Commerce with Salesforce Commerce API — Composable Storefront: https://developer.salesforce.com/docs/commerce/commerce-api/guide/composable-storefront.html
- B2B Commerce APIs — Storefront APIs: https://developer.salesforce.com/docs/commerce/commerce-api/guide/b2b-storefront-api.html
- SLAS (Shopper Login and API Access Service) Overview: https://developer.salesforce.com/docs/commerce/commerce-api/guide/slas.html
- Commerce SDK React (GitHub / npm): https://developer.salesforce.com/docs/commerce/commerce-api/guide/commerce-sdk-react.html
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
