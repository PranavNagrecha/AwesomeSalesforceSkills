# Examples — Data Loader Picklist Validation (Pre-Load)

Three realistic pre-load picklist failures and the validator workflow that catches each before the load runs.

---

## Example 1 — Multi-select picklist with comma typo

### Setup

A CSV exported from a marketing analytics tool needs to load into `Lead.Interests__c`, a **multi-select picklist** with active values:

```
Healthcare
Finance
Public Sector
Retail
```

The CSV (UTF-8, `,` as the column delimiter):

```csv
LastName,Email,Interests__c,RecordType.DeveloperName
Smith,smith@example.com,"Healthcare,Finance",Default
Jones,jones@example.com,"Retail;Public Sector",Default
Lee,lee@example.com,"Healthcare;Finance;Government",Default
```

### What goes wrong without pre-validation

Row `Smith` has `"Healthcare,Finance"` — comma inside a quoted cell. The platform reads this as **one value** literally `Healthcare,Finance`, which is not in the allowed set. Restricted picklist => `BAD_VALUE_FOR_RESTRICTED_PICKLIST`. Unrestricted => silent non-conforming write.

Row `Lee` uses the right delimiter (`;`) but `Government` is not an allowed value. Same rejection.

### Pre-load validator output

```
$ python3 skills/data/data-loader-picklist-validation-pre-load/scripts/check_data_loader_picklist_validation_pre_load.py \
    --csv leads.csv \
    --map picklist_map.json \
    --object Lead \
    --rt-column RecordType.DeveloperName \
    --multi-select-fields Interests__c

[FAIL] line 2 column Interests__c value "Healthcare,Finance" record_type=Default reason=multi-select-delimiter
       (cell contains ',' — multi-select picklists must use ';' as the value separator)
[FAIL] line 4 column Interests__c value "Government" record_type=Default reason=invalid-value-for-record-type
       (value not in allowed list for Lead.Interests__c under RT 'Default'; allowed=[Healthcare,Finance,Public Sector,Retail])

Summary: 2 failures across 1 column. Fix the CSV and re-run.
```

### Fix

```csv
LastName,Email,Interests__c,RecordType.DeveloperName
Smith,smith@example.com,"Healthcare;Finance",Default
Jones,jones@example.com,"Retail;Public Sector",Default
Lee,lee@example.com,"Healthcare;Finance",Default
```

If `Government` is genuinely needed, add it to the picklist metadata first, regenerate the JSON map, re-run. Do not bypass the validator.

---

## Example 2 — Record-type-specific Industry mismatch

### Setup

`Account.Industry` has 30 platform-level values. The org has two record types:

- `Account.Healthcare` exposes `[Healthcare, Biotechnology, Hospitals & Clinics]`
- `Account.Manufacturing` exposes `[Manufacturing, Industrial, Chemicals]`

The CSV:

```csv
Name,Industry,RecordType.DeveloperName
Mercy Hospital,Hospitals & Clinics,Healthcare
Acme Steel,Manufacturing,Manufacturing
Globex Bio,Biotechnology,Manufacturing
Initech,Technology,Healthcare
```

### What goes wrong without pre-validation

- `Globex Bio`: `Biotechnology` is a valid Industry value at the field level AND a valid value for the Healthcare RT, BUT the row claims the Manufacturing RT, where `Biotechnology` is not allowed.
- `Initech`: `Technology` is a perfectly valid platform Industry, but the Healthcare RT does not expose it.

For a **restricted** Industry picklist both rows fail with `BAD_VALUE_FOR_RESTRICTED_PICKLIST`. For an **unrestricted** Industry picklist the values land but become non-conforming and disappear from the page layout — a silent data-quality bug.

### Picklist map JSON (excerpt)

```json
{
  "Account": {
    "Industry": {
      "__field_level__": ["Agriculture", "Apparel", "Banking", "Biotechnology", "Chemicals", "Healthcare", "Hospitals & Clinics", "Industrial", "Manufacturing", "Technology"],
      "Healthcare": ["Healthcare", "Biotechnology", "Hospitals & Clinics"],
      "Manufacturing": ["Manufacturing", "Industrial", "Chemicals"]
    }
  }
}
```

### Validator output

```
[FAIL] line 4 column Industry value "Biotechnology" record_type=Manufacturing reason=invalid-value-for-record-type
       (allowed for Manufacturing=[Manufacturing,Industrial,Chemicals]; valid for Healthcare RT — check the row's RT assignment)
[FAIL] line 5 column Industry value "Technology" record_type=Healthcare reason=invalid-value-for-record-type
       (allowed for Healthcare=[Healthcare,Biotechnology,Hospitals & Clinics])
```

### Fix

Either correct the `RecordType.DeveloperName` (`Globex Bio` should likely be `Healthcare`), or correct the `Industry` value (`Initech` is `Technology` => assign the Manufacturing RT or add a Technology-friendly RT). The validator does not guess which side is wrong — that is a data-owner decision.

---

## Example 3 — Retired picklist value reload from history

### Setup

An archive CSV from 2019 needs to reload into `Opportunity.StageName` for compliance reporting. The historical pipeline used:

```
Suspect
Prospect
Qualified
Closed Won
Closed Lost
```

The current org has **deactivated** `Suspect` (replaced by `Cold Lead` in 2022). Active values are now:

```
Cold Lead
Prospect
Qualified
Closed Won
Closed Lost
```

The CSV (5,000 rows, ~600 of which use `Suspect`):

```csv
Name,StageName,CloseDate,RecordType.DeveloperName
Acme 2019-Q1,Suspect,2019-03-31,Default
Acme 2019-Q2,Prospect,2019-06-30,Default
...
```

### What goes wrong without pre-validation

`StageName` is a **restricted** picklist on `Opportunity` by default. Inserting `Suspect` returns `BAD_VALUE_FOR_RESTRICTED_PICKLIST` — all 600 historical rows fail. The user's first instinct ("just run the load and look at the error CSV") wastes a Bulk API job and reveals the failure only mid-flight.

### Picklist map JSON (excerpt)

The describe map keeps inactive values under a separate `__inactive__` sub-key per field so the validator can distinguish "value never existed" from "value existed but is inactive":

```json
{
  "Opportunity": {
    "StageName": {
      "__field_level__": ["Cold Lead", "Prospect", "Qualified", "Closed Won", "Closed Lost"],
      "__inactive__": ["Suspect"],
      "Default": ["Cold Lead", "Prospect", "Qualified", "Closed Won", "Closed Lost"]
    }
  }
}
```

### Validator output

```
[FAIL] line 2 column StageName value "Suspect" record_type=Default reason=inactive-value
       (value exists in metadata but is inactive — load will be rejected; reactivate temporarily or remap before load)
... (599 more)

Summary: 600 failures (all on inactive value 'Suspect'). Two remediation options:
  (A) Remap "Suspect" -> "Cold Lead" in the CSV (loses historical fidelity)
  (B) Temporarily reactivate "Suspect" in metadata, run the load, deactivate after (preserves historical fidelity)
```

### Decision and fix

The data owner chooses option B because the reporting requirement is "stage-as-was-on-close-date." The runbook becomes:

1. Reactivate `Suspect` on `Opportunity.StageName` (record the change in the deployment log).
2. Run the load (Bulk API, batches of 2,000).
3. Deactivate `Suspect` immediately after the load completes.
4. Re-run the validator on a sample query of the loaded rows to confirm `Suspect` was preserved.
5. Document the activation/deactivation timestamps for audit.

If option A had been chosen, a CSV-side remap step would rewrite `Suspect -> Cold Lead`, the picklist map would be regenerated, and the validator would re-run clean.
