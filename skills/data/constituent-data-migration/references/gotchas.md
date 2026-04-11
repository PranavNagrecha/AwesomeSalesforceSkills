# Gotchas — Constituent Data Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Data Loader and Standard Import Wizard Bypass NPSP Apex Triggers

**What happens:** Inserting Contact records via Data Loader, the Salesforce Data Import Wizard, or any direct API insert to the `Contact` sObject does not invoke NPSP's Table-Driven Trigger Management (TDTM) framework. The result is silent data corruption: Household Account rollup fields (total giving, last gift date, number of gifts) are not populated, household member relationship records (`npe4__Relationship__c`) are not created, and `npsp__Address__c` records are not generated. Every imported Contact also receives its own new one-contact Household Account, even if the intent was to add them to an existing household.

**When it occurs:** Any time a practitioner uses Data Loader, the standard Salesforce Data Import Wizard, or REST/SOAP API inserts directly to `Contact` in an NPSP org.

**How to avoid:** Always use the NPSP Data Importer (staging to `npsp__DataImport__c` followed by the `BDI_DataImport` batch) for all constituent inserts and updates in an NPSP org. This is the only import path that routes through NPSP's trigger framework.

---

## Gotcha 2: Contact2 Fields Are Silently Skipped When Contact1 Fields Are Missing

**What happens:** Each `npsp__DataImport__c` row supports two contacts via Contact1 and Contact2 field pairs. If `npsp__Contact1_Firstname__c` or `npsp__Contact1_Lastname__c` is blank, NPSP silently skips the entire row — including any Contact2 data that is fully populated. The row status is set to `Failed` with an error message referencing Contact1 required fields, but the Contact2 record is not created in a partial way; it is simply lost.

**When it occurs:** When source data has a household where only a second contact name is available (e.g., a partner listed without a full first name), or when the ETL mapping incorrectly places the primary contact in the Contact2 columns.

**How to avoid:** Validate that every staging row with Contact2 data also has Contact1 first name and last name populated before loading. In ETL transformations, always assign the more completely-known individual as Contact1.

---

## Gotcha 3: Household Account Names Are Auto-Generated and Cannot Be Directly Overridden via Import

**What happens:** NPSP auto-formats Household Account names using the Household Naming Format configured in NPSP Settings (default: "{LastName} Household"). The import process ignores any Account name value provided on the staging record. If a legacy CRM stored households under a custom name (e.g., "The Smith Family Fund"), that name will not be preserved — the account will be created as "Smith Household" instead.

**When it occurs:** When migrating from any system that stores household or family names and the receiving NPSP org has not been pre-configured with a matching naming format.

**How to avoid:** Before running the migration, review and configure the Household Naming Format in **NPSP Settings > Household > Household Naming**. If custom names must be preserved post-import, they must be updated via a separate batch update to `Account.Name` after the NPSP import run completes — not during the import itself.

---

## Gotcha 4: Re-running the Import on Already-Processed Rows Creates Duplicates

**What happens:** `npsp__DataImport__c` rows with `npsp__Status__c = Imported` that are left in the org can be re-processed if the Data Importer is run again without filtering. NPSP's Contact Matching Rules will determine whether re-processing creates a new duplicate or matches the existing record — depending on the matching rule configuration and data quality, duplicates may be silently created.

**When it occurs:** When a practitioner re-runs the Data Importer to process new rows but does not filter out already-imported staging records, or when an administrator re-processes a batch job that previously completed successfully.

**How to avoid:** After each successful import run, delete or archive all `npsp__DataImport__c` rows with `npsp__Status__c = Imported`. Use list views or SOQL filters (`WHERE npsp__Status__c = 'Imported'`) to identify and clean up processed rows before each new import run.

---

## Gotcha 5: Large Batch Sizes Cause Apex CPU Time Limit Errors

**What happens:** The `BDI_DataImport` batch class processes `npsp__DataImport__c` rows in configurable batch sizes. When rows contain complex household groupings, multiple donation records, and address data simultaneously, the per-transaction Apex CPU limit (10,000 ms synchronous, 60,000 ms asynchronous) can be exceeded. This causes entire batch chunks to fail with a `System.LimitException: Apex CPU time limit exceeded` error, and the affected rows are marked failed without partial processing.

**When it occurs:** On large migrations where each staging row carries Contact1+Contact2+Address+Donation data simultaneously, especially in orgs with heavy custom trigger logic or many active NPSP TDTM trigger handlers.

**How to avoid:** Reduce the Data Importer batch size in **NPSP Settings > Data Import > Batch Size** (default 50). For complex rows, batch sizes of 10–25 are safer. Monitor the Apex Jobs page during migration runs and check for CPU limit errors in the batch job's exception log.
