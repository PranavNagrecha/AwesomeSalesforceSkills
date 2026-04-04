# Well-Architected Notes — Continuation Callouts

## Relevant Pillars

- **Reliability** — Continuation is the primary mechanism for ensuring that long-running external callouts do not cause Visualforce or LWC page timeouts. Without it, slow external services produce `System.CalloutException: Read timed out` and users see failures. Properly implemented Continuation with explicit timeout values and error handling in the callback produces a reliable integration that tolerates slow external services gracefully. Retry logic can be added in the callback by returning a new `Continuation` object.

- **Scalability** — Continuation offloads the HTTP request execution to Salesforce infrastructure rather than holding a Salesforce application server thread open for the duration of the callout. This means long-running integrations do not consume Salesforce thread pool capacity proportionally to their latency. Parallel callouts (up to 3 per Continuation) further reduce wall-clock latency without proportionally increasing resource consumption. This matters at scale when many users trigger concurrent callouts.

- **Security** — Continuation callouts must use endpoints registered in Remote Site Settings or (preferably) Named Credentials. Named Credentials externalize authentication credentials from Apex code, preventing hard-coded secrets and enabling credential rotation without code changes. The `callout:NamedCredentialName` endpoint syntax also enforces that the call goes through Salesforce's credential management layer. Sensitive data passed through `con.state` should be minimized; state is stored platform-side between phases but should not contain full authentication tokens or PII unnecessarily.

- **Performance** — Parallel callouts within a single `Continuation` replace sequential waits with concurrent execution. This is particularly impactful for dashboard-style pages that aggregate data from multiple services. Measured against sequential async polling patterns, parallel Continuation typically reduces perceived page load time to the latency of the slowest single service rather than the sum of all services.

- **Operational Excellence** — The two-phase pattern (explicit start/callback) makes the callout lifecycle observable. Phase 1 logs can capture what was requested and with what parameters. Phase 2 logs capture response status codes and processing outcomes. This separation makes debugging easier than opaque `@future` fire-and-forget patterns. Test coverage is also explicit: `Test.setContinuationResponse()` and `Test.invokeContinuationMethod()` provide deterministic unit testing of both phases independently.

---

## Architectural Tradeoffs

**Continuation vs. Queueable with callout:** Continuation is synchronous from the user's perspective — the page updates after the callout completes without requiring a page refresh or polling. Queueable with `AllowsCallouts` is fully asynchronous and requires polling or Platform Events to surface results to the UI. Continuation wins for UI-driven, latency-sensitive integrations. Queueable wins for background processing, bulk callouts, or non-UI-triggered integrations.

**Single Continuation vs. chained Continuations:** A single Continuation handles up to 3 parallel callouts per phase. Chaining (returning a new `Continuation` from the callback) supports up to 3 more per chain link, but each additional phase adds network round-trip latency and complexity. Prefer a single Continuation with 1–3 requests unless the data model genuinely requires sequential callout rounds (e.g., the second callout depends on data returned by the first).

**Named Credential vs. hardcoded endpoint:** Named Credentials are strongly preferred. They store authentication credentials outside Apex, support certificate-based auth, and are deployable via metadata. Hardcoded endpoints with secrets embedded in Apex are an anti-pattern under both the Salesforce Well-Architected Security pillar and standard secure development practices.

**Timeout value selection:** Setting the timeout too low wastes the Continuation mechanism (service times out before responding). Setting it to the maximum (120 seconds) when the service normally responds in 5 seconds introduces unnecessary user-perceived latency in failure modes. Set the timeout to 1.5–2x the service's documented P99 response time, with a ceiling of 120 seconds.

---

## Anti-Patterns

1. **Blocking the Salesforce request thread with a slow synchronous callout** — Calling `new Http().send(req)` in a Visualforce action method or standard `@AuraEnabled` method for services that take more than 5–10 seconds causes timeout failures and degrades Salesforce thread pool availability. Use `Continuation` for any callout that may exceed 10 seconds in user-initiated UI contexts.

2. **Using `@future` or Queueable as a workaround for UI-initiated slow callouts** — Moving the callout into an async job avoids the timeout but introduces polling complexity, DML overhead for storing results, and a degraded user experience (page refresh required). The Continuation pattern was purpose-built for this scenario and should be the default choice.

3. **Hard-coding credentials or endpoint URLs in Apex** — Embedding API keys, OAuth tokens, or full endpoint URLs directly in Apex controller code creates a security anti-pattern (secrets in version control) and an operational burden (code changes required for credential rotation). Use Named Credentials and Remote Site Settings for all Continuation callout endpoints.

4. **Passing non-serializable objects through `con.state`** — Assigning SObjects with sub-queries, Type references, or Blob fields to `con.state` causes `SerializationException` failures in the callback phase. This produces silent failures (callback never fires) that are difficult to diagnose without explicit test coverage of both phases.

---

## Official Sources Used

- Apex Developer Guide: Continuation Class Overview — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_continuation_overview.htm
- Apex Developer Guide: Continuation Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_continuation_limits.htm
- Apex Developer Guide: Apex Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Apex Reference Guide: Continuation Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_Continuation.htm
- LWC Developer Guide: Make Long-Running Callouts with Continuations — https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.apex_continuations
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
