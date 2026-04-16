---
name: commerce-inventory-data
description: "Use when managing inventory data in Salesforce Omnichannel Inventory (OCI) — covers stock level APIs, warehouse location mapping, IMPEX bulk upload, inventory availability queries, reservation management, and reorder point design. NOT for Field Service Lightning inventory management, Salesforce standard Product object stock fields, or CPQ product configuration."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "How do I bulk upload inventory stock levels to Salesforce OCI using IMPEX?"
  - "OCI batchInventoryUpdate API limit for SKUs per call in Omnichannel Inventory"
  - "Inventory availability not reflecting correctly in B2B Commerce storefront"
  - "How to map warehouse locations to OCI location groups for Commerce inventory sync"
  - "IMPEX full import causing data corruption when run too frequently in OCI"
tags:
  - OCI
  - omnichannel-inventory
  - inventory-management
  - IMPEX
  - stock-levels
  - commerce
inputs:
  - "Warehouse or location structure: location groups, location IDs, SKU identifiers"
  - "Inventory update frequency: real-time API vs. bulk IMPEX cadence"
  - "Commerce store and catalog context for availability display"
outputs:
  - "OCI API integration design: batchInventoryUpdate vs. IMPEX selection guidance"
  - "IMPEX import specification with file format and scheduling constraints"
  - "Inventory availability query pattern for storefront display"
  - "Reservation and fulfillment flow design"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Commerce Inventory Data

This skill activates when a practitioner needs to manage inventory data in Salesforce Omnichannel Inventory (OCI) — the cloud-native inventory management layer for Commerce Cloud. It covers the two primary data paths (real-time API updates and bulk IMPEX imports), the critical throughput limits on each, and the scheduling constraints that prevent data corruption when running full IMPEX imports in close succession.

---

## Before Starting

Gather this context before working on anything in this domain:

- OCI (Omnichannel Inventory) is the Salesforce inventory management platform that provides real-time availability APIs, reservation management, and bulk import via IMPEX. It is distinct from FSL (Field Service Lightning) inventory management.
- `batchInventoryUpdate` REST endpoint: maximum 100 SKUs per API call. Higher volume updates require batching.
- IMPEX bulk uploads: files over 100 MB must be gzip-compressed. Full IMPEX imports have a required spacing interval between runs to prevent data corruption — do not schedule back-to-back full imports.
- OCI exposes inventory at the Location Group level, not at the individual warehouse level, for availability display in Commerce storefronts.

---

## Core Concepts

### OCI Location Hierarchy

OCI organizes inventory into a two-level location hierarchy:

- **Locations** — Physical warehouses, stores, or distribution centers. Each has a unique Location Identifier.
- **Location Groups** — Logical groupings of Locations used for availability display. A Commerce store is associated with a Location Group, and available inventory is calculated as the aggregate across all Locations in the group.

When mapping from a WMS (warehouse management system) to OCI, each physical location maps to an OCI Location. Location Groups define the inventory pool visible to each storefront.

### Two Data Paths: API vs. IMPEX

**Real-Time API (batchInventoryUpdate):**
- REST endpoint: `POST /commerce/oci/availability-records`
- Processes up to 100 SKU-location pairs per call
- Use for real-time stock updates from POS, WMS webhooks, or order fulfillment events
- Responds synchronously with confirmation or error per SKU

**Bulk IMPEX:**
- Async file upload for large inventory snapshots
- Files must be UTF-8, CSV format, gzip-compressed for files over 100 MB
- Two types: **Full** (replace all inventory data) and **Incremental** (update specific SKU-location records)
- Full IMPEX runs must be spaced sufficiently apart — running full imports too close together can cause data corruption due to overlapping write operations on the inventory store
- Use for daily or nightly bulk sync from WMS systems

### Reservation Management

OCI supports inventory reservation for Commerce checkout:
- `POST /commerce/oci/reservation/actions/reservations` — Reserve inventory for a pending order
- `POST /commerce/oci/reservation/actions/fulfillments` — Confirm fulfillment and reduce on-hand count
- `POST /commerce/oci/reservation/actions/releases` — Release a reservation without fulfillment (e.g., order cancellation)

Reservations have an expiration time. Expired reservations are automatically released, returning inventory to the available pool.

---

## Common Patterns

### Pattern 1: Nightly Bulk Sync via IMPEX

**When to use:** WMS provides a nightly inventory snapshot for all SKUs and locations. Volume exceeds what real-time API can handle efficiently.

**How it works:**
1. WMS exports inventory snapshot as CSV (Location, SKU, OnHandQuantity, SafetyStockCount)
2. Compress file with gzip if > 100 MB
3. Upload to OCI IMPEX endpoint as a Full import job
4. Poll import job status until complete
5. Validate: query OCI availability API for a sample SKU set and compare to WMS source

