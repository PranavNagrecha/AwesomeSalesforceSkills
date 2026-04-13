# Well-Architected Notes — Event-Driven Architecture

## Relevant Pillars

- **Scalability** — EDA is fundamentally a scalability pattern. The Pub/Sub and Queuing bus patterns decouple producer throughput from consumer capacity, allowing each side to scale independently. Event mesh architecture allows the Salesforce platform to participate in enterprise-scale event flows without becoming a bottleneck. The queuing pattern specifically enables load leveling — events accumulate in the buffer during peak load and consumers drain at their own rate.

- **Reliability** — Choreography improves reliability at the component level by isolating failures. A single consumer failure does not cascade to other consumers. However, choreography trades system-level reliability for component reliability — the overall process has no central monitor and compensating transactions must be designed explicitly. Orchestration provides higher system-level reliability for multi-step workflows by enabling coordinated compensation.

- **Operational Excellence** — EDA increases operational complexity. Async failures are harder to trace than synchronous call stacks. Well-architected EDA requires: correlation IDs on every event and every log entry, centralized log aggregation (e.g., Event_Log__c or external observability platform), replay strategy documented and tested, and consumer health monitoring. Without these, mean time to resolution for EDA failures is significantly higher than for synchronous integrations.

- **Security** — Events can carry sensitive data (PII, financial records, health information). Event schema design must include data classification decisions: which fields are safe to include in an event payload vs. which require the consumer to fetch from the source system using a reference ID. Event bus access control (who can publish, who can subscribe) must be governed. For Salesforce Platform Events, this means Named Credentials for external subscribers and permission sets governing internal subscribers.

- **Performance** — EDA introduces inherent latency between event publication and consumer processing. This is acceptable for eventually consistent use cases but incompatible with synchronous response requirements. The architectural decision must explicitly account for this latency budget. Streaming patterns (CDC, Pub/Sub API streaming) minimize latency relative to polling-based approaches.

## Architectural Tradeoffs

**Choreography vs Orchestration:** Choreography maximizes decoupling and independently scalable components at the cost of global process visibility and strong consistency. Orchestration provides transactional control and a centralized process model at the cost of coupling to the orchestrator and a single point of failure if the orchestrator is unavailable. Neither is universally superior — the choice is determined by the business consistency requirement.

**Event sourcing vs mutable state:** Event sourcing provides a complete audit trail and enables temporal queries ("what was the state at time T?") but requires an external durable store and significantly more complex consumer logic. Mutable state (standard Salesforce records) is simpler to implement and query. Event sourcing should be adopted only when audit trail completeness and state reconstruction are genuine business requirements, not as a default pattern.

**EDA complexity vs operational simplicity:** An event-driven solution is harder to debug, harder to test end-to-end, and harder to explain to non-technical stakeholders than a synchronous integration. This complexity cost is justified when the fan-out is high (many consumers), throughput is high (consumers must scale independently), or decoupling is a hard requirement. For simple integrations, request-reply is the operationally simpler and correct choice.

## Anti-Patterns

1. **Treating Platform Events as an event store** — Platform Events are a delivery bus, not a durable log. Using them as the source of truth for event sourcing or relying on their 72-hour replay window for disaster recovery creates an architecture that fails silently after the window expires. Always pair Platform Events with an external durable store when persistence beyond 72 hours is required.

2. **Defaulting to choreography without a consistency decision** — Choreography is easy to start and difficult to retrofit with transactional guarantees. Adopting it without an explicit decision that eventual consistency is acceptable leads to expensive rearchitecting when compliance or audit requirements surface. The consistency model must be a first-class architectural decision, not a default.

3. **Applying EDA to request-reply use cases** — Adding an event bus to a synchronous request-reply integration (single producer, single consumer, synchronous response expected) adds latency, complexity, and debugging overhead with no architectural benefit. EDA is appropriate for fan-out, load leveling, and decoupled async workflows — not as a universal integration pattern.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Event-Driven Architecture Decision Guide (Salesforce Architects) — https://architect.salesforce.com/decision-guides/event-driven
- Integration Patterns and Practices — Appendix C: EDA (Salesforce Architects) — https://architect.salesforce.com/design/decision-guides/integrate
