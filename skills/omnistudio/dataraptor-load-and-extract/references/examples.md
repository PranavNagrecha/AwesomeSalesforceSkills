# Examples — DataRaptor Load and Extract

## Example 1: Extracting Account with Related Contacts Using a Sub-Select

**Context:** An OmniScript needs to display an Account's details along with all active Contacts when an advisor opens a customer record. The data should be available in a single data load, not two separate API calls.

**Problem:** Using two separate DataRaptor Extracts (one for Account, one for Contacts) requires two Integration Procedure steps, increasing latency and complexity.

**Solution:**
Configure a DataRaptor Extract with:
- Base Object: `Account`
- SOQL Query: `SELECT Id, Name, Phone, BillingCity, (SELECT Id, LastName, FirstName, Email FROM Contacts WHERE IsDeleted = false) FROM Account WHERE Id = :accountId`
- Input Variable: `accountId` (bound from the OmniScript context)
- Output Mapping:
  - `Id` → `account.id`
  - `Name` → `account.name`
  - `Phone` → `account.phone`
  - `BillingCity` → `account.billingCity`
  - `Contacts.records` → `account.contacts` (using API relationship name `Contacts`)

Test in Preview tab with a real Account ID to confirm the nested output JSON structure.

**Why it works:** The SOQL sub-select retrieves child contacts in the same query. The OmniStudio output mapping traverses the relationship result set and nests it under the configured JSON path.

---

## Example 2: DataRaptor Load Upsert for External System Sync

**Context:** An external CRM sends customer records to Salesforce. Some records already exist (matching on External_Customer_ID__c), others are new. The team needs one Load that handles both cases without checking manually first.

**Problem:** Using an Insert-only Load would fail on duplicate records. Using Update-only would miss new records.

**Solution:**
Configure a DataRaptor Load with:
- Operation: `Upsert`
- Object: `Contact`
- Upsert Key Field: `External_Customer_ID__c` (must be designated as External ID on the field)
- Input Mappings:
  - `customer.externalId` → `External_Customer_ID__c`
  - `customer.firstName` → `FirstName`
  - `customer.lastName` → `LastName`
  - `customer.email` → `Email`

In the Integration Procedure, after the Load step, check `<LoadStep>:iferror` and surface error messages if any DML failures occurred.

**Why it works:** The platform matches incoming records on `External_Customer_ID__c`. Records with a matching value are updated; records without a match are inserted. The `iferror` check handles cases where DML fails (e.g., duplicate email validation rule).

---

## Anti-Pattern: Using DataRaptor Load for Bulk Record Import

**What practitioners do:** Configure a DataRaptor Load called from an Integration Procedure looping over a large JSON array to insert hundreds of records.

**What goes wrong:** DataRaptor Load uses standard DML — one DML statement per record iteration. For 500 records, this consumes 500 DML statements in a single transaction, quickly hitting governor limits. The Integration Procedure fails with a `Too many DML statements` error.

**Correct approach:** DataRaptor Load is designed for conversational, single-record or small-set operations within an OmniScript interaction. For bulk imports, use Bulk API 2.0 directly, Apex Batch with Database.executeBatch, or a data tool like Data Loader — outside the OmniStudio context.
