# Gotchas — Data Loader Picklist Validation (Pre-Load)

Subtle traps when pre-validating CSV data against picklist rules and record-type assignments.

---

## 1. The org default record type still narrows the picklist

**What happens:** the CSV omits `RecordTypeId`, the loading user has access to the default record type, and a "valid Industry value" is rejected. Practitioners assume that with no record type set, the full field-level list applies. It does not — the inserting user's default RT is applied, and that RT's narrower allowed-values slice is enforced.

**When it occurs:** any insert that does not carry an explicit `RecordTypeId` against an SObject with multiple record types.

**How to avoid:** always treat the picklist map as `(object, field, recordTypeDeveloperName)`-keyed. When the CSV omits the RT column, resolve the inserting user's default RT and substitute it before validating. Never key the validator by `(object, field)` alone.

---

## 2. Unrestricted picklists silently accept garbage values

**What happens:** the field-level metadata shows `restrictedPicklist: false`. The load succeeds. The bad value lives in the database row but the page-layout dropdown does not include it. The first user edit either picks something else (the bad value is lost without warning) or fails an unrelated validation rule.

**When it occurs:** legacy custom picklists created in older API versions where `restrictedPicklist` defaulted to false; standard picklists that have not been explicitly restricted; values that *look* close to a real value but differ in whitespace or capitalisation.

**How to avoid:** validate against the allowed-values list **regardless** of the `restrictedPicklist` flag. Treat unrestricted-picklist mismatches as **warnings** rather than failures, but surface them in the report — silent data drift is more expensive than a noisy validator.

---

## 3. Dependent picklist dependency matrices are NOT in the field describe response

**What happens:** a validator that reads the standard `getDescribe()` JSON sees the dependent field's allowed values but has no idea which controlling-field values are valid pairs. It approves rows that the platform will then reject with `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST` at insert time.

**When it occurs:** any dependent picklist. The `validFor` byte string (an opaque base64-encoded bitmap) is exposed via `getPicklistValues()` on the dependent field, NOT in the top-level field describe.

**How to avoid:** when building the picklist map, decode the `validFor` byte string for each dependent value to recover the (controlling, dependent) pair table. Persist that table in the JSON map and have the validator consult it for any field flagged as dependent. If you skip this step, dependent-picklist validation is fiction.

---

## 4. Multi-select picklist input uses `;` — but the post-load REST/SOAP read returns the same `;`-joined string

**What happens:** developers expecting an array on read see a single string `"Healthcare;Finance;Public Sector"` and assume the load also took a comma-delimited or array form. They write a CSV with commas, the load fails, and they cannot reproduce the failure in Apex (where `Selected__c = new List<String>{...}` would be rejected at compile time anyway).

**When it occurs:** any multi-select picklist load via Data Loader, Bulk API, REST. Apex assignment uses `String` with `;` as the separator too — the format is consistent across the platform but unintuitive coming from REST APIs that use JSON arrays.

**How to avoid:** the validator should treat any field flagged as multi-select as a `;`-split list and validate each token individually. It should also flag any cell that contains `,` inside a multi-select column — almost always a typo.

---

## 5. `RecordType.DeveloperName` external-ID lookup is case-sensitive on the API path

**What happens:** the CSV uses `RecordType.DeveloperName = healthcare` (lowercase) and the load fails with `INVALID_FIELD_FOR_INSERT_UPDATE: RecordType.DeveloperName: not found`. The UI is forgiving — the API is not. A typo in case loses the entire row's record-type assignment, the org default takes over, and now the picklist validation runs against the wrong slice.

**When it occurs:** CSVs hand-edited from Excel; CSVs joined from systems with their own case conventions; CSVs where developer names were typed by hand against the UI label.

**How to avoid:** validate the `RecordType.DeveloperName` column against the actual case-sensitive developer name from the describe before any picklist validation runs. A case mismatch should be reported as a P0 — every other picklist check downstream depends on the correct RT.

---

## 6. Inactive picklist values are still queryable on existing records

**What happens:** the developer queries `SELECT Industry FROM Account` and sees `Suspect` in the results. They assume `Suspect` is still a valid value to insert. The platform actually allows old values to *read* (so existing records are not corrupted) but rejects them on insert/update.

**When it occurs:** historical reloads, sandbox-to-production data refreshes, archive imports.

**How to avoid:** the picklist map must distinguish active from inactive values. Use the `active` flag from `getPicklistValues()` (or the `<picklistValueSet>.<picklistValue>.<active>` element in metadata XML). Validator findings for inactive values should specifically suggest "remap or temporarily reactivate" rather than the generic "value not found."

---

## 7. Translation Workbench labels look exported, but loads need API names

**What happens:** an admin exports a CSV from a list view in a Spanish-locale browser session. The picklist column carries Spanish labels. The CSV is saved and handed off to a different team for the production load. Every row fails — the API name is what the platform actually stores; labels are localisation.

**When it occurs:** any org with the Translation Workbench enabled and a non-English-locale user exporting CSVs.

**How to avoid:** when constructing the picklist map, store API names ONLY. The validator never compares against labels. If a CSV is suspected of carrying labels, run a one-time `label -> apiName` remap step before validation. Document this conversion in the load runbook.

---

## 8. Global Value Set deactivations cascade — but field-level describes lag

**What happens:** a value is deactivated at the Global Value Set level. The field-level describe of one specific field still lists the value as available for some minutes after the metadata change, especially in sandboxes. Validators that only consult the field-level describe will approve rows that the live load then rejects.

**When it occurs:** GVS-backed picklists in orgs where metadata was just changed; sandbox refreshes where the GVS state is older than the per-field describe.

**How to avoid:** when a field is GVS-backed, fetch the GVS allowed-values map directly (Tooling API or metadata XML) and treat IT as authoritative — not the field-level describe. The picklist map JSON should record which fields are GVS-backed and which GVS feeds them.

---

## 9. The 255-character per-value limit silently truncates external imports

**What happens:** an external system sends a verbose categorisation string (e.g. an LLM-generated tag) longer than 255 characters into a picklist field. The load may either fail (`STRING_TOO_LONG`) or — depending on the API path — silently truncate. Either way, the validator should catch it before the load.

**When it occurs:** any inbound feed where the source field is free-text or LLM-generated and the destination is a picklist.

**How to avoid:** the validator should reject any picklist value > 255 characters as `length-over-255`, regardless of whether it appears in the allowed list. Practical guidance: external "tag" data belongs in a Long Text Area or a Tag-managed entity, not a picklist.

---

## 10. Bulk API "hard delete" of a picklist value does not exist — deactivation is the only safe path

**What happens:** an admin "removes" a picklist value via the UI's `Replace and Delete`. Existing records still carry the deactivated value (history is preserved), but the value is gone from the metadata. A pre-load validator that consults the metadata sees no trace of the value and reports `value-not-found` rather than `inactive-value`. The user thinks the CSV typo'd a brand-new value.

**When it occurs:** orgs where picklist values have been replaced-and-deleted rather than simply deactivated.

**How to avoid:** distinguish three states in the picklist map: `active`, `inactive`, and `not-found`. If a value is `not-found`, query historical SOQL on the field to confirm it was once a real value before assuming a typo. The remediation differs (remap vs reactivate vs investigate source).
