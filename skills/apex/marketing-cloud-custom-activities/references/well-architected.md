# Well-Architected Notes — Marketing Cloud Custom Activities

## Relevant Pillars

- **Security** — Custom activities introduce an externally-callable execute endpoint that receives contact PII and journey context. JWT verification (using the Installed Package secret) is mandatory on every inbound request. Failure to verify allows any caller to trigger the endpoint and process arbitrary data. All endpoints must be HTTPS — Journey Builder will not load HTTP-only activity UIs. The config.json endpoint may be public, but execute/save/publish/validate endpoints must verify caller identity.

- **Reliability** — Journey Builder does not retry on execute endpoint timeout or non-200 response. A contact that hits a timeout is permanently errored for that journey activation. Reliability requires async execute patterns (accept and enqueue; return 200 immediately) and graceful fallback paths so that external API failures route contacts to a safe default branch rather than erroring them out.

- **Performance** — The execute endpoint must return HTTP 200 within the configured timeout (default 30 seconds). Synchronous execution of slow external calls violates this requirement at scale. Performance design means keeping the execute hot path to JWT validation + queue write only, with real work delegated to background workers. The Postmonger `ready` handshake sequence also affects perceived performance of the configuration UI — a poorly sequenced initialization causes blank field pickers that frustrate practitioners.

- **Operational Excellence** — Custom activities are external services from Journey Builder's perspective. Operational excellence means: structured logging on execute endpoints to correlate Journey Builder contact keys with external system operations; alerting on TLS certificate expiry for hosted endpoints; monitoring queue depth for async execute workers; and maintaining config.json as a versioned, tested artifact rather than a manually-edited file.

- **Scalability** — A single Journey Builder journey can process millions of contacts. The execute endpoint must handle concurrent POSTs at journey scale. Synchronous blocking execute handlers become bottlenecks. Async queue-based patterns (SQS, Service Bus, etc.) decouple Journey Builder throughput from downstream API throughput and scale horizontally.

## Architectural Tradeoffs

**Sync vs. Async Execute**
Synchronous execute is simpler to implement and debug — one request, one response, no queue infrastructure. It is acceptable for activities that call fast, reliable downstream APIs with sub-second p99 latency. Async execute is more complex (requires a queue, a worker, and idempotency handling) but is required when downstream latency is variable or when the journey processes large volumes concurrently. The 30-second Journey Builder timeout is a hard ceiling that makes async the safer default for any non-trivial operation.

**Custom Split vs. Decision Split**
Decision Split activities operate on data already in a Marketing Cloud Data Extension at the time the contact reaches the split. They are zero-code and suitable for most routing scenarios where contact attributes are known at entry. Custom Split activities are appropriate only when routing logic requires a real-time external API call or computation that cannot be pre-loaded into a DE. Custom splits introduce external dependencies that can become single points of failure; budget for fallback outcomes and monitoring.

**Hosted Infrastructure vs. Heroku/PaaS**
The activity web app and endpoints can be hosted anywhere with HTTPS. PaaS platforms (Heroku, Azure App Service, AWS Elastic Beanstalk) simplify TLS provisioning and scaling. Self-hosted infrastructure requires explicit TLS certificate management and capacity planning. For prototyping, Heroku free/eco dynos are convenient but introduce cold-start latency — inappropriate for production execute endpoints where latency directly affects journey throughput.

## Anti-Patterns

1. **Performing synchronous blocking work in the execute endpoint** — Any synchronous call to a slow external system (Salesforce REST API, loyalty platform, payment gateway) inside the execute handler creates a timeout risk at scale. Contacts error out permanently on timeout. Use an async queue pattern instead: validate JWT, enqueue, return 200.

2. **Skipping JWT verification on execute endpoint** — Relying on "security through obscurity" (an unpublished URL) instead of verifying the Journey Builder JWT on every inbound POST leaves the execute endpoint open to spoofed requests. Any actor who discovers the URL can trigger data processing operations. Always verify the JWT signature against the Installed Package secret before processing the request body.

3. **Hardcoding outcome keys in execute endpoint without syncing config.json** — When config.json `metaData.outcomes` keys and execute endpoint `branchResult` values are maintained separately, they drift. A rename in config.json that is not reflected in the execute endpoint causes silent contact errors. Treat outcome keys as a shared constant and enforce consistency in CI/CD.

## Official Sources Used

- Marketing Cloud Custom Activities Developer Guide — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/creating-activities.html
- Custom Activity Configuration Reference — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/custom-activity-config.html
- Define Custom Split Activity — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/define-split-activity.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
