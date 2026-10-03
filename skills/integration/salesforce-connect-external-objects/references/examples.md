# Examples - Salesforce Connect External Objects

## Example 1: ERP Order Status Without Replication

**Context:** Sales users need current order shipment status from ERP while working in Salesforce.

**Problem:** A nightly ETL copy would already be stale.

**Solution:** Expose the ERP order table through Salesforce Connect as an External Object and place the relevant fields on order-related record pages for lookup and decision support. Keep the queries inside what external objects support:

```sql
-- Supported: filter, sort, limit
SELECT ExternalId, Status__c, Amount__c
FROM SalesOrder__x
WHERE CustomerNumber__c = 'C-1001' AND Status__c = 'Open'
ORDER BY Amount__c DESC
LIMIT 50

-- Supported only with Request Row Counts enabled on the data source (OData)
SELECT COUNT() FROM SalesOrder__x WHERE Status__c = 'Open'

-- Not supported on external objects: aggregates other than COUNT(), LIKE, WITH
-- SELECT SUM(Amount__c) FROM SalesOrder__x GROUP BY Status__c
-- SELECT Id FROM SalesOrder__x WHERE Status__c LIKE 'Op%'
```

Deployable data source, object, Apex, and test files are in [`metadata-examples.md`](metadata-examples.md).

**Why it works:** The source system remains authoritative and users see current data without a full replication pipeline.

---

## Example 2: Hybrid Model For Hot Subset Data

**Context:** A support team needs live contract details from an external billing system, but also needs native reporting on renewal risk.

**Problem:** Pure virtualization cannot satisfy every reporting and automation need.

**Solution:** Keep the full contract catalog external, but replicate only the narrow summary fields needed for internal workflow and reporting.

**Why it works:** The design avoids copying everything while still meeting native-platform needs where they are real.

---

## Anti-Pattern: Treating `__x` Like Native `__c`

**What practitioners do:** They design pages, triggers, and reports as if external objects have the same behavior and latency profile as local data.

**What goes wrong:** Performance, reporting, and automation expectations all break late in the project.

**Correct approach:** Validate which features truly work for the use case before committing to virtualization. The two most common breaks are triggers (not available on external objects) and plain DML:

```apex
// Wrong: Apex cannot run standard insert on an external object
// insert new SalesOrder__x(Status__c = 'Submitted');

// Right: queue the write and keep the locator for monitoring
Database.SaveResult sr = Database.insertAsync(new SalesOrder__x(Status__c = 'Submitted'));
String locator = Database.getAsyncLocator(sr);
```
