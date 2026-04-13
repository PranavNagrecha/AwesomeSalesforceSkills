---
name: event-driven-architecture
description: "Use when making architectural style decisions about whether and how to adopt event-driven architecture (EDA) for a Salesforce solution — including selecting a bus pattern, deciding between choreography and orchestration, designing event schema, and evaluating event sourcing feasibility. Triggers: 'should we use event-driven architecture or request-reply for this integration', 'designing an event mesh for Salesforce enterprise integration', 'choreography vs orchestration for our multi-system workflow', 'when does EDA add more complexity than value', 'how to architect event sourcing on Salesforce'. NOT for Platform Events implementation (use integration/event-driven-architecture-patterns). NOT for selecting between specific Salesforce event mechanisms such as Platform Events, CDC, or Pub/Sub API (use integration/event-driven-architecture-patterns)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
tags:
  - event-driven-architecture
  - choreography
  - orchestration
  - event-sourcing
  - event-mesh
  - pub-sub
  - architecture-decision
  - integration-architecture
  - event-design
inputs:
  - "Current integration topology — number of systems, direction of data flow, latency requirements"
  - "Transaction consistency requirements — strong ACID vs eventual consistency acceptable"
  - "Event volume and throughput expectations"
  - "Whether state reconstruction from event history is required (event sourcing)"
  - "Existing middleware or message broker infrastructure (Kafka, MuleSoft, etc.)"
  - "Salesforce edition and available features (Platform Events, CDC, Pub/Sub API)"
outputs:
  - "Architecture Decision Record (ADR) recommending EDA adoption or rejection with rationale"
  - "Selected EDA bus pattern with trade-off justification"
  - "Choreography vs orchestration recommendation with consistency implications"
  - "Event schema versioning strategy"
  - "External durable store requirement decision for event sourcing scenarios"
  - "Event mesh topology design for enterprise Salesforce"
triggers:
  - "Should we use event-driven architecture or request-reply for this integration"
  - "designing an event mesh for Salesforce enterprise integration"
  - "choreography vs orchestration for our multi-system workflow"
  - "when does event-driven architecture add more complexity than value"
  - "how to architect event sourcing on Salesforce without losing events"
  - "is Platform Events suitable for event sourcing"
  - "which EDA bus pattern should we use for our Salesforce integration"
dependencies:
  - integration/event-driven-architecture-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Event-Driven Architecture

Use this skill when the question is *whether* and *how* to adopt event-driven architecture as a strategic style for a Salesforce solution — not which specific Salesforce mechanism (Platform Events, CDC, Pub/Sub API) to use for a given integration requirement. This is the architectural decision layer that precedes mechanism selection.

---

## Before Starting

Gather this context before making architectural recommendations in this domain:

- What are the consistency requirements? Can the solution commit to eventual consistency, or does the workflow require strong transactional guarantees (e.g., financial settlement, inventory deduction)?
- How many systems need to react to the same business event? EDA pays off when fan-out is high; it adds unnecessary complexity when a single consumer is sufficient.
- Is state reconstruction from the event log a requirement? If yes, evaluate whether the event store has sufficient replay depth before recommending event sourcing.
- What is the failure tolerance model? Choreography tolerates partial failures; orchestration can centrally compensate.
- Most common wrong assumption: that Platform Events provide a durable event log suitable for event sourcing. The 72-hour default replay window does not support state reconstruction from event history without an external durable store.

---

## Core Concepts

### The Five EDA Bus Patterns

The Salesforce Architects EDA guide identifies five bus patterns available for Salesforce enterprise integration. Each solves a different routing and delivery problem:

| Pattern | Description | Best Fit |
|---|---|---|
| **Pub/Sub** | Publisher emits events; one or more subscribers consume independently | Decoupled notifications, audit feeds, cross-cloud fan-out |
| **Fanout** | A single event is delivered to all registered subscribers simultaneously | Broadcast scenarios where all consumers must receive every event |
| **Passed Messages** | Events carry data payloads routed point-to-point through a channel | Request-reply over async channel; workflow hand-off between bounded contexts |
| **Streaming** | Continuous ordered event feed consumed at subscriber pace (replay supported) | Analytics pipelines, CDC-driven data sync, audit trails |
| **Queuing** | Events are buffered; each event is consumed by exactly one worker (competing consumers) | Load leveling, exactly-once processing guarantee per event |

Selecting a bus pattern is an architectural decision — it determines the topology, failure propagation model, and consumer coupling before any Salesforce mechanism is chosen.

### Choreography vs Orchestration

**Choreography** is the coordination style where each service listens for events and reacts autonomously without a central authority directing the flow. There is no coordinator — each participant knows its own role.

- Decouples producers from consumers at design time
- Commits the solution to eventual consistency — no single participant knows the overall state of the process
- Failure in one participant does not block others, but compensating transactions must be designed explicitly
- Well-suited to: order lifecycle notifications, cross-cloud data sync, loosely coupled Salesforce-to-external workflows

