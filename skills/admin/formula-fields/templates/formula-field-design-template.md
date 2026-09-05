# Formula Field Design Template

Use this before creating or rewriting a complex formula field.

---

## Overview

| Property | Value |
|----------|-------|
| Field label | _e.g. Open Pipeline Net_ |
| API name | _e.g. `Open_Pipeline_Net__c`_ |
| Return type | Text / Number / Currency / Percent / Checkbox / Date / URL |
| Object | _e.g. Opportunity_ |
| Business purpose | _one sentence; this becomes the field `description`_ |

## Design Checks

| Question | Answer |
|----------|--------|
| Is a formula field the right tool? | _Yes / No — a value that must be frozen, written to, or replicated is a stored field_ |
| If not a formula, what should store the value? | _field + the Flow or Apex that stamps it_ |
| Cross-object references used? | _list each traversal and its hop count_ |
| Null / blank scenarios handled? | _`BlankAsZero` or `BlankAsBlank`, plus the `ISBLANK()` guards the switch does not cover_ |
| Reporting impact considered? | _which reports, list views, exports, and integrations read it_ |

## Formula Draft

```text
_paste the expression here, then paste the XML-escaped version that goes into `<formula>`_
```

## Test Cases

| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Happy path | _record id + input values_ | _expected result_ |
| Blank value | _record where a referenced field is genuinely null_ | _expected result under the chosen blank handling_ |
| Zero or false value | _record with `0` / unchecked, not blank_ | _expected result, and how it differs from blank_ |
| Cross-object missing parent data | _child with no parent, or parent field empty_ | _expected result_ |

## Documentation

- [ ] Field description updated with business rule
- [ ] Any helper formulas or dependencies documented
- [ ] Decision recorded if formula replaced a stored field or vice versa

## Deploy Checks

- [ ] `<type>` is the return type (`Text` / `Number` / `Currency` / `Percent` / `Checkbox` / `Date`), never `Formula`
- [ ] `<formulaTreatBlanksAs>` written explicitly; `<precision>` and `<scale>` present for numeric return types
- [ ] `&`, `<`, `"` escaped inside `<formula>`; the file parses as XML
- [ ] `package.xml` lists the field as `Object.Field__c` (no `*` wildcard for `CustomField`)
- [ ] `python3 scripts/check_formula_fields.py --manifest-dir <objects dir>` clean, or every finding justified
- [ ] Validate-only deploy (`--dry-run`) passed before the real deploy
