# Commerce Inventory Data — Work Template

Use this template when designing or implementing OCI inventory management for a Salesforce Commerce org.

## Scope

- Inventory update mechanism: [ ] Nightly IMPEX  [ ] Real-time API (batchInventoryUpdate)  [ ] Both
- Commerce store type: [ ] B2B Commerce  [ ] B2C Commerce
- Total SKU count: ___________
- Number of warehouse locations: ___________

---

## Location Hierarchy Design

| Physical Warehouse | OCI Location ID | Location Group | Commerce Store |
|---|---|---|---|
| | | | |
| | | | |

---

## Data Path Selection

| Update Type | API / Method | Frequency | Notes |
|---|---|---|---|
| Nightly inventory snapshot | IMPEX Full Import | Nightly | Min 1 hour spacing between runs |
| Real-time restock event | batchInventoryUpdate (≤100 SKUs/call) | Event-driven | |
| Order fulfillment decrement | OCI reservation fulfillment action | Per order | |
| Checkout reservation | OCI reservation create | Per checkout session | |

---

## IMPEX File Specification

- Format: CSV, UTF-8
- Compression: gzip (required for files > 100 MB; recommended always)
- Key columns: `locationIdentifier`, `skuId`, `onHandQuantity`, `safetyStockCount`
- Full vs. Incremental: [ ] Full (replace all)  [ ] Incremental (delta only)
- Minimum spacing between full runs: ≥ 1 hour

---

## batchInventoryUpdate Batching Plan

- SKU batch size: ≤100 per call
- Total SKUs per event: ___________
- Calls per event: ___________ (ceil(totalSKUs / 100))
- Retry logic: [ ] Exponential backoff  [ ] Fixed delay

---

## Validation SOQL and API Checks

```
-- OCI Availability API query for sample SKUs
GET /services/data/v{version}/commerce/oci/availability

-- IMPEX job status poll
GET /services/data/v{version}/commerce/oci/impex/imports/{jobId}

-- Reservation status
GET /services/data/v{version}/commerce/oci/reservation/actions/reservations/{reservationId}
```

---

## Monitoring Runbook

- IMPEX job status: Poll after each upload; alert on failure status
- batchInventoryUpdate errors: Log per-call failures; retry on 429/503
- Nightly reconciliation: Compare OCI availability API to WMS snapshot for 100 sample SKUs

---

## Notes

_Capture org-specific location IDs, scheduling decisions, and open questions._
