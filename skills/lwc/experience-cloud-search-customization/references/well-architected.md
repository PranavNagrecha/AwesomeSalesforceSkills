# Well-Architected Notes — Experience Cloud Search Customization

## Relevant Pillars

- **Security** — Search scope directly controls what data is exposed to site visitors. Exposing objects not intended for a public or partner audience through an over-broad Search Manager scope is a data leakage risk. The Secure Guest User Record Access setting is a platform-enforced security control for unauthenticated access; bypassing or misconfiguring it violates the least-privilege principle.
- **Performance** — Federated search adds external latency to every search query. External endpoints that respond slowly degrade the perceived performance of the entire search experience. Keeping native search scope tight (only objects with meaningful indexed data) also reduces result set size and improves relevance, which reduces time-to-find-answer for users.
- **Reliability** — Federated search introduces an external dependency at query time. If the external endpoint is unavailable, federated results silently disappear. A well-architected federated search setup degrades gracefully — native Salesforce results continue to appear even when the external endpoint times out or returns an error.

## Architectural Tradeoffs

**Native search scope vs. federated search:**
Keeping all content in Salesforce (Knowledge articles, CMS content) and indexing natively is more operationally simple and gives the strongest search relevance tuning via promoted terms, synonyms, and search layouts. Federated search eliminates content duplication and enables real-time access to external system state, but introduces an external latency dependency and a more complex failure mode. Choose federated search when synchronizing content into Salesforce is prohibitively expensive or when the external system is the authoritative source and must remain so.

**Standard components vs. custom LWC search:**
Standard search components (the LWR `Search Bar`/`Search Results` or the Aura `Search`) are declarative, supported by Salesforce, and automatically pick up Search Manager scope and promoted terms. Custom LWC search using `lightning/uiSearchApi` gives full control over result layout and interaction but requires LWC development effort, testing, and ongoing maintenance as the API evolves. Use standard components unless the result layout requirement cannot be met declaratively.

**Guest search access vs. authenticated-only search:**
Enabling search for guest users dramatically increases the value of a self-service portal but requires deliberate sharing configuration and ongoing vigilance around the Secure Guest User Record Access setting. Restricting search to authenticated users is simpler and safer but reduces deflection potential for anonymous visitors. Evaluate based on the data sensitivity of searchable objects and the org's guest sharing policy.

## Anti-Patterns

1. **Over-broad Search Manager scope** — Leaving all org objects in the site's Search Manager scope because it was the default. Authenticated users may find objects across the org that were not intended to be exposed on the site. Guest users see zero results for restricted objects, creating a confusing and broken search experience. Always explicitly configure the scope to the minimum required set.

2. **Validating guest search only via admin Experience Builder preview** — Admin preview bypasses all guest sharing restrictions and the Secure Guest User Record Access setting. A configuration that looks correct in preview can be completely broken for real guest users. Every guest search configuration must be validated in an incognito session against the live site URL.

3. **Federated search with no degradation strategy** — Relying on the external endpoint being always-available and treating a silent absence of external results as acceptable. A well-architected federated search integration monitors endpoint availability and has a documented fallback (e.g., a status indicator telling users external results may be delayed), rather than silently dropping results without user awareness.

## Official Sources Used

- Salesforce Help — Customize Search in Experience Cloud — scope, search manager, and promoted terms behavior
- Salesforce Help — Federated Search in Experience Cloud — endpoint configuration, result schema, authentication
- Salesforce Help — Search Behavior in Experience Cloud — guest user search, Secure Guest User Record Access, object searchability prerequisites
- Salesforce Well-Architected Overview — architecture quality framing (Trusted/Easy/Adaptable pillars)
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
