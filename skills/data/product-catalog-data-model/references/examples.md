# Examples — Product Catalog Data Model

## Example 1: Bulk Loading a Product Catalog with Standard and Custom Pricebooks via Data Loader

**Context:** A manufacturing company is migrating 3,000 products from a legacy ERP into Salesforce. They have one Standard Pricebook and two custom pricebooks — Wholesale and Retail. Some products have the same price in the Retail pricebook as the standard price; others have discounted wholesale prices.

**Problem:** A developer attempts to load all PricebookEntry rows (standard + both custom) in a single Data Loader job, sorted by product. The job fails for the custom entries because the Standard PBEs have not yet been committed when the custom PBE rows are processed within the same batch.

**Solution:**

Step 1 — Load Product2 records (no price columns):

```csv
Name,ProductCode,Description,Family,IsActive
Widget A,WGT-001,Standard Widget,Hardware,true
Widget B,WGT-002,Premium Widget,Hardware,true
Bearing Kit,BRG-050,Bearing Assembly,Components,true
```

Step 2 — Query the Standard Pricebook ID from the target org (never hardcode):

```sql
SELECT Id FROM Pricebook2 WHERE IsStandard = true LIMIT 1
-- Returns: 01s000000000001AAA (example only — always query your specific org)
```

Step 3 — Load Standard PricebookEntries in a separate job (UseStandardPrice is false/omitted):

```csv
Pricebook2Id,Product2Id,UnitPrice,IsActive
01s000000000001AAA,01t000000000001AAA,150.00,true
01s000000000001AAA,01t000000000002AAA,275.00,true
01s000000000001AAA,01t000000000003AAA,45.00,true
```

Step 4 — Load Wholesale PricebookEntries with explicit discounted prices (UseStandardPrice = false):

```csv
Pricebook2Id,Product2Id,UnitPrice,UseStandardPrice,IsActive
01s000000000002AAA,01t000000000001AAA,120.00,false,true
01s000000000002AAA,01t000000000002AAA,220.00,false,true
01s000000000002AAA,01t000000000003AAA,36.00,false,true
```

Step 5 — Load Retail PricebookEntries that inherit the standard price (UseStandardPrice = true, no UnitPrice column):

```csv
Pricebook2Id,Product2Id,UseStandardPrice,IsActive
01s000000000003AAA,01t000000000001AAA,true,true
01s000000000003AAA,01t000000000002AAA,true,true
01s000000000003AAA,01t000000000003AAA,true,true
```

**Why it works:** Running the Standard PBE load as a separate committed job guarantees the platform constraint is satisfied before any custom PBE row is processed. The Retail pricebook uses `UseStandardPrice = true` so price updates to the Standard PBE automatically flow through — no separate update job required when prices change.

---

## Example 2: Apex Code Correctly Handling the Standard Pricebook ID

**Context:** A developer is writing an Apex class to programmatically create Product2 and PricebookEntry records as part of a product provisioning flow.

**Problem:** The developer hardcodes the Standard Pricebook ID — this works in one org but breaks in every other org (sandbox refresh, production deployment, scratch org):

```apex
// WRONG — hardcoded Pricebook2 ID will fail in any org other than the original
PricebookEntry stdPbe = new PricebookEntry(
    Pricebook2Id = '01s000000000001AAA',  // hardcoded — breaks across orgs
    Product2Id   = newProduct.Id,
    UnitPrice    = 100.00,
    IsActive     = true
);
```

**Solution:** Query the Standard Pricebook ID at runtime in production code. Use `Test.getStandardPricebookId()` in tests.

Production Apex:

```apex
// Query once per transaction — do not issue per-record queries inside a loop
Id standardPbId = [SELECT Id FROM Pricebook2 WHERE IsStandard = true LIMIT 1].Id;

List<PricebookEntry> standardEntries = new List<PricebookEntry>();
for (Product2 p : newProducts) {
    standardEntries.add(new PricebookEntry(
        Pricebook2Id = standardPbId,
        Product2Id   = p.Id,
        UnitPrice    = 0.00,
        IsActive     = true
    ));
}
insert standardEntries; // Standard PBEs committed first

// Custom pricebook entries can only be inserted AFTER standard entries are committed
List<PricebookEntry> customEntries = new List<PricebookEntry>();
for (Product2 p : newProducts) {
    customEntries.add(new PricebookEntry(
        Pricebook2Id     = customPricebookId,
        Product2Id       = p.Id,
        UseStandardPrice = false,
        UnitPrice        = p.List_Price__c,
        IsActive         = true
    ));
}
insert customEntries;
```

Apex test:

```apex
@isTest
static void testProductProvisioning() {
    // Use the platform method — never SOQL-query Standard Pricebook in a test
    Id standardPbId = Test.getStandardPricebookId();

    Product2 prod = new Product2(Name = 'Test Widget', IsActive = true);
    insert prod;

    PricebookEntry stdPbe = new PricebookEntry(
        Pricebook2Id = standardPbId,
        Product2Id   = prod.Id,
        UnitPrice    = 100.00,
        IsActive     = true
    );
    insert stdPbe;
    // Standard PBE committed — now safe to insert custom pricebook entries
}
```

**Why it works:** `Test.getStandardPricebookId()` returns the correct Standard Pricebook ID in test context without requiring `SeeAllData = true`. Using it keeps tests isolated and prevents failures in CI environments where live data queries are blocked.

---

## Anti-Pattern: Loading Standard and Custom PricebookEntries in a Single Bulk API Job

**What practitioners do:** To simplify the load script, they include Standard PBE rows and custom PBE rows for the same product in a single CSV file and submit them as one Bulk API 2.0 job.

**What goes wrong:** Bulk API 2.0 does not guarantee that rows within a job are committed in the order they appear in the CSV. A custom PBE row may be processed before its corresponding Standard PBE row has been committed. The custom PBE insert fails with `FIELD_INTEGRITY_EXCEPTION: pricebook entry in standard price book required before this entry can be created`. This produces a partially loaded catalog with failures distributed unpredictably across the error results file.

**Correct approach:** Always use separate jobs — one job for Standard PBEs (verified to complete successfully), then a subsequent job for custom PBEs. In automated pipelines, implement a verification step between jobs that queries the expected Standard PBE count before launching the custom PBE job.
