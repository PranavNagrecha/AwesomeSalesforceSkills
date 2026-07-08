# Multi-Select Picklist Query Builder

Use this worksheet to turn a filtering requirement into a correct SOQL clause against a
multi-select picklist field, then drop it into static or dynamic Apex safely. Fill in the
blanks top to bottom; the cheat-sheet and Apex skeletons at the end are copy-paste ready.

---

## 1. Confirm the field

- **Object:** `__________`  (e.g. `Contact`)
- **Field API name:** `__________`  (e.g. `Interests__c`)
- **Field type is multi-select?** [ ] yes — *Picklist (Multi-Select)* / metadata `<type>MultiselectPicklist</type>`
  - If **no** (single-select), stop — use plain `=` or `IN` and none of the below applies.
- **Matching by:** [ ] display label  [ ] value **API name** (requires **API version 39.0+**)

---

## 2. State the requirement as groups

Write each condition as a group of values, and mark whether the values in the group must be
**ALL** selected (AND) or the groups are alternatives (OR between groups).

| Group | Values (must ALL be selected together) | Semicolon operand |
|-------|----------------------------------------|-------------------|
| 1     | `__________`                           | `'val;val'`       |
| 2     | `__________`                           | `'val'`           |
| 3     | `__________`                           | `'val;val'`       |

- Include (records that HAVE these) → use `INCLUDES`
- Exclude (records that must NOT have these) → use `EXCLUDES`

---

## 3. Grammar cheat-sheet

| You want… | Write | Meaning |
|---|---|---|
| Has value X (X may be one of several) | `INCLUDES ('X')` | Containment |
| Has X **and** Y both selected | `INCLUDES ('X;Y')` | Semicolon = AND inside one operand |
| Has X **or** Y selected | `INCLUDES ('X','Y')` | Comma = OR between operands |
| Has (X and Y) **or** Z | `INCLUDES ('X;Y','Z')` | Combine both |
| Does **not** have X | `EXCLUDES ('X')` | Negative containment |
| Selection is **exactly** X and nothing else | `= 'X'` | Whole-string exact match (rare) |

**Traps:**
- `= 'X'` / `!= 'X'` match the *entire* stored string, so they under-match "has X". Use `INCLUDES`/`EXCLUDES`.
- A comma **inside** quotes (`'X,Y'`) is part of the literal, not an OR. OR is a comma **between** operands.
- `LIKE '%X%'` is **not** the containment operator — it matches substrings (`Xing`) across the blob.
- The multi-select field **cannot** appear in `ORDER BY` (unsupported data type). Sort on another field.

---

## 4. Assemble the clause

```
WHERE <field> <INCLUDES|EXCLUDES> (<operand1>, <operand2>, ...)
```

**Filled example:**

```sql
SELECT Id, __________
FROM   __________
WHERE  __________ INCLUDES ('____;____', '____')
```

---

## 5. Apex — static (bind, injection-safe) — PREFERRED

Build each group's semicolon string in Apex, pass them as a bound list. Filter literals in a
`WHERE` clause are a supported bind position, and a bind works with `INCLUDES`.

```apex
List<String> groups = new List<String>{ '____;____', '____' }; // group1 (AND), group2, ...
List<SObject> rows = [
    SELECT Id, ____________
    FROM   ____________
    WHERE  ____________ INCLUDES :groups
    WITH   USER_MODE
];
```

## 6. Apex — dynamic (only when the group shape is truly runtime)

Never concatenate raw input into the query text. Keep values in binds; if a literal must be
inlined, escape it with `String.escapeSingleQuotes`.

```apex
List<String> groups = buildGroups(userInput); // each already grouped with ';'
String soql =
    'SELECT Id FROM ____________ ' +
    'WHERE ____________ INCLUDES :groups';
List<SObject> rows = Database.queryWithBinds(
    soql,
    new Map<String, Object>{ 'groups' => groups },
    AccessLevel.USER_MODE
);
```

---

## 7. Pre-ship checklist

- [ ] Field confirmed multi-select (not single-select)
- [ ] `INCLUDES`/`EXCLUDES` used for containment; `=`/`!=` only for exact whole-selection
- [ ] Semicolons (AND) and commas (OR) match the requirement in section 2
- [ ] Every operand is single-quoted or bound (no bare tokens)
- [ ] Run-time values are bound, not concatenated
- [ ] Field is **not** in `ORDER BY`
- [ ] Matching by API name only if the query runs at API 39.0+
- [ ] Ran `scripts/check_soql_multiselect_picklist_queries.py --manifest-dir <src>` clean
