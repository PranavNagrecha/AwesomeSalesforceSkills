# Event-Driven Architecture — Decision Template

Use this template when making an EDA architectural style decision for a Salesforce solution. Complete all sections before mechanism selection (Platform Events vs CDC vs Pub/Sub API vs external broker).

## Scope

**Skill:** `architect/event-driven-architecture`

**Request summary:** (describe the integration or workflow scenario in 1-2 sentences)

**Related mechanism selection:** After completing this ADR, use `integration/event-driven-architecture-patterns` to select the specific Salesforce mechanism.

---

## 1. Business Context

**Systems involved:** (list all producers, consumers, and external systems)

**Event volume estimate:** (events per second / minute / day)

**Latency tolerance:** (real-time < 1s / near-real-time < 30s / batch / not constrained)

**Fan-out requirement:** (how many consumers react to the same event?)

---

## 2. Consistency Model Decision

**Can the solution accept eventual consistency?**
- [ ] Yes — steps may complete at different times; partial completion is tolerable
- [ ] No — all steps must complete or all must roll back; transactional guarantees required

**If No:** Do not use choreography. Proceed to orchestration selection.

**Consistency rationale:** (explain why the business can or cannot accept eventual consistency)

---

## 3. Bus Pattern Selection

Select the pattern that matches the topology and delivery semantics:

| Pattern | Selected | Rationale |
|---|---|---|
| Pub/Sub — one publisher, multiple independent subscribers | | |
| Fanout — broadcast to all subscribers simultaneously | | |
| Passed Messages — point-to-point with payload routing | | |
| Streaming — ordered continuous feed, consumer-paced | | |
| Queuing — competing consumers, exactly-one processing per event | | |

**Selected pattern:** _______________

**Rationale:** (explain why this pattern fits the topology)

---

## 4. Choreography vs Orchestration

*(Complete only if EDA is the correct style — skip if request-reply is sufficient)*

**Coordination style:**
- [ ] Choreography — async, no central authority, eventual consistency accepted
- [ ] Orchestration — central coordinator, transactional control, compensation required

**If Choreography:**
- Failure isolation strategy: (how does each consumer handle its own failure?)
- Compensation strategy: (how are partial completions detected and corrected if needed?)
- Saga correlation: (how will you correlate events across consumers if needed?)

**If Orchestration:**
- Orchestration runtime: (Flow Orchestration / Apex Queueable / external BPM)
- Compensation steps: (what happens if a step fails?)
- Process visibility: (where is the orchestration state monitored?)

---

## 5. Event Sourcing Evaluation

**Is state reconstruction from event history required?**
- [ ] No — mutable record state is sufficient
- [ ] Yes — full event history must be replayable

**If Yes:**
- Platform Events replay window: 72 hours maximum. This is NOT sufficient for event sourcing without a durable store.
- External durable store required:
  - [ ] Data Cloud (Pub/Sub API streaming ingestion)
  - [ ] Apache Kafka (configurable retention)
  - [ ] Custom Event_Log__c append-only object
  - [ ] Other: _______________
- Retention requirement: _______________
- State reconstruction query: (SOQL on Event_Log__c / Kafka consumer group / Data Cloud query)

---

## 6. Event Schema Design

**Event type name:** (use business-event naming: OrderPlaced, PaymentCaptured — NOT RecordUpdated)

**Required envelope fields:**

| Field | Value / Notes |
|---|---|
| schemaVersion | 1.0 |
| eventId | UUID — idempotency key |
| eventType | (business event name) |
| occurredAt | ISO-8601 timestamp |

**Business payload fields:**

| Field | Type | Notes |
|---|---|---|
| (field name) | (type) | (purpose) |

**Schema versioning strategy:** (how will breaking changes be handled — new event type / version negotiation?)

**Idempotency strategy:** (UPSERT on External ID / processed-event log / unique index)

**Ordering requirement:**
- [ ] No ordering guarantee required
- [ ] Sequence number included — consumers implement ordering logic

---

## 7. Is EDA the Correct Architectural Style?

Before finalizing, confirm EDA is justified. EDA is NOT appropriate when:

- [ ] Single producer, single consumer, synchronous response expected → use request-reply
- [ ] All steps require atomic commit → use orchestration with synchronous processing
- [ ] Low event volume, simple point-to-point → use scheduled batch or direct callout
- [ ] Team lacks operational maturity for async debugging → build observability first

**Decision:** 
- [ ] EDA is the correct style — proceed to mechanism selection
- [ ] EDA is NOT appropriate — use: _______________

---

## 8. Architecture Decision Record (ADR)

**Decision:** (EDA / request-reply / orchestration with synchronous processing)

**Bus pattern:** _______________

**Coordination style:** (choreography / orchestration)

**Consistency model:** (eventual / transactional)

**Event sourcing:** (not required / required with [store technology])

**Trade-offs accepted:**
- (list what the solution gives up by choosing this architecture)

**Trade-offs gained:**
- (list the architectural benefits)

**Constraints and assumptions:**
- Platform Events replay window: 72 hours
- (other platform limits relevant to this decision)

**Next step:** Use `integration/event-driven-architecture-patterns` to select the Salesforce mechanism (Platform Events / CDC / Pub/Sub API / external broker) that implements this architectural decision.

---

## 9. Review Checklist

- [ ] Consistency model is explicitly documented and accepted by business stakeholders
- [ ] All producers and consumers are identified
- [ ] Bus pattern selected from the five-pattern framework with rationale
- [ ] Choreography vs orchestration decision is tied to consistency requirement
- [ ] Event sourcing evaluated — external durable store in scope if required
- [ ] Event schema includes version field, idempotency key, and business-event naming
- [ ] Failure and compensation strategy defined
- [ ] ADR completed and approved before mechanism selection begins
