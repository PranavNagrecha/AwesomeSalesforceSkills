---
name: soql-aggregate-field-type-support
description: "Use when you need to know which of the six SOQL aggregate functions (AVG, COUNT, COUNT_DISTINCT, MIN, MAX, SUM) a given Salesforce field type supports — e.g. diagnosing why SUM() or AVG() on a date, text, picklist, or boolean field throws a query error, confirming a field is aggregatable before you write the query, or reasoning about multi-currency and picklist-sort-order semantics. Trigger keywords: soql aggregate field type support, sum/avg unsupported field type, aggregate function malformed query, which fields support avg sum, min max picklist sort order, currency aggregate system currency. NOT for GROUP BY / HAVING / ROLLUP / CUBE / AggregateResult iteration mechanics (use apex/apex-aggregate-queries), NOT for report-builder summary formulas or the Reporting/Analytics API, and NOT for declarative Roll-Up Summary fields."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "diagnosing why SUM() or AVG() throws a query error on a date, text, or picklist field"
  - "checking which field types support all six aggregate functions before writing the SOQL"
  - "how MIN() or MAX() orders a picklist field — alphabetical or the picklist's own sort order"
  - "my currency SUM() returns the wrong total in a multi-currency org"
  - "confirming whether a boolean, time, multipicklist, base64, or encrypted field can be aggregated at all"
tags:
  - soql
  - aggregate-functions
  - field-types
  - query-correctness
  - multi-currency
  - picklist
inputs:
  - "The field API name(s) and their data type(s) you intend to aggregate"
  - "The aggregate function(s) you want to apply (AVG, COUNT, COUNT_DISTINCT, MIN, MAX, SUM)"
  - "Whether the org is multi-currency (affects currency aggregate results)"
outputs:
  - "A supported / not-supported verdict per (field type × function) pair"
  - "The correct function or a refactor when the intended one is unsupported"
  - "Warnings on null handling, picklist sort order, and multi-currency defaulting"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# SOQL Aggregate Field-Type Support

This skill activates when a practitioner needs to know **which SOQL aggregate functions apply to which field types**. Salesforce publishes a dedicated reference page for exactly this because the six functions "aren't relevant for all field types" — `SUM()` and `AVG()` are numeric-only, several field types support no aggregate at all, and a few (currency, picklist) carry non-obvious semantics. The payoff is catching a `SUM(CloseDate)`-style mistake at authoring time instead of as a runtime query error.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Know the exact data type of every field you plan to aggregate.** "It's a number on screen" is not enough — a currency, a percent, a formula returning text, and a picklist all behave differently. Read the type from Setup → Object Manager or a describe call, not from the label.
- **The most common wrong assumption is that any field can be summed or averaged.** `AVG()` and `SUM()` require a *fully numeric* type (int, double, currency, percent). On a date, text, picklist, or boolean field the query fails — it does not silently return null.
- **The six functions are AVG, COUNT, COUNT_DISTINCT, MIN, MAX, SUM.** `MAX()` has been available since API version 18.0 and later. This is longstanding core SOQL reference behavior; the docs attach **no** GA/Beta/Pilot/Developer-Preview label to it — do not invent one.
- **Multi-currency changes the answer.** In a multi-currency org, aggregate results on currency fields default to the system (corporate) currency, not each record's currency.

---

## Core Concepts

### The six functions and what each returns

| Function | Returns | Field-type requirement |
|---|---|---|
| `AVG(field)` | Average value of a numeric field | Numeric only |
| `SUM(field)` | Total sum of a numeric field | Numeric only |
| `COUNT()` / `COUNT(fieldName)` | Number of rows matching the query | Broad (see matrix) |
| `COUNT_DISTINCT(field)` | Number of distinct **non-null** values | Broad (see matrix) |
| `MIN(field)` | Minimum value of a field | Broad (see matrix) |
| `MAX(field)` | Maximum value of a field (API 18.0+) | Broad (see matrix) |

### The compatibility matrix (the reference this skill exists for)

