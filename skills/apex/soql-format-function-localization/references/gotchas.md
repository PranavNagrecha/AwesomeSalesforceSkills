# Gotchas — SOQL FORMAT() Function (Localized Output)

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The result is a String, not the typed value

**What happens:** code that reads a `FORMAT()` column as a `Decimal`, `Double`, `Date`, or
`Datetime` throws a cast/type error, or arithmetic on it silently misbehaves.

**When it occurs:** any time a consumer treats the formatted column as the field's value.
`FORMAT(Amount)` returns a display string like `$44,000.00`, not `44000.00`.

**How to avoid:** keep the raw field in the query for anything computational and read the
formatted column as a `String`. Only the presentation layer should touch it.

---

## Gotcha 2: Output depends on the running user's locale

**What happens:** the same query returns `12/28/2015` for a US user and `28/12/2015`,
`28.12.2015`, `28-12-2015`, or `2015-12-28` for others — and a "1,234.50" for one user is
"1.234,50" for another.

**When it occurs:** whenever the query runs for users with different Locale settings — common
across a global org, and easy to miss when a developer tests only under their own locale.

**How to avoid:** use `FORMAT()` for UI parity, never for a contract that must be one fixed
format. If an integration or file needs a canonical format, format explicitly downstream (e.g.
`Datetime.format('yyyy-MM-dd')` in Apex) and leave `FORMAT()` out.

---

## Gotcha 3: Aliasing is required when the field appears twice

**What happens:** `SELECT LastModifiedDate, FORMAT(LastModifiedDate) FROM Account` fails to run.

**When it occurs:** the raw field and its `FORMAT()` twin are both in the `SELECT` list without
an alias on the formatted column — the field is now referenced more than once.

**How to avoid:** always alias the formatted column when the raw field is also selected:
`FORMAT(LastModifiedDate) formattedDate`. Alias aggregate/`convertCurrency()` columns too, and
read every aliased column back by that alias.

---

## Gotcha 4: FORMAT() only covers four field categories

**What happens:** wrapping a text, picklist, ID, reference, or checkbox field in `FORMAT()` is a
query authoring error, not a graceful no-op.

**When it occurs:** an author assumes `FORMAT()` "localizes any field," then applies it to a
picklist label or a text field.

**How to avoid:** restrict `FORMAT()` to standard/custom **number, date, time, and currency**
fields — the complete documented set. For picklist display labels use `toLabel()` instead; that
is a different function with a different purpose.

---

## Gotcha 5: convertCurrency() cannot go in a WHERE clause

**What happens:** a query that nests `FORMAT(convertCurrency(field))` and also filters with
`convertCurrency(field)` in the `WHERE` clause returns an error.

**When it occurs:** developers try to both convert-for-display and convert-for-filter in one
query. `convertCurrency()` is allowed in the `SELECT` list but "can't [be used] in a WHERE
clause." It also requires a multi-currency-enabled org, and under a `GROUP BY`/`HAVING`
aggregate, currency comes back in the org's default currency, not the converted one.

**How to avoid:** keep `convertCurrency()` (and therefore its `FORMAT()` wrapper) in the
`SELECT` list. For currency comparisons in `WHERE`, use ISO currency-code literals (e.g.
`Amount > USD5000`) against the raw field.
