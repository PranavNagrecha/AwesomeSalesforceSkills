# Examples — limits-and-scalability-planning

## Example 1: Mass Update Across 10 Million Account Records

### Scenario

A financial services org has 10 million Account records accumulated over 12 years. The business needs to retroactively populate a new custom field (`Industry_Segment__c`) on all accounts based on a classification rule applied to the existing `Industry` and `AnnualRevenue` fields. The team's first proposal is a one-time data load using Data Loader.

### Limit Risks Identified

**Batch Apex ceilings.** A full pass over 10 million accounts is inside the 50-million-record ceiling a single `Database.QueryLocator` can return (Apex Developer Guide 264 L17902–17903). The constraint that bites is the 24-hour rolling async execution budget — 250,000 or licenses × 200, whichever is greater (264 L19936–19940). At scope 200 the job needs 50,000 `execute` calls plus `start` and `finish` (L20001–20002); if nightly sync jobs have already drawn the budget down, `executeBatch` throws `AsyncApexExecutions Limit exceeded` and the job never starts (L17895–17899). Check remaining executions before submitting the classification job.

**Batch scope size vs. heap.** If the classification formula in Apex loads related Contact or Opportunity records to inform the decision, each account's "object graph" in memory grows. At 200 records per scope (the default when no scope is passed, 264 L17909–17910), Apex holds 200 accounts plus their related records in heap simultaneously. A 25MB async heap limit (Winter '27 release, not API-version-gated; it was 12MB through Summer '26, about 60KB per account; Apex Developer Guide 264 L19780) at scope 200 means roughly 125KB of in-memory object data per account before overflow. Complex graphs require reducing scope to 50 or 100.

**Data skew and sharing recalculation.** The org uses a private sharing model on Account. The integration user that originally imported these accounts owns 9.8 million of them. The classification job will not change ownership, but if the org's sharing rules are based on field values (e.g., a criteria-based sharing rule on `Industry_Segment__c`), then populating the new field triggers sharing recalculation for every affected record. At 10 million records with a single-owner skew, recalculation may lock the Account object for hours.

**SOQL selectivity on large objects.** Any query in the batch `start()` method that filters Accounts without an indexed WHERE clause runs a full table scan on 10 million records. Use the Account `Id` in ORDER BY, and if filtering by `Industry`, confirm that field is indexed. A non-selective `start()` query will time out before the batch even begins.

### Recommended Approach

1. Use Batch Apex with a `Database.QueryLocator` in `start()` using a selective filter (e.g., `WHERE Industry_Segment__c = null` — null checks on non-indexed fields are not selective; add a date-based indexed filter or process all records using ORDER BY Id).
2. Set scope to 100 to control heap if related records are being loaded, or 200 if the classification is field-only and no related SOQL is required in `execute()`.
3. Disable criteria-based sharing rules on Account temporarily during the bulk operation (requires Salesforce support or a Custom Setting bypass flag in the sharing rule criteria) if sharing recalculation volume is a confirmed risk.
4. Schedule the batch job during off-peak hours to avoid competing for the 5-job queue limit (264 L19985) with other nightly jobs.
5. Confirm `DailyAsyncApexExecutions` headroom in the REST limits resource (REST API Developer Guide 264 L7986) covers the job's 50,002 executions before scheduling.

---

## Example 2: Org Approaching the 800 Custom Object Limit

### Scenario

