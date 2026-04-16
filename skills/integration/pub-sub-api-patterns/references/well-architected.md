# Well-Architected Notes — Pub/Sub API Patterns

## Relevant Pillars

- **Reliability** — Event bus retains events for only 3 days. Consumer downtime exceeding 3 days causes event loss. Replay ID persistence is required for reliable at-least-once delivery. Managed Subscriptions offload replay tracking to the server for stateless consumers.
- **Performance** — FetchRequest flow control enables consumer-paced event delivery, preventing consumers from being overwhelmed. Maximum 100 events per FetchRequest — design processing loops accordingly.
- **Security** — gRPC connections require valid OAuth tokens with correct org scopes. The `tenantid` header must be the 18-character Org ID — use of 15-character IDs causes authentication failures.
- **Operational Excellence** — Monitor consumer lag (how far behind the event stream the consumer is) to detect processing bottlenecks. Alert on consumer downtime approaching the 3-day retention window.

## Architectural Tradeoffs

**Subscribe vs. ManagedSubscribe:** Standard Subscribe requires client-side replay ID persistence — suitable for stateful consumers (long-running processes, databases, persistent cache). ManagedSubscribe offloads replay tracking to Salesforce but adds a 200-subscription org limit — suitable for stateless/containerized consumers. Choose based on consumer deployment architecture.

**Pub/Sub API vs. CometD/EMP Connector:** Pub/Sub API gRPC is the current recommended path for new integrations — better throughput, flow control, and language client support. CometD/EMP Connector is the legacy path, retained for backwards compatibility but not recommended for new development. Choose Pub/Sub API for all new integrations.

**Publish vs. PublishStream:** Unary Publish is simpler (request/response) but limited to sporadic publishing. PublishStream (bidirectional streaming) is for sustained high-throughput publishing without the overhead of new connections per batch. Choose based on publishing frequency and volume.

## Anti-Patterns

1. **Client-Side Replay ID Loss in Stateless Deployments** — Storing replay IDs only in memory or local files in a containerized deployment causes event reprocessing from Earliest after every restart. Use external persistent storage (Redis, RDS, DynamoDB) or switch to ManagedSubscribe.

2. **Treating FetchRequest Cap as API Rate Limit** — Modeling 100 events per FetchRequest as a throughput ceiling leads to unnecessary architectural complexity (multiple consumers, load balancers). It is a per-request batch size — not a rate limit.

3. **No Consumer Lag Monitoring** — Without monitoring, a slow consumer can fall behind the event stream until it exceeds the 3-day retention window, causing silent event loss. Monitor consumer lag and alert early.

## Official Sources Used

- Pub/Sub API Developer Guide — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/intro.html
- Pub/Sub API Allocations — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/allocations.html
- Pub/Sub API Authentication — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/supported-auth.html
- Managed Event Subscriptions — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/managed-sub.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