| Field type(s) | AVG | SUM | COUNT | COUNT_DISTINCT | MIN | MAX |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| **Numeric** — int, double, currency, percent | Yes | Yes | Yes | Yes | Yes | Yes |
| **Date/time** — date, dateTime | No | No | Yes | Yes | Yes | Yes |
| **Text-like** — reference/lookup, ID, email, phone, url, textarea, picklist, combobox, DataCategoryGroupReference | No | No | Yes | Yes | Yes | Yes |
| **No aggregate support** — base64, boolean, time, multipicklist, address, location, encryptedstring | No | No | No | No | No | No |
| **Calculated (formula)** | Depends on the formula's return type — apply the row for that type |

Two behaviors do not fit in a cell:

- **`base64` is excluded because aggregating it "wouldn't generate any meaningful data."** The exclusion is deliberate, not a bug.
- **`MIN()` / `MAX()` on a picklist uses the picklist's defined value sort order, not alphabetical order.** So `MIN(Stage)` returns the *first* stage as ordered in Setup, which may not be the alphabetically-first label.

### Null handling — COUNT() is the exception

All aggregate functions ignore null values **except `COUNT()` and `COUNT(Id)`**. Practical consequence:

- `COUNT()` and `COUNT(Id)` count **every** matching row (nulls included).
- `COUNT(fieldName)` and `COUNT_DISTINCT(fieldName)` count only rows where that field is **populated** (nulls skipped).

So `COUNT(Id)` vs `COUNT(Email)` on the same result set can legitimately differ — the gap is the number of records with a blank Email.

### Formula fields resolve by return type

A calculated (formula) field has no fixed rule: "Support for aggregate functions depends on the type of the calculated field." A formula returning Currency behaves like currency (all six); a formula returning Text behaves like text (no AVG/SUM). Determine the formula's return type first, then apply the matching matrix row.

---

## Common Patterns

### Earliest / latest instead of "average date"

**When to use:** you need a date summary across a group but reached for `AVG()`/`SUM()` out of SQL habit.

**How it works:** date and dateTime support `MIN()` and `MAX()` (and the counts), so use `MIN(CreatedDate)` for the earliest and `MAX(CreatedDate)` for the latest. There is no average or sum of dates — the query will error if you try.

**Why not the alternative:** `AVG(CreatedDate)` is not "unsupported but harmless" — it fails the query outright, breaking the whole request, not just that column.

### Multi-currency aggregate on a currency field

**When to use:** you `SUM()` or `AVG()` an Amount-style currency field in a multi-currency org.

**How it works:** the aggregate result defaults to the corporate (system) currency, so a raw `SUM(Amount)` blends converted values into one number. To keep each subtotal in a single, unambiguous currency, `GROUP BY CurrencyIsoCode`:

```sql
SELECT CurrencyIsoCode, SUM(Amount) total
FROM Opportunity
GROUP BY CurrencyIsoCode
```

**Why not the alternative:** an ungrouped `SUM(Amount)` in a mixed-currency org produces a corporate-currency figure that few stakeholders expect and none can trace back to a currency; the grouped form is auditable.

### Count all rows vs count populated values

**When to use:** you're reporting "how many" and need to be precise about nulls.

