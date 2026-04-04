# Examples — External ID Strategy

## Example 1: ERP Customer Number as Account External ID

**Context:** A manufacturing company is migrating 200,000 Account records from a legacy ERP system into Salesforce. The ERP assigns each customer a numeric account number (e.g., `10042`, `83971`). The same numbers are referenced in open Opportunity and Order records that will be loaded after Accounts. After migration, the ERP will continue sending nightly delta loads of updated customer records via Bulk API 2.0.

**Problem:** Without an external ID field, the initial load inserts all 200,000 Accounts. The nightly delta job has no way to match incoming ERP records to existing Salesforce Accounts without querying for Salesforce IDs first (a fragile two-pass approach). Re-running the initial load would create 200,000 duplicates.

**Solution:**

Create a Number external ID field on Account:

```xml
<!-- force-app/main/default/objects/Account/fields/ERP_Customer_Number__c.field-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>ERP_Customer_Number__c</fullName>
    <label>ERP Customer Number</label>
    <type>Number</type>
    <precision>18</precision>
    <scale>0</scale>
    <externalId>true</externalId>
    <unique>true</unique>
</CustomField>
```

Bulk API 2.0 upsert job configuration (JSON):

```json
{
  "object": "Account",
  "operation": "upsert",
  "externalIdFieldName": "ERP_Customer_Number__c",
  "contentType": "CSV",
  "lineEnding": "LF"
}
```

CSV load file:

```csv
ERP_Customer_Number__c,Name,BillingCity,BillingCountry
10042,Acme Manufacturing,Chicago,US
83971,Globex Corp,Houston,US
```

**Why it works:** The Number field type avoids all case-sensitivity concerns. Marking it External ID creates an automatic index — matching 200,000 records on this field is fast even without a custom Support-provisioned index. Marking it Unique prevents UI-created duplicates and makes upsert deterministic: the same file loaded twice produces the same 200,000 records, not 400,000.

---

## Example 2: Multi-System Composite External ID for Contact Records

**Context:** A company acquired two businesses. Each acquired company's contacts are being migrated into the same Salesforce org. Contact IDs from Company A are integers (e.g., `1001`, `2002`); Contact IDs from Company B are also integers starting from `1001`. Both companies' IDs therefore overlap, so neither can serve as a standalone external ID.

**Problem:** Using raw source IDs as the external ID field would cause Company A's contact `1001` and Company B's contact `1001` to match the same Salesforce record on upsert, corrupting data from both sources.

**Solution:**

Create a Text external ID field with a composite key:

```xml
<!-- force-app/main/default/objects/Contact/fields/Source_Composite_Key__c.field-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Source_Composite_Key__c</fullName>
    <label>Source Composite Key</label>
    <type>Text</type>
    <length>100</length>
    <externalId>true</externalId>
    <unique>true</unique>
    <caseSensitive>false</caseSensitive>
</CustomField>
```

ETL layer composite key generation (Python example):

```python
def build_composite_key(system_code: str, source_id: str) -> str:
    """
    Composite key formula: <SYSTEMCODE>|<SOURCE_ID>
    Separator: pipe (|) — cannot appear in either component field.
    Max length: 100 chars (field limit configured above).
    """
    key = f"{system_code.upper()}|{source_id}"
    if len(key) > 100:
        raise ValueError(f"Composite key exceeds 100 characters: {key!r}")
    return key

# Company A contact 1001 → "ACQA|1001"
# Company B contact 1001 → "ACQB|1001"
```

CSV load file (Company A):

```csv
Source_Composite_Key__c,FirstName,LastName,Email,AccountId
ACQA|1001,Jane,Smith,jane.smith@acqa.com,
ACQA|2002,Bob,Jones,bob.jones@acqa.com,
```

**Why it works:** Prefixing with a system code makes every value globally unique across both companies. Using a pipe separator avoids conflicts with comma (CSV delimiter) or slash (URL path character). Documenting the formula in the ETL layer ensures future loads from either system reproduce identical composite keys — guaranteeing upsert will match existing records rather than inserting duplicates.

---

## Example 3: Parent-Child Relationship Resolution by External ID

**Context:** Loading Opportunity records after Accounts are already in Salesforce with `ERP_Customer_Number__c` populated. The Opportunity source file has the ERP customer number but not the Salesforce Account `Id`.

**Problem:** A two-pass approach (query all Account IDs keyed by `ERP_Customer_Number__c`, embed Salesforce IDs in the Opportunity CSV) works but is fragile in production: it requires a SOQL query that may paginate across 200k records, and the resulting Opportunity file contains Salesforce IDs that are invalid in other org copies (sandboxes, scratch orgs).

**Solution:**

Use relationship resolution syntax in the Opportunity CSV column headers. No pre-query needed:

```csv
ERP_Opportunity_Id__c,Name,StageName,CloseDate,Account.ERP_Customer_Number__c,Amount
OPP-5001,New Server Deal,Prospecting,2026-06-30,10042,50000
OPP-5002,Software License,Qualification,2026-07-15,83971,12000
```

Bulk API 2.0 job:

```json
{
  "object": "Opportunity",
  "operation": "upsert",
  "externalIdFieldName": "ERP_Opportunity_Id__c",
  "contentType": "CSV",
  "lineEnding": "LF"
}
```

The column `Account.ERP_Customer_Number__c` tells Salesforce to look up the Account using `ERP_Customer_Number__c` as the match field. Salesforce resolves the parent `AccountId` at ingest time without any client-side query.

**Why it works:** The parent's external ID field is indexed, so row-level parent resolution is efficient at scale. This approach is also org-portable: the same Opportunity file loaded into a full sandbox produces identical parent relationships, because it references source system keys rather than org-specific Salesforce IDs.

---

## Anti-Pattern: Using Salesforce Record ID as the Upsert Key

**What practitioners do:** After loading records once, some integrations store the returned Salesforce `Id` values in the source system and use them as the upsert match key on subsequent loads (via the standard `Id` field in the CSV, not an external ID field).

**What goes wrong:** Salesforce IDs are org-specific. When the integration is tested against a sandbox, the sandbox `Id` values differ from production. If the sandbox is refreshed, all IDs change again. Any load file that embeds Salesforce IDs is non-portable and will fail or corrupt data when pointed at a different org copy. Additionally, this approach requires the source system to maintain a mapping of Salesforce IDs, creating a circular dependency between the two systems.

**Correct approach:** Design the external ID field at the start of the integration. Populate it in the initial load. Use it as the upsert key on every subsequent load. The source system's natural key is the only cross-system identifier that needs to be stored — never Salesforce record IDs.
