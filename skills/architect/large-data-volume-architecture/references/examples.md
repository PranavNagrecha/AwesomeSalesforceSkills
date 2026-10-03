# Examples — Large Data Volume Architecture

## Example 1: Custom object report timeouts with wide rows

**Context:** A B2B org stores five million rows on `Telemetry_Event__c` with eighty custom fields. Operational dashboards filter on `Event_Type__c` (picklist) and `Occurred_On__c` (date) but still time out.

**Problem:** The object is both wide and high-volume. Filters on the picklist alone may not be selective enough at five million rows; reporting also pays join cost between standard and custom field storage.

**Solution:**

1. Run aggregate SOQL to count rows per `Event_Type__c` and per day bucket for `Occurred_On__c`.
2. If combined filters still exceed custom index thresholds, request a **two-column custom index** on `Event_Type__c, Occurred_On__c` for the dashboard pattern.
3. If read paths need many scalar columns and filters are selective, open a **skinny table** discussion with Support using only supported field types (no formulas in the skinny column list).

**Why it works:** The LDV guide positions two-column indexes for exactly this list-and-sort pattern, and skinny tables remove join overhead once filters are under control.

---

## Example 2: Integration user owns four million rows

**Context:** A single `005` integration user owns all `Invoice__c` rows for downstream sync. Sharing rule recalculation spikes nightly.

**Problem:** Ownership skew concentrates sharing work on one user bucket, which the LDV guide calls out as a performance risk.

**Solution:**

- Introduce queue-owned or partitioned logical owners (region, brand, source system) so no identity holds more than the low tens of thousands of rows per object where possible.
- Narrow integration queries with selective filters instead of scanning the integration user’s visible set.
- For one-time replatforming, follow bulk-load sequencing: roles and users first, owners on records, then groups and rules, using **defer sharing calculation** only when administrators explicitly use that permissioned workflow.

**Why it works:** Redistributing ownership reduces recomputation fan-out; sequencing avoids repeated full sharing passes during loads.

---

## Anti-Pattern: Requesting a skinny table for formula-driven dashboards

**What practitioners do:** Ask Support for a skinny table that includes roll-up summary fields, rich text, or formulas used on dashboards.

**What goes wrong:** Skinny tables only include the scalar field types enumerated in the Large Data Volumes guide. Unsupported types cannot be placed in the skinny projection, so the case stalls or the dashboard still hits the main table for those columns.

**Correct approach:** Materialize only supported columns into the skinny request, or precompute needed values into indexed static fields via asynchronous processing, then report off those columns.

---

## Example 3: LDV Review Evidence and Decision Record for a 62-Million-Row Shipment Object

**Context:** A logistics company's `Shipment__c` object holds 62 million rows and grows by 1.5 million a month. One integration user owns 58 million of them. The dispatcher list view filters `Status__c = 'In Transit' AND Depot__c = :depot` and sorts by `ETA__c`. A nightly extract pulls every row changed in the last day. An "unassigned" report filters `Driver__c = null`. Reports time out and sharing recalculation after role changes takes most of a weekend.

**Evidence collection.** The commands use the REST API Developer Guide resources "Record Count" and "Get Feedback on Query Performance (Beta)" and the Salesforce CLI `data query` command:

```bash
# Cached row counts (snapshot; excludes Recycle Bin and archived rows; needs View Setup and Configuration)
curl -s "https://$MY_DOMAIN/services/data/v67.0/limits/recordCount?sObjects=Shipment__c" \
  -H "Authorization: Bearer $TOKEN"

# Selectivity of each filter value: one exact count per value, filtered rather than grouped
sf data query --target-org prod-readonly --result-format csv \
  --query "SELECT COUNT() FROM Shipment__c WHERE Status__c = 'In Transit'"
sf data query --target-org prod-readonly --result-format csv \
  --query "SELECT COUNT() FROM Shipment__c WHERE Status__c = 'In Transit' AND Depot__c = 'a0B5g00000XYZAbEAP'"

# Ask the optimizer which plan it would choose, without running the query (Beta)
curl -s -G "https://$MY_DOMAIN/services/data/v67.0/query/" \
  --data-urlencode "explain=SELECT Id FROM Shipment__c WHERE Status__c = 'In Transit' AND Depot__c = 'a0B5g00000XYZAbEAP' ORDER BY ETA__c" \
  -H "Authorization: Bearer $TOKEN" | jq '.plans[] | {leadingOperationType, relativeCost, cardinality, sobjectCardinality, notes}'
```

> UNVERIFIED (2026-10-03): `COUNT()` over tens of millions of rows can itself be slow or time out; if it does, count a representative date slice and extrapolate, and record that the figure is estimated.

**Threshold math for this object (LDV guide, "Standard and Custom Indexed Fields"):**

| Index type | Rule | Allowed matches at 62,000,000 rows |
|---|---|---|
| Custom | < 10% of first 1M + < 5% of remaining 61M | 100,000 + 3,050,000 = 3,150,000 |
| Standard | < 30% of first 1M + < 15% of remaining 61M | 300,000 + 9,150,000 = 9,450,000 |
| AND combination | indexes used unless one returns > 20% of rows | 12,400,000 per filter |

Measured: `Status__c = 'In Transit'` matches 1,900,000 rows (selective for a custom index); `Depot__c` alone matches up to 4,100,000 for the largest depot (not selective by itself).

**Decision record (machine-readable form):**

```yaml
adr: LDV-009
title: Shipment__c access paths, skew and retention
status: proposed
date: 2026-10-03
decisions:
  - id: D1
    change: two-column custom index on (Status__c, ETA__c) via Customer Support
    reason: list view selects by Status__c and sorts by ETA__c, the case the LDV guide describes for two-column indexes
  - id: D2
    change: replace Driver__c = null with Assignment_State__c = 'Unassigned' (picklist, indexed)
    reason: index tables omit nulls by default; LDV guide suggests a real value such as NA instead of null
  - id: D3
    change: reassign ownership to 14 regional queues; no owner above 10,000 rows per the LDV guide
    reason: one integration user owns 58M rows (ownership skew)
    load_plan: defer sharing calculation during the reassignment, group updates by Depot__c, run in the maintenance window
  - id: D4
    change: nightly extract moves to a Bulk API 2.0 query job filtered on SystemModstamp >= last run
    reason: result sets above one million rows; SystemModstamp carries a standard index
  - id: D5
    change: rows delivered more than 24 months ago move to big object Shipment_Archive__b, then Bulk API hard delete
    reason: retention purges above one million rows use hard delete; children (Shipment_Event__c) deleted first
    archive_index: [Depot_Code__c, Delivered_On__c, Shipment_Number__c]   # big object composite key
not_doing:
  - skinny table: list view columns still changing; every change would need a Support request, and testing would require a Full sandbox
  - divisions: object qualifies (>1M rows, >35 licences) but depots already partition the access path
verification:
  - rerun the explain call after D1 and D2; expect leadingOperationType Index with relativeCost below the TableScan plan
  - time the dispatcher list view and the unassigned report in the Full sandbox before and after
```

**Why it works:** every decision cites the threshold or rule it relies on, the evidence is re-runnable, the null filter is fixed at the data model rather than with a request Support may not grant, and the archive plan uses the hard-delete path the guide recommends for million-row purges.

