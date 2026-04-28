# Data Loader CSV Column Mapping — Pre-Load Template

Use this template before any CSV load. Fill in every section. Treat it as the runbook artefact that gets attached to the change record.

---

## Scope

**Skill:** `data-loader-csv-column-mapping`

**Request summary:** (fill in — what data is being loaded, into what object, why)

**Tool of record:** [ ] Data Loader UI  [ ] Data Loader CLI  [ ] dataloader.io  [ ] Workbench  [ ] Custom Bulk API V2 client

**Operation:** [ ] insert  [ ] update  [ ] upsert (External ID field: __________)  [ ] hardDelete

**API mode:** [ ] Bulk API V1 (`#N/A` sentinel honoured)  [ ] Bulk API V2 (blank cell = null)

**Source CSV path / system of record:** ____________

**Target object API name:** ____________

**Loading user (and profile/permset):** ____________  TZ: ____________

---

## Pre-Load Checklist

Run through every box. Empty = blocking.

- [ ] Fresh `describe` of the target SObject pulled (paste path to JSON or command):
      `sf sobject describe -s <Object> --json > describe.json`
- [ ] CSV header uses **exact field API name casing** (`AccountId`, not `accountid`)
- [ ] All required fields for the chosen operation are present in the CSV — or intentionally omitted to let the field default fire
- [ ] No "present-but-blank" columns where the intent is "use the default" (drop the column instead)
- [ ] Polymorphic lookups use the explicit type form (`Who.Lead.<ExtId>`, `What.Account.<ExtId>`)
- [ ] External ID fields used for upsert binding are `External ID = true` AND `Unique = true` — verified from describe, not from setup screenshots
- [ ] Picklist columns contain **API names**, not translated labels — translation table built and applied
- [ ] `RecordTypeId` is pre-resolved (or the chosen tool supports `RecordType.DeveloperName`)
- [ ] Datetime columns include explicit timezone offsets, OR the loading user's profile TZ matches the CSV's implicit TZ (and that assumption is documented here: __________)
- [ ] Namespace-prefixed fields use the full prefix in the CSV header (`npe01__Payment_Method__c`, `npsp__Soft_Credit__c`)
- [ ] FLS check: the loading user has Edit on every mapped field — verified via permission set / profile review
- [ ] Sample 50-row dry run completed in sandbox; spot-checked records in the UI for unexpected null fields
- [ ] Pre-load checker run: `python3 scripts/check_data_loader_csv_column_mapping.py --csv-header <path> --describe-json <path> --target-tool <tool>` — exits 0
- [ ] Mapping persisted as `.sdl` (Data Loader) or JSON config (Bulk V2 caller) and committed to source control

---

## Standard `.sdl` Mapping Pattern

For Data Loader CLI (`process-conf.xml`-driven) jobs, save a `.sdl` file alongside the CSV. Form is `<csv_header>=<field_api_name>` per line.

```
# <object> sync — Data Loader CLI, run <cadence>
# CSV: <csv_path>
# Operation: <insert|update|upsert>
# External ID field (upsert only): <field_api_name>

# Identity / External ID columns
External_Id=External_<Object>_Id__c

# Direct field mappings (left = CSV header, right = field API name)
Name=Name
Custom_Text=Custom_Text__c
Owner_Email=Owner.User.Email__c

# Lookup binding via External ID
Account_Ext_Id=Account.External_Account_Id__c

# Polymorphic lookup — pick exactly one per row
Who_Lead_Email=Who.Lead.Email
Who_Contact_Email=Who.Contact.Email

# Source columns intentionally NOT loaded (right-hand side empty)
Source_Region=
Audit_Notes=
```

Rules:

- One mapping per line. No quoting.
- A line with no `=` is invalid (some Data Loader versions error, others silently skip).
- A line with empty right-hand side (`Source_Region=`) means "this column is in the CSV but do not map it" — required when the source CSV has columns you do not want to load.
- Comments start with `#` and are ignored.
- The `.sdl` is referenced from `process-conf.xml` via `<entry key="sfdc.entity" value="<Object>"/>` and `<entry key="dataAccess.fileMappingFilename" value="path/to/file.sdl"/>`.

---

## Cross-Tool Equivalent (Bulk API V2 caller)

If the load runs through a custom Bulk V2 client, persist the same mapping as JSON next to the CSV in the repo:

```json
{
  "object": "<Object>",
  "operation": "upsert",
  "externalIdFieldName": "External_<Object>_Id__c",
  "lineEnding": "LF",
  "columnDelimiter": "COMMA",
  "fieldMapping": {
    "External_Id": "External_<Object>_Id__c",
    "Name": "Name",
    "Custom_Text": "Custom_Text__c",
    "Account_Ext_Id": "Account.External_Account_Id__c",
    "Who_Lead_Email": "Who.Lead.Email",
    "Who_Contact_Email": "Who.Contact.Email"
  },
  "ignoredColumns": ["Source_Region", "Audit_Notes"]
}
```

The CSV that the client uploads must have its header **renamed** to the right-hand-side field API names — Bulk V2 ingest does not honour a separate field-mapping file. The mapping JSON is purely for the pre-upload transform step in your client.

---

## Post-Load Verification

After the job completes:

- [ ] Job result captured: `state`, `numberRecordsProcessed`, `numberRecordsFailed`, any failed-row CSV
- [ ] Diff query executed against a representative sample of loaded records:
      ```sql
      SELECT Id, <key fields>
      FROM <Object>
      WHERE Id IN (<sample of loaded Ids>)
      ```
- [ ] 20+ rows manually compared CSV-vs-Salesforce — no silent drops on any mapped column
- [ ] If upsert: verify `numberRecordsProcessed` matches expected insert + update split
- [ ] Sign-off recorded by data owner

---

## Notes / Deviations

(Record any deviations from the standard pattern, the reason, and the approver.)
