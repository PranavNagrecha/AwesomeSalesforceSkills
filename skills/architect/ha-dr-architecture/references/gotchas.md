# Gotchas — HA/DR Architecture

Non-obvious Salesforce platform behaviors that cause real problems in HA/DR design.

---

## Gotcha 1: Salesforce's 99.9% SLA Covers Infrastructure — Not Your Data

**What happens:** Architects read "99.9% uptime" and assume Salesforce guarantees full data recovery if something goes wrong on Salesforce's side.

**The reality:** The SLA covers infrastructure availability — whether the platform accepts requests. It does not guarantee that customer-deleted, overwritten, or corrupted records are restored. Salesforce's SLA does not include a contractual data-recovery commitment beyond the infrastructure redundancy it already operates. Data protection is a shared responsibility: customer data backup is the customer's obligation.

**How to handle it:** Always separate availability SLA from data recovery SLA. Document both separately. Budget for a backup product if the org holds data that cannot be recreated.

---

## Gotcha 2: Sandbox Refresh Silently Changes the Instance Key

**What happens:** Trust site monitoring is set up against production (e.g., `NA152`) and a critical sandbox (e.g., `CS9`). After a sandbox refresh, the sandbox is provisioned on a different instance. The monitoring configuration still polls the old instance key — which may belong to a completely different customer's pod.

**When it occurs:** Any time a full sandbox refresh is performed or a new sandbox is created.

**How to handle it:** After every sandbox refresh, re-verify the instance key from Setup > Company Information and update monitoring configurations. Automate this check in the refresh runbook.

---

## Gotcha 3: Platform Event Replay Has a 72-Hour Hard Ceiling

**What happens:** An integration uses Platform Events as a buffer. During a Salesforce outage lasting more than 72 hours (rare but possible for extended incidents), events published before the outage expire before the subscriber reconnects.

**The reality:** The 72-hour retention window for Platform Events is a hard limit that cannot be extended. Gap events cannot be replayed after expiry.

**How to handle it:** For integrations where data loss on gaps is unacceptable, supplement Platform Events with an external durable queue (SQS, Service Bus) that has configurable retention. Use Platform Events for the normal path; the external queue as the safety net.

---

## Gotcha 4: Native Data Export (Weekly CSV) is Not a Backup Strategy

**What happens:** Organizations point to Salesforce's native "Data Export" (weekly CSV download) as their backup solution and calculate RPO based on it.

**The reality:** The native Data Export does not include files/attachments, does not include all related metadata, cannot perform record-level restore without manual re-import, and runs only weekly (or daily with the scheduled export option, but that still leaves a 24-hour gap). More critically, re-importing CSV data can create duplicates, miss relationships, and trigger automation incorrectly.

**How to handle it:** Treat native Data Export as an emergency last resort. Use Salesforce Backup and Restore or a third-party tool as the primary backup mechanism.

---

## Gotcha 5: Hyperforce Does Not Equal Customer-Controlled Cross-Region Failover

**What happens:** An architect proposes Hyperforce migration as the HA/DR strategy, implying the customer can trigger cross-region failover themselves during an outage.

**The reality:** Hyperforce provides Salesforce-managed geographic redundancy at the infrastructure layer. Customers cannot initiate failover events. Region selection determines data residency and the cloud provider's infrastructure, but the failover decision remains with Salesforce. Hyperforce improves Salesforce's own recovery posture but does not give customers new controls.

**How to handle it:** Set accurate expectations. Hyperforce is a compliance and data-residency tool as much as an availability tool. Customer-controlled HA must be built at the integration and data layer, not the infrastructure layer.

---

## Gotcha 6: Big Object Archival Data Cannot Be Restored via Backup Tools

**What happens:** An org uses Big Objects to archive historical records. The HA/DR plan assumes the backup tool covers Big Objects.

**The reality:** Most backup tools — including Salesforce's native Backup and Restore — do not support Big Object backup and restore as of Spring '25. Big Objects are append-only and cannot be updated or deleted via standard DML. Backup tooling coverage for Big Objects varies by vendor and must be confirmed explicitly.

**How to handle it:** Treat Big Object data as effectively write-once archive. Back up the upstream data before it is archived into Big Objects. Verify Big Object coverage with your backup vendor before including it in your RPO commitments.
