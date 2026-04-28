# LLM Anti-Patterns — Data Loader Picklist Validation (Pre-Load)

Common mistakes AI coding assistants make when generating or advising on pre-load picklist validation. These help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Validating against the field-level allowed list and ignoring record types

**What the LLM generates:** a validator that builds `{ object: { field: [allowed_values] } }` from `Schema.SObjectType.Account.Industry.getDescribe().getPicklistValues()` and checks every CSV row against that flat list.

**Why it happens:** the LLM defaults to the simplest describe call. Record-type-specific allowed values require `getRecordTypeInfos()` plus `Picklist.getValues()` on the per-RT layout, which is an extra hop the LLM skips unless explicitly prompted.

**Correct pattern:**

```python
# Picklist map MUST be keyed by (object, field, recordTypeDeveloperName).
# Validator picks the slice using the row's RT, not the field-level list.
allowed = picklist_map[obj][field].get(row_rt) or picklist_map[obj][field]["__field_level__"]
if value not in allowed:
    findings.append((line_no, field, value, row_rt, "FAIL", "invalid-value-for-record-type"))
```

**Detection hint:** any validator code that indexes `picklist_map[obj][field]` and immediately looks up a value without going through a record-type slice first.

---

## Anti-Pattern 2: Splitting multi-select picklist cells on `,` instead of `;`

**What the LLM generates:** `for token in cell.split(','):` for multi-select picklist columns.

**Why it happens:** training data contains a lot of "comma-separated values" patterns. The Salesforce-specific `;` delimiter for multi-select picklists is a niche convention the LLM does not weight highly.

**Correct pattern:**

```python
# Multi-select fields use ';' (semicolon). A ',' in a multi-select cell is a typo to flag.
if field in multi_select_fields:
    if ',' in cell:
        findings.append((line_no, field, cell, row_rt, "FAIL", "multi-select-delimiter"))
    tokens = [t.strip() for t in cell.split(';') if t.strip()]
    for t in tokens:
        if t not in allowed:
            findings.append((line_no, field, t, row_rt, "FAIL", "invalid-value-for-record-type"))
```

**Detection hint:** grep for `split(',')` near any reference to a multi-select picklist; grep for `split(\";\")` paired with the right field set.

---

## Anti-Pattern 3: Comparing CSV values against picklist labels instead of API names

**What the LLM generates:** a validator that calls `getLabel()` on each picklist entry and stores labels as the allowed set.

**Why it happens:** the LLM treats "the value users see" and "the value that loads" as the same thing. They are not — labels are localised UI strings; API names are the canonical identifier.

**Correct pattern:**

```python
# Build the map from API names (PicklistEntry.value), NOT labels (PicklistEntry.label).
# Localisation and post-rename drift mean labels diverge from API names.
allowed = [entry.value for entry in field_describe.getPicklistValues() if entry.active]
```

**Detection hint:** any validator that mentions `getLabel`, `pickListEntry.label`, or compares against a localised string. Also check that the picklist map JSON does not store both labels and API names without distinguishing them.

---

## Anti-Pattern 4: Treating inactive values as "value not found"

**What the LLM generates:** a binary validator: value-in-allowed-list-or-not. Inactive values are reported as `value-not-found`, the same as a typo.

**Why it happens:** the LLM does not model the `active` flag. The describe response carries it but the LLM-generated code drops it during list construction.

**Correct pattern:**

```python
# Distinguish three states: active, inactive (existed but deactivated), not-found (never existed).
if value in active_values:
    pass  # OK
elif value in inactive_values:
    findings.append((line, field, value, rt, "FAIL", "inactive-value"))
else:
    findings.append((line, field, value, rt, "FAIL", "value-not-found"))
```

The remediation differs: `inactive-value` -> remap or temporary reactivation; `value-not-found` -> investigate the source (typo, source-org rename, brand-new value the org needs to add).

**Detection hint:** validator logic with only one rejection branch (`if value not in allowed`); no separate handling of inactive values in the picklist map JSON.

---

## Anti-Pattern 5: Skipping dependent-picklist matrix decoding

**What the LLM generates:** a validator that knows about the dependent field's allowed values but never checks the (controlling, dependent) pair.

**Why it happens:** the dependent-picklist `validFor` byte string is opaque (base64-encoded bitmap indexed against the controlling-field value list). Decoding it requires bit-twiddling the LLM does not produce by default; it silently drops the dependency check.

**Correct pattern:**

```python
# Dependent-picklist map: { (object, dependentField): { controllingValue: [allowedDependentValues] } }
# Validator must check that (controlling_value, dependent_value) is a valid pair for the row's RT.
dep_table = dependent_map.get((obj, field), {})
if dep_table:
    allowed_for_pair = dep_table.get(row[controlling_field], [])
    if value not in allowed_for_pair:
        findings.append((line, field, value, rt, "FAIL", "dependent-pair-invalid"))
```

**Detection hint:** validator output that never produces `dependent-pair-invalid` reasons even on CSVs with dependent picklists; picklist map JSON missing a `__dependencies__` block.

---

## Anti-Pattern 6: Hardcoding picklist values as constants in the validator

**What the LLM generates:** a Python list inline in the script: `INDUSTRY_VALUES = ['Manufacturing', 'Healthcare', 'Banking', ...]`.

**Why it happens:** the LLM optimises for "code that runs end-to-end without external inputs." It bakes the allowed list into the script rather than accepting it as a parameter from a generated picklist map.

**Correct pattern:**

```python
# Picklist values come from a JSON map regenerated per load.
# The validator never hardcodes any picklist value.
parser.add_argument('--map', required=True, help='Path to picklist map JSON')
with open(args.map) as fh:
    picklist_map = json.load(fh)
```

**Detection hint:** any list of picklist values literally inside the script body; the script running with no `--map` argument; no documented map-generation step.

---

## Anti-Pattern 7: Trusting the CSV's `RecordType.DeveloperName` casing without validation

**What the LLM generates:** the validator reads `RecordType.DeveloperName` from the CSV and looks it up in the map without normalising case. A row with `healthcare` (lowercase) silently falls back to "no RT match" and the validator runs against the field-level allowed list — which passes values the load will reject under the actual RT.

**Why it happens:** the LLM treats `RecordType.DeveloperName` as opaque text. It does not know that the API's external-ID lookup is case-sensitive while the UI is forgiving.

**Correct pattern:**

```python
# Validate RT developer name against the case-sensitive set BEFORE picklist validation runs.
known_rts = set(picklist_map[obj]["__record_types__"])
if row_rt not in known_rts:
    findings.append((line, "RecordType.DeveloperName", row_rt, row_rt, "FAIL", "record-type-not-found"))
    continue  # do not attempt picklist validation against a wrong RT
```

**Detection hint:** validator that proceeds with picklist checks even when the RT lookup failed; missing P0-priority RT-not-found reason in the output.
