# Examples — limits-and-scalability-planning

## Example 1: Mass Update Across 10 Million Account Records

### Scenario

A financial services org has 10 million Account records accumulated over 12 years. The business needs to retroactively populate a new custom field (`Industry_Segment__c`) on all accounts based on a classification rule applied to the existing `Industry` and `AnnualRevenue` fields. The team's first proposal is a one-time data load using Data Loader.

### Limit Risks Identified

**Batch Apex 50M record/24hr ceiling.** A full pass over 10 million accounts requires 10 million DML rows. The 50 million record/24-hour Batch Apex limit sounds large, but if this same org runs nightly sync jobs processing millions of records, the rolling 24-hour window may already be partially consumed. Check current batch consumption before submitting the classification job.

**Batch scope size vs. heap.** If the classification formula in Apex loads related Contact or Opportunity records to inform the decision, each account's "object graph" in memory grows. At 200 records per scope (the standard default), Apex holds 200 accounts plus their related records in heap simultaneously. A 12MB async heap limit at scope 200 means roughly 60KB of in-memory object data per account before overflow. Complex graphs require reducing scope to 50 or 100.

**Data skew and sharing recalculation.** The org uses a private sharing model on Account. The integration user that originally imported these accounts owns 9.8 million of them. The classification job will not change ownership, but if the org's sharing rules are based on field values (e.g., a criteria-based sharing rule on `Industry_Segment__c`), then populating the new field triggers sharing recalculation for every affected record. At 10 million records with a single-owner skew, recalculation may lock the Account object for hours.

**SOQL selectivity on large objects.** Any query in the batch `start()` method that filters Accounts without an indexed WHERE clause runs a full table scan on 10 million records. Use the Account `Id` in ORDER BY, and if filtering by `Industry`, confirm that field is indexed. A non-selective `start()` query will time out before the batch even begins.

### Recommended Approach

1. Use Batch Apex with a `Database.QueryLocator` in `start()` using a selective filter (e.g., `WHERE Industry_Segment__c = null` — null checks on non-indexed fields are not selective; add a date-based indexed filter or process all records using ORDER BY Id).
2. Set scope to 100 to control heap if related records are being loaded, or 200 if the classification is field-only and no related SOQL is required in `execute()`.
3. Disable criteria-based sharing rules on Account temporarily during the bulk operation (requires Salesforce support or a Custom Setting bypass flag in the sharing rule criteria) if sharing recalculation volume is a confirmed risk.
4. Schedule the batch job during off-peak hours to avoid competing for the 5-job queue limit with other nightly jobs.
5. Confirm 24-hour batch record consumption headroom before scheduling.

---

## Example 2: Org Approaching the 800 Custom Object Limit

### Scenario

An Enterprise Edition org has grown organically over 9 years through multiple project teams building domain-specific data models. A pre-release audit reveals the org has 763 custom objects — 95% of the 800-object Enterprise Edition limit. A new CRM Analytics project wants to add 25 more custom objects for staging data. Approving the request would bring the org to 788 objects, leaving only 12 in reserve for future work.

### Limit Risks Identified

**No safety buffer for emergency objects.** Custom objects are created during incidents (temporary staging, manual data repair tables) and during feature development that is partially complete. At 788 objects, a critical deployment requiring 13 new objects would fail at the org limit before the work is complete.

**Managed package objects count toward the limit.** Many teams overlook that installed managed packages contribute to the org's custom object count. If a newly installed package adds 20 objects, the org could hit 800 without any internal development activity. Verify the current count using the Limits API: `GET /services/data/v59.0/limits` returns `CustomTabsUsed` and `CustomObjectsUsed` among others. Confirm managed vs. unmanaged object counts separately via Setup > Object Manager.

**Field limits on heavily used objects.** With 763 objects in the org, the probability is high that at least some objects have accumulated fields from multiple project cycles. Any object used by multiple teams (e.g., `Account`, `Contact`, `Opportunity`, or a shared case object) may be approaching the 500 custom field ceiling. An audit of the top 10 most-modified objects by field count is needed alongside the object count review.

### Recommended Approach

1. Run `GET /services/data/v59.0/limits` in the org to get the authoritative current count from the Salesforce Limits API, not from a manual Setup count.
2. Audit object usage: query `EntityDefinition` or use the Tooling API to retrieve objects with zero active records and no active Apex, Flow, or integration references. Candidate objects for deletion are those that have been unused for more than 12 months.
3. Establish a governance policy: new custom objects above a threshold (e.g., 750 objects) require an Architecture Review Board (ARB) approval.
4. For the CRM Analytics staging objects: evaluate whether Big Objects (which have a separate, higher limit) or External Objects (for data virtualised from an external lake) can serve the staging use case without consuming the 800-object pool.
5. Set an alerting threshold at 750 objects (93.75% of limit) to trigger a mandatory audit before any new object is approved.

---

## Example 3: Platform Event Throughput Bottleneck in a Real-Time Integration

### Scenario

An order management integration publishes a Salesforce Platform Event (`Order_Update__e`) every time an order status changes in an external ERP. During business hours, the ERP processes roughly 5 orders per second, peaking at 8 orders per second during end-of-quarter surges. The development team proposes a 1:1 event-per-order design.

### Limit Risks Identified

**24-hour delivery ceiling.** At 5 events per second sustained across an 8-hour business day, the integration emits 5 × 3,600 × 8 = 144,000 events per business day. This is within the 250,000/24hr standard limit. However, the end-of-quarter surge at 8 events/second over 8 hours produces 230,400 events — also within limit but approaching it. If the ERP runs weekend catch-up batches that add another 50,000 events in a 24-hour window, the combined total exceeds the 250,000 ceiling.

**Subscriber trigger governor limits.** The Apex trigger subscribing to `Order_Update__e` fires for each batch of events. Each invocation shares the same async governor limits (100 SOQL, 150 DML). If the subscriber performs one SOQL per event to look up a related Account and one DML to update an Order record, and events arrive in batches of 50, the trigger consumes 50 SOQL + 50 DML per invocation — well within limits. But if event batches grow to 200 (which can happen under throughput pressure), the trigger hits 200 SOQL and fails. Ensure the subscriber trigger is bulkified to process events as a collection, not individually.

### Recommended Approach

1. Move to an aggregated event model: instead of one event per order change, publish one event per order batch summary every 30 seconds. This reduces event volume by 2–3 orders of magnitude.
2. Alternatively, evaluate Change Data Capture (CDC) on the Order object as a pull-based alternative to push events for downstream Salesforce subscribers.
3. Ensure the subscriber Apex trigger is fully bulkified — all SOQL outside loops, all DML on collections.
4. Monitor delivery metrics in Setup > Platform Events > Event Monitoring during peak periods.
5. For sustained high-throughput requirements, engage Salesforce to discuss the High-Volume Platform Event add-on (500,000 deliveries/24hr).
