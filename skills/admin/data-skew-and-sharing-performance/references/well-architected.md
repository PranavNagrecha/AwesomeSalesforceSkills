# Well-Architected Notes — Data Skew and Sharing Performance

## Relevant Pillars

- **Reliability** — Data skew directly causes sharing recalculation failures, lock errors, and inconsistent access state. Eliminating skew before it accumulates is a reliability investment: operations that should be fast and deterministic remain so at scale.
- **Scalability** — Sharing recalculation cost grows non-linearly with record concentration. A pattern that works at 1,000 records may cause multi-hour background jobs at 100,000 records. Skew mitigation is fundamentally a scalability concern.
- **Security** — While this skill is not about security design (see sharing-and-visibility), data skew can leave sharing in an inconsistent state after a failed recalculation. Implicit sharing scans that are too slow to complete can temporarily expose incorrect access, making skew a security risk as well as a performance risk.
- **Operational Excellence** — Skew-driven lock errors are frequently misdiagnosed as integration bugs or infrastructure problems. Understanding the root cause reduces meantime-to-resolution and prevents recurring incidents.

## Architectural Tradeoffs

**Distributing ownership vs. simplifying integration:** Parking all imported records under one user simplifies integration design (no assignment logic required), but creates a time bomb. The more records accumulate, the higher the cost of any future role or group change for that user. The correct tradeoff is to build assignment logic early, before skew becomes a remediation project.

**"Controlled by Parent" vs. independent child sharing:** Configuring a child object as "Controlled by Parent" eliminates implicit sharing overhead entirely but permanently removes the ability to grant independent access to individual child records. This is the right choice for tightly-coupled parent-child models (e.g., Order Items under an Order) and the wrong choice for loosely-coupled models where child records may need to be shared independently (e.g., Contacts that might be shared with partners).

**Single large parent vs. segmented parents:** A single catch-all account is easy to manage initially but creates irreversible implicit sharing scan costs. Segmented parents are slightly more complex to maintain but scale indefinitely.

## Anti-Patterns

1. **The catch-all parking-lot account** — Creating a single Account to hold all unassociated Contacts, Leads, or Cases. Easy at import time, expensive as the org grows. Results in O(n) scans on every access change where n is the total children. Replace with multiple segmented accounts or "Controlled by Parent" OWD.

2. **The integration-user owner** — Routing all records from an external system through one service account user to keep integration logic simple. At 10,000+ records, this user becomes the most dangerous node in the role hierarchy. Any role or group change for this user fans out across all owned records. Distribute across queues or multiple service users from the start.

3. **Ignoring skew until it becomes a crisis** — Skew is often invisible until a major operation (end-of-quarter realignment, large import, org restructure) reveals it. By then, remediation requires batch re-parenting or re-assignment under production conditions, which itself can trigger the recalculation problems it is trying to fix. Run quarterly record count reports grouped by owner and by parent to catch accumulation early.

## Official Sources Used

- Designing Record Access for Enterprise Scale (Salesforce Architects) — primary source for ownership skew threshold (10,000 records), parent-child skew threshold (10,000 children), group membership locking behavior, granular locking concurrency table, and all mitigation recommendations. Stored locally at `knowledge/imports/draes.md`.
  URL: https://architect.salesforce.com/design/record-access-for-enterprise-scale
- Salesforce Large Data Volumes Best Practices — supplementary source for parent-child skew impact on related list rendering and implicit sharing scan behavior.
  URL: https://architect.salesforce.com/design/large-data-volumes
- Salesforce Well-Architected Overview — architecture quality framing for reliability and scalability pillars.
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — sObject relationship semantics (Lookup vs Master-Detail, Controlled by Parent OWD behavior).
  URL: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
