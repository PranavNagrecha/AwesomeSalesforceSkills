# SOQL Null-Semantics Review Worksheet

Use this worksheet to reason about a relationship query's outer-join and null behavior *before*
trusting its result set. Copy it into your working notes and fill each section.

## Scope

**Skill:** `soql-outer-join-null-semantics`

**Query under review:**

```sql
-- paste the exact SELECT ... here
```

**Where it runs:** (inline Apex / `Database.query` string / report / list view / .soql file)

## Intended result set

State the ONE thing this query should return, in plain language:

- [ ] Rows whose lookup is **empty** (no parent)
- [ ] Rows whose lookup is **populated** (has a parent)
- [ ] Rows where a **parent field equals a specific value**
- [ ] Rows filtered by a **Boolean / checkbox** field
- [ ] Something else: __________________________________

## Null-semantics audit

| Question | Answer | Action if it bites |
|---|---|---|
| Does the query traverse a relationship (dot notation)? | | Remember it is an outer join — null-FK rows are returned |
| Any `WHERE Parent.Field = null`? | | Replace with a foreign-key filter (`ForeignKeyId = null`) — parent-field null also returns parent-less rows |
| Any Boolean field compared to `null`? | | Rewrite as `= true` / `= false`; `= null` means `= false` |
| Any `OR` branch on a relationship field? | | Confirm null-FK rows matching another branch are acceptable; add `ForeignKeyId != null` if not |
| Any `ORDER BY` on a relationship field? | | It does not filter — null-FK rows still return (for sort *placement* see `apex/soql-null-ordering-patterns`) |
| Does Apex read a parent field from the results? | | Null-guard the relationship object (`rec.Parent != null`) before dereferencing |

## Corrected query

```sql
-- the query after applying the actions above
```

## Apex traversal guard (if applicable)

```apex
for (SObject__c rec : [/* corrected query */]) {
    if (rec.Parent__r != null) {
        // safe to read rec.Parent__r.Field
    }
}
```

## Validation

Run the skill checker against your source tree, then confirm counts against real data that
includes parent-less rows:

```bash
python3 scripts/check_soql_outer_join_null_semantics.py --path force-app/main/default
```

- [ ] Checker reports no unexplained relationship/Boolean null-check warnings
- [ ] Row count of the corrected query matches the intended result set on data with empty lookups

## Notes

(Record why any flagged pattern was intentional and left in place.)