**Orchestration** retains a central coordinator (Flow Orchestration, Apex, or a BPM tool) that directs each step explicitly and knows the overall process state.

- Retains transactional control — the orchestrator can compensate or roll back on failure
- Introduces coupling between the orchestrator and each participant service
- Suitable for: multi-step approval workflows, financial transactions requiring ACID-like guarantees, scenarios where a human-readable process map is required for compliance
- In Salesforce: Flow Orchestration provides managed orchestration with step-level monitoring; Apex-based orchestration via Queueable chains offers lower-level control

The critical architectural decision is not which tool to use but which *consistency model* the business requires. If eventual consistency is acceptable, choreography is the correct style. If the workflow cannot tolerate partial completion, orchestration is required.

### Event Sourcing — Architectural Considerations

Event sourcing is a pattern where the authoritative state of an entity is derived entirely by replaying its event history, rather than storing current state in a mutable record. It is architecturally distinct from simply publishing events.

**Platform Events are not a native event sourcing store.** The platform's default replay window is 72 hours (configurable to 3 days on some editions). After that window, events are no longer retrievable. This makes state reconstruction from event history architecturally unsound without an external durable store.

If event sourcing is genuinely required, the architecture must include one of:
- **Data Cloud** — durable storage with streaming ingestion via Pub/Sub API, suitable for Salesforce-native event sourcing
- **Apache Kafka** — enterprise-grade append-only log with configurable indefinite retention
- **Custom `Event_Log__c` object** — append-only Salesforce object storing event payloads; queryable via SOQL; subject to data storage limits and governor limits at high volume

Platform Events can act as the *transport* that delivers events to the durable store, but the store itself must live outside the Platform Events bus.

### Event Design Principles

Good event design is the foundation of a maintainable EDA. Four principles govern event schema quality:

1. **Schema versioning** — events must carry a schema version field. Consumers must tolerate unknown fields (forward compatibility). Breaking schema changes require version negotiation or a new event type, not an in-place modification.
2. **Idempotency** — consumers must be designed to process the same event more than once without side effects. At-least-once delivery is the default guarantee on most buses. Deduplication strategies: idempotency key on a custom object, UPSERT on an external ID, consumer-side processed-event log.
3. **Ordering guarantees** — most Salesforce buses do not guarantee strict ordering within a topic. Consumers that require ordered processing must implement sequence numbers or use a single-partition queue with a competing-consumer pattern.
4. **Event granularity** — events should represent a meaningful business fact (OrderPlaced, PaymentCaptured), not an implementation operation (RecordUpdated). Fine-grained technical events create brittle coupling between producer internals and consumers.

### Event Mesh Architecture

An event mesh is a network of interconnected event brokers that routes events dynamically across clouds, regions, and system boundaries. In Salesforce enterprise architecture, an event mesh typically connects:

- Salesforce Platform Events / Pub/Sub API as the Salesforce-native bus
- An enterprise message broker (Solace, Kafka, AWS EventBridge) as the inter-cloud routing layer
- External consumers (data warehouses, microservices, partner systems) subscribed through the mesh

Event mesh adoption is appropriate when events must traverse more than two systems or when the publisher and consumer landscape is expected to grow organically. For simple two-system integrations, a direct Pub/Sub channel is sufficient and a mesh adds unnecessary operational overhead.

### When NOT to Choose EDA

EDA adds architectural complexity. It is not the correct style for:

- **Simple request-reply integrations** — if System A needs a synchronous response from System B, use REST callout or SOAP. Adding an async event bus to a request-reply scenario adds latency and complicates error handling with no benefit.
- **Workflows requiring strong transactional guarantees** — if all steps must succeed or all must roll back atomically, choreography cannot deliver this. Consider orchestration or synchronous processing.
- **Low-volume point-to-point data sync** — if one system writes and one system reads, a direct integration or scheduled batch is simpler and more observable than an event-driven pipeline.
- **Teams without operational maturity for async debugging** — event-driven failures are harder to trace than synchronous call stacks. Without correlation ID conventions, centralized logging, and replay tooling, EDA increases mean time to resolution.

---

## Common Patterns

### Choreography for Cross-Cloud Order Lifecycle

**When to use:** An order placed in Salesforce must notify a fulfillment system, a finance system, and a customer notification service independently, with no centralized process coordinator.

**How it works:** Salesforce publishes an `Order_Placed__e` Platform Event. The fulfillment system (via MuleSoft or Pub/Sub API) subscribes and creates a fulfillment record. The finance system subscribes and posts a revenue recognition entry. The notification service subscribes and sends a confirmation email. Each subscriber operates independently and at its own pace.

**Why not orchestration:** The business accepted that a fulfillment delay does not block finance posting. Each system compensates independently on failure. Adding an orchestrator introduces a single point of failure and couples all three systems to the orchestrator's availability.

### Orchestration for Multi-Step Financial Transaction

**When to use:** A loan disbursement workflow requires credit check approval, compliance review, and fund transfer to complete in sequence — with full rollback if any step fails.

