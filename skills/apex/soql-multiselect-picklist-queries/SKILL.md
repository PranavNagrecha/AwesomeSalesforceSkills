---
name: soql-multiselect-picklist-queries
description: "Use when filtering SOQL (static or dynamic Apex) on a multi-select picklist field — the four operators =, !=, INCLUDES, EXCLUDES, the semicolon (AND) / comma (OR) grouping inside quoted operands, querying by a value's API name vs display label (API 39.0+), and why the field can't appear in ORDER BY. Trigger keywords: multi-select picklist, multiselect, INCLUDES, EXCLUDES, semicolon, 'field contains value'. NOT for single-select picklist filtering (use plain = / IN), NOT for query performance/selectivity tuning (use data/soql-query-optimization), and NOT for defining or maintaining the picklist field itself (use admin/picklist-and-value-sets)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
triggers:
  - "how do I query records where a multi-select picklist contains a specific value in SOQL"
  - "filtering on two values that must both be selected in a multi-select picklist"
  - "my SOQL equals filter on a multi-select picklist misses records that clearly have the value"
  - "using INCLUDES and EXCLUDES to match multi-select picklist selections in an Apex query"
  - "ORDER BY on a multi-select picklist field throws an error"
tags:
  - soql-multiselect-picklist-queries
  - multi-select-picklist
  - includes-excludes
  - soql-where-clause
  - semicolon-grouping
inputs:
  - "The multi-select picklist field API name and the object it lives on"
  - "The values to match, and whether each set of values must be ALL selected (AND) or ANY-of (OR)"
  - "Whether the query is static SOQL or dynamic (Database.query) Apex, and the target API version"
outputs:
  - "A correct SOQL WHERE clause using INCLUDES / EXCLUDES with semicolon-AND / comma-OR grouping"
  - "An injection-safe Apex query (bind variable or escaped dynamic string) for the multi-select filter"
  - "A rewrite of fragile = / != / LIKE / ORDER BY usage on the multi-select field"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# SOQL Multi-Select Picklist Queries

This skill activates when a SOQL query has to filter on a multi-select picklist field. A multi-select picklist stores every selected value in one semicolon-delimited string, so ordinary equality is fragile and the query language exposes dedicated containment operators — `INCLUDES` and `EXCLUDES` — with their own semicolon-AND / comma-OR grammar. It also carries a hard restriction: a multi-select picklist may not appear in `ORDER BY`.

The SOQL reference documents this as standard `WHERE`-clause syntax and stamps **no GA/Beta/Pilot label** on it. The only version gate is that querying a value by its **API name** (which can differ from the display label) is available in **API version 39.0 and later**.

---

## Before Starting

Gather this context before writing the query:

- **Confirm the field is actually a multi-select picklist.** In Setup the field type reads *Picklist (Multi-Select)*; in metadata the field's `<type>` is `MultiselectPicklist`. If it is an ordinary single-select picklist, none of this applies — use plain `=` or `IN`. Guessing wrong is the most common source of "why doesn't my filter work."
- **Decide AND vs OR per group.** For each value or group of values, know whether the record must have *all* of them selected (AND) or *any* of them (OR). That decision maps directly to semicolons and commas — get it explicit before you type.
- **Know whether you are matching the label or the API name.** A value's API name can differ from what users see. Filtering by API name is only supported in **API version 39.0+**; below that you match the display value.
- **Know where the query runs.** Static SOQL can bind a value directly; dynamic SOQL built by string concatenation is a SOQL-injection surface (see the Security pillar in `references/well-architected.md`).

---

## Core Concepts

### The four operators

A multi-select picklist supports exactly four comparison operators in a `WHERE` clause:

| Operator | Meaning (per the SOQL reference) |
|---|---|
| `=` | Equals the specified string |
| `!=` | Does not equal the specified string |
| `INCLUDES` | Contains the specified string |
| `EXCLUDES` | Does not contain the specified string |

`INCLUDES` and `EXCLUDES` are containment tests — they are what you almost always want. `=` and `!=` compare against the **entire** stored string.

### Semicolon = AND, comma = OR

The grammar lives *inside* the quoted operands:

- A **semicolon** joins values that must **all** be selected on the same record. `'AAA;BBB'` means "AAA and BBB are both selected."
- A **comma** separates alternative operands inside `INCLUDES(...)` / `EXCLUDES(...)` and expresses **OR** across those groups.

