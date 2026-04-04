# Custom Index Requests — Salesforce Support Case Template

Use this template when submitting a Salesforce Support case requesting a custom index, skinny table, or two-column composite index.

---

## Case Information

**Case Type:** [ ] Custom index (non-unique) [ ] Skinny table [ ] Two-column composite index
**Priority:** [ ] Standard [ ] High (justify below)
**Org ID (15-char production org):** _______________________

---

## Object and Field Information

**Object API Name:** _______________________
**Approximate Record Count:** _______________________
**Field(s) to Index:** _______________________
**Field Type(s):** (picklist / text / lookup / formula / etc.) _______________________

*For two-column index — specify column order (Column 1 = leading filter):*
**Column 1:** _________________ **Column 2:** _________________

---

## Problem Query

Paste the exact SOQL query that is performing poorly:

```sql
SELECT [fields]
FROM [Object]
WHERE [conditions]
ORDER BY [sort field]
LIMIT [n]
```

**Realistic bind variable values for the query:**
(e.g., `Status__c = 'Active'`, `OwnerId = '005...'`)

---

## Query Plan Output

Paste the Query Plan tool output (from Developer Console > Query Plan) here.
Run against your Full sandbox or production with the actual record count.

```
[Paste Query Plan output here]
Estimated rows: ___________
Leading operation type: [STORAGE / INDEX / TABLESCAN]
Cost: ___________
```

---

## Selectivity Analysis

**Total records in the object:** _______________________
**Records matching the filter:** _______________________
**Selectivity percentage (matching / total):** _______%

**Confirm selectivity is below threshold:**
- [ ] < 10% of records (required for custom index to be used by query optimizer)
- [ ] Filter produces ≤ 200,000 records (recommended target for large orgs)

---

## Query Frequency

**How often does this query run?** (per hour / per day)
_______________________

**What process runs this query?**
(e.g., "Lead routing automation runs every 5 seconds during business hours")
_______________________

---

## Business Impact

Describe the business impact of the slow query:
_______________________

**Current average query duration:** _______ seconds
**Target query duration:** _______ seconds

---

## Skinny Table — Additional Fields (if requesting skinny table)

List the fields to include in the skinny table (max 200, include only fields queried together):

| Field API Name | Type | Used in WHERE? | Used in SELECT? |
|---|---|---|---|
| Id | ID | N | Y (always) |
| | | | |

---

## Notes

_______________________

---

## Checklist Before Submitting

- [ ] Query Plan shows TABLESCAN (not already using an index)
- [ ] Selectivity is below 10% threshold
- [ ] Org ID is the production 15-character ID (not sandbox)
- [ ] Full sandbox or production used for Query Plan (not Developer/Partial sandbox)
- [ ] Field distribution information included
- [ ] Business justification included
