# Well-Architected Notes — Change Data Capture Apex

## Relevant Pillars

- **Reliability** — CDC trigger execution is asynchronous and decoupled from the originating transaction. The trigger must be resilient to gap events, batched event delivery, and partial failures. Proper GAP event handling with re-fetch logic is the primary reliability concern. Event retention is 72 hours — any subscriber (including Apex) that fails to process events within that window loses them permanently.

- **Performance Efficiency** — CDC triggers receive up to 2,000 event messages per batch. All SOQL and DML must operate on collected Sets outside the event loop. Field-level filtering via `changedFields` prevents unnecessary SOQL queries on irrelevant updates, which is the primary performance optimization available to CDC trigger authors. Naively issuing one SOQL per event record in a 2,000-event batch guarantees a governor limit violation.

## Architectural Tradeoffs

**CDC trigger vs. standard object trigger:** A standard Apex trigger executes synchronously inside the DML transaction. A CDC trigger executes asynchronously after commit. Use CDC triggers for resource-intensive logic (integrations, complex calculations, heavy SOQL) where decoupling from the transaction is desirable. Use standard object triggers for logic that must roll back with the transaction, validate before commit, or enforce field-level business rules.

**CDC trigger vs. Platform Events from standard trigger:** Some patterns publish a Platform Event from a standard trigger to decouple processing. CDC triggers eliminate the need for that indirection when the event is simply "this record changed." Use CDC when the event semantics map directly to a DML operation; use Platform Events when the event represents a business fact that is not one-to-one with a DML operation (e.g., "Order Approved").

**Apex subscriber vs. external subscriber:** Choose an Apex CDC trigger when the downstream logic lives within Salesforce (Flow invocation, record updates, task creation, internal notifications). Choose an external subscriber (Pub/Sub API or CometD) when events must reach an external system. Do not use both an Apex CDC trigger and an external subscriber on the same object unless the use cases are genuinely independent — combined event delivery consumes allocation from both.

## Anti-Patterns

1. **Querying inside the event loop** — Issuing SOQL or DML inside the `for (Event event : Trigger.new)` loop is the most common governor limit violation in CDC triggers. The batch size of 2,000 events means a single inner SOQL blows through the 100-query limit in 100 iterations. The correct pattern is to collect all relevant IDs across the full loop, then issue a single bulk query.

2. **Ignoring GAP events** — A CDC trigger with no `GAP_` branch is not production-ready. Gap events fire in real production orgs during bulk data loads, large transactions, and internal platform incidents. Ignoring them causes silent data drift that is difficult to detect and expensive to repair. Every CDC trigger must include a GAP handler that at minimum marks affected records for re-sync.

3. **Performing synchronous callouts from CDC trigger body** — CDC triggers cannot perform synchronous HTTP callouts. Attempting to do so throws a `System.CalloutException`. Developers who test CDC triggers with mocked callouts in unit tests may not discover this restriction until production. Any integration callout must be dispatched to a `Queueable` with `Database.AllowsCallouts` or a `@future(callout=true)` method.

## Official Sources Used

- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm — primary authority for trigger syntax, header fields, execution model, GAP events, and entity selection
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm — governor limits, async execution, Queueable patterns
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm — `EventBus.ChangeEventHeader` class and `getRecordIds()` method signature
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — reliability and performance framing
