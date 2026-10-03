# LLM Anti-Patterns — HA/DR Architecture

Mistakes AI assistants commonly make when advising on Salesforce HA/DR architecture.

---

## Anti-Pattern 1: Treating Salesforce's 99.9% SLA as a Data Recovery Guarantee

**What the LLM generates:** "Salesforce guarantees 99.9% uptime and handles all recovery, so you don't need a separate backup strategy."

**Why it is wrong:** The 99.9% SLA (figure UNVERIFIED 2026-10-03; it is contractual) is an infrastructure availability commitment. It does not guarantee record-level data recovery if customer data is deleted, corrupted, or overwritten. Data protection is explicitly in the customer's portion of the shared responsibility model. A Salesforce outage that results in no data loss is still covered by the SLA; customer-caused data loss is not.

**Correct guidance:** Clearly separate infrastructure availability (Salesforce's responsibility) from data recovery readiness (customer's responsibility). Always recommend a dedicated backup solution for production orgs holding non-recreatable data.

---

## Anti-Pattern 2: Recommending Hyperforce Migration as the Primary HA Control

**What the LLM generates:** "Migrate to Hyperforce for high availability — it gives you multi-region redundancy and cross-region failover."

**Why it is wrong:** Hyperforce provides Salesforce-managed infrastructure redundancy and data-residency options. It does not give customers the ability to initiate or control cross-region failover. Presenting Hyperforce as a customer-controllable HA lever creates false confidence and incorrect architecture decisions.

**Correct guidance:** Hyperforce is relevant to HA/DR architecture for compliance/data-residency framing and Salesforce's own infrastructure posture. Customer-controlled resilience must be built at the integration layer (circuit breakers, durable queues) and the data layer (backup tooling), regardless of whether the org is on Hyperforce.

---

## Anti-Pattern 3: Assuming Platform Events Can Buffer Indefinitely

**What the LLM generates:** "Use Platform Events as the integration buffer — subscribers can replay missed events when they reconnect after an outage."

**Why it is wrong:** High-volume platform events are retained for 72 hours and legacy standard-volume events for 24 hours (Platform Events Developer Guide); change events for three days (Change Data Capture Developer Guide). Events older than the window cannot be replayed, and Salesforce does not retry delivery (*Integration Patterns and Practices*). For extended outages or slow-recovering subscribers, events will be permanently lost. This limit cannot be extended by configuration or purchase (UNVERIFIED 2026-10-03: no fetched source states whether an extension exists).

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

---

## Anti-Pattern 7: Promising an RTO Without Restore-Throughput Math

**What the LLM generates:** "With hourly backups you can restore any object within 4 hours."

**Why it is wrong:** Restore speed is bounded by the Bulk API allocation, 15,000 batches and 150,000,000 records per rolling 24 hours, shared between Bulk API and Bulk API 2.0 (*Salesforce Developer Limits and Allocations Quick Reference*), and further slowed by automation on every inserted row. Backup frequency sets RPO; it says nothing about RTO.

**Correct guidance:** Compute restore time per object from row counts, the remaining daily allocation after normal integration use, and a measured sandbox restore rate. Tier the RTO (recent records first) when the full restore cannot meet the target.

---

## Anti-Pattern 8: Restoring Through the API With All Automation Running

**What the LLM generates:** A runbook step that says "use the backup tool to restore the deleted records" with nothing about automation.

**Why it is wrong:** A restore is an insert or update, so it runs the whole order of execution in the Apex Developer Guide ("Triggers and Order of Execution"): flows, triggers, validation, workflow, and post-commit email and async jobs. Restores can email customers, fail on validation rules added since the backup, and re-send records to integrations.

**Correct guidance:** Build an automation bypass (custom permission or setting held by a dedicated restore user) before the incident, test the restore with it in a sandbox, and list the validation rules that must be relaxed for historical data.

---

## Anti-Pattern 9: Hardcoding the Instance Key and Reading Only the Top-Level Status

**What the LLM generates:** A monitor that polls `/v1/instances/NA152/status` forever and pages when `status != "OK"` or when `Incidents` is non-empty.

**Why it is wrong:** The instance key belongs in the org (`Organization.InstanceName`, Object Reference), not in a script constant. In the Trust API response checked on 2026-10-03, `Incidents` also held resolved incidents, and `Services` entries had no health field, so both naive checks misfire.

**Correct guidance:** Read the instance from the org at startup and after refreshes. Page on incidents whose own `status` is not resolved and whose `serviceKeys` include a service the org depends on (see `examples.md` Example 5).

