# Well-Architected Notes — Retry and Backoff Patterns

## Relevant Pillars

- **Reliability** — Retry and backoff patterns are a direct implementation of the Salesforce Well-Architected Reliability pillar. Transient failures in external systems should not cause permanent data loss. The skill ensures integrations degrade gracefully and recover automatically within defined bounds.
- **Operational Excellence** — Dead-letter queues and circuit breaker logging make integration failures observable and actionable. Operators can identify degraded integrations, manually intervene via circuit breaker CMDT flags, and drain dead-letter queues without code changes.
- **Security** — Idempotency keys prevent duplicate data creation from retry storms, which can create exploitable duplicate records or double-charges in payment integrations. Retry logic must not log sensitive payload fields (PII, credentials) to `Failed_Integration_Log__c`.
- **Performance** — Jitter in the backoff formula prevents synchronized retry storms that amplify load on a recovering external system. Circuit breakers reduce unnecessary callout attempts that would consume governor limits without prospect of success.

## Architectural Tradeoffs

**Retry depth vs. async Apex budget:** More retries (higher `maxRetries`) increases resilience to long-duration outages but also increases async Apex consumption. For high-volume integrations, a lower `maxRetries` (3) with a longer base delay is preferable to a higher count (8) with a short delay. The circuit breaker is the primary mechanism for handling extended outages.

**Exact delay vs. approximate delay:** Queueable scheduling does not enforce specific timing. If integration SLAs require precise retry intervals, Outbound Messages (native platform retry) or an external orchestration system may be more appropriate than Apex Queueable chaining. Apex retry is best suited for "eventually consistent" integration patterns.

**Idempotency key scope:** Generating a key per-record (based on the Salesforce record Id) is simpler but means the same record can only have one in-flight idempotency key at a time. For bulk integrations, keys should be scoped to the request payload (record Id + operation type + timestamp window) to handle concurrent operations on the same record.

**CMDT for circuit breaker vs. custom object:** CMDT reads are cached and do not consume SOQL per transaction. However, CMDT records cannot be updated via Apex DML — they require a metadata deployment or a Setup UI change. This makes CMDT appropriate for operator-controlled circuit breaking but unsuitable for automatic state transitions. Automatic circuit state management (e.g., counting consecutive failures) requires a custom object or platform cache.

## Anti-Patterns

1. **Unbounded retry loop** — Retry logic with no `maxRetries` cap or with a cap of 50+ will exhaust the daily async Apex limit during extended outages. This blocks all background processing org-wide. Every retry implementation must have an explicit maximum and a dead-letter path when that maximum is reached.

2. **Retrying non-retriable errors** — HTTP 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), and 404 (Not Found) are not transient errors. Retrying them will never succeed and wastes async limit. Only retry on 429, 503, 5xx (excluding 501), and `System.CalloutException` (timeout). Log 4xx errors directly to the dead-letter queue without retry.

3. **Retry without idempotency** — Retrying a callout that creates or modifies records without an idempotency key risks duplicate records or double-charges. Idempotency is not optional when the downstream system does not provide at-least-once delivery guarantees.

## Official Sources Used

- Apex Developer Guide — Apex Callouts: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Apex Developer Guide — Queueable Apex: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
- Apex Developer Guide — Governor Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Help — Outbound Messaging Retry: https://help.salesforce.com/s/articleView?id=sf.workflow_outbound_troubleshoot.htm
- Platform Events Developer Guide — Event Replay: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_subscribe_intro.htm
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected — Reliability: https://architect.salesforce.com/well-architected/reliable/overview
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
