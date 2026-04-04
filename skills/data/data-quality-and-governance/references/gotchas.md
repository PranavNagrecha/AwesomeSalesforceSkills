# Gotchas — Data Quality and Governance

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Field History Does Not Capture the Initial Value Set at Record Creation

**What happens:** When a record is created, the value placed in a field at creation time is NOT written to the `XxxHistory` object. The first history row for that field appears only after the field is edited for the first time after creation. If a record is never edited, there is no history row at all. Querying `AccountHistory` for a newly-created account returns zero rows, even though the account has field values.

**When it occurs:** Any time you rely on `XxxHistory` to answer the question "what was the original value of this field when the record was created?" This gap affects compliance audits, contract start values, and any workflow that needs to confirm what was entered initially.

**How to avoid:** For fields where the initial value is compliance-critical (e.g., `KYC_Status__c`, `Contract_Start_Date__c`, `AUM_Amount__c`), implement an Apex trigger on `after insert` that writes the initial values to a custom audit object (e.g., `Field_Audit_Entry__c`). This is a deliberate, permanent supplement to platform-provided field history, not a workaround to be removed later.

---

## Gotcha 2: Validation Rules Fire on Every API Save — Including Bulk Loads

**What happens:** Validation rules have no concept of "UI only." Every operation that causes a record save — REST API, SOAP API, Apex DML, Bulk API v1, Bulk API 2.0, Flow, Process Builder — triggers all active validation rules for the affected fields. A rule designed for user-entered data will fire identically during a data migration.

**When it occurs:** Data migration loads, integration upsert jobs, scheduled ETL runs, any batch that touches fields covered by validation rules. Rules that enforce data completeness standards appropriate for new records (e.g., "Stage must have a Close Reason") will reject historical records that predate that field.

**How to avoid:** Implement the Custom Permission bypass pattern before any bulk operation. Create a `Bypass_Validation_Rules` Custom Permission, wrap every validation rule formula with `AND(NOT($Permission.Bypass_Validation_Rules), <original_formula>)`, assign the permission to the integration/migration user via a dedicated Permission Set, and revoke it immediately after the load completes. Never use a profile-based check (`$Profile.Name`) as a bypass — it is permanent and unauditable.

---

## Gotcha 3: Duplicate Rules Are Bypassed by Apex DML by Default

**What happens:** Inserting or updating records via Apex (`insert myList;` or `Database.insert(myList)`) completely bypasses all Duplicate Rules, regardless of how those rules are configured. No duplicate alert is shown, no block occurs, duplicates are created silently.

**When it occurs:** Any Apex code that creates or updates records — triggers, batch jobs, scheduled jobs, controller logic, API endpoint handlers. This is especially dangerous in orgs that have Block-mode Duplicate Rules configured and assume those rules protect against all paths of data entry.

**How to avoid:** Set `Database.DMLOptions.DuplicateRuleHeader.allowSave = false` on the DML options object before performing the insert or update:

```apex
Database.DMLOptions opts = new Database.DMLOptions();
opts.DuplicateRuleHeader.allowSave = false;
opts.DuplicateRuleHeader.runAsCurrentUser = true;
Database.SaveResult[] results = Database.insert(recordList, opts);
```

Review `SaveResult` for duplicate errors. For read-only duplicate detection without a save, use `Database.findDuplicates(recordList)` instead.

---

## Gotcha 4: Bulk API 2.0 Cannot Trigger Duplicate Rules Under Any Circumstances

**What happens:** Unlike Bulk API v1 (which has limited Duplicate Rule support via `DMLOptions`), Bulk API 2.0 does not support `DMLOptions` at all. Duplicate Rules are completely silenced for any load job submitted via Bulk API 2.0, and there is no configuration option to change this.

**When it occurs:** Data Loader (when configured to use Bulk API 2.0), third-party ETL tools that default to Bulk API 2.0 for performance, any integration that uses the `/services/data/vXX.0/jobs/ingest` endpoint.

**How to avoid:** Run deduplication as a separate step before or after the load. Options:
- Pre-load: deduplicate the source data file using an external tool or a SOQL-based lookup before submitting the job.
- Post-load: query `DuplicateRecordSet` and `DuplicateRecordItem` objects and remediate programmatically or via a scheduled batch.
- For integrations where real-time duplicate prevention is required, use the REST API (single record or collection) with `DMLOptions` instead of Bulk API 2.0.

---

## Gotcha 5: Shield Platform Encryption Breaks SOQL LIKE Searches and Full-Text Search (SOSL)

**What happens:** Fields encrypted with probabilistic encryption (the default Shield encryption mode) produce a different ciphertext every time the same plaintext is encrypted. This means SOQL `LIKE` queries, wildcard searches, and SOSL full-text searches on encrypted fields return no results. The field is not searchable.

**When it occurs:** After enabling Shield Platform Encryption on a field (e.g., `Email`, `Phone`, `SSN__c`), any SOQL query using `LIKE '%smith%'` on that field returns zero rows even though matching data exists.

**How to avoid:** Before enabling encryption on a field, audit all SOQL queries and reports that filter or search that field. If search capability is required, use deterministic encryption (available in Shield) which enables exact-match SOQL (`=` operator only — not `LIKE`). If full-text search is required and cannot be removed, do not encrypt the field with Shield — use field-level security (FLS) and masking instead, and accept that the stored value is not encrypted at rest. Document this decision in the data classification register as a known compensating control.

---

## Gotcha 6: Cross-Object Validation Rules Are Limited to One Relationship Level

**What happens:** A validation rule on `Opportunity` can traverse one relationship hop (e.g., `Account.Type`), but cannot traverse two hops (e.g., `Account.Parent.Type`). Attempting to reference a grandparent field causes a compile error: "Error: Compile Error: Field Account.Parent.Type does not exist or is not accessible."

**When it occurs:** Complex org hierarchies (Account hierarchies, channel partner structures, territory models) where a child record's validity depends on grandparent-level attributes.

**How to avoid:** For two-level cross-object validation requirements, use an Apex trigger. The trigger can traverse the full relationship chain via SOQL and throw a `DMLException` with a custom message, which surfaces to the user identically to a validation rule error. Alternatively, denormalize the relevant grandparent attribute into a formula field on the direct parent and reference that formula field in the validation rule (staying within one hop).

---

## Gotcha 7: Data Sensitivity Level Metadata Is Not Enforced — It Is Metadata-Only

**What happens:** Setting `Data Sensitivity Level = Restricted` on a field in Setup does NOT restrict access to that field. It does not automatically apply FLS, sharing rules, or encryption. Users with field-level access to the field can still read and write it regardless of the Sensitivity Level setting.

**When it occurs:** Any time a team treats the Data Sensitivity Level attribute as a security control rather than a classification label. Compliance teams may assume "we've marked it Restricted, so it's protected" without realizing no enforcement has occurred.

**How to avoid:** Use `Data Sensitivity Level` as a classification and discovery tool only. For actual enforcement, combine it with: FLS restrictions via Permission Sets (restrict read/edit access), Shield Platform Encryption (encrypt at rest), and Event Monitoring (Shield) to audit who accessed the field. The classification attribute is input to your governance process, not a substitute for security controls.
