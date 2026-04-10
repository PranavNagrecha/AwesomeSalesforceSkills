# Well-Architected Notes — Marketing Cloud API

## Relevant Pillars

- **Security** — OAuth 2.0 client credentials from a Marketing Cloud Installed Package are the only supported authentication mechanism. Client ID and Client Secret must be stored in Custom Metadata, Named Credentials, or a secrets manager — never hardcoded in Apex or configuration files. Tokens are short-lived (typically 20 minutes) and must not be logged or persisted beyond their use. API Integration components in Installed Packages should be granted the minimum required scopes (e.g., only `journeys_read` and `journeys_write` if journey injection is all that is needed).
- **Performance** — Tokens should be cached and reused for their lifetime rather than requested per API call. Bulk DE operations should use the async (`dataeventsasync`) endpoint to avoid blocking Apex threads and hitting account-level rate limits. Batch requests should be chunked to stay within documented row limits per request.
- **Reliability** — Journey injection returns 201 on acceptance, not on confirmed contact entry. DE async inserts return a `requestId` that must be polled for completion status. Any integration that does not implement status verification and retry logic for error states will silently lose data. Implement idempotency using DE primary keys (upsert rather than insert) where possible to tolerate retries safely.
- **Operational Excellence** — Log the full response body for every Marketing Cloud API call, not just the HTTP status code. Marketing Cloud error messages are in the response body and are often the only diagnostic signal. Store `requestId` values for async operations with timestamps so operations can be monitored and retried.

## Architectural Tradeoffs

### REST vs SOAP

The Marketing Cloud REST API is the documented preferred approach for new integrations: JSON-native, simpler authentication handshake, and broader coverage of modern features (Journey Builder, Content Builder, Transactional Messaging). The SOAP API predates REST and is still required for some legacy operations (e.g., full `TriggeredSendDefinition` lifecycle management in older MC configurations), but should not be chosen for new work unless a specific operation has no REST equivalent.

### Synchronous vs Asynchronous DE Row Operations

The synchronous endpoint (`/hub/v1/dataevents/key:{ExternalKey}/rowset`) is appropriate for real-time, low-volume row operations where immediate confirmation is required. For any batch or bulk scenario — generally above ~100 rows or in any context where throughput matters more than immediacy — the async endpoint (`dataeventsasync`) is the correct choice. The async pattern decouples submission from confirmation, avoids blocking Apex threads, and reduces the risk of hitting account-level throttle limits.

### Credential Isolation per Business Unit

In multi-BU Marketing Cloud orgs, using a single Installed Package credential set across Business Units is an architectural anti-pattern. Each BU's API Integration credentials are scoped to that BU. Sharing credentials across BUs either fails with permission errors or, if a parent BU package is used, creates unexpected cross-BU data access risks. Design credential management to map one credential set per target BU.

## Anti-Patterns

1. **Requesting a new OAuth token on every API call** — This exhausts the token endpoint's rate allowance and introduces unnecessary latency. Tokens are valid for ~20 minutes. Implement a token cache (e.g., a static variable in Apex or a short-lived Custom Setting value) that checks expiry before requesting a new token. This is the documented best practice for MC API integrations.

2. **Using a generic or non-tenant-specific base URL** — Old documentation and blog posts reference `exacttarget.com` or shared endpoint URLs that are no longer valid. All current Marketing Cloud REST and auth endpoints are tenant-specific subdomains. Using a generic URL causes cryptic authentication failures or 404 errors. Always derive the base URL from the Installed Package's subdomain field.

3. **Treating HTTP 201 from journey injection as end-to-end confirmation** — The `interaction/v1/events` endpoint is asynchronous by design. A 201 response confirms the request was queued, not that the contact entered the journey. Field name mismatches, journey status issues, and schema validation failures all cause silent drops after the 201 is returned. Verification must happen inside Journey Builder's contact history, not from the API response alone.

## Official Sources Used

- Marketing Cloud API Overview — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/mc-apis.html
- Fire Entry Event (Journey Injection) — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/fireEntryEvent.html
- Data Extension Row Operations — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/datatransferapi.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
