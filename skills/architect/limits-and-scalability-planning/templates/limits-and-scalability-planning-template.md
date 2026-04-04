# Limits and Scalability Planning Template

Use this template to document governor limit exposure and scalability risk for a Salesforce org build, release, or health check engagement. Fill in all sections before completing a design review or pre-release sign-off.

---

## 1. Scope and Context

| Field | Value |
|---|---|
| Org Edition | _Enterprise / Unlimited / Developer_ |
| Review Type | _New Build / Pre-Release Audit / Production Incident / Health Check_ |
| Key Objects in Scope | _List the primary sObjects this review covers_ |
| Review Date | _YYYY-MM-DD_ |
| Reviewed By | _Name / Role_ |

---

## 2. Governor Limit Inventory — Synchronous Transactions

For each significant synchronous transaction type (user action, trigger path, API callout handler), complete one row. Add rows as needed.

| Transaction Name | Description | Est. SOQL Queries | Est. DML Statements | Est. DML Rows | Est. CPU (ms) | Est. Heap (MB) | Callouts | Risk Rating |
|---|---|---|---|---|---|---|---|---|
| _e.g. Account Save Trigger Path_ | _On account insert: validation + rollup_ | _12_ | _3_ | _50_ | _1,200_ | _0.5_ | _0_ | _Low_ |
| | | | | | | | | |
| | | | | | | | | |

**Reference limits (synchronous):**
- SOQL: 100 per transaction (shared with managed packages)
- DML statements: 150 per transaction
- DML rows: 10,000 per transaction
- CPU time: 10,000ms
- Heap: 6MB
- Callouts: 100 per transaction; 120s total timeout

**Risk Rating Key:** Low (<50% of any limit) | Medium (50–70%) | High (70–90%) | Critical (>90%)

---

## 3. Governor Limit Inventory — Asynchronous Transactions

For each Queueable, Future method, or Scheduled Apex, complete one row.

| Job / Method Name | Type | Est. SOQL Queries | Est. DML Statements | Est. DML Rows | Est. CPU (ms) | Est. Heap (MB) | Risk Rating |
|---|---|---|---|---|---|---|---|
| _e.g. OrderSyncQueueable_ | _Queueable_ | _45_ | _20_ | _1,000_ | _8,000_ | _3_ | _Low_ |
| | | | | | | | |
| | | | | | | | |

**Reference limits (async — Queueable, Future, Scheduled):**
- SOQL: 100 per transaction
- DML statements: 150 per transaction
- DML rows: 10,000 per transaction
- CPU time: 60,000ms
- Heap: 12MB

---

## 4. Batch Apex Job Inventory

For each Batch Apex job in the org, complete one row.

| Job Class Name | Purpose | Scope Size | Est. Records/Run | Frequency | Est. 24hr Record Volume | Queue Priority | Risk Rating |
|---|---|---|---|---|---|---|---|
| _e.g. AccountClassificationBatch_ | _Populate Industry_Segment__c_ | _200_ | _10,000,000_ | _One-time_ | _10,000,000_ | _High_ | _High_ |
| | | | | | | | |
| | | | | | | | |

**Reference limits (Batch Apex):**
- Max scope size: 2,000 records (recommended: 200)
- Max records processed per 24-hour rolling window: 50,000,000
- Max concurrent/queued jobs: 5 (Flex Queue: 100 in Holding state)
- CPU per execute() call: 60,000ms; Heap: 12MB

**24-hour rolling window total (all jobs):** _Sum of est. 24hr record volumes above_
**Headroom against 50M limit:** _50,000,000 − total = remaining_

---

## 5. Org-Wide Metadata Limit Headroom

| Metadata Type | Current Count | Limit | Used % | Headroom | Risk Rating |
|---|---|---|---|---|---|
| Custom Objects | | 800 | | | |
| Custom Fields — Account | | 500 | | | |
| Custom Fields — Contact | | 500 | | | |
| Custom Fields — Opportunity | | 500 | | | |
| Custom Fields — _[Object]_ | | 500 | | | |
| Active Flows | | 4,000 | | | |
| Custom Tabs | | 25 | | | |
| Apex Classes | | 5,000 | | | |
| Apex Triggers | | 5,000 | | | |

**Source:** Use `GET /services/data/v59.0/limits` (Salesforce Limits API) for authoritative current counts. Setup UI counts may lag.

