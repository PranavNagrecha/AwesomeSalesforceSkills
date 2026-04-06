# Gotchas — NFR Definition for Salesforce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Full Sandbox Required for Performance Validation

**What happens:** Performance NFRs validated in a Developer Pro or Partial Copy sandbox produce optimistic results that do not reflect production behaviour. Developer Pro sandboxes have a 200 MB storage ceiling and sparse record distribution. Queries that perform well against 10,000 records often degrade non-linearly when record counts reach millions, due to index selectivity changes and storage tier I/O differences.

**When it occurs:** Any time a performance NFR is tested in a sandbox that is not a Full sandbox with a representative data copy.

**How to avoid:** State explicitly in every performance NFR: "Validated in Full sandbox with production-equivalent data volume (specify record count)." If a Full sandbox is unavailable before go-live, the NFR is unverified and must be flagged as a go-live risk, not signed off as met.

---

## Gotcha 2: Daily API Limit is Org-Wide and Shared Across All Integrations

**What happens:** Salesforce API call limits are calculated at the org level across all licensed users and all integrations. A new integration that consumes a large percentage of the daily allocation can starve other integrations or block interactive UI features that rely on API calls (e.g., external lookups, Connected App OAuth flows).

**When it occurs:** When multiple integration teams define their throughput NFRs independently, each assuming they have the full allocation, without a cross-integration capacity plan.

**How to avoid:** Maintain a single API allocation budget table in the NFR register. List every integration by name, estimated calls per day, and percentage of total allocation. Ensure the sum stays under 80% to leave headroom for interactive usage and unexpected spikes. Use Bulk API v2 for record-volume integrations to minimise call count.

---

## Gotcha 3: Salesforce Trust SLA is Infrastructure-Only — Custom Code is Not Covered

**What happens:** Teams interpret the Salesforce 99.9% Trust SLA as a total system availability guarantee. When custom Apex code causes a production outage (unhandled exception disabling a critical flow, governor limit breach in peak load, scheduled job failure), the incident is classified as a customer-caused issue and is not covered by the SLA credit mechanism.

**When it occurs:** During post-incident reviews, when teams try to claim SLA credits for incidents caused by custom code, bad deployments, or integration failures. Also during NFR sign-off, when "99.9% availability" is accepted without defining what "availability" means for this implementation.

**How to avoid:** Define availability at two levels in the NFR register. Level 1: Salesforce infrastructure availability (99.9%, Salesforce-owned, monitored at trust.salesforce.com). Level 2: Application availability (custom-code-level, team-owned, with RPO/RTO, alerting, and rollback procedures defined).

---

## Gotcha 4: Governor Limits Do Not Scale With License Count for Synchronous Transactions

**What happens:** Teams assume that buying more licenses increases all governor limits proportionally. Daily API call allocation does scale with license count, but synchronous transaction limits (SOQL rows, DML statements, CPU time, heap) are fixed per transaction regardless of edition or license count. A transaction processing 60,000 SOQL rows will fail whether the org has 10 users or 10,000.

**When it occurs:** When scalability NFRs are written as "must handle X records" without distinguishing batch (async, higher limits per chunk) from real-time (sync, hard per-transaction ceilings).

**How to avoid:** Every scalability NFR must specify the processing mode. Sync NFRs must stay within per-transaction ceilings. Async NFRs (Batch Apex, Queueable, Platform Events) have different and generally higher limits and are the correct target for high-volume operations.

---

## Gotcha 5: Compliance NFRs That Reference Future Features Are Not Met Until the Feature is Live

**What happens:** A security NFR states "encryption at rest enabled via Shield Platform Encryption." The team adds it to the register, assumes it is satisfied by Salesforce's product roadmap or their Shield license purchase, and signs off go-live. The encryption policy has not yet been configured and tested. Sensitive data goes live unencrypted.

**When it occurs:** When compliance NFRs are written at the feature-purchase level ("we have Shield") rather than at the configuration and verification level ("Shield encryption policy is active on these fields, verified by attempting a plaintext API read").

**How to avoid:** Every compliance NFR must include a concrete acceptance criterion that is verified by a specific test step — not by license ownership or feature availability. "Shield Platform Encryption is licensed" is not an acceptance criterion. "Querying Account.SSN via REST API returns an encrypted token (not plaintext) in UAT" is.
