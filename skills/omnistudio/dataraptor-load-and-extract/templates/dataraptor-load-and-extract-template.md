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

**Extract Steps (Extract tab: object, filter, Extract Output Path):**
| Object | Filter | Extract Output Path |
|---|---|---|
| `Account` | `Id = AccountId` (input parameter) | `Account` |
| `Contact` | `AccountId = Account:Id` (earlier step) | `Contact` |

**Output Mapping (Output tab):**
| Extract Path | Output JSON Path | Notes |
|---|---|---|
| `Account:Name` | `Account:Name` | |
| `Contact:LastName` | `Account:Contacts:LastName` | Child list nested under the parent |

**Extract Type:** Standard / Turbo (circle one; Turbo reads one object type with related-object fields, and has no formulas or complex output mappings)

**Options:** Field-level security check on/off: ___  Cache type and TTL: ___

**Preview Tab Test:** [ ] Tested with real record ID — output JSON confirmed

---

## DataRaptor Load Design

**Object:** ___

**Write behavior:** create and update in one run, decided by the Upsert Keys (deletes are not documented for Loads in the fetched sources)

**Upsert Key Field(s):** ___ (any mapped field; together they must match one existing record)

**Is Required For Upsert Field(s):** ___ (records missing these are skipped)

**Input Mapping:**
| Input JSON Path | Target Field API Name | Notes |
|---|---|---|
| `data.externalId` | `External_Id__c` | Upsert key |
| `data.firstName` | `FirstName` | |

**Post-Load Check:** [ ] Integration Procedure inspects the Load step's response before returning success (confirm the error node name in the IP debug output)

**Volume estimate:** ___ records per call (compare with `synchronousProcessThreshold`; above it the Load runs as Apex batch jobs)

---

## Multi-Object Load Sequence (if applicable)

Order of object writes:
1. Object A: ___ (operation: ___)
2. Object B: ___ (operation: ___, depends on ID from step 1)

**Rollback setting:** `rollbackOnError` = true / false (false commits partial work). Compensating actions if false: ___

---

## Test Checklist

- [ ] Extract steps, filters, and Extract Output Paths reviewed
- [ ] Output JSON structure matches OmniScript's expected data paths
- [ ] Preview tab tested with real data
- [ ] Load Preview run in a developer sandbox only (Preview saves records)
- [ ] Load tested with invalid input and the IP response shows the failure
