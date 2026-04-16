# Examples — Commerce Inventory Data

## Example 1: batchInventoryUpdate Fails for Large SKU Count

**Scenario:** A retailer's WMS integration called `batchInventoryUpdate` with 250 SKU-location pairs in a single API request. The API returned 400 errors for every request exceeding 100 SKUs.

**Problem:** The `batchInventoryUpdate` REST endpoint enforces a hard limit of 100 SKU-location pairs per call. The integration was not batching requests.

**Solution:**
1. Chunk the SKU list into batches of ≤100 before calling the API
2. For 250 SKUs: send three calls (100 + 100 + 50)
3. Implement retry logic with exponential backoff for failed calls

**Why this works:** The 100 SKU limit is a per-call constraint, not a daily rate limit. Batching the input resolves the error.

---

## Example 2: Full IMPEX Import Scheduled Too Frequently — Data Corruption

**Scenario:** An operations team scheduled OCI full inventory IMPEX imports every 15 minutes. After two weeks, inventory data for certain SKUs became inconsistent — showing availability for sold-out products.

**Problem:** OCI full inventory imports have a required spacing interval between runs. Back-to-back full imports cause overlapping write operations on the inventory store, producing corrupted availability data. The OCI IMPEX Best Practices documentation explicitly warns against this pattern.

**Solution:**
1. Change the schedule to a nightly full IMPEX with minimum spacing (at least 1 hour between full runs)
2. Replace high-frequency IMPEX with `batchInventoryUpdate` API calls for real-time SKU changes
3. Implement IMPEX job status monitoring to confirm each import completes before scheduling the next

**Why this works:** Full IMPEX is designed for daily snapshots. Real-time changes should use the event-driven batchInventoryUpdate API.

---

## Example 3: OCI vs. FSL Inventory Confusion

**Scenario:** A field service organization asked whether to use Field Service Lightning inventory or Omnichannel Inventory for their B2B Commerce product availability display.

**Problem:** FSL inventory tracks parts and materials for field technician dispatch via separate objects (`WorkOrderLineItem`, `ServiceResource` inventory). OCI tracks product availability for Commerce storefronts. They are entirely separate systems.

**Solution:**
1. Use OCI for Commerce storefront product availability
2. Use FSL inventory for field technician parts management and work order fulfillment
3. If the same physical product exists in both systems, build an integration that syncs between FSL and OCI via `batchInventoryUpdate`

**Why this works:** OCI and FSL serve different business functions. They are not interchangeable and require separate configuration, data models, and APIs.
