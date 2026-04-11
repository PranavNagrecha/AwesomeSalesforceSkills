# Well-Architected Notes — Commerce Order Management

## Relevant Pillars

- **Reliability** — OMS processes are transactional; order state must be consistent even when async payment jobs fail. The ProcessExceptionEvent pattern is the primary reliability mechanism: ensure it is always deployed before ensure-funds-async or ensure-refunds-async are enabled. FulfillmentOrder status transitions must be idempotent.
- **Security** — Payment and refund actions invoke external gateway integrations. Credentials must be stored in Named Credentials or OMS Payment Gateway configuration, never hardcoded. OrderSummary and FulfillmentOrder records contain financial PII; review OWD and sharing rules to ensure customer service agents, warehouse users, and external integration users have minimum necessary access.
- **Performance** — OMS Connect API actions are synchronous in the context of the calling transaction but spawn async jobs. Avoid calling ensure-funds-async inside a tight loop or within a transaction that already has DML on large sets of records. Use Queueable chaining to spread load. FulfillmentOrder routing logic that queries inventory across many locations should use selective SOQL with proper indexes.
- **Scalability** — High order volumes require that platform event subscriptions (OrderSummaryCreatedEvent, FOStatusChangedEvent) are designed for bulk delivery. Apex triggers on platform events process up to 2,000 events per transaction; ensure batching logic handles this ceiling. Avoid storing large state in static variables inside event-triggered Apex.
- **Operational Excellence** — All OMS state transitions should produce observable signals: platform events for status changes, ProcessExceptionEvent for errors, and ChangeOrder records for financial mutations. Build dashboards or alerts on ProcessExceptionEvent volume and OrderSummary status distribution to detect systemic fulfillment or payment failures early.

## Architectural Tradeoffs

**MANAGED vs UNMANAGED lifecycle type:**
MANAGED provides financial consistency guarantees and auditable ChangeOrders but requires all mutations to go through Connect API actions, which adds implementation complexity and API call overhead. UNMANAGED allows simpler DML-based integration but loses OMS financial aggregate automation. The tradeoff is between platform safety and integration flexibility. For any standard commerce implementation, MANAGED is the correct choice.

**Synchronous vs async payment actions:**
ensure-funds-async and ensure-refunds-async are designed to be non-blocking for the user-facing transaction. This improves checkout and return response times but requires a separate error-handling path (ProcessExceptionEvent). Teams that need synchronous payment confirmation for user-facing flows must use a different payment pattern outside of the OMS async jobs.

**Routing logic in Flow vs Apex:**
OMS routing can be implemented in Flow (lower code, admin-maintainable) or Apex (more control, easier unit testing). Flow routing is sufficient for straightforward single-location scenarios. Multi-location, inventory-aware routing with fallback logic requires Apex for testability and reliability at scale.

## Anti-Patterns

1. **Skipping ProcessExceptionEvent subscription** — Deploying ensure-funds-async or ensure-refunds-async without a ProcessExceptionEvent subscriber means payment failures are invisible at runtime. Operations teams discover problems only through customer complaints or financial reconciliation failures. Always deploy the event subscriber before enabling payment jobs.

2. **Reusing CPQ order management patterns in OMS** — CPQ workflows (quote → order → activate) do not produce OrderSummary records. Teams that carry CPQ Apex patterns into OMS and expect them to work against OrderItemSummary and FulfillmentOrder objects will face missing records, DML errors, and broken aggregates. Treat OMS as a distinct data model that requires its own patterns.

3. **One-shot fulfillment routing without status event handling** — Creating FulfillmentOrders at Order activation time but not subscribing to FOStatusChangedEvent leaves the OrderSummary status stale and prevents downstream processes (invoice generation, shipping notification) from triggering. OMS is event-driven; the routing step is the start, not the end, of the fulfillment lifecycle.

## Official Sources Used

- Salesforce Order Management Developer Guide v66.0 Spring '26 — https://developer.salesforce.com/docs/atlas.en-us.order_management_developer_guide.meta/order_management_developer_guide/
- Connect REST API Developer Guide — Order Management Actions — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_order_management.htm
- Platform Events Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Object Reference — OrderSummary — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_ordersummary.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
