---
name: soql-format-function-localization
description: "Use when a SOQL SELECT clause or SOSL FIND/RETURNING clause must return number, date, time, or currency fields already localized to the running user's locale (e.g. $44,000.00 or 4/10/2025, 3:31 PM instead of a raw decimal or ISO 8601 string). Covers the FORMAT() function: its four supported field categories, the aliasing rule when the same field is queried twice, and nesting FORMAT() inside aggregate functions or convertCurrency(). NOT for grouping or filtering by date period — use apex/soql-date-functions. NOT for multi-currency setup and conversion rates — use data/currency-management-patterns."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - soql
  - sosl
  - localization
  - format-function
  - currency-formatting
triggers:
  - "format a currency field in a SOQL query so it shows the locale currency symbol and thousands separators"
  - "return dates from a SOQL query already formatted for the user's locale instead of raw ISO 8601"
  - "get both the raw value and a localized display value of the same field in one query"
  - "make SOQL or SOSL output match what users see in the Salesforce UI for numbers and dates"
  - "apply FORMAT() to an aggregate MIN/MAX result or a convertCurrency() value in a query"
inputs:
  - "A SOQL SELECT (or SOSL FIND/RETURNING) query that returns number, date, time, or currency fields"
  - "Whether the caller needs the raw value, the localized display value, or both side by side"
  - "The execution context that runs the query (REST/SOAP/Bulk query API, dynamic Apex SOQL, or a report)"
outputs:
  - "A SOQL/SOSL query using FORMAT() with correct aliasing"
  - "Guidance on nesting FORMAT() inside aggregate or convertCurrency() functions"
  - "An explicit note that FORMAT() emits a locale-dependent String, not the typed field value"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# SOQL FORMAT() Function — Localized Output

This skill activates when a query must return **display-ready, locale-aware strings** for number, date, time, or currency fields — so exported, integrated, or reported values match what a user sees in the Salesforce UI, rather than the raw decimal or ISO 8601 value the query engine returns by default. The mechanism is the `FORMAT()` function in a SOQL `SELECT` clause or a SOSL `RETURNING` field list.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the field is one of the four supported categories.** `FORMAT()` applies "localized formatting to standard and custom number, date, time, and currency fields." It does nothing for text, picklist, reference, or boolean fields — wrapping those is a mistake, not a no-op you can ignore.
- **Decide whether you need the raw value too.** `FORMAT()` returns a **string**, not the underlying typed value. If a consumer needs to do math, sort numerically, or round-trip the value, keep the unformatted field in the query as well — which then forces the aliasing rule below.
- **Know whose locale drives the output.** Formatting reflects "the appropriate format for the given user locale" — the *running user's* Locale, not the org default. The same query returns `12/28/2015` for a US user and `28/12/2015` or `28.12.2015` for others. That non-determinism is fine for UI parity and wrong for a fixed-format integration contract.
- **No maturity gate applies, but do not invent one.** The SOQL and SOSL reference pages document `FORMAT()` as a standard SELECT-clause function with **no Beta, Pilot, or Developer Preview label**. Treat it as standard, generally documented SOQL/SOSL functionality; do not assert a GA/Beta status the docs don't state.

---

## Core Concepts

### What FORMAT() does

`FORMAT()` wraps a field in the `SELECT` list and returns a locale-formatted **string** representation of that field's value. Per the reference, "when the FORMAT function is applied, fields reflect the appropriate format for the given user locale," and the result "matches what appears in the Salesforce Classic user interface." Concretely:

- **Datetime** — without `FORMAT()`, `LastModifiedDate` returns `2025-04-10T22:31:37.000+0000`; with it, `4/10/2025, 3:31 PM`.
- **Currency** — "using FORMAT with currencies returns a fully formatted value, such as `$44,000.00`, instead of a plain number."
- **Date** — `December 28, 2015` can come back as `2015-12-28`, `28-12-2015`, `28/12/2015`, `12/28/2015`, or `28.12.2015` depending on the org/user locale.

