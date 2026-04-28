---
name: data-loader-picklist-validation-pre-load
description: "When and how to pre-validate a CSV against Salesforce picklist rules and record-type assignments BEFORE running a Data Loader / Bulk API insert or upsert — restricted picklists, record-type-scoped values, inactive values, Global Value Sets, dependent picklists, multi-select delimiters, API name vs label, and the 255-char per-value limit. NOT for post-load reconciliation, NOT for general Data Loader column mapping (see data-loader-csv-column-mapping), NOT for choosing between Data Loader and Bulk API (see bulk-api-and-large-data-loads)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - data-loader
  - picklist
  - record-type
  - validation
  - csv
  - bulk-api
  - global-value-set
  - dependent-picklist
triggers:
  - "data loader rejecting picklist values that look correct"
  - "csv has industry values that fail to load on accounts with custom record types"
  - "bulk insert returning INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST or BAD_VALUE_FOR_RESTRICTED_PICKLIST"
  - "multi-select picklist comes through as a single concatenated string after load"
  - "historical data with retired picklist values needs reloading"
  - "how do I check picklist values per record type before a data load"
inputs:
  - CSV file ready to load (path, header row, sample rows)
  - Target SObject(s) and their picklist fields
  - Per record type allowed values for each picklist (or describe metadata to derive them)
  - Whether each picklist is restricted, dependent, multi-select, or backed by a Global Value Set
  - Mapping between RecordTypeId or RecordType.DeveloperName and the rows in the CSV
outputs:
  - Pre-load picklist validation report listing rows + columns where the value is invalid for the assigned record type
  - List of inactive / retired values that the load will reject
  - List of dependent-picklist combinations that violate the controlling-field rule
  - Multi-select fields that use the wrong delimiter
  - Recommended remediation per finding (rename, remap to valid value, temporarily activate, switch to API name, fix delimiter)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Data Loader Picklist Validation (Pre-Load)

Activate this skill when an inbound CSV is about to be sent through Data Loader, Workbench, or the Bulk API and the destination SObject has **restricted picklists, record-type-scoped picklists, dependent picklists, multi-select picklists, or Global Value Sets**. The goal is to run a deterministic pre-load check that surfaces every row + column whose value will be rejected (or silently truncated) by the platform — before the load runs, not from the error CSV after.

This is NOT a general Data Loader CSV mapping skill (see `data/data-loader-csv-column-mapping`), NOT a batch-window sizing skill (see `data/data-loader-batch-window-sizing`), and NOT a post-load reconciliation skill. It assumes the column mapping is already correct and the question is "will the *values* survive the load?".

---

## Before Starting

Gather this context before validating:

