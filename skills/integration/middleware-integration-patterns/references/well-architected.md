# Well-Architected Notes — Middleware Integration Patterns

## Relevant Pillars

- **Reliability** — Middleware is justified primarily by reliability requirements: durable message queuing, guaranteed delivery, and independent error handling per integration leg. A middleware integration that lacks a dead-letter queue and compensating transaction design is not reliable even if it uses an enterprise iPaaS. Per Salesforce Architects guidance, every middleware integration must have a documented failure and recovery path.
- **Scalability** — Middleware decouples Salesforce governor limit exposure from integration volume. By publishing Platform Events and exiting the Salesforce transaction immediately, the integration does not consume callout budget proportional to downstream system count. Middleware can scale horizontally (additional Mule workers, Boomi Atom Cloud nodes) without impacting the Salesforce org.
- **Security** — Middleware introduces additional attack surface: the middleware platform itself, the credentials it stores, and the network paths between systems. All middleware-to-Salesforce authentication must use OAuth 2.0 (JWT Bearer for server-to-server, never username/password). Connected Apps must be scoped to minimum required permissions. Credentials must be stored in the middleware platform's secrets management facility, not in flow configurations.
- **Operational Excellence** — Middleware integrations must be observable. Correlation IDs must propagate end-to-end so that a failed message can be traced from the Salesforce event through each middleware hop to the target system. Alerting must fire on dead-letter queue accumulation, not only on explicit errors. Runbooks must exist for manual message reprocessing.

## Architectural Tradeoffs

**Middleware vs. native Salesforce capabilities:** Native Salesforce integration capabilities (Platform Events, Pub/Sub API, Flow HTTP Callout, External Services) have no licensing cost beyond the Salesforce edition, require no additional infrastructure, and are well-understood by Salesforce developers. Middleware adds operational cost, vendor dependency, and a second platform to maintain. The tradeoff is justified only when the native platform demonstrably cannot meet a specific requirement: protocol conversion, cross-system orchestration, durable queuing, or complex transformation.

**MuleSoft vs. lower-cost iPaaS:** MuleSoft provides the deepest Salesforce connector coverage, the most expressive transformation language (DataWeave), and the only native integration with Agentforce via Agent Fabric. The premium pricing is justified for enterprise organizations with multiple integration teams, API governance requirements, and Agentforce deployments. For single-team integrations between Salesforce and 2–3 SaaS applications, Workato or Boomi deliver equivalent outcomes at lower total cost.

**Eventual consistency vs. distributed atomicity:** Distributed transactions across Salesforce and external systems are architecturally expensive and practically unavailable in most iPaaS platforms. Per Salesforce Architects guidance, integrations should be designed for eventual consistency with compensating transactions rather than attempting distributed ACID semantics. Accepting eventual consistency simplifies the integration design and removes the need for two-phase commit infrastructure.

**Synchronous vs. asynchronous delivery:** Synchronous middleware integrations (Salesforce waits for middleware to confirm downstream system write before returning to user) keep the Salesforce transaction open for the full round trip. For orchestrations touching multiple backends, this is impractical. Asynchronous delivery via Platform Events decouples the Salesforce transaction from downstream processing, improving user experience and resilience but requiring the consuming application to handle eventual-consistency states in the UI.

## Anti-Patterns

1. **Using middleware as a workaround for missing Apex skill** — Introducing MuleSoft or Boomi to handle HTTP callouts that a competent Apex callout and Named Credential pattern could handle natively. This is a common pattern in organizations where integration consultants are more available than Apex developers. The result is unnecessary operational complexity and licensing cost for scenarios the native platform handles well.

2. **Neglecting dead-letter queue and alerting design** — Implementing the happy path of a middleware integration without designing the failure path. Messages that fail all retries accumulate silently in a dead-letter queue or are discarded. Business processes (order fulfillment, invoice sync) stall without any operational signal. Every middleware integration must treat the dead-letter queue as a first-class artifact, not an afterthought.

3. **Selecting middleware vendor based on brand familiarity rather than scenario requirements** — Choosing MuleSoft by default because it is a Salesforce company product, without evaluating whether the integration scenario requires API-led governance, complex transformation, or enterprise Salesforce connector features. For simple Salesforce + SaaS automation, a low-code iPaaS delivers faster value with lower cost and no meaningful architectural disadvantage.

## Related Skills (Cross-References)

- **integration/mulesoft-salesforce-connector** — Deep-dive on Anypoint Salesforce Connector: API selection (SOAP/REST/Bulk/Streaming), JWT Bearer auth, watermark, batch processing. Use when MuleSoft is selected as the middleware platform.
- **integration/api-led-connectivity** — Multi-layer API architecture (System/Process/Experience APIs). Use when MuleSoft is selected and the integration architecture requires governed, reusable API layers across multiple consumers.
- **integration/integration-pattern-selection** — Synchronous vs asynchronous vs event-driven pattern selection before middleware vendor selection.
- **integration/error-handling-in-integrations** — Retry strategies, dead-letter queue design, and compensating transaction patterns applicable across all middleware vendors.

## Official Sources Used

- Integration Patterns (Salesforce Architects) — Primary authority for when middleware is required vs native Salesforce capabilities, pattern selection (request-reply, fire-and-forget, batch, event-driven), and architectural tradeoffs
  URL: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html

- MuleSoft Anypoint Connector for Salesforce documentation — Connector API selection (SOAP/REST/Bulk/Streaming), authentication, and real-time event subscription capabilities
  URL: https://developer.salesforce.com/docs/atlas.en-us.mulesoft.meta/mulesoft/mulesoft_connector_sf.htm

- Salesforce Well-Architected Overview — Well-Architected pillars (Reliability, Scalability, Security, Operational Excellence) applied to integration architecture
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

- Pub/Sub API Developer Guide — Salesforce Pub/Sub API (gRPC), replay ID management, event retention window (72 hours), and external subscriber requirements
  URL: https://developer.salesforce.com/docs/platform/pub-sub-api/guide/pub-sub-api-intro.html
