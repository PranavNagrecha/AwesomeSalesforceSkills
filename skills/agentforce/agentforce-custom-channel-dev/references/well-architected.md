# Well-Architected Notes — Agentforce Custom Channel Dev

## Relevant Pillars

- **Security** — Agent API and BYOC integrations require OAuth 2.0 with specific scopes (`api` + `chatbot_api`). The `externalSessionKey` UUID acts as a session handle and must be treated as sensitive — exposure allows replay or hijacking of session idempotency. Context variables injected at session start may carry PII (authenticated user IDs, phone numbers, account identifiers) — ensure they are transmitted over TLS and not logged in plain text. BYOC CCaaS integrations handling `MessagingEndUser` records store end-user PII in Salesforce — data residency and retention policies apply.

- **Reliability** — The 409 idempotency pattern on session POST is the primary reliability mechanism for session creation under unreliable networks. The `sequenceId` monotonic ordering guarantee makes message delivery order deterministic but requires careful retry logic — sending the same sequenceId on retry rather than incrementing is essential for reliability. Session cleanup (DELETE) must be implemented in error and timeout paths, not only the happy path, to prevent resource exhaustion under failure conditions.

- **Performance** — Each Agent API message is a synchronous round-trip — the client must wait for the agent's response before sending the next message. Design the integration layer to handle response latency (agent reasoning can take 1–5 seconds) without client-side timeouts that are too aggressive. For BYOC CCaaS, the Interaction API push model (webhook-based outbound) decouples response delivery from the inbound message call, enabling more efficient connection handling on the CCaaS side.

- **Scalability** — The org's concurrent session limit is a hard ceiling. At scale, failing to DELETE sessions creates backpressure that limits new conversation capacity. Session pool management (TTL-based cleanup, background DELETE jobs) is essential for integrations handling hundreds or thousands of simultaneous conversations. The `externalSessionKey` idempotency mechanism prevents duplicate session creation under horizontal scaling (multiple integration nodes retrying the same session).

- **Operational Excellence** — Log every `externalSessionKey`, `sessionId`, and `sequenceId` to a durable audit store. This enables: debugging message ordering issues, identifying orphaned sessions, correlating Salesforce session records with external system events, and diagnosing BYOC routing failures. Alert on 409 response rates (unexpected retries), 400 responses (sequenceId/UUID format issues), and session pool utilization thresholds.

## Architectural Tradeoffs

**Raw Agent API vs. BYOC for CCaaS**

The raw Agent API is simpler to implement (3 endpoints, direct REST) but sacrifices Omni-Channel integration. BYOC for CCaaS adds routing, supervisor visibility, and CRM record creation but requires more complex event-driven architecture (webhook receivers, event dispatch). Choose based on whether Omni-Channel routing and human escalation are requirements — they cannot be retrofitted later without a full re-architecture.

**Synchronous vs. Asynchronous Response Handling**

The raw Agent API returns agent responses synchronously in the POST /messages response body. This is simple but means the integration must hold the HTTP connection open during agent reasoning. For long-reasoning scenarios (complex queries, multi-action sequences), this may exceed platform or client timeouts. BYOC CCaaS's push-based Interaction API avoids this by decoupling request and response, at the cost of a more complex webhook infrastructure.

**Session State in Integration Layer vs. Salesforce**

The raw Agent API does not persist conversation history in Salesforce — all state management is the integration layer's responsibility. BYOC CCaaS creates Salesforce records (`MessagingEndUser`, `MessagingSession`) that serve as the system of record for conversation history. Choose BYOC CCaaS when conversation history, audit trail, or CRM linkage is a requirement.

## Anti-Patterns

1. **Using Apex REST as a Custom Agent API Proxy** — Creating an Apex `@RestResource` class that attempts to "wrap" or "proxy" Agentforce sessions is not supported. Apex cannot invoke the Agentforce reasoning engine, bypass the Einstein Trust Layer, or create/manage Agent API sessions. The Agent API must be called directly from the integration layer using OAuth credentials. Any Apex involvement should be limited to agent action implementations (custom actions invoked by the agent during a session), not session management.

2. **Sharing a Single Session Across Multiple End Users** — Some integrations attempt to reuse a single Agent API session across multiple users to reduce API call overhead (e.g., a server-side session pool). This is architecturally unsound: context variables are user-specific, the session carries conversation history that spans multiple users, and session termination by one user breaks all others. Each logical conversation (one end user, one session lifetime) must have its own `externalSessionKey` and `sessionId`.

3. **Missing the chatbot_api OAuth Scope** — The `api` OAuth scope alone is insufficient for Agent API calls. The `chatbot_api` scope is required and must be explicitly added to the Connected App configuration. This is the most common initial auth failure during integration setup. Alert on 401/403 responses and check scopes before debugging other configuration.

## Official Sources Used

- Agentforce Agent API Session Lifecycle — https://developer.salesforce.com/docs/einstein/genai/guide/agent-api-session-lifecycle.html
- Bring Your Own Channel for CCaaS Agentforce Service Agent — https://developer.salesforce.com/docs/einstein/genai/guide/byoc-ccaas-agentforce.html
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
