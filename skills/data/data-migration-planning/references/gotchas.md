# Gotchas — Data Migration Planning

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Validation Rules Fire for System Administrators and Integration Users

**What happens:** Every validation rule fires for every user, including users with the System Administrator profile, API-only users, and integration users. There is no built-in "admin bypass" for validation rules at the platform level. A migration load running under an admin user will fail on every record that violates an active validation rule — even if the rule was written for end-user data entry scenarios, not migration scenarios.

**When it occurs:** Any time a migration job loads records into an object that has active validation rules. Common examples: a rule requiring a picklist field to have a specific value, a rule requiring a related object to exist, or a rule enforcing a date constraint that source system records do not satisfy.

**How to avoid:** Build an explicit bypass before the migration starts. The preferred approach is a Custom Permission (e.g., `Bypass_Migration_Validation`) added to each validation rule's formula as `NOT($Permission.Bypass_Migration_Validation) AND (<original rule>)`. Assign the Custom Permission to the migration user via a Permission Set. Remove the Permission Set assignment after the migration completes. Never rely on profile alone to bypass validation rules.

---

## Gotcha 2: Text External ID Lookups Are Case-Sensitive

**What happens:** When Bulk API 2.0 resolves a relationship cross-reference using a Text-type External ID field (e.g., `Account.Legacy_CRM_Id__c`), the match is case-sensitive. If the Account was loaded with `Legacy_CRM_Id__c = "ACCT-001"` but the Contact CSV references `Account.Legacy_CRM_Id__c = "acct-001"`, Salesforce will not find the Account and the Contact insert will fail with "INVALID_CROSS_REFERENCE_KEY."

**When it occurs:** Any migration that uses text-based source system keys (most legacy systems) where the source data has inconsistent or mixed-case ID values. It also occurs when the source system export produces lowercase IDs but the parent was loaded with uppercase IDs, or vice versa.

**How to avoid:** Normalize all external ID values to a consistent case (all uppercase is recommended) in both the parent load file and all child load files before the migration starts. If using a Number-type External ID field, this problem does not apply because numbers are case-independent. Document the chosen casing convention in the migration plan.

---

## Gotcha 3: Inactive or Unlicensed Owner Assignments Cause Row-Level Failures That Look Like Partial Success

**What happens:** A Bulk API 2.0 job that includes records assigned to an inactive or unlicensed user does not fail the entire job — it fails only the affected rows. The job shows a "PartialSuccess" state. The error for each failed row is "INVALID_CROSS_REFERENCE_ID: invalid cross reference id" on the OwnerId field. Rows with valid owner assignments succeed. If the migration team does not check the error results file, they may believe the load completed correctly when in fact a portion of records was not created.

**When it occurs:** Any time the source system includes owner references (salesperson, assigned user, account manager) where some of those users have been deactivated in Salesforce or are not yet provisioned. This is especially common in CRM migrations where legacy sales reps have left the company and their Salesforce user accounts are inactive.

**How to avoid:** Before the migration, export `SELECT Id, Name, IsActive, UserType FROM User` from Salesforce. Cross-reference all owner IDs in the source data against this list. For records owned by inactive users, either re-assign to a designated placeholder active user ("Migration Owner"), or coordinate with the project team to temporarily reactivate the user for the migration window. Document the re-assignment mapping and plan for ownership correction after cutover.

---

## Gotcha 4: Formula Fields Cannot Be External ID Fields

**What happens:** External ID fields must be stored fields. Salesforce does not allow formula fields to be designated as External IDs, even if the formula computes a unique value that would be a perfect natural key. If a team designs their migration plan around using a formula-computed unique key as the upsert external ID, they discover this limitation only when trying to create the field — and must redesign the approach.

**When it occurs:** When the natural key in the source system is a concatenation of two or more fields (e.g., `{AccountNumber}-{ContactType}`) and the Salesforce data model uses a formula field to replicate this combined key. The formula field correctly computes the unique value, but the External ID checkbox is not available on formula field setup.

**How to avoid:** Always materialize natural keys into stored fields. Create a Text or Number field (not a formula), mark it External ID and Unique, and populate it explicitly in the migration load. If a formula-based unique key is the intent for ongoing use after migration, keep the formula field for display purposes but use a parallel stored field for upsert matching.

---

## Gotcha 5: Lookup Fields Reference Missing Parents Silently When the Lookup Is Not Required

**What happens:** A lookup relationship field that is not marked required on the record's page layout or field definition will allow inserts with a null or blank parent reference. If a child record's parent reference fails to resolve (because the parent was not yet loaded, the external ID cross-reference was wrong, or the parent load had errors), the Bulk API may insert the child record with a blank lookup field rather than failing the row — depending on the API version and configuration. The result is child records that appear in Salesforce but have no visible relationship to any parent.

**When it occurs:** Most commonly with lookup fields (as opposed to master-detail fields, which are always required and always block the insert on a missing parent). Affects Contact-to-Account lookups, Case-to-Contact lookups, and any custom lookup relationship where the field is optional.

**How to avoid:** After each load batch, run a SOQL integrity check against every migrated object to count records with blank lookup fields that should be populated:

```sql
SELECT COUNT(Id) FROM Contact
WHERE AccountId = null AND Legacy_CRM_Id__c != null
```

If the count is non-zero, investigate the parent load and re-upsert the affected child records with the correct parent reference. Include these integrity checks in the post-migration validation plan before it is formally approved.

---

## Gotcha 6: Triggers and Flows Bypass with a Custom Setting Flag Must Be Removed Promptly

**What happens:** The Custom Setting flag pattern (`Migration_In_Progress__c = true`) is highly effective at suppressing automation during loads. However, if the flag is not cleared after the migration completes, the suppression persists indefinitely. New records created by end users or other integrations after cutover will also have their trigger and flow logic bypassed, causing silent data quality failures — missing related record creation, missing notifications, missing field updates.

**When it occurs:** When the migration cutover is rushed, the post-migration checklist is incomplete, or the team member who set the flag is not the same person responsible for clearing it. Also occurs when multiple migration batches run across days and the flag is set and forgotten between runs.

**How to avoid:** Include "Clear `Migration_In_Progress__c` flag" as a mandatory, signed-off step in the migration runbook — not an optional checklist item. Assign a named person responsible for clearing the flag. After clearing it, run a test manual record save on each affected object and confirm that the expected automation (email, related record creation, field update) fires correctly. Document the flag status in the post-migration sign-off document.
