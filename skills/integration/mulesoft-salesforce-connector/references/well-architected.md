# Well-Architected Notes — MuleSoft Salesforce Connector

## Relevant Pillars

- **Security** — Authentication method selection (JWT Bearer vs username-password) directly impacts credential exposure, rotation risk, and MFA compatibility. Connected App scope configuration controls the blast radius of a compromised integration. Certificate-based auth is the Well-Architected default for server-to-server integrations.
- **Reliability** — Watermark-based incremental sync with Object Store provides at-least-once delivery guarantees. Batch scope error isolation ensures individual record failures do not cascade to the entire job. Streaming replay with durable replay ID storage prevents event loss across restarts.
- **Performance** — API selection (SOAP vs REST Composite vs Bulk) determines throughput and governor limit consumption. Choosing SOAP for high-volume loads exhausts the daily API limit and causes timeouts. Bulk API offloads processing to the Salesforce async infrastructure, freeing the Mule runtime for transformation work.
- **Scalability** — Bulk API 2.0 scales to millions of records per job without proportional API call increase. Object Store-backed watermark allows horizontal scaling of Mule workers because the watermark is externalized, not held in JVM memory.
- **Operational Excellence** — Centralized error handling with dead-letter queues and Anypoint Monitoring dashboards provides visibility into sync failures. Consistent use of Custom Metadata or Mule properties for configuration (endpoints, thresholds, watermark keys) enables environment promotion without code changes.

## Architectural Tradeoffs

1. **Polling vs event-driven sync.** Polling with watermark is simpler to implement and debug but introduces latency (sync interval). Streaming/Pub/Sub provides near-real-time but requires fallback reconciliation for the 72-hour retention window and adds complexity for replay management. Most production implementations use both: streaming for real-time and polling for durability.

2. **Bulk API vs REST Composite for medium volumes (1,000 - 10,000 records).** Bulk API is async and has higher startup overhead per job, making it slower for small batches. REST Composite processes up to 200 records per call synchronously, which is faster for medium volumes but counts against the standard API limit. The crossover point is typically around 5,000 records — below that, Composite is faster; above that, Bulk is more limit-efficient.

3. **Single integration user vs per-user OAuth.** JWT Bearer authenticates as one integration user, which simplifies setup but means all data access runs under that user's sharing rules. Per-user OAuth (Authorization Code flow) preserves row-level security but requires interactive consent and session management. Use JWT Bearer for system-to-system sync; use per-user OAuth when the Mule flow acts on behalf of individual Salesforce users.

## Anti-Patterns

1. **Using username-password auth in production** — Credentials are embedded in properties files, break on password rotation, and fail when MFA is enforced on API users. Use JWT Bearer with certificate-based auth instead.
2. **Advancing watermark before confirming processing success** — If the watermark is stored immediately after querying (before processing), a mid-batch failure skips the failed records permanently. Always advance watermark only after the batch completes within acceptable error thresholds.
3. **Using SOAP API for all volumes regardless of record count** — SOAP API is convenient for small reads but exhausts the daily API limit at scale and suffers query-more cursor timeouts. Match the API to the volume using the decision table in SKILL.md.
4. **Ignoring Bulk API's separate limit pool** — Teams assume Bulk API is "unlimited" because it does not count against the standard API limit. Bulk API 2.0 has its own daily rolling limit. Monitor both pools independently.

## Official Sources Used

- MuleSoft Salesforce Connector 11.x Documentation — connector operations, API mode configuration, auth setup
  https://docs.mulesoft.com/salesforce-connector/latest/
- MuleSoft Batch Processing Documentation — batch scope, maxFailedRecords, on-complete handling
  https://docs.mulesoft.com/mule-runtime/latest/batch-processing-concept
- MuleSoft Object Store Connector — watermark replacement pattern for Mule 4
  https://docs.mulesoft.com/object-store-connector/latest/
- Salesforce Integration Patterns — pattern selection, sync vs async tradeoffs
  https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — architecture quality model, trusted/easy/adaptable framing
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Bulk API 2.0 Developer Guide — job lifecycle, limits, query result retrieval
  https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Salesforce Connected App and OAuth Documentation — JWT Bearer flow setup, scope configuration
  https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm
