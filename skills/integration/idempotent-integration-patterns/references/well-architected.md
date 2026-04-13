# Well-Architected Notes — Idempotent Integration Patterns

## Relevant Pillars

- **Reliability** — Idempotent integrations tolerate network failures and retries without producing data corruption. External ID upsert and Publish After Commit are the two highest-leverage reliability improvements available to Salesforce integration architects.
- **Security** — Idempotency keys transmitted via HTTP headers should use HTTPS. Keys should not encode sensitive data — use opaque UUIDs or hashes, not plaintext business identifiers. Processing logs that accumulate over time should have a documented retention and purge policy to avoid unbounded data growth.

## Architectural Tradeoffs

**External ID upsert vs. idempotency key log:** External ID upsert is the simpler and more performant approach because it offloads deduplication to the database (UNIQUE index on the External ID field). The idempotency key log approach adds a lookup step before every insert and requires log maintenance. Use External ID upsert where a stable external identifier exists. Use idempotency key log only when External ID upsert is not available.

**Publish Immediately vs. Publish After Commit:** Publish Immediately provides lower latency (event delivered before the transaction commits) at the cost of possible orphan events from rolled-back transactions. Publish After Commit adds commit-level latency but guarantees events only represent committed state. For business process events (record created, order fulfilled), always use Publish After Commit. For internal debug or monitoring events where rollback is acceptable, Publish Immediately is acceptable.

## Anti-Patterns

1. **Generating idempotency key on each retry** — The most common and fundamental idempotency design error. Keys must be pre-generated and reused across all retries for the same logical operation.

2. **Using POST for inserts that need to be idempotent** — POST creates new records on every call. Use PATCH with an External ID for any inbound write operation that needs to be retry-safe.

3. **Unbounded idempotency log growth** — Accumulating processed keys in an `IntegrationIdempotencyLog__c` object without a purge policy. Over time, the log grows to millions of records, making lookups slower and consuming storage limits. Implement a time-based purge (delete entries older than the maximum expected retry window for the integration).

## Official Sources Used

- Salesforce Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- REST API Developer Guide: Upsert a Record Using an External ID — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_upsert.htm
- EventBus.publish() — Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_EventBus.htm
- Platform Events Developer Guide — Publish and Subscribe — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_publish_apex.htm