**How it works:** Flow Orchestration coordinates the steps sequentially. The orchestrator invokes each step, waits for completion, and can trigger compensation steps (e.g., reverse a credit hold) if a downstream step fails. All steps are visible in the orchestration monitor.

**Why not choreography:** The business requires that all three steps complete or none do. Eventual consistency is not acceptable for fund disbursement. An orchestrator provides centralized state and compensation capability.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Multiple systems must react to the same business event independently | Choreography via Pub/Sub or Fanout | No coordinator needed; decoupling maximizes |
| Workflow requires all steps to complete or all to roll back | Orchestration (Flow Orchestration or Apex Queueable) | Central coordinator can compensate on failure |
| State reconstruction from event history is required | Event sourcing with external durable store (Data Cloud / Kafka) | 72-hour Platform Events replay window is insufficient |
| Single producer, single consumer, synchronous response needed | Request-reply (REST/SOAP callout) | EDA adds complexity without benefit |
| Enterprise-wide events spanning multiple clouds and systems | Event mesh with enterprise broker | Direct bus-to-bus connections become unmanageable at scale |
| Event volume exceeds what a single consumer can process in real time | Queuing pattern with competing consumers | Load leveling distributes processing across workers |
| Two-system integration with low volume | Direct callout or scheduled batch | EDA overhead is not justified |

---

## Recommended Workflow

Step-by-step instructions for making an EDA architectural decision:

1. **Clarify consistency requirements** — establish whether the business process requires strong transactional guarantees or can accept eventual consistency. This single answer constrains the rest of the decision.
2. **Map the event topology** — identify all producers and consumers, the events that flow between them, and whether fan-out (one event, many consumers) or point-to-point is the dominant pattern.
3. **Select a bus pattern** — using the five-pattern framework (Pub/Sub, Fanout, Passed Messages, Streaming, Queuing), identify which pattern matches the topology and delivery semantics required.
4. **Choose choreography or orchestration** — if eventual consistency is acceptable and consumers are independent, choose choreography. If transactional control or compensation is required, choose orchestration.
5. **Evaluate event sourcing need** — if state reconstruction from event history is required, confirm an external durable store is included in scope (Data Cloud, Kafka, or Event_Log__c). Do not rely on Platform Events replay.
6. **Design event schema** — define event payloads with schema version field, idempotency key, business event name (not operation name), and ordering metadata if sequence matters.
7. **Document the Architecture Decision Record** — record the chosen pattern, the consistency model, the trade-offs accepted, and the external store strategy. This ADR is the deliverable that precedes mechanism selection.

---

## Review Checklist

Run through these before marking EDA architectural work complete:

- [ ] Consistency model is explicitly documented — eventual consistency or transactional control
- [ ] All producers and consumers are identified with event topology mapped
- [ ] Bus pattern selected from the five-pattern framework with rationale recorded
- [ ] Choreography vs orchestration decision is explicit and tied to consistency requirement
- [ ] Event sourcing feasibility evaluated — external durable store included in design if required
- [ ] Event schema includes version field and idempotency key
- [ ] Failure and compensation strategy is defined for choreography scenarios
- [ ] ADR completed before mechanism selection (Platform Events vs CDC vs Pub/Sub API vs external broker)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Platform Events 72-hour replay ceiling** — the default event replay window is 72 hours. After that, events are gone from the bus. Any architecture that relies on replaying Platform Events to reconstruct state or recover a consumer backlog beyond 3 days will fail silently — consumers simply miss events with no error.
2. **Choreography commits to eventual consistency — permanently** — teams often adopt choreography because it is easy to get started, then discover later that a compliance requirement demands proof that all steps completed. Choreography does not provide this by default. The consistency model must be a conscious architectural choice, not an afterthought.
3. **Platform Events ordering is not guaranteed** — events published to the same Platform Events channel can be delivered out of order under high throughput. Consumers that assume ordered delivery will produce incorrect results. Sequence number fields and consumer-side ordering logic are required if order matters.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Architecture Decision Record (ADR) | Documents EDA adoption decision, selected bus pattern, consistency model, and trade-offs accepted |
| Event topology diagram | Producer-consumer map showing event flows, bus patterns, and external system boundaries |
| Event schema specification | Field definitions including schema version, idempotency key, and business event name |
| External durable store design | Required when event sourcing is in scope; specifies store technology and retention policy |
| Choreography/Orchestration decision memo | Records which coordination style is chosen and why, tied to consistency requirements |

---

## Related Skills

- `integration/event-driven-architecture-patterns` — use after the architectural decision is made to select the specific Salesforce mechanism (Platform Events, CDC, Pub/Sub API, Change Data Capture)
- `apex/long-running-process-orchestration` — use when orchestration is chosen and Apex Queueable chains are the implementation vehicle
- `flow/orchestration-flows` — use when Flow Orchestration is selected as the orchestration runtime
- `architect/integration-framework-design` — use when designing the reusable integration layer that carries events between systems
- `architect/data-cloud-architecture` — use when Data Cloud is the selected external durable store for event sourcing
