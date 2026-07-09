# Gotchas — SOQL Aggregate Field-Type Support

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: AVG()/SUM() on a non-numeric field fails the whole query

**What happens:** the query does not return null or skip the column — it errors and the entire
request fails.

**When it occurs:** you apply `AVG()` or `SUM()` to any field that is not fully numeric — a date,
dateTime, text, email, url, picklist, or reference field. Only int, double, currency, and percent
support `AVG()` and `SUM()`.

**How to avoid:** confirm the field's type is int/double/currency/percent before reaching for
`AVG()`/`SUM()`. For dates use `MIN()`/`MAX()`; for categorical fields count them instead of
averaging.

---

## Gotcha 2: Seven field types support no aggregate function at all

**What happens:** even `COUNT()` on the field is rejected — there is no "at least you can count it"
fallback.

**When it occurs:** the field is base64, boolean, time, multipicklist, address, location, or
encryptedstring. `base64` is excluded specifically because aggregating it "wouldn't generate any
meaningful data," and the others are likewise non-aggregatable.

**How to avoid:** derive a supported field first — e.g. a number/formula field that encodes the
boolean as 1/0, or a separate text field extracted from an address — and aggregate that instead.

---

## Gotcha 3: Currency aggregates default to the corporate (system) currency

**What happens:** an ungrouped `SUM(Amount)` or `AVG(Amount)` returns a figure in the org's system
currency, converting each record from its own currency first — with nothing in the result to say
which currency it is.

**When it occurs:** the org has multi-currency enabled and you aggregate a currency field without
grouping by currency.

**How to avoid:** `GROUP BY CurrencyIsoCode` so every subtotal stays in a single, labeled currency;
or explicitly document that the total is a corporate-currency figure if that is genuinely what you
want.

---

## Gotcha 4: MIN()/MAX() on a picklist uses picklist sort order, not alphabetical

**What happens:** `MIN(StageName)` returns the stage that is *first in the picklist's Setup
ordering*, which may not be the alphabetically-first label — so "minimum stage" surprises anyone
expecting A–Z.

**When it occurs:** any time you apply `MIN()` or `MAX()` to a picklist field.

**How to avoid:** treat picklist MIN/MAX as "first/last in defined order." If you actually need
alphabetical order, aggregate the underlying label as text or sort the values another way; don't
assume the picklist order matches the alphabet.

---

## Gotcha 5: COUNT(field) silently ignores nulls — unlike COUNT() and COUNT(Id)

**What happens:** `COUNT(Email)` can return a smaller number than `COUNT(Id)` on the same result
set, with no error to explain the gap. The difference is the number of records where the field is
null.

**When it occurs:** you use `COUNT(fieldName)` or `COUNT_DISTINCT(fieldName)` expecting a total
row count. All aggregate functions ignore nulls **except** `COUNT()` and `COUNT(Id)`.

**How to avoid:** use `COUNT(Id)` (or `COUNT()`) when you want every row; reserve `COUNT(field)` /
`COUNT_DISTINCT(field)` for "how many records have this populated / how many distinct values,"
and label the metric accordingly.

---

## Gotcha 6: LIMIT is not allowed on an aggregate query without GROUP BY

**What happens:** adding `LIMIT` to an aggregate query that has no `GROUP BY` is rejected — "You
can't use a LIMIT clause in a query that uses an aggregate function, but does not use a GROUP BY
clause."

**When it occurs:** you write something like `SELECT COUNT(Id) FROM Account LIMIT 100`, expecting
LIMIT to cap the scan. A bare aggregate already collapses to one row, so LIMIT is meaningless
there and disallowed.

**How to avoid:** drop the `LIMIT` from ungrouped aggregates. Use `WHERE` to constrain the rows
that feed the aggregate; `LIMIT` (and `OFFSET`) are only valid on aggregate queries once a
`GROUP BY` produces multiple grouped rows.
