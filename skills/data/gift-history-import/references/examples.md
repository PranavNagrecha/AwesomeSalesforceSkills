# Examples — Gift History Import

## Example 1: Direct Data Loader Import Bypassing BDI — Missing OCRs and Payments

**Scenario:** A nonprofit migrated 12,000 historical gift records from Raiser's Edge into NPSP by exporting to CSV and loading directly into the Opportunity object via Data Loader. The import completed successfully with exit code 0, but all Opportunities were missing payment records and soft credits.

**Problem:** Direct Opportunity insert bypasses the NPSP BDI Apex batch entirely. BDI is responsible for creating `npe01__OppPayment__c` records and Opportunity Contact Roles (soft credits). When you skip BDI, these child records are never created.

**Solution:**
1. Delete the incorrectly imported Opportunities (after verifying they are the migration batch, not live donations)
2. Prepare a DataImport__c staging CSV with the correct column structure
3. Load the staging records into `npsp__DataImport__c` via Data Loader
4. Run NPSP Data Importer batch from the App Launcher
5. Verify with SOQL: `SELECT COUNT() FROM npe01__OppPayment__c WHERE npe01__Opportunity__r.Name LIKE 'Import%'` — count should match gift record count

**Why this works:** BDI is the only supported mechanism for bulk gift creation in NPSP that preserves the full gift data model including payments, OCRs, and GAU allocations.

---

## Example 2: Custom Payment Fields Silently Unmapped — Advanced Mapping Not Enabled

**Scenario:** A healthcare nonprofit needed to import gift records with a custom `Check_Reference__c` field on the payment record. The DataImport__c staging CSV included a custom column for this field. After import, the field was blank on all payment records.

**Problem:** NPSP Advanced Mapping was not enabled in NPSP Settings. Without Advanced Mapping, BDI only processes standard NPSP-shipped field mappings. Custom fields on DataImport__c are present in the staging row but silently ignored during BDI processing — no error is raised.

**Solution:**
1. Navigate to NPSP Settings > Data Import > Advanced Mapping and enable it
2. Go to Field Mappings and create a mapping: DataImport__c source field → npe01__OppPayment__c target field
3. Re-stage the affected records (reset Status on DataImport__c rows to blank, or delete and re-insert)
4. Re-run BDI batch
5. Verify: `SELECT Check_Reference__c FROM npe01__OppPayment__c WHERE Check_Reference__c != null LIMIT 5`

**Why this works:** Advanced Mapping unlocks the full field mapping engine in BDI, allowing custom fields on DataImport__c to drive custom fields on Opportunity, Payment, and GAU Allocation records.

---

## Example 3: GAU Allocation Percent vs. Amount Mixed in Same Row

**Scenario:** An environmental nonprofit imported 8,000 gifts with GAU splits. Some gifts used percentage splits (50%/50%), others used fixed amounts ($75 to Fund A, $25 to Fund B). The staging CSV mixed percent fields and amount fields within the same DataImport__c row for some records.

**Problem:** BDI does not support mixing percent and amount allocation types within the same staging row. When both are present, BDI uses the amount fields and silently ignores the percent fields, resulting in incorrect GAU allocation totals for mixed rows.

**Solution:**
1. Standardize all GAU allocation rows to use either amount or percent — not both
2. For records with percentage splits, calculate the dollar amounts from the gift total and populate amount fields only
3. Re-stage affected records with corrected field values and re-run BDI

**Why this works:** The BDI GAU allocation engine expects a consistent split type per row. Converting percentages to amounts before staging is the safest approach for large volume imports with mixed split types.
