# SOSL External Object Search — Review Worksheet

Use this template when writing or debugging a SOSL search that targets a Salesforce Connect
external object (an object whose API name ends in `__x`).

## Scope

**Skill:** `sosl-external-object-search-limits`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- External object(s) (`__x`): 
- Adapter type: OData 2.0 / OData 4.0 / custom (Apex Connector Framework)
- Searchable text field(s) (`Text` / `Text Area` / `Long Text Area`): 
- Search enabled on the external **object**? yes / no
- Search enabled on the external **data source**? yes / no
- Last data-source **sync** (may have reset object search)? 

## Safe-SOSL Skeleton

Adapt this instead of porting a standard-object query. Name the external object explicitly in
`RETURNING`, list only text fields, keep the FIND term ≤ 100 characters, use wildcards not `LIKE`.

```apex
List<List<SObject>> hits = [
    FIND '<term*>'                       // <= 100 chars, wildcards ok (* ?), no LIKE
    IN ALL FIELDS
    RETURNING <Object>__x(<TextFieldA__c>, <TextFieldB__c>)
];
List<<Object>__x> rows = (List<<Object>__x>) hits[0];
```

## Restriction Compliance Matrix

Tick each row; every unchecked box is a likely failure.

| Restriction | Scope | OK? |
|---|---|---|
| Search enabled on object **and** data source | all | [ ] |
| At least one searchable text field on the object | all | [ ] |
| External object named explicitly in `RETURNING` | all | [ ] |
| FIND search term ≤ 100 characters | all | [ ] |
| No `INCLUDES` / `LIKE` / `EXCLUDES` | all | [ ] |
| No `toLabel()` | all | [ ] |
| No `UPDATE TRACKING` / `UPDATE VIEWSTAT` | all | [ ] |
| No `WITH DATA CATEGORY` | all | [ ] |
| No logical operators (`AND`/`OR`/`AND NOT`) in FIND | OData adapters | [ ] |
| No `convertCurrency()` | custom adapters | [ ] |
| No generic `WITH` clause | custom adapters | [ ] |

## "Returns no records" — Diagnosis Order

1. [ ] Search enabled on the external **data source**
2. [ ] Search enabled on the external **object** (re-check after every sync — sync overwrites it)
3. [ ] Object has at least one searchable **text** field
4. [ ] Object named explicitly in `RETURNING`
5. [ ] FIND term ≤ 100 chars and free of unsupported operators

## Validation

Run the skill linter against your query or source tree:

```bash
python3 scripts/check_sosl_external_object_search_limits.py --query "FIND 'Acme*' RETURNING Order__x(Name__c)"
python3 scripts/check_sosl_external_object_search_limits.py --manifest-dir force-app/main/default --adapter odata
```

## Notes

- Adapter type determines which adapter-scoped rows apply — don't generalize OData or custom-adapter
  rules across adapter types.
- The reference page states no GA/Beta/Pilot maturity — do not add one.
- Record any deviation from the standard pattern and why.
