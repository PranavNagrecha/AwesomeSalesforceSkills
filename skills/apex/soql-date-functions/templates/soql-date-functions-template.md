# SOQL Date Functions — Work Template

Use this template when building a SOQL query that groups or filters by a date period.

## Scope

**Skill:** `soql-date-functions`

**Request summary:** (what report/query does the user need?)

## Context Gathered

- Object and field: (e.g. `Opportunity.CloseDate` — Date, or `Case.CreatedDate` — DateTime)
- Field type: [ ] Date  [ ] DateTime   (DAY_ONLY / HOUR_IN_DAY need DateTime)
- Period: [ ] year [ ] quarter [ ] month [ ] week [ ] day [ ] hour
- Calendar or fiscal: [ ] calendar  [ ] fiscal
- Org fiscal-year config: [ ] standard  [ ] custom (custom => FISCAL_* unavailable)
- Local-day accuracy needed (wrap in convertTimezone)? [ ] yes  [ ] no

## Approach

- Placement: [ ] WHERE only (filter, no GROUP BY)  [ ] SELECT + GROUP BY (rollup)
  [ ] date literal on raw field (rolling window — out of scope, see soql-fundamentals)
- Function chosen: `______________(field)`
- Pattern from SKILL.md applied and why:

## Query skeleton

Filter (no aggregation):

```sql
SELECT Id, <fields>
FROM <Object>
WHERE <DATE_FUNC>(<field>) = <integer>
```

Rollup (repeat the function in GROUP BY):

```sql
SELECT <DATE_FUNC>(<field>) grp, <AGG>(<field>) total
FROM <Object>
WHERE <optional filter, e.g. CloseDate = THIS_YEAR>
GROUP BY <DATE_FUNC>(<field>)
ORDER BY <DATE_FUNC>(<field>)
```

## Checklist

- [ ] Every SELECT date function is repeated verbatim in GROUP BY
- [ ] No date-function result compared to a date literal in WHERE (use an integer)
- [ ] DAY_ONLY / HOUR_IN_DAY applied only to DateTime fields
- [ ] FISCAL_* not used if the org has custom fiscal years enabled
- [ ] Time-zone basis decided (convertTimezone where local-day bucketing matters)

## Validation

```bash
python3 scripts/check_soql_date_functions.py --query "SELECT CALENDAR_YEAR(CloseDate) yr, SUM(Amount) t FROM Opportunity GROUP BY CALENDAR_YEAR(CloseDate)"
# or, over a source tree:
python3 scripts/check_soql_date_functions.py --manifest-dir force-app/main/default
```

## Notes

(Record any deviations from the standard pattern and why.)
