# Custom Index Requests — Salesforce Support Case Template

Use this template when submitting a Salesforce Support case requesting a custom index, skinny table, or two-column composite index.

---

## Case Information

**Case Type:** [ ] Custom index [ ] Null-inclusive custom index [ ] Skinny table [ ] Two-column index (state column order)
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
Run in production, or in a sandbox that has the index (custom indexes: any sandbox created after the index exists; skinny tables: Full sandboxes only).

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
- [ ] Under the custom-index threshold: 10% of the first million rows plus 5% of rows beyond (state the computed number)
- [ ] Filter count recorded next to the computed threshold (no flat row target applies; the threshold scales with the object's row count)

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
- [ ] Filter count is under the computed custom-index threshold for the object's row count
- [ ] Org ID is the production 15-character ID (not sandbox)
- [ ] Plan captured where the index exists (production, or a sandbox created after the index; Full sandbox for skinny tables)
- [ ] Field distribution information included
- [ ] Business justification included
