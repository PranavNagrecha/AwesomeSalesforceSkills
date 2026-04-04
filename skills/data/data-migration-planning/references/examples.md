# Examples — Data Migration Planning

## Example 1: Legacy CRM to Salesforce — Account, Contact, and Opportunity Migration

**Context:** A company is migrating 180,000 Accounts, 620,000 Contacts, and 95,000 Opportunities from an on-premises legacy CRM to a new Salesforce org. The source system uses integer IDs as primary keys. Contacts have a lookup to Account; Opportunities have a lookup to Account. Opportunity Line Items (OLIs) have a master-detail to Opportunity and require a matching Price Book Entry.

**Problem:** The team's first attempt loaded all objects simultaneously using separate insert jobs. Contacts failed because their Account lookup IDs were source system integers, not Salesforce record IDs. OLIs failed because the related Opportunities were still in the queue when the OLI job started. After the load, 40,000 Contact records had blank Account fields (the insert silently succeeded with a null lookup rather than failing — this was a Lookup, not an MDR). Duplicate Accounts appeared on re-run because insert was used instead of upsert.

**Solution:**

Step 1: Add External ID fields before any load.

```
Object        Field API Name         Type       Config
Account       Legacy_CRM_Id__c       Text(20)   External ID, Unique, Not Required
Contact       Legacy_CRM_Id__c       Text(20)   External ID, Unique, Not Required
Opportunity   Legacy_CRM_Id__c       Text(20)   External ID, Unique, Not Required
```

Step 2: Define the load sequence.

```
1. Accounts     (no dependencies)
2. Contacts     (lookup to Account — Account must exist first)
3. Opportunities  (lookup to Account — Account must exist first)
4. Products / PricebookEntries  (must exist before OLIs)
5. Opportunity Line Items  (master-detail to Opportunity; references PricebookEntry)
```

Step 3: Prepare the Contact CSV to reference Account by external ID.

```csv
Legacy_CRM_Id__c,FirstName,LastName,Account.Legacy_CRM_Id__c,Email
CONT-001,Jane,Smith,ACCT-042,jane.smith@example.com
CONT-002,Bob,Jones,ACCT-017,bob.jones@example.com
```

The column `Account.Legacy_CRM_Id__c` uses Bulk API 2.0 relationship notation. Salesforce resolves the Account Salesforce record ID at load time using the Account's external ID.

Step 4: Load each object via Bulk API 2.0 upsert with `Legacy_CRM_Id__c` as the external ID field. Set `Migration_Batch_Id__c` to a unique value per run (e.g., `ACCT-2026-04-04-001`).

Step 5: After each object completes, verify:
- Source count matches Salesforce query count
- Error file from Bulk API is empty or understood
- Sample 1% of records for field accuracy

**Why it works:** Upsert with external ID prevents duplicate creation on re-run. Relationship cross-references via `Parent__r.ExternalId__c` eliminate the need to pre-resolve Salesforce IDs. The strict load sequence ensures no child insert is attempted before its parent exists.

---

## Example 2: Product Catalog and Price Book First — Prerequisite for Opportunity Line Items

**Context:** A retailer is migrating 50,000 Opportunities and 210,000 Opportunity Line Items (OLIs). The legacy system has product SKUs. Salesforce requires that each OLI reference both an Opportunity record and a Price Book Entry record. The migration team initially tried to load OLIs immediately after Opportunities, without first loading the product catalog.

**Problem:** Every OLI insert failed with "FIELD_INTEGRITY_EXCEPTION: PricebookEntryId: id value of incorrect type." The team had not loaded Products or Price Book Entries. Because OLIs are a master-detail child of Opportunity, every failed OLI insert also created an orphaned Opportunity with no line items, making the Opportunities appear incomplete in the UI.

**Solution:**

Extended load sequence:

```
1. Accounts
2. Contacts
3. Opportunities
4. Products (Product2 object — the product catalog)
5. Standard Price Book Entries (PricebookEntry — links Product2 to the Standard Price Book)
6. Custom Price Book Entries (if the org uses a custom price book)
7. Opportunity Line Items (OpportunityLineItem — master-detail to Opportunity;
                           references PricebookEntryId)
```

OLI CSV structure (using external ID cross-references):

```csv
Legacy_OLI_Id__c,Opportunity.Legacy_CRM_Id__c,PricebookEntry.ProductCode,Quantity,UnitPrice
OLI-10001,OPP-5001,SKU-9900,2,299.99
OLI-10002,OPP-5001,SKU-8812,1,149.00
```

`PricebookEntry.ProductCode` uses the ProductCode field on the PricebookEntry as a cross-reference (must be marked External ID, or use an explicit external ID field added to PricebookEntry).

**Why it works:** The Salesforce referential integrity model enforces that every master-detail parent exists before a child can be inserted. By loading the full product catalog before Opportunities and OLIs, all references are resolvable at load time. Using external ID cross-references for both parent relationships avoids manual ID resolution.

---

## Anti-Pattern: Loading All Objects in Parallel Without a Dependency Sequence

**What practitioners do:** To save time, teams submit Bulk API jobs for all objects simultaneously — Accounts, Contacts, Opportunities, and Cases all start loading at the same time across parallel jobs.

**What goes wrong:** Child object jobs complete rows before their parent jobs finish loading the corresponding parent records. Contacts with a reference to Account "ACCT-5500" fail if that Account hasn't been committed yet. Master-detail children (OLIs, Case Comments) fail with hard errors. Lookup children (Contacts) may partially succeed with null parent references if the lookup is not required — creating orphan records that are hard to detect without a post-migration integrity check.

**Correct approach:** Build an explicit dependency graph before starting any loads. Submit load jobs sequentially per dependency tier — all records in Tier 1 (no parents) complete before Tier 2 begins. Verify each tier's error file before proceeding to the next. Use `Migration_Batch_Id__c` to tag each tier's records so any tier can be rolled back independently if downstream failures occur.

---

## Anti-Pattern: Using Insert Instead of Upsert

**What practitioners do:** Teams use Bulk API insert for the initial load. When a partial failure occurs and they re-run the job, they use insert again for all records — including ones that succeeded the first time.

**What goes wrong:** Every record that loaded successfully in the first run is now duplicated. Accounts appear twice, Contacts appear twice, and every downstream relationship now has ambiguous parent references. Deduplication is expensive, time-consuming, and risks breaking relationships.

**Correct approach:** Always use upsert with a populated External ID field, even for the very first load. If a record already exists, upsert updates it. If it does not exist, upsert inserts it. A re-run is always safe. The only cost is that the External ID field must be designed and created before the first load — which should be part of the migration planning phase, not an afterthought.
