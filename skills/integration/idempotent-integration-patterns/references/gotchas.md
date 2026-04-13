# Gotchas — Idempotent Integration Patterns

## Gotcha 1: Idempotency Key Generated on Each Retry Defeats Idempotency

**What happens:** The integration generates a new UUID or timestamp-based key on each retry attempt. The idempotency check finds no match for the new key and treats each retry as a new unique operation. Duplicate records are created on every successful retry. The integration team believes idempotency is implemented but the implementation is fundamentally broken.

**When it occurs:** When developers apply idempotency patterns without understanding the "compute once before first attempt" requirement. Common when adapting general-purpose HTTP retry libraries that generate request IDs per-request rather than per-logical-operation.

**How to avoid:** The idempotency key must be generated before the first attempt and persisted until all retries are exhausted or the operation succeeds. Store the key alongside the operation's payload in a message queue or retry queue. Use the stored key for all retry attempts. A key should represent a logical operation — not a single HTTP request.

---

## Gotcha 2: Platform Event Default Publish Immediately Delivers for Rolled-Back Transactions

**What happens:** A business process event is published from an Apex trigger using the default Publish Immediately setting. A validation rule or subsequent trigger causes the transaction to fail after the publish call. The event has already been delivered to subscribers (CometD clients and Apex trigger subscribers). Subscribers process business logic (send emails, create records, call external systems) for a Salesforce record that was never committed.

**When it occurs:** Any Apex code that publishes Platform Events correlated with DML using the default Publish Immediately setting, where transaction failure after the publish call is possible. This is surprisingly common in triggers that have complex validation logic after the platform event publish.

**How to avoid:** Use Publish After Commit for all Platform Events correlated with committed DML. Review every `EventBus.publish()` call in the org's Apex codebase and evaluate whether Publish Immediately is acceptable (it isn't, for most business process events). For Platform Events published from Flow, check the event's `PublishBehavior` setting in the Flow element.

---

## Gotcha 3: External ID Upsert Errors on 2+ Matching Records Instead of Updating One

**What happens:** An External ID upsert operation returns an error: `EXTERNAL_ID_NON_UNIQUE: More than one record found for the External ID field value`. The integration team is confused — if duplicates exist, shouldn't the upsert update one of them?

**When it occurs:** When an External ID field is not marked as Unique. Without the UNIQUE constraint, multiple records can share the same External ID value. When the upsert finds 2+ matching records, it errors rather than picking one to update — this is intentional Salesforce platform behavior to prevent ambiguous updates.

**How to avoid:** Always mark External ID fields as Unique when creating them. This enforces uniqueness at the database level — only one record can exist with a given External ID value. If an existing External ID field already has duplicates, resolve them before enabling the Unique flag. For orgs with existing duplicate External ID data, run a SOQL query to find duplicates before enabling the Unique constraint.
