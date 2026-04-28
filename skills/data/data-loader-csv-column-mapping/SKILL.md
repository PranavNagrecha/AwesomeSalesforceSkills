---
name: data-loader-csv-column-mapping
description: "Mapping CSV columns to Salesforce field API names for Data Loader, dataloader.io, Workbench, and custom Bulk API V2 loads. Covers header normalization, missing/extra-column behaviour per tool, required-field detection from describe metadata, polymorphic lookup prefixes, External ID upsert binding, picklist API names vs labels, datetime/timezone handling, and the case-sensitivity divergence between Data Loader (insensitive match) and Bulk API V2 (case-sensitive headers). NOT for picklist value validation pre-load — see data-loader-picklist-validation-pre-load. NOT for batch sizing — see data-loader-batch-window-sizing. NOT for general migration planning — see data-migration-planning."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
  - Operational Excellence
  - Scalability
tags:
  - data-loader
  - csv
  - column-mapping
  - bulk-api
  - external-id
  - upsert
  - polymorphic-lookup
  - sdl
  - dataloader-io
  - workbench
triggers:
  - "data loader load succeeded but some fields are blank in salesforce"
  - "bulk api v2 job failed with InvalidBatch unknown column"
  - "csv column header case sensitivity data loader vs bulk api"
  - "how do I map csv column to lookup using external id"
  - "task whoid polymorphic lookup csv import"
  - "saved sdl mapping file data loader"
  - "picklist label vs api name csv data loader load"
  - "datetime timezone wrong after csv import"
  - "managed package namespaced field csv mapping"
  - "data loader silently dropped column"
inputs:
  - CSV header row (or sample CSV) being loaded
  - Target SObject API name and field describe (real or mocked)
  - Tool of record — Data Loader, dataloader.io, Workbench, or custom Bulk API V2 client
  - Operation — insert / update / upsert / hard-delete and any External ID field
  - Org context — managed package namespaces present, locale, default user timezone
outputs:
  - Header-to-field-API-name mapping plan with type-compatibility notes
  - Saved `.sdl` mapping file pattern (Data Loader) or equivalent JSON config
  - Required-field gap report from describe metadata
  - Polymorphic lookup prefix decisions (e.g. `WhoId` → Lead vs Contact via `Type` column)
  - Pre-load checker run summarising missing/extra/case/type/polymorphic issues
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Data Loader CSV Column Mapping

Activate this skill before any CSV load — Data Loader, dataloader.io, Workbench, or a custom Bulk API V2 client — to lock down the column-to-field binding before a single row is sent. The cost of a wrong mapping is rarely a hard error: it is a "successful" job that silently dropped fields because of FLS, header case mismatches, polymorphic lookups missing a type prefix, or picklist labels submitted where API names were required.

This is NOT a picklist value validator (see `data/data-loader-picklist-validation-pre-load`), NOT a batch-window tuning skill (see `data/data-loader-batch-window-sizing`), and NOT a full migration planner (see `data/data-migration-planning`).

---

## Before Starting

Gather this context before mapping a single column:

- Which tool will run the load? Data Loader (CLI or UI), dataloader.io, Workbench, or a custom Bulk API V2 caller? Mapping rules differ.
- Is the operation `insert`, `update`, `upsert` (with which External ID field?), or `hardDelete`? Required fields differ per operation.
- Has a fresh **describe** of the target SObject been pulled? Field types, nillable flags, default values, picklist API names, controlling-field metadata, and reference-target lists must come from describe, not from a screenshot of a setup page.
- Is the CSV authored in a locale where date or number formatting differs from the API expectation (`yyyy-MM-dd`, ISO 8601 datetime, `.` decimal separator)?
- Is the loading user's profile timezone the one you want applied to naive datetimes? Bulk API V2 silently coerces a CSV `2026-04-28T09:00:00` (no offset) to the loading user's profile timezone — not the org default.
- Are managed packages installed that prefix fields with a namespace (e.g. `npe01__Payment_Method__c`)? Spell the prefix in the header — Data Loader will not infer it.

The most common wrong assumption: "the load succeeded so the data is correct." A Bulk API V2 success means rows were accepted by the database, not that every column you intended to populate actually wrote a value. FLS-hidden fields, blank cells, picklist label submissions, and silently-ignored columns all produce green job results.

---

## Core Concepts

### CSV header is a contract, not a hint

Every load tool resolves a CSV header against the target object's field API names. The resolution rules diverge:

