# Examples — Data Model Design Patterns

## Example 1: Modeling Course Enrollments as a Junction Object

**Context:** An education org has a `Course__c` object and a `Student__c` object. Each student can enroll in many courses, and each course can have many students. The business also wants a rollup count of active enrollments on each Course record.

**Problem:** The initial design used two lookup fields on an `Enrollment__c` junction object — one lookup to `Course__c` and one lookup to `Student__c`. The team discovered they could not create a rollup summary field on `Course__c` to count active enrollments, because rollup summary fields only work on master-detail relationships. Additionally, when a student record was deleted, the enrollment records were left as orphans with a blank `Student__c` field.

**Solution:**

Replace both lookup fields with master-detail relationships:

1. Delete the existing lookup field `Student__c` on `Enrollment__c` (requires clearing data or doing a full re-import).
2. Create a new master-detail field `Student__c` on `Enrollment__c` pointing to `Student__c` object.
3. Repeat for `Course__c`: replace the lookup with a master-detail field.
4. Populate both MDR fields on all existing enrollment records.
5. Create a rollup summary field `Active_Enrollment_Count__c` on `Course__c` using COUNT with filter `Status__c = "Active"`.

Result: Deleting a student cascades to delete their enrollments. Deleting a course cascades to delete its enrollments. The rollup on `Course__c` works as expected.

**Why it works:** Master-detail relationships enforce referential integrity at the platform level (child cannot exist without a parent) and expose the child record set to the rollup summary engine. The junction pattern with two MDR fields is the only native Salesforce way to achieve both rollup summaries and cascade delete on a many-to-many link.

---

## Example 2: External ID Field for Integration Upsert

**Context:** A manufacturing org syncs product data from an ERP system into a custom `Product_Record__c` object nightly via Bulk API 2.0. The ERP has its own stable identifier for each product (`ERP_Product_Code`), which is not the Salesforce record Id. The integration team initially used the `Name` field as the matching key, causing duplicate records on every sync run.

**Problem:** The Bulk API 2.0 upsert operation requires an External ID field as the match key. `Name` is not an External ID field — the upsert API does not use it for matching. Because there was no External ID, every run inserted all records as new rather than updating existing ones. After three months, the org had 90,000 duplicate product records.

**Solution:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Product_Record__c/fields/ERP_Product_Code__c.field-meta.xml -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>ERP_Product_Code__c</fullName>
    <label>ERP Product Code</label>
    <type>Text</type>
    <length>50</length>
    <externalId>true</externalId>
    <unique>true</unique>
    <caseSensitive>false</caseSensitive>
</CustomField>
```

After adding the field:

1. Backfill `ERP_Product_Code__c` on all existing records from the ERP source.
2. Deduplicate the 90,000 records by merging or deleting duplicates, keeping the canonical `ERP_Product_Code__c` value per record.
3. Update the integration job to use Bulk API 2.0 upsert with `ERP_Product_Code__c` as the external ID field.

**Why it works:** External ID fields are indexed by default. The platform uses the external ID value as the match key during upsert — if a record with that value exists, it updates; otherwise it inserts. Marking the field Unique prevents duplicate values from being inserted, so a second run with the same ERP code always resolves to the existing record.

---

## Example 3: Custom Index Request for Large Account Queries

**Context:** A financial services org has 4 million Account records. Every morning, a reporting process runs a SOQL query filtering on `Account_Region__c` (a custom picklist field, not indexed) to generate territory summaries. The query times out (the limits guide gives a query operation 2 minutes to execute).

**Problem:** `Account_Region__c` is not indexed, so the plan is a table scan across 4 million rows. Each region holds about 5% of rows, which may be selective enough for a custom index; the arithmetic decides.

**Solution:**

1. Verify selectivity against the tiered threshold: for 4,000,000 rows a custom index is used below 10% × 1,000,000 + 5% × 3,000,000 = 250,000 rows. The largest region matches about 200,000 rows, so it qualifies. (At 8%, 320,000 rows, it would not, and the request would be wasted.)
2. Confirm the field type can take a custom index: a single-select picklist can; a multi-select picklist, long text, encrypted text, or non-deterministic formula can't.
3. Open a Salesforce Support case with:
   - Object: `Account`
   - Field API name: `Account_Region__c`
   - Justification: frequent large-volume SOQL query, 4M records, filter is selective
4. After the index is created, capture the plan with the REST API `explain` parameter (Beta):
   ```bash
   curl -H "Authorization: Bearer $ACCESS_TOKEN" \
     "$INSTANCE_URL/services/data/v67.0/query/?explain=SELECT+Id,Name+FROM+Account+WHERE+Account_Region__c='APAC'"
   ```
   The first plan should show `leadingOperationType: Index` and `relativeCost` under 1.0.

**Why it works:** The filter value is under the custom-index threshold for the object's size, so the optimizer can drive the query from the index instead of scanning every row. Re-check when the object grows, because the threshold is a share of the row count.

---

## Anti-Pattern: Using Text(255) for Phone and Email Data

**What practitioners do:** Create custom fields for phone numbers and email addresses as `Text(255)` fields because "it's just a string."

**What goes wrong:**
- Phone fields stored as Text do not render with click-to-dial in Salesforce mobile or Lightning. Users cannot tap a phone number to initiate a call.
- Email fields stored as Text do not get email validation on entry. Invalid email addresses (missing `@`, typos) are stored without error.
- Text fields do not participate in the Salesforce duplicate rule email/phone matching engine.
- In formulas and flow, Phone and Email types have distinct formatting behavior; Text fields do not.

**Correct approach:** Use the `Phone` field type for phone numbers and the `Email` field type for email addresses. Both provide platform-level formatting, validation, and UI affordances. If the data already exists in Text fields, create new Phone/Email fields, migrate the data via a data loader job, then retire the old Text fields.
