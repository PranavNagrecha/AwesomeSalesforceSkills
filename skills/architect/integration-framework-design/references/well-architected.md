# Well-Architected Alignment — Integration Framework Design

## Relevant Pillars

### Reliability

A centralized `HttpCalloutDispatcher` enforces consistent retry behavior, timeout configuration, and error propagation across all integrations. Without a dispatcher, each team sets (or omits) timeouts independently, leading to unbounded wait times that exhaust Apex CPU limits and block transactions.

The typed `IntegrationException` with an `ErrorCode` enum allows calling contexts to distinguish transient failures (retry-eligible) from permanent failures (dead-letter) without string parsing. The dead-letter queue pattern ensures that transient external outages do not silently drop integration requests.

Reference: [Integration Patterns — architect.salesforce.com](https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html)

### Scalability

The `Integration_Service__mdt` service registry allows the integration catalog to grow without modifying orchestration code. Adding a new API is additive: create one CMDT record and one concrete class. The factory and dispatcher are unchanged.

Custom Metadata records are queryable in test context without DML, enabling unit tests to run without governor limit concerns. The framework's layered design (interface → factory → dispatcher → logger) keeps each concern independently scalable — logging can be switched to Platform Events for volume without touching service or factory layers.

Reference: [Salesforce Well-Architected Overview](https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html)

### Operational Excellence

`IntegrationLog__c` with a `Correlation_ID__c` field creates a queryable audit trail per transaction. Support teams can trace a specific business transaction across multiple service calls using a single correlation ID that flows through every log record.

The `Active__c` flag on `Integration_Service__mdt` allows disabling a service without a deployment — critical for incident response. Logging failures through Platform Events (for high-volume scenarios) keeps logging observable without blocking the integration transaction itself.

Reference: [Apex Developer Guide — Apex Callouts](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm)

### Adaptable (Well-Architected Dimension)

Custom Metadata drives configuration, not code. Endpoint URLs, timeout values, active flags, and class names live in CMDT records that are deployable metadata. Swapping a sandbox endpoint for a production endpoint requires a CMDT record update, not a code change and deployment cycle.

The service interface pattern means a concrete adapter can be replaced with a mock, a stub, or an entirely new API provider by creating a new class and updating a CMDT record. The calling context is insulated from that change.

### Trustworthy (Well-Architected Dimension)

Authentication is centralized in the dispatcher, which injects auth headers from Named Credentials. Concrete service classes never handle credentials directly. This single-point-of-auth enforcement makes security review tractable: review one class, not every integration implementation.

Request and response bodies are truncated before logging to `IntegrationLog__c`, preventing PII from persisting indefinitely in a custom object without field-level security controls.

Reference: [Apex Developer Guide — Named Credentials](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm)

---

## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing for reliability, scalability, operational excellence, and adaptable dimensions
- Integration Patterns (architect.salesforce.com) — synchronous vs asynchronous pattern selection, system-boundary design, integration pattern taxonomy
- Apex Developer Guide — Apex callout behavior, governor limits, transaction semantics, Named Credentials usage
- Apex Reference Guide — `Type.forName()` behavior, `Http` / `HttpRequest` / `HttpResponse` class signatures