**Soft-deleted fields note:** Custom fields pending deletion are still counted against the 500 limit for up to 15 days. Hard-delete from Setup > Deleted Fields to reclaim immediately.

---

## 6. Data Volume Projections

| Object | Current Record Count | Projected Count (1 yr) | Projected Count (3 yr) | Selectivity Risk? | Skinny Table Candidate? | Data Skew Risk? |
|---|---|---|---|---|---|---|
| _Account_ | | | | _Yes / No_ | _Yes / No_ | _Yes / No_ |
| _Contact_ | | | | | | |
| _Opportunity_ | | | | | | |
| _[Custom Object]_ | | | | | | |

**Selectivity threshold reminder:**
- Objects < 333K records: query result must be < 10% of total, or < 33,333 records.
- Objects > 1M records: query result must be < 333K records or < 10% — whichever is smaller.

**Skinny table trigger:** Recommend Salesforce support case for skinny table when an object is projected to exceed 5M records AND is queried frequently on non-ID fields.

**Data skew trigger:** Flag when a single owner holds > 10,000 records on a private-sharing object.

---

## 7. Async Strategy Summary

Document the async offload decisions for operations that cannot safely run in synchronous context.

| Operation | Current Layer | Proposed Async Layer | Reason for Offload | Dependency / Chaining Risk |
|---|---|---|---|---|
| _e.g. Send order confirmation email_ | _Synchronous trigger_ | _@future_ | _Email sends do not need to block record save_ | _None — fire and forget_ |
| | | | | |
| | | | | |

**Async layer selection guide:**
- `@future`: simple one-shot async with callout or non-user-facing logic; cannot chain to another `@future`
- Queueable: chainable async with state; supports callouts; preferred over `@future` for new development
- Batch Apex: bulk data processing > 10,000 records; fresh governor limit per execute() call
- Scheduled Apex: time-based recurring jobs; can enqueue Batch or Queueable

---

## 8. Platform Event Throughput Assessment

| Event Name | Publisher | Estimated Events/Hour | Estimated Events/24hr | % of 250K Limit | Risk Rating |
|---|---|---|---|---|---|
| _e.g. Order_Update__e_ | _ERP Integration_ | _2,000_ | _48,000_ | _19%_ | _Low_ |
| | | | | | |
| | | | | | |

**Combined 24hr event total (all events):** _Sum of estimated Events/24hr above_
**Headroom against 250,000 standard limit:** _250,000 − total = remaining_

**Subscriber bulkification check:** Confirm that all Apex triggers subscribing to each event process the event list as a collection (not record-by-record in a loop). Each trigger invocation receives a batch of up to 2,000 events.

---

## 9. Storage Capacity Projection

| Storage Type | Current Usage | Allocated | Used % | Projected Usage (1 yr) | Archival Strategy |
|---|---|---|---|---|---|
| Data Storage | | | | | |
| File Storage | | | | | |

**Allocation reference (Enterprise):**
- Data: 1GB base + 20MB per user license
- File: 1GB base + 2GB per user license

**Source:** Setup > Storage Usage for current values.

**Archival options:**
- Big Objects: write-once cold storage, async SOQL only, no DML limit
- Data Export + Deletion: scheduled CSV export followed by bulk delete
- External archive: move to external system and delete Salesforce records

---

## 10. Risk Summary and Recommendations

| Category | Risk Level | Key Finding | Recommended Action | Owner | Target Date |
|---|---|---|---|---|---|
| Synchronous governor limits | _Low / Medium / High / Critical_ | | | | |
| Async governor limits | | | | | |
| Batch Apex queue / throughput | | | | | |
| Org metadata headroom | | | | | |
| Data volume / query selectivity | | | | | |
| Platform event throughput | | | | | |
| Storage capacity | | | | | |

**Overall scalability posture:** _Low Risk / Manageable Risk / Action Required / Immediate Action Required_

---

## 11. Sign-Off

| Role | Name | Approved | Date |
|---|---|---|---|
| Architect | | _Yes / No_ | |
| Lead Developer | | _Yes / No_ | |
| Release Manager | | _Yes / No_ | |

**Notes / Escalations:**

_Record any items that require escalation to Salesforce Support (skinny table requests, High-Volume Platform Events add-on, storage increase requests)._
