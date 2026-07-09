# Examples — SOQL Date Functions

All queries below are illustrative and use standard fields. Swap in your own object,
date/dateTime field, and period. Date functions are one of the seven SOQL `SELECT`
function categories (alongside aggregate functions, `convertCurrency()`,
`convertTimezone()`, `FORMAT()`, `GROUPING()`, and `toLabel()`).

## Example 1: Revenue rolled up per calendar year

**Context:** a dashboard needs total closed-won Amount per calendar year. The current
code queries every Opportunity and sums in an Apex loop.

**Problem:** pulling every row into heap to bucket by year burns query rows and risks a
heap/limit exception on large orgs — the database can do the grouping.

**Solution:**

```apex
Map<Integer, Decimal> revenueByYear = new Map<Integer, Decimal>();
for (AggregateResult ar : [
        SELECT CALENDAR_YEAR(CloseDate) yr, SUM(Amount) total
        FROM Opportunity
        WHERE StageName = 'Closed Won'
        GROUP BY CALENDAR_YEAR(CloseDate)]) {
    revenueByYear.put((Integer) ar.get('yr'), (Decimal) ar.get('total'));
}
```

**Why it works:** `CALENDAR_YEAR(CloseDate)` appears in both `SELECT` and `GROUP BY` (a
date function in `SELECT` must also be in `GROUP BY`), so the database returns one row per
year and does the summation itself.

---

## Example 2: Filter a period with no aggregation

**Context:** a batch needs the Opportunities that close in calendar year 2026 — just the
records, no rollup.

**Problem:** developers hand-compute `CloseDate >= 2026-01-01 AND CloseDate <= 2026-12-31`,
which is verbose and easy to get wrong at the boundaries.

**Solution:**

```sql
SELECT Id, Name, Amount, CloseDate
FROM Opportunity
WHERE CALENDAR_YEAR(CloseDate) = 2026
```

**Why it works:** a date function is allowed in `WHERE` even with no `GROUP BY` clause. The
comparison is to the **integer** `2026` — comparing a date-function result to a date literal
is not allowed.

---

## Example 3: Fiscal-quarter breakdown (standard fiscal years)

**Context:** finance wants opportunity counts by fiscal quarter for the current year.

**Problem:** calendar quarters do not line up with the company's fiscal calendar.

**Solution:**

```sql
SELECT FISCAL_QUARTER(CloseDate) fq, COUNT(Id) cnt
FROM Opportunity
WHERE CloseDate = THIS_FISCAL_YEAR
GROUP BY FISCAL_QUARTER(CloseDate)
ORDER BY FISCAL_QUARTER(CloseDate)
```

**Why it works:** `FISCAL_QUARTER()` follows the org's fiscal calendar. Note the `WHERE`
uses the relative **literal** `THIS_FISCAL_YEAR` on the raw field (a rolling window), while
the *grouping* uses the fiscal **function**. This query only works when the org uses
**standard** fiscal years — `FISCAL_*` functions are unsupported under custom fiscal years.

---

## Example 4: Case volume per calendar day from a DateTime field

**Context:** support wants a count of Cases opened per calendar day this month.

**Problem:** `CreatedDate` is a `DateTime`; grouping on it directly yields one bucket per
distinct instant, which is meaningless.

**Solution:**

```sql
SELECT DAY_ONLY(CreatedDate) d, COUNT(Id) c
FROM Case
WHERE CreatedDate = THIS_MONTH
GROUP BY DAY_ONLY(CreatedDate)
ORDER BY DAY_ONLY(CreatedDate)
```

**Why it works:** `DAY_ONLY()` returns the `Date` portion of a `DateTime`, so each calendar
day collapses to one group. `DAY_ONLY()` accepts only a `DateTime` field.

---

## Example 5: Hour-of-day distribution, adjusted to the user's time zone

**Context:** you want to know which hours Cases are created, in local time, not UTC.

**Problem:** `HOUR_IN_DAY(CreatedDate)` buckets on the raw UTC instant, so a case created at
11pm local shows in the wrong hour.

**Solution:**

```sql
SELECT HOUR_IN_DAY(convertTimezone(CreatedDate)) hr, COUNT(Id) c
FROM Case
GROUP BY HOUR_IN_DAY(convertTimezone(CreatedDate))
```

**Why it works:** `convertTimezone()` shifts the `DateTime` to the running user's time zone
before `HOUR_IN_DAY()` extracts the hour, so buckets follow local time. `HOUR_IN_DAY()`
requires a `DateTime` field. See `apex/timezone-and-datetime-pitfalls` for the details.

---

## Anti-Pattern: comparing a date function to a date literal

**What practitioners do:** try to pin a period by comparing the function result to a date.

```sql
-- Rejected: date-function result vs. a date literal
WHERE CALENDAR_YEAR(CloseDate) = 2026-01-01
WHERE CALENDAR_MONTH(CloseDate) = THIS_MONTH
```

**What goes wrong:** the query fails to compile — a date function returns a number, and you
cannot compare that number to a date literal (an ISO date or a relative literal like
`THIS_MONTH`).

**Correct approach:** compare to an integer (`CALENDAR_YEAR(CloseDate) = 2026`,
`CALENDAR_MONTH(CloseDate) = 1`). If you actually want a rolling window, use a date **literal
on the raw field** instead of a function: `WHERE CloseDate = THIS_MONTH`.