**How it works:** use `COUNT(Id)` (or `COUNT()`) for the total record count; use `COUNT(field)` or `COUNT_DISTINCT(field)` when you specifically want the count of records where `field` is populated (or the count of unique values). Keep the SOQL inside a selector method — see [`templates/apex/BaseSelector.cls`](../../../templates/apex/BaseSelector.cls) — rather than inline in a trigger or controller.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need a total or average of a number | `SUM()` / `AVG()` — but only on int, double, currency, or percent | Only fully numeric types support AVG/SUM |
| Need earliest / latest of a date or dateTime | `MIN()` / `MAX()` | Dates support MIN/MAX/COUNT but not AVG/SUM |
| Field is boolean, time, multipicklist, base64, address, location, or encryptedstring | Restructure — derive a numeric or supported field first | None of the six functions apply to these types |
| Need a distinct count of a text or picklist field | `COUNT_DISTINCT(field)` (ignores nulls) | Text-like types support the counts, MIN, and MAX |
| Aggregating a formula field | Look up the formula's return type, then apply that type's matrix row | Support "depends on the type of the calculated field" |
| Summing a currency field in a multi-currency org | `GROUP BY CurrencyIsoCode`; know the ungrouped result is corporate currency | Currency aggregates default to the system currency |
| Ordering a picklist with MIN/MAX | Expect picklist **sort order**, not alphabetical | MIN/MAX use the picklist's defined value order |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Enumerate the fields and their exact data types.** For each field you want to aggregate, record its API name and type (Object Manager or a describe). For formula fields, record the *return* type.
2. **Look up each (type × function) cell in the compatibility matrix.** If the cell is "No," the query will fail when parsed or executed — do not ship it.
3. **Swap or refactor unsupported combinations.** Replace `AVG()`/`SUM()` on non-numeric fields with `MIN()`/`MAX()`/`COUNT()` as appropriate, or derive a numeric field upstream when you truly need a total.
4. **Choose COUNT semantics deliberately.** Use `COUNT(Id)`/`COUNT()` for total rows; use `COUNT(field)`/`COUNT_DISTINCT(field)` when nulls should be excluded.
5. **Handle currency and picklist semantics.** For multi-currency currency aggregates, decide whether to `GROUP BY CurrencyIsoCode`; for `MIN()`/`MAX()` on picklists, confirm picklist sort order gives the value you expect.
6. **Validate before shipping.** Run `scripts/check_soql_aggregate_field_type_support.py` over the query (optionally with a field-type map) and confirm it in the Developer Console Query Editor.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every aggregated field's data type is confirmed and the chosen function shows "Yes" for that type in the matrix
- [ ] No `AVG()` or `SUM()` on a non-numeric field (date, text, picklist, boolean, etc.)
- [ ] No aggregate function applied to base64, boolean, time, multipicklist, address, location, or encryptedstring fields
- [ ] COUNT semantics chosen deliberately — `COUNT(Id)`/`COUNT()` count all rows; `COUNT(field)`/`COUNT_DISTINCT` ignore nulls
- [ ] Formula-field aggregates verified against the formula's return type
- [ ] Multi-currency currency aggregates grouped by `CurrencyIsoCode` or explicitly documented as corporate-currency totals
- [ ] No `LIMIT` clause on an aggregate query that has no `GROUP BY`

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`AVG()`/`SUM()` on a non-numeric field fails the query** — date, text, picklist, and boolean fields support only the counts and (where applicable) MIN/MAX. The whole request errors; it does not degrade gracefully.
2. **Seven types support *no* aggregate at all** — base64, boolean, time, multipicklist, address, location, and encryptedstring. No function, including COUNT, works on them; you must derive a supported field.
3. **Currency aggregates default to the system (corporate) currency** in a multi-currency org — an ungrouped `SUM(Amount)` is not "the sum of what each record shows."
4. **`MIN()`/`MAX()` on a picklist uses picklist sort order, not alphabetical** — the "minimum" stage is the first one in Setup's ordering, which can surprise anyone expecting A–Z.
5. **`COUNT(field)` quietly ignores nulls** — unlike `COUNT()`/`COUNT(Id)`, so a populated-field count can be lower than the row count without any error to signal it.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `templates/soql-aggregate-field-type-support-template.md` | The full compatibility matrix plus a per-query pre-flight worksheet to fill in for your fields |
| `scripts/check_soql_aggregate_field_type_support.py` | Stdlib checker that flags unsupported (field type × function) combinations and the LIMIT-without-GROUP-BY error in a SOQL string or file |

---

## Related Skills

- `apex/apex-aggregate-queries` — the *mechanics* once you know a field is aggregatable: GROUP BY, HAVING, ROLLUP/CUBE, GROUPING(), and reading `AggregateResult.get('alias')`. This skill answers "can I aggregate this field type at all?"; that one answers "how do I write and iterate the grouped query?"
- `apex/apex-decimal-arithmetic-precision` — when a `SUM()`/`AVG()` result feeds further math and you need to control Decimal scale and rounding.
