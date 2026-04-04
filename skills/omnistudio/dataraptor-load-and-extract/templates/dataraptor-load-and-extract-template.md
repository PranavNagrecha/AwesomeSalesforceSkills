# DataRaptor Load and Extract — Design Template

## Operation Type

- [ ] Extract (read from Salesforce)
- [ ] Load (write to Salesforce)
- [ ] Both (separate DataRaptors, one for each)

---

## DataRaptor Extract Design

**Base Object:** ___

**SOQL Query:**
```sql
SELECT
    -- list fields here
FROM Object
WHERE condition = :inputVar
```

**Input Variables:**
| Variable Name | Source in OmniScript/IP |
|---|---|
| `inputVar` | |

**Output Mapping:**
| SOQL Field Path | Output JSON Path | Notes |
|---|---|---|
| `FieldName` | `result.fieldName` | |
| `Relationship.FieldName` | `result.parent.fieldName` | Parent via lookup |
| `ChildRel.records` | `result.children` | Sub-select child records |

**Extract Type:** Standard / Turbo (circle one — use Turbo only if no relationships needed)

**Preview Tab Test:** [ ] Tested with real record ID — output JSON confirmed

---

## DataRaptor Load Design

**Object:** ___

**Operation:** Insert / Update / Upsert / Delete (circle one)

**Upsert Key Field (if upsert):** ___ (must be designated as External ID)

**Input Mapping:**
| Input JSON Path | Target Field API Name | Notes |
|---|---|---|
| `data.externalId` | `External_Id__c` | Upsert key |
| `data.firstName` | `FirstName` | |

**Post-Load iferror Check:** [ ] Integration Procedure checks `<stepName>:iferror` after Load

**Volume estimate:** ___ records per transaction (flag if >50 for Bulk API discussion)

---

## Multi-Object Load Sequence (if applicable)

Order of object writes:
1. Object A: ___ (operation: ___)
2. Object B: ___ (operation: ___, depends on ID from step 1)

**Rollback warning:** No automatic rollback — compensating actions for failure: ___

---

## Test Checklist

- [ ] SOQL tested in Developer Console before DataRaptor configuration
- [ ] Output JSON structure matches OmniScript's expected data paths
- [ ] Preview tab tested with real data
- [ ] Load tested with valid input and confirmed record created/updated in org
- [ ] Load tested with invalid input and confirmed iferror node returned
