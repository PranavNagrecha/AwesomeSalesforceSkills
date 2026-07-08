# SOQL USING SCOPE — Planning & Reference Sheet

Copy this sheet when adding a `USING SCOPE` clause to a query. It combines a quick
reference (so you don't guess syntax) with a short plan (so the query is also secure
and object-appropriate). `USING SCOPE` is "Available in API version 32.0 and later";
the docs attach no GA/Beta/Pilot label to the clause itself.

## 1. Clause position (memorize this)

```
SELECT fieldList [subquery][...]
FROM objectType[,...]
    USING SCOPE filterScope        <-- after FROM
WHERE conditionExpression          <-- before WHERE
[WITH USER_MODE]                   <-- security is separate (Summer '23+)
[ORDER BY ...] [LIMIT ...]
```

## 2. The eight valid SOQL scope values

| Value | Returns | Constraint |
|---|---|---|
| `delegated` | Records delegated to another user for action | — |
| `everything` | All (accessible) records | Mandatory for the Scoping Rules SOQL operator |
| `mine` | Records owned by the running user | — |
| `mine_and_my_groups` | Running user's records + their queues | `ProcessInstanceWorkItem` only |
| `my_territory` | Records in the running user's territory | Territory management enabled |
| `my_team_territory` | Records in the running user's team's territory | Territory management enabled |
| `scopingRule` | Records matching the active scoping rule | An active scoping rule on the object |
| `team` | Records assigned to a team (e.g. Account team) | Object must support teams |

> Not valid in SOQL: `Queue`, `AssignedToMe`, `SalesTeam`, `all`, `owned` — the first
> three are Metadata API ListView `filterScope` values; the last two are invented.

## 3. Request

**Skill:** `soql-using-scope-clause`

- Query / selector method to scope:
- Target sObject:
- Desired audience (mine / team / my_territory / delegated / queues / scoping rule):

## 4. Pre-flight checklist

- [ ] Object confirmed (via `describeSObject()` / sObject Describe) to support the chosen scope
- [ ] Prerequisite verified (territory management on / active scoping rule / Performance-Unlimited edition for the Scoping Rules operator)
- [ ] "The running user" is the intended principal in this execution context (interactive vs. async/system)
- [ ] Scope value uses the SOQL enumeration above (not a Metadata API list-view value)
- [ ] Clause placed after `FROM`, before `WHERE`
- [ ] Security added separately: `WITH USER_MODE` (or `with sharing` + CRUD/FLS) — scope is NOT enforcement
- [ ] If inside a scoping-rule SOQL operator: `USING SCOPE EVERYTHING` on the outer *and* every nested `SELECT`

## 5. Draft query

```apex
// Fill in. Keep SOQL in a selector (see templates/apex/BaseSelector.cls).
[
    SELECT ...
    FROM <Object>
    USING SCOPE <value>
    WHERE ...
    WITH USER_MODE
]
```

## 6. Lint

```bash
python3 ../scripts/check_soql_using_scope_clause.py --file path/to/YourSelector.cls
```

## 7. Notes / deviations

(Record why this scope was chosen over an explicit filter, and any context-specific caveats.)