The output is a display artifact. It is not the field's typed value, and no downstream consumer should parse it as a number or a canonical date.

### The four supported categories — and only four

`FORMAT()` "supports standard and custom number, date, time, and currency fields." That is the complete list: number, date, time, currency. There is no localized formatting of text, ID, picklist, or checkbox fields through this function.

### Aliasing: optional, until it isn't

"The FORMAT function supports aliasing. In addition, aliasing is **required** when the query includes the same field multiple times." The canonical shape is the raw field and its formatted twin side by side, and the formatted one **must** carry an alias:

```sql
SELECT Id, LastModifiedDate, FORMAT(LastModifiedDate) formattedDate FROM Account
```

Without the `formattedDate` alias, the query references `LastModifiedDate` twice and errors. Give the formatted column a stable alias whenever the raw field is also selected.

### Nesting with aggregate and convertCurrency()

`FORMAT()` can wrap two other function results: "you can also nest it with aggregate or convertCurrency() functions."

- **Aggregate** — `SELECT FORMAT(MIN(closedate)) Amt FROM opportunity`. The aggregate runs, then `FORMAT()` localizes the single scalar it produces. Aggregate queries return `AggregateResult`, so you read the value by its alias.
- **convertCurrency()** — `SELECT amount, FORMAT(convertCurrency(amount)) convertedCurrency FROM Opportunity`. `convertCurrency()` requires a multi-currency org and "can't [be used] in a WHERE clause." It converts to the user's currency; `FORMAT()` then renders that converted amount with the locale symbol and separators.

### SOSL is symmetric

The same function exists for SOSL, applied inside a `RETURNING` field list: "use FORMAT with the FIND clause to apply localized formatting." Example: `FIND {Acme} RETURNING Account(Id, LastModifiedDate, FORMAT(LastModifiedDate) FormattedDate)`. The aliasing and nesting rules are identical.

---

## Common Patterns

### Raw + formatted side by side

**When to use:** a consumer needs the machine value for logic and a localized string for display in the same result row.

**How it works:** select the field twice — once bare, once wrapped — and alias the formatted column: `SELECT Id, Amount, FORMAT(Amount) amountDisplay FROM Opportunity`. The alias is mandatory here because `Amount` appears twice.

**Why not the alternative:** returning only the formatted value strands any code that needs to compute or compare; returning only the raw value pushes locale formatting into every client, duplicating logic Salesforce already localizes correctly.

### UI-parity reporting / export

**When to use:** an export or emailed report must read exactly like the Salesforce UI (currency symbols, thousands separators, locale dates) without a client-side formatting layer.

**How it works:** wrap each number/date/time/currency column in `FORMAT()` with a clear alias. The API query then returns display-ready strings that match Classic's rendering for the running user's locale.

**Why not the alternative:** hand-formatting on the client re-implements locale rules per platform and drifts from the org's actual settings; `FORMAT()` centralizes it in the query.

### Localized aggregate scalar

**When to use:** a dashboard tile or summary needs one localized figure — earliest close date, largest deal.

**How it works:** nest the aggregate inside `FORMAT()` and alias it — `SELECT FORMAT(MIN(CloseDate)) earliest FROM Opportunity`. Read `earliest` off the `AggregateResult`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Consumer needs to do math or sort numerically | Return the **raw** field (no `FORMAT()`) | `FORMAT()` output is a string; arithmetic/sort on it is wrong |
| Display must match the Salesforce UI for the viewer | Wrap the field in `FORMAT()` with an alias | Localizes to the running user's locale, Classic-parity |
| Both machine value and display value needed | Select field twice: bare + `FORMAT(field) alias` | Aliasing is required when a field appears more than once |
| Fixed-format integration contract (e.g. always `yyyy-MM-dd`) | Do **not** use `FORMAT()`; format explicitly downstream | Output varies by each user's locale — non-deterministic |
| Localizing an aggregate result | `FORMAT(MIN(field)) alias` | `FORMAT()` nests around aggregate functions |
| Localizing a converted currency amount | `FORMAT(convertCurrency(field)) alias` (multi-currency org) | `FORMAT()` nests around `convertCurrency()` |
| Filtering/sorting by the localized value | Filter/sort on the raw field instead | `FORMAT()` belongs in `SELECT`, not `WHERE`/`ORDER BY` |