- **Data Loader (Java client and CLI)** matches headers case-insensitively against field API names and against pre-saved `.sdl` mappings. Unknown headers are quietly dropped at mapping time unless you have a `.sdl` that explicitly references them.
- **dataloader.io** is browser-based and behaves like Data Loader for case-insensitivity but persists mappings in the cloud project, not in a local file.
- **Workbench Insert/Upsert** matches case-insensitively but offers no saved-mapping file — every load re-maps.
- **Bulk API V2 (REST `/jobs/ingest`)** is **strict and case-sensitive**. The header `accountid` does not match the field `AccountId` and the row will return `InvalidBatch` or write `null`. Extra columns are also rejected — V1 was tolerant, V2 is not.

If the same CSV will be loaded by both Data Loader and a custom Bulk API V2 client (a common dev/prod split), **author the header in the exact field API name casing** and assume the strictest rule wins.

### Required fields and the describe round-trip

Salesforce required-ness for a load is the union of:

1. `nillable=false` and `defaultedOnCreate=false` on the field describe.
2. `createable=true` (for insert) or `updateable=true` (for update) — non-createable system fields like `CreatedDate` cannot be mapped on insert without `setAuditFields` permission.
3. Validation rules referencing the field (only enforceable at runtime, but plannable from rule metadata).
4. Master-detail relationships — the parent ID is required and populating it via header is mandatory.
5. Record types — when multiple are active for the user, `RecordTypeId` is effectively required for predictable picklist behaviour.

Pull `describeSObjectResult` once, drive the rest of the mapping from it. Never hand-curate a list of "required fields" from screenshots.

### Default values do NOT fire for blank CSV cells

A field with `Default Value = TODAY()` or a static literal on a custom field **does not** populate when the CSV column for that field is present and the cell is blank. The blank cell is treated as an explicit empty string (in V2) or `#N/A` is required for a true null (in V1). The default fires only when the field is absent from the load request entirely. Practical consequence: if you want the org default to apply, **do not include the column in the CSV** — do not include it with empty cells.

### Null vs empty string vs `#N/A`

- **Bulk API V1** (legacy SOAP-style batches): a blank cell means "leave field as-is on update" or "use field default on insert." To explicitly null a field on update, write `#N/A` in the cell. Data Loader UI exposes the "Insert Null Values" checkbox, which translates blank cells to nulls — but only for Bulk V1.
- **Bulk API V2**: there is no `#N/A` convention. A blank cell on update means "set the field to null" (always). On insert, a blank cell on a nillable field stores null, and on a non-nillable field the row errors.
- Empty string vs null on text fields: most text fields normalise empty string to null on the server. Long Text Area fields preserve empty string in some org configurations — never rely on the difference; treat both as null.

### Polymorphic lookup needs a type prefix

`Task.WhoId` (Lead or Contact) and `Task.WhatId` (Account, Opportunity, custom...) are polymorphic. A bare 18-character ID works because the prefix encodes the type, but **External ID upsert** on a polymorphic field requires the explicit relationship column form:

```
Who.Lead.External_Id__c
Who.Contact.External_Id__c
```

Submitting just `Who.External_Id__c` without naming the target type is invalid — the API has no way to choose between `Lead` and `Contact`.

### Reference-field resolution by External ID

To bind a lookup without pre-resolving the target ID:

- Header form: `<RelationshipName>.<TargetExternalIdField>` — e.g. `Account.External_Account_Id__c` to populate `Contact.AccountId`.
- The relationship name is the **relationship API name** (singular for lookups, plural-form rule does not apply here), not the field API name. `AccountId` (field) → `Account` (relationship).
- The target External ID field must have `External ID = true` and `Unique = true`. Non-unique External IDs cause non-deterministic matches and the job will error per row.
- For self-referential parent links (Account hierarchy via `ParentId`): the relationship name is `Parent` — header is `Parent.External_Account_Id__c`.

### Picklist values: API name, never label

Translated orgs and picklists with global value sets often have labels that differ from API names. The load API stores the **API name**. Submitting the label may succeed (because picklists are validated at the storage level only when `Restrict picklist to the values defined in the value set` is on) and write the label as a free-text value — visible in the UI but not selectable, and not matching any reporting filter.

### Record Type ID lookup

`RecordTypeId` cannot be looked up by name in Bulk API V2. Either:

1. Pre-resolve the Id via SOQL (`SELECT Id FROM RecordType WHERE SObjectType='Account' AND DeveloperName='Customer'`) and hard-code in the CSV; or
2. Use `RecordType.DeveloperName` as the External-ID-style header — supported in Data Loader and dataloader.io, **not** in raw Bulk API V2 ingest endpoints.

---

## Common Patterns

