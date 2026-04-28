# Template — Pre-Load Picklist Validation Report

Use this template to document and act on a pre-load picklist validation run before sending a CSV through Data Loader, Workbench, or the Bulk API.

---

## 1. Load context

| Field | Value |
|---|---|
| Target org | `<org alias / production / sandbox name>` |
| Target SObject(s) | `<SObject>` |
| CSV path | `<absolute path>` |
| CSV row count (excluding header) | `<n>` |
| CSV encoding | `UTF-8` (confirmed via `file <path>`) |
| Record type column | `RecordType.DeveloperName` / `RecordTypeId` / *(none — using user default)* |
| Picklist map JSON path | `<absolute path>` |
| Picklist map generated on | `<YYYY-MM-DDThh:mm:ss±tz>` from `<org alias>` |
| Salesforce release | `Spring '25` / `Summer '25` / etc |

---

## 2. Picklist columns in scope

List every column in the CSV that maps to a picklist field on the target SObject:

| Column | Field on target | Type | Restricted | GVS-backed | Multi-select | Dependent on |
|---|---|---|---|---|---|---|
| `Industry` | `Account.Industry` | Picklist | yes | no | no | — |
| `Sub_Industry__c` | `Account.Sub_Industry__c` | Picklist | yes | no | no | `Industry` |
| `Tags__c` | `Account.Tags__c` | Multi-select | yes | yes (`Tag_GVS`) | yes | — |
| `Stage` | `Opportunity.StageName` | Picklist | yes | no | no | — |

---

## 3. Validator command

```bash
python3 skills/data/data-loader-picklist-validation-pre-load/scripts/check_data_loader_picklist_validation_pre_load.py \
    --csv <csv-path> \
    --map <picklist-map.json> \
    --object <SObject> \
    --rt-column RecordType.DeveloperName \
    --multi-select-fields Tags__c \
    --dependent-fields Sub_Industry__c:Industry
```

Exit code: `0` (clean) / `1` (findings) / `2` (usage error).

---

## 4. Findings summary

| Severity | Count | Top reason |
|---|---|---|
| FAIL | `<n>` | `<reason code>` |
| WARN | `<n>` | `<reason code>` |
| INFO | `<n>` | `<reason code>` |

Reason codes used by the validator:

- `invalid-value-for-record-type` — value not in the allowed list for the row's record type
- `value-not-found` — value not present in metadata at all (likely typo or label-vs-API-name mismatch)
- `inactive-value` — value present in metadata but inactive; load will be rejected
- `multi-select-delimiter` — multi-select cell contains `,` instead of `;`
- `dependent-pair-invalid` — `(controlling, dependent)` pair not allowed for the row's RT
- `length-over-255` — value exceeds the 255-character per-value limit
- `record-type-not-found` — `RecordType.DeveloperName` does not match any RT on the SObject (case-sensitive)

---

## 5. Findings detail

Group findings by reason. For each group, document the remediation chosen.

### Group A — `<reason code>` (`<n>` rows)

Sample rows:

| Line | Column | Value | Record type |
|---|---|---|---|
| 42 | `Industry` | `Manufacturing` | `Healthcare` |
| 87 | `Industry` | `Manufacturing` | `Healthcare` |
| ... | | | |

Remediation chosen: `<rename | remap | reactivate window | two-pass load | reject and escalate>`

Owner: `<name>`

Effective date: `<date>`

### Group B — `<reason code>` (`<n>` rows)

(repeat per group)

---

## 6. Remediation actions taken

Document each action so the load is reproducible.

| Action | Detail | Reversible | Reversal step | Owner |
|---|---|---|---|---|
| Reactivated `Suspect` on `Opportunity.StageName` | Metadata change in target org | yes | Deactivate after load | `<name>` |
| CSV remap `Government -> Public Sector` on `Lead.Interests__c` | sed in repo `data/leads-fixed.csv` | n/a (CSV-side) | Re-export from source | `<name>` |
| Split CSV into two passes for `Sub_Industry__c` dependency | Pass 1 = controlling field only; pass 2 = dependent | n/a | — | `<name>` |

---

## 7. Re-validation

After remediation, re-run the validator:

```bash
python3 skills/data/data-loader-picklist-validation-pre-load/scripts/check_data_loader_picklist_validation_pre_load.py ...
```

Result: `<exit 0 — clean>` or `<exit 1 — N accepted exceptions documented in section 8>`

---

## 8. Accepted exceptions

If the validator exits non-zero but the load is approved to proceed, list every accepted exception with explicit justification:

| Reason | Rows | Justification | Approver | Reversal/cleanup task |
|---|---|---|---|---|
| `inactive-value` | 600 | Historical reload, RT-faithfulness required; `Suspect` reactivated for the load window | `<name>` | Deactivate `Suspect` after load (ticket `<id>`) |

---

## 9. Post-load verification

After the load completes:

- [ ] Spot-check `<n>` random rows from each remediated group; confirm the loaded value matches the CSV value.
- [ ] Run a SOQL query against the affected fields and confirm row counts match the CSV.
- [ ] If a temporary metadata change was made (e.g. value reactivation), confirm the reversal step ran.
- [ ] Archive the CSV, the picklist map JSON, and this report together with the load run.

---

## 10. Sign-off

| Role | Name | Date |
|---|---|---|
| Data owner | `<name>` | `<date>` |
| Salesforce admin | `<name>` | `<date>` |
| Load operator | `<name>` | `<date>` |
