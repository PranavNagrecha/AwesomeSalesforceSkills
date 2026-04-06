# Well-Architected Notes — API Error Handling Design

## Relevant Pillars

- **Reliability** — Error classification drives retry vs dead-letter routing. A poorly designed error contract that retries permanent failures (4xx) exhausts async Apex quota and creates infinite loops; one that dead-letters transient failures (5xx, 429) silently drops recoverable data. The classification table in this skill is the primary reliability control for integration resilience.

- **Operational Excellence** — Structured error envelopes (RFC 7807 or consistent JSON) make integration failures observable. When errors carry `errorCode` and `instance` fields, support teams can trace a failed request through logs without parsing free-form text. Sanitizing 500 responses (no stack traces in external responses) is an operational discipline, not just a security concern.

- **Security** — Returning Apex stack traces, class names, or internal field names in error responses leaks implementation details that attackers can use to probe the system. Custom Apex REST endpoints that expose `e.getStackTraceString()` in the response body violate the Salesforce Well-Architected security principle of minimizing information disclosure.

- **Performance** — Explicit timeout configuration on every `HttpRequest` directly affects transaction completion time and governor limit consumption. An unset timeout that defaults to a long platform value holds up synchronous transactions unnecessarily. Correct timeout values prevent callouts from consuming excessive CPU time against slow external endpoints.

- **Scalability** — The retry-safe vs non-retry-safe classification determines whether a failure mode scales safely. If a misconfigured integration dead-letters a 401 response and retries it instead, the retry volume grows linearly with the processing volume, eventually exhausting the daily async Apex limit. Correct classification prevents error handling itself from becoming a scalability bottleneck.

## Architectural Tradeoffs

**RFC 7807 vs Salesforce-native error format:** RFC 7807 provides a stable, standards-based contract that third-party callers can parse without Salesforce-specific knowledge. Salesforce's native format (array of `{message, errorCode, fields}`) is more compact and consistent with native API behavior, reducing the parser complexity for callers that already integrate with Salesforce APIs. Choosing RFC 7807 introduces a small translation layer for Salesforce DML errors (`DmlException.getDmlMessage()` maps to `detail`; field names map to a custom extension). The tradeoff is standards adherence vs in-ecosystem consistency.

**Strict status code semantics vs defensive dead-lettering:** Mapping every exception type to the correct HTTP status code (400 vs 422 vs 500) requires maintaining the exception-to-status mapping as application logic grows. A conservative approach of returning 400 for all client errors and 500 for all server errors is simpler to maintain but obscures the failure reason from callers. Strict semantics are preferable when callers are integration-aware systems; conservative codes are acceptable when the caller is a simple alerting system that only checks success vs failure.

**Inline error classification vs separate classifier class:** Placing `if (status == 429) enqueueRetry()` logic inline in each Queueable is fast to write but scatters the classification policy across multiple classes. Centralizing in a `CalloutErrorClassifier` class makes the policy explicit, testable in isolation, and changeable without touching every consumer. The tradeoff is an additional class dependency for marginal runtime overhead.

## Anti-Patterns

1. **Collapsing all non-2xx responses to a generic retry** — Retrying 400 Bad Request or 403 Forbidden responses consumes async Apex executions for requests that will always fail. The correct design routes permanent errors directly to dead letter and retries only transient errors (429, 5xx, timeout). Refer to the decision guidance table in SKILL.md.

2. **Exposing internal exception details in 500 responses** — Returning `e.getMessage()` or `e.getStackTraceString()` in the response body of a `@RestResource` method exposes Apex class names, field names, and SOQL structure to external callers. The correct design logs the full exception server-side and returns a sanitized message with a support-traceable reference ID.

3. **Using message-string matching to classify Salesforce error responses** — The `message` field in Salesforce REST API errors is human-readable, potentially localized, and subject to change across releases. The `errorCode` field is the stable programmatic identifier. Classification logic built on `message.contains('Required fields are missing')` will break silently when Salesforce changes error text; classification built on `errorCode == 'REQUIRED_FIELD_MISSING'` is release-stable.

## Official Sources Used

- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Apex REST Services Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_rest.htm
- Salesforce REST API Error Codes — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/errorcodes.htm
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- RFC 7807 Problem Details for HTTP APIs — https://www.rfc-editor.org/rfc/rfc7807
- HttpRequest Class (Apex Reference) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_httprequest.htm
