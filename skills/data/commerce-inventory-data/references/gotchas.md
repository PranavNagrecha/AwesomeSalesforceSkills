# Gotchas — Commerce Inventory Data

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: batchInventoryUpdate Is Capped at 100 SKUs Per Call

The `batchInventoryUpdate` endpoint (`POST /commerce/oci/availability-records`) accepts a maximum of 100 SKU-location pairs per API call. Exceeding this limit returns a 400 error. Integration code that does not enforce batching will fail silently in development (where SKU counts are low) but break in production (where restock events span hundreds of SKUs).

**Fix:** Always chunk SKU-location update payloads at ≤100 items before calling batchInventoryUpdate. Implement batch logic in the WMS integration middleware.

---

## Gotcha 2: Full IMPEX Imports Must Not Run Back-to-Back

Running two full OCI IMPEX imports in rapid succession (within minutes) causes overlapping write operations on the OCI inventory data store. Salesforce documents this risk in OCI Inventory IMPEX Best Practices: back-to-back full imports can corrupt availability data for specific SKUs, making sold-out products appear in-stock or available products appear sold-out.

**Fix:** Enforce a minimum spacing between full IMPEX runs. Monitor import job completion before scheduling the next run. For near-real-time updates, use the batchInventoryUpdate API rather than frequent full IMPEX.

---

## Gotcha 3: OCI Exposes Inventory at Location Group Level, Not Individual Warehouse Level

Commerce storefronts display product availability aggregated at the Location Group level — the sum of available inventory across all Locations in the group. Individual warehouse stock levels are not directly surfaced to buyers. This means a product may show "In Stock" even if only one of six warehouses has stock, because the Location Group aggregates across all.

**Fix:** Design Location Groups to match the fulfillment pool that is genuinely available to ship for each storefront. If a warehouse is too far to ship within SLA, do not include it in the Location Group for that store.

---

## Gotcha 4: Gzip Compression Is Required for IMPEX Files Over 100 MB

IMPEX file uploads over 100 MB must be gzip-compressed. Uploading an uncompressed file over 100 MB will fail. The OCI IMPEX documentation specifies this size threshold explicitly. Integration scripts that do not implement conditional gzip compression based on file size will work in development (small catalogs) but fail in production (large catalogs).

**Fix:** Always apply gzip compression to IMPEX files as a standard step in the export pipeline, regardless of file size. This simplifies the integration and ensures the upload path is always tested with compression active.

---

## Gotcha 5: Reservation Expiration Releases Inventory Back to Available Pool Without Notification

OCI reservations have a configurable expiration time. When a reservation expires (e.g., a customer abandons checkout), the reserved inventory is automatically returned to the available pool. If the Commerce storefront does not proactively handle expired reservations (e.g., by refreshing availability on checkout timeout), customers may see incorrect availability counts during the abandoned checkout window.

**Fix:** Set reservation expiration to match the Commerce checkout session timeout. Implement a checkout session timeout handler that explicitly releases the reservation via `POST /commerce/oci/reservation/actions/releases` before the session expires, rather than relying on automatic expiration.
