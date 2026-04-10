# Well-Architected Notes — Marketing Integration Patterns

## Relevant Pillars

### Security

Marketing Cloud integrations expose customer PII (email addresses, behavioral data, purchase history) over REST API calls. Security requirements include:

- OAuth 2.0 client credentials (`clientId` and `clientSecret`) must be stored in secrets management systems (environment variables, secret vaults) — never hardcoded in source code or configuration files.
- Access tokens are short-lived (20 minutes). Token refresh must be automated; exposed tokens should be treated as compromised.
- Installed Package scopes should follow the principle of least privilege — a Triggered Send integration does not need `Journeys > Execute` scope.
- SFTP transfers must use SFTP (SSH-based) protocol, not FTP. Marketing Cloud SFTP credentials are separate from API credentials and must be rotated on a schedule.
- MC Connect traffic between Salesforce core and Marketing Cloud uses the Connected App OAuth flow — this must be reviewed against org-level IP restrictions.

### Reliability

Marketing Cloud APIs are external service dependencies. Integrations must treat them as unreliable at any given moment:

- Triggered Send and Event API calls can return 429 (rate limit) or 5xx (transient server error). Implement exponential backoff with jitter for retry logic.
- Async batch Journey injection returns a `requestId` — poll for completion status rather than assuming success after HTTP 202.
- SFTP file drops and Automation Studio automations have dependency chains. A failed Import Activity silently stops the downstream send pipeline. Build monitoring and alerting on Automation Studio activity status.
- Triggered Send Definitions can auto-pause on volume thresholds. Design operational runbooks for TSD re-activation.

### Scalability

Pattern selection has direct scalability implications:

- Triggered Send and synchronous Event API calls are single-contact operations. For high-volume real-time use cases, they require horizontal scaling of the calling system and must respect Marketing Cloud API rate limits.
- Async batch Event API (up to 100 contacts/request) provides a middle ground for near-real-time bulk enrollment.
- SFTP import is the only pattern that scales to millions of records — it bypasses per-record API overhead entirely.
- MC Connect SDEs are refreshed on a schedule; they are not appropriate for use cases requiring sub-minute data freshness.

### Operational Excellence

- Each integration pattern has observable failure modes: Triggered Send API returns 400 on inactive TSD, Event API returns 400 on wrong `eventDefinitionKey`, SFTP import silently skips mismatched columns.
- All API integrations should log request ID, HTTP status, and error response body for every call.
- Automation Studio provides an Activity Log — surface this in operational dashboards.
- Separate Installed Packages per environment (production, sandbox) prevent production token leakage and allow scope changes to be tested safely.

---

## Architectural Tradeoffs

### Real-Time vs. Batch

Triggered Send and Journey Injection provide real-time or near-real-time contact engagement but require external systems to maintain API client code, token management, and retry logic. SFTP batch is operationally simpler for bulk data but introduces 15–60 minutes of latency. Choosing the wrong pattern for the latency requirement (e.g., using batch SFTP for transactional emails, or using per-call API for million-record audience sync) creates either poor customer experience or unsustainable operational complexity.

### Single-Message vs. Journey Enrollment

Triggered Sends are optimized for one-shot delivery — they are simpler, lower latency, and require less Marketing Cloud configuration. Journey Injection is necessary when message logic must branch or sequence based on subscriber behavior. Using Journey Injection for simple transactional sends adds unnecessary latency and Journey quota consumption.

### Custom API Integration vs. MC Connect

When Salesforce CRM is the data source, MC Connect Synchronized Data Extensions avoid custom API code entirely. The tradeoff is that SDEs are read-only in Marketing Cloud and refresh on a schedule (not real-time). Custom API integration (e.g., Apex callout to Marketing Cloud REST API) provides more control and real-time capability but requires ongoing maintenance and security management of credentials.

---

## Anti-Patterns

1. **Re-authenticating on Every API Call** — Obtaining a new OAuth 2.0 token for each Triggered Send or Journey Injection call is wasteful and can trigger rate limits on the auth endpoint. Tokens are valid for 20 minutes and must be cached. This anti-pattern is common when developers treat the token endpoint like a session login rather than a credential exchange.

2. **Using a Single Installed Package for All Integration Contexts** — Sharing one Installed Package and its credentials across production, staging, and development environments means a compromised credential affects all environments simultaneously. It also prevents scope isolation — a development integration with broad scopes exposes production systems. Use separate Installed Packages per environment and per integration concern.

3. **Ignoring Silent Import Failures in SFTP Batch** — SFTP Import Activities that fail column mapping do not surface errors in a way that breaks the Automation Studio automation chain. Downstream sends execute against a stale or empty Data Extension. Without an explicit record-count validation step, these failures can persist undetected for days.

---

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Marketing Cloud REST API Overview — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/rest-api.html
- Marketing Cloud API Integration (Installed Package) — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/mc-create-an-installed-package.html
- Fire Entry Event (Journey Injection) — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/postEvent.html
- Insert Contacts Async (Batch Journey Injection) — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/postEventAsync.html
- Triggered Send Definition REST API — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/messageDefinitionSends.html