```sql
-- Records where AAA AND BBB are both selected, OR CCC is selected:
SELECT Id, MSP1__c FROM CustObj__c WHERE MSP1__c INCLUDES ('AAA;BBB','CCC')
```

The official worked example resolves like this. `INCLUDES ('AAA;BBB','CCC')` matches a stored value of `'AAA;BBB'` or `'AAA;BBB;DDD'` (they satisfy the first group), and also `'CCC'`, `'CCC;EEE'`, or `'AAA;CCC'` (they satisfy the second group). A record whose only selection is `'AAA'` matches neither group.

### `=` is a whole-string exact match, not a containment test

The reference example `WHERE MSP1__c = 'AAA;BBB'` matches only records whose stored value is exactly the string `AAA;BBB`. Because the stored value is one semicolon-delimited string, `=` is brittle: a record that also has `DDD` selected (stored as `AAA;BBB;DDD`), or that serialized the same two values in a different order, will **not** match. Reach for `=` / `!=` only when you truly need an exact-selection match; use `INCLUDES` / `EXCLUDES` for "has this value."

### Label vs API name (API 39.0+)

Since **API version 39.0**, you can filter by a picklist value's **API name**, which can differ from the actual (display) value. Below 39.0 you filter by the display value. This matters when labels have been translated or renamed while the underlying API names stayed stable.

### Multi-select picklist is not sortable

A multi-select picklist is one of the data types that **cannot** appear in an `ORDER BY` clause (alongside rich text area, long text area, encrypted fields, and data category group reference). Attempting it is a query error, not a silent no-op. Sort on a different field (or sort in Apex after the query).

---

## Common Patterns

### Containment — "has this value" (INCLUDES)

**When to use:** the everyday case — find records where a value (or a required set of values) is selected, regardless of what else is selected.

**How it works:** put each required-together set in one quoted operand with semicolons, and OR alternative sets with commas.

```sql
-- Interests includes Golf, OR includes (Tennis AND Squash):
SELECT Id FROM Contact WHERE Interests__c INCLUDES ('Golf','Tennis;Squash')
```

**Why not the alternative:** `Interests__c = 'Golf'` matches only contacts whose *sole* selection is Golf; `LIKE '%Golf%'` looks tempting but risks matching substrings of other values (e.g. `Golfing`) and reads across the whole delimited blob unpredictably.

### Exclusion — "does not have this value" (EXCLUDES)

**When to use:** filter records *out* by selection.

**How it works:** `EXCLUDES` is the negative of `INCLUDES` with the same semicolon/comma grammar.

```sql
-- Exclude anyone who selected either Spam OR (Bulk AND Promo):
SELECT Id FROM Contact WHERE Interests__c EXCLUDES ('Spam','Bulk;Promo')
```

**Why not the alternative:** `!= 'Spam'` only excludes records whose entire selection is exactly `Spam`; someone with `Spam;News` would slip through.

### Injection-safe filtering in Apex

**When to use:** the values come from user input, a Flow, an LWC, or any run-time source.

**How it works:** prefer a **static** SOQL query with a bind variable — the SOQL reference lists *filter literals in `WHERE` clauses* as a supported bind position, and demonstrates a bind used with `INCLUDES`. Build the semicolon/comma grouping in the String you bind:

```apex
String group1 = 'Tennis;Squash';         // both must be selected
String group2 = 'Golf';                   // OR this one
// Static SOQL, bound literals — no string concatenation into the query:
List<Contact> matches = [
    SELECT Id FROM Contact
    WHERE Interests__c INCLUDES (:group1, :group2)
];
```

If you must build the clause dynamically, do not concatenate raw input into the query string; escape it (`String.escapeSingleQuotes`) or, better, keep the values in bind variables. See `apex/apex-dynamic-soql-binding-safety`.

**Why not the alternative:** concatenating user-supplied values straight into a `Database.query(...)` string is the classic SOQL-injection hole, and the semicolon grammar makes hand-built strings easy to get subtly wrong.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| "Record has value X selected" (X may be one of several selections) | `INCLUDES ('X')` | Containment test; ignores other selections |
| "Record has X **and** Y both selected" | `INCLUDES ('X;Y')` | Semicolon = AND inside one operand |
| "Record has X **or** Y selected" | `INCLUDES ('X','Y')` | Comma = OR across operands |
| "Record's selection is exactly X and nothing else" | `= 'X'` | Whole-string exact match is what you want here |
| "Record does not have X selected" | `EXCLUDES ('X')` | Negative containment; `!= 'X'` only excludes the exact-`X` case |
| Values come from user/Flow/LWC input | Static SOQL with `:bindVar`, grouping built in the String | Injection-safe; filter literals are a supported bind position |
| Need to sort results by the multi-select field | Not possible in `ORDER BY` — sort on another field or in Apex | Multi-select picklist is unsupported in `ORDER BY` |
| Labels were translated/renamed | Filter by the value's **API name** (API 39.0+) | API name is stable; display label may differ |

