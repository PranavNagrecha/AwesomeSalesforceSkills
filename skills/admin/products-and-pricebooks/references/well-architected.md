# Well-Architected Notes — Products and Pricebooks

## Reliability

**Referential integrity in the PricebookEntry model is a hard dependency chain.** Standard Pricebook entries must exist before custom Pricebook entries. Any automation, migration, or integration that creates PricebookEntry records must enforce this order explicitly — the platform will reject out-of-order inserts. Bulkified data loads should sort or partition creation by Pricebook type (Standard first, custom second).

**Deactivation over deletion.** Products that have ever been used on closed Opportunities, historical Quotes, or Orders should never be deleted. Deactivating `Product2.IsActive` is the only safe deprecation path. Build catalog management processes around a lifecycle model (Active → Deprecated/Inactive) rather than hard deletion, especially in orgs with reporting or compliance requirements for historical data.

**Custom Pricebooks that are still referenced by open Opportunities cannot be deleted.** Before any batch cleanup process attempts to remove legacy Pricebooks, run pre-flight queries to identify blocking records. Deactivating the Pricebook before deletion is an intermediate safe step.

## Operational Excellence

**Automate Pricebook assignment on Opportunities.** Requiring sales reps to manually select the correct Pricebook on each Opportunity introduces human error and inconsistent pricing. Use a Record-Triggered Flow or Process Builder equivalent to auto-assign `Opportunity.Pricebook2Id` based on deterministic business logic (e.g., Account record type, partner flag, or region field). This reduces support requests and prevents wrong-pricebook line items from slipping into reports.

**Bulk-manage PricebookEntry records with Data Loader or scripts for catalog changes.** For orgs with more than 20–30 products or more than two currencies, managing PricebookEntry records through the UI is error-prone and slow. Use CSV-based bulk loads with explicit `CurrencyIsoCode` and `Pricebook2Id` values. Maintain the source CSV as a versioned artifact in version control.

**Use product families consistently.** The `Product2.Family` field drives reporting, filtering, and record type assignment. Establish a controlled vocabulary for product family values before the catalog grows; retrofitting families after hundreds of products are created requires a bulk update.

## User Experience

**Empty product picker on Opportunities in non-USD currencies is the most common user-reported issue.** Train admins to immediately check PricebookEntry coverage by currency when a rep reports that no products appear. The platform gives no error message to the rep — the picker is simply empty. Proactive PricebookEntry completeness checks should be part of any multi-currency go-live checklist.

**Product Schedule installments should be validated against the financial reporting calendar.** Revenue installments that do not align to fiscal periods create reconciliation friction for the finance team. When configuring product default schedules, confirm the installment frequency matches the org's fiscal period settings.

---

## Official Sources Used

- Salesforce Help — Products and Pricebooks: https://help.salesforce.com/s/articleView?id=sf.products_landing_page.htm
- Salesforce Object Reference — PricebookEntry: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_pricebookentry.htm
- Salesforce Object Reference — Product2: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_product2.htm
- Salesforce Object Reference — Pricebook2: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_pricebook2.htm
- Salesforce Help — Enable and Configure Product Schedules: https://help.salesforce.com/s/articleView?id=sf.products_schedules_enable.htm
- Salesforce Help — Considerations for Multiple Currencies: https://help.salesforce.com/s/articleView?id=sf.currencies_multicurrency_considerations.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
