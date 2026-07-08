# Examples — SOQL FORMAT() Function (Localized Output)

All queries below are drawn from the SOQL/SOSL FORMAT() reference and adapted with realistic
field names. Output strings are illustrative for a US-English locale; the actual rendering
follows the running user's Locale setting. `FORMAT()` output is always a **string**.

## Example 1: Localized datetime alongside the raw value

**Context:** an admin console lists Accounts and needs the last-modified stamp to read like the
UI (`4/10/2025, 3:31 PM`) while a client-side sort still uses the machine value.

**Problem:** a bare `SELECT LastModifiedDate` returns `2025-04-10T22:31:37.000+0000` — correct
for logic, unreadable for the console, and not what the user sees in Salesforce.

**Solution:**

```sql
SELECT Id, LastModifiedDate, FORMAT(LastModifiedDate) formattedDate
FROM Account
```

Returned per row: `LastModifiedDate` = `2025-04-10T22:31:37.000+0000` (raw), `formattedDate` =
`4/10/2025, 3:31 PM` (localized string).

**Why it works:** the raw field feeds logic; `FORMAT(LastModifiedDate)` renders the locale
display. Because `LastModifiedDate` now appears twice, the `formattedDate` **alias is required**
— drop it and the query errors.

---

## Example 2: Currency field as a fully formatted string

**Context:** a monthly statement export must show amounts exactly as the UI does, with the
locale currency symbol and thousands separators.

**Problem:** `SELECT Amount` returns `44000.00` (a plain number). The export layer would have to
re-implement locale currency formatting.

**Solution:**

```sql
SELECT Id, Name, FORMAT(Amount) amountDisplay
FROM Opportunity
WHERE StageName = 'Closed Won'
```

`amountDisplay` comes back as a fully formatted value such as `$44,000.00` instead of a plain
number.

**Why it works:** `FORMAT()` localizes the currency field to the running user's locale, matching
the Classic UI rendering. The filter stays on `StageName`, not on any formatted column.

---

## Example 3: Reading formatted columns in Apex

**Context:** dynamic Apex SOQL builds the statement query and must hand the display strings to a
Visualforce/LWC layer.

**Problem:** developers try to read `FORMAT()` columns as `Decimal`/`Datetime` and hit a cast
error, because the value is a `String`.

**Solution:**

```apex
List<sObject> rows = Database.query(
    'SELECT Id, Amount, FORMAT(Amount) amountDisplay FROM Opportunity ' +
    'WHERE StageName = :stage'
);
for (sObject row : rows) {
    Decimal raw     = (Decimal) row.get('Amount');       // machine value for logic
    String display  = (String)  row.get('amountDisplay'); // "$44,000.00" for the UI
}
```

**Why it works:** the aliased formatted column is retrieved by its alias and typed as `String`.
The raw `Amount` remains a `Decimal` for computation. (Prefer dynamic `Database.query` when you
are unsure `FORMAT()` compiles in inline Apex SOQL for your API version.)

---

## Example 4: FORMAT() nested around an aggregate

**Context:** a dashboard tile needs the earliest close date in the pipeline, localized.

**Problem:** `MIN(CloseDate)` returns a raw date; the tile wants the user-locale string.

**Solution:**

```sql
SELECT FORMAT(MIN(CloseDate)) earliest
FROM Opportunity
```

Read it off the `AggregateResult`:

```apex
AggregateResult ar = [SELECT FORMAT(MIN(CloseDate)) earliest FROM Opportunity];
String earliest = (String) ar.get('earliest');
```

**Why it works:** the aggregate produces one scalar, then `FORMAT()` localizes it. Aggregate
result columns are read by alias — which is also why the `earliest` alias is present.

---

## Example 5: FORMAT() nested around convertCurrency() (multi-currency org)

**Context:** a global pipeline report must show each Opportunity amount converted to the viewer's
currency and formatted for their locale.

**Problem:** raw `Amount` is in the record's own currency and is unformatted.

**Solution:**

```sql
SELECT amount, FORMAT(convertCurrency(amount)) convertedCurrency
FROM Opportunity
```

**Why it works:** `convertCurrency()` (which requires a multi-currency org) converts to the
user's currency, and `FORMAT()` renders that converted number with the locale symbol and
separators. Note `convertCurrency()` **cannot** appear in a `WHERE` clause — keep it in the
`SELECT` list only.

---

## Example 6: SOSL RETURNING with FORMAT()

**Context:** a global search over Accounts should show a localized last-modified date in the
result list.

**Solution:**

```sql
FIND {Acme} RETURNING Account(Id, LastModifiedDate, FORMAT(LastModifiedDate) FormattedDate)
```

Converted currency in a SOSL result works the same way:

```sql
FIND {Acme} RETURNING Account(AnnualRevenue, FORMAT(convertCurrency(AnnualRevenue)) convertedCurrency)
```

**Why it works:** SOSL exposes the identical `FORMAT()` function inside the `RETURNING` field
list, with the same aliasing and nesting rules as SOQL.

---

## Anti-Pattern: FORMAT() in a WHERE / ORDER BY clause

**What practitioners do:** try to filter or sort on the display string, e.g.
`... WHERE FORMAT(CloseDate) = '12/28/2015'` or `... ORDER BY FORMAT(Amount)`.

**What goes wrong:** `FORMAT()` is a `SELECT`-clause presentation function. Filtering or sorting
on its output compares locale-dependent strings (so `Amount` sorts lexically as text, and the
date literal only matches one locale) — the results are wrong and non-portable, not just slow.

**Correct approach:** filter and sort on the **raw** field (`WHERE CloseDate = 2015-12-28`,
`ORDER BY Amount DESC`) and use `FORMAT()` only to shape the columns you return for display.
