# Well-Architected Notes — Commerce Order History Migration

## Relevant Pillars

### Reliability

Order Management requires OrderSummary records to be correctly initialized via ConnectAPI. Any shortcut that bypasses this initialization produces silently broken records that appear valid in SOQL but fail in Order Management reports and actions. Reliability requires following the prescribed API path without exception.

### Operational Excellence

Setting `LifeCycleType = Unmanaged` for historical orders prevents agents from taking actions (refund, cancel, fulfillment) on historical data. This is both a business process control and a data integrity protection.

---

## WAF Mapping

| WAF Area | Guidance |
|---|---|
| Reliability | Use ConnectAPI exclusively for OrderSummary creation; validate with SOQL after each batch |
| Operational Excellence | Set LifeCycleType = Unmanaged for all historical orders; document which orders are Managed vs. Unmanaged |
| Security | Order financial data requires FLS on Amount fields; historical orders should be read-only for most profiles |
| Performance | ConnectAPI has per-transaction limits; use Batch Apex with chunks of ≤200 OrderSummary creations per execute() call |

---

## Cross-Skill References

- `data/product-catalog-migration-commerce` — For B2B Commerce product catalog migration
- `apex/commerce-order-api` — For Apex-level Order Management API patterns and ConnectAPI usage
- `devops/cpq-deployment-patterns` — For CPQ-specific order and billing configuration migration

---

## Official Sources Used

- Salesforce Order Management Developer Guide: Importing Order Data — https://developer.salesforce.com/docs/atlas.en-us.order_management_developer_guide.meta/order_management_developer_guide/order_management_import_data.htm
- Salesforce Help: Order Management Object Reference — https://help.salesforce.com/s/articleView?id=sf.om_object_reference.htm
- ConnectAPI OrderSummary Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_connectapi_order_summary.htm
