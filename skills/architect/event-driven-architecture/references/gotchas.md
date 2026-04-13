# Gotchas — Event-Driven Architecture

Non-obvious Salesforce platform behaviors and architectural traps that cause real production problems in EDA design.

## Gotcha 1: Platform Events 72-Hour Replay Window Does Not Support Event Sourcing

**What happens:** Architects design an event sourcing solution using Platform Events as the event store, assuming that the replay mechanism can reconstruct entity state from the full event history. After 72 hours (or up to 3 days with extended retention), events age out of the bus. A consumer that restarts after the window misses all events that occurred during the outage. State reconstruction fails silently — the consumer simply starts from a blank slate.

**When it occurs:** Any time a consumer is offline for longer than the replay window, or when an architecture attempts to reconstruct entity state from Platform Events history for entities older than 3 days.

**How to avoid:** Separate the transport from the store. Use Platform Events (or Pub/Sub API) for delivery only. Write every event to an external durable store — Data Cloud (streaming ingestion via Pub/Sub API), Apache Kafka (configurable unlimited retention), or a custom append-only `Event_Log__c` Salesforce object — before the replay window expires. State reconstruction queries the durable store, not the bus.

---

## Gotcha 2: Choreography Commits to Eventual Consistency — There Is No Going Back

**What happens:** A team adopts choreography because it is quick to start: publish a Platform Event, subscribe in a Flow or Apex trigger, done. Months later, a compliance audit requires proof that all steps of the workflow completed for every business transaction. Choreography has no central state — there is no built-in mechanism to answer "did all three downstream systems process Order #12345?" Teams must retrofit correlation tracking, consumer acknowledgment events, and a saga monitor — a significant architectural rework.

**When it occurs:** When the consistency model is not consciously decided upfront, and choreography is chosen because it is operationally easy rather than because eventual consistency is genuinely acceptable.

**How to avoid:** Make the consistency decision explicit before implementation. If the business requires proof of completion or the ability to roll back partially completed workflows, choose orchestration (Flow Orchestration or Apex Queueable orchestrator) rather than choreography. Document this decision in an Architecture Decision Record.

---

## Gotcha 3: Platform Events Do Not Guarantee Message Ordering

**What happens:** A consumer processes events in a different order than they were published. For example, an `Account_Updated__e` event for a status change from Active to Closed arrives before an earlier `Account_Updated__e` event for an address change. The consumer overwrites the Closed status with the address-change payload's previous status value, producing incorrect state.

**When it occurs:** Under high throughput, when the Salesforce platform routes events across multiple partitions or processes them in parallel. Also occurs when consumers restart from a checkpoint that creates a different delivery order than the original publication sequence.

**How to avoid:** Include a monotonically increasing `Sequence_Number__c` field in event payloads. Consumers should discard events with sequence numbers lower than the last processed sequence for the same entity. If strict ordering is required, use a Queuing pattern with a single-consumer model rather than a Pub/Sub fan-out. Do not assume events arrive in publication order.

---

## Gotcha 4: Idempotency Must Be Designed Into Consumers — At-Least-Once Delivery Is the Default

**What happens:** A Platform Event is delivered twice (due to a consumer restart or a network retry), and the consumer processes it twice — creating duplicate records, double-posting a journal entry, or sending two confirmation emails to a customer.

**When it occurs:** Any time a consumer processes events with at-least-once delivery semantics, which is the default for Platform Events and most message buses. Consumer restarts, resubscriptions, and replay all create duplicate delivery scenarios.

**How to avoid:** Every consumer must implement idempotency. Standard approaches: store a processed-event log keyed on the event's idempotency key (External_Event_ID__c) and skip processing if the key exists; use Salesforce UPSERT on an External ID field so duplicate events produce the same result as a single event; implement a unique index on the idempotency key in the target object.

---

## Gotcha 5: EDA Architectural Decision Must Precede Mechanism Selection

**What happens:** A team skips the architectural style decision and jumps directly to mechanism selection ("we'll use Platform Events for this"). They build a Platform Events-based solution, then discover that the use case requires event sourcing with durable replay, or that all consumers must process events in strict order, or that the fan-out pattern requires a competing-consumer queue — none of which Platform Events supports natively. Rearchitecting after implementation is expensive.

**When it occurs:** When mechanism selection is driven by familiarity ("we know Platform Events") rather than by architectural requirements (bus pattern, consistency model, replay depth, ordering guarantees).

**How to avoid:** Complete the architectural decision layer first: select a bus pattern from the five-pattern framework, decide choreography vs orchestration, establish the consistency model, and evaluate event sourcing requirements. Only after these decisions are recorded in an ADR should mechanism selection begin. The mechanism must fit the architecture, not the other way around.