**Why not real-time API for bulk:** `batchInventoryUpdate` at 100 SKUs per call would require thousands of API calls for a large catalog. IMPEX is designed for bulk inventory snapshots.

### Pattern 2: Real-Time Update for Order Fulfillment Events

**When to use:** An order is fulfilled in the WMS and stock count must be decremented immediately in OCI before the next page load.

**How it works:**
1. WMS sends webhook on fulfillment event
2. Integration layer calls `POST /commerce/oci/reservation/actions/fulfillments` with the reservation ID
3. OCI decrements on-hand count and closes the reservation
4. Storefront availability query reflects updated count within seconds

**Why not wait for nightly IMPEX:** Customers checking the storefront after a product sells out need accurate availability. Real-time reservation fulfillment keeps OCI synchronized with WMS without waiting for the next batch window.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Nightly full inventory sync | IMPEX Full import (gzip-compressed for > 100 MB) | Designed for bulk snapshots; handles large catalog efficiently |
| Real-time stock decrements < 100 SKUs | batchInventoryUpdate REST API | Synchronous; immediate confirmation |
| Real-time stock update > 100 SKUs | Batch into multiple batchInventoryUpdate calls | Hard limit of 100 SKUs per call |
| Order fulfillment stock decrement | OCI reservation fulfillment action | Closes reservation and decrements count atomically |
| IMPEX scheduling | Space full imports by at least 1 hour minimum | Back-to-back full imports risk data corruption |
| FSL technician inventory | Field Service Lightning inventory module | OCI is for Commerce inventory, not FSL field stock |

---

## Recommended Workflow

1. **Design location hierarchy** — Map physical warehouses to OCI Locations. Create Location Groups matching the inventory pool for each Commerce store. Document Location IDs and Location Group IDs.
2. **Select data path** — Decide between nightly IMPEX (for bulk snapshot sync) and real-time API (for event-driven updates). Many implementations use both: IMPEX for nightly reconciliation and API for real-time reservation/fulfillment.
3. **Design IMPEX file format** — Prepare the CSV schema for inventory records: Location Identifier, SKU, OnHandQuantity, SafetyStockCount. Confirm gzip compression is applied for large files.
4. **Configure IMPEX scheduling** — Schedule nightly full IMPEX with sufficient spacing from any other full imports. Document the minimum interval between runs in the operations runbook.
5. **Implement reservation flow** — For Commerce checkout, integrate the reservation API call into the order submission flow. Set reservation expiration time matching checkout session timeout.
6. **Validate inventory availability** — After each IMPEX or API update, query the OCI availability endpoint for a sample of SKUs and confirm values match the source system.
7. **Monitor for import errors** — Poll IMPEX job status endpoint after each upload. Log failures to an operations alert system — silent IMPEX failures cause stale inventory without any visible error in the storefront.

---

## Review Checklist

- [ ] Location Group hierarchy documented and mapped to Commerce stores
- [ ] batchInventoryUpdate calls batched at ≤100 SKUs per call
- [ ] IMPEX files gzip-compressed for files > 100 MB
- [ ] Full IMPEX runs scheduled with minimum spacing (no back-to-back full imports)
- [ ] Reservation, fulfillment, and release flows implemented for Commerce checkout
- [ ] IMPEX job status polling implemented — errors logged to operations alerts
- [ ] Availability API validation run after each import

---

## Salesforce-Specific Gotchas

1. **batchInventoryUpdate is capped at 100 SKUs per call** — Any call exceeding 100 SKU-location pairs is rejected. Integration code must batch updates into chunks of ≤100. This limit applies to the real-time API, not IMPEX.
2. **Full IMPEX imports must not run back-to-back** — Running full inventory imports in rapid succession (within minutes) risks overlapping write operations on the OCI inventory store, which can produce corrupted availability data. Salesforce documents that full imports require spacing between runs. Enforce a minimum interval in job scheduling.
3. **OCI exposes inventory at Location Group level, not individual Location level, to Commerce** — The Commerce storefront availability display aggregates inventory across all Locations in the associated Location Group. Individual warehouse stock levels are not surfaced to the buyer. Design reporting and ops dashboards at the Location level but configure storefront availability at the Location Group level.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Location hierarchy mapping | Physical warehouse to OCI Location and Location Group mapping document |
| IMPEX file specification | CSV column structure, compression requirements, and scheduling constraints |
| API integration design | batchInventoryUpdate call batching pattern and reservation/fulfillment flow |
| Monitoring runbook | IMPEX job status polling, error alerting, and nightly validation queries |

---

## Related Skills

- `admin/commerce-product-catalog` — For product catalog configuration and store availability settings
- `data/product-catalog-migration-commerce` — For initial product catalog migration into B2B Commerce
- `data/commerce-order-history-migration` — For order fulfillment data migration into Order Management
