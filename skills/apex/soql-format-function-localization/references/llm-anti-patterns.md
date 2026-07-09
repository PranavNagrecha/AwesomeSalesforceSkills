# LLM Anti-Patterns — SOQL FORMAT() Function (Localized Output)

Common mistakes AI coding assistants make when generating or advising on SOQL/SOSL `FORMAT()`.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Reaching for Apex formatting instead of FORMAT()

**What the LLM generates:** a query that returns the raw field, then Apex that hand-formats it —
`String display = amt.format();` or a `Datetime.format(...)` loop — when the ask was simply
"return the value formatted for the user's locale."

**Why it happens:** Apex `String.format()` / `Datetime.format()` dominate training data, so the
model routes formatting through code it has seen more often than the SOQL function.

**Correct pattern:**

```sql
SELECT Id, FORMAT(Amount) amountDisplay FROM Opportunity
```

**Detection hint:** an `sObject.get(...)` value being fed into `.format()` in Apex when the
requirement was just localized query output — the localization could have happened in `SELECT`.

---

## Anti-Pattern 2: Omitting the alias when the field is selected twice

**What the LLM generates:** `SELECT LastModifiedDate, FORMAT(LastModifiedDate) FROM Account`
with no alias on the formatted column.

**Why it happens:** the model treats the alias as optional cosmetic sugar and drops it to keep
the query terse.

**Correct pattern:**

```sql
SELECT Id, LastModifiedDate, FORMAT(LastModifiedDate) formattedDate FROM Account
```

**Detection hint:** a `FORMAT(x)` whose inner field `x` also appears bare in the same `SELECT`
list, with no alias token after the closing paren.

---

## Anti-Pattern 3: Treating the formatted output as a number or date

**What the LLM generates:** `Decimal total = (Decimal) row.get('amountDisplay');` or a `Date`
parse of a `FORMAT()` column, then arithmetic or a numeric `ORDER BY` on it.

**Why it happens:** the model conflates "the amount field" with "the FORMAT() of the amount
field" and forgets the function returns a string.

**Correct pattern:**

```apex
String display = (String) row.get('amountDisplay'); // "$44,000.00"
Decimal raw    = (Decimal) row.get('Amount');        // keep the raw field for math
```

**Detection hint:** a cast of a `FORMAT()` alias to `Decimal`/`Double`/`Date`/`Datetime`, or a
`FORMAT()` column used in a numeric comparison.

---

## Anti-Pattern 4: Putting FORMAT() or convertCurrency() in WHERE/ORDER BY

**What the LLM generates:** `... WHERE FORMAT(CloseDate) = '12/28/2015'`,
`... ORDER BY FORMAT(Amount)`, or `... WHERE convertCurrency(Amount) > 5000`.

**Why it happens:** the model treats `FORMAT()`/`convertCurrency()` as general expressions
usable in any clause, as they would be in SQL.

**Correct pattern:** filter and sort on the raw field; keep both functions in the `SELECT` list.

```sql
SELECT FORMAT(Amount) amt FROM Opportunity WHERE Amount > USD5000 ORDER BY Amount DESC
```

**Detection hint:** the tokens `FORMAT(` or `convertCurrency(` appearing after `WHERE`,
`HAVING`, or `ORDER BY` — `convertCurrency()` in a `WHERE` clause is a documented error.

---

## Anti-Pattern 5: Applying FORMAT() to unsupported field types

**What the LLM generates:** `FORMAT(StageName)`, `FORMAT(Name)`, or `FORMAT(OwnerId)` to
"localize" a picklist, text, or reference field.

**Why it happens:** the model over-generalizes "FORMAT() localizes fields" to every field type.

**Correct pattern:** restrict `FORMAT()` to number, date, time, and currency fields; use
`toLabel()` for translated picklist labels.

```sql
SELECT FORMAT(Amount) amt, toLabel(StageName) stage FROM Opportunity
```

**Detection hint:** `FORMAT()` wrapping anything that isn't a number/date/time/currency field.

---

## Anti-Pattern 6: Inventing a GA/Beta status or a locale-format flag

**What the LLM generates:** "FORMAT() is a Beta function introduced in Spring '25…" or a made-up
argument like `FORMAT(CloseDate, 'yyyy-MM-dd')` to force a specific pattern.

**Why it happens:** models pattern-fill maturity labels and assume a formatting function must
accept a format-mask argument, as `Datetime.format(String)` does.

**Correct pattern:** `FORMAT()` takes only the field/expression to localize — there is no
format-mask argument, and the reference states no maturity label. State it as standard,
documented SOQL/SOSL functionality; if you need a fixed pattern, format in Apex instead.

**Detection hint:** a second argument inside `FORMAT(...)`, or any "GA/Beta/Pilot/introduced in
<release>" claim about `FORMAT()` not backed by a docs citation.
