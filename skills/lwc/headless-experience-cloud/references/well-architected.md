# Well-Architected Notes — Headless Experience Cloud

## Relevant Pillars

- **Security** — Public channels expose CMS content without authentication. Practitioners must deliberately decide whether content is safe to serve publicly and configure CORS to prevent unauthorized origins from calling the endpoint. Authenticated channels require a connected app with minimal OAuth scopes; over-scoped connected apps are a common security gap.
- **Performance** — The delivery API supports pagination. Fetching all content in a single unbounded request is a latency and payload risk as the CMS library grows. Edge caching (CDN layer in front of the delivery API calls) is an appropriate pattern for public channel content with low update frequency.
- **Adaptability** — Channel IDs are org-specific record IDs that differ across sandboxes and production. Hardcoding them creates a fragile coupling that breaks every time code is promoted. Externalizing channel IDs as environment variables is the adaptable pattern.
- **Reliability** — Token expiry must be handled for authenticated channels. An unhandled 401 response causes silent content delivery failures. Implement token refresh proactively before expiry rather than reactively on 401.
- **Operational Excellence** — The absence of Salesforce-side debug logs for CORS errors and public channel 403s means monitoring must be implemented on the client side. Log delivery API errors with full URL context (sanitized) so that org configuration issues (wrong channel ID, missing CORS entry) can be diagnosed without Workbench access.

## Architectural Tradeoffs

**Public vs authenticated channel** is the primary design decision. Public channels minimize auth complexity but remove the ability to deliver personalized or access-controlled content. Authenticated channels enable per-user content visibility but require a connected app, token management, and refresh logic in every client. Default to public channels for marketing content and authenticated channels for member-facing portals.

**Direct client-to-Salesforce vs proxy layer**: Browser-based frontends calling the delivery API directly are subject to CORS and IP restrictions. A thin server-side proxy (Node, Lambda, Cloudflare Worker) can shield the frontend from Salesforce's network-level policies, cache responses at the edge, and avoid CORS entirely. The tradeoff is operational overhead for the proxy layer. For high-traffic public sites, a proxy with CDN caching is the recommended architecture.

**Salesforce CMS vs external CMS**: If content volumes are large, authoring workflows are complex, or the content team already uses a dedicated CMS platform, evaluate whether Salesforce CMS is the right authoring tool versus bringing an external CMS in via CMS Connect. The headless delivery API is purpose-built for Salesforce-authored content; it is not a bridge to external CMS systems.

## Anti-Patterns

1. **Fetching all content without pagination** — Calling the delivery endpoint without `pageSize` and iterating to exhaustion is a reliability and performance risk. As the content library grows, the first page response time increases and the payload size becomes unpredictable. Always paginate using `pageSize` and follow `nextPageUrl` in the response.

2. **Hardcoding channel IDs and org-specific URLs** — Channel IDs are record IDs that differ between every org. Hardcoding them in source code causes deployment failures when the code is promoted to a different environment. The correct pattern is environment variables or a configuration service that resolves per-environment values at startup.

3. **Skipping CORS setup and discovering the failure in production** — CORS entries must be added in Setup before the first browser request. Discovering the omission in production, after a deployment, causes visible content failures in the browser that require a Setup change (not a code deploy) to resolve.

## Official Sources Used

- Salesforce CMS Developer Guide: Display CMS Content in Other Systems — content delivery API behavior, channel setup, public vs authenticated access
- Connect REST API Developer Guide: CMS Delivery Content resources — endpoint signatures, query parameters, pagination, response shape
- Salesforce Well-Architected Overview — architecture quality framing for security, adaptability, and reliability pillars (https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html)
- Integration Patterns — proxy layer and caching patterns for external content delivery (https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html)
- Salesforce Developer Blog: Build Static Sites with SF CMS Headless APIs — practical guidance on the headless delivery API for static site generators
