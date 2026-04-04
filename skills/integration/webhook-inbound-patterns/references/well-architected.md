# Well-Architected Notes — Webhook Inbound Patterns

## Relevant Pillars

- **Security** — Inbound webhooks are unauthenticated entry points into Salesforce. HMAC signature verification is the security boundary. Without it, any party who discovers the endpoint URL can inject arbitrary payloads. Salesforce Sites endpoints are publicly accessible — this makes signature verification non-optional for unauthenticated webhooks.
- **Reliability** — The async ACK pattern (respond 200 immediately, process in Queueable) is a reliability pattern. It decouples the receiver's acknowledgment from processing, allowing the system to handle sender retries gracefully while ensuring the event is eventually processed.
- **Operational Excellence** — Idempotent processing via External ID upsert means the system handles retries and duplicate deliveries without manual intervention. Logging processed event IDs enables audit and replayability.

## Architectural Tradeoffs

**Synchronous vs. Async processing:** Synchronous is simpler but risks timeout failures under load. Async adds Queueable depth consumption and requires a state management pattern for retry visibility. For anything non-trivial, async is the safe default.

**Salesforce Sites vs. Connected App:** Salesforce Sites is simpler to configure but requires HMAC as the sole authentication layer. Connected App with OAuth Client Credentials adds authentication overhead for the sender but provides session-level identity. Use Sites for SaaS integrations; use Connected App for internal or partner systems.

## Anti-Patterns

1. **Processing webhook payload synchronously without timeout protection** — Synchronous processing risks exceeding sender timeout, causing retries, causing more load, causing more timeouts. Always enqueue async for non-trivial processing.
2. **Storing shared secrets in Apex code** — Hardcoded secrets cannot be rotated without a deployment. Store shared secrets in Custom Metadata or Custom Settings, accessible via SOQL.
3. **Not implementing idempotency** — Webhook senders retry on any non-2xx response or network error. Without idempotency, retries create duplicate records.

## Official Sources Used

- Apex Developer Guide — Apex REST Methods — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_rest_methods.htm
- Apex Developer Guide — Apex REST — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_rest.htm
- Salesforce Help — Remote Access — OAuth Endpoints — https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_endpoints.htm
- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest.htm
- Integration Patterns — https://architect.salesforce.com/docs/architecture/integration-patterns