### Pattern A: Strict-header CSV, single source of truth

**When to use:** any production load, especially when the same CSV will flow through multiple tools (e.g. Data Loader for spot fixes, Bulk API V2 for the bulk run).

**How it works:**

1. Pull a fresh describe of the target SObject.
2. Author the CSV header using exact field API name casing — `Id`, `AccountId`, `Custom_Field__c`, namespaced where applicable.
3. Run `scripts/check_data_loader_csv_column_mapping.py` against the header + describe to surface missing/extra/case/type/polymorphic issues.
4. Save the mapping as a `.sdl` file (Data Loader) or pinned project mapping (dataloader.io) so re-loads do not re-prompt.

**Why not the alternative:** loose-cased headers work in Data Loader but break the moment the CSV is replayed through Bulk API V2 directly — and they always break in CI pipelines that call `sfdx force:data:tree:import` or the REST ingest endpoint.

### Pattern B: External ID upsert with type-explicit polymorphic columns

**When to use:** loading Tasks, Activities, or any polymorphic lookup where targets exist in multiple objects.

**How it works:**

```
Subject,Status,Who.Contact.Email,Who.Lead.Email,What.Account.External_Account_Id__c
"Follow up","Completed",alice@example.com,,EXT-12345
"Trial signup","In Progress",,bob@example.com,
```

Each row populates exactly one of the `Who.Contact.Email` or `Who.Lead.Email` columns. The empty cell on the unused side is fine — the API resolves the populated one. Both columns must use a unique, indexed External ID field (`Email` is implicitly indexed and serves as External ID for Lead/Contact in many orgs).

**Why not the alternative:** a single `WhoId` column with raw IDs forces the consumer of the CSV to pre-resolve every ID, which is exactly the work upsert was designed to skip.

### Pattern C: `.sdl` saved mapping for repeatable Data Loader runs

**When to use:** scheduled Data Loader CLI jobs (e.g. nightly Account sync from an upstream system).

**How it works:** a `.sdl` file is a plain-text, line-per-mapping file in the form `<csv_header>=<field_api_name>`. Lines without `=` are flagged as "ignore." Example:

```
# Account sync — Data Loader CLI, run nightly
External_Id=External_Account_Id__c
Account_Name=Name
Industry=Industry
Owner_Email=Owner.User.Email__c
Parent_Account_Ext_Id=Parent.External_Account_Id__c
# Source field intentionally not loaded:
Source_Region=
```

Empty right-hand side after `=` is the canonical "this column exists in the CSV but do not map it" signal. **Required for any CLI job** because the headless run cannot prompt for unknown columns.

**Why not the alternative:** without a `.sdl`, a Data Loader CLI run with an unmapped CSV column produces an error in some versions and silently ignores it in others. Always pin the mapping.

---

## Decision Guidance

Compare the four mainstream tools on column-mapping behaviour. Pick the row that matches the loader you must actually use, and let the strictest constraint win for the CSV you author.

| Behaviour | Data Loader (UI/CLI) | dataloader.io | Workbench | Bulk API V2 (raw `/jobs/ingest`) |
|---|---|---|---|---|
| Header case sensitivity | Insensitive | Insensitive | Insensitive | **Strictly case-sensitive** |
| Extra columns in CSV | Tolerated, dropped at mapping | Tolerated | Tolerated | **Rejected — `InvalidBatch`** |
| Missing required fields | Caught pre-load via describe | Caught pre-load | Caught at row error | Caught at row error only |
| Saved mapping file | `.sdl` file (local) | Cloud project mapping | None — re-map every time | Caller's responsibility |
| Polymorphic External ID syntax | `Who.Lead.<ExtId>` supported | Supported | Supported | Supported |
| Record Type by DeveloperName | Supported via `RecordType.DeveloperName` header | Supported | Supported | **Not supported — pre-resolve Id** |
| Blank cell on update (Bulk V1 mode) | Leaves field unchanged unless "Insert Null Values" set | Same | N/A | N/A |
| Blank cell on update (Bulk V2 mode) | **Sets field to null** | Same | Same | **Sets field to null** |
| `#N/A` for explicit null | Honoured in V1 mode only | Honoured in V1 mode only | Honoured in V1 mode only | **Not interpreted — written literally** |
| Datetime without timezone | Loading user's profile TZ applied | Same | Same | Same |
| Namespace-prefixed fields | Must include prefix in header | Same | Same | Same |
| Best for | Ad hoc and scheduled CLI jobs | Browser-only ops, light scheduling | One-off admin tasks | High-throughput automated pipelines |

