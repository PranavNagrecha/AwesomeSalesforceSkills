# Examples — Data Migration Planning

## Example 1: Legacy CRM to Salesforce — Account, Contact, and Opportunity Migration

**Context:** A company is migrating 180,000 Accounts, 620,000 Contacts, and 95,000 Opportunities from an on-premises legacy CRM to a new Salesforce org. The source system uses integer IDs as primary keys. Contacts have a lookup to Account; Opportunities have a lookup to Account. Opportunity Line Items (OLIs) have a master-detail to Opportunity and require a matching Price Book Entry.

**Problem:** The team's first attempt loaded all objects simultaneously using separate insert jobs. Contacts failed because their Account lookup IDs were source system integers, not Salesforce record IDs. OLIs failed because the related Opportunities were still in the queue when the OLI job started. After the load, 40,000 Contacts whose source rows had no account key loaded with a blank Account lookup, which is legal for an optional lookup and went unnoticed until a report showed them. Duplicate Accounts appeared on re-run because insert was used instead of upsert.

**Solution:**

Step 1: Add External ID fields before any load.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Contact/fields/Legacy_CRM_Id__c.field-meta.xml (same shape on Account and Opportunity) -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Legacy_CRM_Id__c</fullName>
    <label>Legacy CRM ID</label>
    <type>Text</type>
    <length>20</length>
    <externalId>true</externalId>
    <unique>true</unique>
    <required>false</required>
</CustomField>
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

The column `Account.Legacy_CRM_Id__c` uses the Bulk API `RelationshipName.IndexedFieldName` header form; it works because `Legacy_CRM_Id__c` is an External ID on Account (only indexed parent fields are allowed). Sort the file by that column so contacts of the same account share a batch.

Step 4: Load each object via Bulk API 2.0 upsert with `Legacy_CRM_Id__c` as the external ID field. Set `Migration_Batch_Id__c` to a unique value per run (e.g., `ACCT-2026-04-04-001`).

Step 5: After each object completes, verify:
- Source count matches Salesforce query count
- Error file from Bulk API is empty or understood
- Sample 1% of records for field accuracy

**Why it works:** Upsert with an external ID makes re-runs safe. Relationship columns remove the step of looking up Salesforce IDs. The sequence means no child row is attempted before its parent exists, and a post-load count of contacts with a source account key but a blank `AccountId` catches the rows that slipped through.

---

## Example 2: Product Catalog and Price Book First — Prerequisite for Opportunity Line Items

**Context:** A retailer is migrating 50,000 Opportunities and 210,000 Opportunity Line Items (OLIs). The legacy system has product SKUs. Salesforce requires that each OLI reference both an Opportunity record and a Price Book Entry record. The migration team initially tried to load OLIs immediately after Opportunities, without first loading the product catalog.

**Problem:** Every OLI row failed because its price book entry reference did not resolve: the team had not loaded Products or Price Book Entries. The Opportunities loaded fine but had no line items, so amounts and products looked wrong in the UI until the catalog was loaded and the OLI job re-run.

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
Legacy_OLI_Id__c,Opportunity.Legacy_CRM_Id__c,PricebookEntry.Legacy_PBE_Id__c,Quantity,UnitPrice
OLI-10001,OPP-5001,PBE-STD-9900,2,299.99
OLI-10002,OPP-5001,PBE-STD-8812,1,149.00
```

`PricebookEntry.Legacy_PBE_Id__c` references a custom External ID field added to PricebookEntry. A relationship column can only use an indexed parent field: a custom field with External ID selected, or a standard field whose `idLookup` property is true.

**Why it works:** Every reference an OLI row carries (its Opportunity and its price book entry) exists before the OLI job starts, and both are referenced through External ID keys, so no Salesforce IDs need to be looked up.

---

## Anti-Pattern: Loading All Objects in Parallel Without a Dependency Sequence

**What practitioners do:** To save time, teams submit Bulk API jobs for all objects simultaneously — Accounts, Contacts, Opportunities, and Cases all start loading at the same time across parallel jobs.

**What goes wrong:** Child object jobs complete rows before their parent jobs finish loading the corresponding parent records. Contacts with a reference to Account "ACCT-5500" fail if that Account hasn't been committed yet. Master-detail children (OLIs, Case Comments) fail with hard errors. Rows whose parent key has not been committed yet fail to resolve, so a parallel run produces a scatter of failures that must be re-run in order anyway.

**Correct approach:** Build an explicit dependency graph before starting any loads. Submit load jobs sequentially per dependency tier — all records in Tier 1 (no parents) complete before Tier 2 begins. Verify each tier's error file before proceeding to the next. Use `Migration_Batch_Id__c` to tag each tier's records so any tier can be rolled back independently if downstream failures occur.

---

## Anti-Pattern: Using Insert Instead of Upsert

**What practitioners do:** Teams use Bulk API insert for the initial load. When a partial failure occurs and they re-run the job, they use insert again for all records — including ones that succeeded the first time.

**What goes wrong:** Every record that loaded successfully in the first run is now duplicated. Accounts appear twice, Contacts appear twice, and every downstream relationship now has ambiguous parent references. Deduplication is expensive, time-consuming, and risks breaking relationships.

**Correct approach:** Use upsert with a populated External ID field for any load that may be re-run. If a record exists, upsert updates it; otherwise it inserts it. The LDV guide ranks insert as faster than update and upsert, so for a very large first load into an empty object, an insert pass is reasonable as long as the External ID is populated and any re-run switches to upsert.
