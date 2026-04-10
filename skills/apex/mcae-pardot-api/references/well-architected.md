# Well-Architected Notes — MCAE (Pardot) API v5

## Relevant Pillars

- **Security** — API v5 mandates Salesforce OAuth (Connected App) for all authentication. No standalone Pardot credentials are accepted. The Connected App must follow least-privilege scoping: request only the `pardot_api` OAuth scope, not broad Salesforce admin scopes. Client secrets must be stored in secure credential stores (Named Credentials in Salesforce, environment variables server-side), never in source code or browser-side JavaScript. Form Handlers are the correct pattern for collecting prospect data from external forms because they expose a public URL with no credential exposure.
- **Performance** — API v5 caps list responses at 200 records per page. Integrations that need to export large datasets must implement nextPageMark pagination and process records in batches. Avoid querying all fields (`fields=*`) — always specify only the fields needed to reduce payload size and latency. For high-frequency upsert patterns, batch multiple field updates into a single PATCH rather than issuing sequential single-field updates.
- **Scalability** — Account Engagement imposes API call rate limits (varies by edition; Standard and Plus editions have lower limits than Advanced and Premium). Design integrations to queue requests and implement exponential backoff on 429 responses. For bulk prospect imports, evaluate whether a native Salesforce data import or Marketing Cloud data sync is more appropriate than individual API calls.
- **Reliability** — OAuth tokens expire; integrations must implement token refresh using the `refresh_token` grant. Network failures should be retried with idempotency awareness: Prospect POSTs are upserts by email, so retrying a failed POST is safe. Visitor Activity queries are read-only and fully idempotent. Store the `nextPageMark` value during long pagination runs so interrupted exports can resume from the correct position rather than restarting from page one.
- **Operational Excellence** — All API integrations should log the `Pardot-Business-Unit-Id`, request timestamp, HTTP status, and the returned Prospect `id` for every mutation. This enables debugging of silent upserts and allows correlation of API activity with MCAE engagement logs. Version your integration explicitly against API v5 so that future deprecation notices are caught early.

## Architectural Tradeoffs

**Form Handler vs. Prospects API for web form submissions**
- Form Handler: no server-side credential management required; supports native MCAE completion actions (list adds, autoresponders, CRM tasks); limited to standard HTML form POST from the browser. Correct choice when the submission source is a browser form and no custom server logic is needed.
- Prospects API: full programmatic control; supports complex field logic, conditional updates, and integration with non-form data sources (CRM events, e-commerce, support tickets). Requires server-side credential management. Correct choice for backend integrations.

**Batch export via API vs. native MCAE reporting**
- API-based export (VisitorActivities): complete programmatic access; supports custom filters and incremental exports. Must handle pagination and rate limits.
- Native MCAE reporting (built-in dashboards, exports): simpler but limited to predefined dimensions; not suitable for warehouse-level ETL. Use the API for custom data pipelines; use native reporting for operational marketing reviews.

## Anti-Patterns

1. **Hardcoding API v3/v4 Endpoints** — Using deprecated `https://pi.pardot.com/api/3/do/...` or `https://pi.pardot.com/api/4/...` endpoints in new integrations. These endpoints are deprecated and may be removed. All new integrations must use `https://pi.pardot.com/api/v5/objects/...`. Migrate existing integrations proactively.

2. **Offset-Based Pagination** — Implementing list queries with a `page` counter instead of `nextPageMark` cursor. v5 does not honor offset parameters; the result is silent first-page repetition and incomplete data exports. Always follow the `nextPageMark` cursor from the response.

3. **Exposing Client Credentials in Browser-Side Code** — Calling the Prospects API directly from JavaScript running in the browser, which exposes the OAuth client secret. Use Form Handlers for browser-initiated submissions. Server-side API calls must be made from a trusted server or Salesforce org component (Named Credential, Apex callout), never from browser JavaScript.

4. **Conflating MCAE Prospects with Salesforce CRM Leads/Contacts** — Attempting to read or write Salesforce Lead/Contact fields through the MCAE API, or attempting to read Prospect engagement data through the CRM REST API. These are distinct systems with distinct APIs. The bidirectional sync is managed by Marketing Data Sharing rules, not by the API caller.

## Official Sources Used

- Account Engagement API v5 Overview — https://developer.salesforce.com/docs/marketing/pardot/guide/overview.html
- Prospects API v5 — https://developer.salesforce.com/docs/marketing/pardot/guide/prospects-v5.html
- Visitors API v5 — https://developer.salesforce.com/docs/marketing/pardot/guide/visitors-v5.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
