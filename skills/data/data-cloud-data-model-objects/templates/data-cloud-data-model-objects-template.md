# Data Cloud Data Model Objects — Work Template

Use this template when designing or onboarding Data Model Objects in Salesforce Data Cloud.

## Scope

- New data source being onboarded: ___________
- Custom DMOs to create: ___________
- Identity resolution scope: [ ] Yes — identity fields present  [ ] No

---

## Mandatory Identity DMO Coverage

| Mandatory DMO | Source Field | DLO Field | Status |
|---|---|---|---|
| Individual | | | [ ] Mapped / [ ] Missing |
| Party Identification | | | [ ] Mapped / [ ] Missing |
| Contact Point Email | | | [ ] Mapped / [ ] Missing |
| Contact Point Phone | | | [ ] Mapped / [ ] Missing |
| Contact Point Address | | | [ ] Mapped / [ ] Missing |

---

## Custom DMO Design

| DMO Name | Subject Area | Source DLO(s) | Key Fields | Relationship to Other DMO |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

## Data Transform Selection

| DMO Population Path | Source DLO Count | Transform Type | Schedule |
|---|---|---|---|
| | 1 | Streaming | Near-real-time |
| | 2+ | Batch | Nightly / Hourly |

---

## XMD Customization Plan

| Dataset / DMO | Field API Name | Current Label | New Label | XMD Type to Update |
|---|---|---|---|---|
| | | | | Main XMD |
| | | | | Main XMD |

**XMD Update API:**
```
PATCH /services/data/v{version}/wave/datasets/{datasetId}/xmds/main
```

---

## Data Relationship Map

| From DMO | From Field | To DMO | To Field | Relationship Name |
|---|---|---|---|---|
| | | | | |

Note: Only one relationship per field pair is supported.

---

## Validation Plan

```sql
-- Data Cloud Query API (ANSI SQL) — confirm DMO record counts
SELECT COUNT(*) FROM ssot__Individual__dlm

-- Confirm identity resolution coverage
SELECT COUNT(*) FROM ssot__ContactPointEmail__dlm
SELECT COUNT(*) FROM ssot__ContactPointPhone__dlm

-- Confirm custom DMO records
SELECT COUNT(*) FROM {CustomDMOApiName}__dlm
```

---

## Notes

_Capture schema decisions, relationship design choices, and open questions._
