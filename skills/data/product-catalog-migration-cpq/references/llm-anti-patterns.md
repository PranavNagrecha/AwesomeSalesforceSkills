# LLM Anti-Patterns — Product Catalog Migration CPQ

Common mistakes AI coding assistants make when generating or advising on CPQ product catalog migrations. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Loading SBQQ Objects in Wrong Dependency Order

**What the LLM generates:** A migration plan that loads ProductOption and PriceAction in the same wave as Product2 and PriceRule, or that groups all SBQQ objects into a single Bulk API job ordered by "parent before child" row sequencing.

**Why it happens:** LLMs treat row ordering within a file as equivalent to commit ordering. They apply standard bulk load heuristics (parents before children, one file per object type) without accounting for CPQ's managed-package FK constraints, which require full wave completion — not just row ordering — before dependent objects can be loaded.

**Correct pattern:**

```
Wave 1: Pricebook2, SBQQ__DiscountCategory__c
Wave 2: Product2 (pass 1 — no self-refs), SBQQ__PriceRule__c
Wave 3: PricebookEntry, SBQQ__DiscountSchedule__c, SBQQ__DiscountTier__c
Wave 4: SBQQ__ProductOption__c, SBQQ__PriceAction__c
Wave 5: SBQQ__ConfigurationAttribute__c, SBQQ__OptionConstraint__c
Each wave is a separate completed Bulk API job confirmed before the next wave starts.
```

**Detection hint:** Look for a migration plan that puts ProductOption, PriceAction, ConfigurationAttribute, or OptionConstraint in the same load file or job as Product2 or PriceRule.

---

## Anti-Pattern 2: Not Disabling CPQ Triggers Before Bulk Load

**What the LLM generates:** A bulk load script or Data Loader procedure with no mention of disabling CPQ triggers in Additional Settings, or a note that says "CPQ triggers will fire but that's acceptable."

**Why it happens:** LLMs are aware that Salesforce triggers can be disabled via metadata but are not reliably aware that CPQ managed-package triggers are controlled through a CPQ-specific UI setting (Additional Settings > Triggers Disabled), not through standard Apex or metadata deployment patterns. The LLM may advise disabling custom triggers in code, which does not affect CPQ managed-package triggers at all.

**Correct pattern:**

```
Before any bulk DML:
1. Navigate to CPQ Setup > Additional Settings
2. Set "Triggers Disabled" = true
3. Confirm: SELECT SBQQ__TriggerAutoRuns__c FROM SBQQ__PackageSettings__c LIMIT 1
   (SBQQ__TriggerAutoRuns__c = false means triggers are disabled)
After all waves complete and validation passes:
4. Re-enable: set "Triggers Disabled" = false
```

**Detection hint:** Any migration plan that does not reference CPQ Additional Settings, or that advises managing trigger behavior through custom Apex, is missing the correct control.

---

## Anti-Pattern 3: Single-Pass Insert for Self-Referencing Product2 Records

**What the LLM generates:** A single Bulk API job that loads all Product2 records including those with SBQQ__UpgradeTarget__c or similar self-referencing fields populated, relying on row ordering to ensure the referenced product is committed before the referencing product.

**Why it happens:** LLMs know that foreign key constraints require parent records to exist first and apply this as a row-ordering rule within a single file. They are not aware that Bulk API 2.0 processes rows in configurable-size batches — a row early in the file may be in Batch 1, but a row later in the file that references it may be in Batch 2, which can start processing before Batch 1 is fully committed.

**Correct pattern:**

```
Pass 1 INSERT — all Product2 records with self-referencing fields blank:
Id,Name,ProductCode,...,SBQQ__UpgradeTarget__c
(leave SBQQ__UpgradeTarget__c empty)

After Pass 1 confirms all Product2 records in target:
Pass 2 UPDATE — only records with self-referencing fields:
Id,SBQQ__UpgradeTarget__c
<target_id_of_product>,<target_id_of_upgrade_target>
```

**Detection hint:** Any plan that populates SBQQ__UpgradeTarget__c or similar self-referencing Product2 fields in a single insert wave.

---

## Anti-Pattern 4: Not Validating PriceActions Against Existing PriceRules Before Go-Live

**What the LLM generates:** A migration procedure that considers the PriceAction bulk insert job successful based solely on the Bulk API success response, then re-enables CPQ triggers and moves to UAT.

**Why it happens:** LLMs treat platform-level DML success as equivalent to data integrity. They are not aware that CPQ's managed-package FK relationship between PriceAction and PriceRule is not enforced at the DML layer — orphaned PriceAction records insert without error, and the silent failure only surfaces during quote calculation.

**Correct pattern:**

```soql
-- Run this after Wave 4 PriceAction load, before re-enabling triggers
SELECT Id, Name, SBQQ__PriceRule__c, SBQQ__Type__c
FROM SBQQ__PriceAction__c
WHERE SBQQ__PriceRule__c = null
```

Zero rows required. If rows are returned, diagnose missing PriceRule FKs, re-load affected PriceRule records, and re-upsert affected PriceAction records before proceeding.

**Detection hint:** Any migration plan that calls the PriceAction load "complete" based on Bulk API success count alone, without a post-load orphan detection query.

---

## Anti-Pattern 5: Using Source Org Salesforce IDs Directly for SBQQ FK Columns

**What the LLM generates:** A migration CSV that uses the source org's 18-character Salesforce record IDs directly in FK columns (e.g., SBQQ__PriceRule__c = '0lQ000000XXXXXX'). The LLM may note that "you'll need to update the IDs after loading parent records" without providing a concrete mechanism.

**Why it happens:** LLMs generate syntactically valid CSVs using the ID format they know from training. They are not reliably aware of the external ID relationship notation pattern in Bulk API 2.0 and Data Loader, which allows the platform to resolve FKs using a business key field rather than a Salesforce ID.

**Correct pattern:**

```
Step 1: Add an External ID field to each SBQQ object (e.g., Migration_ExternalId__c)
Step 2: Populate the field with the source org's record ID (or a stable business key)
Step 3: In load files, use relationship notation instead of direct ID columns:
  Wrong:  SBQQ__PriceRule__c,  0lQ000000XXXXXX
  Correct: SBQQ__PriceRule__r.Migration_ExternalId__c, 0lQ000000XXXXXX (source ID as key)
Step 4: The platform resolves the FK at upsert time — no manual ID mapping needed
```

**Detection hint:** Any migration CSV template that contains 15- or 18-character Salesforce IDs in FK columns without a corresponding note about how those IDs will be remapped to target org IDs.

---

## Anti-Pattern 6: Loading OptionConstraint in the Same Wave as ProductOption

**What the LLM generates:** A migration plan that combines SBQQ__OptionConstraint__c and SBQQ__ProductOption__c in a single bulk job, reasoning that OptionConstraint rows can be ordered after ProductOption rows in the same file.

**Why it happens:** LLMs apply the same "parents before children in same file" heuristic. They are not aware that OptionConstraint references two ProductOption records (constrained and constraining), and that Bulk API batch boundaries can cause both referenced ProductOption records to be uncommitted when the OptionConstraint batch is processed.

**Correct pattern:**

```
Wave 4: SBQQ__ProductOption__c (separate completed job)
  → Confirm: SELECT COUNT() FROM SBQQ__ProductOption__c WHERE Migration_ExternalId__c != null
  → Count must match source export count before proceeding

Wave 5: SBQQ__OptionConstraint__c (new job, only after Wave 4 count confirmed)
```

**Detection hint:** Any plan that places OptionConstraint in Wave 4 or in the same job as ProductOption.
