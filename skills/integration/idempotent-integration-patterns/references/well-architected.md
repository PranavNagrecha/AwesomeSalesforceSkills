# Well-Architected Notes — Idempotent Integration Patterns

## Relevant Pillars

- **Reliability** — Idempotency is the foundational property that makes integrations resilient to network failures, transient errors, and at-least-once delivery guarantees. Without it, retry logic introduces data corruption rather than recovery. External ID upsert, ReplayId checkpointing, and persisted idempotency keys are all Reliability mechanisms. This is the primary pillar for this skill.
- **Security** — Idempotency keys transmitted over HTTP must be treated as sensitive tokens: they should be generated with sufficient entropy (UUID v4 or a cryptographic hash), scoped to a single operation and a short TTL, and not logged in plaintext. External ID field values that carry business identifiers (order IDs, payment references) may also require access controls so that upsert endpoints cannot be exploited to overwrite records by guessing External ID values.
- **Operational Excellence** — Idempotent integrations are easier to operate because failures can be retried by the platform or by operations teams without coordination overhead or rollback procedures. ReplayId checkpoints enable self-healing subscriber resumption. Persisted idempotency keys provide an audit trail of which callout was attempted, when, and with what key.
- **Scalability** — Bulk API v2 upsert with External ID fields scales inbound idempotent sync to millions of records asynchronously. Designing for idempotency from the start avoids the scalability bottleneck of query-then-insert patterns that require row-level locking or deduplication queries under load.
- **Performance** — External ID upsert reduces round-trips compared to query-then-branch patterns. However, unique External ID constraints add index overhead on the object. For high-write objects, measure insert/upsert throughput with the unique index in place and apply record locking strategies if contention is observed.

## Architectural Tradeoffs

**At-least-once vs exactly-once delivery:** Salesforce Platform Events guarantee at-least-once delivery, not exactly-once. Building exactly-once processing on top of at-least-once delivery requires idempotent subscriber logic (the External ID upsert guard) combined with a durable checkpoint (the ReplayId store). Accept that exactly-once delivery is not a platform guarantee and design subscriber processing to be safe under re-delivery. This is cheaper and more reliable than building distributed transaction coordination on top of the event bus.

**Idempotency key storage: record field vs external store:** Storing the idempotency key on the Salesforce record (a custom field) keeps the key co-located with the work item and avoids an additional dependency. The tradeoff is that the field is visible to anyone with read access to the record and is limited by field-level security. An external key-value store (Redis, a custom Platform Cache partition) provides isolation but adds latency and a failure domain. For most Salesforce outbound callout patterns, storing the key on the record is the right default.

**Publish After Commit and subscriber latency:** "Publish After Commit" adds a small latency compared to "Publish Immediately" because the event is only enqueued after the transaction closes. For near-real-time use cases this latency is typically imperceptible (sub-second). The tradeoff of phantom events under "Publish Immediately" is far more dangerous than the small latency cost of "Publish After Commit." Default to "Publish After Commit" unless there is a documented, tested justification for the alternative.

**External ID upsert and Bulk API case sensitivity:** The convenience of the REST upsert endpoint (case-insensitive matching) does not transfer to Bulk API v2 (case-sensitive). If the integration will need to scale to bulk volumes, normalize External ID casing at design time rather than retrofitting case normalization after a production incident.

## Anti-Patterns

1. **Query-then-insert without locking** — Querying for an existing record and then inserting if not found is a two-step, non-atomic operation. A concurrent integration thread can insert between the query and the insert, creating a duplicate. External ID upsert collapses this to a single atomic operation handled by the platform. Use upsert; never use query-then-conditional-insert.

2. **Idempotency key generated at execution time** — Generating a new UUID or hash on each callout attempt defeats idempotency even when the external system supports `X-Idempotency-Key`. The external system sees a new key on each retry and processes it as a new operation. Generate the key once at enqueue time, persist it, and read it on all subsequent attempts.

3. **Platform Events with "Publish Immediately" in transactional contexts** — Using the default "Publish Immediately" setting for events that describe the outcome of DML operations allows phantom events to propagate if the publishing transaction rolls back. Subscribers process events for records that do not exist, causing lookup failures, null reference errors, and orphaned child records. Change to "Publish After Commit" for all transactional Platform Event patterns.

4. **ReplayId checkpoint advanced before processing completes** — Writing the ReplayId checkpoint before event processing finishes converts at-least-once delivery into at-most-once delivery for the failure case. Failed events are skipped silently. Write the checkpoint only after all DML and callouts for the event batch have committed successfully.

## Official Sources Used

- REST API Developer Guide — External ID Upsert — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_upsert.htm
- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Integration Patterns — https://architect.salesforce.com/content/1-salesforce-platform/integration-patterns/
- Integration Patterns (Fundamentals) — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
