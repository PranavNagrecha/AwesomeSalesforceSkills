# Well-Architected Notes — Territory API and Assignment

## Relevant Pillars

- **Performance** — Territory assignment operations frequently involve bulk volumes (thousands of users or accounts). Synchronous DML against `UserTerritory2Association` and `ObjectTerritory2Association` must be done in bulk (list-based DML, not record-by-record in a loop) and chunked appropriately. SOAP callouts for rule evaluation add per-call network latency and must be chunked to ≤200 IDs to avoid faults; a naive loop adds up quickly in high-volume migrations and approaches the 100 callout per transaction limit.
- **Reliability** — `DUPLICATE_VALUE` errors on association inserts are the primary cause of silent partial failures. Using `Database.insert(list, false)` with `SaveResult` inspection ensures the transaction does not roll back on a race condition or pre-existing record. Async patterns (batch jobs that publish Platform Events to trigger synchronous rule evaluation) must handle eventual consistency: there is a window between batch completion and rule evaluation where associations may be stale.
- **Security** — `UserTerritory2Association` and `ObjectTerritory2Association` DML is subject to object-level security. Code running in a context with reduced permissions may receive `INSUFFICIENT_ACCESS_OR_READONLY` errors. Ensure the running user or connected app has "Manage Territories" permission or is a System Administrator. SOAP callout authentication uses the session ID directly; this ID must be treated as a credential and never logged or stored.
- **Operational Excellence** — Territory assignment logic that runs invisibly (no logging, no audit trail) is hard to debug when rules stop working after a model change or sandbox refresh. All assignment scripts should emit structured logs that record which accounts/users were assigned, which territories, and whether rule evaluation was triggered. The `check_territory_api_and_assignment.py` script provides a static analysis safety net for pre-deployment review.

## Architectural Tradeoffs

**DML-only pin vs. rule-based assignment:**
Manual `ObjectTerritory2Association` inserts (`AssociationCause = 'Territory'`) give explicit, predictable control over which accounts are in which territories. However, they do not respond to Account field changes — if an account's `BillingState` changes, the pin does not move. Rule-based assignment is dynamic but requires explicit rule evaluation triggers. Most production orgs use a hybrid: rule-based for the bulk of accounts, manual pins for strategic or exception accounts.

**Synchronous callout vs. deferred rule evaluation:**
Triggering rule evaluation synchronously provides immediate consistency but consumes callout limits and fails in async contexts. Deferring evaluation via Platform Events provides resilience but introduces a consistency window during which territory data may be stale. For integrations that query territory assignments immediately after writes, synchronous evaluation is preferred if the volume permits.

**Batch DML vs. synchronous trigger DML:**
`UserTerritory2Association` and `ObjectTerritory2Association` DML in triggers is feasible for low-volume record changes (e.g., a single Account update triggers a re-pin). For bulk imports or realignments affecting thousands of records, trigger-initiated DML will hit the 10,000-row DML limit. Design for batch processing from the start for any scenario where bulk territory changes are anticipated.

## Anti-Patterns

1. **Triggering rule evaluation from async Apex** — Using Batch Apex or a Queueable to both write associations and call the SOAP rule evaluation endpoint fails because `UserInfo.getSessionId()` returns `null`. The SOAP callout must be architecturally separated from the async DML step, typically via a Platform Event bridge to a synchronous subscriber.

2. **Relying on ObjectTerritory2Association triggers for downstream processing** — Triggers declared on `ObjectTerritory2Association` never fire. Any downstream logic (sending notifications, updating related records, publishing events) that is placed in such a trigger is silently dropped. Platform Events dispatched from the service layer that performs the DML are the correct architectural pattern.

3. **Single-record DML in loops for territory assignments** — Inserting `UserTerritory2Association` or `ObjectTerritory2Association` one record at a time inside a `for` loop exhausts DML statement limits (150 per transaction) and produces DML-in-loop anti-patterns. All territory association DML must be accumulated in lists and executed as a single bulk operation.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Object Reference: UserTerritory2Association — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_userterritory2association.htm
- Object Reference: ObjectTerritory2Association — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_objectterritory2association.htm
- Salesforce ETM Implementation Guide — https://developer.salesforce.com/docs/atlas.en-us.salesforce_territories_implementation_guide.meta/salesforce_territories_implementation_guide/
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
