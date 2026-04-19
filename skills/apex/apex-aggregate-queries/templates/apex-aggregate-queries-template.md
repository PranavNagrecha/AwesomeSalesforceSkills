# Apex Aggregate Queries — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `apex-aggregate-queries`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Object and metric field(s):
- Grouping dimension(s):
- Estimated result cardinality (include ROLLUP/CUBE subtotals if applicable):
- HAVING threshold (if any):
- Known constraints (org size, expected record volume, governor limit context):

## Approach

Which pattern from SKILL.md applies? Check one:

- [ ] Flat GROUP BY + HAVING (result cardinality < ~1,800)
- [ ] GROUP BY ROLLUP for subtotals
- [ ] GROUP BY CUBE for cross-dimensional subtotals
- [ ] Date-function grouping (CALENDAR_YEAR / CALENDAR_MONTH / etc.)
- [ ] Partitioned aggregate query via Batch Apex (cardinality > 2,000 risk)

## Query Draft

```apex
List<AggregateResult> results = [
    SELECT /* grouping fields */,
           /* SUM/COUNT/AVG/MIN/MAX with explicit alias */
    FROM   /* Object */
    WHERE  /* pre-aggregation filters */
    GROUP BY /* ROLLUP / CUBE optional */
    HAVING /* aggregate filter if needed */
    ORDER BY /* optional */
    LIMIT  2000
];
```

## Apex Iteration Draft

```apex
for (AggregateResult ar : results) {
    // Cast each field via get('alias')
    // Null-guard ROLLUP/CUBE subtotal rows before casting
}
```

## Review Checklist

- [ ] Every aggregate function in SELECT has an explicit alias
- [ ] Apex code uses ar.get('aliasName') with cast — not a typed SObject getter
- [ ] Result row count (including ROLLUP/CUBE subtotals) is expected to stay under 2,000
- [ ] Filters on aggregate values use HAVING, not WHERE
- [ ] ROLLUP/CUBE subtotal rows are null-checked before casting
- [ ] No aggregate GROUP BY inside an inner/subquery
- [ ] No WITH DATA CATEGORY combined with GROUP BY
- [ ] Unit tests cover the aggregate iteration logic

## Notes

Record any deviations from the standard pattern and why.