An Enterprise Edition org has grown organically over 9 years through multiple project teams building domain-specific data models. A pre-release audit reveals the org has 763 custom objects — 95% of the 800-object Enterprise Edition limit (UNVERIFIED (2026-10-20): the 800 figure is not in the Winter '27 corpus and conflicts with the 200 EE figure in llm-anti-patterns.md; confirm the edition allocation before using this percentage). A new CRM Analytics project wants to add 25 more custom objects for staging data. Approving the request would bring the org to 788 objects, leaving only 12 in reserve for future work.

### Limit Risks Identified

**No safety buffer for emergency objects.** Custom objects are created during incidents (temporary staging, manual data repair tables) and during feature development that is partially complete. At 788 objects, a critical deployment requiring 13 new objects would fail at the org limit before the work is complete.

**Managed package objects count toward the limit.** Many teams overlook that installed managed packages contribute to the org's custom object count. If a newly installed package adds 20 objects, the org could hit 800 without any internal development activity. The REST limits resource does not report custom object usage — its documented keys cover API, async Apex, Bulk API, platform event and storage allocations (REST API Developer Guide 264 L7923–8222), with no custom-object key — so count objects with a Tooling API query on `EntityDefinition` and confirm managed vs. unmanaged counts separately via Setup > Object Manager.

**Field limits on heavily used objects.** With 763 objects in the org, the probability is high that at least some objects have accumulated fields from multiple project cycles. Any object used by multiple teams (e.g., `Account`, `Contact`, `Opportunity`, or a shared case object) may be approaching the 500 custom field ceiling. An audit of the top 10 most-modified objects by field count is needed alongside the object count review.

### Recommended Approach

1. Count custom objects with a Tooling API `EntityDefinition` query (the REST limits resource has no custom-object key, 264 L7923–8222), not from a manual Setup count.
2. Audit object usage: query `EntityDefinition` or use the Tooling API to retrieve objects with zero active records and no active Apex, Flow, or integration references. Candidate objects for deletion are those that have been unused for more than 12 months.
3. Establish a governance policy: new custom objects above a threshold (e.g., 750 objects) require an Architecture Review Board (ARB) approval.
4. For the CRM Analytics staging objects: evaluate whether Big Objects (which have a separate allocation — UNVERIFIED (2026-10-20): the big-object allocation is not in the corpus) or External Objects (for data virtualised from an external lake) can serve the staging use case without consuming the 800-object pool.
5. Set an alerting threshold at 750 objects (93.75% of limit) to trigger a mandatory audit before any new object is approved.

---

## Example 3: Platform Event Throughput Bottleneck in a Real-Time Integration

### Scenario

An order management integration publishes a Salesforce Platform Event (`Order_Update__e`) every time an order status changes in an external ERP. During business hours, the ERP processes roughly 5 orders per second, peaking at 8 orders per second during end-of-quarter surges. The development team proposes a 1:1 event-per-order design.

### Limit Risks Identified

**Publishing vs. delivery allocations.** Publishing is metered per rolling hour: 5 events per second is 18,000 an hour and the 8-per-second surge 28,800, far inside the 250,000-per-hour Enterprise/Unlimited publishing allocation (Platform Events Developer Guide 264 L7141). Delivery is the tighter one, but only for external subscribers: 5 × 3,600 × 8 = 144,000 events per business day delivered to one Pub/Sub API or CometD client is almost six times the 25,000 Enterprise (50,000 Unlimited) 24-hour delivery allocation (L7071), and each extra external client adds its own count (L7047–7049). If the only subscriber is an Apex trigger, deliveries do not count against the allocation at all (L7039–7041).

**Subscriber trigger governor limits.** The Apex trigger subscribing to `Order_Update__e` fires for each batch of events and gets the synchronous limits (100 SOQL, 150 DML), even though it runs asynchronously (Platform Events Developer Guide 264 L2339). If the subscriber performs one SOQL per event to look up a related Account and one DML to update an Order record, and events arrive in batches of 50, the trigger consumes 50 SOQL + 50 DML per invocation — within limits. But a platform event trigger batch can hold up to 2,000 events (L3098–3099), so under throughput pressure the per-event query fails at the 101st event. Ensure the subscriber trigger is bulkified to process events as a collection, not individually.

### Recommended Approach

1. Move to an aggregated event model: instead of one event per order change, publish one event per order batch summary every 30 seconds. This reduces event volume by 2–3 orders of magnitude.
2. Alternatively, evaluate Change Data Capture (CDC) on the Order object as a pull-based alternative to push events for downstream Salesforce subscribers.
3. Ensure the subscriber Apex trigger is fully bulkified — all SOQL outside loops, all DML on collections.
4. Monitor `HourlyPublishedPlatformEvents` and `DailyDeliveredPlatformEvents` in the REST limits resource during peak periods (REST API Developer Guide 264 L8030, L8047).
5. For sustained high-throughput external delivery, engage Salesforce about the platform event add-on: each add-on adds 100,000 deliveries per day and 25,000 publishes per hour (Platform Events Developer Guide 264 L7231–7233).