When the same CSV must work across all four, author it for **Bulk API V2** rules — case-exact headers, no extra columns, no `#N/A` sentinels — and the looser tools will accept it unchanged.

---

## Recommended Workflow

1. Pull a fresh describe of the target SObject (`sf sobject describe -s Account` or REST `/services/data/vXX.X/sobjects/Account/describe`) — capture field API names, types, nillable, defaultedOnCreate, picklist values, and reference targets.
2. Inventory the source CSV — list every header, sample first 5 rows for each column, note locale-sensitive formats (date, decimal, boolean).
3. Build the mapping table — header → field API name → type → required? → notes (polymorphic, External ID, picklist label-vs-name risk).
4. Run `scripts/check_data_loader_csv_column_mapping.py --csv-header <hdr> --describe-json <describe.json> --target-tool bulkv2` and fix every reported issue before loading.
5. Persist the mapping — save a `.sdl` for Data Loader CLI, or commit the JSON-equivalent for the Bulk API V2 caller. Treat it as code, version-controlled.
6. Dry-run on a sandbox with a 50-row sample. Spot-check the loaded records in the UI for blank fields you expected populated (FLS / silent drops).
7. Diff post-load — query back the loaded records and compare key fields against the CSV. A green job result is necessary but not sufficient.

---

## Review Checklist

Run through these before any CSV load is considered complete:

- [ ] Describe of the target SObject was pulled fresh, not copied from earlier notes
- [ ] CSV header uses exact field API name casing (assume case-sensitive)
- [ ] Every required field on the chosen operation is present in the CSV (or intentionally relying on field default with the column omitted entirely)
- [ ] Polymorphic lookup columns use the explicit `Who.<Type>.<ExtIdField>` form
- [ ] External ID fields used for upsert are `External ID = true` and `Unique = true`
- [ ] Picklist columns contain API names, not translated labels
- [ ] `RecordTypeId` is pre-resolved (or the tool supports `RecordType.DeveloperName`)
- [ ] Datetime columns include timezone offset OR you have explicitly verified the loading user's profile TZ
- [ ] Namespace-prefixed fields use the full prefix in the header
- [ ] Mapping is persisted as `.sdl` or equivalent and committed to source control
- [ ] Post-load diff query confirms expected fields populated (no FLS-induced silent drops)

---

## Salesforce-Specific Gotchas

1. **Bulk API V2 case sensitivity** — `accountid` does not match `AccountId`. The row errors with `InvalidBatch` or, depending on client, the column is silently dropped. Data Loader users porting CSVs to a CI pipeline hit this every time.
2. **Field default does not fire for blank cells** — a `Default Value = TODAY()` field stays null if the column is in the CSV with a blank cell. Drop the column from the CSV entirely to let the default apply.
3. **Datetime without timezone applies the loading user's TZ silently** — `2026-04-28T09:00:00` loaded by a user with `America/Los_Angeles` profile TZ is stored as `2026-04-28T16:00:00Z`. Always include the offset (`...09:00:00-07:00`) or explicit `Z`.
4. **Picklist labels accepted in unrestricted picklists** — if "Restrict picklist to the values defined in the value set" is off, submitting a label writes the label as free text. The record looks fine in the UI but never matches a filter on API name.
5. **Polymorphic upsert without type prefix is rejected** — `Who.External_Id__c` without `Lead` or `Contact` in the path is an invalid header. Always disambiguate.
6. **Self-referential parent uses `Parent`, not the field name** — for Account hierarchy, the External ID upsert header is `Parent.External_Account_Id__c`, not `ParentId.External_Account_Id__c`.
7. **FLS-hidden fields drop silently** — the loading user's profile must have field-level Edit on every column. Hidden fields produce a green load with the column unwritten and no per-row error.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Mapping plan | Header → field API name table with type, required, polymorphic, and External ID notes |
| `.sdl` mapping file | Persisted Data Loader mapping for repeatable CLI runs (templates/data-loader-csv-column-mapping-template.md) |
| Pre-load checker run | `scripts/check_data_loader_csv_column_mapping.py` clean exit |
| Post-load diff query | SOQL spot-check confirming key fields populated |

---

## Related Skills

- `data/data-loader-picklist-validation-pre-load` — validate picklist values against the active value set before the load runs
- `data/data-loader-batch-window-sizing` — choose Bulk API V2 batch size and concurrency
- `data/data-loader-and-tools` — selecting between Data Loader, dataloader.io, Workbench, and custom clients
- `data/external-id-strategy` — designing External ID fields for upsert binding
- `data/data-migration-planning` — full migration sequencing, including dependency order
