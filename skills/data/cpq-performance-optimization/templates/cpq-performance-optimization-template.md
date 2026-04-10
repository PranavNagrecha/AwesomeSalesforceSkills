# CPQ Performance Optimization — Work Template

Use this template when diagnosing or resolving CPQ quote calculation performance issues.

## Scope

**Skill:** `cpq-performance-optimization`

**Request summary:** (fill in what the user asked for — e.g., "QLE timeout on 250-line quotes", "QCP returning null for custom field", "SBQQ__Code__c over character limit")

---

## Context Gathered

Answer these before recommending any change:

- **Typical quote line count (P50):** ___
- **Maximum quote line count (P99):** ___
- **Current Large Quote Mode status:** Enabled / Disabled
- **Current Large Quote Mode threshold:** ___ lines
- **QCP in use:** Yes / No
- **QCP code location:** Inline SBQQ__Code__c / Static Resource
- **Current SBQQ__Code__c character count (if inline):** ___
- **Known QCP field declaration list (fieldsToCalculate):** (paste or describe)
- **Known QCP field declaration list (lineFieldsToCalculate):** (paste or describe)
- **Calculate Quote API used in batch jobs:** Yes / No

---

## Diagnosis

Check all that apply:

- [ ] Governor limit errors on quotes above ___ lines → Large Quote Mode likely needed
- [ ] QCP returning wrong prices on specific fields → undeclared field suspected
- [ ] SBQQ__Code__c approaching or over 131,072 chars → Static Resource migration needed
- [ ] Calculate Quote API jobs failing on large quotes → Large Quote Mode not enabled for API path
- [ ] Reps confused by async indicator → UX communication gap

---

## Approach

Which pattern from SKILL.md applies? (check one or more)

- [ ] Enable Large Quote Mode (threshold configuration + UX communication)
- [ ] Audit and correct QCP field declarations
- [ ] Migrate QCP to Static Resource architecture
- [ ] Educate on Calculate Quote API limits (not a performance bypass)

**Rationale:** (explain why this pattern fits the situation)

---

## Configuration Changes

### Large Quote Mode (if applicable)

| Setting | Current Value | Recommended Value |
|---|---|---|
| Large Quote Mode | | |
| Threshold (lines) | | |
| SBQQ__LargeQuote__c on key accounts | | |

### QCP Field Declarations (if applicable)

**Fields to ADD to fieldsToCalculate:**
- (list fields referenced in plugin but missing from declaration)

**Fields to REMOVE from fieldsToCalculate:**
- (list fields declared but not referenced in plugin code)

**Fields to ADD to lineFieldsToCalculate:**
- (list)

**Fields to REMOVE from lineFieldsToCalculate:**
- (list)

---

## Checklist

- [ ] Large Quote Mode threshold set and documented
- [ ] QCP field declarations audited — declared fields match exactly what plugin reads/writes
- [ ] SBQQ__Code__c character count below 131,072 (or Static Resource migration planned)
- [ ] UX communication prepared for reps (async indicator explanation)
- [ ] Apex job queue monitoring configured for failed calculation jobs
- [ ] Validated in sandbox with representative large quote
- [ ] Sales ops team notified before production enablement

---

## Notes

(Record any deviations from the standard pattern, org-specific constraints, or decisions made during implementation)