---

## Recommended Workflow

1. **Classify the fields.** Confirm each field you want to localize is a number, date, time, or currency field — the only four categories `FORMAT()` supports. Drop the wrapper from any other type.
2. **Decide raw vs formatted vs both.** If any consumer needs the typed value, keep the bare field in the `SELECT` in addition to the formatted one.
3. **Write the query and alias correctly.** Wrap the display columns in `FORMAT()`. If the same field appears twice (raw + formatted), give the formatted column a required alias; alias aggregate/converted columns too.
4. **Add nesting where needed.** For a summary figure use `FORMAT(<aggregate>)`; for a converted amount in a multi-currency org use `FORMAT(convertCurrency(<field>))`. Keep `convertCurrency()` out of any `WHERE` clause.
5. **Retrieve by alias.** When the query runs as an aggregate (or in dynamic Apex SOQL), read each formatted column by its alias off the `AggregateResult`/`sObject`, and type it as a `String`.
6. **Verify against locale and context.** Confirm the rendered strings match the target locale, that no integration contract depends on a fixed format, and — if the query is inline Apex — that it compiles in your API version (prefer dynamic `Database.query` if inline support is uncertain). Run `scripts/check_soql_format_function_localization.py` over the source.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every `FORMAT()` wraps a number, date, time, or currency field — nothing else
- [ ] Any field selected both raw and formatted has an **alias** on the formatted column
- [ ] Aggregate and `convertCurrency()` columns wrapped by `FORMAT()` are aliased
- [ ] No `FORMAT()` (or `convertCurrency()`) sits in a `WHERE`, `HAVING`, or `ORDER BY` clause
- [ ] Consumers that need to compute/sort receive the raw field, not the formatted string
- [ ] No integration contract silently depends on a per-user, locale-variable string
- [ ] No GA/Beta/Pilot maturity claim was made about `FORMAT()` beyond what the docs state

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **The output is a String, not the value** — `FORMAT(Amount)` returns `"$44,000.00"`, so any downstream arithmetic, numeric sort, or `Date` parsing breaks. Keep the raw field for logic and use the formatted column only for display.
2. **Locale is the running user's, not the org's** — the same query returns `12/28/2015` for one user and `28.12.2015` for another. Great for UI parity, silently corrupting for a fixed-format export or a partner integration that expects one canonical format.
3. **Duplicate-field aliasing is mandatory, not optional** — selecting `LastModifiedDate` and `FORMAT(LastModifiedDate)` without an alias errors, because the field now appears twice. The alias is what disambiguates the two columns.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| SOQL/SOSL query with `FORMAT()` | A query that returns localized, display-ready strings for the chosen number/date/time/currency columns, aliased correctly |
| Field/format worksheet | The `templates/` cookbook filled in: each field mapped to raw / formatted / both, with the target locale and execution context recorded |
| Checker report | Output of `scripts/check_soql_format_function_localization.py` flagging missing aliases and misplaced `FORMAT()`/`convertCurrency()` usage |

---

## Related Skills

- `apex/soql-fundamentals` — the base `SELECT` syntax, aliasing, and function placement this skill builds on; consult it for overall query structure, then apply `FORMAT()` for the localized output layer.
- `data/multi-currency-and-advanced-currency-management` — the multi-currency (and dated-exchange-rate) setup that `convertCurrency()` depends on before you can wrap it in `FORMAT()`.
- `apex/soql-security` — CRUD/FLS still gates the underlying field even when the output is a formatted string; use it to keep `FORMAT()` queries enforcing field access.
