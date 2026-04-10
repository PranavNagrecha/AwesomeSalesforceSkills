# Examples — Product Catalog Migration CPQ

## Example 1: Migrating Product Bundles with Options Using the Two-Pass Insert Strategy

**Context:** A CPQ org contains 120 product bundles. Each bundle is a Product2 record. Several products appear both as a bundle parent (in SBQQ__ConfiguredSKU__c on ProductOption) and as an option product inside a different bundle (in SBQQ__Product__c on ProductOption). The migration target is a sandbox refreshed from production with no CPQ catalog data.

**Problem:** A practitioner attempts to load Product2 records and ProductOption records in a single Bulk API 2.0 job, ordering rows so that parent products come before child products. The job fails with FK errors on ProductOption rows because Bulk API processes records in configurable-size batches, not row-by-row in sequence. Products earlier in the file are not guaranteed to be committed to the database before later rows in the same batch attempt to reference them. Additionally, several ProductOption rows reference a product that is both a bundle and an option — that product's ProductOption rows cannot be inserted until all Product2 records exist.

**Solution:**

```
# Wave 2a — INSERT all Product2 records first (no ProductOption in this file)
# File: wave2a_product2.csv
Id,Name,ProductCode,IsActive,SBQQ__SubscriptionType__c,...
(no SBQQ__UpgradeTarget__c — leave blank if self-referencing)

# Bulk API 2.0 job completes. Capture new Ids via query:
SELECT Id, Migration_ExternalId__c FROM Product2 WHERE Migration_ExternalId__c != null

# Wave 2b — UPDATE Product2 self-referencing fields (e.g., UpgradeTarget)
# File: wave2b_product2_selfref_update.csv
Id,SBQQ__UpgradeTarget__c
<new target Id of product>,<new target Id of upgrade target product>

# Wave 4a — INSERT ProductOption after ALL Product2 records are confirmed
# File: wave4a_product_option.csv
# Use relationship notation for FK resolution:
SBQQ__ConfiguredSKU__r.Migration_ExternalId__c,SBQQ__Product__r.Migration_ExternalId__c,SBQQ__Number__c,SBQQ__Quantity__c,...
EXT-BUNDLE-001,EXT-OPTION-042,10,1,...
```

**Why it works:** Separating Product2 and ProductOption into distinct Bulk API jobs guarantees all Product2 records are committed and queryable before any ProductOption row attempts FK resolution. Relationship notation (`__r.Migration_ExternalId__c`) delegates FK resolution to the platform at upsert time, eliminating manual ID mapping.

---

## Example 2: Discovering Silent FK Failure on PriceAction During Quote Calculation

**Context:** A practitioner migrates 45 PriceRule records and 180 PriceAction records from a production org to a new sandbox for UAT. All inserts succeed with zero errors reported by Bulk API 2.0. During UAT, a tester configures a bundle quote and notices that volume discount pricing is not applying correctly — line prices are at list price despite the bundle having an active volume pricing rule in production.

**Problem:** During the PriceAction load, 12 PriceAction records had their `SBQQ__PriceRule__c` FK unresolved. The source export file contained the source org's Salesforce ID for the parent PriceRule, but no external ID mapping was configured on SBQQ__PriceRule__c. The Bulk API job inserted the PriceAction records with a null SBQQ__PriceRule__c value. The platform accepted the insert because the managed-package FK constraint is not enforced at the DML layer. The CPQ pricing engine silently ignores PriceActions with a null parent rule — they exist in the database but never fire.

**Detection and Resolution:**

```soql
-- Run this SOQL in Developer Console after Wave 4 loads, before re-enabling CPQ triggers
SELECT Id, Name, SBQQ__PriceRule__c, SBQQ__Type__c, SBQQ__Value__c
FROM SBQQ__PriceAction__c
WHERE SBQQ__PriceRule__c = null
ORDER BY Name
```

If this query returns rows, the PriceRule load did not fully resolve. Steps:
1. Identify which PriceRule external IDs are missing from the target using a comparison query.
2. Re-run the PriceRule upsert for the missing records.
3. Re-run the PriceAction upsert with corrected relationship notation: `SBQQ__PriceRule__r.Migration_ExternalId__c`.
4. Re-run the orphan detection query until it returns zero rows.
5. Only then re-enable CPQ triggers.

**Why it works:** The orphan detection query exposes the silent failure that Bulk API success responses hide. Running it as a mandatory post-wave gate — before trigger re-enable — catches the problem in a controlled migration state rather than during live UAT or production cutover.

---

## Anti-Pattern: Loading ProductOption in the Same Wave as Product2

**What practitioners do:** To save time, practitioners combine Product2 and ProductOption records into a single Bulk API 2.0 job, ordering the CSV so Product2 rows appear first. They assume row order within a file determines insert order.

**What goes wrong:** Bulk API 2.0 splits records into batches of up to 10,000 rows each. Batch boundaries can fall mid-file. A ProductOption row in Batch 2 may attempt to resolve its FK to a Product2 record that was in Batch 1 but not yet committed when Batch 2 starts processing. The result is sporadic FK errors that vary by file size and batch configuration — making the failure non-deterministic and hard to reproduce.

**Correct approach:** Always load Product2 in a separate completed job (Wave 2) and confirm all records are queryable in the target before starting the ProductOption job (Wave 4). Use `SELECT COUNT() FROM Product2 WHERE Migration_ExternalId__c != null` to verify row count matches source before proceeding.
