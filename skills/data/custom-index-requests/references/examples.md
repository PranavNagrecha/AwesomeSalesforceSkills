# Examples — Custom Index Requests

## Example 1: Lead Routing Query — Change the Query Before Asking for an Index

**Scenario:** 4,000,000 Lead rows. A routing job runs `SELECT Id, OwnerId FROM Lead WHERE Lead_Source_Detail__c = 'Inbound Web' AND Status = 'Open'` every few seconds. The plan shows a table scan.

**Arithmetic:** custom-index threshold for 4,000,000 rows = 10% × 1,000,000 + 5% × 3,000,000 = 250,000. `'Inbound Web'` matches 600,000 rows, so a custom index on `Lead_Source_Detail__c` would not be used.

**Solution:**

1. Add a recent-records filter the routing logic actually needs:

```soql
SELECT Id, OwnerId
FROM Lead
WHERE Lead_Source_Detail__c = 'Inbound Web'
AND Status = 'Open'
AND CreatedDate = LAST_N_DAYS:30
```

2. `CreatedDate = LAST_N_DAYS:30` matches about 40,000 rows, far under the standard-index threshold for 4,000,000 rows (300,000 + 450,000 = 750,000), so the CreatedDate index can drive the query. Capture the plan to confirm `leadingOperationType: Index` on `CreatedDate`.
3. Only if the plan still scans, request a two-column index with the selecting field first, using the case format in `support-case-worked-example.md`.

**Why it works:** The request that was going to fail the threshold is never filed; the query is made selective with an index that already exists.

---

## Example 2: Integration Key That Must Stay Unique

**Scenario:** An ERP sends Accounts keyed by `ERP_Account_Number__c` (Text). Upserts must never hit two records.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Account/fields/ERP_Account_Number__c.field-meta.xml -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>ERP_Account_Number__c</fullName>
    <label>ERP Account Number</label>
    <type>Text</type>
    <length>30</length>
    <externalId>true</externalId>
    <unique>true</unique>
    <caseSensitive>false</caseSensitive>
</CustomField>
```

**Why it works:** External ID makes the field usable for upsert and gets it indexed; Unique is what rejects duplicates. With External ID alone, a duplicated value would make upserts on that key fail with a 300 error instead of being prevented at insert time.

---

## Example 3: Skinny Table for an Executive Dashboard

**Scenario:** 3,800,000 Opportunity rows. A dashboard's reports filter `CreatedDate = THIS_QUARTER` (about 300,000 rows, under the standard-index threshold of 300,000 + 15% × 2,800,000 = 720,000) and read the same eight fields, a mix of standard and custom. CreatedDate is indexed by default; CloseDate is not among the default indexed fields (LDV guide L399-407), so a CloseDate filter would need its own custom index and would face the tighter 240,000 custom threshold.

**Problem:** The filter is selective and indexed, but every read joins the standard-field and custom-field tables.

**Solution:** Ask Support for a skinny table on Opportunity with exactly the fields the reports use (`Id`, `OwnerId`, `CreatedDate`, `CloseDate`, `StageName`, `Amount`, `AccountId`, `Forecast_Region__c`). Test it in a Full sandbox, the only sandbox type it is copied to. When a report adds a field, file a follow-up request, because a query that needs a field outside the skinny table does not use it.

**Why it works:** The reports are read-only and use only fields in the skinny table, which is the case the LDV guide describes. The request is narrow so the maintenance overhead the guide warns about stays small.
