# SOQL Query — [Object Name] — [Use Case]

## Query

```sql
SELECT [field1], [field2], [RelationshipName.ParentField]
FROM [ObjectApiName]
WHERE [filter conditions]
  AND [additional filters]
ORDER BY [fieldName] ASC NULLS LAST, Id ASC
LIMIT [n]
```

## Relationship Traversal (if applicable)

**Type:** [ ] Child-to-parent (dot notation)  [ ] Parent-to-child (subquery)

**Relationship path:** `[ChildObject] → [ParentObject]` via `[RelationshipName__r]`

## Filters Applied

| Field | Operator | Value | Notes |
|---|---|---|---|
| [FieldName] | = / != / LIKE / IN | [value] | [e.g., uses date literal THIS_MONTH] |

## Aggregate (if applicable)

```sql
SELECT [groupByField], COUNT(Id) recCount, SUM([NumericField]) total
FROM [ObjectApiName]
WHERE [conditions]
GROUP BY [groupByField]
HAVING COUNT(Id) > [threshold]
ORDER BY total DESC
```

## Pagination Strategy

- [ ] LIMIT + OFFSET (result set < 2,000 rows total)
- [ ] queryMore() / nextRecordsUrl (result set > 2,000 rows)
- [ ] Database.QueryLocator in Batch Apex (bulk processing)

**Page size:** [n]  
**Order-by field + tiebreaker:** [e.g., `CreatedDate DESC, Id DESC`]

## Governor Limit Check

| Limit | Budget | This Query |
|---|---|---|
| SOQL queries per transaction | 100 (sync) / 200 (async) | [1 or more] |
| Rows returned | 50,000 per transaction | LIMIT [n] |
| Query character length | 100,000 chars | [estimate] |

## Security Enforcement

```apex
// Recommended: use WITH USER_MODE to enforce FLS and sharing
List<[ObjectName]> records = [
    SELECT [fields]
    FROM [Object]
    WHERE [conditions]
    WITH USER_MODE
    LIMIT [n]
];
```

## Notes

[Record any deviations from standard patterns, org-specific considerations, or performance observations here.]
