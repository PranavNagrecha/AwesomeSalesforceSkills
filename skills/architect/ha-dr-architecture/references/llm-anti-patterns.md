# LLM Anti-Patterns — HA/DR Architecture

Mistakes AI assistants commonly make when advising on Salesforce HA/DR architecture.

---

## Anti-Pattern 1: Treating Salesforce's 99.9% SLA as a Data Recovery Guarantee

**What the LLM generates:** "Salesforce guarantees 99.9% uptime and handles all recovery, so you don't need a separate backup strategy."

**Why it is wrong:** The 99.9% SLA is an infrastructure availability commitment. It does not guarantee record-level data recovery if customer data is deleted, corrupted, or overwritten. Data protection is explicitly in the customer's portion of the shared responsibility model. A Salesforce outage that results in no data loss is still covered by the SLA; customer-caused data loss is not.

**Correct guidance:** Clearly separate infrastructure availability (Salesforce's responsibility) from data recovery readiness (customer's responsibility). Always recommend a dedicated backup solution for production orgs holding non-recreatable data.

---

## Anti-Pattern 2: Recommending Hyperforce Migration as the Primary HA Control

**What the LLM generates:** "Migrate to Hyperforce for high availability — it gives you multi-region redundancy and cross-region failover."

**Why it is wrong:** Hyperforce provides Salesforce-managed infrastructure redundancy and data-residency options. It does not give customers the ability to initiate or control cross-region failover. Presenting Hyperforce as a customer-controllable HA lever creates false confidence and incorrect architecture decisions.

**Correct guidance:** Hyperforce is relevant to HA/DR architecture for compliance/data-residency framing and Salesforce's own infrastructure posture. Customer-controlled resilience must be built at the integration layer (circuit breakers, durable queues) and the data layer (backup tooling), regardless of whether the org is on Hyperforce.

---

## Anti-Pattern 3: Assuming Platform Events Can Buffer Indefinitely

**What the LLM generates:** "Use Platform Events as the integration buffer — subscribers can replay missed events when they reconnect after an outage."

**Why it is wrong:** Platform Events have a 72-hour hard retention limit. Events older than 72 hours cannot be replayed. For extended outages or slow-recovering subscribers, events will be permanently lost. This limit cannot be extended by configuration or purchase.

**Correct guidance:** Platform Events are appropriate for short-duration buffering. For integrations where event loss is unacceptable and outage duration is unpredictable, supplement with an external durable queue (AWS SQS, Azure Service Bus, Anypoint MQ) with configurable retention.

---

## Anti-Pattern 4: Equating "Daily Backup" with an Acceptable RPO

**What the LLM generates:** "Salesforce Backup and Restore runs daily, so your RPO is 24 hours — which is standard and acceptable."

**Why it is wrong:** Whether 24 hours is an acceptable RPO depends entirely on the business requirements for each data category. For financial transaction records, a 24-hour RPO may be a regulatory compliance failure. The LLM should not normalize a 24-hour RPO; it should prompt the user to define RPO from business requirements and then map it to backup tooling capability.

**Correct guidance:** Start with the business's required RPO (obtained from stakeholders, not assumed). Map that requirement against the actual backup cadence. If there is a gap, recommend tooling that closes it — hourly incremental backup tools or near-real-time replication.

---

## Anti-Pattern 5: Omitting Metadata from the DR Scope

**What the LLM generates:** A DR plan that covers record data, files, and integration state — but does not mention metadata (Apex classes, flows, page layouts, permission sets, etc.).

**Why it is wrong:** Metadata loss can be as catastrophic as record data loss. An org with records but no metadata is not recoverable. Metadata recovery from a weekly CSV export is effectively impossible. If configuration drift or a bad deployment corrupts metadata, recovery speed depends entirely on whether metadata is version-controlled.

**Correct guidance:** Always include metadata in the DR scope. The recommended approach is source-control-driven deployment (Salesforce CLI + Git) with a Git history that serves as the metadata backup. Supplement with automated metadata retrieval jobs for orgs that have significant declarative configuration that may not be captured in the deployment pipeline.

---

## Anti-Pattern 6: Designing Integration Failover Without Testing Drain Procedures

**What the LLM generates:** A circuit-breaker and queue-based failover design is proposed and documented, but the design stops at the recovery queue setup without describing how the queue drains after Salesforce recovers.

**Why it is wrong:** Queue drain is where most HA/DR failures happen in practice. Without documented and tested drain procedures — including idempotency checks, duplicate prevention, order guarantees, and rate limit awareness — recovery can cause a data integrity incident that is worse than the original outage.

**Correct guidance:** For every integration failover pattern that includes a durable queue, explicitly design and test the drain procedure: drain order, idempotency handling, upsert vs insert semantics, API rate limit consumption, and stakeholder notification when drain completes.
