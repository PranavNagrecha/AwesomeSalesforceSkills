# Well-Architected Notes — Commerce Inventory Data

## Relevant Pillars

### Reliability

Inventory availability accuracy is a direct customer experience reliability requirement. Overselling (showing in-stock for sold-out products) causes order fulfillment failures. OCI reliability requires: correctly spacing full IMPEX runs, batching batchInventoryUpdate at ≤100 SKUs, and monitoring import job status after every IMPEX upload.

### Operational Excellence

OCI inventory operations require a monitoring runbook: IMPEX job status polling after each upload, alerting on import failures, and nightly reconciliation between WMS and OCI availability API. Silent IMPEX failures cause stale inventory without any visible error in the storefront.

---

## WAF Mapping

| WAF Area | Guidance |
|---|---|
| Reliability | Monitor IMPEX job status; enforce spacing between full imports; batch API calls at ≤100 SKUs |
| Operational Excellence | Implement import status polling and alerting; nightly reconciliation between WMS and OCI |
| Performance | Full IMPEX for bulk sync; batchInventoryUpdate for real-time event-driven changes |
| Security | OCI APIs require OAuth 2.0 Connected App with commerce_data OAuth scope |

---

## Cross-Skill References

- `data/product-catalog-migration-commerce` — For initial product catalog migration into B2B Commerce
- `data/commerce-order-history-migration` — For order fulfillment and history data in Order Management
- `admin/commerce-product-catalog` — For product catalog configuration and store settings

---

## Official Sources Used

- Salesforce Omnichannel Inventory OCI Connect REST API Developer Guide — https://developer.salesforce.com/docs/commerce/omnichannel-inventory/guide/oci-api.html
- Salesforce Help — OCI Inventory IMPEX Best Practices — https://help.salesforce.com/s/articleView?id=sf.oci_impex_best_practices.htm
- Omnichannel Inventory REST API Reference — https://developer.salesforce.com/docs/commerce/omnichannel-inventory/references/oci-api-reference