- The CSV path, header row, and a representative sample of rows. Confirm the file uses UTF-8 (Data Loader's default) — encoding mismatches turn the picklist validation problem into a "looks identical but is not" problem.
- Every picklist field you intend to load, plus its **type**: standard picklist, restricted picklist, multi-select picklist, dependent picklist, or Global Value Set-backed picklist.
- The **record type assignment per row**. The CSV either carries a literal `RecordTypeId`, a `RecordType.DeveloperName` external-ID upsert key, or — most commonly — assumes the org default. The default does not save you here: the org default record type still narrows picklist value sets.
- The **active / inactive** status of every value. Salesforce keeps inactive values queryable on existing records but **rejects them on insert and update**. Historical reloads frequently fail on values that were deactivated years ago.
- For dependent picklists: the controlling field (a checkbox or another picklist) and the dependency matrix. The controlling-field value must be a valid combination for the dependent-field value, **per record type**.

The most common wrong assumption is "if it's in the CSV and the field is a picklist, it'll go in." Restricted picklists, record-type filters, inactive values, and dependent-field rules all reject values that look syntactically valid.

---

## Core Concepts

### Restricted vs unrestricted picklists

A picklist field with `restrictedPicklist: true` rejects any value not in the active list with `BAD_VALUE_FOR_RESTRICTED_PICKLIST`. A picklist with `restrictedPicklist: false` will silently accept arbitrary values via API (Data Loader, REST, Bulk), even though the UI hides them — those values become "non-conforming" and never appear in the dropdown again. Restricted is the default for new custom picklists in modern API versions; some legacy custom picklists are still unrestricted, so confirm via metadata describe rather than guessing.

### Record-type-scoped picklist values

`Account.Industry` may have 30 platform-level values, but a record type named `Healthcare` may only expose `Healthcare`, `Biotechnology`, and `Hospitals & Clinics` for that picklist. A row with `Industry = Manufacturing` AND `RecordTypeId = <Healthcare RT>` is invalid even though `Manufacturing` is a perfectly valid Industry value at the field level. The API behaviour is:

- For **restricted** picklists: insert is rejected.
- For **unrestricted** picklists: insert may succeed but the value is non-conforming (will not show in the page layout, will fail next edit).

Both cases are bugs you want caught before load. Pre-load validation must therefore key off `(SObject, field, recordTypeDeveloperName) -> allowedValues`, not `(SObject, field) -> allowedValues`.

### Inactive picklist values

Salesforce treats picklist values as soft-deleted: deactivating a value keeps it visible on existing records but removes it from inserts and updates. Historical / archive loads regularly fail on values like `Suspect` that were retired five years ago. The fix is either:

1. **Temporarily reactivate** the value, run the load, deactivate again — this preserves history but requires careful scheduling and changeset tracking.
2. **Remap** the retired value to a current equivalent in the CSV before load.

Choose by data-faithfulness need. Reporting on the historical state of "Suspect" later requires option 1.

### Global Value Sets (GVS)

A Global Value Set is a single source of truth for shared picklists across multiple fields and SObjects. Adding a value to a GVS adds it everywhere instantly; deactivating a value at the GVS level cascades. When validating, treat every GVS-backed field as pointing to the same allowed-values map keyed by GVS API name. Pre-load validation should warn if a CSV column references a value that exists in a GVS but is **inactive at the GVS level** — the field-level metadata describe alone may not reveal this.

### Dependent picklists

A dependent picklist is gated by a controlling field. Example: `Account.Sub_Industry__c` depends on `Account.Industry`. Rules:

- The controlling-field value must be present in the same row (or already on the record for an update).
- The (controlling, dependent) pair must be valid in the dependency matrix **for that record type**.
- A null or blank controlling value typically means no dependent value is allowed (depends on metadata setup).

Bulk loads frequently violate this when the CSV is sorted by dependent value, the controlling field is computed by formula, or the controlling field is loaded in a separate pass.

### Multi-select picklist delimiter

Multi-select picklists use **`;` semicolon** as the value separator on input — NOT a comma. CSVs naturally use comma as a column separator, so a row like `Tags__c = "Healthcare,Finance"` ends up as a single value `"Healthcare,Finance"` (which then fails as a non-existent value). The correct shape is `Tags__c = "Healthcare;Finance"`. Tools that auto-quote will often help mask the problem until the load fails.

### API name vs label

Picklist values have a stored API name (the canonical value used by the Apex/SOQL/REST layer) and a label (the localised string shown in the UI). Up to and including the value's first save, label == API name; after a label rename, they diverge. **Loads must use API names**. A CSV exported from one org and loaded into another may break here: the source org may have renamed labels while the API name stayed the same, or vice versa. Pre-load validation should compare against API names only and flag mismatches.

### Sorting and the 255-char limit

Picklist values are returned alphabetically by default in API responses; the custom display order is UI-only metadata. This affects validation: do not assume the *order* in the metadata matches the *order* in the page layout. Also, every picklist value is capped at **255 characters** — long inbound values from external systems can exceed this and silently truncate or fail.

---

## Common Patterns

### Pattern 1 — Describe-driven per-RT picklist map

**When to use:** every pre-load validation. This is the foundation pattern.

**How it works:** call the platform describe API (e.g. `Schema.SObjectType.Account.getRecordTypeInfos()` plus `getPicklistValues()`, or the Tooling/Metadata API) to build a JSON map of `{ "Account": { "Industry": { "<RT_DeveloperName>": ["Manufacturing", "Healthcare", ...] } } }`. Persist this map alongside the CSV and feed both into `scripts/check_data_loader_picklist_validation_pre_load.py`. The script then validates each row against the slice of the map that matches the row's record type.

**Why not the alternative:** hardcoding "valid Industry values" in the validator drifts the moment an admin adds a value. The describe map is regenerated per load, so it always matches the live org.

### Pattern 2 — Two-pass load for dependent picklists

**When to use:** the controlling field and the dependent field are both being loaded for the same record, AND the controlling field is computed (formula or trigger) rather than supplied by the CSV.

**How it works:** load the controlling field in pass 1; in pass 2, load the dependent field. The platform validates dependent picklists at insert/update time using the *current* controlling value, so a same-batch load can race when the controlling value is derived. If both must travel together, ensure they are in the same row of the same batch (Data Loader processes rows in CSV order within a batch, but cross-row dependencies are unsafe).

**Why not the alternative:** loading the dependent field first leaves it with no valid controlling context and the platform either rejects (`INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST`) or silently writes a value that disappears on next save.

### Pattern 3 — Reactivate-load-deactivate window for retired values

**When to use:** loading historical data that uses values which have since been deactivated, AND data faithfulness requires keeping the original value (not remapping).

**How it works:** before the load, reactivate the retired values in metadata; run the load with a tight time window; deactivate the values immediately after. Log every value reactivated, why, and the deactivation timestamp so the change is auditable.

**Why not the alternative:** remapping `Suspect -> Prospect` loses the historical signal. Bulk-bypassing validation rules does not bypass restricted-picklist enforcement — there is no `EnforceFLSAndPicklist = false` for restricted picklists.

---

## Decision Guidance

| Picklist situation | Recommended pre-load action | Reason |
|---|---|---|
| Standard picklist (unrestricted) | Run the validator in *warn* mode against the field-level allowed list | Loads will technically succeed but non-conforming values become orphaned UI-invisible data |
| Restricted picklist | Run the validator in *fail* mode against the field-level allowed list AND record-type slice | Platform rejects with `BAD_VALUE_FOR_RESTRICTED_PICKLIST`; every invalid row is a guaranteed batch error |
| Record-type-specific picklist | Validate per-row against the allowed values for that row's record type, not the global field list | A value valid at field level can be invalid for a specific record type; the platform applies the RT slice |
| Dependent picklist | Validate (controlling, dependent) pair against the dependency matrix for the row's record type | Platform requires both halves to be a valid pair; controlling-field loads must precede or accompany dependent-field loads |
| Multi-select picklist | Confirm the field uses `;` (semicolon) as delimiter and split each cell on `;` before validating each token | Comma in the CSV value collapses multiple selections into one bogus combined value |
| Global Value Set-backed picklist | Validate against the GVS allowed-values map (cascades across SObjects); flag values inactive at the GVS level | A value can look valid at the field describe but be inactive at the GVS level; cascading deactivation is the most common surprise |

---

## Recommended Workflow

1. **Pull metadata describe.** For every SObject in the load, fetch the record types and, for each (record type, picklist field), the active values. Save as a JSON map keyed `{ object: { field: { recordTypeDeveloperName: [values...] } } }`. Include a `__field_level__` key per field for the field-level allowed list (used for unrestricted-picklist warnings).
2. **Identify the picklist columns in the CSV.** Cross-reference the CSV header against the SObject describe; flag any header that names a picklist field. Also identify the record-type column (`RecordTypeId` or `RecordType.DeveloperName`).
3. **Run the validator.** `python3 skills/data/data-loader-picklist-validation-pre-load/scripts/check_data_loader_picklist_validation_pre_load.py --csv <file> --map <picklist-map.json> --object <SObject> --rt-column RecordType.DeveloperName`. The validator emits one row per finding: `(line_number, column, value, record_type, severity, reason)`.
4. **Triage the findings.** Group by reason: invalid-for-RT, retired/inactive, multi-select-delimiter, label-vs-API-name, length-over-255, dependent-pair-invalid. Each group has a different remediation.
5. **Remediate in the CSV (or the org).** Rename labels back to API names, fix delimiters, remap retired values (or reactivate temporarily — see Pattern 3), split dependent picklists into a two-pass load if needed.
6. **Re-run the validator.** Iterate until the script exits 0 (no findings) or all remaining findings are explicitly accepted (e.g. inactive values that will be reactivated for the load window).
7. **Document the accepted exceptions.** Any non-zero exit accepted as a known-good load (e.g. reactivated values) goes in the load runbook with an explicit re-deactivation step after the load completes.

---

## Review Checklist

- [ ] Picklist map JSON was regenerated from the **target org**, not a sandbox with stale metadata
- [ ] Every restricted picklist column in the CSV passes the per-record-type validator
- [ ] Every multi-select column uses `;` as the delimiter (no commas inside the cell)
- [ ] Every value compared against API names, not labels
- [ ] No value exceeds 255 characters
- [ ] Dependent picklist pairs are valid for the row's record type
- [ ] Inactive / retired values either remapped or scheduled for temporary reactivation with a paired deactivation step
- [ ] `python3 scripts/check_data_loader_picklist_validation_pre_load.py` exits 0 OR all remaining findings are documented exceptions

---

## Salesforce-Specific Gotchas

1. **Org default record type still applies a slice.** Even if the CSV omits `RecordTypeId`, the assigned default record type filters picklist values for the inserting user. "I'm not setting record type, so the full list applies" is wrong.
2. **Unrestricted picklists silently accept garbage.** The load succeeds, the value lands in the database, but the UI dropdown does not show it. The first user edit either picks something else (data lost) or fails validation.
3. **`RecordType.DeveloperName` upsert lookup is case-sensitive in the API but UI-edited names are not always.** A typo like `healthcare` vs `Healthcare` resolves in the UI and fails in the load.
4. **Dependent picklist dependency matrices are NOT in the standard describe response.** They live in a separate metadata payload (`getPicklistValues` returns a `validFor` byte string per dependent value). Validators that only read field describe miss dependent rules entirely.
5. **Translation Workbench renames hit labels but not API names.** If your org translates labels and your CSV came from a translated UI export, the values are localised labels, not API names — every row will fail until you re-export against API names.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Picklist map JSON | Per-(object, field, record type) allowed-values map fed into the validator |
| Validator findings report | One row per `(line, column, value, record_type, severity, reason)` violation |
| Remediation plan | Documented action per finding group: rename, remap, reactivate window, two-pass load |
| Pre-load validation template (`templates/data-loader-picklist-validation-pre-load-template.md`) | Filled-in report following this skill's canonical shape |

---

## Related Skills

- `data/data-loader-csv-column-mapping` — make sure the columns map to the right fields *before* validating values
- `data/data-loader-batch-window-sizing` — once values are clean, choose the right batch size and window
- `data/bulk-api-and-large-data-loads` — choosing Data Loader vs Bulk API for the actual load
- `data/external-id-strategy` — using `RecordType.DeveloperName` as an External ID lookup vs literal `RecordTypeId`
- `admin/picklist-administration` — admin-side rules for activating, deactivating, and renaming picklist values