---

## Recommended Workflow

1. **Confirm the field type.** Verify in Setup or metadata that the field is `MultiselectPicklist`. If it is single-select, stop — use `=` / `IN` instead.
2. **Translate the requirement into groups.** Write out each value set and label it AND (semicolon-joined) or OR (separate operand). This is the step people skip and then debug.
3. **Choose the operator.** `INCLUDES` for "has value(s)", `EXCLUDES` for "does not have", and `=` / `!=` only for exact whole-selection matches.
4. **Decide label vs API name.** If matching by API name, confirm the query runs at API version 39.0 or later.
5. **Make it injection-safe.** In Apex, put run-time values in bind variables (build the semicolon/comma grouping inside the bound String); never concatenate raw input into a dynamic query.
6. **Keep the field out of ORDER BY.** If results need sorting, order by a different field or sort the returned list in Apex.
7. **Validate.** Run `scripts/check_soql_multiselect_picklist_queries.py` over the source to catch `=`/`!=`/`LIKE`/`ORDER BY` on the multi-select field and missing-quote grouping bugs.

---

## Review Checklist

Run through these before marking the query done:

- [ ] The target field is confirmed multi-select, not single-select
- [ ] `INCLUDES` / `EXCLUDES` is used for containment; `=` / `!=` only for true exact-selection matches
- [ ] Semicolons (AND) and commas (OR) inside the operands match the stated requirement
- [ ] Each operand is a single-quoted string literal (or a bind variable), not a bare/unquoted token
- [ ] Run-time values are bound, not concatenated, into the query
- [ ] The multi-select field does not appear in `ORDER BY`
- [ ] If matching by API name, the query runs at API version 39.0+

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`=` silently under-matches** — `Field__c = 'AAA'` matches only records whose *entire* selection is `AAA`; anyone who also picked another value is excluded with no error. This masquerades as "the filter works" on demo data (one value selected) and breaks in production. Use `INCLUDES`.
2. **`ORDER BY` on the field is a hard error** — multi-select picklist is an unsupported `ORDER BY` data type. The query fails to compile/run; it does not fall back to unsorted.
3. **Semicolon vs comma is easy to invert** — `INCLUDES ('AAA,BBB')` (comma inside the quotes) and `INCLUDES ('AAA;BBB')` (semicolon) mean different things, and a comma placed *inside* a single operand is treated as part of the literal, not as an OR separator. OR must be *between* quoted operands.
4. **API name ≠ label** — filtering by the display label works, but if labels were translated or edited, matching by the value's API name (API 39.0+) is the stable choice; below 39.0 you have only the display value.
5. **`LIKE` is a trap** — `LIKE '%Golf%'` seems like a containment test but matches substrings across the delimited blob (e.g. `Golfing`, or a value that merely contains the letters) and is not the supported containment operator. Use `INCLUDES`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| SOQL `WHERE` clause | `INCLUDES` / `EXCLUDES` (or exact `=`) filter with correct semicolon-AND / comma-OR grouping |
| Injection-safe Apex query | Static SOQL binding the grouped value String(s), or an escaped dynamic query |
| `templates/soql-multiselect-picklist-queries-template.md` | Fill-in worksheet + operator/grammar cheat-sheet that turns a requirement into the right clause |
| `scripts/check_soql_multiselect_picklist_queries.py` | Stdlib validator that flags fragile `=`/`!=`/`LIKE`/`ORDER BY` and missing-quote grouping on multi-select fields |

---

## Related Skills

- `apex/apex-dynamic-soql-binding-safety` — how to bind values (including into `INCLUDES`) and avoid SOQL injection when the query is built dynamically.
- `apex/soql-null-ordering-patterns` — the broader `ORDER BY` semantics; relevant because the multi-select field is excluded from sorting.
- `admin/picklist-and-value-sets` — defining and maintaining the multi-select field, its values, and the label-vs-API-name distinction this skill filters on.
- `data/soql-query-optimization` — selectivity and performance; multi-select picklist filters are not selective, so pair this skill with optimization work on large objects.
